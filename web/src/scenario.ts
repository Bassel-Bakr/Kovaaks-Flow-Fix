// The scenario file: the template's profiles with this track's settings, and the map (room, chalk, waypoints).
// A port of trace_track.build_track.
import { type Pt, dist, check, radius3, rdp, INF } from "./geometry.ts";
import { type Shape, svgLines, fit, prepare } from "./svg.ts";
import { planTour, layPath, routeLength } from "./tour.ts";
import { MapPieces, chains } from "./carve.ts";
import { lectureHall, CHALK } from "./hall.ts";
import { TEMPLATE } from "./template.ts";

export interface Options {
  name: string;
  description: string;                 // "{tour}" becomes the shapes in the order the bot visits them
  speed: number;                       // deg/s
  rBot: number;                        // deg
  box: Pt;                             // the board's half width and half height, deg
  turnR: number;
  clear: number;
  tags: string;
  prepared?: boolean;                  // the shapes already have points STEP apart and no tight turns
  maxHop?: number;                     // deg: the longest straight hop between shapes
}

export const DEFAULTS: Options = {
  name: "My Drawing",
  description: "Smooth tracking along a path you can see.[nl]The bot traces the drawing on the chalkboard: {tour}. "
    + "Hold fire: every second on the bot scores 100.",
  speed: 5, rBot: 0.4, box: [41, 20], turnR: 0.25, clear: 0.3, tags: "Tracking, Smooth",
};

export interface Result {
  sce: string;
  shapes: Shape[];
  path: Pt[];
  routes: Pt[][];
  seconds: number;
  waypoints: number;
  objects: number;
  warnings: string[];
}

const C = TEMPLATE.consts;
const f1 = (v: number) => v.toFixed(1);
const f6 = (v: number) => v.toFixed(6);

function setKey(lines: string[], section: string | null, key: string, value: string): void {
  let inside = section === null, current = "";
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (l.startsWith("[")) { inside = false; current = l; continue; }
    if (section !== null && l.startsWith("Name=")) inside = `${current}|${l.slice(5)}` === section;
    if (inside && l.startsWith(key + "=")) { lines[i] = `${key}=${value}`; return; }
  }
  throw new Error(`no ${key} in ${section ?? "the scenario settings"}`);
}

function dumpMap(m: any): string {
  // indented like the game writes it, with compact mesh data (one vertex a line, 60 indices a line)
  const meshes: any[] = [];
  const copy = { ...m, objects: m.objects.map((o: any) => {
    if (!o.procedural) return o;
    meshes.push(o.procedural);
    return { ...o, procedural: `@@mesh${meshes.length - 1}@@` };
  }) };
  let text = JSON.stringify(copy, null, 4);
  meshes.forEach((secs, k) => {
    const parts = secs.map((sec: any) => {
      const rows: string[] = [];
      for (let i = 0; i < sec.indices.length; i += 60) rows.push(sec.indices.slice(i, i + 60).join(","));
      return `{"indices":[\n${rows.join(",\n")}\n],"vertices":[\n${sec.vertices.map((v: any) => JSON.stringify(v)).join(",\n")}\n]}`;
    });
    text = text.replace(`"@@mesh${k}@@"`, `[\n${parts.join(",\n")}\n]`);
  });
  return text;
}

export function buildFromSvg(svgText: string, options: Partial<Options> = {}): Result {
  const o: Options = { ...DEFAULTS, ...options };
  const lines = svgLines(svgText);
  if (!lines.length) throw new Error("no lines in the drawing");
  return buildTrack(fit(lines, o.box), o);
}

