// trace_track.js: a KovaaK's tracking scenario from a drawing. Built from web/src by web/build.mjs; do not edit.
// Include it and add <div data-trace-track></div> where the tool should appear.
(function () {
"use strict";
// ---- geometry.ts
const __geometry_ts = (() => {

// Geometry on the board, in degrees (x across, y up). A port of trace_track.py's helpers.

                                  
const STEP = 0.05;              // deg between the points of every line
const INF = Infinity;

function dist(a    , b    )         {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

function at   (arr     , i        )    {
  const n = arr.length;
  return arr[((i % n) + n) % n];
}

function resample(pts      , h         = STEP, closed          = true)       {
  const src = closed ? [...pts, pts[0]] : [...pts];
  const out       = [src[0]];
  let carry = 0;
  for (let k = 0; k + 1 < src.length; k++) {
    const p0 = src[k], p1 = src[k + 1];
    const seg = dist(p0, p1);
    let d = h - carry;
    while (d <= seg) {
      out.push([p0[0] + (p1[0] - p0[0]) * d / seg, p0[1] + (p1[1] - p0[1]) * d / seg]);
      d += h;
    }
    carry = seg - (d - h);
  }
  if (closed) return dist(out[out.length - 1], out[0]) < h / 2 ? out.slice(0, -1) : out;
  const last = src[src.length - 1];
  if (dist(out[out.length - 1], last) > 1e-9) out.push(last);
  return out;
}

function turnAngle(a    , b    , c    )         {
  const t = Math.atan2(c[1] - b[1], c[0] - b[0]) - Math.atan2(b[1] - a[1], b[0] - a[0]) + Math.PI;
  return Math.abs((((t % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI);
}

// Smooth only the turns tighter than `radius` (and a few samples round them), a little each round.
function ease(pts      , radius        , closed          = true, gap         = 4, rounds         = 60)       {
  const n = pts.length;
  for (let r = 0; r < rounds; r++) {
    const tight = new Set        ();
    const lo = closed ? 0 : gap, hi = closed ? n : n - gap;
    for (let i = lo; i < hi; i++) {
      const a = at(pts, i - gap), b = pts[i], c = at(pts, i + gap);
      const t = turnAngle(a, b, c);
      if (t > 1e-9 && (dist(a, b) + dist(b, c)) / 2 / t < radius) {
        for (let j = -2 * gap; j <= 2 * gap; j++) {
          tight.add(closed ? (((i + j) % n) + n) % n : Math.min(Math.max(i + j, 1), n - 2));
        }
      }
    }
    if (tight.size === 0) break;
    const next = pts.slice();
    for (const i of tight) {
      const p = at(pts, i - 1), q = pts[i], s = at(pts, i + 1);
      next[i] = [(p[0] + 2 * q[0] + s[0]) / 4, (p[1] + 2 * q[1] + s[1]) / 4];
    }
    pts = next;
  }
  return resample(pts, STEP, closed);
}

// (tightest turn radius, closest approach of two parts of the line more than a few samples apart), in deg.
function check(pts      , clear        , closed          = true)                   {
  const n = pts.length;
  let tight = 1e9;
  for (let i = closed ? 0 : 4; i < (closed ? n : n - 4); i++) {
    const a = at(pts, i - 4), b = pts[i], c = at(pts, i + 4);
    const t = turnAngle(a, b, c);
    if (t > 1e-9) tight = Math.min(tight, (dist(a, b) + dist(b, c)) / 2 / t);
  }
  const grid = new Map                  ();
  const gap = Math.floor(4 * clear / 0.1);
  pts.forEach(([y, z], i) => {
    const key = `${Math.floor(y / clear)},${Math.floor(z / clear)}`;
    if (!grid.has(key)) grid.set(key, []);
    grid.get(key) .push(i);
  });
  let close = 1e9;
  for (let i = 0; i < n; i += 3) {
    const [y, z] = pts[i];
    for (let a = -1; a <= 1; a++) {
      for (let b = -1; b <= 1; b++) {
        for (const j of grid.get(`${Math.floor(y / clear) + a},${Math.floor(z / clear) + b}`) ?? []) {
          const sep = closed ? Math.min(Math.abs(i - j), n - Math.abs(i - j)) : Math.abs(i - j);
          if (sep > gap) close = Math.min(close, dist(pts[i], pts[j]));
        }
      }
    }
  }
  return [tight, close];
}

function bezier(p0    , p1    , p2    , p3    , step        )       {
  const n = Math.max(8, Math.floor(3 * (dist(p0, p1) + dist(p1, p2) + dist(p2, p3)) / step));
  const out       = [];
  for (let j = 1; j < n; j++) {
    const s = j / n;
    const f = (i        ) => (1 - s) ** 3 * p0[i] + 3 * (1 - s) ** 2 * s * p1[i] + 3 * (1 - s) * s * s * p2[i]
      + s ** 3 * p3[i];
    out.push([f(0), f(1)]);
  }
  return out;
}

function radius3(a    , b    , c    )         {
  const area2 = Math.abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
  return area2 > 1e-12 ? dist(a, b) * dist(b, c) * dist(a, c) / (2 * area2) : INF;
}

function tangent(pts      , i        , back          = false)     {
  const [a, b] = back ? [at(pts, i - 6), pts[i]] : [pts[i], at(pts, i + 6)];
  const d = dist(a, b) || 1;
  return [(b[0] - a[0]) / d, (b[1] - a[1]) / d];
}

// Ramer-Douglas-Peucker, as strokes.rdp (points as given, any 2D units).
function rdp(pts      , eps        )       {
  if (pts.length < 3) return pts;
  const [y0, x0] = pts[0], [y1, x1] = pts[pts.length - 1];
  const dy = y1 - y0, dx = x1 - x0;
  const norm = Math.hypot(dy, dx) || 1;
  let far = 0, idx = 0;
  for (let i = 1; i < pts.length - 1; i++) {
    const [y, x] = pts[i];
    const d = Math.abs(dy * (x - x0) - dx * (y - y0)) / norm;
    if (d > far) { far = d; idx = i; }
  }
  if (far <= eps) return [pts[0], pts[pts.length - 1]];
  return [...rdp(pts.slice(0, idx + 1), eps).slice(0, -1), ...rdp(pts.slice(idx), eps)];
}
return { STEP, INF, dist, at, resample, turnAngle, ease, check, bezier, radius3, tangent, rdp };
})();

// ---- svg.ts
const __svg_ts = (() => {
const { dist, resample, ease, STEP } = __geometry_ts;
// Reading SVG: every line of a drawing as points in its own units (y down), sampled by the browser's own SVG engine,
// so every path command, arc and transform works. Then fitted to the board.


                        
               
               
                  
 

const GEOMETRY = "path, polyline, polygon, line, rect, circle, ellipse";

function svgLines(svgText        )                                      {
  const doc = new DOMParser().parseFromString(svgText, "image/svg+xml");
  const root = doc.documentElement;
  if (root.nodeName.toLowerCase() !== "svg") throw new Error("not an SVG drawing");
  // attached (out of sight), so the browser can measure lengths and transforms
  const holder = document.createElement("div");
  holder.style.cssText = "position:absolute;left:-10000px;top:0;width:10px;height:10px;overflow:hidden";
  const svg = document.importNode(root, true)                            ;
  holder.appendChild(svg);
  document.body.appendChild(holder);
  try {
    const out                                      = [];
    const bbox = svg.getBBox();
    const size = Math.max(bbox.width, bbox.height) || 1;
    const rootCtm = svg.getCTM();
    for (const el of Array.from(svg.querySelectorAll(GEOMETRY))                        ) {
      if (el.closest("defs, clipPath, mask, symbol")) continue;
      const len = el.getTotalLength();
      if (!(len > 0)) continue;
      const toRoot = (rootCtm ? rootCtm.inverse() : new DOMMatrix()).multiply(el.getCTM() ?? new DOMMatrix());
      const h = size / 4000;                           // fine sampling; resampled on the board afterwards
      const n = Math.max(8, Math.ceil(len / h));
      const pts       = [];
      for (let i = 0; i <= n; i++) {
        const p = el.getPointAtLength(len * i / n);
        const q = new DOMPoint(p.x, p.y).matrixTransform(toRoot);
        pts.push([q.x, q.y]);
      }
      // a path with several subpaths jumps at each moveto: split there
      const parts         = [[pts[0]]];
      for (let i = 1; i < pts.length; i++) {
        if (dist(pts[i], pts[i - 1]) > 20 * (len / n) + 1e-9) parts.push([]);
        parts[parts.length - 1].push(pts[i]);
      }
      const tag = el.nodeName.toLowerCase();
      for (const part of parts) {
        if (part.length < 2) continue;
        const closedShape = ["polygon", "rect", "circle", "ellipse"].includes(tag)
          || dist(part[0], part[part.length - 1]) < size * 1e-3;
        out.push({ points: part, closed: closedShape });
      }
    }
    return out;
  } finally {
    holder.remove();
  }
}

// Lines in any units (y down) scaled to fit the board (deg, y up), centred; lines shorter than minLen deg after
// scaling are dropped (specks and dots the bot could not follow).
function fit(lines                                     , box    , margin = 1.5, minLen = 1.0)          {
  const xs = lines.flatMap((l) => l.points.map((p) => p[0]));
  const ys = lines.flatMap((l) => l.points.map((p) => p[1]));
  const w = (Math.max(...xs) - Math.min(...xs)) || 1, h = (Math.max(...ys) - Math.min(...ys)) || 1;
  const k = Math.min((2 * box[0] - 2 * margin) / w, (2 * box[1] - 2 * margin) / h);
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2, cy = (Math.max(...ys) + Math.min(...ys)) / 2;
  const shapes          = [];
  lines.forEach((line, i) => {
    let q       = line.points.map(([x, y]) => [(x - cx) * k, (cy - y) * k]);
    if (line.closed && dist(q[0], q[q.length - 1]) < 1e-6) q = q.slice(0, -1);
    let length = 0;
    for (let j = 0; j + 1 < q.length; j++) length += dist(q[j], q[j + 1]);
    if (line.closed) length += dist(q[q.length - 1], q[0]);
    if (length >= minLen && q.length >= 2) shapes.push({ name: `line ${i + 1}`, points: q, closed: line.closed });
  });
  return shapes;
}

// A shape as the builder wants it: points STEP apart, no turn tighter than turnR.
function prepare(shape       , turnR        )        {
  const pts = resample(shape.points, STEP, shape.closed);
  return { name: shape.name, points: ease(pts, turnR, shape.closed), closed: shape.closed };
}
return { svgLines, fit, prepare };
})();

// ---- tour.ts
const __tour_ts = (() => {
const { dist, at, bezier, resample, tangent, INF, STEP } = __geometry_ts;
// The tour: the order of the shapes, where the bot joins and leaves each, and the routes between them.
// A port of trace_track.py's plan_tour and lay_path.

                                      

                                 
                                                                    

const coarseAll = (p      ) => Array.from({ length: Math.ceil(p.length / 20) }, (_, i) => i * 20);

function* permutations(items          )                      {
  if (items.length <= 1) { yield items.slice(); return; }
  for (let i = 0; i < items.length; i++) {
    const rest = [...items.slice(0, i), ...items.slice(i + 1)];
    for (const p of permutations(rest)) yield [items[i], ...p];
  }
}

function nearestOrder(gap                                  , n        )           {
  const order = [0];
  const left = new Set(Array.from({ length: n - 1 }, (_, i) => i + 1));
  while (left.size) {
    let best = -1;
    for (const j of left) if (best < 0 || gap(order[order.length - 1], j) < gap(order[order.length - 1], best)) best = j;
    order.push(best);
    left.delete(best);
  }
  return order;
}

function twoOpt(order          , gap                                  )           {
  const n = order.length;
  const length = (o          ) => o.reduce((s, k, i) => s + gap(k, o[(i + 1) % n]), 0);
  let improved = true;
  while (improved) {
    improved = false;
    for (let i = 1; i < n - 1; i++) {
      for (let j = i + 1; j < n; j++) {
        const cand = [...order.slice(0, i), ...order.slice(i, j + 1).reverse(), ...order.slice(j + 1)];
        if (length(cand) < length(order) - 1e-9) { order = cand; improved = true; }
      }
    }
  }
  return order;
}

// Order, entries and exits for a tour of all shapes; null when no tour keeps its hops `clear` of the lines.
function planTour(shapes         , clear        , maxHop        , log     )              {
  const n = shapes.length;
  const pts = shapes.map((s) => s.points);
  if (n === 1) return { order: [0], ports: [shapes[0].closed ? [0, 0] : [0, pts[0].length - 1]] };
  const CELL = 0.1, END = 0.5;
  const near = new Set        ();                    // grid cells within `clear` of any line
  const round = (v        ) => Math.round(v);
  for (const line of pts) {
    for (const [py, pz] of line) {
      for (let i = round((py - clear) / CELL) - 1; i <= round((py + clear) / CELL) + 1; i++) {
        for (let j = round((pz - clear) / CELL) - 1; j <= round((pz + clear) / CELL) + 1; j++) {
          if (Math.hypot(i * CELL - py, j * CELL - pz) <= clear) near.add(`${i},${j}`);
        }
      }
    }
  }
  const clearHop = (a    , b    ) => {
    const d = dist(a, b);
    const steps = Math.floor(d / CELL) + 1;
    for (let s = 1; s < steps; s++) {
      const f = s / steps;
      if (Math.min(f, 1 - f) * d < END) continue;
      if (near.has(`${round((a[0] + f * (b[0] - a[0])) / CELL)},${round((a[1] + f * (b[1] - a[1])) / CELL)}`)) return false;
    }
    return true;
  };
  const memo = new Map                ();
  const hop = (k        , i        , j        , m        ) => {
    const key = `${k},${i},${j},${m}`;
    let v = memo.get(key);
    if (v === undefined) {
      const a = pts[k][i], b = pts[j][m];
      const d = dist(a, b);
      v = d < maxHop && clearHop(a, b) ? d : INF;
      memo.set(key, v);
      memo.set(`${j},${m},${k},${i}`, v);
    }
    return v;
  };
  const arc = (k        , e        , x        ) => {
    const L = pts[k].length;
    if (!shapes[k].closed) return (e !== x && Math.min(e, x) === 0 && Math.max(e, x) === L - 1) ? 0 : INF;
    const f = (((x - e) % L) + L) % L;
    return Math.min(f, L - f) * STEP;
  };
  const coarse = shapes.map((s, k) => s.closed ? coarseAll(pts[k]) : [0, pts[k].length - 1]);

  const ringPorts = (order          )                                      => {
    const small = order.reduce((best, k) => coarse[k].length < coarse[best].length ? k : best, order[0]);
    const r = order.indexOf(small);
    const ring = [...order.slice(r), ...order.slice(0, r)];
    const steps = [...Array.from({ length: n - 1 }, (_, i) => i + 1), 0];
    let found                                                 = [INF, null];
    for (const x0 of coarse[ring[0]]) {
      let cost = new Map                ([[x0, 0]]);
      const back                                                                   = [];
      for (const s of steps) {
        const k = ring[s], kp = at(ring, s - 1);
        const ent = new Map                          ();
        for (const e of coarse[k]) {
          let c = INF, from = -1;
          for (const [xp, cp] of cost) { const v = cp + hop(kp, xp, k, e); if (v < c) { c = v; from = xp; } }
          if (c < INF) ent.set(e, [c, from]);
        }
        const ext = new Map                          ();
        for (const x of (s === 0 ? [x0] : coarse[k])) {
          let c = INF, from = -1;
          for (const [e, [ce]] of ent) { const v = ce + arc(k, e, x); if (v < c) { c = v; from = e; } }
          if (c < INF) ext.set(x, [c, from]);
        }
        back.push([ent, ext]);
        cost = new Map(Array.from(ext, ([x, [c]]) => [x, c]                    ));
      }
      const total = cost.get(x0) ?? INF;
      if (total < found[0]) {
        const ports = new Map                          ();
        let x = x0;
        for (let q = steps.length - 1; q >= 0; q--) {
          const [ent, ext] = back[q];
          const e = ext.get(x) [1];
          ports.set(ring[steps[q]], [e, x]);
          x = ent.get(e) [1];
        }
        found = [total, ports];
      }
    }
    return found[1] ? [found[0], order.map((k) => found[1] .get(k) )] : [INF, null];
  };

  const refine = (order          , pe                    ) => {
    for (let round_ = 0; round_ < 6; round_++) {
      const before = JSON.stringify(pe);
      order.forEach((k, s) => {
        if (!shapes[k].closed) return;
        const kp = at(order, s - 1), kn = order[(s + 1) % n], xp = at(pe, s - 1)[1], en = pe[(s + 1) % n][0];
        const m = pts[k].length;
        let best                           = [INF, 0, 0];
        for (let de = -20; de <= 20; de++) {
          const e = (((pe[s][0] + de) % m) + m) % m;
          const h1 = hop(kp, xp, k, e);
          if (h1 === INF) continue;
          for (let dx = -20; dx <= 20; dx++) {
            const x = (((pe[s][1] + dx) % m) + m) % m;
            const c = h1 + arc(k, e, x) + hop(k, x, kn, en);
            if (c < best[0]) best = [c, e, x];
          }
        }
        if (best[0] < INF) pe[s] = [best[1], best[2]];
      });
      if (JSON.stringify(pe) === before) break;
    }
    return pe;
  };

  const gapMemo = new Map                ();
  const gap = (a        , b        ) => {
    const key = a < b ? `${a},${b}` : `${b},${a}`;
    let v = gapMemo.get(key);
    if (v === undefined) {
      v = INF;
      for (const i of coarseAll(pts[a])) for (const j of coarseAll(pts[b])) v = Math.min(v, dist(pts[a][i], pts[b][j]));
      gapMemo.set(key, v);
    }
    return v;
  };
  let orders            ;
  if (n === 2) orders = [[0, 1]];
  else if (n <= 7) {
    orders = [];
    for (const rest of permutations(Array.from({ length: n - 1 }, (_, i) => i + 1))) {
      if (rest[0] < rest[rest.length - 1]) orders.push([0, ...rest]);
    }
    const lb = (o          ) => o.reduce((s, k, i) => s + gap(k, o[(i + 1) % n]), 0);
    orders.sort((a, b) => lb(a) - lb(b));
  } else orders = [twoOpt(nearestOrder(gap, n), gap)];
  let best                                                       = [INF, null, null];
  let feasible = 0;
  for (const order of orders) {                        // the most promising orders first, until ten work
    const [c, pe] = ringPorts(order);
    if (c < INF && pe) {
      feasible++;
      if (c < best[0]) best = [c, order, pe];
      if (feasible === 10) break;
    }
  }
  if (!best[1] || !best[2]) return null;
  const order = best[1], pe = refine(order, best[2]);
  const repeat = order.reduce((s, k, i) => s + arc(k, pe[i][0], pe[i][1]), 0);
  const hops = order.reduce((s, k, i) => s + hop(k, pe[i][1], order[(i + 1) % n], pe[(i + 1) % n][0]), 0);
  log(`tour ${order.map((k) => shapes[k].name).join(" > ")}: hops ${hops.toFixed(1)} deg, repeated line ${repeat.toFixed(1)} deg`);
  return { order, ports: pe };
}

                                                                                          

// The bot's whole path (deg, STEP apart, starting nearest the board's centre) and the routes between shapes.
function layPath(shapesIn         , tour      , log     )       {
  const shapes = shapesIn.map((s) => ({ ...s, points: s.points.slice() }));
  const { order } = tour;
  const pe = tour.ports.map((p) => [p[0], p[1]]                    );
  const n = shapes.length;
  order.forEach((k, s) => {                            // lap each closed shape the way that repeats the shorter stretch
    if (!shapes[k].closed) return;
    const [e, x] = pe[s];
    const m = shapes[k].points.length;
    if (2 * ((((x - e) % m) + m) % m) > m) {
      shapes[k].points.reverse();
      pe[s] = [m - 1 - e, m - 1 - x];
    }
  });
  const pts = shapes.map((s) => s.points);
  const trav = (k        , e        , x        )       => {
    const line = pts[k];
    if (shapes[k].closed) {
      const L = line.length;
      const lap = [...line.slice(e), ...line.slice(0, e), line[e]];
      const on = [...line.slice(e + 1), ...line.slice(0, e + 1)].slice(0, (((x - e) % L) + L) % L);
      return [...lap, ...on];
    }
    return e === 0 ? line : line.slice().reverse();
  };
  let path       = [];
  const routes         = [];
  if (n === 1 && shapes[0].closed) path = pts[0].slice();
  else {
    order.forEach((k, s) => {
      const kn = order[(s + 1) % n];
      const [e, x] = pe[s];
      const [en, xn] = pe[(s + 1) % n];
      const here = trav(k, e, x), next = trav(kn, en, xn);
      path.push(...here);
      const a = here[here.length - 1], b = next[0];
      const ta = shapes[k].closed ? tangent(pts[k], x, true) : tangent(here, here.length - 1, true);
      const tb = shapes[kn].closed ? tangent(pts[kn], en) : tangent(next, 0);
      let route       = [];
      for (const tension of [1.0, 0.6, 0.35, 0.15, 0.0]) {   // straighter until the curve keeps off every line
        const reach = (Math.min(1.5, 0.4 * dist(a, b)) + 0.4) * tension;
        route = bezier(a, [a[0] + reach * ta[0], a[1] + reach * ta[1]], [b[0] - reach * tb[0], b[1] - reach * tb[1]], b, STEP);
        const inner = route.filter((p) => Math.min(dist(p, a), dist(p, b)) > 0.6);
        let c = 99;
        for (let i = 0; i < inner.length; i += 2) for (const line of pts) for (let j = 0; j < line.length; j += 2) c = Math.min(c, dist(inner[i], line[j]));
        if (c >= 0.15) break;
      }
      path.push(...route);
      routes.push([a, ...route, b]);
      log(`route ${shapes[k].name} to ${shapes[kn].name}: ${route.length * STEP > 0 ? (routeLength([a, ...route, b])).toFixed(1) : "0"} deg`);
    });
  }
  path = resample(path, STEP);
  let mid = 0;
  path.forEach((p, i) => { if (Math.hypot(p[0], p[1]) < Math.hypot(path[mid][0], path[mid][1])) mid = i; });
  path = [...path.slice(mid), ...path.slice(0, mid)];   // the tour starts nearest the board's centre
  let first = 0, bestD = INF;
  order.forEach((k, i) => { for (const q of pts[k]) { const d = dist(path[0], q); if (d < bestD) { bestD = d; first = i; } } });
  const tourNames = [...order.slice(first), ...order.slice(0, first)].map((k) => shapes[k].name);
  return { path, routes, tourNames, shapes };
}

function routeLength(pts      )         {
  let s = 0;
  for (let i = 0; i + 1 < pts.length; i++) s += dist(pts[i], pts[i + 1]);
  return s;
}
return { planTour, layPath, routeLength };
})();

// ---- template.ts
const __template_ts = (() => {

// Generated by web/make_template.py from trace_track.base_scenario (do not edit by hand).
const TEMPLATE = {
 "head": "Name=Trace Template\nPlayerCharacters=Player\nBotCharacters=tracer.bot\nIsChallenge=true\nOvershotProtectionTimer=0.25\nTimelimit=61.0\nPlayerProfile=Player\nAddedBots=tracer.bot\nPlayerMaxLives=0\nBotMaxLives=0\nPlayerTeam=1\nBotTeams=2\nScoreToWin=0.0\nScorePerDamage=1.0\nScorePerHit=0.0\nScorePerKill=0.0\nScorePerMidairDirect=0.0\nScorePerAnyDirect=0.0\nScoreLossPerDamageTaken=0.0\nScoreLossPerDeath=0.0\nScoreLossPerMidairDirected=0.0\nScoreLossPerAnyDirected=0.0\nScoreMultAccuracy=false\nScoreMultDamageEfficiency=false\nScoreMultKillEfficiency=false\nScorePerTime=0.0\nScorePerDistance=0.0\nMBSEnable=false\nMBSTime1=0.25\nMBSTime2=0.5\nMBSTime3=0.75\nMBSTime1Mult=1.0\nMBSTime2Mult=2.0\nMBSTime3Mult=3.0\nMBSFBInstead=false\nMBSRequireEnemyAlive=false\nMaxDistanceTraveledScore=0.0\nMaxMBSScore=0.0\nDistanceScoreCondition=None\nDistScoreCondAcceptTime=0.2\nScoreLossPerMiss=0.0\nScoreLossPerReload=0.0\nMultSqrtAcc=true\nEnableOverDamage=true\nMapName=Trace_Template.json\nMapScale=3.15\nBlockProjectilePredictors=true\nBlockCheats=true\nInvinciblePlayer=true\nInvincibleBots=false\nTimescale=1.0\nBlockHealthbars=true\nTimeRefilledByKill=0.0\nBlockHitMarkers=false\nBlockHitSounds=false\nBlockMissSounds=false\nBlockFCT=true\nLockFOVRange=true\nLockedFOVMin=103.0\nLockedFOVMax=130.0\nLockedFOVScale=Clamped Horizontal\nEndChallengeAfterKills=0.0\nEndChallengeAfterDamage=0.0\nForceParticleEffectsOn=false\nIsTimeDilationActive=false\nIsTargetSizeActive=false\nIsHeightLocked=false\nPerformanceMetricType=KillsPerSecond\nTimeDilationType=TargetDilation\nMaxTargetSizeMultiplier=4.0\nMinTargetSizeMultiplier=0.1\nMaxTargetSpeedMultiplier=5.0\nMinTargetSpeedMultiplier=0.1\nPerformanceTarget=0.5\nPerformanceThreshold=0.01\nTimeDilationBaseMultiplier=1.0\nTargetSizeBaseMultiplier=1.0\nAdjustmentRate=0.05\nAdjustmentInterval=1.5\nAimTypeTag=Tracking\nAimSubTypeTag=Smoothness\nAimTypeFlicking=false\nAimTypeProjectile=false\nAimTypePlayerMovement=false\nDifficultyTag=5\nSearchTags=Tracking, Smooth\nDescription=\nGameVersion=3.9.9\nScenarioVersion=Initial\n\n[Aim Profile]\nName=Default\nMinReactionTime=0.3\nMaxReactionTime=0.4\nMinSelfMovementCorrectionTime=0.001\nMaxSelfMovementCorrectionTime=0.05\nFlickFov=30.0\nFlickSpeed=1.5\nFlickError=15.0\nTrackSpeed=3.5\nTrackError=3.5\nMaxTurnAngleFromPadCenter=75.0\nMinReCenterTime=0.3\nMaxReCenterTime=0.5\nOptimalAimFov=30.0\nOuterAimPenalty=1.0\nMaxError=40.0\nShootFov=15.0\nVerticalAimOffset=0.0\nMaxTolerableSpread=5.0\nMinTolerableSpread=1.0\nTolerableSpreadDist=2000.0\nMaxSpreadDistFactor=2.0\nAimingStyle=Original\nScanSpeedMultiplier=1.0\nMaxSeekPitch=30.0\nMaxSeekYaw=30.0\nAimingSpeed=5.0\nMinShootDelay=0.3\nMaxShootDelay=0.6\n\n[Bot Profile]\nName=tracer\nDodgeProfileNames=follow\nDodgeProfileWeights=1.0\nDodgeProfileMaxChangeTime=60.0\nDodgeProfileMinChangeTime=60.0\nWeaponsProfileNames=;;;;;;;\nWeaponProfileWeights=1.0;1.0;1.0;1.0;1.0;1.0;1.0;1.0\nAimingProfileNames=Default;Default;Default;Default;Default;Default;Default;Default\nWeaponSwitchTime=3.0\nUseWeapons=false\nCharacterProfile=tracer\nSeeThroughWalls=false\nNoDodging=false\nStandStillUntilHurt=false\nNoAiming=false\nSpawnGroup=0\nAbilityUseTimer=0.1\nUseAbilityFrequency=1.0\nUseAbilityFreqMinTime=0.3\nUseAbilityFreqMaxTime=0.6\nShowLaser=false\nLaserRgb=X=1.000 Y=0.300 Z=0.000\nLaserAlpha=1.0\nRandomizeDodgeProfiles=false\nRepeatDodgeProfileEntries=true\nUseMinimumRespawnTime=true\nDisableScoring=false\nRestartDodgeProfileTimerOnRespawn=false\nUntargetable=false\n\n[Character Profile]\nName=Player\nMaxHealth=100.0\nWeaponProfileNames=LG;;;;;;;\nMinRespawnDelay=1.0\nMaxRespawnDelay=5.0\nStepUpHeight=0.0\nCrouchHeightModifier=0.5\nCrouchAnimationSpeed=1.0\nCameraOffset=X=0.000 Y=0.000 Z=-1.000\nHeadshotOnly=false\nDamageKnockbackFactor=0.0\nMaxSpeed=0.0\nMaxCrouchSpeed=0.0\nAcceleration=0.0\nCrouchingAcceleration=0.0\nFriction=0.0\nBrakingFrictionFactor=0.0\nJumpVelocityMin=0.0\nJumpVelocityMax=0.0\nGravity=0.0\nAirControl=0.0\nCanCrouch=true\nCanPogoJump=false\nCanCrouchInAir=false\nCrouchInAirRaisesFeet=false\nCanJumpFromCrouch=false\n// Note: the color channel values are interpreted as 0.0 (0%) to 1.0 (100%) going over 1.0 will start to produce a glow effect when the user is in HDR mode (SceneColor is set to \"Medium\" or higher)\nEnemyBodyColor=X=255.000 Y=0.000 Z=0.000\nEnemyBodyColorOnHit=X=1.000 Y=1.000 Z=1.000\nEnemyBodyColorOnLookAt=X=1.000 Y=1.000 Z=1.000\nEnemyHeadColor=X=255.000 Y=255.000 Z=255.000\nEnemyHeadColorOnHit=X=1.000 Y=1.000 Z=1.000\nEnemyHeadColorOnLookAt=X=1.000 Y=1.000 Z=1.000\nTeamBodyColor=X=0.000 Y=0.000 Z=255.000\nTeamHeadColor=X=255.000 Y=255.000 Z=255.000\nMainBBType=Cylindrical\nMainBBHeight=2.0\nMainBBRadius=1.0\nMainBBHasHead=false\nMainBBHeadRadius=0.1\nMainBBHeadOffset=0.0\nMainBBHide=false\nProjBBType=Cylindrical\nProjBBHeight=2.0\nProjBBRadius=1.0\nProjBBHasHead=false\nProjBBHeadRadius=0.1\nProjBBHeadOffset=0.0\nProjBBHide=true\nBlockSelfDamage=false\nInvinciblePlayer=false\nInvincibleBots=false\nBlockTeamDamage=false\nHasJetpack=false\nJetpackActivationDelay=0.2\nJetpackFullFuelTime=4.0\nJetpackFuelIncPerSec=1.0\nJetpackFuelRegensInAir=false\nJetpackThrust=6000.0\nJetpackMaxZVelocity=400.0\nJetpackAirControlWithThrust=0.25\nAirJumpCount=0\nAirJumpVelocity=800.0\nAbilityProfileNames=;;;\nHideWeapon=false\nAerialFriction=0.0\nAerialVerticalTurningFriction=100000.0\nAerialVerticalBreakingFriction=0.0\nUseAerialVerticalFriction=false\nStrafeSpeedMult=1.0\nBackSpeedMult=1.0\nRespawnInvulnTime=0.0\nBlockedSpawnRadius=0.0\nBlockSpawnFOV=0.0\nBlockSpawnDistance=0.0\nRespawnAnimationDuration=0.5\nAllowBufferedJumps=false\nBounceOffWalls=false\nLeanAngle=0.0\nLeanDisplacement=0.0\nAirJumpExtraControl=0.0\nForwardSpeedBias=1.0\nHealthRegainedonkill=0.0\nHealthRegenPerSec=0.0\nHealthRegenDelay=0.0\nJumpSpeedPenaltyDuration=0.0\nJumpSpeedPenaltyPercent=0.0\nThirdPersonCamera=false\nTPSArmLength=300.0\nTPSOffset=X=0.000 Y=150.000 Z=150.000\nBrakingDeceleration=2048.0\nTerminalVelocity=0.0\nCharacterModel=None\nCharacterSkin=Default\nMeshHitDetection=false\nSpawnOffsetMin=X=-0.000 Y=0.000 Z=0.000\nSpawnOffsetMax=X=-0.000 Y=0.000 Z=0.000\nInvertBlockedSpawn=false\nViewBobTime=0.0\nViewBobAngleAdjustment=0.0\nViewBobCameraZOffset=0.0\nViewBobAffectsShots=false\nIsFlyer=false\nFlightObeysPitch=false\nFlightVelocityUp=800.0\nFlightAccelUp=800.0\nFlightVelocityDown=800.0\nFlightAccelDown=800.0\nIsFlyUpOnJumpAndCrouch=false\nDisableCharacterCollision=false\nLifeStealPercent=0.0\nAbilityGlobalCooldown=0.0\nBlockAbilityOnStartDuration=1.0\nDragCoefficient=10.0\nAmmoRegainedOnKill=0\nContinuousGroundFriction=0.0\nContinuousAirFriction=0.0\nScaledGroundAcceleration=0.0\nScaledAirAcceleration=0.0\nMaxAirSpeed=0.0\nStopSpeed=0.0\nStopSpeedThreshold=0.0\nClampVelocityToInputSpeed=true\nJumpSkipsFriction=false\nEnableQuakeMovement=false\nEnableQuakeJump=false\nKtJump=0.0\nMovementPhysicsTickInterval=0.0\nMovementPhysicsTickEnabled=false\nTeamGlowUpHead=0.0\nTeamGlowUpBody=0.0\nEnemyGlowUpHead=0.0\nEnemyGlowUpBody=0.0\nEnemyGlowUpHeadOnHit=0.0\nEnemyGlowUpBodyOnHit=0.0\nEnemyGlowUpHeadOnLookAt=0.0\nEnemyGlowUpBodyOnLookAt=0.0\nPlaybackOptions.PlaybackMode=Input\nPlaybackOptions.OverrideRotation=true\nPlaybackOptions.OverrideAbilities=true\nPlaybackOptions.OverrideWeapons=true\nPlaybackOptions.OverrideMovement=true\nPlaybackOptions.OverrideDodgeTime=false\nPlaybackOptions.LoopUponCompletion=true\nPlaybackOptions.BreakToInputMode=false\n\n[Character Profile]\nName=tracer\nMaxHealth=1000000.0\nWeaponProfileNames=;;;;;;;\nMinRespawnDelay=0.001\nMaxRespawnDelay=0.001\nStepUpHeight=0.0\nCrouchHeightModifier=0.5\nCrouchAnimationSpeed=1.0\nCameraOffset=X=0.000 Y=0.000 Z=0.000\nHeadshotOnly=false\nDamageKnockbackFactor=0.0\nMaxSpeed=810.9\nMaxCrouchSpeed=0.0\nAcceleration=9731.1\nCrouchingAcceleration=0.0\nFriction=0.0\nBrakingFrictionFactor=0.0\nJumpVelocityMin=0.0\nJumpVelocityMax=0.0\nGravity=0.0\nAirControl=1.0\nCanCrouch=false\nCanPogoJump=false\nCanCrouchInAir=false\nCrouchInAirRaisesFeet=false\nCanJumpFromCrouch=false\n// Note: the color channel values are interpreted as 0.0 (0%) to 1.0 (100%) going over 1.0 will start to produce a glow effect when the user is in HDR mode (SceneColor is set to \"Medium\" or higher)\nEnemyBodyColor=X=0.000 Y=0.000 Z=0.000\nEnemyBodyColorOnHit=X=1.000 Y=1.000 Z=1.000\nEnemyBodyColorOnLookAt=X=1.000 Y=1.000 Z=1.000\nEnemyHeadColor=X=255.000 Y=255.000 Z=255.000\nEnemyHeadColorOnHit=X=1.000 Y=1.000 Z=1.000\nEnemyHeadColorOnLookAt=X=1.000 Y=1.000 Z=1.000\nTeamBodyColor=X=0.000 Y=0.000 Z=255.000\nTeamHeadColor=X=255.000 Y=255.000 Z=255.000\nMainBBType=Spheroid\nMainBBHeight=129.7\nMainBBRadius=64.9\nMainBBHasHead=false\nMainBBHeadRadius=0.1\nMainBBHeadOffset=0.0\nMainBBHide=false\nProjBBType=Spheroid\nProjBBHeight=127.8\nProjBBRadius=59.9\nProjBBHasHead=false\nProjBBHeadRadius=0.1\nProjBBHeadOffset=0.0\nProjBBHide=true\nBlockSelfDamage=false\nInvinciblePlayer=false\nInvincibleBots=false\nBlockTeamDamage=true\nHasJetpack=false\nJetpackActivationDelay=0.2\nJetpackFullFuelTime=100000.0\nJetpackFuelIncPerSec=0.1\nJetpackFuelRegensInAir=true\nJetpackThrust=6000.0\nJetpackMaxZVelocity=400.0\nJetpackAirControlWithThrust=1.0\nAirJumpCount=0\nAirJumpVelocity=800.0\nAbilityProfileNames=;;;\nHideWeapon=true\nAerialFriction=0.0\nAerialVerticalTurningFriction=100000.0\nAerialVerticalBreakingFriction=0.0\nUseAerialVerticalFriction=false\nStrafeSpeedMult=1.0\nBackSpeedMult=1.0\nRespawnInvulnTime=0.0\nBlockedSpawnRadius=0.0\nBlockSpawnFOV=0.0\nBlockSpawnDistance=0.0\nRespawnAnimationDuration=0.0\nAllowBufferedJumps=false\nBounceOffWalls=false\nLeanAngle=0.0\nLeanDisplacement=0.0\nAirJumpExtraControl=0.0\nForwardSpeedBias=1.0\nHealthRegainedonkill=0.0\nHealthRegenPerSec=0.0\nHealthRegenDelay=0.0\nJumpSpeedPenaltyDuration=0.0\nJumpSpeedPenaltyPercent=0.0\nThirdPersonCamera=false\nTPSArmLength=300.0\nTPSOffset=X=0.000 Y=150.000 Z=150.000\nBrakingDeceleration=0.0\nTerminalVelocity=0.0\nCharacterModel=None\nCharacterSkin=Default\nMeshHitDetection=false\nSpawnOffsetMin=X=0.000 Y=0.000 Z=0.000\nSpawnOffsetMax=X=0.000 Y=0.000 Z=0.000\nInvertBlockedSpawn=false\nViewBobTime=0.0\nViewBobAngleAdjustment=0.0\nViewBobCameraZOffset=0.0\nViewBobAffectsShots=false\nIsFlyer=true\nFlightObeysPitch=true\nFlightVelocityUp=810.9\nFlightAccelUp=9731.1\nFlightVelocityDown=810.9\nFlightAccelDown=9731.1\nIsFlyUpOnJumpAndCrouch=false\nDisableCharacterCollision=false\nLifeStealPercent=0.0\nAbilityGlobalCooldown=0.0\nBlockAbilityOnStartDuration=1.0\nDragCoefficient=10.0\nAmmoRegainedOnKill=0\nContinuousGroundFriction=0.0\nContinuousAirFriction=0.0\nScaledGroundAcceleration=0.0\nScaledAirAcceleration=0.0\nMaxAirSpeed=0.0\nStopSpeed=0.0\nStopSpeedThreshold=0.0\nClampVelocityToInputSpeed=true\nJumpSkipsFriction=false\nEnableQuakeMovement=false\nEnableQuakeJump=false\nKtJump=0.0\nMovementPhysicsTickInterval=0.0\nMovementPhysicsTickEnabled=false\nTeamGlowUpHead=0.0\nTeamGlowUpBody=0.0\nEnemyGlowUpHead=0.0\nEnemyGlowUpBody=0.0\nEnemyGlowUpHeadOnHit=0.0\nEnemyGlowUpBodyOnHit=0.0\nEnemyGlowUpHeadOnLookAt=0.0\nEnemyGlowUpBodyOnLookAt=0.0\nPlaybackOptions.PlaybackMode=Input\nPlaybackOptions.OverrideRotation=true\nPlaybackOptions.OverrideAbilities=true\nPlaybackOptions.OverrideWeapons=true\nPlaybackOptions.OverrideMovement=true\nPlaybackOptions.OverrideDodgeTime=false\nPlaybackOptions.LoopUponCompletion=true\nPlaybackOptions.BreakToInputMode=false\n\n[Dodge Profile]\nName=follow\nMaxTargetDistance=10000.0\nMinTargetDistance=0.0\nToggleLeftRight=false\nToggleForwardBack=false\nMinLRTimeChange=0.4\nMaxLRTimeChange=0.7\nMinFBTimeChange=0.4\nMaxFBTimeChange=0.7\nDamageReactionChangesDirection=false\nDamageReactionChanceToIgnore=0.5\nDamageReactionMinimumDelay=0.125\nDamageReactionMaximumDelay=0.25\nDamageReactionCooldown=1.0\nDamageReactionThreshold=0.0\nDamageReactionResetTimer=0.1\nJumpFrequency=0.0\nCrouchInAirFrequency=0.0\nCrouchOnGroundFrequency=0.0\nTargetStrafeOverride=Ignore\nTargetStrafeMinDelay=0.125\nTargetStrafeMaxDelay=0.25\nMinProfileChangeTime=0.0\nMaxProfileChangeTime=0.0\nMinCrouchTime=0.5\nMaxCrouchTime=0.5\nMinJumpTime=0.5\nMaxJumpTime=0.5\nAlterateJumpCrouchInput=false\nToggleUpDownMinTime=0.2\nToggleUpDownMaxTime=0.5\nUpDownSwapPauseMinTime=0.0\nUpDownSwapPauseMaxTime=0.0\nLeftStrafeTimeMult=1.0\nRightStrafeTimeMult=1.0\nStrafeSwapMinPause=0.0\nStrafeSwapMaxPause=0.0\nBlockedMovementPercent=0.5\nBlockedMovementReactionMin=0.1\nBlockedMovementReactionMax=0.1\nWaypointLogic=FollowAimAtWaypoint\nWaypointTurnRate=100000.0\nMinTimeBeforeShot=0.15\nMaxTimeBeforeShot=0.25\nIgnoreShotChance=0.0\nForwardTimeMult=1.0\nBackTimeMult=1.0\nDamageReactionChangesFB=false\nCooldownTime=0.0\nDamageReactionTriggersProfileChange=false\nLOSReactType=None\nLOSReactInitMin=0.175\nLOSReactInitMax=0.25\nLOSReactChanceIgnore=0.0\nLOSReactCooldownTime=1.0\nLOSReactDurationMin=1.0\nLOSReactDurationMax=1.0\nLOSReactKillBot=false\nLOSReactKillBotTimerMin=0.5\nLOSReactKillBotTimerMax=0.75\nInitialForwardMovementState=Forward\nInitialRightMovementState=Right\nCounterStrafeOnCollision=false\nInitialLeftRightStrafeResetBehavior=InitialSpawn\nInitialForwardBackStrafeResetBehavior=InitialSpawn\nPlaybackOptions.PlaybackMode=Input\nPlaybackOptions.OverrideRotation=true\nPlaybackOptions.OverrideAbilities=true\nPlaybackOptions.OverrideWeapons=true\nPlaybackOptions.OverrideMovement=true\nPlaybackOptions.OverrideDodgeTime=false\nPlaybackOptions.LoopUponCompletion=true\nPlaybackOptions.BreakToInputMode=false\n\n[Weapon Profile]\nName=LG\nType=Hitscan\nShotsPerClick=1\nDamagePerShot=1.0\nKnockbackFactor=2.0\nTimeBetweenShots=0.01\nPierces=false\nCategory=FullyAuto\nBurstShotCount=1\nTimeBetweenBursts=0.5\nChargeStartDamage=10.0\nChargeStartVelocity=X=500.000 Y=0.000 Z=0.000\nChargeTimeToAutoRelease=2.0\nChargeTimeToCap=1.0\nMuzzleVelocityMin=X=2000.000 Y=0.000 Z=0.000\nMuzzleVelocityMax=X=2000.000 Y=0.000 Z=0.000\nInheritOwnerVelocity=0.0\nOriginOffset=X=0.000 Y=0.000 Z=0.000\nMaxTravelTime=5.0\nMaxHitscanRange=100000.0\nGravityScale=1.0\nHeadshotCapable=false\nHeadshotMultiplier=2.0\nCooldownType=InfiniteUse\nMagazineMax=0\nReloadTimeFromEmpty=0.5\nReloadTimeFromPartial=0.5\nCooldownTimer=0.8\nMaxCharges=3\nDamageFalloffStartDistance=100000.0\nDamageFalloffStopDistance=100000.0\nDamageAtMaxRange=7.0\nDelayBeforeShot=0.0\nProjectileGraphic=Ball\nVisualLifetime=0.05\nExplosive=false\nRadius=500.0\nDamageAtCenter=100.0\nDamageAtEdge=0.0\nSelfDamageMultiplier=0.5\nExplodesOnContactWithEnemy=false\nDelayAfterEnemyContact=0.0\nExplodesOnContactWithWorld=false\nDelayAfterWorldContact=0.0\nExplodesOnNextAttack=false\nDelayAfterSpawn=0.0\nBlockedByWorld=false\nClearAttackersOnSelfDmg=false\nBounceOffWorld=false\nBounceFactor=0.0\nBounceCount=0\nHomingProjectileAcceleration=0.0\nSpreadSSA=1.0,1.0,-1.0,0.0\nSpreadSCA=1.0,1.0,-1.0,0.0\nSpreadMSA=1.0,1.0,-1.0,0.0\nSpreadMCA=1.0,1.0,-1.0,0.0\nSpreadSSH=1.0,1.0,-1.0,0.0\nSpreadSCH=1.0,1.0,-1.0,0.0\nSpreadMSH=1.0,1.0,-1.0,0.0\nSpreadMCH=1.0,1.0,-1.0,0.0\nMaxRecoilUp=0.0\nMinRecoilUp=0.0\nMinRecoilHoriz=0.0\nMaxRecoilHoriz=0.0\nFirstShotRecoilMult=1.0\nRecoilAutoReset=false\nTimeToRecoilPeak=0.05\nTimeToRecoilReset=0.35\nProjectileWorldHitRadius=1.0\nProjectileEnemyHitRadius=1.0\nCanAimDownSight=true\nADSZoomSensFactor=0.7\nADSMoveFactor=1.0\nADSStartDelay=0.0\nAAMode=0\nAAPreferClosestPlayer=false\nAAAlpha=0.05\nAAMaxSpeed=1.0\nAADeadZone=0.0\nAAFOV=30.0\nAANeedsLOS=true\nTrackHorizontal=true\nTrackVertical=true\nAABlocksMouse=false\nAAOffTimer=0.0\nAABackOnTimer=0.0\nTriggerBotEnabled=false\nTriggerBotDelay=0.0\nTriggerBotFOV=1.0\nStickyLock=false\nHeadLock=false\nVerticalOffset=0.0\nDisableLockOnKill=false\nShootSoundCooldown=0.08\nHitSoundCooldown=0.08\nShootSound=Shot\nHitscanVisualOffset=X=0.000 Y=0.000 Z=-80.000\nADSBlocksShooting=false\nShootingBlocksADS=false\nKnockbackFactorAir=4.0\nRecoilNegatable=false\nDecalType=0\nDecalSize=30.0\nDelayAfterShooting=0.0\nBeamTracksCrosshair=true\nAlsoShoot=\nADSShoot=\nChargeMoveSpeedModifier=1.0\nStunDuration=0.0\nAmmoPerShot=1\nUsePerShotRecoil=false\nPSRLoopStartIndex=0\nPSRViewRecoilTracking=0.45\nPSRCapUp=9.0\nPSRCapRight=4.0\nPSRCapLeft=4.0\nPSRTimeToPeak=0.095\nPSRResetDegreesPerSec=40.0\nCircularSpread=true\nSpreadStationaryVelocity=0.0\nPassiveCharging=false\nBurstFullyAuto=true\nFlatKnockbackHorizontal=0.0\nFlatKnockbackVertical=0.0\nHitscanRadius=0.0\nHitscanVisualRadius=6.0\nTaggingDuration=0.0\nTaggingMaxFactor=1.0\nTaggingHitFactor=1.0\nRecoilCrouchScale=1.0\nRecoilADSScale=1.0\nPSRCrouchScale=1.0\nPSRADSScale=1.0\nProjectileAcceleration=0.0\nAccelIncludeVertical=true\nAimPunchAmount=0.0\nAimPunchResetTime=0.05\nAimPunchCooldown=0.5\nAimPunchHeadshotOnly=false\nAimPunchCosmeticOnly=true\nMinimumDecelVelocity=0.0\nPSRManualNegation=false\nPSRAutoReset=true\nUsePerBulletSpread=false\nPBS0=0.0,0.0\nAimPunchUpTime=0.05\nAmmoReloadedOnKill=0\nCancelReloadOnKill=false\nFlatKnockbackHorizontalMin=0.0\nFlatKnockbackVerticalMin=0.0\nADSScope=No Scope\nADSFOVOverride=70.0\nADSAllowUserOverrideFOV=true\nHitscanGraphicOriginAtWeapon=false\nProjectileGraphicOriginAtWeapon=false\nIsChargeWeapon=false\nIsBurstWeapon=false\nForceFirstPersonInADS=true\nZoomBlockedInAir=false\nADSCameraOffsetX=0.0\nADSCameraOffsetY=0.0\nADSCameraOffsetZ=0.0\nQuickSwitchTime=0.0\nWeaponModel=KovaaKs Rifle\nWeaponAnimation=Primary\nUseIncReload=false\nIncReloadStartupTime=0.1\nIncReloadLoopTime=0.1\nIncReloadAmmoPerLoop=1\nIncReloadEndTime=0.1\nIncReloadCancelWithShoot=true\nWeaponSkin=Default\nProjectileVisualOffset=X=0.000 Y=0.000 Z=0.000\nSpreadDecayDelay=0.0\nReloadBeforeRecovery=false\n3rdPersonWeaponModel=Pistol\n3rdPersonWeaponSkin=Default\nParticleMuzzleFlash=None\nParticleWallImpact=None\nParticleBodyImpact=None\nParticleProjectileTrail=None\nParticleHitscanTrace=Tracer\nParticleMuzzleFlashScale=1.0\nParticleWallImpactScale=1.0\nParticleBodyImpactScale=1.0\nParticleProjectileTrailScale=1.0\nADSFOVScale=Quake/Source\nADSCustomFOVAspectX=16\nADSCustomFOVAspectY=9\nADSCustomFOVScale=hML\nADSResetsCharge=true\nADSZoomInDuration=0.0\nADSZoomOutDuration=0.0\nADSFOVScaleString=Quake/Source\nFullyAutomatic=false\nDelayBeforePassiveCharge=0.0\nBaseChargeRecoilFactor=0.0\n\n",
 "map": {
  "materialSets": [
   {
    "wall": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "e6dcc4ff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.2
      }
     ]
    },
    "ground": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "8a5a36ff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.35
      }
     ]
    },
    "ceiling": {
     "material": "MI_WA_ConcretePoured",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "f2f0eaff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.35
      }
     ]
    },
    "ramp": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "a8773fff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.3
      }
     ]
    }
   },
   {
    "wall": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "3d6f50ff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.4
      }
     ]
    },
    "ground": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "ecece4ff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.3
      }
     ]
    },
    "ceiling": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "5c3b22ff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.3
      }
     ]
    },
    "ramp": {
     "material": "MI_WA_PureColor",
     "pack": "Default",
     "properties": [
      {
       "name": "Tint",
       "value": "3a3a3aff"
      },
      {
       "name": "Scale",
       "value": 1.0
      },
      {
       "name": "Roughness",
       "value": 0.9
      },
      {
       "name": "Metallic",
       "value": 0.0
      },
      {
       "name": "FullBright",
       "value": 0.5
      }
     ]
    }
   },
   {
    "ceiling": {
     "material": "None",
     "pack": "None"
    },
    "ground": {
     "material": "None",
     "pack": "None"
    },
    "ramp": {
     "material": "None",
     "pack": "None"
    },
    "wall": {
     "material": "None",
     "pack": "None"
    }
   }
  ],
  "objects": [
   {
    "location": "-1023999.937500, 1023.999817, -1036.000000",
    "materialSets": [
     {
      "group": 0,
      "surface": "ceiling"
     },
     {
      "group": 0,
      "surface": "wall"
     },
     {
      "group": 0,
      "surface": "ground"
     },
     {
      "group": 0,
      "surface": "wall"
     },
     {
      "group": 0,
      "surface": "wall"
     },
     {
      "group": 0,
      "surface": "wall"
     }
    ],
    "mesh": "Cube",
    "name": "Default",
    "rotation": "0.000000, 0.000000, -89.999939",
    "scale": "20.480000, 0.640000, 20.480000",
    "type": "brush"
   },
   {
    "location": "-5999.999512, 0.000000, 0.000000",
    "name": "SpawnPoint",
    "properties": [
     {
      "name": "Name",
      "value": "SpawnVolume0"
     },
     {
      "name": "TeamMask",
      "value": 1
     },
     {
      "name": "Path",
      "value": ""
     },
     {
      "name": "LoopingPath",
      "value": false
     },
     {
      "name": "PermittedCharacterProfiles",
      "value": ""
     },
     {
      "name": "Weight",
      "value": 1.0
     }
    ],
    "rotation": "0.000000, 0.000000, 0.000000",
    "scale": "0.250000, 0.250000, 0.250000",
    "type": "gameObject"
   }
  ],
  "version": "1.0.0"
 },
 "spawn": {
  "location": "-2949.999756, 0.000000, -41.174603",
  "name": "SpawnVolume",
  "properties": [
   {
    "name": "Name",
    "value": ""
   },
   {
    "name": "TeamMask",
    "value": 2
   },
   {
    "name": "Path",
    "value": ""
   },
   {
    "name": "LoopingPath",
    "value": false
   },
   {
    "name": "PermittedCharacterProfiles",
    "value": "tracer"
   },
   {
    "name": "Weight",
    "value": 1.0
   }
  ],
  "rotation": "0.000000, 0.000000, 0.000000",
  "scale": "0.160000, 15.273262, 10.264384",
  "type": "gameObject"
 },
 "brush": {
  "location": "-1023999.937500, 1023.999817, -1036.000000",
  "materialSets": [
   {
    "group": 0,
    "surface": "ceiling"
   },
   {
    "group": 0,
    "surface": "wall"
   },
   {
    "group": 0,
    "surface": "ground"
   },
   {
    "group": 0,
    "surface": "wall"
   },
   {
    "group": 0,
    "surface": "wall"
   },
   {
    "group": 0,
    "surface": "wall"
   }
  ],
  "mesh": "Cube",
  "name": "Default",
  "rotation": "0.000000, 0.000000, -89.999939",
  "scale": "20.480000, 0.640000, 20.480000",
  "type": "brush"
 },
 "consts": {
  "SCALE": 3.15,
  "EYE_X": -6000.0,
  "X_BOT": -3049.999756,
  "FACE_X": -2900.0,
  "D_BOT": 2950.000244,
  "D_WALL": 3100.0,
  "PROC_UNIT": 3.15,
  "UV_UNIT": 100.0,
  "BRUSH_NAME": "DefaultNoCollision",
  "GROUP_BASE": 10,
  "MAP_SCALE": 3.15
 }
}         ;
return { TEMPLATE };
})();

