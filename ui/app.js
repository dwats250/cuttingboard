'use strict';

// ---------------------------------------------------------------------------
// Theme system
// ---------------------------------------------------------------------------

const THEME_MANIFEST = [
  { id: 'default',            label: 'Default' },
  { id: 'projection-finance', label: 'Projection Finance' },
  { id: 'echofi',             label: 'EchoFi' },
];

const THEME_STORAGE_KEY = 'cb_theme';

function currentThemeId() {
  return localStorage.getItem(THEME_STORAGE_KEY) || 'default';
}

function applyTheme(id) {
  const link = document.getElementById('theme-link');
  if (!link) return;
  const valid = THEME_MANIFEST.some(function (t) { return t.id === id; });
  const safeId = valid ? id : 'default';
  link.href = 'themes/' + safeId + '.css';
  localStorage.setItem(THEME_STORAGE_KEY, safeId);
  const sel = document.getElementById('theme-select');
  if (sel) sel.value = safeId;
}

function initTheme() {
  const link = document.getElementById('theme-link');
  if (!link) return;
  link.addEventListener('error', function () {
    const failedId = currentThemeId();
    console.warn('[cuttingboard] theme failed to load: ' + failedId + ' — falling back to default');
    localStorage.setItem(THEME_STORAGE_KEY, 'default');
    link.href = 'themes/default.css';
    const sel = document.getElementById('theme-select');
    if (sel) sel.value = 'default';
  });
  applyTheme(currentThemeId());
}

function renderThemeSwitcher() {
  const container = document.getElementById('theme-switcher');
  if (!container) return;
  const lbl = document.createElement('span');
  lbl.id = 'theme-switcher-label';
  lbl.textContent = 'Theme';
  const sel = document.createElement('select');
  sel.id = 'theme-select';
  const active = currentThemeId();
  for (const t of THEME_MANIFEST) {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = t.label;
    if (t.id === active) opt.selected = true;
    sel.appendChild(opt);
  }
  sel.addEventListener('change', function () { applyTheme(sel.value); });
  container.appendChild(lbl);
  container.appendChild(sel);
}

// ---------------------------------------------------------------------------
// Defensive accessors
// ---------------------------------------------------------------------------

function safeGet(obj, ...keys) {
  let v = obj;
  for (const k of keys) {
    if (v == null || typeof v !== 'object') return null;
    v = v[k];
  }
  return v ?? null;
}

function display(val) {
  if (val === null || val === undefined) return 'N/A';
  return String(val);
}

// ---------------------------------------------------------------------------
// PRD-340 Slice 2 (R1/R4/R3c + fail-closed): the browser channel derives the
// authoritative execution posture ONLY from the resolver-provenanced
// effective_permission envelope, routed through the validated accessor
// admitAuthority() below (never status + system_state.tradable). An absent,
// malformed, prior-session, or unknown-verdict envelope fails closed to
// UNAVAILABLE. This mirrors cuttingboard.authority_projection.admit_projection.
// ---------------------------------------------------------------------------

// verdict -> authoritative posture (mirrors _VERDICT_MAP in authority_projection.py)
var _VERDICT_POSTURE = {
  PERMITTED: 'TRADE_READY',
  NO_TRADE: 'STAY_FLAT',
  OBSERVE_ONLY: 'OBSERVE_ONLY',
  HALT: 'HALT',
  UNAVAILABLE: 'UNAVAILABLE',
};

// verdict -> restriction rank (mirrors _RANK in effective_permission.py). Also the
// canonical CLOSED key set and the recovery-basis schema, mirrored so the browser
// enforces the SAME closed-schema + cross-field admission the Python read boundary
// (effective_permission._valid_canonical) does -- a forged/partial envelope missing
// any canonical field (or with a cross-field mismatch) fails closed here too.
var _RANK = { PERMITTED: 0, NO_TRADE: 1, OBSERVE_ONLY: 1, HALT: 2, UNAVAILABLE: 3 };
var _CANONICAL_KEYS = ['authority_version', 'decision_seq', 'decision_uid',
  'permission_line', 'recovery_basis', 'restriction_rank', 'run_uid',
  'session_date', 'valid_until', 'verdict'];

