import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test, { after, before } from "node:test";

import {
  closeTarget,
  configureViewport,
  createTarget,
  enablePageRuntime,
  evaluate,
  injectCss,
  launchChrome,
  navigateFile,
  setRootFontScale,
  shutdownChrome
} from "../runner/cdp.mjs";
import { classifyObservation } from "../runner/checks.mjs";
import {
  MANDATORY_VIEWPORTS,
  SCALE_MODES,
  caseKey,
  expandMatrix,
  screenshotStem
} from "../runner/matrix.mjs";
import { buildProbeExpression } from "../runner/probe.mjs";
import {
  compareCasePair,
  stableStringify
} from "../runner/report.mjs";

const testsDirectory = fileURLToPath(new URL(".", import.meta.url));
const labRoot = join(testsDirectory, "..");
const selfTestRoot = join(labRoot, "fixtures", "self-test");
const catalog = JSON.parse(
  await readFile(join(labRoot, "fixtures", "catalog.json"), "utf8")
);
const currentmainCatalog = JSON.parse(
  await readFile(join(labRoot, "fixtures", "currentmain-catalog.json"), "utf8")
);
const candidateCssText = (
  await readFile(join(labRoot, "prototypes", "opportunity-125.css"), "utf8")
).trim();

let chrome = null;

before(async () => {
  // A missing/broken Chrome installation is an infrastructure failure. Do not
  // turn it into a skipped calibration suite.
  chrome = await launchChrome();
});

after(async () => {
  const runningChrome = chrome;
  chrome = null;
  if (runningChrome) await shutdownChrome(runningChrome);
});

function rawObservation(overrides = {}) {
  return {
    viewport: { width: 360, height: 800, rootFontSize: "16px" },
    page: { overflowX: 0 },
    elements: {},
    opportunityValues: {},
    text: { body: "", byKey: {} },
    dom: { surfaceOrder: [] },
    geometry: {},
    fold: { intersecting: [], fullyAbove: [] },
    ...overrides
  };
}

function elementMeasurement(overrides = {}) {
  return {
    present: true,
    rect: { top: 0, right: 96, bottom: 24, left: 0, width: 96, height: 24 },
    clientWidth: 96,
    scrollWidth: 96,
    clientHeight: 24,
    scrollHeight: 24,
    display: "block",
    visibility: "visible",
    opacity: 1,
    overflowX: "visible",
    directlyHidden: false,
    zeroSize: false,
    hiddenByAncestor: [],
    clippedByAncestor: [],
    nonScrollHorizontalOverflow: false,
    nonScrollVerticalOverflow: false,
    textExitsBoxX: false,
    textExitsBoxY: false,
    wraps: false,
    ...overrides
  };
}

function classificationFor(raw, expected, defaults = {}) {
  return classifyObservation(raw, { id: "self-test", expected }, defaults);
}

async function measure(fileName, viewport, contract = {}, root = selfTestRoot, scale = 100) {
  assert.ok(chrome, "Chrome must be running for browser integration tests");
  const target = await createTarget(chrome);
  try {
    await enablePageRuntime(target);
    await configureViewport(target, viewport.width, viewport.height);
    await navigateFile(target, join(root, fileName));
    await setRootFontScale(target, scale);
    return await evaluate(target, buildProbeExpression(contract));
  } finally {
    await closeTarget(target);
  }
}

function fixtureContract(fileName) {
  const selectors = {
    critical: '[data-lab-key="critical"]',
    first: '[data-lab-key="first"]',
    second: '[data-lab-key="second"]',
    missing: '[data-lab-key="missing"]'
  };
  if (fileName === "horizontal-overflow.html") return { selectors: {} };
  if (fileName === "cell-clipping.html" || fileName === "wrapped-readable.html" ||
      fileName === "hidden-critical.html") {
    return { selectors: { critical: selectors.critical } };
  }
  return { selectors, surfaceKeys: ["first", "second"] };
}

test("catalog contains the exact core and total fixture set", () => {
  const core = new Set([
    "normal",
    "halt",
    "operator-lock",
    "state-unavailable",
    "candidate-carrier-unavailable",
    "gex-unavailable",
    "movement-unavailable",
    "red-folder-event",
    "healthy-empty-red-folder",
    "no-candidate",
    "multiple-candidates",
    "opportunity-suppressed",
    "qualified-zero-b-candidate",
    "stale-board",
    "inactive-session"
  ]);
  assert.equal(catalog.fixtures.length, 35);
  assert.deepEqual(
    new Set(catalog.fixtures.filter((fixture) => fixture.groups?.includes("core")).map((fixture) => fixture.id)),
    core
  );
  assert.equal(new Set(catalog.fixtures.map((fixture) => fixture.id)).size, 35);
});

