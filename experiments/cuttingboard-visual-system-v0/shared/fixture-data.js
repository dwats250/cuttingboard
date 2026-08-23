/*
 * CUTTINGBOARD VISUAL SYSTEM LAB V0
 * Static fixture catalog only. No production imports, calculations, or network calls.
 */

const CBLabBaseFixture = Object.freeze({
  slug: "normal",
  label: "NORMAL LONG-CONTENT",
  freshness: {
    status: "stale",
    headline: "BOARD 12H OLD",
    detail: "Last successful board update · 2026-08-22 21:06 PT",
    updated: "2026-08-22 21:06:15 PT",
    updatedUtc: "2026-08-23T04:06:15+00:00"
  },
  alerts: [],
  marketState: [
    {
      label: "ENVIRONMENT",
      value: "EXPANSION",
      provenance: "as of 00:49 ET"
    },
    {
      label: "PERMISSION",
      value: "No new trades permitted — operator cannot monitor.",
      provenance: "as of 00:49 ET"
    },
    {
      label: "POSITIONING",
      value: "net +$10.0B *",
      provenance: "as of 00:50 ET · Cboe ~15m delayed",
      qualifier: "* net signed under a configured positioning assumption; positioning is not measured"
    },
    {
      label: "PARTICIPATION",
      value: "12/12 captured",
      provenance: "captured 00:49 ET"
    },
    {
      label: "EVENT RISK",
      value: "no events in 48h",
      provenance: "red-folder calendar"
    }
  ],
  systemState: {
    status: "observe",
    decision: "OBSERVE ONLY",
    verdict: "OPERATOR LOCK — CANNOT MONITOR · NO TRADE",
    reason: "No new trades permitted — operator cannot monitor.",
    context: "Expansion regime",
    updated: "2026-08-22 21:06:15 PT"
  },
  opportunity: {
    surfaced: 23,
    setups: 1,
    setupsLabel: "SETUPS FOUND",
    watchlist: 13,
    rejected: 9,
    primaryRejection: "CHOP"
  },
  candidate: {
    symbol: "SPY",
    grade: "B",
    state: "DEVELOPING",
    structure: "BULLISH PULLBACK",
    level: "hold above EMA9 with constructive follow-through",
    invalidation: "loses EMA9 with weak recovery, or structure turns choppy",
    reason: "B: bullish pullback, regime aligned, near key level",
    watch: "watch hold above EMA9; look for higher low with expanding volume",
    play: "Observation only. Setup quality never overrides Decision State or Permission.",
    diagram: [
      { label: "EMA9", value: "767.79", delta: "+0.3%", position: 16 },
      { label: "NOW", value: "765.72", delta: "", position: 26 },
      { label: "EMA21", value: "763.29", delta: "-0.3%", position: 37 },
      { label: "0.382", value: "760.17", delta: "-0.7%", position: 53 },
      { label: "0.5", value: "754.24", delta: "-1.5%", position: 72 },
      { label: "EMA50", value: "752.63", delta: "-1.7%", position: 81 },
      { label: "0.618", value: "748.30", delta: "-2.3%", position: 96 }
    ]
  },
  gex: {
    rows: [
      { label: "NET", value: "+$10.0B *" },
      { label: "DOMINANT", value: "7900 · +2.94%" },
      { label: "CALL WALL", value: "8000 · +4.24%" },
      { label: "PUT WALL", value: "8000 · +4.24%" },
      { label: "0DTE", value: "0.0%" }
    ],
    provenance: "as of 00:50 ET · Cboe ~15m delayed source",
    qualifier: "* net is signed under a configured positioning assumption; positioning is not measured."
  },
  movement: {
    rows: [
      { label: "INDEX", value: "SPY +0.4% · QQQ +0.4%" },
      { label: "METALS", value: "GDX +3.1% · GLD +2.0% · SLV +1.7%" },
      { label: "ENERGY", value: "XLE -0.3% · UCO +1.3%" },
      { label: "TECH", value: "NVDA -1.1% · META +0.7% · AMZN -0.7% · GOOG +1.1%" },
      { label: "HIGH_BETA", value: "TSLA +4.8%" }
    ],
    provenance: "12/12 captured · captured 00:49 ET"
  },
  macro: {
    bias: "SHORT",
    tally: "Risk votes: 3 off / 1 on → SHORT",
    pressures: [
      "VIX permits longs",
      "DXY pressures longs",
      "BTC pressures risk-on"
    ],
    drivers: [
      { label: "GC", direction: "↑", value: "4680.6" },
      { label: "SI", direction: "↑", value: "69.53" },
      { label: "BTC", direction: "↓", value: "76.6K" },
      { label: "VIX", direction: "↓", value: "15.1" },
      { label: "DXY", direction: "↑", value: "98.8" },
      { label: "10Y", direction: "↑", value: "4.74" },
      { label: "OIL", direction: "↑", value: "87.1" }
    ],
    tradables: [
      { label: "SPY", value: "765.72" },
      { label: "QQQ", value: "713.44" },
      { label: "GLD", value: "423.36" },
      { label: "GDX", value: "102.83" },
      { label: "SLV", value: "62.72" },
      { label: "XLE", value: "63.64" }
    ],
    provenance: "macro carriers retain their own source clocks; values shown are context only"
  },
  eventDetail: null,
  sessionObservation: null,
  marketControl: null,
  trend: {
    provenance: "daily structure snapshot · intraday column unavailable",
    rows: [
      { symbol: "SPY", price: "765.72", alignment: "BULL", rvol: "0.84", sma: "↑ 50 · ↑ 200", intraday: "VWAP N/A" },
      { symbol: "QQQ", price: "713.44", alignment: "BULL", rvol: "0.83", sma: "↑ 50 · ↑ 200", intraday: "VWAP N/A" },
      { symbol: "GDX", price: "102.83", alignment: "BULL", rvol: "1.43", sma: "↑ 50 · ↑ 200", intraday: "VWAP N/A" },
      { symbol: "GLD", price: "423.36", alignment: "BULL", rvol: "1.58", sma: "↑ 50 · ↑ 200", intraday: "VWAP N/A" },
      { symbol: "SLV", price: "62.72", alignment: "MIX", rvol: "1.46", sma: "↑ 50 · ↓ 200", intraday: "VWAP N/A" },
      { symbol: "XLE", price: "63.64", alignment: "BULL", rvol: "1.02", sma: "↑ 50 · ↑ 200", intraday: "VWAP N/A" }
    ]
  },
  changes: {
    summary: "No changes since last run",
    detail: "Environment, permission, candidate state, and context values are unchanged."
  },
  scoreboard: [
    { date: "2026-08-23", regime: "EXPANSION", posture: "Expansion Long", next: "SPY next n/a" },
    { date: "2026-08-21", regime: "EXPANSION", posture: "Expansion Long", next: "SPY next n/a" },
    { date: "2026-08-20", regime: "RISK_OFF", posture: "Stay Flat", next: "SPY next +0.41%" },
    { date: "2026-08-19", regime: "RISK_ON", posture: "Stay Flat", next: "SPY next -0.84%" },
    { date: "2026-08-18", regime: "RISK_OFF", posture: "Stay Flat", next: "SPY next +0.21%" }
  ],
  diagnostics: {
    open: false,
    summary: "Diagnostics",
    rows: [
      { label: "PAYLOAD", value: "coherent · generation 2026-08-23T04:06Z" },
      { label: "STATE CARRIER", value: "available · 00:49 ET" },
      { label: "GEX CARRIER", value: "available · 00:50 ET · delayed" },
      { label: "MOVEMENT CARRIER", value: "available · 00:49 ET" },
      { label: "RED FOLDER", value: "available · no events in 48h" }
    ]
  }
});
window.CBLabFixtures = Object.freeze({
  normal: CBLabBaseFixture,

  halt: Object.freeze({
    ...CBLabBaseFixture,
    slug: "halt",
    label: "HALT",
    alerts: [
      {
        status: "halt",
        headline: "SYSTEM HALT",
        detail: "Execution failed closed · current context remains informational only"
      }
    ],
    marketState: [
      CBLabBaseFixture.marketState[0],
      {
        label: "PERMISSION",
        value: "No new trades permitted — system halted.",
        provenance: "as of 00:49 ET"
      },
      CBLabBaseFixture.marketState[2],
      CBLabBaseFixture.marketState[3],
      CBLabBaseFixture.marketState[4]
    ],
    systemState: {
      status: "halt",
      decision: "HALT",
      verdict: "SYSTEM HALT · NO TRADE",
      reason: "disk full",
      context: "Execution stopped. Context does not authorize action.",
      updated: "2026-08-22 21:06:15 PT"
    },
    sessionObservation: {
      state: "UNAVAILABLE — SYSTEM_HALTED",
      provenance: "intended session 2026-08-23 · America/New_York",
      rows: []
    },
    diagnostics: {
      open: true,
      summary: "Halt diagnostics",
      rows: [
        { label: "STATUS", value: "FAIL" },
        { label: "ERROR", value: "disk full" },
        { label: "EXECUTION", value: "failed closed" },
        { label: "CONTEXT", value: "retained for operator inspection only" }
      ]
    }
  }),

  degraded: Object.freeze({
    ...CBLabBaseFixture,
    slug: "degraded",
    label: "DEGRADED / CARRIER UNAVAILABLE",
    alerts: [
      {
        status: "degraded",
        headline: "PRIMARY STATE CARRIER UNAVAILABLE",
        detail: "Current permission cannot be verified · no authorization inferred from context"
      }
    ],
    marketState: [
      {
        label: "ENVIRONMENT",
        value: "EXPANSION · LAST KNOWN",
        provenance: "state carrier last observed 00:49 ET"
      },
      {
        label: "PERMISSION",
        value: "UNAVAILABLE",
        provenance: "primary state carrier unavailable"
      },
      CBLabBaseFixture.marketState[2],
      CBLabBaseFixture.marketState[3],
      CBLabBaseFixture.marketState[4]
    ],
    systemState: {
      status: "degraded",
      decision: "STATE UNAVAILABLE",
      verdict: "NO AUTHORIZATION — CARRIER UNAVAILABLE",
      reason: "Current permission cannot be verified.",
      context: "GEX, Movement, and Red Folder retain independent source clocks.",
      updated: "2026-08-22 21:06:15 PT"
    },
    candidate: {
      ...CBLabBaseFixture.candidate,
      state: "DEVELOPING · LAST KNOWN",
      play: "Candidate content is retained for diagnosis only. State unavailability never becomes permission."
    },
    diagnostics: {
      open: true,
      summary: "Carrier diagnostics",
      rows: [
        { label: "PAYLOAD", value: "degraded · primary state carrier unavailable" },
        { label: "STATE CARRIER", value: "UNAVAILABLE · last observed 00:49 ET" },
        { label: "GEX CARRIER", value: "available · 00:50 ET · delayed" },
        { label: "MOVEMENT CARRIER", value: "available · 00:49 ET" },
        { label: "RED FOLDER", value: "available · no events in 48h" }
      ]
    }
  }),

  event: Object.freeze({
    ...CBLabBaseFixture,
    slug: "event",
    label: "RED-FOLDER EVENT PRESENT",
    alerts: [
      {
        status: "event",
        headline: "RED-FOLDER EVENT · CPI",
        detail: "2026-08-24 08:30 ET · event context does not change permission"
      }
    ],
    marketState: [
      CBLabBaseFixture.marketState[0],
      CBLabBaseFixture.marketState[1],
      CBLabBaseFixture.marketState[2],
      CBLabBaseFixture.marketState[3],
      {
        label: "EVENT RISK",
        value: "1 red-folder event in 48h",
        provenance: "calendar captured 00:48 ET"
      }
    ],
    eventDetail: {
      status: "event",
      headline: "CPI (July)",
      when: "2026-08-24 08:30 ET",
      type: "INFLATION",
      provenance: "red-folder calendar · captured 00:48 ET"
    },
    sessionObservation: {
      state: "OBSERVED",
      provenance: "2026-08-23 · America/New_York · observed 09:35 ET",
      rows: [
        { label: "CURRENT", value: "104.00" },
        { label: "SESSION VWAP", value: "102.00 · ABOVE VWAP" },
        { label: "ORB", value: "FORMED [100.00, 105.00]" }
      ]
    },
    marketControl: {
      provenance: "daily context · present only when its own section is available",
      rows: [
        { label: "LOCATION", value: "ABOVE VWAP · FORMED [100.00, 105.00]" },
        { label: "STATE", value: "RANGE" },
        { label: "PERMISSION", value: "Selective only — defined risk, R:R >= 3:1." },
        { label: "EVENT", value: "2026-08-24 08:30 ET — CPI: CPI (July)" },
        { label: "TRANSITION", value: "NO_BREAK" },
        { label: "INVALIDATION", value: "NO_ACTIVE_CANDIDATES" },
        { label: "CANDIDATE-IMPLICATION", value: "CANDIDATES_PRESENT_NONE_ACTIONABLE (ACTIVE 1 / NEAR_MISS 0 / BLOCKED 0)" }
      ]
    },
    changes: {
      summary: "Event risk changed: CPI entered the 48h window",
      detail: "Permission remains unchanged. Event context may inform; it does not authorize."
    }
  }),

  "no-candidate": Object.freeze({
    ...CBLabBaseFixture,
    slug: "no-candidate",
    label: "NO CANDIDATE",
    opportunity: {
      surfaced: 23,
      setups: 0,
      setupsLabel: "SETUPS FOUND",
      watchlist: 13,
      rejected: 10,
      primaryRejection: "CHOP"
    },
    candidate: null,
    changes: {
      summary: "Candidate removed: SPY no longer meets developing criteria",
      detail: "The opportunity zone remains present and explicitly reports no developing setups."
    },
    marketControl: {
      provenance: "daily context · does not replace the empty candidate state",
      rows: [
        { label: "LOCATION", value: "ABOVE VWAP" },
        { label: "STATE", value: "RANGE" },
        { label: "PERMISSION", value: "Observe only — current System State remains authoritative." },
        { label: "EVENT", value: "NO_EVENTS_48H" },
        { label: "TRANSITION", value: "NO_BREAK" },
        { label: "INVALIDATION", value: "NO_ACTIVE_CANDIDATES" },
        { label: "CANDIDATE-IMPLICATION", value: "NO_CANDIDATES_PRESENT" }
      ]
    }
  })
});
