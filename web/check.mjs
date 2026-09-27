// Regression check: the browser builder (web/src) against the Python one (trace_track.py) on World Map's coasts.
// Run web/export_shapes.py first (it writes test_out/wm_shapes.json), then: node web/check.mjs
// The two must lay the same tour: identical waypoints, blocks and spawn points (labels are Python-only for now).
import { readFileSync } from "node:fs";
const { buildTrack, DEFAULTS } = await import("./src/scenario.ts");
const shapes = JSON.parse(readFileSync("test_out/wm_shapes.json", "utf8"));
const r = buildTrack(shapes, { ...DEFAULTS, name: "World Map", prepared: true, maxHop: 40 });
const map = (text) => JSON.parse(text.split("[Map Data]")[1]);
const ts = map(r.sce), py = map(readFileSync("out/World Map.sce", "utf8"));
const pick = (m, f) => m.objects.filter(f).map((o) => `${o.location}|${o.scale ?? ""}|${o.rotation ?? ""}`).join("\n");
const same = (f) => pick(ts, f) === pick(py, f);
const results = {
  waypoints: same((o) => o.name === "Waypoint"),
  blocks: same((o) => o.type === "brush" && !o.procedural),
  spawnPoints: same((o) => o.name === "SpawnPoint"),
};
console.log(results);
if (!Object.values(results).every(Boolean)) process.exit(1);