function _isInt(x) { return typeof x === 'number' && Number.isInteger(x); }

function _recoveryBasisWellFormed(rb) {
  if (rb === null) return true;                          // None is well-formed
  if (typeof rb !== 'object' || Array.isArray(rb)) return false;
  var keys = Object.keys(rb).sort();
  var want = ['reason', 'superseded_authority_version', 'superseding_decision_uid'];
  if (keys.length !== want.length) return false;
  for (var i = 0; i < want.length; i++) { if (keys[i] !== want[i]) return false; }
  if (rb.reason !== 'REDECISION') return false;
  if (typeof rb.superseding_decision_uid !== 'string' || !rb.superseding_decision_uid.trim()) return false;
  var sav = rb.superseded_authority_version;
  return Array.isArray(sav) && sav.length === 3
    && typeof sav[0] === 'string' && !!sav[0] && _isInt(sav[1]) && _isInt(sav[2]);
}

function isCanonicalEnvelope(env) {
  if (!env || typeof env !== 'object' || Array.isArray(env)) return false;
  var keys = Object.keys(env).sort();                    // EXACT closed key set, no extras
  if (keys.length !== _CANONICAL_KEYS.length) return false;
  for (var i = 0; i < _CANONICAL_KEYS.length; i++) { if (keys[i] !== _CANONICAL_KEYS[i]) return false; }
  if (!Object.prototype.hasOwnProperty.call(_RANK, env.verdict)) return false;   // known verdict
  if (typeof env.decision_uid !== 'string' || !env.decision_uid) return false;
  if (typeof env.run_uid !== 'string' || !env.run_uid) return false;
  if (typeof env.session_date !== 'string' || !env.session_date) return false;
  if (typeof env.valid_until !== 'string') return false;
  if (typeof env.permission_line !== 'string') return false;
  if (!_recoveryBasisWellFormed(env.recovery_basis)) return false;
  if (!_isInt(env.restriction_rank) || !_isInt(env.decision_seq) || env.decision_seq < 1) return false;
  if (env.restriction_rank !== _RANK[env.verdict]) return false;                 // rank == _RANK[verdict]
  var av = env.authority_version;                        // == [session_date, decision_seq, restriction_rank]
  return Array.isArray(av) && av.length === 3
    && av[0] === env.session_date && av[1] === env.decision_seq && av[2] === env.restriction_rank;
}

// The SOLE reader of the canonical projection field on the served contract (T4
// routing): validate + return the admitted envelope, else null (fail-closed).
function admitAuthority(contract) {
  var env = safeGet(contract, 'effective_permission');
  // closed-schema + cross-field admission (mirrors effective_permission._valid_canonical):
  // a forged/partial envelope is rejected before any posture is derived.
  if (!isCanonicalEnvelope(env)) return null;
  if (env.verdict === 'UNAVAILABLE') return null;        // sentinel is never a grant
  // prior-session fail-closed: the authority must be for THIS served session.
  var sessionDate = safeGet(contract, 'session_date');
  if (sessionDate && env.session_date !== sessionDate) return null;
  // fail-closed freshness (mirrors admit_persisted's now-vs-valid_until compare):
  // an unparseable or already-expired valid_until is never a live grant.
  var validUntilMs = Date.parse(env.valid_until);
  if (isNaN(validUntilMs) || Date.now() > validUntilMs) return null;
  return env;
}

function derivePosture(contract) {
  var env = admitAuthority(contract);
  if (env === null) return 'UNAVAILABLE';
  return _VERDICT_POSTURE[env.verdict] || 'UNAVAILABLE';
}

// ---------------------------------------------------------------------------
// UI state helpers
// ---------------------------------------------------------------------------

function showStatus(msg, isError) {
  const el = document.getElementById('status-msg');
  const cv = document.getElementById('contract-view');
  el.textContent = msg;
  el.className = 'visible' + (isError ? ' error' : '');
  cv.className = '';
}

function showContract() {
  document.getElementById('status-msg').className = '';
  document.getElementById('contract-view').className = 'visible';
}

