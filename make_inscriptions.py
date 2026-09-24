"""Render the user's hieroglyph inscriptions into pixel art for egypt.py (writes inscriptions.json).

Signs come from Windows' Segoe UI Historic font, which draws them as thin outlines. For relief they are
rendered 8x oversize, their enclosed interiors filled (a raised silhouette, as in Egyptian relief), then
shrunk by area coverage. All signs of one size share the font's em square, so small signs (bread, water,
strokes) stay small, as in real writing.

Text (the user's own, 2026-09-23):
  left columns   "Welcome to my humble home"
  right columns  "This place was made by" + Bassel Bakr in a cartouche
  left wall      "Left side";  right wall "Right side"
  filler         ankh djed was, "life, stability, dominion"

Usage: python make_inscriptions.py
"""
import json

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = r"C:\Windows\Fonts\seguihis.ttf"
OVER = 8                     # oversampling factor
COVER = 0.33                 # a pixel is carved when at least this share of it is ink

TEXT = {
    "welcome": "𓉐𓏏𓊖 𓎡𓄿𓂋𓇋 𓈖𓎡",
    "maker": "𓏏𓏭 𓇋𓅓 𓊪𓏏𓏭 𓅓𓄿𓂋𓎡𓄿",
    "name": "𓃀𓄿𓋴𓇋𓃭 𓃀𓄿𓎡𓂋",
    "madeby": "𓁹𓈖",          # iri.n, "made by": the formula before a craftsman's name (2026-09-23)
    "left": "𓂋𓂝 𓎡𓃏𓏏",
    "right": "𓇋𓃀 𓎡𓃏𓏏",
    "filler": "𓋹𓊽𓌀",
}
COLUMN_EMS = (13, 12, 11, 10, 9, 8)  # sign sizes the layout may use (the cartouche uses smaller ones)
NAME_EMS = (10, 9, 8)              # sign sizes inside the cartouche
LINE_EM = 12                       # side-wall labels


def filled(img):
    """Fill every background region not connected to the border (the inside of outlined shapes)."""
    w, h = img.size
    mask = img.point(lambda v: 255 if v > 100 else 0)
    outside = mask.copy()
    ImageDraw.floodfill(outside, (0, 0), 128)   # border was padded, so (0,0) is background
    return outside.point(lambda v: 0 if v == 128 else 255)


def ink(text, em):
    font = ImageFont.truetype(FONT, em * OVER)
    l, t, r, b = font.getbbox(text)
    pad = 2 * OVER
    img = Image.new("L", (r - l + 2 * pad, b - t + 2 * pad), 0)
    ImageDraw.Draw(img).text((pad - l, pad - t), text, font=font, fill=255)
    img = img.filter(ImageFilter.MaxFilter(3))          # close hairline gaps before filling
    return filled(img)


def shrink(img):
    w, h = img.size
    cw, ch = w // OVER, h // OVER
    px = img.load()
    rows = []
    for cy in range(ch):
        row = []
        for cx in range(cw):
            on = sum(px[cx * OVER + dx, cy * OVER + dy] > 0 for dx in range(OVER) for dy in range(OVER))
            row.append("#" if on >= COVER * OVER * OVER else ".")
        rows.append("".join(row))
    return trim(rows)


def trim(rows):
    rows = [r for r in rows]
    while rows and set(rows[0]) == {"."}:
        rows.pop(0)
    while rows and set(rows[-1]) == {"."}:
        rows.pop()
    if not rows:
        return ["."]
    left = min((len(r) - len(r.lstrip(".")) for r in rows if "#" in r))
    right = max((len(r.rstrip(".")) for r in rows if "#" in r))
    return [r[left:right] for r in rows]


