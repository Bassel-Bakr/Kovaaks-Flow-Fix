// Map pieces: plain blocks (the hall) and one custom mesh of flat chalk ribbons (the lines, dashes and labels).
// A port of egypt.Scene.box/end_mesh and trace_track.ribbon.
import { type Pt, dist } from "./geometry.ts";
import { TEMPLATE } from "./template.ts";

export type Slot = [number, string];
type V3 = [number, number, number];
interface MeshSec { v: [V3, V3, V3, [number, number]][]; i: number[] }

const C = TEMPLATE.consts;
const f6 = (v: number) => v.toFixed(6);
const f4 = (v: number) => v.toFixed(4);

export class MapPieces {
  objects: any[] = [];
  group: number = C.GROUP_BASE;
  mesh: Map<string, MeshSec> | null = null;

  section(): void {                                    // a new editor group; a mesh in progress ends here
    this.endMesh();
    this.group += 1;
  }

  box(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, slot: Slot): void {
    if (x1 - x0 <= 0 || y1 - y0 <= 0 || z1 - z0 <= 0) return;
    const b: any = JSON.parse(JSON.stringify(TEMPLATE.brush));
    delete b.group;
    b.name = C.BRUSH_NAME;
    b.group = this.group;
    b.location = `${f6(x0)}, ${f6(y0)}, ${f6(z0)}`;
    b.scale = `${f6((x1 - x0) / 100)}, ${f6((y1 - y0) / 100)}, ${f6((z1 - z0) / 100)}`;
    b.rotation = "0.000000, 0.000000, 0.000000";
    b.materialSets = Array.from({ length: 6 }, () => ({ group: slot[0], surface: slot[1] }));
    this.objects.push(b);
  }

  beginMesh(): void { this.mesh = new Map(); }

  endMesh(): void {
    const mesh = this.mesh;
    this.mesh = null;
    if (!mesh || mesh.size === 0) return;
    const all = Array.from(mesh.values()).flatMap((s) => s.v);
    const origin = [0, 1, 2].map((i) => Math.min(...all.map((v) => v[0][i])));
    const b: any = JSON.parse(JSON.stringify(TEMPLATE.brush));
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
  ribbon(slot: Slot, ptsIn: Pt[], faceX: number, width: number, closed: boolean = false): void {
    let pts = ptsIn.filter((p, i) => i === 0 || dist(p, ptsIn[i - 1]) > 1e-6);
    if (closed && pts.length > 2 && dist(pts[0], pts[pts.length - 1]) < 1e-6) pts = pts.slice(0, -1);
    if (pts.length < 2 || !this.mesh) return;
    const hw = width / 2, n = pts.length;
    const unit = (v: Pt): Pt => { const l = Math.hypot(v[0], v[1]) || 1; return [v[0] / l, v[1] / l]; };
    const dirs: Pt[] = pts.map((p, i) => unit([pts[(i + 1) % n][0] - p[0], pts[(i + 1) % n][1] - p[1]]));
    if (!closed) {
      dirs[n - 1] = dirs[n - 2];
      pts = [[pts[0][0] - dirs[0][0] * hw, pts[0][1] - dirs[0][1] * hw], ...pts.slice(1, -1),
        [pts[n - 1][0] + dirs[n - 1][0] * hw, pts[n - 1][1] + dirs[n - 1][1] * hw]];
    }
    const key = `${slot[0]}|${slot[1]}`;
    if (!this.mesh.has(key)) this.mesh.set(key, { v: [], i: [] });
    const sec = this.mesh.get(key)!;
    const base = sec.v.length, x = faceX - CHALK_D;
    pts.forEach(([py, pz], i) => {
      const d1 = dirs[i];
      const d0 = closed || i > 0 ? dirs[(i - 1 + n) % n] : d1;
      const n0: Pt = [-d0[1], d0[0]], n1: Pt = [-d1[1], d1[0]];
      const sum: Pt = [n0[0] + n1[0], n0[1] + n1[1]];
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

export const CHALK_D = 2.0;                             // the chalk stands this far proud of the board

// Join segments that meet end to start into polylines.
export function chains(segs: [Pt, Pt][]): Pt[][] {
  const out: Pt[][] = [];
  for (const [a, c] of segs) {
    const last = out[out.length - 1];
    if (last && last[last.length - 1][0] === a[0] && last[last.length - 1][1] === a[1]) last.push(c);
    else out.push([a, c]);
  }
  return out;
}
