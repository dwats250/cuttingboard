import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

function normalizeNumber(value) {
  if (!Number.isFinite(value)) return null;
  return Math.round(value * 10) / 10;
}

export function canonicalize(value) {
  if (typeof value === "number") return normalizeNumber(value);
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])])
    );
  }
  return value;
}

export function stableStringify(value) {
  return `${JSON.stringify(canonicalize(value), null, 2)}\n`;
}

export async function writeStableJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, stableStringify(value), "utf8");
  return path;
}

function evaluatePrd314Calibration(cases) {
  const preId = cases.find((entry) => entry.fixture.startsWith("prd314-prefi"))?.fixture;
  const currentId = cases.find((entry) => entry.fixture.startsWith("prd314-current"))?.fixture;
  if (!preId || !currentId) {
    return {
      applicable: false,
      verdict: "INFORMATIONAL",
      failures: [],
      reason: "PRD-314 calibration fixtures were not selected"
    };
  }
  const findCell = (fixture, width, scale) => cases.find((entry) =>
    entry.fixture === fixture &&
    entry.viewport.width === width &&
    entry.scale === scale
  );
  const pre360Baseline = findCell(preId, 360, 100);
  const current360Baseline = findCell(currentId, 360, 100);
  const pre360Pressure = findCell(preId, 360, 125);
  const current360Pressure = findCell(currentId, 360, 125);
  const pre431 = findCell(preId, 431, 100);
  const current431 = findCell(currentId, 431, 100);
  const failures = [];
  const requiredClipIds = [
    "critical-horizontal-clipping:opportunity:SURFACED",
    "critical-horizontal-clipping:opportunity:WATCHLIST"
  ];
  if (!pre360Baseline) failures.push("missing pre-fix 360x800 scale-100 baseline cell");
  if (!current360Baseline) failures.push("missing current 360x800 scale-100 baseline cell");
  if (!pre360Pressure) failures.push("missing pre-fix 360x800 scale-125 pressure cell");
  if (!current360Pressure) failures.push("missing current 360x800 scale-125 pressure cell");
  if (pre360Baseline?.verdict === "FAIL") {
    failures.push("pre-fix 360x800 scale-100 baseline is not green on this host");
  }
  if (current360Baseline?.verdict === "FAIL") {
    failures.push("current 360x800 scale-100 baseline is not green");
  }
  if (pre360Pressure) {
    const failedIds = new Set((pre360Pressure.checks || [])
      .filter((check) => check.status === "FAIL")
      .map((check) => check.id));
    for (const id of requiredClipIds) {
      if (!failedIds.has(id)) failures.push(`pre-fix calibration did not trigger ${id}`);
    }
  }
  if (current360Pressure) {
    const currentFailedIds = new Set((current360Pressure.checks || [])
      .filter((check) => check.status === "FAIL")
      .map((check) => check.id));
    for (const id of requiredClipIds) {
      if (currentFailedIds.has(id)) {
        failures.push(`current calibration unexpectedly triggers ${id}`);
      }
    }
  }
  if (pre431 && pre431.verdict === "FAIL") {
    failures.push("pre-fix profile still fails at the 431px boundary");
  }
  if (current431 && current431.verdict === "FAIL") {
    failures.push("current profile fails at the 431px boundary");
  }
  return {
    applicable: true,
    verdict: failures.length ? "FAIL" : "PASS",
    failures,
    preFixFixture: preId,
    currentFixture: currentId,
    checkedCells: {
      preFix360Baseline: pre360Baseline?.key || null,
      current360Baseline: current360Baseline?.key || null,
      preFix360Pressure: pre360Pressure?.key || null,
      current360Pressure: current360Pressure?.key || null,
      preFix431: pre431?.key || null,
      current431: current431?.key || null
    },
    independentPressureFailures: {
      preFix: pre360Pressure?.failures || [],
      current: current360Pressure?.failures || []
    },
    hostNote: "Chrome 151 host font metrics reproduce the historical value-cell collapse at 125% root text scaling; both profiles are green for these values at 100%."
  };
}

