'use strict';

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

function setClass(id, cls) {
  document.getElementById(id).className = cls;
}

// ---------------------------------------------------------------------------
// Block renderers
// ---------------------------------------------------------------------------

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

function renderExecution(contract) {
  const status = safeGet(contract, 'status');
  const tradable = safeGet(contract, 'system_state', 'tradable');
  const posture = derivePosture(status, tradable);

  const el = document.getElementById('posture-value');
  el.textContent = posture;
  el.className = posture;

  setText('tradable-value', display(tradable));
}

function renderCorrelation(contract) {
  const block = document.getElementById('correlation-block');
  const corr = safeGet(contract, 'correlation');
  if (!corr) {
    block.style.display = 'none';
    return;
  }
  block.style.display = '';

  const state = display(safeGet(corr, 'state'));
  const el = document.getElementById('corr-state');
  el.textContent = state;
  el.className = state;

  setText('corr-modifier', display(safeGet(corr, 'risk_modifier')));
  setText('corr-pair', `${display(safeGet(corr, 'gold_symbol'))} / ${display(safeGet(corr, 'dollar_symbol'))}`);
}

function renderSetups(contract) {
  const tbody = document.getElementById('setups-tbody');
  const empty = document.getElementById('setups-empty');
  tbody.innerHTML = '';

  const candidates = safeGet(contract, 'trade_candidates');
  if (!Array.isArray(candidates) || candidates.length === 0) {
    empty.style.display = '';
    document.getElementById('setups-table').style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  document.getElementById('setups-table').style.display = '';

  const slice = candidates.slice(0, 5);
  for (const c of slice) {
    const rr = safeGet(c, 'risk_reward');
    const rrDisplay = rr != null ? Number(rr).toFixed(1) : 'N/A';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${display(safeGet(c, 'symbol'))}</td>
      <td>${display(safeGet(c, 'direction'))}</td>
      <td>${display(safeGet(c, 'entry_mode'))}</td>
      <td>${display(safeGet(c, 'strategy_tag'))}</td>
      <td>${rrDisplay}</td>
    `;
    tbody.appendChild(tr);
  }
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
    tr.innerHTML = `
      <td>${display(safeGet(r, 'symbol'))}</td>
      <td>${display(safeGet(r, 'stage'))}</td>
      <td>${display(safeGet(r, 'reason'))}</td>
    `;
    tbody.appendChild(tr);
  }
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
  renderHeader(contract);
  renderExecution(contract);
  renderCorrelation(contract);
  renderSetups(contract);
  renderRejections(contract);
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

// ---------------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
  showStatus('NO CONTRACT LOADED', false);

  // File input
  document.getElementById('file-input').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (ev) { loadJSON(ev.target.result); };
    reader.onerror = function () { showStatus('FILE READ ERROR', true); };
    reader.readAsText(file);
    // Reset so same file can be re-loaded
    e.target.value = '';
  });

  // Paste toggle
  document.getElementById('paste-toggle').addEventListener('click', function () {
    const area = document.getElementById('paste-area');
    area.classList.toggle('visible');
  });

  // Paste render
  document.getElementById('paste-btn').addEventListener('click', function () {
    const text = document.getElementById('paste-input').value.trim();
    if (!text) { showStatus('NO CONTRACT LOADED', false); return; }
    loadJSON(text);
  });
});
