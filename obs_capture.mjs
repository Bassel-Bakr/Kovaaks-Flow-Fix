// obs_capture.mjs (2026-09-27): a minimal obs-websocket v5 client for watching KovaaK's through OBS.
// Connection settings (host, port, password, source) come from KovOBS's config; the password is never printed.
//   node obs_capture.mjs info                       version, scene, inputs (no capture)
//   node obs_capture.mjs shot <out.png> [width]     one screenshot of the game source
//   node obs_capture.mjs burst <dir> <n> [width]    n screenshots as fast as OBS returns them, with timestamps
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
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
    mkdirSync(dir, { recursive: true });
    const times = [];
    const t0 = performance.now();
    let i = 0;
    while (performance.now() - t0 < Number(secs) * 1000) {
      const t = performance.now() - t0;
      const r = await request("GetSourceScreenshot", { sourceName: cfg.source_name, imageFormat: "jpg",
        imageWidth: Number(width), imageCompressionQuality: Number(quality) });
      writeFileSync(join(dir, `f${String(i++).padStart(4, "0")}.jpg`), Buffer.from(r.imageData.split(",")[1], "base64"));
      times.push(t);
    }
    writeFileSync(join(dir, "times.json"), JSON.stringify(times));
    console.log(`${i} frames in ${secs} s (${(i / Number(secs)).toFixed(1)} per s)`);
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
