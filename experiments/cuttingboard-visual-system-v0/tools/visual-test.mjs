#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { setTimeout as delay } from "node:timers/promises";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const labRoot = dirname(scriptDirectory);
const screenshotRoot = join(labRoot, "screenshots");
const measurementsPath = join(labRoot, "measurements.json");
const chromeExecutable = process.env.CB_LAB_CHROME || "/usr/bin/google-chrome";
const quickMode = process.argv.includes("--quick");

const variants = [
  { key: "a", directory: "variant-a" },
  { key: "b", directory: "variant-b" },
  { key: "c", directory: "variant-c" }
];

const normalViewports = [
  { width: 360, height: 800 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 800 },
  { width: 1440, height: 900 }
];

const exceptionFixtures = ["halt", "degraded", "event", "no-candidate"];
const exceptionViewports = [
  { width: 390, height: 844 },
  { width: 1280, height: 800 }
];

function cbLabWaitForChrome(chromeProcess) {
  return new Promise((resolve, reject) => {
    let stderr = "";
    const timeout = setTimeout(() => {
      reject(new Error(`Chrome DevTools endpoint did not start. stderr: ${stderr.slice(-2000)}`));
    }, 12000);

    chromeProcess.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
      const match = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) {
        clearTimeout(timeout);
        resolve(match[1]);
      }
    });

    chromeProcess.once("exit", (code) => {
      clearTimeout(timeout);
      reject(new Error(`Chrome exited before DevTools was ready (code ${code}). stderr: ${stderr.slice(-2000)}`));
    });
  });
}

function cbLabCdpClient(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  const pending = new Map();
  const waiters = new Map();
  let commandId = 0;

  const ready = new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });

  socket.addEventListener("message", async (event) => {
    const raw = typeof event.data === "string"
      ? event.data
      : event.data instanceof Blob
        ? await event.data.text()
        : Buffer.from(event.data).toString("utf8");
    const message = JSON.parse(raw);

    if (message.id && pending.has(message.id)) {
      const entry = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(entry.timeout);
      if (message.error) {
        entry.reject(new Error(`${entry.method}: ${message.error.message}`));
      } else {
        entry.resolve(message.result || {});
      }
      return;
    }

    if (message.method && waiters.has(message.method)) {
      const entries = waiters.get(message.method);
      waiters.delete(message.method);
      entries.forEach((entry) => {
        clearTimeout(entry.timeout);
        entry.resolve(message.params || {});
      });
    }
  });

  socket.addEventListener("close", () => {
    for (const entry of pending.values()) {
      clearTimeout(entry.timeout);
      entry.reject(new Error("CDP socket closed with a command pending"));
    }
    pending.clear();
  });

  return {
    async send(method, params = {}) {
      await ready;
      commandId += 1;
      const id = commandId;
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          pending.delete(id);
          reject(new Error(`CDP command timed out: ${method}`));
        }, 12000);
        pending.set(id, { method, resolve, reject, timeout });
        socket.send(JSON.stringify({ id, method, params }));
      });
    },

    waitFor(method) {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          const entries = waiters.get(method) || [];
          waiters.set(method, entries.filter((entry) => entry.resolve !== resolve));
          reject(new Error(`CDP event timed out: ${method}`));
        }, 12000);
        const entries = waiters.get(method) || [];
        entries.push({ resolve, reject, timeout });
        waiters.set(method, entries);
      });
    },

    close() {
      socket.close();
    }
  };
}

async function cbLabConnectCdp(debuggingUrl) {
  const browserEndpoint = new URL(debuggingUrl);
  const targetResponse = await fetch(
    `http://${browserEndpoint.host}/json/new?${encodeURIComponent("about:blank")}`,
    { method: "PUT" }
  );
  if (!targetResponse.ok) {
    throw new Error(`Could not create Chrome target: ${targetResponse.status}`);
  }
  const target = await targetResponse.json();
  return {
    target,
    client: cbLabCdpClient(target.webSocketDebuggerUrl),
    browserHost: browserEndpoint.host
  };
}