// ---- carve.ts
const __carve_ts = (() => {
const { dist } = __geometry_ts;
const { TEMPLATE } = __template_ts;
// Map pieces: plain blocks (the hall) and one custom mesh of flat chalk ribbons (the lines, dashes and labels).
// A port of egypt.Scene.box/end_mesh and trace_track.ribbon.



                                    
                                   
                                                                      

const C = TEMPLATE.consts;
const f6 = (v        ) => v.toFixed(6);
const f4 = (v        ) => v.toFixed(4);

class MapPieces {
  objects        = [];
  group         = C.GROUP_BASE;
  mesh                              = null;

  section()       {                                    // a new editor group; a mesh in progress ends here
    this.endMesh();
    this.group += 1;
  }

  box(x0        , x1        , y0        , y1        , z0        , z1        , slot      )       {
    if (x1 - x0 <= 0 || y1 - y0 <= 0 || z1 - z0 <= 0) return;
    const b      = JSON.parse(JSON.stringify(TEMPLATE.brush));
    delete b.group;
    b.name = C.BRUSH_NAME;
    b.group = this.group;
    b.location = `${f6(x0)}, ${f6(y0)}, ${f6(z0)}`;
    b.scale = `${f6((x1 - x0) / 100)}, ${f6((y1 - y0) / 100)}, ${f6((z1 - z0) / 100)}`;
    b.rotation = "0.000000, 0.000000, 0.000000";
    b.materialSets = Array.from({ length: 6 }, () => ({ group: slot[0], surface: slot[1] }));
    this.objects.push(b);
  }

  beginMesh()       { this.mesh = new Map(); }

  endMesh()       {
    const mesh = this.mesh;
    this.mesh = null;
    if (!mesh || mesh.size === 0) return;
    const all = Array.from(mesh.values()).flatMap((s) => s.v);
    const origin = [0, 1, 2].map((i) => Math.min(...all.map((v) => v[0][i])));
    const b      = JSON.parse(JSON.stringify(TEMPLATE.brush));
    delete b.group;
    delete b.materialSets;
    Object.assign(b, { location: `${f6(origin[0])}, ${f6(origin[1])}, ${f6(origin[2])}`, mesh: "Cube",
      name: C.BRUSH_NAME, rotation: "0.000000, 0.000000, 0.000000", scale: "1.000000, 1.000000, 1.000000",
      type: "brush", group: this.group });
    b.materialSets = Array.from(mesh.keys()).map((k) => { const [g, s] = k.split("|"); return { group: +g, surface: s }; });
    b.procedural = Array.from(mesh.values()).map((sec) => ({
      indices: sec.i,
      vertices: sec.v.map(([p, n, tg, uv]) => ({
        location: [0, 1, 2].map((i) => f4((p[i] - origin[i]) / C.PROC_UNIT)).join(", "),
        normal: n.map(f4).join(", "),
        tangent: `${tg.map(f4).join(", ")}, false`,
        uv0: `${f4(uv[0])}, ${f4(uv[1])}`,
      })),
    }));
    this.objects.push(b);
  }

  // A flat line along pts ((y, z) wall points), width wide, facing the player: two vertices a point shared by the
  // triangles on both sides (mitred joins, the mitre capped at twice the half-width); open ends run on half a width.
  ribbon(slot      , ptsIn      , faceX        , width        , closed          = false)       {
    let pts = ptsIn.filter((p, i) => i === 0 || dist(p, ptsIn[i - 1]) > 1e-6);
    if (closed && pts.length > 2 && dist(pts[0], pts[pts.length - 1]) < 1e-6) pts = pts.slice(0, -1);
    if (pts.length < 2 || !this.mesh) return;
    const hw = width / 2, n = pts.length;
    const unit = (v    )     => { const l = Math.hypot(v[0], v[1]) || 1; return [v[0] / l, v[1] / l]; };
    const dirs       = pts.map((p, i) => unit([pts[(i + 1) % n][0] - p[0], pts[(i + 1) % n][1] - p[1]]));
    if (!closed) {
      dirs[n - 1] = dirs[n - 2];
      pts = [[pts[0][0] - dirs[0][0] * hw, pts[0][1] - dirs[0][1] * hw], ...pts.slice(1, -1),
        [pts[n - 1][0] + dirs[n - 1][0] * hw, pts[n - 1][1] + dirs[n - 1][1] * hw]];
    }
    const key = `${slot[0]}|${slot[1]}`;
    if (!this.mesh.has(key)) this.mesh.set(key, { v: [], i: [] });
    const sec = this.mesh.get(key) ;
    const base = sec.v.length, x = faceX - CHALK_D;
    pts.forEach(([py, pz], i) => {
      const d1 = dirs[i];
      const d0 = closed || i > 0 ? dirs[(i - 1 + n) % n] : d1;
      const n0     = [-d0[1], d0[0]], n1     = [-d1[1], d1[0]];
      const sum     = [n0[0] + n1[0], n0[1] + n1[1]];
      const m = Math.hypot(sum[0], sum[1]) > 1e-6 ? unit(sum) : n1;
      const k = hw / Math.max(m[0] * n1[0] + m[1] * n1[1], 0.5);
      for (const sgn of [1, -1]) {
        const y = py + sgn * k * m[0], z = pz + sgn * k * m[1];
        sec.v.push([[x, y, z], [-1, 0, 0], [0, 1, 0], [y / C.UV_UNIT, z / C.UV_UNIT]]);
      }
    });
    for (let i = 0; i < (closed ? n : n - 1); i++) {
      const j = (i + 1) % n;
      const l0 = base + 2 * i, r0 = base + 2 * i + 1, l1 = base + 2 * j, r1 = base + 2 * j + 1;
      for (let tri of [[l0, r0, r1], [l0, r1, l1]]) {
        const [a, b, c] = tri.map((v) => sec.v[v][0]);
        // (B - A) x (C - A) must point +x, against the face normal (-x): the installed winding
        if ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]) < 0) tri = [tri[0], tri[2], tri[1]];
        sec.i.push(...tri);
      }
    }
  }
}

