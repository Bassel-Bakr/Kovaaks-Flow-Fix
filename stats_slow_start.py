"""Read-only check of Flow Fix Slow Start: what does the score pay for?

Each kill scores the target's remaining HP (HP-as-score, EnableOverDamage off), so the damage on a kill row gives
the target's age at the kill: age = LIFE x (1 - value / MAX_HP), readable in 0.1 s steps. The time since the
previous kill is how long the player took for this one. When age is about that time, the player shot the target
that appeared at the previous kill (the fresh one); when age is about the last two intervals, they shot the
target that was already waiting (the old one). Expiries come from slot time: 2 slots x run length = time the
killed targets were alive + LIFE per expired target. Runs are grouped by build (the scenario hash).

Usage: python stats_slow_start.py
"""
import glob
import statistics as st

from stats_basic import STATS, parse, secs

SLOTS, MAX_HP, LIFE, RUN = 2, 2.0, 1.0, 60.0


def run_stats(f):
    rows, tot = parse(f)
    start = secs(tot["Challenge Start"])
    prev, iv, ages, vals = start, [], [], []
    for r in rows:
        t = secs(r["Timestamp"])
        iv.append(t - prev)
        prev = t
        v = float(r["Damage Done"])
        vals.append(v)
        ages.append(LIFE * (1 - v / MAX_HP))
    length = RUN
    fresh = old = other = 0
    for k in range(1, len(rows)):
        if abs(ages[k] - iv[k]) <= 0.1:
            fresh += 1
        elif abs(ages[k] - iv[k] - iv[k - 1]) <= 0.15:
            old += 1
        else:
            other += 1
    expired = (SLOTS * length - sum(ages)) / LIFE
    return dict(hash=tot.get("Hash", "?"), score=float(tot["Score"]), kills=len(rows),
                misses=int(tot["Miss Count"]), value=st.mean(vals), age=st.median(ages), interval=st.median(iv),
                fresh=fresh / (len(rows) - 1), old=old / (len(rows) - 1), other=other / (len(rows) - 1),
                expired=expired, zero=sum(1 for v in vals if v < 0.05))


runs = [(f.split(" - ")[-1][:19], run_stats(f))
        for f in sorted(glob.glob(f"{STATS}/Flow Fix Slow Start - Challenge - *Stats.csv"))]
for h in dict.fromkeys(r["hash"] for _, r in runs):
    print(f"== Flow Fix Slow Start, build {h[:8]}")
    for name, r in runs:
        if r["hash"] != h:
            continue
        print(f"  {name}  score {r['score']:5.1f}  kills {r['kills']:3}  misses {r['misses']:2}  "
              f"value per kill {r['value']:.2f}  | median time per kill {r['interval']:.3f}  median age at kill "
              f"{r['age']:.2f} s | shot the fresh target {r['fresh']:.0%}, the old one {r['old']:.0%}, "
              f"unclear {r['other']:.0%} | about {r['expired']:.0f} expired, {r['zero']} kills worth 0")
