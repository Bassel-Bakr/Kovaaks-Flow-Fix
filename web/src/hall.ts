// The lecture hall: walls, the board with its frame and ledge, the stepped floor with its desks, the lecturer's desk.
// A port of trace_track.lecture_hall (v11: slab tiers, the outermost desk column left out).
import { type MapPieces, type Slot } from "./carve.ts";
import { TEMPLATE } from "./template.ts";

export const WALLS: Slot = [0, "wall"];
export const FLOOR: Slot = [0, "ground"];
export const CEIL: Slot = [0, "ceiling"];
export const WOOD: Slot = [0, "ramp"];
export const BOARD: Slot = [1, "wall"];
export const CHALK: Slot = [1, "ground"];                // the lines
export const FRAME: Slot = [1, "ceiling"];
export const DARK: Slot = [1, "ramp"];

export function lectureHall(s: MapPieces, bw: number, bh: number): void {
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
  const tiers: [number, number, number][] = [];
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