test("expandMatrix has 438 deterministic cases and covers 430/431 at every scale", () => {
  const cases = expandMatrix(catalog);
  assert.equal(cases.length, 438);
  assert.deepEqual(MANDATORY_VIEWPORTS.map(({ width, height }) => `${width}x${height}`), [
    "360x800", "390x844", "430x932", "431x932", "768x1024", "960x900", "1280x800", "1440x900"
  ]);
  assert.deepEqual(SCALE_MODES, [100, 125, 150, 200]);
  const normalBoundaryCells = cases.filter((entry) =>
    entry.fixture.id === "normal" && (entry.viewport.width === 430 || entry.viewport.width === 431)
  );
  assert.equal(normalBoundaryCells.length, 8);
  assert.deepEqual(
    normalBoundaryCells.map((entry) => `${entry.viewport.width}:${entry.scale}`),
    ["430:100", "430:125", "430:150", "430:200", "431:100", "431:125", "431:150", "431:200"]
  );
  assert.equal(caseKey("normal", { width: 430, height: 932 }, 100), "normal__430x932__scale-100");
});

test("stableStringify is byte-stable, rounds measurements, and sorts object keys", () => {
  const left = {
    z: 1.234,
    nested: { beta: 2.345, alpha: 1.234 },
    list: [{ z: 9.876, a: 0.004 }],
    a: "first"
  };
  const right = {
    a: "first",
    list: [{ a: 0.004, z: 9.876 }],
    nested: { alpha: 1.234, beta: 2.345 },
    z: 1.234
  };
  const firstBytes = Buffer.from(stableStringify(left), "utf8");
  const secondBytes = Buffer.from(stableStringify(right), "utf8");
  assert.deepEqual(firstBytes, secondBytes);
  assert.equal(stableStringify(left), [
    "{",
    "  \"a\": \"first\",",
    "  \"list\": [",
    "    {",
    "      \"a\": 0,",
    "      \"z\": 9.9",
    "    }",
    "  ],",
    "  \"nested\": {",
    "    \"alpha\": 1.2,",
    "    \"beta\": 2.3",
    "  },",
    "  \"z\": 1.2",
    "}",
    ""
  ].join("\n"));
});

test("classifier detects overflow, critical clipping, hidden critical, wrong order, and missing expected", () => {
  const overflow = classificationFor(rawObservation({ page: { overflowX: 4 } }), {});
  assert.equal(overflow.verdict, "FAIL");
  assert.ok(overflow.checks.some((check) => check.id === "page-horizontal-overflow" && check.status === "FAIL"));

  const clipped = classificationFor(rawObservation({
    elements: { critical: elementMeasurement({
      scrollWidth: 240,
      overflowX: "hidden",
      nonScrollHorizontalOverflow: true
    }) }
  }), { criticalKeys: ["critical"] });
  assert.equal(clipped.verdict, "FAIL");
  assert.ok(clipped.checks.some((check) => check.id === "critical-horizontal-clipping:critical" && check.status === "FAIL"));

  const hidden = classificationFor(rawObservation({
    elements: { critical: elementMeasurement({ directlyHidden: true, visibility: "hidden" }) }
  }), { criticalKeys: ["critical"] });
  assert.equal(hidden.verdict, "FAIL");
  assert.ok(hidden.checks.some((check) => check.id === "critical-visible:critical" && check.status === "FAIL"));

  const wrongOrder = classificationFor(rawObservation({ dom: { surfaceOrder: ["second", "first"] } }), {
    order: ["first", "second"]
  });
  assert.equal(wrongOrder.verdict, "FAIL");
  assert.ok(wrongOrder.checks.some((check) => check.id === "top-level-authority-order" && check.status === "FAIL"));

  const missing = classificationFor(rawObservation(), { presence: { missing: "present" } });
  assert.equal(missing.verdict, "FAIL");
  assert.ok(missing.checks.some((check) => check.id === "presence:missing" && check.status === "FAIL"));

  const tooFewCards = classificationFor(rawObservation({
    candidateStats: { cardCount: 1, cardIds: ["card-SPY"] }
  }), { candidate: { minimumCards: 2 } });
  assert.equal(tooFewCards.verdict, "FAIL");
  assert.ok(tooFewCards.checks.some((check) =>
    check.id === "candidate-minimum-card-count" && check.status === "FAIL"
  ));
});

