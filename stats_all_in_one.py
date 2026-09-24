"""Read-only analysis of all-in-one runs (flowfix 12, renumbered 13), grouped by build (identified by the outer target's value)."""
import glob
import os
import statistics as st

STATS = "C:/Program Files (x86)/Steam/steamapps/common/FPSAimTrainer/FPSAimTrainer/stats"
# build -> (label, cube lifetime in s); the outer target's HP identifies the build
BUILDS = {1.0: ("outer 1, cube 1 s", 1.0), 2.0: ("outer 2, cube 1 s", 1.0), 1.5: ("outer 1.5, cube 1.5 s", 1.5)}


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


groups = {}
# "flowfix NN all-in-one" runs used nested rings; "Flow Fix Check" runs use the smaller on-screen layout
# (side bands for the small target), so the two are grouped separately.
files = glob.glob(f"{STATS}/flowfix * all-in-one - *Stats.csv") + glob.glob(f"{STATS}/Flow Fix Check - *Stats.csv")
for f in sorted(files, key=lambda f: f.split(" - ")[-1]):
    rows, tot = parse(f)
    far = [float(r["Damage Done"]) for r in rows if r["Bot"] == "far"]
    if not far or far[0] > 100:  # old kill-count builds (1000 damage per kill)
        continue
    layout = "on-screen layout" if "Flow Fix Check" in f else "rings layout"
    groups.setdefault((round(far[0], 2), layout), []).append((f, rows, tot))

for (key, layout), runs in groups.items():
    label, life = BUILDS.get(key, (f"outer {key}", None))
    label = f"{label}, {layout}"
    print(f"==== build: {label} ({len(runs)} runs)")
    iv, vals, kills, score = {}, [], {}, []
    for f, rows, tot in runs:
        prev = secs(tot["Challenge Start"])
        for r in rows:
            t = secs(r["Timestamp"])
            iv.setdefault(r["Bot"], []).append(t - prev)
            prev = t
            kills[r["Bot"]] = kills.get(r["Bot"], 0) + 1
            if r["Bot"] == "pressure":
                vals.append(float(r["Damage Done"]))
        score.append(float(tot["Score"]))
        print(f"  {os.path.basename(f).split(' - ')[-1][:19]}  score {float(tot['Score']):.1f}  "
              f"kills {tot['Kills']}  misses {tot['Miss Count']}")
    n = len(runs)
    print(f"  mean score {st.mean(score):.1f}")
    for b in ("cluster", "far", "pressure"):
        med = st.median(iv[b])
        print(f"  {b:8}  kills/run {kills[b] / n:5.1f}  time per kill {med:.3f}s")
    spawned = kills["cluster"] / 3 / n  # each slot cycle: 3 cluster, 1 far, 1 cube
    print(f"  cubes: ~{spawned:.1f} spawned/run, {kills['pressure'] / n:.1f} killed, "
          f"~{spawned - kills['pressure'] / n:.1f} expired")
    if life:
        hit = sorted(life * (1 - v / 4) for v in vals)
        print(f"  cube value: median {st.median(vals):.2f} (quartiles {vals and sorted(vals)[len(vals) // 4]:.2f}"
              f"-{sorted(vals)[3 * len(vals) // 4]:.2f});  hit at {st.median(hit):.2f}s after spawn "
              f"(fastest {hit[0]:.2f}s, slowest {hit[-1]:.2f}s)")
    pps = {b: (1.0 if b == "cluster" else key if b == "far" else st.median(vals)) / st.median(iv[b])
           for b in ("cluster", "far", "pressure")}
    print("  points per second: " + ", ".join(f"{b} {v:.2f}" for b, v in pps.items()))