async function cbLabCloseTarget(connection) {
  connection.client.close();
  try {
    await fetch(
      `http://${connection.browserHost}/json/close/${encodeURIComponent(connection.target.id)}`
    );
  } catch {
    // Chrome process shutdown is the final cleanup fallback.
  }
}

async function cbLabCaptureMeasurements(client, fixtureName, variantKey, viewport) {
  const expression = `
    (() => {
      const fixtureName = ${JSON.stringify(fixtureName)};
      const variantKey = ${JSON.stringify(variantKey)};
      const viewport = ${JSON.stringify(viewport)};
      const one = (selector) => document.querySelector(selector);
      const all = (selector) => Array.from(document.querySelectorAll(selector));
      const rectOf = (element) => {
        if (!element) return null;
        const rect = element.getBoundingClientRect();
        return {
          top: Math.round(rect.top * 10) / 10,
          right: Math.round(rect.right * 10) / 10,
          bottom: Math.round(rect.bottom * 10) / 10,
          left: Math.round(rect.left * 10) / 10,
          width: Math.round(rect.width * 10) / 10,
          height: Math.round(rect.height * 10) / 10
        };
      };
      const visibility = (element) => {
        const rect = rectOf(element);
        if (!element || !rect) {
          return {
            rendered: false,
            intersectsInitialViewport: false,
            fullyAboveFold: false,
            top: null,
            bottom: null
          };
        }
        const style = getComputedStyle(element);
        const rendered = style.display !== "none" &&
          style.visibility !== "hidden" &&
          rect.width > 0 &&
          rect.height > 0;
        return {
          rendered,
          intersectsInitialViewport: rendered && rect.top < innerHeight && rect.bottom > 0,
          fullyAboveFold: rendered && rect.top >= 0 && rect.bottom <= innerHeight,
          top: rect.top,
          bottom: rect.bottom
        };
      };
      const hasFullBorder = (element) => {
        const style = getComputedStyle(element);
        return ["Top", "Right", "Bottom", "Left"].every((side) => {
          return parseFloat(style["border" + side + "Width"]) > 0 &&
            style["border" + side + "Style"] !== "none";
        });
      };

      const board = one("[data-board]");
      const boardRect = rectOf(board);
      const opportunityZone = one('[data-zone="opportunity"]');
      const opportunitySummary = one('[data-surface="opportunity-survival"]');
      const candidateSurface = one('[data-surface="candidate"]');
      const candidateIdentity = one("[data-candidate-identity]");
      const candidateLevel = one("[data-candidate-level]");
      const candidateInvalidation = one("[data-candidate-invalidation]");
      const candidateAnchor = candidateIdentity || candidateSurface;
      const candidateAnchorRect = rectOf(candidateAnchor);
      const contextStart = one("[data-context-start]");
      const contextRect = rectOf(contextStart);
      const opportunityZoneRect = rectOf(opportunityZone);
      const opportunitySummaryRect = rectOf(opportunitySummary);

      const fullBorderedBeforeCandidate = candidateAnchorRect
        ? all("[data-container]")
            .filter((element) => {
              const rect = rectOf(element);
              return rect &&
                hasFullBorder(element) &&
                !element.contains(candidateAnchor) &&
                rect.bottom <= candidateAnchorRect.top + 1;
            })
            .length
        : 0;

      const surfaceVisibility = all("[data-surface]").map((surface) => ({
        name: surface.dataset.surface,
        ...visibility(surface)
      }));

      const contextSurfaces = all("[data-context-surface]");
      const contextAboveFold = contextSurfaces.filter((surface) => {
        const rect = surface.getBoundingClientRect();
        return rect.top < innerHeight && rect.bottom > 0;
      });
      const contextColumns = new Set(
        contextSurfaces.map((surface) => Math.round(surface.getBoundingClientRect().left))
      ).size;

      const bodyText = document.body.innerText.toUpperCase();
      const alwaysMarkers = [
        "BOARD 12H OLD",
        "MARKET STATE",
        "SYSTEM STATE",
        "ENVIRONMENT",
        "PERMISSION",
        "GEX",
        "CONTEXT ONLY",
        "CBOE ~15M DELAYED",
        "POSITIONING IS NOT MEASURED",
        "MARKET MOVEMENT",
        "12/12 CAPTURED",
        "MACRO TAPE",
        "TREND STRUCTURE",
        "CHANGES SINCE LAST RUN",
        "SCOREBOARD"
      ];
      const fixtureMarkers = {
        normal: ["OBSERVE ONLY", "OPERATOR LOCK", "SPY", "LEVEL", "INVALIDATION"],
        halt: ["SYSTEM HALT", "HALT", "DISK FULL", "NO TRADE", "UNAVAILABLE — SYSTEM_HALTED"],
        degraded: ["PRIMARY STATE CARRIER UNAVAILABLE", "STATE UNAVAILABLE", "NO AUTHORIZATION", "INDEPENDENT SOURCE CLOCKS"],
        event: ["RED-FOLDER EVENT", "CPI (JULY)", "2026-08-24 08:30 ET", "SPY SESSION OBSERVATION", "MARKET CONTROL", "FORMED [100.00, 105.00]"],
        "no-candidate": ["NO DEVELOPING SETUPS", "NO CANDIDATE IDENTITY", "MARKET CONTROL", "NO_CANDIDATES_PRESENT"]
      };

      const errors = [];
      for (const marker of [...alwaysMarkers, ...fixtureMarkers[fixtureName]]) {
        if (!bodyText.includes(marker)) {
          errors.push("missing marker: " + marker);
        }
      }

      const overflowPx = document.documentElement.scrollWidth -
        document.documentElement.clientWidth;
      if (overflowPx > 0) {
        errors.push("horizontal overflow: " + overflowPx + "px");
      }

      const criticalSelectors = [
        "[data-critical-lane]",
        "[data-critical-content]",
        "[data-decision]",
        ".system-verdict",
        "[data-candidate-identity]",
        "[data-candidate-level]",
        "[data-candidate-invalidation]"
      ];
      for (const element of all(criticalSelectors.join(","))) {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        if (style.display === "none" || style.visibility === "hidden" ||
            rect.width <= 0 || rect.height <= 0) {
          errors.push("hidden critical element: " + (element.className || element.tagName));
        }
        if (element.clientWidth > 0 && element.scrollWidth - element.clientWidth > 1) {
          errors.push("clipped critical element: " + (element.className || element.tagName));
        }
      }

      for (const element of all(".axis__provenance, .qualifier, .provenance")) {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        if (style.display === "none" || style.visibility === "hidden" ||
            rect.width <= 0 || rect.height <= 0) {
          errors.push("hidden provenance");
        }
      }

      for (const summary of all("details > summary")) {
        const height = summary.getBoundingClientRect().height;
        if (height < 43.5) {
          errors.push("disclosure target below 44px: " + Math.round(height) + "px");
        }
      }

      const orderedSelectors = [
        '[data-surface="market-state"]',
        '[data-surface="system-state"]',
        '[data-surface="opportunity-survival"]',
        '[data-surface="candidate"]',
        '[data-surface="gex"]'
      ];
      const orderedElements = orderedSelectors.map(one);
      for (let index = 1; index < orderedElements.length; index += 1) {
        const previous = orderedElements[index - 1];
        const current = orderedElements[index];
        if (previous && current &&
            !(previous.compareDocumentPosition(current) & Node.DOCUMENT_POSITION_FOLLOWING)) {
          errors.push("source order failure: " + orderedSelectors[index - 1] + " before " + orderedSelectors[index]);
        }
      }

      if (fixtureName === "no-candidate") {
        if (candidateIdentity || candidateLevel || candidateInvalidation) {
          errors.push("no-candidate fixture fabricated candidate critical fields");
        }
      } else if (!candidateIdentity || !candidateLevel || !candidateInvalidation) {
        errors.push("candidate minimum read is incomplete");
      }

      const marketRect = rectOf(one('[data-surface="market-state"]'));
      const systemRect = rectOf(one('[data-surface="system-state"]'));
      const gexRect = rectOf(one('[data-surface="gex"]'));
      const movementRect = rectOf(one('[data-surface="movement"]'));
      if (viewport.width === 768) {
        if (Math.abs(marketRect.left - systemRect.left) > 2) {
          errors.push("tablet forced MARKET/SYSTEM into desktop columns");
        }
      }
      if (viewport.width >= 1280 && (variantKey === "b" || variantKey === "c")) {
        if (Math.abs(marketRect.left - systemRect.left) < 20) {
          errors.push("desktop STATE comparison pair did not activate");
        }
      }
      if (viewport.width >= 1280 && variantKey === "a") {
        if (Math.abs(gexRect.left - movementRect.left) < 20) {
          errors.push("Evolutionary desktop context comparison did not use width");
        }
      }

      const levelVisibility = visibility(candidateLevel);
      const identityVisibility = visibility(candidateIdentity);
      const invalidationVisibility = visibility(candidateInvalidation);

      return {
        fixture: fixtureName,
        variant: variantKey,
        viewport,
        horizontalOverflowPx: overflowPx,
        board: {
          widthPx: boardRect.width,
          widthUsePct: Math.round((boardRect.width / innerWidth) * 1000) / 10,
          heightPx: boardRect.height
        },
        phoneRead: {
          topThroughOpportunityZonePx: opportunityZoneRect
            ? Math.round((opportunityZoneRect.bottom - boardRect.top) * 10) / 10
            : null,
          topThroughOpportunitySurvivalPx: opportunitySummaryRect
            ? Math.round((opportunitySummaryRect.bottom - boardRect.top) * 10) / 10
            : null,
          candidateLevelScrollToFirstPixelPx: candidateLevel
            ? Math.max(0, Math.round(candidateLevel.getBoundingClientRect().top - innerHeight))
            : null,
          candidateLevelScrollToFullyVisiblePx: candidateLevel
            ? Math.max(0, Math.round(candidateLevel.getBoundingClientRect().bottom - innerHeight))
            : null,
          fullBorderedContainersBeforeCandidate: fullBorderedBeforeCandidate,
          firstContextTopPx: contextRect ? contextRect.top : null,
          firstContextScrollToFirstPixelPx: contextRect
            ? Math.max(0, Math.round(contextRect.top - innerHeight))
            : null,
          candidateIdentity: identityVisibility,
          candidateLevel: levelVisibility,
          candidateInvalidation: invalidationVisibility
        },
        desktopRead: {
          surfacesIntersectingFold: surfaceVisibility
            .filter((surface) => surface.intersectsInitialViewport)
            .map((surface) => surface.name),
          surfacesFullyAboveFold: surfaceVisibility
            .filter((surface) => surface.fullyAboveFold)
            .map((surface) => surface.name),
          candidateIdentity: identityVisibility,
          candidateLevel: levelVisibility,
          candidateInvalidation: invalidationVisibility,
          contextSurfacesIntersectingFold: contextAboveFold.length,
          contextComparisonColumns: contextColumns
        },
        provenanceNodesVisible: all(".axis__provenance, .qualifier, .provenance").length,
        disclosureTargetsChecked: all("details > summary").length,
        errors
      };
    })()
  `;

  const result = await client.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true
  });

  if (result.exceptionDetails) {
    throw new Error(`Measurement evaluation failed: ${JSON.stringify(result.exceptionDetails)}`);
  }
  return result.result.value;
}