test("classifier does not call visible surface bleed clipping", () => {
  const visibleBleed = classificationFor(rawObservation({
    elements: { critical: elementMeasurement({
      scrollWidth: 106,
      overflowX: "visible",
      nonScrollHorizontalOverflow: true,
      textExitsBoxX: false
    }) }
  }), { criticalKeys: ["critical"] });
  assert.notEqual(visibleBleed.verdict, "FAIL");
  assert.equal(
    visibleBleed.checks.find((check) => check.id === "critical-horizontal-clipping:critical").status,
    "PASS"
  );
});

test("classifier does not fail readable wrapping", () => {
  const wrapped = classificationFor(rawObservation({
    elements: { critical: elementMeasurement({ wraps: true, scrollHeight: 48, clientHeight: 48 }) }
  }), { criticalKeys: ["critical"] });
  assert.notEqual(wrapped.verdict, "FAIL");
  assert.equal(wrapped.checks.find((check) => check.id === "critical-horizontal-clipping:critical").status, "PASS");
  assert.equal(wrapped.checks.find((check) => check.id === "critical-vertical-clipping:critical").status, "PASS");
});

test("comparison reports candidate disappearance and keeps resolved clipping informational", () => {
  const before = {
    key: "case",
    fixture: "fixture",
    viewport: { width: 360, height: 800 },
    scale: 100,
    checks: [{ id: "critical-horizontal-clipping:candidate", severity: "FAIL", status: "FAIL", message: "clipped" }],
    raw: {
      page: { overflowX: 0 },
      elements: {
        candidate: { present: true },
        candidateIdentity: { present: true },
        candidateLevel: { present: true },
        candidateInvalidation: { present: true }
      },
      text: { byKey: {} },
      dom: { surfaceOrder: ["candidate"] },
      geometry: {}
    }
  };
  const after = {
    ...before,
    checks: [],
    raw: {
      ...before.raw,
      elements: {
        candidate: { present: false },
        candidateIdentity: { present: false },
        candidateLevel: { present: false },
        candidateInvalidation: { present: false }
      }
    }
  };
  const comparison = compareCasePair(before, after);
  assert.equal(comparison.verdict, "FAIL");
  assert.ok(comparison.failures.some((message) => message.includes("candidate discoverability regressed")));
  assert.deepEqual(comparison.clipping.new, []);
  assert.deepEqual(comparison.clipping.resolved, ["critical-horizontal-clipping:candidate"]);
});

test("screenshot naming is deterministic", () => {
  assert.equal(
    screenshotStem("cell-clipping", { width: 360, height: 800 }, 100, "FAIL"),
    "cell-clipping__360x800__scale-100__fail"
  );
  assert.equal(
    screenshotStem("normal", { width: 431, height: 932 }, 125, "PASS"),
    "normal__431x932__scale-125__pass"
  );
});

test("Chrome measures every static self-test detector at 360px", async () => {
  const cases = [
    ["horizontal-overflow.html", {}, (raw, result) => {
      assert.ok(raw.page.overflowX > 1);
      assert.equal(result.verdict, "FAIL");
    }],
    ["cell-clipping.html", { criticalKeys: ["critical"] }, (raw, result) => {
      assert.ok(raw.elements.critical.nonScrollHorizontalOverflow);
      assert.equal(result.verdict, "FAIL");
    }],
    ["wrapped-readable.html", { criticalKeys: ["critical"] }, (raw, result) => {
      assert.equal(raw.elements.critical.wraps, true);
      assert.equal(result.verdict, "PASS");
    }],
    ["hidden-critical.html", { criticalKeys: ["critical"] }, (raw, result) => {
      assert.equal(raw.elements.critical.directlyHidden, true);
      assert.equal(result.verdict, "FAIL");
    }],
    ["wrong-order.html", { order: ["first", "second"] }, (raw, result) => {
      assert.deepEqual(raw.dom.surfaceOrder, ["second", "first"]);
      assert.equal(result.verdict, "FAIL");
    }],
    ["missing-expected.html", { presence: { missing: "present" } }, (raw, result) => {
      assert.equal(raw.elements.missing.present, false);
      assert.equal(result.verdict, "FAIL");
    }]
  ];
  for (const [fileName, expected, verify] of cases) {
    const raw = await measure(fileName, { width: 360, height: 800 }, fixtureContract(fileName));
    verify(raw, classificationFor(raw, expected));
  }
});

test("Chrome reports the 430/431 breakpoint transition", async () => {
  const contract = { selectors: { boundary: '[data-lab-key="boundary"]' } };
  const at430 = await measure("breakpoint.html", { width: 430, height: 800 }, contract);
  const at431 = await measure("breakpoint.html", { width: 431, height: 800 }, contract);
  assert.equal(at430.boundary.marker, "narrow");
  assert.equal(at431.boundary.marker, "wide");
  assert.notEqual(at430.boundary.rect.width, at431.boundary.rect.width);
});