export function buildValidationReport({
  baseline,
  sourceIdentifier,
  sourceMode,
  method,
  matrix,
  cases
}) {
  const verdictCounts = { FAIL: 0, PASS: 0, WARNING: 0 };
  for (const entry of cases) verdictCounts[entry.verdict] += 1;
  const outcomeMatches = (entry) => {
    if (entry.expectedVerdict === "FAIL") return entry.verdict === "FAIL";
    if (entry.expectedVerdict === "WARNING") return entry.verdict !== "FAIL";
    return entry.verdict !== "FAIL";
  };
  const expectedFailures = cases.filter((entry) =>
    entry.verdict === "FAIL" && entry.expectedVerdict === "FAIL"
  ).length;
  const unexpectedFailures = cases.filter((entry) => !outcomeMatches(entry)).length;
  const screenshotCount = cases.filter((entry) => entry.screenshot).length;
  const calibration = evaluatePrd314Calibration(cases);
  const suiteFailureCount = unexpectedFailures +
    (calibration.applicable && calibration.verdict === "FAIL" ? 1 : 0);

  return {
    schemaVersion: "production-visual-regression-report.v1",
    baseline,
    source: {
      identifier: sourceIdentifier,
      mode: sourceMode
    },
    method,
    matrix,
    summary: {
      totalCases: cases.length,
      fixtureCount: new Set(cases.map((entry) => entry.fixture)).size,
      verdictCounts,
      expectedFailures,
      unexpectedFailures,
      screenshotCount,
      suiteVerdict: suiteFailureCount === 0 ? "PASS" : "FAIL"
    },
    calibration,
    cases
  };
}

function delta(before, after) {
  return Number.isFinite(before) && Number.isFinite(after)
    ? normalizeNumber(after - before)
    : null;
}

function clippingFailureIds(caseResult) {
  return (caseResult.checks || [])
    .filter((check) =>
      check.status === "FAIL" &&
      check.severity === "FAIL" &&
      check.id.includes("clipping")
    )
    .map((check) => check.id)
    .sort();
}

function candidateDiscovery(raw) {
  return {
    wrapper: Boolean(raw.elements?.candidate?.present),
    identity: Boolean(raw.elements?.candidateIdentity?.present),
    level: Boolean(raw.elements?.candidateLevel?.present),
    invalidation: Boolean(raw.elements?.candidateInvalidation?.present)
  };
}

export function compareCasePair(before, after, options = {}) {
  const textKeys = options.visibleTextKeys || [
    "marketState",
    "systemState",
    "opportunity",
    "candidateIdentity"
  ];
  const criticalTextEquality = Object.fromEntries(textKeys.map((key) => {
    const beforeText = String(before.raw?.text?.byKey?.[key] || "");
    const afterText = String(after.raw?.text?.byKey?.[key] || "");
    return [key, {
      before: beforeText,
      after: afterText,
      equal: beforeText === afterText
    }];
  }));

  const geometryKeys = [
    "firstZoneHeight",
    "candidateY",
    "candidateIdentityY",
    "candidateLevelY",
    "candidateInvalidationY",
    "contextY",
    "gexExposedSpace",
    "opportunityToCandidateGap"
  ];
  const geometryDeltas = Object.fromEntries(geometryKeys.map((key) => [
    key,
    {
      before: before.raw?.geometry?.[key] ?? null,
      after: after.raw?.geometry?.[key] ?? null,
      delta: delta(before.raw?.geometry?.[key], after.raw?.geometry?.[key])
    }
  ]));

  const beforeClipping = clippingFailureIds(before);
  const afterClipping = clippingFailureIds(after);
  const newClipping = afterClipping.filter((id) => !beforeClipping.includes(id));
  const resolvedClipping = beforeClipping.filter((id) => !afterClipping.includes(id));
  const beforeCandidate = candidateDiscovery(before.raw || {});
  const afterCandidate = candidateDiscovery(after.raw || {});
  const candidateRegressions = Object.keys(beforeCandidate).filter((key) =>
    beforeCandidate[key] && !afterCandidate[key]
  );
  const requiredTextChanges = Object.entries(criticalTextEquality)
    .filter(([key, comparison]) =>
      (options.requireTextEquality || []).includes(key) && !comparison.equal
    )
    .map(([key]) => key);
  const pageOverflowTransition = {
    before: before.raw?.page?.overflowX ?? null,
    after: after.raw?.page?.overflowX ?? null,
    delta: delta(before.raw?.page?.overflowX, after.raw?.page?.overflowX)
  };
  const domOrderChanged = JSON.stringify(before.raw?.dom?.surfaceOrder || []) !==
    JSON.stringify(after.raw?.dom?.surfaceOrder || []);
  const failures = [];
  if (newClipping.length) failures.push(`new clipping: ${newClipping.join(", ")}`);
  if ((pageOverflowTransition.before || 0) <= 1 &&
      (pageOverflowTransition.after || 0) > 1) {
    failures.push("new horizontal page overflow");
  }
  if (candidateRegressions.length) {
    failures.push(`candidate discoverability regressed: ${candidateRegressions.join(", ")}`);
  }
  if (requiredTextChanges.length) {
    failures.push(`required visible text changed: ${requiredTextChanges.join(", ")}`);
  }

  return {
    key: before.key,
    fixture: before.fixture,
    viewport: before.viewport,
    scale: before.scale,
    verdict: failures.length ? "FAIL" : "PASS",
    failures,
    criticalVisibleText: criticalTextEquality,
    domOrder: {
      before: before.raw?.dom?.surfaceOrder || [],
      after: after.raw?.dom?.surfaceOrder || [],
      changed: domOrderChanged
    },
    geometryDeltas,
    overflow: pageOverflowTransition,
    clipping: {
      before: beforeClipping,
      after: afterClipping,
      new: newClipping,
      resolved: resolvedClipping
    },
    candidateDiscoverability: {
      before: beforeCandidate,
      after: afterCandidate,
      regressions: candidateRegressions
    },
    contextPosition: geometryDeltas.contextY,
    screenshotPair: {
      before: before.screenshot || null,
      after: after.screenshot || null
    }
  };
}

