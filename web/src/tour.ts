// The tour: the order of the shapes, where the bot joins and leaves each, and the routes between them.
// A port of trace_track.py's plan_tour and lay_path.
import { type Pt, dist, at, bezier, resample, tangent, INF, STEP } from "./geometry.ts";
import type { Shape } from "./svg.ts";

type Log = (msg: string) => void;
export interface Tour { order: number[]; ports: [number, number][] }

const coarseAll = (p: Pt[]) => Array.from({ length: Math.ceil(p.length / 20) }, (_, i) => i * 20);

function* permutations(items: number[]): Generator<number[]> {
  if (items.length <= 1) { yield items.slice(); return; }
  for (let i = 0; i < items.length; i++) {
    const rest = [...items.slice(0, i), ...items.slice(i + 1)];
    for (const p of permutations(rest)) yield [items[i], ...p];
  }
}

function nearestOrder(gap: (a: number, b: number) => number, n: number): number[] {
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

function twoOpt(order: number[], gap: (a: number, b: number) => number): number[] {
  const n = order.length;
  const length = (o: number[]) => o.reduce((s, k, i) => s + gap(k, o[(i + 1) % n]), 0);
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
export function planTour(shapes: Shape[], clear: number, maxHop: number, log: Log): Tour | null {
  const n = shapes.length;
  const pts = shapes.map((s) => s.points);
  if (n === 1) return { order: [0], ports: [shapes[0].closed ? [0, 0] : [0, pts[0].length - 1]] };
  const CELL = 0.1, END = 0.5;
  const near = new Set<string>();                    // grid cells within `clear` of any line
  const round = (v: number) => Math.round(v);
  for (const line of pts) {
    for (const [py, pz] of line) {
      for (let i = round((py - clear) / CELL) - 1; i <= round((py + clear) / CELL) + 1; i++) {
        for (let j = round((pz - clear) / CELL) - 1; j <= round((pz + clear) / CELL) + 1; j++) {
          if (Math.hypot(i * CELL - py, j * CELL - pz) <= clear) near.add(`${i},${j}`);
        }
      }
    }
  }
  const clearHop = (a: Pt, b: Pt) => {
    const d = dist(a, b);
    const steps = Math.floor(d / CELL) + 1;
    for (let s = 1; s < steps; s++) {
      const f = s / steps;
      if (Math.min(f, 1 - f) * d < END) continue;
      if (near.has(`${round((a[0] + f * (b[0] - a[0])) / CELL)},${round((a[1] + f * (b[1] - a[1])) / CELL)}`)) return false;
    }
    return true;
  };
  const memo = new Map<string, number>();
  const hop = (k: number, i: number, j: number, m: number) => {
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
  const arc = (k: number, e: number, x: number) => {
    const L = pts[k].length;
    if (!shapes[k].closed) return (e !== x && Math.min(e, x) === 0 && Math.max(e, x) === L - 1) ? 0 : INF;
    const f = (((x - e) % L) + L) % L;
    return Math.min(f, L - f) * STEP;
  };
  const coarse = shapes.map((s, k) => s.closed ? coarseAll(pts[k]) : [0, pts[k].length - 1]);

  const ringPorts = (order: number[]): [number, [number, number][] | null] => {
    const small = order.reduce((best, k) => coarse[k].length < coarse[best].length ? k : best, order[0]);
    const r = order.indexOf(small);
    const ring = [...order.slice(r), ...order.slice(0, r)];
    const steps = [...Array.from({ length: n - 1 }, (_, i) => i + 1), 0];
    let found: [number, Map<number, [number, number]> | null] = [INF, null];
    for (const x0 of coarse[ring[0]]) {
      let cost = new Map<number, number>([[x0, 0]]);
      const back: [Map<number, [number, number]>, Map<number, [number, number]>][] = [];
      for (const s of steps) {
        const k = ring[s], kp = at(ring, s - 1);
        const ent = new Map<number, [number, number]>();
        for (const e of coarse[k]) {
          let c = INF, from = -1;
          for (const [xp, cp] of cost) { const v = cp + hop(kp, xp, k, e); if (v < c) { c = v; from = xp; } }
          if (c < INF) ent.set(e, [c, from]);
        }
        const ext = new Map<number, [number, number]>();
        for (const x of (s === 0 ? [x0] : coarse[k])) {
          let c = INF, from = -1;
          for (const [e, [ce]] of ent) { const v = ce + arc(k, e, x); if (v < c) { c = v; from = e; } }
          if (c < INF) ext.set(x, [c, from]);
        }
        back.push([ent, ext]);
        cost = new Map(Array.from(ext, ([x, [c]]) => [x, c] as [number, number]));
      }
      const total = cost.get(x0) ?? INF;
      if (total < found[0]) {
        const ports = new Map<number, [number, number]>();
        let x = x0;
        for (let q = steps.length - 1; q >= 0; q--) {
          const [ent, ext] = back[q];
          const e = ext.get(x)![1];
          ports.set(ring[steps[q]], [e, x]);
          x = ent.get(e)![1];
        }
        found = [total, ports];
      }
    }
    return found[1] ? [found[0], order.map((k) => found[1]!.get(k)!)] : [INF, null];
  };

  const refine = (order: number[], pe: [number, number][]) => {
    for (let round_ = 0; round_ < 6; round_++) {
      const before = JSON.stringify(pe);
      order.forEach((k, s) => {
        if (!shapes[k].closed) return;
        const kp = at(order, s - 1), kn = order[(s + 1) % n], xp = at(pe, s - 1)[1], en = pe[(s + 1) % n][0];
        const m = pts[k].length;
        let best: [number, number, number] = [INF, 0, 0];
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

  const gapMemo = new Map<string, number>();
  const gap = (a: number, b: number) => {
    const key = a < b ? `${a},${b}` : `${b},${a}`;
    let v = gapMemo.get(key);
    if (v === undefined) {
      v = INF;
      for (const i of coarseAll(pts[a])) for (const j of coarseAll(pts[b])) v = Math.min(v, dist(pts[a][i], pts[b][j]));
      gapMemo.set(key, v);
    }
    return v;
  };
  let orders: number[][];
  if (n === 2) orders = [[0, 1]];
  else if (n <= 7) {
    orders = [];
    for (const rest of permutations(Array.from({ length: n - 1 }, (_, i) => i + 1))) {
      if (rest[0] < rest[rest.length - 1]) orders.push([0, ...rest]);
    }
    const lb = (o: number[]) => o.reduce((s, k, i) => s + gap(k, o[(i + 1) % n]), 0);
    orders.sort((a, b) => lb(a) - lb(b));
  } else orders = [twoOpt(nearestOrder(gap, n), gap)];
  let best: [number, number[] | null, [number, number][] | null] = [INF, null, null];
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

export interface Laid { path: Pt[]; routes: Pt[][]; tourNames: string[]; shapes: Shape[] }

// The bot's whole path (deg, STEP apart, starting nearest the board's centre) and the routes between shapes.
export function layPath(shapesIn: Shape[], tour: Tour, log: Log): Laid {
  const shapes = shapesIn.map((s) => ({ ...s, points: s.points.slice() }));
  const { order } = tour;
  const pe = tour.ports.map((p) => [p[0], p[1]] as [number, number]);
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
  const trav = (k: number, e: number, x: number): Pt[] => {
    const line = pts[k];
    if (shapes[k].closed) {
      const L = line.length;
      const lap = [...line.slice(e), ...line.slice(0, e), line[e]];
      const on = [...line.slice(e + 1), ...line.slice(0, e + 1)].slice(0, (((x - e) % L) + L) % L);
      return [...lap, ...on];
    }
    return e === 0 ? line : line.slice().reverse();
  };
  let path: Pt[] = [];
  const routes: Pt[][] = [];
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
      let route: Pt[] = [];
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

export function routeLength(pts: Pt[]): number {
  let s = 0;
  for (let i = 0; i + 1 < pts.length; i++) s += dist(pts[i], pts[i + 1]);
  return s;
}
