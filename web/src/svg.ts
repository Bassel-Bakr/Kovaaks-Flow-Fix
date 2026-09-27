// Reading SVG: every line of a drawing as points in its own units (y down), sampled by the browser's own SVG engine,
// so every path command, arc and transform works. Then fitted to the board.
import { type Pt, dist, resample, ease, STEP } from "./geometry.ts";

export interface Shape {
  name: string;
  points: Pt[];
  closed: boolean;
}

const GEOMETRY = "path, polyline, polygon, line, rect, circle, ellipse";

export function svgLines(svgText: string): { points: Pt[]; closed: boolean }[] {
  const doc = new DOMParser().parseFromString(svgText, "image/svg+xml");
  const root = doc.documentElement;
  if (root.nodeName.toLowerCase() !== "svg") throw new Error("not an SVG drawing");
  // attached (out of sight), so the browser can measure lengths and transforms
  const holder = document.createElement("div");
  holder.style.cssText = "position:absolute;left:-10000px;top:0;width:10px;height:10px;overflow:hidden";
  const svg = document.importNode(root, true) as unknown as SVGSVGElement;
  holder.appendChild(svg);
  document.body.appendChild(holder);
  try {
    const out: { points: Pt[]; closed: boolean }[] = [];
    const bbox = svg.getBBox();
    const size = Math.max(bbox.width, bbox.height) || 1;
    const rootCtm = svg.getCTM();
    for (const el of Array.from(svg.querySelectorAll(GEOMETRY)) as SVGGeometryElement[]) {
      if (el.closest("defs, clipPath, mask, symbol")) continue;
      const len = el.getTotalLength();
      if (!(len > 0)) continue;
      const toRoot = (rootCtm ? rootCtm.inverse() : new DOMMatrix()).multiply(el.getCTM() ?? new DOMMatrix());
      const h = size / 4000;                           // fine sampling; resampled on the board afterwards
      const n = Math.max(8, Math.ceil(len / h));
      const pts: Pt[] = [];
      for (let i = 0; i <= n; i++) {
        const p = el.getPointAtLength(len * i / n);
        const q = new DOMPoint(p.x, p.y).matrixTransform(toRoot);
        pts.push([q.x, q.y]);
      }
      // a path with several subpaths jumps at each moveto: split there
      const parts: Pt[][] = [[pts[0]]];
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
export function fit(lines: { points: Pt[]; closed: boolean }[], box: Pt, margin = 1.5, minLen = 1.0): Shape[] {
  const xs = lines.flatMap((l) => l.points.map((p) => p[0]));
  const ys = lines.flatMap((l) => l.points.map((p) => p[1]));
  const w = (Math.max(...xs) - Math.min(...xs)) || 1, h = (Math.max(...ys) - Math.min(...ys)) || 1;
  const k = Math.min((2 * box[0] - 2 * margin) / w, (2 * box[1] - 2 * margin) / h);
  const cx = (Math.max(...xs) + Math.min(...xs)) / 2, cy = (Math.max(...ys) + Math.min(...ys)) / 2;
  const shapes: Shape[] = [];
  lines.forEach((line, i) => {
    let q: Pt[] = line.points.map(([x, y]) => [(x - cx) * k, (cy - y) * k]);
    if (line.closed && dist(q[0], q[q.length - 1]) < 1e-6) q = q.slice(0, -1);
    let length = 0;
    for (let j = 0; j + 1 < q.length; j++) length += dist(q[j], q[j + 1]);
    if (line.closed) length += dist(q[q.length - 1], q[0]);
    if (length >= minLen && q.length >= 2) shapes.push({ name: `line ${i + 1}`, points: q, closed: line.closed });
  });
  return shapes;
}

// A shape as the builder wants it: points STEP apart, no turn tighter than turnR.
export function prepare(shape: Shape, turnR: number): Shape {
  const pts = resample(shape.points, STEP, shape.closed);
  return { name: shape.name, points: ease(pts, turnR, shape.closed), closed: shape.closed };
}
