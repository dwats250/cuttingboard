#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

import {
  captureScreenshot,
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
} from "./cdp.mjs";
import { buildProbeExpression } from "./probe.mjs";

const labRoot = resolve(dirname(new URL(import.meta.url).pathname), "..");
const fixtureRoot = resolve(labRoot, "fixtures/currentmain");
const outputRoot = resolve(labRoot, "mobile-sweep");
const viewports = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 1280, height: 800 }
];
const fixtures = ["stale-board", "no-candidate", "normal"];
const selectors = {
  root: ".wrap",
  staleness: "#staleness-banner",
  marketState: "#market-state",
  systemState: "#system-state",
  opportunity: "#opportunity-survival",
  candidate: "#candidate-board",
  candidateIdentity: "#candidate-board .candidate-card .card-header",
  gex: "#gex-context",
  movement: "#market-movement",
  macro: "#macro-tape",
  trend: "#trend-structure",
  runDelta: "#run-delta",
  scoreboard: "#scoreboard"
};
const probeContract = {
  selectors,
  criticalKeys: ["staleness", "marketState", "systemState", "opportunity", "candidate"],
  contextKeys: ["gex", "movement", "macro", "trend"],
  surfaceKeys: [
    "staleness", "marketState", "systemState", "opportunity", "candidate",
    "gex", "movement", "macro", "trend", "runDelta", "scoreboard"
  ]
};

function compact(result) {
  const top = (key) => result.elements[key]?.rect?.pageTop ?? null;
  const height = (key) => result.elements[key]?.rect?.height ?? null;
  return {
    pageHeight: result.page.scrollHeight,
    horizontalOverflow: result.page.overflowX,
    authoritativeDecisionY: top("systemState"),
    opportunityY: top("opportunity"),
    candidateY: result.geometry.candidateY,
    candidateIdentityY: result.geometry.candidateIdentityY,
    candidateLevelY: result.geometry.candidateLevelY,
    candidateInvalidationY: result.geometry.candidateInvalidationY,
    firstMeaningfulContext: result.geometry.contextKey,
    firstMeaningfulContextY: result.geometry.contextY,
    staleBannerHeight: height("staleness"),
    marketStateHeight: height("marketState"),
    systemStateHeight: height("systemState"),
    opportunityHeight: height("opportunity"),
    candidateHeight: height("candidate"),
    fold: result.fold,
    surfaceOrder: result.dom.surfaceOrder,
    criticalText: {
      staleness: result.text.byKey.staleness,
      marketState: result.text.byKey.marketState,
      systemState: result.text.byKey.systemState,
      opportunity: result.text.byKey.opportunity,
      candidate: result.text.byKey.candidate
    }
  };
}

async function settle(target) {
  await evaluate(target, `new Promise((resolve) => requestAnimationFrame(() =>
    requestAnimationFrame(() => { scrollTo(0, 0); resolve(true); })))`);
}

async function run() {
  const cssPath = process.argv[2] ? resolve(process.argv[2]) : null;
  const phase = cssPath ? "after" : "before";
  const css = cssPath ? await readFile(cssPath, "utf8") : null;
  await mkdir(resolve(outputRoot, "screenshots"), { recursive: true });
  const chrome = await launchChrome();
  const results = [];
  try {
    for (const fixture of fixtures) {
      for (const viewport of viewports) {
        const target = await createTarget(chrome);
        try {
          await enablePageRuntime(target);
          await configureViewport(target, viewport.width, viewport.height);
          await navigateFile(target, resolve(fixtureRoot, `${fixture}.html`));
          await setRootFontScale(target, 100);
          if (css) await injectCss(target, css, "mobile-operator-sweep");
          await settle(target);
          const raw = await evaluate(target, buildProbeExpression(probeContract));
          const screenshot = resolve(
            outputRoot,
            "screenshots",
            `${phase}-${fixture}-${viewport.width}x${viewport.height}.png`
          );
          await captureScreenshot(target, screenshot);
          results.push({
            phase,
            fixture,
            viewport: `${viewport.width}x${viewport.height}`,
            screenshot,
            metrics: compact(raw)
          });
        } finally {
          await closeTarget(target);
        }
      }
    }
  } finally {
    await shutdownChrome(chrome);
  }
  const output = resolve(outputRoot, `${phase}-measurements.json`);
  await writeFile(output, `${JSON.stringify({ phase, cssPath, results }, null, 2)}\n`);
  console.log(output);
}

await run();