function setText(id, val) {
  document.getElementById(id).textContent = val;
}

// ---------------------------------------------------------------------------
// Block renderers
// ---------------------------------------------------------------------------

function renderSignalBar(contract) {
  // PRD-340 R4: posture is the EP-derived authoritative action, not status+tradable.
  const posture = derivePosture(contract);

  const postureEl = document.getElementById('sig-posture');
  postureEl.textContent = posture;
  postureEl.className = 'sig-val ' + posture;

  const corrState = safeGet(contract, 'correlation', 'state');
  const riskModifier = safeGet(contract, 'correlation', 'risk_modifier');

  const corrEl = document.getElementById('sig-corr-state');
  corrEl.textContent = corrState !== null ? display(corrState) : 'N/A';
  corrEl.className = 'sig-val' + (corrState ? ' ' + corrState : '');

  const riskEl = document.getElementById('sig-risk');
  riskEl.textContent = riskModifier !== null ? riskModifier + 'x' : 'N/A';
}

function renderPrimaryTrade(contract) {
  const block = document.getElementById('primary-trade-block');
  const candidates = safeGet(contract, 'trade_candidates');
  // PRD-340 F3 (fail-closed grant): the PRIMARY TRADE surface shows ONLY when the
  // admitted authority is PERMITTED (TRADE_READY posture) -- never on candidate
  // presence alone. A stale/invalid/absent authority hides the grant surface.
  if (derivePosture(contract) !== 'TRADE_READY'
      || !Array.isArray(candidates) || candidates.length === 0) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const c = candidates[0];
  const rr = safeGet(c, 'risk_reward');
  // PRD-260 R3: a continuation R:R is derived from the synthetic 3xATR
  // reward ceiling (PRD-240 R3), not a calibrated target — label it.
  const rrCeiling = safeGet(c, 'entry_mode') === 'CONTINUATION' ? ' (3xATR ceiling)' : '';
  const rrDisplay = (rr != null ? Number(rr).toFixed(1) : 'N/A') + rrCeiling;

  document.getElementById('primary-trade-inner').innerHTML =
    `<div class="primary-trade-symbol">${display(safeGet(c, 'symbol'))}</div>` +
    `<div class="primary-trade-meta">` +
    `<span>${display(safeGet(c, 'direction'))}</span>` +
    `<span>${display(safeGet(c, 'entry_mode'))}</span>` +
    `<span>${display(safeGet(c, 'strategy_tag'))}</span>` +
    `<span>R:R ${rrDisplay}</span>` +
    `</div>`;
}

function renderNoTrade(contract) {
  const block = document.getElementById('no-trade-block');
  // PRD-340 F4: authority is the admitted EP posture (derivePosture(contract)),
  // not status+tradable. NO_TRADE (STAY_FLAT) with NO gated candidates is the pure
  // no-setup state; a STAY_FLAT with candidates present is the watchlist below.
  const candidates = safeGet(contract, 'trade_candidates');
  const hasCandidates = Array.isArray(candidates) && candidates.length > 0;
  if (derivePosture(contract) !== 'STAY_FLAT' || hasCandidates) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const reasons = [];

  const stayFlatReason = safeGet(contract, 'system_state', 'stay_flat_reason');
  if (stayFlatReason) reasons.push(stayFlatReason);

  if (!hasCandidates) reasons.push('No valid setups');

  const corrState = safeGet(contract, 'correlation', 'state');
  if (corrState === 'CONFLICT') reasons.push('Correlation conflict');

  document.getElementById('no-trade-reasons').innerHTML =
    reasons.map(r => `<div class="reason-item">${r}</div>`).join('');
}

function renderWatchlist(contract) {
  const block = document.getElementById('watchlist-block');
  // PRD-340 F4: the WATCHLIST posture is retired (no such EP verdict). The
  // watchlist is NON-AUTHORITATIVE evidence: candidates were present but the
  // admitted authority is STAY_FLAT (no grant). It is framing, never a permission
  // -- so it shows only under the admitted STAY_FLAT posture with candidates.
  const candidates = safeGet(contract, 'trade_candidates');
  const hasCandidates = Array.isArray(candidates) && candidates.length > 0;
  if (derivePosture(contract) !== 'STAY_FLAT' || !hasCandidates) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  document.getElementById('watchlist-reasons').innerHTML =
    `<div class="reason-item">Candidates present but no execution authority</div>`;
}

