import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const COMMAND_TIMEOUT = 15_000;
const START_TIMEOUT = 15_000;
const FIXED_NOW = Date.parse("2026-08-23T20:00:00Z");
const FIXED_DATE_SCRIPT = `(() => {
  const fixedNow = ${FIXED_NOW};
  const NativeDate = Date;
  class FixedDate extends NativeDate {
    constructor(...args) { super(...(args.length ? args : [fixedNow])); }
    static now() { return fixedNow; }
  }
  globalThis.Date = FixedDate;
})()`;

function waitForChrome(process) {
  return new Promise((resolve, reject) => {
    let stderr = "";
    let settled = false;
    const finish = (fn, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      fn(value);
    };
    const timer = setTimeout(() => finish(reject, new Error(`Chrome DevTools endpoint did not start: ${stderr.slice(-2000)}`)), START_TIMEOUT);
    process.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
      const match = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) finish(resolve, match[1]);
    });
    process.once("error", (error) => finish(reject, error));
    process.once("exit", (code) => finish(reject, new Error(`Chrome exited before DevTools was ready (code ${code}): ${stderr.slice(-2000)}`)));
  });
}

function cdpClient(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  const pending = new Map();
  const events = new Map();
  let nextId = 0;
  let closed = false;
  const ready = new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  socket.addEventListener("message", async ({ data }) => {
    const text = typeof data === "string" ? data : data instanceof Blob ? await data.text() : Buffer.from(data).toString("utf8");
    const message = JSON.parse(text);
    if (message.id && pending.has(message.id)) {
      const entry = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(entry.timer);
      if (message.error) entry.reject(new Error(`${entry.method}: ${message.error.message}`));
      else entry.resolve(message.result ?? {});
      return;
    }
    const listeners = events.get(message.method);
    if (listeners) {
      events.delete(message.method);
      for (const listener of listeners) { clearTimeout(listener.timer); listener.resolve(message.params ?? {}); }
    }
  });
  socket.addEventListener("close", () => {
    closed = true;
    for (const entry of pending.values()) { clearTimeout(entry.timer); entry.reject(new Error("CDP socket closed with a command pending")); }
    pending.clear();
  });
  return {
    async send(method, params = {}) {
      await ready;
      if (closed) throw new Error("CDP socket is closed");
      const id = ++nextId;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP command timed out: ${method}`)); }, COMMAND_TIMEOUT);
        pending.set(id, { method, resolve, reject, timer });
        socket.send(JSON.stringify({ id, method, params }));
      });
    },
    waitFor(method) {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`CDP event timed out: ${method}`)), COMMAND_TIMEOUT);
        const listeners = events.get(method) ?? [];
        listeners.push({ resolve, reject, timer });
        events.set(method, listeners);
      });
    },
    close() { if (!closed) socket.close(); }
  };
}

export async function launchChrome({ executable = process.env.CB_VISUAL_LAB_CHROME || "/usr/bin/google-chrome" } = {}) {
  const profileDirectory = await mkdtemp(join(tmpdir(), "cb-visual-lab-"));
  const chromeProcess = spawn(executable, [
    "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-background-networking",
    "--disable-component-update", "--disable-default-apps", "--disable-extensions",
    "--disable-features=Translate,MediaRouter", "--disable-sync", "--font-render-hinting=none",
    "--hide-scrollbars", "--mute-audio", "--no-first-run", "--remote-debugging-port=0",
    `--user-data-dir=${profileDirectory}`, "about:blank"
  ], { stdio: ["ignore", "ignore", "pipe"] });
  try {
    const debuggingUrl = await waitForChrome(chromeProcess);
    const endpoint = new URL(debuggingUrl);
    return { process: chromeProcess, profileDirectory, debuggingUrl, browserHost: endpoint.host };
  } catch (error) {
    chromeProcess.kill("SIGTERM");
    await rm(profileDirectory, { recursive: true, force: true });
    throw error;
  }
}

export async function createTarget(chrome) {
  const response = await fetch(`http://${chrome.browserHost}/json/new?${encodeURIComponent("about:blank")}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Could not create Chrome target: ${response.status}`);
  const target = await response.json();
  return { ...target, browserHost: chrome.browserHost, client: cdpClient(target.webSocketDebuggerUrl) };
}

export async function closeTarget(target) {
  target.client.close();
  try { await fetch(`http://${target.browserHost}/json/close/${encodeURIComponent(target.id)}`); } catch { /* shutdown is the fallback */ }
}

export async function enablePageRuntime(target) {
  await target.client.send("Page.enable");
  await target.client.send("Runtime.enable");
}

export async function configureViewport(target, width, height) {
  await target.client.send("Emulation.setDeviceMetricsOverride", {
    width, height, deviceScaleFactor: 1, mobile: false,
    screenWidth: width, screenHeight: height,
    screenOrientation: { type: "portraitPrimary", angle: 0 }
  });
  await target.client.send("Emulation.setEmulatedMedia", { features: [
    { name: "prefers-color-scheme", value: "dark" },
    { name: "prefers-reduced-motion", value: "reduce" }
  ] });
  await target.client.send("Emulation.setTimezoneOverride", { timezoneId: "America/Vancouver" });
}

export async function navigateFile(target, filePath) {
  const file = await stat(filePath);
  if (!file.isFile()) throw new Error(`HTML path is not a regular file: ${filePath}`);
  const contents = await readFile(filePath);
  if (!contents.length) throw new Error(`HTML file is empty: ${filePath}`);
  await target.client.send("Page.addScriptToEvaluateOnNewDocument", { source: FIXED_DATE_SCRIPT });
  const loaded = target.client.waitFor("Page.loadEventFired");
  await target.client.send("Page.navigate", { url: pathToFileURL(filePath).href });
  await loaded;
}

export async function setRootFontScale(target, percent = 100) {
  if (!Number.isFinite(percent) || percent <= 0) throw new RangeError("font scale must be a positive number");
  const expression = percent === 100
    ? "document.documentElement.style.removeProperty('font-size');"
    : `document.documentElement.style.setProperty('font-size', ${JSON.stringify(`${percent}%`)}, 'important');`;
  await evaluate(target, expression);
  await evaluate(target, "document.fonts?.ready ?? Promise.resolve()");
}

/**
 * Apply candidate CSS to the already-loaded, immutable document as a trailing
 * <style> element. The source HTML file on disk is never rewritten; the override
 * lives only in the live DOM. Equal-specificity, later-source-order lets a rule
 * that reuses the production selector win over the production stylesheet.
 * Returns proof of application for the report.
 */
export async function injectCss(target, css, id = "lab-candidate-override") {
  const expression = `(() => {
    const css = ${JSON.stringify(String(css))};
    const previous = document.getElementById(${JSON.stringify(id)});
    if (previous) previous.remove();
    const style = document.createElement("style");
    style.id = ${JSON.stringify(id)};
    style.setAttribute("data-lab-candidate", "1");
    style.textContent = css;
    document.head.appendChild(style);
    let ruleCount = null;
    try { ruleCount = style.sheet ? style.sheet.cssRules.length : null; } catch { ruleCount = null; }
    return {
      injected: document.getElementById(${JSON.stringify(id)}) !== null,
      chars: css.length,
      ruleCount,
      isLastHeadStyle:
        document.head.querySelector("style:last-of-type") === style
    };
  })()`;
  return evaluate(target, expression);
}

export async function evaluate(target, expression) {
  const result = await target.client.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(`Evaluation failed: ${JSON.stringify(result.exceptionDetails)}`);
  return result.result?.value;
}

export async function captureScreenshot(target, outputPath) {
  const result = await target.client.send("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false, optimizeForSpeed: false });
  await writeFile(outputPath, Buffer.from(result.data, "base64"));
  return outputPath;
}

export async function shutdownChrome(chrome) {
  if (!chrome) return;
  if (chrome.process.exitCode === null) {
    chrome.process.kill("SIGTERM");
    await new Promise((resolve) => chrome.process.once("exit", resolve));
  }
  await rm(chrome.profileDirectory, {
    recursive: true,
    force: true,
    maxRetries: 5,
    retryDelay: 50
  });
}

export { FIXED_NOW };