const CHALK_D = 2.0;                             // the chalk stands this far proud of the board

// Join segments that meet end to start into polylines.
function chains(segs            )         {
  const out         = [];
  for (const [a, c] of segs) {
    const last = out[out.length - 1];
    if (last && last[last.length - 1][0] === a[0] && last[last.length - 1][1] === a[1]) last.push(c);
    else out.push([a, c]);
  }
  return out;
}
return { MapPieces, CHALK_D, chains };
})();

// ---- hall.ts
const __hall_ts = (() => {
const { TEMPLATE } = __template_ts;
// The lecture hall: walls, the board with its frame and ledge, the stepped floor with its desks, the lecturer's desk.
// A port of trace_track.lecture_hall (v11: slab tiers, the outermost desk column left out).



const WALLS       = [0, "wall"];
const FLOOR       = [0, "ground"];
const CEIL       = [0, "ceiling"];
const WOOD       = [0, "ramp"];
const BOARD       = [1, "wall"];
const CHALK       = [1, "ground"];                // the lines
const FRAME       = [1, "ceiling"];
const DARK       = [1, "ramp"];

function lectureHall(s           , bw        , bh        )       {
  const { FACE_X, EYE_X, D_WALL } = TEMPLATE.consts;
  const rw = bw + 900, floorZ = -bh - 700, ceilZ = bh + 700, backX = EYE_X - 2600;
  const t = 40;
  s.box(FACE_X, FACE_X + t, -rw, rw, floorZ, ceilZ, WALLS);
  s.box(backX - t, backX, -rw, rw, floorZ, ceilZ + 1400, WALLS);
  s.box(backX, FACE_X, -rw - t, -rw, floorZ, ceilZ + 1400, WALLS);
  s.box(backX, FACE_X, rw, rw + t, floorZ, ceilZ + 1400, WALLS);
  s.box(backX, FACE_X, -rw, rw, ceilZ + 1400, ceilZ + 1400 + t, CEIL);
  s.box(FACE_X - 6, FACE_X, -bw - 60, bw + 60, -bh - 60, bh + 60, BOARD);
  for (const [y0, y1, z0, z1] of [[-bw - 90, bw + 90, bh + 60, bh + 95], [-bw - 90, bw + 90, -bh - 95, -bh - 60],
    [-bw - 90, -bw - 60, -bh - 60, bh + 60], [bw + 60, bw + 90, -bh - 60, bh + 60]]) {
    s.box(FACE_X - 18, FACE_X, y0, y1, z0, z1, FRAME);
  }
  s.box(FACE_X - 45, FACE_X - 6, -bw + 150, bw - 150, -bh - 120, -bh - 95, FRAME);
  let x = FACE_X, z = floorZ;
  const tiers                             = [];
  while (x > backX) {                                  // tiers rising from the board to the back, a row of desks on each
    const x0 = Math.max(backX, x - 520);
    s.box(x0, x, -rw, rw, z - t, z, FLOOR);
    tiers.push([x0, x, z]);
    x = x0;
    z += 170;
  }
  const cols = Math.floor((rw - 750) / 700);
  for (const [x0, x1, zt] of tiers.slice(2)) {
    for (let j = 0; j < cols; j++) {
      for (const sgn of [-1, 1]) {
        const yc = sgn * (350 + 700 * j);
        if (Math.abs(yc) < 400 && x0 < EYE_X && EYE_X < x1 + 200) continue;   // the player's own place stays clear
        const top = zt + 230;
        if (top > -bh * (FACE_X - x1) / D_WALL - 60) continue;               // never above the line to the board
        s.box(x0 + 120, x0 + 400, yc - 260, yc + 260, top - 25, top, WOOD);
        s.box(x0 + 140, x0 + 380, yc - 240, yc + 240, zt, top - 25, DARK);
      }
    }
  }
  s.box(FACE_X - 900, FACE_X - 400, -700, 700, floorZ, floorZ + 280, WOOD);   // the lecturer's desk
}
return { WALLS, FLOOR, CEIL, WOOD, BOARD, CHALK, FRAME, DARK, lectureHall };
})();

