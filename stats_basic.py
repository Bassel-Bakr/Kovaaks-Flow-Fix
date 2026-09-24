"""Read-only summary of runs for any scenarios, matched by name.

Usage: python stats_basic.py "wide varying" "confirm precise" ...
Each argument matches "<anything> <argument> - Challenge - <date> Stats.csv", so old and new numbers both count.
"""
import glob
import statistics as st
import sys

STATS = "C:/Program Files (x86)/Steam/steamapps/common/FPSAimTrainer/FPSAimTrainer/stats"


def parse(f):
    rows, tot, hdr = [], {}, None
    for line in open(f, encoding="utf-8", errors="replace"):
        p = [x.strip() for x in line.rstrip("\n").split(",")]
        if p[0] == "Kill #":
            hdr = p
        elif hdr and p[0].isdigit():
            rows.append(dict(zip(hdr, p)))
        elif len(p) >= 2 and p[0].endswith(":"):
            tot[p[0][:-1]] = p[1]
    return rows, tot


def secs(s):
    h, m, x = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(x)


for name in sys.argv[1:]:
    files = sorted(glob.glob(f"{STATS}/*{name} - Challenge - *Stats.csv"))
    print(f"== {name}: {len(files)} runs")
    allv = []
    for f in files:
        rows, tot = parse(f)
        prev, iv = secs(tot["Challenge Start"]), []
        for r in rows:
            t = secs(r["Timestamp"])
            iv.append(t - prev)
            prev = t
        allv += iv
        missed = sum(1 for r in rows if int(r["Shots"]) > int(r["Hits"]))
        q = sorted(iv)
        print(f"  {f.split(' - ')[-1][:19]}  score {float(tot['Score']):7.2f}  kills {tot['Kills']:>3}  "
              f"misses {tot['Miss Count']:>3}  kills with a miss {missed / len(rows):4.0%}  | time per kill "
              f"p10 {q[len(q) // 10]:.3f}  median {st.median(iv):.3f}  p90 {q[9 * len(q) // 10]:.3f}  "
              f"spread (CV) {st.pstdev(iv) / st.mean(iv):.2f}")
    if len(files) > 1:
        q = sorted(allv)
        print(f"  all runs: time per kill p10 {q[len(q) // 10]:.3f}  median {st.median(allv):.3f}  "
              f"p90 {q[9 * len(q) // 10]:.3f}  spread (CV) {st.pstdev(allv) / st.mean(allv):.2f}")
