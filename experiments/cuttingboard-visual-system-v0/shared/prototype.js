/*
 * CUTTINGBOARD VISUAL SYSTEM LAB V0
 * Prototype-only renderer. Static data in; semantic HTML out.
 */

function cbLabEscape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

function cbLabKvRows(rows, className = "") {
  return `
    <div class="kv-list ${cbLabEscape(className)}">
      ${rows.map((row) => `
        <div class="kv-row">
          <div class="kv-label">${cbLabEscape(row.label)}</div>
          <div class="kv-value">${cbLabEscape(row.value)}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function cbLabSurface(key, title, body, options = {}) {
  const note = options.note
    ? `<span class="surface-title__note">${cbLabEscape(options.note)}</span>`
    : "";
  const classes = ["surface", `surface--${key}`, options.className || ""]
    .filter(Boolean)
    .join(" ");
  const attributes = Object.entries(options.attributes || {})
    .map(([name, value]) => `${cbLabEscape(name)}="${cbLabEscape(value)}"`)
    .join(" ");

  return `
    <section class="${classes}" data-surface="${cbLabEscape(key)}" data-container="surface" ${attributes}>
      <h2 class="surface-title">
        <span>${cbLabEscape(title)}</span>
        ${note}
      </h2>
      ${body}
    </section>
  `;
}

function cbLabMarketState(fixture) {
  const axes = fixture.marketState.map((axis) => `
    <div class="axis">
      <div class="axis__label">${cbLabEscape(axis.label)}</div>
      <div class="axis__content">
        <div class="axis__value">${cbLabEscape(axis.value)}</div>
        ${axis.provenance ? `<div class="axis__provenance">${cbLabEscape(axis.provenance)}</div>` : ""}
        ${axis.qualifier ? `<div class="qualifier">${cbLabEscape(axis.qualifier)}</div>` : ""}
      </div>
    </div>
  `).join("");

  return cbLabSurface(
    "market-state",
    "Market State",
    `<div class="axis-list" data-critical-content="market-state">${axes}</div>`,
    { attributes: { "data-authority": "market-state" } }
  );
}

function cbLabSystemState(fixture) {
  const state = fixture.systemState;
  return cbLabSurface(
    "system-state",
    "System State",
    `
      <div class="system-state" data-status="${cbLabEscape(state.status)}" data-critical-content="system-state">
        <div class="decision-label">DECISION STATE</div>
        <p class="decision" data-decision>${cbLabEscape(state.decision)}</p>
        <p class="system-verdict">${cbLabEscape(state.verdict)}</p>
        <p class="system-reason">${cbLabEscape(state.reason)}</p>
        <p class="system-context">${cbLabEscape(state.context)}</p>
        <div class="updated-row">
          <span>UPDATED</span>
          <span>${cbLabEscape(state.updated)}</span>
        </div>
      </div>
    `,
    { attributes: { "data-authority": "system-state" } }
  );
}

function cbLabOpportunity(fixture) {
  const opportunity = fixture.opportunity;
  const metrics = [
    { label: "SURFACED", value: opportunity.surfaced },
    { label: opportunity.setupsLabel, value: opportunity.setups },
    { label: "WATCHLIST", value: opportunity.watchlist },
    { label: "REJECTED", value: opportunity.rejected }
  ];

  return cbLabSurface(
    "opportunity-survival",
    "Opportunity Survival",
    `
      <div class="metric-grid">
        ${metrics.map((metric) => `
          <div class="metric">
            <span class="metric__label">${cbLabEscape(metric.label)}</span>
            <strong class="metric__value">${cbLabEscape(metric.value)}</strong>
          </div>
        `).join("")}
      </div>
      <div class="rejection">
        <span class="kv-label">PRIMARY REJECTION</span>
        <strong>${cbLabEscape(opportunity.primaryRejection)}</strong>
      </div>
    `,
    { attributes: { "data-opportunity-summary": "true" } }
  );
}

function cbLabCandidateDiagram(candidate) {
  return `
    <div class="level-map" aria-label="SPY level map">
      ${candidate.diagram.map((level) => `
        <div class="level-map__row" data-level="${cbLabEscape(level.label)}">
          <span>${cbLabEscape(level.label)}</span>
          <span>${cbLabEscape(level.value)}</span>
          <span class="level-map__delta">${cbLabEscape(level.delta)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function cbLabCandidate(fixture) {
  const candidate = fixture.candidate;

  if (!candidate) {
    return cbLabSurface(
      "candidate",
      "Developing Setups",
      `
        <div class="empty-state" data-candidate="empty">
          <strong>NO DEVELOPING SETUPS</strong>
          <span>Opportunity Survival remains visible; no candidate identity, level, or invalidation is fabricated.</span>
        </div>
      `,
      { attributes: { "data-candidate-surface": "true" } }
    );
  }

  return cbLabSurface(
    "candidate",
    "Developing Setup",
    `
      <article class="candidate-minimum" data-candidate="present">
        <header class="candidate-head" data-candidate-identity>
          <strong class="candidate-symbol">${cbLabEscape(candidate.symbol)}</strong>
          <span class="candidate-tags">${cbLabEscape(candidate.grade)} · ${cbLabEscape(candidate.state)} · ${cbLabEscape(candidate.structure)}</span>
        </header>
        <p class="truth-note">${cbLabEscape(candidate.play)}</p>
        <div>
          <div class="critical-pair" data-candidate-level>
            <span class="critical-pair__label">LEVEL</span>
            <strong class="critical-pair__value">${cbLabEscape(candidate.level)}</strong>
          </div>
          <div class="critical-pair" data-candidate-invalidation>
            <span class="critical-pair__label">INVALIDATION</span>
            <strong class="critical-pair__value">${cbLabEscape(candidate.invalidation)}</strong>
          </div>
        </div>
        <div class="candidate-disclosures">
          <details class="disclosure">
            <summary>Candidate reason / watch</summary>
            <div class="disclosure__body detail-copy">
              <span><strong>REASON</strong> · ${cbLabEscape(candidate.reason)}</span>
              <span><strong>WATCH</strong> · ${cbLabEscape(candidate.watch)}</span>
            </div>
          </details>
          <details class="disclosure">
            <summary>Level map</summary>
            <div class="disclosure__body">${cbLabCandidateDiagram(candidate)}</div>
          </details>
        </div>
      </article>
    `,
    { attributes: { "data-candidate-surface": "true" } }
  );
}

function cbLabGex(fixture) {
  return cbLabSurface(
    "gex",
    "GEX",
    `
      <p class="context-warning">Context only · positioning never grants permission.</p>
      ${cbLabKvRows(fixture.gex.rows)}
      <p class="provenance">${cbLabEscape(fixture.gex.provenance)}</p>
      <p class="qualifier">${cbLabEscape(fixture.gex.qualifier)}</p>
    `,
    {
      note: "CONTEXT ONLY",
      attributes: {
        "data-context-start": "true",
        "data-context-surface": "true"
      }
    }
  );
}

function cbLabMovement(fixture) {
  return cbLabSurface(
    "movement",
    "Market Movement",
    `
      ${cbLabKvRows(fixture.movement.rows)}
      <p class="provenance">${cbLabEscape(fixture.movement.provenance)}</p>
    `,
    { attributes: { "data-context-surface": "true" } }
  );
}

function cbLabMacro(fixture) {
  const macro = fixture.macro;
  return cbLabSurface(
    "macro",
    "Macro Tape",
    `
      <div class="macro-summary">
        <div class="macro-bias">
          <div class="macro-bias__label">MACRO BIAS</div>
          <div class="macro-bias__value">${cbLabEscape(macro.bias)}</div>
        </div>
        <div>
          <div class="macro-tally">${cbLabEscape(macro.tally)}</div>
          <ul class="pressure-list">
            ${macro.pressures.map((pressure) => `<li>• ${cbLabEscape(pressure)}</li>`).join("")}
          </ul>
        </div>
      </div>
      <p class="provenance">${cbLabEscape(macro.provenance)}</p>
      <details class="disclosure">
        <summary>Macro drivers and tradable prices</summary>
        <div class="disclosure__body">
          <div class="driver-grid">
            ${macro.drivers.map((driver) => `
              <span class="driver">
                <span>${cbLabEscape(driver.label)} ${cbLabEscape(driver.direction)}</span>
                <strong>${cbLabEscape(driver.value)}</strong>
              </span>
            `).join("")}
          </div>
          <div class="tradable-grid" style="margin-top:6px">
            ${macro.tradables.map((item) => `
              <span class="tradable">
                <span>${cbLabEscape(item.label)}</span>
                <strong>${cbLabEscape(item.value)}</strong>
              </span>
            `).join("")}
          </div>
        </div>
      </details>
    `,
    { attributes: { "data-context-surface": "true" } }
  );
}

function cbLabEventDetail(fixture) {
  if (!fixture.eventDetail) {
    return "";
  }

  const event = fixture.eventDetail;
  return cbLabSurface(
    "event-detail",
    "Red Folder",
    `
      <div class="event-line">
        <strong class="event-name">${cbLabEscape(event.headline)}</strong>
        <span class="event-time">${cbLabEscape(event.when)}</span>
        <span class="kv-label">${cbLabEscape(event.type)}</span>
      </div>
      <p class="provenance">${cbLabEscape(event.provenance)}</p>
    `,
    {
      className: "event-card",
      attributes: { "data-event-detail": "true" }
    }
  );
}

function cbLabSessionObservation(fixture) {
  if (!fixture.sessionObservation) {
    return "";
  }

  const observation = fixture.sessionObservation;
  return cbLabSurface(
    "session-observation",
    "SPY Session Observation",
    `
      <p class="history-summary">${cbLabEscape(observation.state)}</p>
      ${observation.rows.length ? cbLabKvRows(observation.rows) : ""}
      <p class="provenance">${cbLabEscape(observation.provenance)}</p>
    `,
    { note: "DAILY / SESSION" }
  );
}

function cbLabMarketControl(fixture) {
  if (!fixture.marketControl) {
    return "";
  }

  return cbLabSurface(
    "market-control",
    "Market Control",
    `
      ${cbLabKvRows(fixture.marketControl.rows)}
      <p class="provenance">${cbLabEscape(fixture.marketControl.provenance)}</p>
    `,
    { note: "CONTEXT · NOT AUTHORITY" }
  );
}

function cbLabTrend(fixture) {
  const rows = fixture.trend.rows.map((row) => `
    <tr>
      <td data-label="Symbol">${cbLabEscape(row.symbol)}</td>
      <td data-label="Price">${cbLabEscape(row.price)}</td>
      <td data-label="Alignment">${cbLabEscape(row.alignment)}</td>
      <td data-label="RVOL">${cbLabEscape(row.rvol)}</td>
      <td data-label="SMA 50/200">${cbLabEscape(row.sma)}</td>
      <td data-label="Intraday">${cbLabEscape(row.intraday)}</td>
    </tr>
  `).join("");

  return cbLabSurface(
    "trend",
    "Trend Structure",
    `
      <table class="data-table" aria-label="Trend Structure comparison">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Price</th>
            <th>Alignment</th>
            <th>RVOL</th>
            <th>SMA 50/200</th>
            <th>Intraday</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <p class="provenance">${cbLabEscape(fixture.trend.provenance)}</p>
    `
  );
}

function cbLabHistory(fixture) {
  const changes = cbLabSurface(
    "changes",
    "Changes Since Last Run",
    `
      <p class="history-summary">${cbLabEscape(fixture.changes.summary)}</p>
      <p class="history-detail">${cbLabEscape(fixture.changes.detail)}</p>
    `
  );

  const scoreboard = cbLabSurface(
    "scoreboard",
    "Scoreboard",
    `
      <details class="disclosure">
        <summary>Five-session calibration history</summary>
        <div class="disclosure__body scoreboard-list">
          ${fixture.scoreboard.map((row) => `
            <div class="scoreboard-row">
              <span>${cbLabEscape(row.date)}</span>
              <span>${cbLabEscape(row.regime)}</span>
              <span>${cbLabEscape(row.posture)}</span>
              <span>${cbLabEscape(row.next)}</span>
            </div>
          `).join("")}
        </div>
      </details>
    `
  );

  return { changes, scoreboard };
}

function cbLabDiagnostics(fixture) {
  return cbLabSurface(
    "diagnostics",
    "Integrity / Diagnostics",
    `
      <details class="disclosure" ${fixture.diagnostics.open ? "open" : ""}>
        <summary>${cbLabEscape(fixture.diagnostics.summary)}</summary>
        <div class="disclosure__body">
          ${cbLabKvRows(fixture.diagnostics.rows)}
        </div>
      </details>
    `,
    { note: fixture.diagnostics.open ? "ATTENTION" : "DETAIL" }
  );
}

function cbLabNotices(fixture) {
  const notices = [
    {
      status: fixture.freshness.status,
      headline: fixture.freshness.headline,
      detail: fixture.freshness.detail
    },
    ...fixture.alerts
  ];

  return `
    <div class="notice-stack" data-critical-lane>
      ${notices.map((notice) => `
        <div class="notice" data-status="${cbLabEscape(notice.status)}">
          <strong class="notice__headline">${cbLabEscape(notice.headline)}</strong>
          <span class="notice__detail">${cbLabEscape(notice.detail)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function cbLabBoardHeader(variant, fixture) {
  const descriptions = {
    a: {
      kicker: "VARIANT A · EVOLUTIONARY",
      title: "The familiar board, with a clearer voice",
      subtitle: "Current vertical architecture, lighter chrome, stronger type roles, and restored Opportunity continuity."
    },
    b: {
      kicker: "VARIANT B · ZONED COCKPIT",
      title: "Five coherent decision zones",
      subtitle: "State and Opportunity lead. Context, structure, and history remain complete but visibly subordinate."
    },
    c: {
      kicker: "VARIANT C · DENSE RESPONSIVE DESK",
      title: "Compare wide. Read narrow.",
      subtitle: "One deliberate phone column; a measured comparison desk only when the viewport can carry it."
    }
  };
  const copy = descriptions[variant];

  return `
    <header class="board-titlebar">
      <div class="board-brand">
        <p class="board-kicker">${cbLabEscape(copy.kicker)}</p>
        <h1 class="board-title">${cbLabEscape(copy.title)}</h1>
        <p class="board-subtitle">${cbLabEscape(copy.subtitle)}</p>
      </div>
      <div class="board-principle">
        <div>STATE FIRST · TRADES SECOND</div>
        <div>${cbLabEscape(fixture.label)}</div>
      </div>
    </header>
  `;
}

function cbLabRenderVariant(variant, fixture, parts) {
  const optionalState = parts.eventDetail;
  const optionalStructure = `${parts.sessionObservation}${parts.marketControl}`;

  if (variant === "a") {
    return `
      <div class="a-stack">
        ${parts.marketState}
        ${parts.systemState}
        ${optionalState}
        <div class="a-opportunity" data-zone="opportunity">
          ${parts.opportunity}
          ${parts.candidate}
        </div>
        ${parts.gex}
        ${parts.movement}
        ${parts.macro}
        ${optionalStructure}
        ${parts.trend}
        ${parts.history.changes}
        ${parts.history.scoreboard}
        ${parts.diagnostics}
      </div>
    `;
  }

  if (variant === "b") {
    return `
      <div class="b-zones">
        <section class="zone zone--state" data-zone="state" data-container="zone">
          <p class="family-label zone-title">01 · STATE</p>
          <div class="zone-grid zone-grid--state">
            ${parts.marketState}
            ${parts.systemState}
          </div>
          ${optionalState}
        </section>
        <section class="zone zone--opportunity" data-zone="opportunity" data-container="zone">
          <p class="family-label zone-title">02 · OPPORTUNITY</p>
          <div class="zone-grid zone-grid--opportunity">
            ${parts.opportunity}
            ${parts.candidate}
          </div>
        </section>
        <section class="zone zone--context" data-zone="context" data-container="zone">
          <p class="family-label zone-title">03 · CONTEXT · NEVER AUTHORIZATION</p>
          <div class="zone-grid zone-grid--context">
            ${parts.gex}
            ${parts.movement}
            ${parts.macro}
          </div>
        </section>
        <section class="zone zone--structure" data-zone="structure" data-container="zone">
          <p class="family-label zone-title">04 · STRUCTURE / SESSION</p>
          <div class="zone-grid zone-grid--structure">
            ${optionalStructure}
            ${parts.trend}
          </div>
        </section>
        <section class="zone zone--history" data-zone="history" data-container="zone">
          <p class="family-label zone-title">05 · HISTORY / DETAIL</p>
          <div class="zone-grid zone-grid--history">
            ${parts.history.changes}
            ${parts.history.scoreboard}
            ${parts.diagnostics}
          </div>
        </section>
      </div>
    `;
  }

  return `
    <div class="c-desk">
      <section class="desk-band desk-band--state" data-zone="state" data-container="band">
        <p class="family-label">STATE READ</p>
        <div class="desk-pair desk-pair--state">
          ${parts.marketState}
          ${parts.systemState}
        </div>
        ${optionalState}
      </section>
      <section class="desk-band desk-band--opportunity" data-zone="opportunity" data-container="band">
        <p class="family-label">OPPORTUNITY READ</p>
        <div class="desk-pair desk-pair--opportunity">
          ${parts.opportunity}
          ${parts.candidate}
        </div>
      </section>
      <section class="desk-band desk-band--context" data-zone="context" data-container="band">
        <p class="family-label">CONTEXT READ · NEVER AUTHORIZATION</p>
        <div class="desk-pair desk-pair--context">
          ${parts.gex}
          ${parts.movement}
        </div>
        ${parts.macro}
      </section>
      <section class="desk-band desk-band--structure" data-zone="structure" data-container="band">
        <p class="family-label">STRUCTURE / SESSION</p>
        <div class="desk-conditional">${optionalStructure}</div>
        ${parts.trend}
      </section>
      <section class="desk-band desk-band--history" data-zone="history" data-container="band">
        <p class="family-label">HISTORY / DETAIL</p>
        <div class="desk-pair desk-pair--history">
          ${parts.history.changes}
          ${parts.history.scoreboard}
        </div>
        ${parts.diagnostics}
      </section>
    </div>
  `;
}

function cbLabBuildBoard(variant, fixture) {
  const parts = {
    marketState: cbLabMarketState(fixture),
    systemState: cbLabSystemState(fixture),
    opportunity: cbLabOpportunity(fixture),
    candidate: cbLabCandidate(fixture),
    gex: cbLabGex(fixture),
    movement: cbLabMovement(fixture),
    macro: cbLabMacro(fixture),
    eventDetail: cbLabEventDetail(fixture),
    sessionObservation: cbLabSessionObservation(fixture),
    marketControl: cbLabMarketControl(fixture),
    trend: cbLabTrend(fixture),
    history: cbLabHistory(fixture),
    diagnostics: cbLabDiagnostics(fixture)
  };

  return `
    <div class="board-shell" data-board data-fixture="${cbLabEscape(fixture.slug)}">
      ${cbLabNotices(fixture)}
      ${cbLabBoardHeader(variant, fixture)}
      ${cbLabRenderVariant(variant, fixture, parts)}
    </div>
  `;
}

function cbLabSyncControls(fixtureName) {
  const select = document.querySelector("[data-fixture-select]");
  if (select) {
    select.value = fixtureName;
  }

  document.querySelectorAll("[data-variant-link]").forEach((link) => {
    const url = new URL(link.getAttribute("href"), window.location.href);
    url.searchParams.set("fixture", fixtureName);
    if (document.body.classList.contains("capture")) {
      url.searchParams.set("capture", "1");
    }
    link.href = url.href;
  });
}

function cbLabActivateFixture(requestedName) {
  const fixtureName = Object.hasOwn(window.CBLabFixtures, requestedName)
    ? requestedName
    : "normal";
  const fixture = window.CBLabFixtures[fixtureName];
  const variant = document.body.dataset.variant;
  const root = document.querySelector("[data-board-root]");

  root.innerHTML = cbLabBuildBoard(variant, fixture);
  root.setAttribute("data-active-fixture", fixtureName);
  cbLabSyncControls(fixtureName);

  const url = new URL(window.location.href);
  url.searchParams.set("fixture", fixtureName);
  window.history.replaceState({}, "", url);
  document.title = `Cuttingboard Lab · Variant ${variant.toUpperCase()} · ${fixture.label}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("capture") === "1") {
    document.body.classList.add("capture");
  }

  const initialFixture = params.get("fixture") || "normal";
  cbLabActivateFixture(initialFixture);

  const select = document.querySelector("[data-fixture-select]");
  select?.addEventListener("change", (event) => {
    cbLabActivateFixture(event.target.value);
  });
});

window.cbLabActivateFixture = cbLabActivateFixture;