function renderSecondarySetups(contract) {
  const block = document.getElementById('secondary-setups-block');
  const candidates = safeGet(contract, 'trade_candidates');
  if (!Array.isArray(candidates) || candidates.length <= 1) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const tbody = document.getElementById('secondary-setups-tbody');
  tbody.innerHTML = '';

  const slice = candidates.slice(1, 5);
  for (const c of slice) {
    const rr = safeGet(c, 'risk_reward');
    // PRD-260 R3: label continuation R:R as the synthetic ceiling ratio.
    const rrCeiling = safeGet(c, 'entry_mode') === 'CONTINUATION' ? ' (3xATR ceiling)' : '';
    const rrDisplay = (rr != null ? Number(rr).toFixed(1) : 'N/A') + rrCeiling;
    const tr = document.createElement('tr');
    tr.innerHTML =
      `<td>${display(safeGet(c, 'symbol'))}</td>` +
      `<td>${display(safeGet(c, 'direction'))}</td>` +
      `<td>${display(safeGet(c, 'entry_mode'))}</td>` +
      `<td>${display(safeGet(c, 'strategy_tag'))}</td>` +
      `<td>${rrDisplay}</td>`;
    tbody.appendChild(tr);
  }
}

function renderCorrelation(contract) {
  const block = document.getElementById('correlation-block');
  const corr = safeGet(contract, 'correlation');
  if (!corr) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const state = safeGet(corr, 'state');
  block.className = 'block' + (state ? ' corr-' + state : '');

  const el = document.getElementById('corr-state');
  el.textContent = display(state);
  el.className = display(state);

  setText('corr-modifier', display(safeGet(corr, 'risk_modifier')));
  setText('corr-pair', `${display(safeGet(corr, 'gold_symbol'))} / ${display(safeGet(corr, 'dollar_symbol'))}`);
}

function renderRejections(contract) {
  const tbody = document.getElementById('rej-tbody');
  const empty = document.getElementById('rej-empty');
  tbody.innerHTML = '';

  const rejections = safeGet(contract, 'rejections');
  if (!Array.isArray(rejections) || rejections.length === 0) {
    empty.style.display = '';
    document.getElementById('rej-table').style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  document.getElementById('rej-table').style.display = '';

  for (const r of rejections) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      `<td>${display(safeGet(r, 'symbol'))}</td>` +
      `<td>${display(safeGet(r, 'stage'))}</td>` +
      `<td>${display(safeGet(r, 'reason'))}</td>`;
    tbody.appendChild(tr);
  }
}

function renderHeader(contract) {
  const raw = safeGet(contract, 'generated_at');
  let ts = 'N/A';
  if (raw) {
    try { ts = new Date(raw).toLocaleString(); } catch (_) { ts = raw; }
  }
  setText('header-timestamp', ts);
  setText('header-regime', display(safeGet(contract, 'system_state', 'market_regime')));
  setText('header-status', display(safeGet(contract, 'status')));
}

function renderRouter(contract) {
  const block = document.getElementById('router-block');
  const mode = safeGet(contract, 'system_state', 'router_mode');
  if (!mode) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';
  setText('router-value', mode);
}

// ---------------------------------------------------------------------------
// Main render
// ---------------------------------------------------------------------------

function renderContract(contract) {
  renderSignalBar(contract);
  renderPrimaryTrade(contract);
  renderNoTrade(contract);
  renderWatchlist(contract);
  renderSecondarySetups(contract);
  renderCorrelation(contract);
  renderRejections(contract);
  renderHeader(contract);
  renderRouter(contract);
  showContract();
}

// ---------------------------------------------------------------------------
// JSON load + error handling
// ---------------------------------------------------------------------------