async function cbLabCaptureOne(debuggingUrl, variant, fixtureName, viewport) {
  const connection = await cbLabConnectCdp(debuggingUrl);
  const { client } = connection;

  try {
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    await client.send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.width < 700,
      screenWidth: viewport.width,
      screenHeight: viewport.height,
      screenOrientation: {
        type: "portraitPrimary",
        angle: 0
      }
    });
    await client.send("Emulation.setEmulatedMedia", {
      features: [
        { name: "prefers-color-scheme", value: "dark" },
        { name: "prefers-reduced-motion", value: "reduce" }
      ]
    });

    const pageUrl = new URL(
      pathToFileURL(join(labRoot, variant.directory, "index.html")).href
    );
    pageUrl.searchParams.set("fixture", fixtureName);
    pageUrl.searchParams.set("capture", "1");

    const loaded = client.waitFor("Page.loadEventFired");
    await client.send("Page.navigate", { url: pageUrl.href });
    await loaded;
    await delay(60);

    const measurements = await cbLabCaptureMeasurements(
      client,
      fixtureName,
      variant.key,
      viewport
    );

    const screenshot = await client.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
      optimizeForSpeed: false
    });
    const outputDirectory = join(screenshotRoot, variant.directory);
    await mkdir(outputDirectory, { recursive: true });
    const outputName = `${fixtureName}-${viewport.width}x${viewport.height}.png`;
    const outputPath = join(outputDirectory, outputName);
    await writeFile(outputPath, Buffer.from(screenshot.data, "base64"));

    return {
      ...measurements,
      screenshot: `screenshots/${variant.directory}/${outputName}`
    };
  } finally {
    await cbLabCloseTarget(connection);
  }
}

