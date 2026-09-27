// Geometry on the board, in degrees (x across, y up). A port of trace_track.py's helpers.

export type Pt = [number, number];
export const STEP = 0.05;              // deg between the points of every line
export const INF = Infinity;

export function dist(a: Pt, b: Pt): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

export function at<T>(arr: T[], i: number): T {
  const n = arr.length;
  return arr[((i % n) + n) % n];
}

export function resample(pts: Pt[], h: number = STEP, closed: boolean = true): Pt[] {
  const src = closed ? [...pts, pts[0]] : [...pts];
  const out: Pt[] = [src[0]];
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

export function turnAngle(a: Pt, b: Pt, c: Pt): number {
  const t = Math.atan2(c[1] - b[1], c[0] - b[0]) - Math.atan2(b[1] - a[1], b[0] - a[0]) + Math.PI;
  return Math.abs((((t % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI);
}

// Smooth only the turns tighter than `radius` (and a few samples round them), a little each round.
export function ease(pts: Pt[], radius: number, closed: boolean = true, gap: number = 4, rounds: number = 60): Pt[] {
  const n = pts.length;
  for (let r = 0; r < rounds; r++) {
    const tight = new Set<number>();
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
export function check(pts: Pt[], clear: number, closed: boolean = true): [number, number] {
  const n = pts.length;
  let tight = 1e9;
  for (let i = closed ? 0 : 4; i < (closed ? n : n - 4); i++) {
    const a = at(pts, i - 4), b = pts[i], c = at(pts, i + 4);
    const t = turnAngle(a, b, c);
    if (t > 1e-9) tight = Math.min(tight, (dist(a, b) + dist(b, c)) / 2 / t);
  }
  const grid = new Map<string, number[]>();
  const gap = Math.floor(4 * clear / 0.1);
  pts.forEach(([y, z], i) => {
    const key = `${Math.floor(y / clear)},${Math.floor(z / clear)}`;
    if (!grid.has(key)) grid.set(key, []);
    grid.get(key)!.push(i);
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

export function bezier(p0: Pt, p1: Pt, p2: Pt, p3: Pt, step: number): Pt[] {
  const n = Math.max(8, Math.floor(3 * (dist(p0, p1) + dist(p1, p2) + dist(p2, p3)) / step));
  const out: Pt[] = [];
  for (let j = 1; j < n; j++) {
    const s = j / n;
    const f = (i: number) => (1 - s) ** 3 * p0[i] + 3 * (1 - s) ** 2 * s * p1[i] + 3 * (1 - s) * s * s * p2[i]
      + s ** 3 * p3[i];
    out.push([f(0), f(1)]);
  }
  return out;
}

export function radius3(a: Pt, b: Pt, c: Pt): number {
  const area2 = Math.abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
  return area2 > 1e-12 ? dist(a, b) * dist(b, c) * dist(a, c) / (2 * area2) : INF;
}

export function tangent(pts: Pt[], i: number, back: boolean = false): Pt {
  const [a, b] = back ? [at(pts, i - 6), pts[i]] : [pts[i], at(pts, i + 6)];
  const d = dist(a, b) || 1;
  return [(b[0] - a[0]) / d, (b[1] - a[1]) / d];
}

// Ramer-Douglas-Peucker, as strokes.rdp (points as given, any 2D units).
export function rdp(pts: Pt[], eps: number): Pt[] {
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