// ---- scenario.ts
const __scenario_ts = (() => {
const { dist, check, radius3, rdp, INF } = __geometry_ts;
const { svgLines, fit, prepare } = __svg_ts;
const { planTour, layPath, routeLength } = __tour_ts;
const { MapPieces, chains } = __carve_ts;
const { lectureHall, CHALK } = __hall_ts;
const { TEMPLATE } = __template_ts;
// The scenario file: the template's profiles with this track's settings, and the map (room, chalk, waypoints).
// A port of trace_track.build_track.







                          
               
                                                                                                      
                                               
                                             
                                                                                     
                
                
               
                                                                                                      
                                                                                      
 

const DEFAULTS          = {
  name: "My Drawing",
  description: "Smooth tracking along a path you can see.[nl]The bot traces the drawing on the chalkboard: {tour}. "
    + "Hold fire: every second on the bot scores 100.",
  speed: 5, rBot: 0.4, box: [41, 20], turnR: 0.25, clear: 0.3, tags: "Tracking, Smooth",
};

                         
              
                  
             
                 
                  
                    
                  
                     
 

const C = TEMPLATE.consts;
const f1 = (v        ) => v.toFixed(1);
const f6 = (v        ) => v.toFixed(6);

function setKey(lines          , section               , key        , value        )       {
  let inside = section === null, current = "";
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (l.startsWith("[")) { inside = false; current = l; continue; }
    if (section !== null && l.startsWith("Name=")) inside = `${current}|${l.slice(5)}` === section;
    if (inside && l.startsWith(key + "=")) { lines[i] = `${key}=${value}`; return; }
  }
  throw new Error(`no ${key} in ${section ?? "the scenario settings"}`);
}

function dumpMap(m     )         {
  // indented like the game writes it, with compact mesh data (one vertex a line, 60 indices a line)
  const meshes        = [];
  const copy = { ...m, objects: m.objects.map((o     ) => {
    if (!o.procedural) return o;
    meshes.push(o.procedural);
    return { ...o, procedural: `@@mesh${meshes.length - 1}@@` };
  }) };
  let text = JSON.stringify(copy, null, 4);
  meshes.forEach((secs, k) => {
    const parts = secs.map((sec     ) => {
      const rows           = [];
      for (let i = 0; i < sec.indices.length; i += 60) rows.push(sec.indices.slice(i, i + 60).join(","));
      return `{"indices":[\n${rows.join(",\n")}\n],"vertices":[\n${sec.vertices.map((v     ) => JSON.stringify(v)).join(",\n")}\n]}`;
    });
    text = text.replace(`"@@mesh${k}@@"`, `[\n${parts.join(",\n")}\n]`);
  });
  return text;
}

function buildFromSvg(svgText        , options                   = {})         {
  const o          = { ...DEFAULTS, ...options };
  const lines = svgLines(svgText);
  if (!lines.length) throw new Error("no lines in the drawing");
  return buildTrack(fit(lines, o.box), o);
}

function buildTrack(shapesIn         , o         )         {
  const warnings           = [];
  const log = (msg        ) => { if (msg.startsWith("WARNING")) warnings.push(msg.slice(8)); };
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
  const m      = JSON.parse(JSON.stringify(TEMPLATE.map));
  const wallPt = (p    )     => [C.D_WALL * Math.tan(p[0] * Math.PI / 180), C.D_WALL * Math.tan(p[1] * Math.PI / 180)];
  const bw = C.D_WALL * Math.tan(o.box[0] * Math.PI / 180), bh = C.D_WALL * Math.tan(o.box[1] * Math.PI / 180);
  const pieces = new MapPieces();
  pieces.section();
  lectureHall(pieces, bw, bh);
  pieces.section();
  pieces.beginMesh();
  for (const s of laid.shapes) {
    const wall = s.points.map(wallPt);
    let line      ;
    if (s.closed) {
      const half = Math.floor(wall.length / 2);
      line = [...rdp(wall.slice(0, half + 1), 1.5).slice(0, -1), ...rdp([...wall.slice(half), wall[0]], 1.5)];
    } else line = rdp(wall, 1.5);
    pieces.ribbon(CHALK, line, C.FACE_X - 6, 12, s.closed);
  }
  for (const route of laid.routes) {                   // dashes: one simplified ribbon per dash
    const dense       = [route[0]];
    for (let i = 0; i + 1 < route.length; i++) {
      const p = route[i], q = route[i + 1];
      const steps = Math.max(1, Math.floor(dist(p, q) / 0.05));
      for (let j = 1; j <= steps; j++) dense.push([p[0] + (q[0] - p[0]) * j / steps, p[1] + (q[1] - p[1]) * j / steps]);
    }
    let run = 0, dash       = [];
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
  const plane       = path.map(([a, b]) => [Math.tan(a * Math.PI / 180), Math.tan(b * Math.PI / 180)]);
  const step = (o.speed * Math.PI / 180) * 0.125;
  const wps       = [plane[0]];
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
  const sp      = JSON.parse(JSON.stringify(TEMPLATE.spawn));
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
  const player = m.objects.find((ob     ) => ob.name === "SpawnPoint"
    && ob.properties?.some((q     ) => q.name === "TeamMask" && q.value === 1));
  player.rotation = `0.000000, ${f6(Math.atan(v0 / Math.sqrt(1 + u0 * u0)) * 180 / Math.PI)}, ${f6(Math.atan(u0) * 180 / Math.PI)}`;

  let rMin = INF;
  for (let i = 0; i < path.length; i++) rMin = Math.min(rMin, radius3(path[(i - 5 + path.length) % path.length], path[i], path[(i + 5) % path.length]));
  if (rMin < o.turnR * 0.5) warnings.push(`the tightest turn has a radius of ${rMin.toFixed(2)} deg`);
  const sce = (head.join("\n") + "[Map Data]\n" + dumpMap(m)).replace(/\n/g, "\r\n");
  return { sce, shapes: laid.shapes, path, routes: laid.routes, seconds, waypoints: wps.length,
    objects: m.objects.length, warnings };
}
return { DEFAULTS, buildFromSvg, buildTrack };
})();

