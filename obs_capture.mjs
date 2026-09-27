// obs_capture.mjs (2026-09-27): a minimal obs-websocket v5 client for watching KovaaK's through OBS.
// Connection settings (host, port, password, source) come from KovOBS's config; the password is never printed.
//   node obs_capture.mjs info                       version, scene, inputs (no capture)
//   node obs_capture.mjs shot <out.png> [width]     one screenshot of the game source
//   node obs_capture.mjs burst <dir> <n> [width]    n screenshots as fast as OBS returns them, with timestamps
//   node obs_capture.mjs fast <dir> <secs> [width] [quality]   JPEG frames as fast as OBS returns them
//   node obs_capture.mjs onstart <dir> <secs> [scenario] ...   the same, from the moment KovaaK's logs the
//                                                  scenario's start (so the user starts it after "go")
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync, statSync, openSync, readSync, closeSync, readdirSync, rmSync }
  from "node:fs";
import { join } from "node:path";

const cfg = JSON.parse(readFileSync(join(process.env.APPDATA, "KovOBS", "config.json"), "utf8")).obs;
const [cmd, ...args] = process.argv.slice(2);
const sha = (s) => createHash("sha256").update(s).digest("base64");

const ws = new WebSocket(`ws://${cfg.host}:${cfg.port}`);
let nextId = 0;
const pending = new Map();
const request = (requestType, requestData = {}) =>
  new Promise((resolve, reject) => {
    const requestId = String(++nextId);
    pending.set(requestId, { resolve, reject });
    ws.send(JSON.stringify({ op: 6, d: { requestType, requestId, requestData } }));
  });

ws.onerror = (e) => { console.error("connection error:", e.message || e.type); process.exit(1); };
ws.onmessage = async (msg) => {
  const { op, d } = JSON.parse(msg.data);
  if (op === 0) {                                   // Hello: identify, with auth if OBS asks for it
    const identify = { rpcVersion: 1 };
    if (d.authentication) {
      identify.authentication = sha(sha(cfg.password + d.authentication.salt) + d.authentication.challenge);
    }
    ws.send(JSON.stringify({ op: 1, d: identify }));
  } else if (op === 2) {                            // Identified
    try { await run(); } catch (e) { console.error("error:", e.message); }
    ws.close();
  } else if (op === 7) {                            // RequestResponse
    const p = pending.get(d.requestId);
    pending.delete(d.requestId);
    if (d.requestStatus.result) p.resolve(d.responseData || {});
    else p.reject(new Error(`${d.requestType}: ${d.requestStatus.code} ${d.requestStatus.comment || ""}`));
  }
};

async function shot(width) {
  const data = { sourceName: cfg.source_name, imageFormat: "png" };
  if (width) data.imageWidth = Number(width);
  const r = await request("GetSourceScreenshot", data);
  return Buffer.from(r.imageData.split(",")[1], "base64");
}

async function capture(dir, secs, width, quality, meta, restarted = null) {
  mkdirSync(dir, { recursive: true });
  for (const f of readdirSync(dir)) if (/^f\d+\.jpg$/.test(f)) rmSync(join(dir, f));   // a restart starts clean
  const times = [];
  const t0 = performance.now();
  const wall0 = Date.now();
  let i = 0, lastCheck = 0;
  while (performance.now() - t0 < Number(secs) * 1000) {
    const t = performance.now() - t0;
    if (restarted && t - lastCheck > 200) {           // every 0.2 s: did the scenario start again?
      lastCheck = t;
      if (restarted()) return true;                  // frames are overwritten by the next capture
    }
    const r = await request("GetSourceScreenshot", { sourceName: cfg.source_name, imageFormat: "jpg",
      imageWidth: Number(width), imageCompressionQuality: Number(quality) });
    writeFileSync(join(dir, `f${String(i++).padStart(4, "0")}.jpg`), Buffer.from(r.imageData.split(",")[1], "base64"));
    times.push(t);
  }
  writeFileSync(join(dir, "times.json"), JSON.stringify(times));
  writeFileSync(join(dir, "meta.json"), JSON.stringify({ ...meta, captureStart: wall0 }));
  console.log(`${i} frames in ${secs} s (${(i / Number(secs)).toFixed(1)} per s)`);
}

