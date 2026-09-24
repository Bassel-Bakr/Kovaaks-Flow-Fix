"""Read-only check of Flow Fix Recovery: does a miss slow the next kills, and does the drill change that?

For each run: kill rate, misses, the time for the kill right after a kill that had a miss against the time after a
clean kill, the next 3 kills, and miss contagion (the chance of a miss on the next kill after a miss, against the
base rate). The same numbers for the last 30 cA sixshot runs are the baseline. Expiries are estimated from slot
time: 5 slots x run length = time the killed targets were alive + one lifetime per expired target, so the estimate is a
range over the unknown average alive time at the kill. Runs are grouped by build (the scenario hash in each
stats file), so a change to the scenario never mixes with runs of the old version.

Usage: python stats_recovery.py
"""
import glob
import statistics as st

from stats_basic import STATS, parse, secs

LIFETIME = {"1303a0a4f7be819f09c2e4d48f127391": 1.5,     # until 2026-09-24 00:43
            "6a508a94137b8b9938eeba0df9852ba5": 3.0}     # from 2026-09-24 00:43


def run_stats(f):
    rows, tot = parse(f)
    prev, iv = secs(tot["Challenge Start"]), []
    for r in rows:
        t = secs(r["Timestamp"])
        iv.append(t - prev)
        prev = t
    miss = [int(r["Shots"]) > int(r["Hits"]) for r in rows]
    after_miss = [iv[k + 1] for k in range(len(iv) - 1) if miss[k]]
    after_clean = [iv[k + 1] for k in range(len(iv) - 1) if not miss[k]]
    next3_miss = [st.mean(iv[k + 1:k + 4]) for k in range(len(iv) - 3) if miss[k]]
    next3_clean = [st.mean(iv[k + 1:k + 4]) for k in range(len(iv) - 3) if not miss[k]]
    p_miss = sum(miss) / len(miss)
    after = [miss[k + 1] for k in range(len(miss) - 1) if miss[k]]
    p_after = sum(after) / len(after) if after else float("nan")
    return dict(hash=tot.get("Hash", "?"), score=float(tot["Score"]), kills=len(rows), misses=int(tot["Miss Count"]),
                length=secs(rows[-1]["Timestamp"]) - secs(tot["Challenge Start"]),
                med=st.median(iv), cv=st.pstdev(iv) / st.mean(iv),
                am=st.median(after_miss) if after_miss else float("nan"), ac=st.median(after_clean),
                n3m=st.median(next3_miss) if next3_miss else float("nan"), n3c=st.median(next3_clean),
                p_miss=p_miss, p_after=p_after, n_miss=sum(miss))


def show(label, runs):
    print(f"== {label}: {len(runs)} runs")
    for name, r in runs:
        print(f"  {name}  score {r['score']:6.1f}  kills {r['kills']:3}  misses {r['misses']:3}  "
              f"median {r['med']:.3f}  CV {r['cv']:.2f} | next kill after a miss {r['am']:.3f} vs after clean "
              f"{r['ac']:.3f} (x{r['am'] / r['ac']:.2f}); next 3 {r['n3m']:.3f} vs {r['n3c']:.3f} "
              f"(x{r['n3m'] / r['n3c']:.2f}) | miss after a miss {r['p_after']:.0%} vs base {r['p_miss']:.0%}")
    rs = [r for _, r in runs]
    ratio = st.median(r["am"] / r["ac"] for r in rs)
    ratio3 = st.median(r["n3m"] / r["n3c"] for r in rs)
    contagion = st.median(r["p_after"] / r["p_miss"] for r in rs if r["p_miss"])
    print(f"  median over runs: next kill after a miss x{ratio:.2f}, next 3 x{ratio3:.2f}, "
          f"miss contagion x{contagion:.2f}")
    return rs


rec = [(f.split(" - ")[-1][:19], run_stats(f))
       for f in sorted(glob.glob(f"{STATS}/Flow Fix Recovery - Challenge - *Stats.csv"))]
base = [(f.split(" - ")[-1][:19], run_stats(f))
        for f in sorted(glob.glob(f"{STATS}/cA sixshot - Challenge - *Stats.csv"))[-30:]]
for h in dict.fromkeys(r["hash"] for _, r in rec):
    runs = [(n, r) for n, r in rec if r["hash"] == h]
    life = LIFETIME.get(h)
    show(f"Flow Fix Recovery, build {h[:8]} (lifetime {life or '?'} s)", runs)
    if life:
        for name, r in runs:      # alive time at the kill: somewhere between 0.4 and 0.8 of the lifetime
            lo, hi = ((5 * 60 - r["kills"] * alive * life) / life for alive in (0.8, 0.4))
            print(f"  {name}: about {max(lo, 0):.0f}-{max(hi, 0):.0f} targets expired against {r['kills']} killed")
show("cA sixshot (last 30)", base)
