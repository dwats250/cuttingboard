#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, rm } from "node:fs/promises";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  captureScreenshot,
  closeTarget,
  configureViewport,
  createTarget,
  enablePageRuntime,
  evaluate,
  launchChrome,
  navigateFile,
  setRootFontScale,
  shutdownChrome
} from "./cdp.mjs";
import { classifyObservation } from "./checks.mjs";
import {
  MANDATORY_VIEWPORTS,
  SCALE_MODES,
  caseKey,
  expandMatrix,
  matrixSummary,
  screenshotStem,
  selectedBaselineScreenshot
} from "./matrix.mjs";
import { buildProbeExpression } from "./probe.mjs";
import {
  buildComparisonReport,
  buildValidationReport,
  compareCasePair,
  geometryArtifact,
  renderResultsMarkdown,
  writeStableJson,
  writeText
} from "./report.mjs";

const runnerDirectory = dirname(fileURLToPath(import.meta.url));
const labRoot = dirname(runnerDirectory);
const defaultCatalogPath = join(labRoot, "fixtures", "catalog.json");
const screenshotRoot = join(labRoot, "screenshots");
const reportRoot = join(labRoot, "reports");
const measurementRoot = join(labRoot, "measurements");

function parseArgs(values) {
  const options = { _: [] };
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (!value.startsWith("--")) {
      options._.push(value);
      continue;
    }
    const key = value.slice(2);
    const next = values[index + 1];
    if (next !== undefined && !next.startsWith("--")) {
      options[key] = next;
      index += 1;
    } else {
      options[key] = true;
    }
  }
  return options;
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function sha256(path) {
  return createHash("sha256").update(await readFile(path)).digest("hex");
}

function fixturePath(catalogPath, fixture) {
  if (fixture.absoluteFile) return fixture.absoluteFile;
  const path = fixture.file;
  if (!path) throw new Error(`Fixture ${fixture.id} has no file`);
  return isAbsolute(path) ? path : resolve(dirname(catalogPath), path);
}

function expectedVerdictFor(fixture, viewport, scale) {
  for (const rule of fixture.expectedVerdicts || []) {
    const widthMatch = rule.width === undefined || rule.width === viewport.width;
    const heightMatch = rule.height === undefined || rule.height === viewport.height;
    const scaleMatch = rule.scale === undefined || rule.scale === scale;
    if (widthMatch && heightMatch && scaleMatch) return rule.verdict;
  }
  return fixture.expectedVerdict || "PASS";
}

function appendCheck(classification, check) {
  classification.checks.push(check);
  if (check.status === "FAIL" && check.severity === "FAIL") {
    classification.failures.push(check.message);
    classification.verdict = "FAIL";
  } else if (check.status === "FAIL" && check.severity === "WARNING") {
    classification.warnings.push(check.message);
    if (classification.verdict === "PASS") classification.verdict = "WARNING";
  }
}

async function settleDocument(target) {
  await evaluate(target, `new Promise((resolve) => {
    const finish = () => requestAnimationFrame(() => requestAnimationFrame(() => {
      scrollTo(0, 0);
      resolve(true);
    }));
    if (document.readyState === "complete") finish();
    else addEventListener("load", finish, { once: true });
  })`);
}