function loadJSON(text) {
  let data;
  try {
    data = JSON.parse(text);
  } catch (_) {
    showStatus('INVALID JSON', true);
    return;
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    showStatus('INVALID CONTRACT STRUCTURE', true);
    return;
  }
  renderContract(data);
}

function autoFetch() {
  if (location.protocol === 'file:') return;
  fetch('./contract.json?v=' + Date.now())
    .then(function (r) { return r.ok ? r.text() : null; })
    .then(function (text) { if (text) loadJSON(text); })
    .catch(function () {});
}

// ---------------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
  initTheme();
  renderThemeSwitcher();

  if (document.getElementById('status-msg')) {
    showStatus('NO CONTRACT LOADED', false);

    document.getElementById('file-input').addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function (ev) { loadJSON(ev.target.result); };
      reader.onerror = function () { showStatus('FILE READ ERROR', true); };
      reader.readAsText(file);
      e.target.value = '';
    });

    document.getElementById('paste-toggle').addEventListener('click', function () {
      document.getElementById('paste-area').classList.toggle('visible');
    });

    document.getElementById('paste-btn').addEventListener('click', function () {
      const text = document.getElementById('paste-input').value.trim();
      if (!text) { showStatus('NO CONTRACT LOADED', false); return; }
      loadJSON(text);
    });

    autoFetch();
  }

  initPayloadDashboard();
});

// ---------------------------------------------------------------------------
// Payload dashboard — Signal Forge candidate viewer (index.html)
// ---------------------------------------------------------------------------

function _dashVal(val) {
  if (val === null || val === undefined || val === '') return '—';
  return String(val);
}

function _esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function filter(candidates, grade, vis, dir) {
  return candidates.filter(function (c) {
    if (grade !== 'ALL' && (c.grade || null) !== grade) return false;
    const status = c.visibility_status || null;
    if (vis === 'DEFAULT') {
      if (status !== 'ACTIVE' && status !== 'NEAR_MISS') return false;
    } else if (vis !== 'ALL') {
      if (status !== vis) return false;
    }
    if (dir !== 'ALL' && (c.direction || null) !== dir) return false;
    return true;
  });
}

function renderDetailPanel(c) {
  const conditions = Array.isArray(c.enable_conditions) && c.enable_conditions.length > 0
    ? c.enable_conditions.map(function (s) { return '<li>' + _esc(s) + '</li>'; }).join('')
    : '<li>—</li>';
  const expl = (c.explanation && typeof c.explanation === 'object') ? c.explanation : {};
  const blockReasons = Array.isArray(expl.block_reasons) ? expl.block_reasons : [];
  const requiredChanges = Array.isArray(expl.required_changes) ? expl.required_changes : [];
  const macroAlignment = expl.macro_alignment != null ? expl.macro_alignment : null;

  const blockReasonsHtml = blockReasons.length > 0
    ? '<div class="detail-row"><span class="detail-label">block_reasons</span><ul class="detail-conditions">' +
      blockReasons.map(function (s) { return '<li>' + _esc(s) + '</li>'; }).join('') +
      '</ul></div>'
    : '';
  const macroAlignmentHtml = macroAlignment != null
    ? '<div class="detail-row"><span class="detail-label">macro_alignment</span><span class="detail-val">' + _esc(String(macroAlignment)) + '</span></div>'
    : '';
  const requiredChangesHtml = requiredChanges.length > 0
    ? '<div class="detail-row"><span class="detail-label">required_changes</span><ul class="detail-conditions">' +
      requiredChanges.map(function (s) { return '<li>' + _esc(s) + '</li>'; }).join('') +
      '</ul></div>'
    : '';

  return (
    '<div class="candidate-detail">' +
    '<div class="detail-row"><span class="detail-label">grade</span><span class="detail-val">' + _esc(_dashVal(c.grade)) + '</span></div>' +
    '<div class="detail-row"><span class="detail-label">visibility_status</span><span class="detail-val">' + _esc(_dashVal(c.visibility_status)) + '</span></div>' +
    '<div class="detail-row"><span class="detail-label">visibility_reason</span><span class="detail-val">' + _esc(_dashVal(c.visibility_reason)) + '</span></div>' +
    '<div class="detail-row"><span class="detail-label">enable_conditions</span><ul class="detail-conditions">' + conditions + '</ul></div>' +
    blockReasonsHtml +
    macroAlignmentHtml +
    requiredChangesHtml +
    '</div>'
  );
}