async function run() {
  if (cmd === "info") {
    const v = await request("GetVersion");
    console.log("OBS", v.obsVersion, "websocket", v.obsWebSocketVersion);
    const s = await request("GetCurrentProgramScene");
    console.log("program scene:", s.currentProgramSceneName ?? s.sceneName);
    const inputs = await request("GetInputList");
    console.log("inputs:", inputs.inputs.map((i) => `${i.inputName} (${i.inputKind})`).join("; "));
    console.log("KovOBS source:", cfg.source_name);
    const t0 = performance.now();
    const img = await shot(640);                    // timing only; the image is not kept
    console.log(`screenshot works: ${img.length} bytes at 640 wide in ${(performance.now() - t0).toFixed(0)} ms`);
  } else if (cmd === "shot") {
    writeFileSync(args[0], await shot(args[1]));
    console.log("saved", args[0]);
  } else if (cmd === "fast") {                     // fast <dir> <seconds> [width] [quality]: JPEG frames for motion
    const [dir, secs, width = "1280", quality = "80"] = args;
    await capture(dir, secs, width, quality, {});
  } else if (cmd === "onstart") {
    // onstart <dir> <seconds> [scenario] [width] [quality] [wait seconds]: wait for KovaaK's to log a scenario start
    // (the kovaaks-events method: its log records "Scenario start broadcast: '<name>'"), then capture as fast does.
    // Frame times count from the capture's start; meta.json holds the logged start and when it was seen.
    const [dir, secs, scenario = "", width = "1280", quality = "80", wait = "600"] = args;
    const logPath = join(process.env.LOCALAPPDATA, "FPSAimTrainer", "Saved", "Logs", "FPSAimTrainer.log");
    let pos = statSync(logPath).size, rest = "";
    const deadline = Date.now() + Number(wait) * 1000;
    console.log(`waiting for ${scenario ? `'${scenario}'` : "any scenario"} to start`);
    for (;;) {
      if (Date.now() > deadline) throw new Error("no scenario start seen");
      const size = statSync(logPath).size;
      if (size < pos) pos = 0;                       // the game started a new log
      if (size > pos) {
        const buf = Buffer.alloc(size - pos);
        const fd = openSync(logPath, "r");
        readSync(fd, buf, 0, buf.length, pos);
        closeSync(fd);
        pos = size;
        const lines = (rest + buf.toString("utf8")).split(/\r?\n/);
        rest = lines.pop();
        const hit = lines.map((l) => l.match(
          /^\[(\d{4})\.(\d\d)\.(\d\d)-(\d\d)\.(\d\d)\.(\d\d):(\d{3})\].*Scenario start broadcast: '(.+?)'/))
          .find((m) => m && (!scenario || m[8] === scenario));
        if (hit) {
          const [, Y, M, D, h, mi, s, ms, name] = hit;
          const logTs = Date.UTC(+Y, +M - 1, +D, +h, +mi, +s, +ms);   // the log's stamps are UTC
          console.log(`'${name}' started (logged ${new Date(logTs).toISOString()}, seen ${Date.now() - logTs} ms later)`);
          // a restart logs a new start: then the capture starts over, so it always holds the last attempt
          const restarted = () => {
            const size2 = statSync(logPath).size;
            if (size2 <= pos) return false;
            const b2 = Buffer.alloc(size2 - pos);
            const fd2 = openSync(logPath, "r");
            readSync(fd2, b2, 0, b2.length, pos);
            closeSync(fd2);
            pos = size2;
            return b2.toString("utf8").includes(`Scenario start broadcast: '${name}'`);
          };
          for (;;) {
            const again = await capture(dir, secs, width, quality, { scenario: name, logStart: logTs,
              seenAt: Date.now() }, restarted);
            if (!again) return;
            console.log("restarted: capturing again from the new start");
          }
        }
      }
      await new Promise((r) => setTimeout(r, 50));
    }
  } else if (cmd === "burst") {
    const [dir, n, width] = args;
    mkdirSync(dir, { recursive: true });
    const times = [];
    const t0 = performance.now();
    for (let i = 0; i < Number(n); i++) {
      const t = performance.now() - t0;
      writeFileSync(join(dir, `f${String(i).padStart(3, "0")}.png`), await shot(width));
      times.push(t);
    }
    writeFileSync(join(dir, "times.json"), JSON.stringify(times));
    console.log(`${n} frames in ${((performance.now() - t0) / 1000).toFixed(2)} s`);
  }
}