export function buildComparisonReport({
  beforeIdentifier,
  afterIdentifier,
  method,
  pairs
}) {
  const failedPairs = pairs.filter((pair) => pair.verdict === "FAIL").length;
  return {
    schemaVersion: "production-visual-comparison-report.v1",
    before: { identifier: beforeIdentifier },
    after: { identifier: afterIdentifier },
    method,
    summary: {
      totalPairs: pairs.length,
      failedPairs,
      verdict: failedPairs ? "FAIL" : "PASS"
    },
    pairs
  };
}

export function geometryArtifact(report) {
  return {
    schemaVersion: "production-visual-geometry.v1",
    baseline: report.baseline,
    source: report.source,
    cases: Object.fromEntries(report.cases.map((entry) => [entry.key, entry.raw]))
  };
}

export function renderResultsMarkdown(report) {
  const calibrationCases = report.cases.filter((entry) =>
    (entry.groups || []).includes("calibration")
  );
  const screenshots = report.cases
    .filter((entry) => entry.screenshot)
    .map((entry) => entry.screenshot)
    .sort();
  const lines = [
    "# Cuttingboard Production Visual Regression Torture Lab V0 Results",
    "",
    `- Baseline: \`${report.baseline}\``,
    `- Source: \`${report.source.identifier}\` (${report.source.mode})`,
    `- Fixtures: ${report.summary.fixtureCount}`,
    `- Validation cases: ${report.summary.totalCases}`,
    `- Suite verdict: **${report.summary.suiteVerdict}**`,
    `- PASS / WARNING / FAIL: ${report.summary.verdictCounts.PASS} / ${report.summary.verdictCounts.WARNING} / ${report.summary.verdictCounts.FAIL}`,
    `- Expected calibration failures: ${report.summary.expectedFailures}`,
    `- Unexpected outcomes: ${report.summary.unexpectedFailures}`,
    `- Screenshots: ${report.summary.screenshotCount}`,
    "",
    "## PRD-314 calibration",
    ""
  ];
  for (const entry of calibrationCases) {
    lines.push(
      `- \`${entry.fixture}\` ${entry.viewport.width}x${entry.viewport.height} ` +
      `scale ${entry.scale}%: ${entry.verdict} (expected ${entry.expectedVerdict})`
    );
  }
  lines.push("", "## Screenshot inventory", "");
  for (const screenshot of screenshots) lines.push(`- \`${screenshot}\``);
  lines.push(
    "",
    "## Isolation",
    "",
    "All implementation, fixtures, measurements, reports, and screenshots are contained beneath `experiments/production-visual-regression-lab-v0/`. No production behavior is modified.",
    ""
  );
  return lines.join("\n");
}

export async function writeText(path, text) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, text.endsWith("\n") ? text : `${text}\n`, "utf8");
  return path;
}
