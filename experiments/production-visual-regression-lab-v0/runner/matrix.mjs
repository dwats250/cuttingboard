export const MANDATORY_VIEWPORTS = Object.freeze([
  Object.freeze({ width: 360, height: 800 }),
  Object.freeze({ width: 390, height: 844 }),
  Object.freeze({ width: 430, height: 932 }),
  Object.freeze({ width: 431, height: 932 }),
  Object.freeze({ width: 768, height: 1024 }),
  Object.freeze({ width: 960, height: 900 }),
  Object.freeze({ width: 1280, height: 800 }),
  Object.freeze({ width: 1440, height: 900 })
]);

export const SCALE_MODES = Object.freeze([100, 125, 150, 200]);

const REPRESENTATIVE_VIEWPORTS = Object.freeze([
  MANDATORY_VIEWPORTS[1],
  MANDATORY_VIEWPORTS[6]
]);

const PRESSURE_VIEWPORTS = Object.freeze([
  MANDATORY_VIEWPORTS[0],
  MANDATORY_VIEWPORTS[2],
  MANDATORY_VIEWPORTS[3],
  MANDATORY_VIEWPORTS[6]
]);

const CALIBRATION_VIEWPORTS = Object.freeze([
  MANDATORY_VIEWPORTS[0],
  MANDATORY_VIEWPORTS[1],
  MANDATORY_VIEWPORTS[2],
  MANDATORY_VIEWPORTS[3]
]);

const SELECTED_SCREENSHOT_FIXTURES = new Set([
  "halt",
  "state-unavailable",
  "red-folder-event",
  "no-candidate"
]);

const REQUIRED_CORE_FIXTURES = Object.freeze([
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

function viewportKey(viewport) {
  return `${viewport.width}x${viewport.height}`;
}

function matrixViewports(name) {
  if (name === "all") return MANDATORY_VIEWPORTS;
  if (name === "representative") return REPRESENTATIVE_VIEWPORTS;
  if (name === "pressure") return PRESSURE_VIEWPORTS;
  if (name === "calibration") return CALIBRATION_VIEWPORTS;
  throw new Error(`Unknown fixture matrix: ${name}`);
}

export function caseKey(fixtureId, viewport, scale) {
  return `${fixtureId}__${viewportKey(viewport)}__scale-${scale}`;
}

export function screenshotStem(fixtureId, viewport, scale, verdict) {
  return `${fixtureId}__${viewportKey(viewport)}__scale-${scale}__${verdict.toLowerCase()}`;
}

export function selectedBaselineScreenshot(caseEntry) {
  if (caseEntry.scale !== 100) return false;
  if (caseEntry.fixture.id === "normal") return true;
  return SELECTED_SCREENSHOT_FIXTURES.has(caseEntry.fixture.id) &&
    (caseEntry.viewport.width === 390 || caseEntry.viewport.width === 1280);
}

export function validateCatalogCoverage(catalog) {
  const fixtures = catalog.fixtures || [];
  const ids = new Set(fixtures.map((fixture) => fixture.id));
  const missingCore = REQUIRED_CORE_FIXTURES.filter((id) => !ids.has(id));
  if (missingCore.length) {
    throw new Error(`Catalog missing core fixtures: ${missingCore.join(", ")}`);
  }

  const normal = fixtures.find((fixture) => fixture.id === "normal");
  if (normal?.matrix !== "all") {
    throw new Error("NORMAL must use the full mandatory viewport/scale matrix");
  }

  const viewportSet = new Set(
    (catalog.viewports || MANDATORY_VIEWPORTS).map(viewportKey)
  );
  const missingViewports = MANDATORY_VIEWPORTS
    .map(viewportKey)
    .filter((key) => !viewportSet.has(key));
  if (missingViewports.length) {
    throw new Error(`Catalog missing mandatory viewports: ${missingViewports.join(", ")}`);
  }

  const scaleSet = new Set(catalog.scales || SCALE_MODES);
  const missingScales = SCALE_MODES.filter((scale) => !scaleSet.has(scale));
  if (missingScales.length) {
    throw new Error(`Catalog missing scale modes: ${missingScales.join(", ")}`);
  }

  const coverTokens = new Set(fixtures.flatMap((fixture) => fixture.covers || []));
  const requiredCoverTokens = catalog.requiredCoverage || [];
  const missingCoverage = requiredCoverTokens.filter((token) => !coverTokens.has(token));
  if (missingCoverage.length) {
    throw new Error(`Catalog missing torture coverage: ${missingCoverage.join(", ")}`);
  }
}

export function expandMatrix(catalog, { quick = false, fixtureIds = null } = {}) {
  validateCatalogCoverage(catalog);
  const selectedIds = fixtureIds ? new Set(fixtureIds) : null;
  const fixtures = [...catalog.fixtures]
    .filter((fixture) => !selectedIds || selectedIds.has(fixture.id))
    .sort((left, right) => left.id.localeCompare(right.id));
  const cases = [];

  for (const fixture of fixtures) {
    let runPlan = fixture.runPlan || null;
    let viewports = runPlan
      ? runPlan.map((entry) => ({ width: entry.width, height: entry.height }))
      : matrixViewports(fixture.matrix || "pressure");
    let scales = SCALE_MODES;
    if (quick) {
      if (fixture.id === "normal") {
        viewports = REPRESENTATIVE_VIEWPORTS;
        scales = [100];
      } else if ((fixture.groups || []).includes("calibration")) {
        viewports = [MANDATORY_VIEWPORTS[0], MANDATORY_VIEWPORTS[3]];
        scales = [100];
      } else {
        continue;
      }
    }

    for (const viewport of viewports) {
      const viewportScales = runPlan
        ? runPlan.find((entry) =>
            entry.width === viewport.width && entry.height === viewport.height
          ).scales
        : scales;
      for (const scale of viewportScales) {
        cases.push({
          key: caseKey(fixture.id, viewport, scale),
          fixture,
          viewport: { ...viewport },
          scale
        });
      }
    }
  }

  cases.sort((left, right) =>
    left.fixture.id.localeCompare(right.fixture.id) ||
    left.viewport.width - right.viewport.width ||
    left.viewport.height - right.viewport.height ||
    left.scale - right.scale
  );

  if (!quick && !selectedIds && catalog.expectedCaseCount !== undefined &&
      cases.length !== catalog.expectedCaseCount) {
    throw new Error(
      `Catalog case-count pin mismatch: expected ${catalog.expectedCaseCount}, got ${cases.length}`
    );
  }
  return cases;
}

export function matrixSummary(cases) {
  return {
    totalCases: cases.length,
    fixtureCount: new Set(cases.map((entry) => entry.fixture.id)).size,
    viewports: [...new Set(cases.map((entry) => viewportKey(entry.viewport)))],
    scales: [...new Set(cases.map((entry) => entry.scale))].sort((a, b) => a - b)
  };
}