export function buildTrack(shapesIn: Shape[], o: Options): Result {
  const warnings: string[] = [];
  const log = (msg: string) => { if (msg.startsWith("WARNING")) warnings.push(msg.slice(8)); };
  const shapes = o.prepared ? shapesIn.map((s) => ({ ...s, points: s.points.slice() })) : shapesIn.map((s) => prepare(s, o.turnR));
  for (const s of shapes) {
    const [, close] = check(s.points, o.clear, s.closed);
    if (close < o.clear) log(`WARNING ${s.name}: two parts of the line only ${close.toFixed(2)} deg apart (the bot may cut across)`);
  }
  let tour = null;
  for (const c of [o.clear, o.clear / 2, 0]) {         // hops keep clear of the lines; relaxed only if nothing else works
    tour = planTour(shapes, c, o.maxHop ?? INF, log);
    if (tour) break;
    log(`WARNING no tour whose hops keep ${c.toFixed(2)} deg clear of the lines; trying less`);
  }
  if (!tour) throw new Error("no tour found");
  const laid = layPath(shapes, tour, log);
  for (const r of laid.routes) {
    const inner = r.filter((p) => Math.min(dist(p, r[0]), dist(p, r[r.length - 1])) > 0.6);
    let c = 99;
    for (let i = 0; i < inner.length; i += 2) for (const s of laid.shapes) for (let j = 0; j < s.points.length; j += 2) c = Math.min(c, dist(inner[i], s.points[j]));
    if (c < 0.15) log(`WARNING a route passes ${c.toFixed(2)} deg from a line`);
  }
  const path = laid.path;
  const total = routeLength([...path, path[0]]);
  const seconds = total / (o.speed * 0.91);

  // the profiles: the template with this track's name, time, tags and bot
  const head = TEMPLATE.head.split("\n");
  const v = (o.speed * Math.PI / 180) * C.D_BOT * C.SCALE, acc = v * 12;
  const rW = C.D_BOT * C.SCALE * Math.tan(o.rBot * Math.PI / 180);
  const ride = 0.45 * rW / C.SCALE;                    // a flyer rides this far above its waypoints (map units)
  const slug = o.name.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  setKey(head, null, "Name", o.name);
  setKey(head, null, "Description", o.description.replace("{tour}", laid.tourNames.join(", ")));
  setKey(head, null, "Timelimit", f1(Math.ceil(seconds) + 1));
  setKey(head, null, "MapName", `${slug}.json`);
  setKey(head, null, "SearchTags", o.tags);
  const bot = "[Character Profile]|tracer";
  for (const [k, val] of [["MainBBRadius", f1(rW)], ["MainBBHeight", f1(2 * rW)], ["ProjBBRadius", f1(rW * 60 / 65)],
    ["ProjBBHeight", f1(2 * rW * 64 / 65)], ["MaxSpeed", f1(v)], ["Acceleration", f1(acc)], ["FlightVelocityUp", f1(v)],
    ["FlightVelocityDown", f1(v)], ["FlightAccelUp", f1(acc)], ["FlightAccelDown", f1(acc)]]) setKey(head, bot, k, val);

  // the map: the base, the room, the chalk, the waypoints
  const m: any = JSON.parse(JSON.stringify(TEMPLATE.map));
  const wallPt = (p: Pt): Pt => [C.D_WALL * Math.tan(p[0] * Math.PI / 180), C.D_WALL * Math.tan(p[1] * Math.PI / 180)];
  const bw = C.D_WALL * Math.tan(o.box[0] * Math.PI / 180), bh = C.D_WALL * Math.tan(o.box[1] * Math.PI / 180);
  const pieces = new MapPieces();
  pieces.section();
  lectureHall(pieces, bw, bh);
  pieces.section();
  pieces.beginMesh();
  for (const s of laid.shapes) {
    const wall = s.points.map(wallPt);
    let line: Pt[];
    if (s.closed) {
      const half = Math.floor(wall.length / 2);
      line = [...rdp(wall.slice(0, half + 1), 1.5).slice(0, -1), ...rdp([...wall.slice(half), wall[0]], 1.5)];
    } else line = rdp(wall, 1.5);
    pieces.ribbon(CHALK, line, C.FACE_X - 6, 12, s.closed);
  }
  for (const route of laid.routes) {                   // dashes: one simplified ribbon per dash
    const dense: Pt[] = [route[0]];
    for (let i = 0; i + 1 < route.length; i++) {
      const p = route[i], q = route[i + 1];
      const steps = Math.max(1, Math.floor(dist(p, q) / 0.05));
      for (let j = 1; j <= steps; j++) dense.push([p[0] + (q[0] - p[0]) * j / steps, p[1] + (q[1] - p[1]) * j / steps]);
    }
    let run = 0, dash: Pt[] = [];
    for (let i = 0; i + 1 < dense.length; i++) {
      const p = dense[i], q = dense[i + 1];
      if (Math.floor(run / 0.5) % 2 === 0) dash.push(p);
      else if (dash.length) { pieces.ribbon(CHALK, rdp([...dash, p].map(wallPt), 1.0), C.FACE_X - 6, 12 * 0.8); dash = []; }
      run += dist(p, q);
    }
    if (dash.length) pieces.ribbon(CHALK, rdp(dash.map(wallPt), 1.0), C.FACE_X - 6, 12 * 0.8);
  }
  pieces.endMesh();
  m.objects.push(...pieces.objects);

  // the bot's waypoints: the path in the bot's plane, 0.125 s apart, lowered so its centre runs on the line
  const plane: Pt[] = path.map(([a, b]) => [Math.tan(a * Math.PI / 180), Math.tan(b * Math.PI / 180)]);
  const step = (o.speed * Math.PI / 180) * 0.125;
  const wps: Pt[] = [plane[0]];
  let carry = 0;
  for (let i = 0; i < plane.length; i++) {
    const p0 = plane[i], p1 = plane[(i + 1) % plane.length];
    const seg = dist(p0, p1);
    let dd = step - carry;
    while (dd <= seg) { wps.push([p0[0] + (p1[0] - p0[0]) * dd / seg, p0[1] + (p1[1] - p0[1]) * dd / seg]); dd += step; }
    carry = seg - (dd - step);
  }
  if (dist(wps[wps.length - 1], wps[0]) < step / 2) wps.pop();
  const names = wps.map((_, i) => `w${i}`);
  wps.forEach(([u, w], i) => m.objects.push({
    location: `${f6(C.X_BOT)}, ${f6(C.D_BOT * u)}, ${f6(C.D_BOT * w - ride)}`, name: "Waypoint",
    properties: [{ name: "Name", value: names[i] }, { name: "BotPauseTimeMin", value: 0.0 }, { name: "BotPauseTimeMax", value: 0.0 }],
    rotation: "0.000000, 0.000000, 0.000000", scale: "0.100000, 0.100000, 0.100000", type: "gameObject",
  }));
  const sp: any = JSON.parse(JSON.stringify(TEMPLATE.spawn));
  const [u0, v0] = wps[0];
  sp.name = "SpawnPoint";
  sp.location = `${f6(C.X_BOT)}, ${f6(C.D_BOT * u0)}, ${f6(C.D_BOT * v0 - 2 * rW / C.SCALE)}`;
  sp.scale = "0.100000, 0.100000, 0.100000";
  for (const q of sp.properties) {
    if (q.name === "Path") q.value = [...names.slice(1), names[0]].join(",");
    else if (q.name === "LoopingPath") q.value = true;
    else if (q.name === "PermittedCharacterProfiles") q.value = "tracer";
  }
  m.objects.push(sp);
  const player = m.objects.find((ob: any) => ob.name === "SpawnPoint"
    && ob.properties?.some((q: any) => q.name === "TeamMask" && q.value === 1));
  player.rotation = `0.000000, ${f6(Math.atan(v0 / Math.sqrt(1 + u0 * u0)) * 180 / Math.PI)}, ${f6(Math.atan(u0) * 180 / Math.PI)}`;

  let rMin = INF;
  for (let i = 0; i < path.length; i++) rMin = Math.min(rMin, radius3(path[(i - 5 + path.length) % path.length], path[i], path[(i + 5) % path.length]));
  if (rMin < o.turnR * 0.5) warnings.push(`the tightest turn has a radius of ${rMin.toFixed(2)} deg`);
  const sce = (head.join("\n") + "[Map Data]\n" + dumpMap(m)).replace(/\n/g, "\r\n");
  return { sce, shapes: laid.shapes, path, routes: laid.routes, seconds, waypoints: wps.length,
    objects: m.objects.length, warnings };
}