async function observeOne({
  chrome,
  catalog,
  catalogPath,
  caseEntry,
  sourcePath = null,
  sourceIdentifier,
  baseline,
  screenshotPrefix = "",
  forceScreenshot = false
}) {
  const fixture = caseEntry.fixture;
  const htmlPath = sourcePath || fixturePath(catalogPath, fixture);
  const target = await createTarget(chrome);
  try {
    await enablePageRuntime(target);
    await configureViewport(target, caseEntry.viewport.width, caseEntry.viewport.height);
    await navigateFile(target, htmlPath);
    await setRootFontScale(target, caseEntry.scale);
    for (const selector of fixture.setup?.openDetails || []) {
      await evaluate(target, `Array.from(document.querySelectorAll(${JSON.stringify(selector)}))
        .forEach((element) => { element.open = true; });`);
    }
    await settleDocument(target);
    const raw = await evaluate(target, buildProbeExpression({
      ...(catalog.defaults || {}),
      ...(fixture.probe || {})
    }));
    const classification = classifyObservation(raw, fixture, catalog.defaults || {});
    const requested = caseEntry.viewport;
    const viewportMatches = raw.viewport?.width === requested.width &&
      raw.viewport?.height === requested.height;
    appendCheck(classification, {
      id: "viewport-exact",
      severity: "FAIL",
      status: viewportMatches ? "PASS" : "FAIL",
      message: viewportMatches
        ? `viewport is exactly ${requested.width}x${requested.height}`
        : `viewport mismatch: requested ${requested.width}x${requested.height}, observed ${raw.viewport?.width}x${raw.viewport?.height}`,
      evidence: { requested, observed: raw.viewport }
    });

    const expectedRootPx = caseEntry.scale * 16 / 100;
    const observedRootPx = Number.parseFloat(raw.viewport?.rootFontSize || "NaN");
    const scaleMatches = Number.isFinite(observedRootPx) &&
      Math.abs(observedRootPx - expectedRootPx) <= 0.2;
    appendCheck(classification, {
      id: "root-font-scale",
      severity: "FAIL",
      status: scaleMatches ? "PASS" : "FAIL",
      message: scaleMatches
        ? `root font scale ${caseEntry.scale}% resolved to ${observedRootPx}px`
        : `root font scale ${caseEntry.scale}% expected ${expectedRootPx}px, observed ${raw.viewport?.rootFontSize}`,
      evidence: { scalePercent: caseEntry.scale, expectedPx: expectedRootPx, observedPx: observedRootPx }
    });

    const expectedVerdict = expectedVerdictFor(
      fixture,
      caseEntry.viewport,
      caseEntry.scale
    );
    const shouldCapture = forceScreenshot ||
      selectedBaselineScreenshot(caseEntry) ||
      classification.verdict === "FAIL";
    let screenshot = null;
    if (shouldCapture) {
      await mkdir(screenshotRoot, { recursive: true });
      const stem = screenshotStem(
        `${screenshotPrefix}${fixture.id}`,
        caseEntry.viewport,
        caseEntry.scale,
        classification.verdict
      );
      const outputPath = join(screenshotRoot, `${stem}.png`);
      await captureScreenshot(target, outputPath);
      screenshot = `screenshots/${basename(outputPath)}`;
    }

    return {
      key: caseEntry.key,
      baseline,
      sourceIdentifier,
      sourceHash: await sha256(htmlPath),
      fixture: fixture.id,
      fixtureLabel: fixture.label,
      groups: fixture.groups || [],
      synthetic: Boolean(fixture.synthetic),
      viewport: { ...caseEntry.viewport },
      scale: caseEntry.scale,
      scaleMethod: "root-font-size",
      expectedVerdict,
      geometry: raw.geometry,
      fold: raw.fold,
      checks: classification.checks,
      verdict: classification.verdict,
      failures: classification.failures,
      warnings: classification.warnings,
      information: classification.information,
      screenshot,
      raw
    };
  } finally {
    await closeTarget(target);
  }
}

async function chromeMethod(chrome) {
  const target = await createTarget(chrome);
  try {
    await enablePageRuntime(target);
    const version = await target.client.send("Browser.getVersion");
    return {
      browser: version.product,
      protocolVersion: version.protocolVersion,
      deviceScaleFactor: 1,
      colorScheme: "dark",
      reducedMotion: true,
      timezone: "America/Vancouver",
      fixedNow: "2026-08-23T20:00:00Z",
      textScaleMethod: "root-font-size"
    };
  } finally {
    await closeTarget(target);
  }
}

async function runCases({
  catalog,
  catalogPath,
  cases,
  sourcePath = null,
  sourceIdentifier,
  baseline,
  screenshotPrefix = "",
  forceScreenshot = false
}) {
  const chrome = await launchChrome();
  const results = [];
  try {
    const method = await chromeMethod(chrome);
    for (const [index, caseEntry] of cases.entries()) {
      results.push(await observeOne({
        chrome,
        catalog,
        catalogPath,
        caseEntry,
        sourcePath,
        sourceIdentifier,
        baseline,
        screenshotPrefix,
        forceScreenshot
      }));
      if ((index + 1) % 25 === 0 || index + 1 === cases.length) {
        console.log(`measured ${index + 1}/${cases.length} cases`);
      }
    }
    return { results, method };
  } finally {
    await shutdownChrome(chrome);
  }
}