// ---- ui.ts
const __ui_ts = (() => {
const { buildFromSvg, DEFAULTS } = __scenario_ts;
// The page: an SVG in, a picture of the board and the tour, a KovaaK's scenario out.



const CSS = `
.tt-root{font:14px/1.45 system-ui,sans-serif;color:inherit;max-width:1100px}
.tt-root h3{margin:.2em 0 .6em;font-size:1.15em}
.tt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.6em 1em;margin:.6em 0}
.tt-root label{display:flex;flex-direction:column;gap:.2em;font-size:.9em}
.tt-root input,.tt-root textarea{font:inherit;padding:.35em .5em;border:1px solid #8888;border-radius:6px;background:transparent;color:inherit}
.tt-root textarea{width:100%;min-height:110px;font-family:ui-monospace,monospace;font-size:12px;box-sizing:border-box}
.tt-row{display:flex;gap:.6em;align-items:center;flex-wrap:wrap;margin:.6em 0}
.tt-root button,.tt-root a.tt-btn{font:inherit;padding:.45em 1em;border-radius:6px;border:1px solid #2e6b4f;background:#2e6b4f;color:#fff;cursor:pointer;text-decoration:none}
.tt-root button[disabled]{opacity:.5;cursor:default}
.tt-root canvas{width:100%;border-radius:8px;display:block;margin:.6em 0;background:#2d5741}
.tt-out{font-size:.9em;margin:.4em 0}
.tt-warn{color:#c77a14}
.tt-err{color:#c0392b}
`;

const SAMPLE = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <path d="M 150 140 C 150 80, 60 80, 60 150 C 60 210, 150 250, 150 290 C 150 250, 240 210, 240 150 C 240 80, 150 80, 150 140 Z"/>
  <circle cx="410" cy="200" r="80"/>
  <rect x="580" y="120" width="160" height="160" rx="30"/>
</svg>`;

function mount(host             )       {
  if (host.dataset.ttMounted) return;
  host.dataset.ttMounted = "1";
  if (!document.getElementById("tt-style")) {
    const st = document.createElement("style");
    st.id = "tt-style";
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  host.innerHTML = `
  <div class="tt-root">
    <h3>Trace track: a KovaaK's tracking scenario from a drawing</h3>
    <div>Give it an SVG. The bot traces every line of the drawing on a lecture hall's chalkboard, flying a dashed route
    from one line to the next. Download the scenario and put it in KovaaK's Scenarios folder.</div>
    <div class="tt-row"><input type="file" accept=".svg,image/svg+xml" class="tt-file"> <span>or paste the SVG below</span></div>
    <textarea class="tt-svg" spellcheck="false"></textarea>
    <div class="tt-grid">
      <label>Scenario name<input class="tt-name"></label>
      <label>Bot speed (deg/s)<input class="tt-speed" type="number" min="1" max="30" step="0.5"></label>
      <label>Bot radius (deg)<input class="tt-radius" type="number" min="0.1" max="3" step="0.05"></label>
      <label>Search tags<input class="tt-tags"></label>
    </div>
    <label>Description ({tour} becomes the lines in the order the bot visits them)<textarea class="tt-desc" style="min-height:60px"></textarea></label>
    <div class="tt-row"><button class="tt-build">Build</button><a class="tt-btn tt-dl" style="display:none">Download .sce</a><span class="tt-status"></span></div>
    <canvas class="tt-canvas" width="1640" height="840"></canvas>
    <div class="tt-out"></div>
  </div>`;
  const q =                    (sel        ) => host.querySelector(sel)     ;
  const svgBox = q                     (".tt-svg"), nameBox = q                  (".tt-name");
  const speedBox = q                  (".tt-speed"), radiusBox = q                  (".tt-radius");
  const tagsBox = q                  (".tt-tags"), descBox = q                     (".tt-desc");
  const btn = q                   (".tt-build"), dl = q                   (".tt-dl");
  const status = q                 (".tt-status"), out = q                (".tt-out");
  const canvas = q                   (".tt-canvas");
  svgBox.value = SAMPLE;
  nameBox.value = DEFAULTS.name;
  speedBox.value = String(DEFAULTS.speed);
  radiusBox.value = String(DEFAULTS.rBot);
  tagsBox.value = DEFAULTS.tags;
  descBox.value = DEFAULTS.description;
  q                  (".tt-file").addEventListener("change", async (ev) => {
    const file = (ev.target                    ).files?.[0];
    if (file) {
      svgBox.value = await file.text();
      nameBox.value = file.name.replace(/\.svg$/i, "");
    }
  });
  btn.addEventListener("click", () => {
    btn.disabled = true;
    status.textContent = "building…";
    dl.style.display = "none";
    setTimeout(() => {                                 // let the page repaint first: a big drawing takes a while
      try {
        const res = buildFromSvg(svgBox.value, {
          name: nameBox.value.trim() || DEFAULTS.name, description: descBox.value, tags: tagsBox.value,
          speed: +speedBox.value || DEFAULTS.speed, rBot: +radiusBox.value || DEFAULTS.rBot,
        });
        draw(canvas, res);
        const blob = new Blob([res.sce], { type: "text/plain" });
        dl.href = URL.createObjectURL(blob);
        dl.download = `${nameBox.value.trim() || DEFAULTS.name}.sce`;
        dl.style.display = "";
        out.innerHTML = `${res.shapes.length} lines · run ${res.seconds.toFixed(0)} s · ${res.waypoints} waypoints · `
          + `${res.objects} map objects · ${(res.sce.length / 1e6).toFixed(2)} MB`
          + res.warnings.map((w) => `<div class="tt-warn">${escapeHtml(w)}</div>`).join("");
        status.textContent = "";
        (host       ).ttLast = res;
      } catch (e) {
        out.innerHTML = `<div class="tt-err">${escapeHtml(String((e         ).message || e))}</div>`;
        status.textContent = "";
      } finally {
        btn.disabled = false;
      }
    }, 30);
  });
}

function escapeHtml(s        )         {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]          ));
}

function draw(canvas                   , res        )       {
  const ctx = canvas.getContext("2d") ;
  const box     = [41, 20], f = 20;
  ctx.fillStyle = "#2d5741";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const P = (p    )     => [20 + (p[0] + box[0]) * f, 20 + (box[1] - p[1]) * f];
  ctx.lineCap = ctx.lineJoin = "round";
  ctx.strokeStyle = "#ecece4";
  ctx.lineWidth = 3;
  for (const s of res.shapes) {
    ctx.beginPath();
    s.points.forEach((p, i) => { const [x, y] = P(p); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
    if (s.closed) ctx.closePath();
    ctx.stroke();
  }
  ctx.setLineDash([10, 10]);
  ctx.lineWidth = 2;
  for (const r of res.routes) {
    ctx.beginPath();
    r.forEach((p, i) => { const [x, y] = P(p); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
    ctx.stroke();
  }
  ctx.setLineDash([]);
  const [sx, sy] = P(res.path[0]);
  ctx.fillStyle = "#e0533c";
  ctx.beginPath();
  ctx.arc(sx, sy, 8, 0, 2 * Math.PI);
  ctx.fill();
}
return { mount };
})();

// ---- main.ts
const __main_ts = (() => {
const { mount } = __ui_ts;
const { buildFromSvg, buildTrack, DEFAULTS } = __scenario_ts;
// Entry point: window.TraceTrack, and every element with data-trace-track gets the tool.



(window       ).TraceTrack = { mount, buildFromSvg, buildTrack, DEFAULTS };

function autoMount()       {
  document.querySelectorAll             ("[data-trace-track]").forEach((el) => mount(el));
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", autoMount);
else autoMount();
return {  };
})();
})();
