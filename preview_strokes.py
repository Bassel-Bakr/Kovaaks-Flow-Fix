"""Preview stroke-built signs next to the current pixel signs (writes test_out/preview_strokes.png)."""
import json

from PIL import Image, ImageDraw

import strokes

ins = json.load(open("inscriptions.json", encoding="utf-8"))
chars = [c for c in ins["text"]["welcome"] + ins["text"]["madeby"] + ins["text"]["name"] if c != " "]
seen = []
for c in chars:
    if c not in seen:
        seen.append(c)

S = 3                      # preview pixels per em-pixel
CELL = 80 * S
rows = [("now: pixel blocks", None), ("proposed: strokes (one rotated block each; count below)", (120, 4.0))]
img = Image.new("RGB", (len(seen) * CELL + 20, len(rows) * (CELL + 40)), (217, 183, 138))
d = ImageDraw.Draw(img)
totals = []
for ri, (label, eps) in enumerate(rows):
    y_off = ri * (CELL + 40) + 30
    d.text((10, y_off - 25), label, fill=(0, 0, 0))
    total = 0
    for ci, ch in enumerate(seen):
        x_off = ci * CELL + 10
        if eps is None:
            bm = ins["signs"]["13"][ch]
            p = 72 / 13 * S      # draw at the same em scale as the strokes
            for r, line in enumerate(bm):
                for c, v in enumerate(line):
                    if v != ".":
                        d.rectangle([x_off + c * p, y_off + r * p, x_off + (c + 1) * p, y_off + (r + 1) * p],
                                    fill=(29, 77, 122))
            continue
        em, strokes.EPS = eps
        strokes.MIN_LEN = max(3, em // 20)
        segs, size = strokes.sign_strokes(ch, em)
        k = 72 / em                                   # draw every row at the same scale
        segs = [((a[0] * k, a[1] * k), (b[0] * k, b[1] * k)) for a, b in segs]
        total += len(segs)
        for (y0, z0), (y1, z1) in segs:
            d.line([x_off + y0 * S, y_off + z0 * S, x_off + y1 * S, y_off + z1 * S], fill=(29, 77, 122), width=2 * S)
        d.text((x_off, y_off + CELL - 30), str(len(segs)), fill=(120, 0, 0))
    totals.append((label, total))
img.save("test_out/preview_strokes.png")
print(totals)