async function validateCommand(options) {
  const catalogPath = resolve(options.catalog || defaultCatalogPath);
  const catalog = await readJson(catalogPath);
  const fixtureIds = options.fixture ? String(options.fixture).split(",") : null;
  const cases = expandMatrix(catalog, {
    quick: Boolean(options.quick),
    fixtureIds
  });
  await rm(screenshotRoot, { recursive: true, force: true });
  const { results, method } = await runCases({
    catalog,
    catalogPath,
    cases,
    sourceIdentifier: catalog.sourceIdentifier,
    baseline: catalog.baseline
  });
  const report = buildValidationReport({
    baseline: catalog.baseline,
    sourceIdentifier: catalog.sourceIdentifier,
    sourceMode: "deterministic-current-renderer-fixtures",
    method,
    matrix: matrixSummary(cases),
    cases: results
  });
  const outputPath = resolve(options.output || join(reportRoot, "validation.json"));
  await writeStableJson(outputPath, report);
  await writeStableJson(join(measurementRoot, "geometry.json"), geometryArtifact(report));
  await writeText(join(labRoot, "RESULTS.md"), renderResultsMarkdown(report));
  console.log(`suite verdict: ${report.summary.suiteVerdict}`);
  console.log(`report: ${outputPath}`);
  if (report.summary.suiteVerdict === "FAIL") process.exitCode = 1;
}

function defaultExternalFixture(id, file) {
  return {
    id,
    label: id,
    file,
    absoluteFile: file,
    matrix: "all",
    groups: ["external"],
    synthetic: false,
    expectedVerdict: "PASS",
    expected: {
      presence: {
        marketState: "present",
        systemState: "present",
        candidate: "present"
      },
      requiredText: ["MARKET STATE", "SYSTEM STATE"],
      order: ["marketState", "systemState", "candidate"],
      information: ["Candidate field expectations require an explicit contract."]
    }
  };
}

async function contractFixture(options, catalog, htmlPath) {
  if (options.contract) {
    const contract = await readJson(resolve(options.contract));
    if (contract.fixtures) {
      const id = options.fixture || "normal";
      const fixture = contract.fixtures.find((entry) => entry.id === id);
      if (!fixture) throw new Error(`Contract catalog has no fixture: ${id}`);
      return fixture;
    }
    return contract.fixture || contract;
  }
  const fromCatalog = catalog.fixtures.find((entry) =>
    entry.id === (options.fixture || "normal")
  );
  return fromCatalog || defaultExternalFixture(options.fixture || "external", htmlPath);
}

async function inspectCommand(options) {
  if (!options.html) throw new Error("inspect requires --html PATH");
  const htmlPath = resolve(options.html);
  const catalogPath = resolve(options.catalog || defaultCatalogPath);
  const baseCatalog = await readJson(catalogPath);
  const fixture = await contractFixture(options, baseCatalog, htmlPath);
  const catalog = { ...baseCatalog, fixtures: [{ ...fixture, absoluteFile: htmlPath }] };
  const cases = MANDATORY_VIEWPORTS.flatMap((viewport) =>
    SCALE_MODES.map((scale) => ({
      key: caseKey(fixture.id, viewport, scale),
      fixture: catalog.fixtures[0],
      viewport: { ...viewport },
      scale
    }))
  );
  const sourceIdentifier = options["source-id"] || `sha256:${await sha256(htmlPath)}`;
  const { results, method } = await runCases({
    catalog,
    catalogPath,
    cases,
    sourcePath: htmlPath,
    sourceIdentifier,
    baseline: baseCatalog.baseline
  });
  const report = buildValidationReport({
    baseline: baseCatalog.baseline,
    sourceIdentifier,
    sourceMode: "supplied-rendered-html",
    method,
    matrix: matrixSummary(cases),
    cases: results
  });
  const outputPath = resolve(options.output || join(reportRoot, `inspect-${fixture.id}.json`));
  await writeStableJson(outputPath, report);
  console.log(`suite verdict: ${report.summary.suiteVerdict}`);
  console.log(`report: ${outputPath}`);
  if (report.summary.suiteVerdict === "FAIL") process.exitCode = 1;
}