async function measureDomainFixture(id, width, scale = 100) {
  const fixture = catalog.fixtures.find((entry) => entry.id === id);
  assert.ok(fixture, `catalog fixture ${id} must exist`);
  const raw = await measure(join("fixtures", fixture.file), {
    width,
    height: width === 360 ? 800 : 932
  }, {
    ...(catalog.defaults || {}),
    ...(fixture.probe || {})
  }, labRoot, scale);
  return { fixture, raw, result: classifyObservation(raw, fixture, catalog.defaults || {}) };
}

test("PRD-314 pre-fix/current domain fixtures preserve the exact clipping calibration", async () => {
  const pre360 = await measureDomainFixture("prd314-prefixt-23-13", 360);
  const current360 = await measureDomainFixture("prd314-current-23-13", 360);
  // On the Chrome 151 host used by this lab, font metrics keep the historical
  // four-column grid readable at 360/100. At the accessibility-pressure scale,
  // the same pre-fix grid collapses the two value cells and exposes the intended
  // clipping regression; do not manufacture a 100% failure.
  const pre360Scale125 = await measureDomainFixture("prd314-prefixt-23-13", 360, 125);
  const current360Scale125 = await measureDomainFixture("prd314-current-23-13", 360, 125);
  const pre431 = await measureDomainFixture("prd314-prefixt-23-13", 431);
  const current431 = await measureDomainFixture("prd314-current-23-13", 431);
  const required = new Set([
    "critical-horizontal-clipping:opportunity:SURFACED",
    "critical-horizontal-clipping:opportunity:WATCHLIST"
  ]);
  assert.equal(pre360.result.verdict, "PASS");
  assert.equal(current360.result.verdict, "PASS");
  const preFailures = pre360Scale125.result.checks
    .filter((check) => check.status === "FAIL" && check.severity === "FAIL")
    .map((check) => check.id);
  for (const id of required) assert.ok(preFailures.includes(id), `pre-fix 360/125 must fail ${id}`);
  const currentTargetedFailures = new Set(current360Scale125.result.checks
    .filter((check) => check.status === "FAIL" && check.severity === "FAIL")
    .map((check) => check.id)
    .filter((id) => required.has(id)));
  assert.deepEqual(currentTargetedFailures, new Set());
  assert.equal(pre431.result.verdict, "PASS");
  assert.equal(current431.result.verdict, "PASS");
});

// --- Opportunity 125% prototype: current-main content + candidate CSS override ---

async function measureCurrentMain(id, viewport, scale, { inject = false } = {}) {
  const fixture = currentmainCatalog.fixtures.find((entry) => entry.id === id);
  assert.ok(fixture, `current-main fixture ${id} must exist`);
  const target = await createTarget(chrome);
  try {
    await enablePageRuntime(target);
    await configureViewport(target, viewport.width, viewport.height);
    await navigateFile(target, join(labRoot, "fixtures", fixture.file));
    await setRootFontScale(target, scale);
    let injection = null;
    if (inject) injection = await injectCss(target, candidateCssText);
    const raw = await evaluate(target, buildProbeExpression({
      ...(currentmainCatalog.defaults || {}),
      ...(fixture.probe || {})
    }));
    const result = classifyObservation(raw, fixture, currentmainCatalog.defaults || {});
    return { fixture, raw, result, injection };
  } finally {
    await closeTarget(target);
  }
}

test("candidate CSS resolves Opportunity 125% overflow, and removing it reintroduces it (red test)", async () => {
  // Worst case: operator-lock SETUPS FOUND + PRIMARY REJECTION at 360x800/125.
  const before = await measureCurrentMain("operator-lock", { width: 360, height: 800 }, 125);
  assert.ok(before.raw.page.overflowX > 1,
    `operator-lock 360/125 must overflow the page without the fix (saw ${before.raw.page.overflowX}px)`);
  assert.equal(before.result.verdict, "FAIL");

  const after = await measureCurrentMain("operator-lock", { width: 360, height: 800 }, 125, { inject: true });
  assert.equal(after.injection.injected, true);
  assert.ok(after.raw.page.overflowX <= 1,
    `candidate CSS must remove page overflow (saw ${after.raw.page.overflowX}px)`);
  assert.equal(after.result.verdict, "PASS");

  // Values remain readable (no clipping) with the fix applied.
  const surfaced = after.raw.opportunityValues?.SURFACED;
  assert.equal(String(surfaced?.text).trim(), "23");
});

