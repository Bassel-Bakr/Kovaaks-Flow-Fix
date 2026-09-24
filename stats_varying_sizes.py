"""Read-only analysis of "varying sizes pacing" runs (flowfix 08, renumbered 09) from KovaaK's stats CSVs."""
import glob
import os
import statistics as st

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


# Small radius became 30 at this time; only runs finished after it are analysed (earlier runs used 35).
CUTOFF = "2026.09.23-01.12.22"
# Fixed size cycles replaced the random rotation at this time. Set BUILD=random to analyse the earlier runs.
FIXED = "2026.09.23-01.22.27"
BUILD = "fixed"
files = [f for f in sorted((glob.glob(f"{STATS}/flowfix * varying sizes pacing - *Stats.csv") + glob.glob(f"{STATS}/Flow Fix Pacing Drop - *Stats.csv")))
         if (FIXED if BUILD == "fixed" else CUTOFF) < f.split(" - ")[-1][:19] < ("9" if BUILD == "fixed" else FIXED)]
if not files:
    raise SystemExit("no varying-sizes runs in this build yet")
agg, after = {}, {}
print("runs:")
for f in files:
    rows, tot = parse(f)
    prev, prevbot, ivs, by = secs(tot["Challenge Start"]), None, [], {}
    for r in rows:
        t = secs(r["Timestamp"])
        iv, prev, b = t - prev, t, r["Bot"]
        a = agg.setdefault(b, {"n": 0, "iv": [], "miss": 0})
        a["n"] += 1
        a["iv"].append(iv)
        a["miss"] += int(r["Shots"]) - int(r["Hits"])
        if prevbot:
            after.setdefault(prevbot, []).append(iv)
        prevbot = b
        ivs.append(iv)
        by[b] = by.get(b, 0) + 1
    cv = st.pstdev(ivs) / st.mean(ivs)
    print(f"  {os.path.basename(f).split(' - ')[-1][:19]}  score {tot['Score']}  kills {tot['Kills']}  "
          f"misses {tot['Miss Count']}  {by}  rhythm spread (CV) {cv:.2f}")

total = sum(a["n"] for a in agg.values())
print("\nper size, all runs:")
for b in ("big", "mid", "small"):
    a = agg[b]
    med = st.median(a["iv"])
    print(f"  {b:5}  kills {a['n']:3} ({a['n'] / total:.0%} of kills, {'50' if b == 'mid' else '25'}% of spawns)  "
          f"median {med:.3f}s  misses per kill {a['miss'] / a['n']:.2f}")
print("\nnext kill's time, by the size killed just before:")
for b in ("big", "mid", "small"):
    v = after.get(b, [])
    print(f"  after {b:5}  median {st.median(v):.3f}s  (n={len(v)})")
