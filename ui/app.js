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
// Sole allowed derivation (PRD-024 §EXECUTION POSTURE)
// ---------------------------------------------------------------------------

function derivePosture(status, tradable) {
  if (status === 'ERROR') return 'ERROR';
  if (status === 'STAY_FLAT') return 'STAY_FLAT';
  if (status === 'OK' && tradable === true) return 'TRADE_READY';
  if (status === 'OK' && tradable === false) return 'WATCHLIST';
  return 'N/A';
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
  const status = safeGet(contract, 'status');
  const tradable = safeGet(contract, 'system_state', 'tradable');
  const posture = derivePosture(status, tradable);

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
  if (!Array.isArray(candidates) || candidates.length === 0) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const c = candidates[0];
  const rr = safeGet(c, 'risk_reward');
  const rrDisplay = rr != null ? Number(rr).toFixed(1) : 'N/A';

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
  const status = safeGet(contract, 'status');
  const tradable = safeGet(contract, 'system_state', 'tradable');
  if (derivePosture(status, tradable) !== 'STAY_FLAT') {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const reasons = [];

  const stayFlatReason = safeGet(contract, 'system_state', 'stay_flat_reason');
  if (stayFlatReason) reasons.push(stayFlatReason);

  const candidates = safeGet(contract, 'trade_candidates');
  if (!Array.isArray(candidates) || candidates.length === 0) reasons.push('No valid setups');

  const corrState = safeGet(contract, 'correlation', 'state');
  if (corrState === 'CONFLICT') reasons.push('Correlation conflict');

  document.getElementById('no-trade-reasons').innerHTML =
    reasons.map(r => `<div class="reason-item">${r}</div>`).join('');
}

function renderWatchlist(contract) {
  const block = document.getElementById('watchlist-block');
  const status = safeGet(contract, 'status');
  const tradable = safeGet(contract, 'system_state', 'tradable');
  if (derivePosture(status, tradable) !== 'WATCHLIST') {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const candidates = safeGet(contract, 'trade_candidates');
  const reason = (Array.isArray(candidates) && candidates.length > 0)
    ? 'Candidates present but system not tradable'
    : 'No valid setups';

  document.getElementById('watchlist-reasons').innerHTML =
    `<div class="reason-item">${reason}</div>`;
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
    const rrDisplay = rr != null ? Number(rr).toFixed(1) : 'N/A';
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
  fetch('./contract.json')
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
});