test("candidate override is media-scoped: it changes the grid under phone pressure and is inert at 431", async () => {
  // Read at a fixed 800px height so 360 and 431 are the only variable.
  const readColumns = async (width, inject) => {
    const target = await createTarget(chrome);
    try {
      await enablePageRuntime(target);
      await configureViewport(target, width, 800);
      await navigateFile(target, join(labRoot, "fixtures", "currentmain", "operator-lock.html"));
      await setRootFontScale(target, 125);
      if (inject) await injectCss(target, candidateCssText);
      return await evaluate(target,
        "getComputedStyle(document.querySelector('#opportunity-survival .kv-grid')).gridTemplateColumns");
    } finally {
      await closeTarget(target);
    }
  };
  // 360px is inside @media(max-width:430) and under real overflow pressure, so
  // the label tracks (max-content -> auto) resolve to different widths.
  const at360Plain = await readColumns(360, false);
  const at360Fixed = await readColumns(360, true);
  // 431px is outside the phone media query entirely; the injected @media rule
  // never applies, so it is inert.
  const at431Plain = await readColumns(431, false);
  const at431Fixed = await readColumns(431, true);
  assert.notEqual(at360Fixed, at360Plain,
    "override must shrink the Opportunity label tracks under 360px/125 pressure");
  assert.equal(at431Fixed, at431Plain,
    "override must be inert at 431px (outside @media max-width:430)");
});

test("runtime candidate injection never mutates the source HTML bytes", async () => {
  const sourcePath = join(labRoot, "fixtures", "currentmain", "operator-lock.html");
  const before = createHash("sha256").update(await readFile(sourcePath)).digest("hex");
  await measureCurrentMain("operator-lock", { width: 360, height: 800 }, 125, { inject: true });
  const after = createHash("sha256").update(await readFile(sourcePath)).digest("hex");
  assert.equal(after, before, "candidate CSS is a runtime override; the fixture bytes must be unchanged");
});

test("current-main authority order is truthful under PRD-315; the pre-PRD-315 order is a red test", async () => {
  const { raw, result } = await measureCurrentMain("normal", { width: 390, height: 844 }, 100);
  const order = raw.dom.surfaceOrder;
  assert.equal(order.indexOf("candidate"), order.indexOf("opportunity") + 1,
    "current main renders candidate immediately after opportunity");
  assert.ok(!result.failures.some((message) => message.startsWith("wrong DOM authority order")),
    "current-main catalog order must PASS on current-main render");

  // Red test: the reusable lab's pre-PRD-315 order (candidate after trend) must
  // FAIL against current-main content -- exactly the calibration bug corrected.
  const preOrder = [
    "marketState", "systemState", "opportunity", "gex", "movement",
    "macro", "redFolder", "trend", "candidate", "runDelta", "scoreboard"
  ];
  const normalFixture = currentmainCatalog.fixtures.find((entry) => entry.id === "normal");
  const red = classifyObservation(
    raw,
    { id: "normal", expected: { ...normalFixture.expected, order: preOrder } },
    currentmainCatalog.defaults || {}
  );
  assert.ok(red.failures.some((message) => message.startsWith("wrong DOM authority order")),
    "pre-PRD-315 order must FAIL on current-main render");
});

test("candidate CSS is Opportunity-scoped, media-bounded, and free of forbidden techniques", () => {
  const css = candidateCssText;
  assert.ok(css.includes("@media (max-width: 430px)"), "must stay within the phone breakpoint");
  assert.ok(css.includes("#opportunity-survival .kv-grid"), "must reuse the Opportunity selector");
  assert.ok(css.includes("minmax(2.5ch, 1fr)"), "must preserve PRD-314 value floor");
  const forbidden = [
    /display\s*:\s*none/i,
    /visibility\s*:\s*hidden/i,
    /overflow[a-z-]*\s*:\s*(scroll|auto)/i,
    /text-overflow/i,
    /ellipsis/i,
    /white-space\s*:\s*nowrap/i,
    /font-size/i,
    /#market-state/i,
    /#system-state/i,
    /#gex-context/i
  ];
  for (const pattern of forbidden) {
    assert.ok(!pattern.test(css), `candidate CSS must not use ${pattern}`);
  }
});

test("committed prototype report is byte-stable under re-normalization", async () => {
  const path = join(labRoot, "reports", "opportunity-125-prototype.json");
  const committed = await readFile(path, "utf8");
  const reNormalized = stableStringify(JSON.parse(committed));
  assert.equal(reNormalized, committed, "prototype report must already be in normalized form");
});