function renderRow(c) {
  const sym = _esc(c.symbol || '?');
  const grade = _esc(_dashVal(c.grade));
  const vis = _esc(_dashVal(c.visibility_status));
  const dir = _esc(_dashVal(c.direction));
  const visClass = 'vis-' + (c.visibility_status || 'unknown').toLowerCase().replace(/_/g, '-');
  return (
    '<tr class="candidate-row ' + visClass + '" data-symbol="' + sym + '">' +
    '<td>' + sym + '</td>' +
    '<td>' + grade + '</td>' +
    '<td class="' + visClass + '">' + vis + '</td>' +
    '<td>' + dir + '</td>' +
    '</tr>' +
    '<tr class="candidate-detail-row" data-detail-for="' + sym + '" style="display:none">' +
    '<td colspan="4">' + renderDetailPanel(c) + '</td>' +
    '</tr>'
  );
}

const _expandedRows = new Set();

function expandRow(symbol, tbody) {
  const detailRow = tbody.querySelector('[data-detail-for="' + symbol + '"]');
  if (!detailRow) return;
  if (_expandedRows.has(symbol)) {
    _expandedRows.delete(symbol);
    detailRow.style.display = 'none';
  } else {
    _expandedRows.add(symbol);
    detailRow.style.display = '';
  }
}

function _renderCandidateTable(candidates) {
  const container = document.getElementById('candidate-table-container');
  if (!container) return;

  const gradeEl = document.getElementById('filter-grade');
  const visEl   = document.getElementById('filter-visibility');
  const dirEl   = document.getElementById('filter-direction');
  if (!gradeEl || !visEl || !dirEl) return;

  _expandedRows.clear();
  const filtered = filter(candidates, gradeEl.value, visEl.value, dirEl.value);

  const rows = filtered.length > 0
    ? filtered.map(renderRow).join('')
    : '<tr><td colspan="4" class="cb-no-results">No matching candidates</td></tr>';

  container.innerHTML =
    '<table class="candidate-table">' +
    '<thead><tr><th>Symbol</th><th>Grade</th><th>Visibility</th><th>Direction</th></tr></thead>' +
    '<tbody id="candidate-tbody">' + rows + '</tbody>' +
    '</table>';

  const tbody = document.getElementById('candidate-tbody');
  tbody.addEventListener('click', function (e) {
    const row = e.target.closest('tr.candidate-row');
    if (!row) return;
    const sym = row.dataset.symbol;
    if (sym) expandRow(sym, tbody);
  });
}

function _outcomeBadgeClass(outcome) {
  if (outcome === 'TRADE')    return 'badge-trade';
  if (outcome === 'NO_TRADE') return 'badge-no-trade';
  if (outcome === 'HALT')     return 'badge-halt';
  return 'badge-unknown';
}

function _renderOutcomeBadge(outcome) {
  const badge = document.getElementById('outcome-badge');
  if (!badge) return;
  badge.className = 'outcome-badge ' + _outcomeBadgeClass(outcome);
  badge.textContent = outcome !== null ? String(outcome) : '';
}

function initPayloadDashboard() {
  const container = document.getElementById('candidate-table-container');
  if (!container) return;

  let candidateCache = [];

  function rerender() {
    _renderCandidateTable(candidateCache);
  }

  ['filter-grade', 'filter-visibility', 'filter-direction'].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', rerender);
  });

  fetch('./latest_payload.json?v=' + Date.now())
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (payload) {
      if (!payload) return;
      const sections = payload.sections;
      candidateCache = (sections && Array.isArray(sections.top_trades)) ? sections.top_trades : [];
      rerender();
    })
    .catch(function () {});

  fetch('./contract.json?v=' + Date.now())
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (contract) {
      if (!contract) return;
      _renderOutcomeBadge(safeGet(contract, 'outcome'));
    })
    .catch(function () {});
}