async function main() {
  const profileDirectory = await import("node:fs/promises")
    .then(({ mkdtemp }) => mkdtemp(join(tmpdir(), "cb-lab-chrome-")));
  const chromeProcess = spawn(chromeExecutable, [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=Translate,MediaRouter",
    "--disable-sync",
    "--font-render-hinting=none",
    "--hide-scrollbars",
    "--mute-audio",
    "--no-first-run",
    "--remote-debugging-port=0",
    `--user-data-dir=${profileDirectory}`,
    "about:blank"
  ], {
    stdio: ["ignore", "ignore", "pipe"]
  });

  const results = [];
  let debuggingUrl;

  try {
    debuggingUrl = await cbLabWaitForChrome(chromeProcess);

    for (const variant of variants) {
      const viewports = quickMode
        ? normalViewports.filter((viewport) => viewport.width === 390 || viewport.width === 1280)
        : normalViewports;
      for (const viewport of viewports) {
        results.push(await cbLabCaptureOne(debuggingUrl, variant, "normal", viewport));
      }

      if (!quickMode) {
        for (const fixtureName of exceptionFixtures) {
          for (const viewport of exceptionViewports) {
            results.push(await cbLabCaptureOne(
              debuggingUrl,
              variant,
              fixtureName,
              viewport
            ));
          }
        }
      }
    }
  } finally {
    chromeProcess.kill("SIGTERM");
    await delay(120);
    await rm(profileDirectory, { recursive: true, force: true });
  }

  const measurementOutput = {
    generatedAt: new Date().toISOString(),
    authority: {
      main: "8bf3b58a98120c43860a689756d84950a0b3aadb",
      visualAudit: "c2299f9f7358ccbea2109b79a616717f34a97024",
      firstScreenRecon: "19178e504ef0a41caf54e544aacbcc61c047d174",
      pinnedPublish: "77e9fc8b0780133994058f5a8fb82daf60ed1a3d"
    },
    method: {
      browser: "Google Chrome headless via Chrome DevTools Protocol",
      screenshotType: "exact viewport, deviceScaleFactor 1",
      fullBorderCount: "fully bordered containers ending before the candidate identity",
      foldVisibility: "computed at scrollY=0 with prototype controls hidden"
    },
    captures: results,
    requiredMeasurements: Object.fromEntries(
      variants.map((variant) => [
        `variant-${variant.key}`,
        {
          "390x844": results.find((entry) =>
            entry.variant === variant.key &&
            entry.fixture === "normal" &&
            entry.viewport.width === 390
          ),
          "1280x800": results.find((entry) =>
            entry.variant === variant.key &&
            entry.fixture === "normal" &&
            entry.viewport.width === 1280
          )
        }
      ])
    )
  };

  await writeFile(measurementsPath, JSON.stringify(measurementOutput, null, 2) + "\n");

  const failures = results.flatMap((result) =>
    result.errors.map((error) =>
      `${result.variant}/${result.fixture}/${result.viewport.width}x${result.viewport.height}: ${error}`
    )
  );

  if (failures.length) {
    console.error(failures.join("\n"));
    console.error(`Visual validation failed with ${failures.length} error(s).`);
    process.exitCode = 1;
    return;
  }

  console.log(`${results.length} screenshots captured`);
  console.log("0 overflow failures");
  console.log("0 critical-content failures");
  console.log(`measurements written: ${measurementsPath}`);
}

await main();