# Hand-drawn pixel signs (egypt_glyphs.json) win where they exist: filled font signs lose what tells
# them apart at this size (owl vs vulture look alike, the djed loses its bars).
HAND = {"𓋹": "ankh", "𓊽": "djed pillar", "𓌀": "was sceptre", "𓄿": "vulture", "𓅓": "owl",
        "𓇋": "reed leaf", "𓈖": "water ripple", "𓂋": "mouth", "𓏏": "bread loaf"}
_hand = {g["name"]: g["rows"] for g in json.load(open("egypt_glyphs.json", encoding="utf-8"))["glyphs"]}


def sign(char, em):
    """One sign, trimmed to its ink. Font signs rendered at one em keep their relative sizes."""
    if char in HAND:
        return trim(_hand[HAND[char]])
    return shrink(ink(char, em))


GAP, WORD_GAP = 3, 5        # empty pixels between signs and words; 1-px outlines fuse below a gap of 3


def cartouche(name, em):
    """Name signs stacked top to bottom inside a vertical cartouche: 1 px ring, 2 px padding, tie bar below."""
    signs = [sign(c, em) for c in name if c != " "]
    inner_w = max(len(s[0]) for s in signs)
    body = []
    for i, s in enumerate(signs):
        if i:
            body += ["." * inner_w] * GAP
        for r in s:
            lpad = (inner_w - len(r)) // 2
            body.append("." * lpad + r + "." * (inner_w - len(r) - lpad))
    w = inner_w + 6
    blank = "#" + "." * (w - 2) + "#"
    rows = ["." + "#" * (w - 2) + ".", blank, blank]
    rows += ["#.." + r + "..#" for r in body]
    rows += [blank, blank, "." + "#" * (w - 2) + ".", "." * w, "." * w, "#" * w]
    return rows


def line(text, em):
    """A horizontal line of signs, vertically centred, with fixed gaps (font spacing is too tight for outlines)."""
    parts = []
    for wi, word in enumerate(text.split()):
        for ci, ch in enumerate(word):
            if parts:
                parts.append(GAP if ci else WORD_GAP)
            parts.append(sign(ch, em))
    h = max(len(s) for s in parts if isinstance(s, list))
    out = [""] * h
    for s in parts:
        if isinstance(s, int):
            out = [r + "." * s for r in out]
            continue
        top = (h - len(s)) // 2
        for i in range(h):
            out[i] += s[i - top] if top <= i < top + len(s) else "." * len(s[0])
    return out


def main():
    out = {"text": TEXT, "signs": {}, "cartouche": {}, "lines": {}, "strokes": {}}
    chars = {c for k in ("welcome", "maker", "filler", "madeby", "name") for c in TEXT[k] if c != " "}
    for em in COLUMN_EMS:
        out["signs"][str(em)] = {c: sign(c, em) for c in sorted(chars)}
    for em in NAME_EMS:
        out["cartouche"][str(em)] = cartouche(TEXT["name"], em)
    for k in ("left", "right"):
        out["lines"][k] = line(TEXT[k], LINE_EM)
    import strokes                                   # stroke signs: one rotated block per stroke
    for c in sorted({c for k in ("welcome", "maker", "madeby", "name") for c in TEXT[k] if c != " "}):
        segs, size = strokes.sign_strokes(c)
        out["strokes"][c] = {"em": strokes.EM, "size": [round(v, 2) for v in size],
                             "segs": [[round(v, 2) for v in a + b] for a, b in segs]}
    with open("inscriptions.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    s13 = out["signs"]["13"]
    for c in TEXT["welcome"].replace(" ", ""):
        print(c, f"{len(s13[c][0])}x{len(s13[c])}")
        print("\n".join("   " + r for r in s13[c]))
    print("cartouche em 10:", f"{len(out['cartouche']['10'][0])}x{len(out['cartouche']['10'])}")
    print("\n".join("   " + r for r in out["cartouche"]["10"]))
    for k in ("left", "right"):
        rows = out["lines"][k]
        print(f"{k} label {len(rows[0])}x{len(rows)}")
        print("\n".join("   " + r for r in rows))


if __name__ == "__main__":
    main()