async function compareCommand(options) {
  if (!options.before || !options.after) {
    throw new Error("compare requires --before PATH and --after PATH");
  }
  const beforePath = resolve(options.before);
  const afterPath = resolve(options.after);
  const catalogPath = resolve(options.catalog || defaultCatalogPath);
  const baseCatalog = await readJson(catalogPath);
  const fixture = await contractFixture(options, baseCatalog, afterPath);
  const catalog = { ...baseCatalog, fixtures: [{ ...fixture, absoluteFile: afterPath }] };
  const scales = options.scales
    ? String(options.scales).split(",").map((value) => Number.parseInt(value, 10))
    : options["all-scales"] ? SCALE_MODES : [100];
  const unsupportedScales = scales.filter((scale) => !SCALE_MODES.includes(scale));
  if (unsupportedScales.length) {
    throw new Error(`Unsupported scales: ${unsupportedScales.join(", ")}`);
  }
  const requestedViewportKeys = options.viewports
    ? new Set(String(options.viewports).split(","))
    : null;
  const viewports = requestedViewportKeys
    ? MANDATORY_VIEWPORTS.filter((viewport) =>
        requestedViewportKeys.has(`${viewport.width}x${viewport.height}`)
      )
    : MANDATORY_VIEWPORTS;
  if (requestedViewportKeys && viewports.length !== requestedViewportKeys.size) {
    const supported = MANDATORY_VIEWPORTS
      .map((viewport) => `${viewport.width}x${viewport.height}`)
      .join(", ");
    throw new Error(`--viewports must select mandatory viewport keys: ${supported}`);
  }
  const cases = viewports.flatMap((viewport) =>
    scales.map((scale) => ({
      key: caseKey(fixture.id, viewport, scale),
      fixture: catalog.fixtures[0],
      viewport: { ...viewport },
      scale
    }))
  );
  const beforeIdentifier = options["before-id"] || `sha256:${await sha256(beforePath)}`;
  const afterIdentifier = options["after-id"] || `sha256:${await sha256(afterPath)}`;
  const beforeRun = await runCases({
    catalog,
    catalogPath,
    cases,
    sourcePath: beforePath,
    sourceIdentifier: beforeIdentifier,
    baseline: baseCatalog.baseline,
    screenshotPrefix: "compare-before-",
    forceScreenshot: true
  });
  const afterRun = await runCases({
    catalog,
    catalogPath,
    cases,
    sourcePath: afterPath,
    sourceIdentifier: afterIdentifier,
    baseline: baseCatalog.baseline,
    screenshotPrefix: "compare-after-",
    forceScreenshot: true
  });
  const pairs = beforeRun.results.map((before, index) =>
    compareCasePair(before, afterRun.results[index], fixture.comparison || {})
  );
  const report = buildComparisonReport({
    beforeIdentifier,
    afterIdentifier,
    method: beforeRun.method,
    pairs
  });
  const outputPath = resolve(options.output || join(reportRoot, "comparison.json"));
  await writeStableJson(outputPath, report);
  console.log(`comparison verdict: ${report.summary.verdict}`);
  console.log(`report: ${outputPath}`);
  if (report.summary.verdict === "FAIL") process.exitCode = 1;
}

function usage() {
  return `Usage:
  node runner/cli.mjs validate [--quick] [--fixture ID[,ID]] [--output PATH]
  node runner/cli.mjs inspect --html PATH [--fixture ID] [--contract PATH] [--source-id ID]
  node runner/cli.mjs compare --before PATH --after PATH [--fixture ID] [--contract PATH]
      [--all-scales | --scales 100,125] [--viewports 360x800,431x932]
`;
}

async function main() {
  const [command = "validate", ...rest] = process.argv.slice(2);
  const options = parseArgs(rest);
  if (command === "validate") return validateCommand(options);
  if (command === "inspect") return inspectCommand(options);
  if (command === "compare") return compareCommand(options);
  if (command === "help" || command === "--help" || command === "-h") {
    console.log(usage());
    return;
  }
  throw new Error(`Unknown command: ${command}\n${usage()}`);
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
