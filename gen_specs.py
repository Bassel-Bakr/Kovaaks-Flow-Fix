"""Generate specs.json for the flowfix scenario set.

Sizes and distances are relative to cA sixshot dense: target radius 65, grid about
1185 x 1050 map units, MapScale 3.15. Its grid is centred on (y=-30, z=-80), 0.6 deg left of and 1.5 deg below the
crosshair; every Flow Fix spawn area is centred on the crosshair instead (user, 2026-09-24).
"""
import json
from pathlib import Path

SCEN = "C:/Program Files (x86)/Steam/steamapps/common/FPSAimTrainer/FPSAimTrainer/Saved/SaveGames/Scenarios"
BASE = SCEN + "/cA sixshot dense.sce"
POKE_SRC = SCEN + "/VT 1w1ts Advanced Pokeball.sce"
ROT_SRC = SCEN + "/ClickTrack 3t.sce"
BASE_CY, BASE_CZ = -30.0, -80.0   # the centre of cA sixshot dense's grid
# The centre of every spawn area, and so of the window: the crosshair, dead centre (user, 2026-09-24). Until then
# it was the base map's centre, and the whole window sat 0.6 deg left and 1.5 deg low.
CY, CZ = 0.0, 0.0
FAR = "100000.0"


def kv(**kw):
    return [{"key": k, "value": v} for k, v in kw.items()]


def tiles(hy, hz, step, profile, hole=None):
    """Tile a (2*hy) x (2*hz) area around the grid centre with touching volumes.
    hole=(hy2, hz2) leaves the inner rectangle empty (ring layouts)."""
    vols = []
    ny, nz = round(2 * hy / step), round(2 * hz / step)
    assert abs(ny * step - 2 * hy) < 1e-6 and abs(nz * step - 2 * hz) < 1e-6, "area must be a whole number of tiles"
    for i in range(ny):
        for j in range(nz):
            dy = -hy + step * (i + 0.5)
            dz = -hz + step * (j + 0.5)
            if hole and abs(dy) < hole[0] and abs(dz) < hole[1]:
                continue
            # A SpawnVolume of scale 1 spans 200 units (half-extent = scale * 100), confirmed in game on 2026-09-23
            # when targets spawned past the arena frame. So scale = step / 200 makes the tiles touch.
            vols.append({"y": round(CY + dy, 3), "z": round(CZ + dz, 3),
                         "size_y": step / 200, "size_z": step / 200, "permitted_profile": profile})
    return vols


def cluster_tiles(offsets, hy, hz, step, profile):
    """Separate clusters: a (2*hy) x (2*hz) tiled box around each (dy, dz) offset from the grid centre."""
    return [dict(v, y=round(v["y"] + oy, 3), z=round(v["z"] + oz, 3))
            for oy, oz in offsets for v in tiles(hy, hz, step, profile)]


def base_volumes():
    import build
    m = json.loads(build.load(BASE)["map"])
    out = []
    for o in m["objects"]:
        if o.get("name") == "SpawnVolume" and any(p["name"] == "TeamMask" and p["value"] == 2 for p in o["properties"]):
            _, y, z = (float(t) for t in o["location"].split(","))
            _, sy, sz = (float(t) for t in o["scale"].split(","))
            out.append({"y": y - BASE_CY + CY, "z": z - BASE_CZ + CZ, "size_y": sy, "size_z": sz,
                        "permitted_profile": "target"})
    return out


BLACK = "X=0.000 Y=0.000 Z=0.000"


def char(new_name, radius, **extra):
    # Black targets by default; keep the base's ProjBB/MainBB ratio (60/65 radius, 128/130 height).
    extra.setdefault("EnemyBodyColor", BLACK)
    o = kv(MainBBRadius=f"{radius:.1f}", MainBBHeight=f"{2 * radius:.1f}",
           ProjBBRadius=f"{radius * 60 / 65:.1f}", ProjBBHeight=f"{2 * radius * 64 / 65:.1f}", **extra)
    return {"section_type": "Character Profile", "copy_from_file": BASE, "copy_section_name": "target",
            "new_name": new_name, "overrides": o}


def bot(new_name, character):
    return {"section_type": "Bot Profile", "copy_from_file": BASE, "copy_section_name": "target",
            "new_name": new_name, "overrides": kv(CharacterProfile=character)}


def rotation(new_name, names, weights, randomized):
    return {"section_type": "Bot Rotation Profile", "copy_from_file": ROT_SRC, "copy_section_name": "staticRot",
            "new_name": new_name, "overrides": kv(ProfileNames=";".join(names),
                                                  ProfileWeights=";".join(f"{w:.1f}" for w in weights),
                                                  Randomized=randomized, AllowRepeatEntries="true")}


def player(**extra):
    return {"section_type": "Character Profile", "copy_from_file": BASE, "copy_section_name": "Player",
            "new_name": "Player", "overrides": kv(**extra)}


BLOCK_VIEW = dict(BlockSpawnFOV="20.0", BlockSpawnDistance=FAR)
POKE = {"section_type": "Weapon Profile", "copy_from_file": POKE_SRC, "copy_section_name": "Poke-Drill",
        "new_name": "Poke-Drill", "overrides": kv(ADSShoot="", CanAimDownSight="false")}

specs = []


def add(**s):
    s.setdefault("drop_sections", [])
    s.setdefault("sections", [])
    s.setdefault("scenario_overrides", [])
    specs.append(s)


# Spawn areas are capped at about 46 x 26 deg (2026-09-23): the view is centred on the crosshair, so a wider
# area can put one target off screen while aiming at another (checked with check_view.py, 16:9 at 103 FOV).
# Tags: the user asked for their name in them (2026-09-24).
COMMON = dict(SearchTags="Flow Fix, flowfix, Static, Clicking, Bassel, Bakr, Egypt", ScenarioVersion="Initial")
# Timed target in 12: a dark orange cube, so it stands out by shape even when enemy colours are forced.
# A cube of half-width 53 (106 x 106) has the same face-on area as the radius-60 spheres.
AMBER = "X=0.350 Y=0.150 Z=0.000"
CUBE = dict(MainBBType="Cuboid", ProjBBType="Cuboid")

add(id="01", scenario_name="Flow Fix Overflick",
    nodes=["sc-overflick", "sc-too-much-force", "sc-arm-too-tense", "sc-scen-multi-target", "sc-cleaner-landings"],
    description=('Chinese weakness-targeted static flowchart: overflick / too much force (decelerating too '
                 'late).[nl]Trains stopping ON the target instead of flying past it.[nl]Six targets. Your shot fires '
                 '50 ms after you click, where the crosshair is at that moment, so a shot taken while the crosshair is'
                 ' still moving lands past the target.[nl]Use less force: stop on the target, then click. A miss costs'
                 ' half a kill. Click with the mouse button, not a keyboard key.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.5", **COMMON),
    added_bots=["target"] * 6,
    # 50 ms fire delay (added 2026-09-23): the user's runs showed 01 played like plain sixshot, and a miss penalty
    # cannot tell an overshoot miss from an undershoot miss. A delayed shot only scores if the crosshair has stopped.
    sections=[{"section_type": "Weapon Profile", "copy_from_file": BASE, "copy_section_name": "BB Gun",
               "new_name": "BB Gun steady", "overrides": kv(DelayBeforeShot="0.05")},
              player(WeaponProfileNames="BB Gun steady;;;;;;;"),
              char("target", 72, BlockedSpawnRadius="900.0")],
    spawn_volumes=tiles(900, 600, 150, "target"))

add(id="02", scenario_name="Flow Fix Lingering",
    nodes=["sc-overflick", "sc-fluid-transition", "sc-crosshair-lingers", "sc-scen-stabilise-landing",
           "sc-faster-transitions", "sc-preemptive-confirmation"],
    description=('Chinese weakness-targeted static flowchart: crosshair lingers after the flick / fluid '
                 'transitions.[nl]Trains a fast flick, a short stop and moving straight on.[nl]Four targets. Hold '
                 'fire: a target dies after 80 ms of unbroken contact, and any gap heals it fully.[nl]Flick, settle '
                 'for a moment, then go to the next one without lingering. Misses are free.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.0", **COMMON),
    added_bots=["target"] * 4,
    sections=[POKE, player(WeaponProfileNames="Poke-Drill;;;;;;;", **BLOCK_VIEW),
              char("target", 60, MaxHealth="1.8", HealthRegenPerSec="100.0", HealthRegenDelay="0.0",
                   BlockedSpawnRadius="900.0")],
    spawn_volumes=tiles(1000, 600, 200, "target"))

add(id="03", scenario_name="Flow Fix Wide Control",
    nodes=["sc-too-little-control", "sc-arm-too-tense", "sc-scen-wide-small"],
    description=('Chinese weakness-targeted static flowchart: too little control on wide flicks / tense arm, bad micro'
                 ' adjustments.[nl]Trains landing wide flicks under control and correcting before you click.[nl]Four '
                 'small targets spread across the whole wall, never next to your crosshair.[nl]Land, correct, confirm.'
                 ' A miss costs a quarter kill.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.25", **COMMON),
    added_bots=["target"] * 4,
    sections=[player(BlockSpawnFOV="12.0", BlockSpawnDistance=FAR), char("target", 40, BlockedSpawnRadius="1500.0")],
    spawn_volumes=tiles(1300, 700, 200, "target"))

add(id="04", scenario_name="Flow Fix Slow Start",
    nodes=["sc-too-smooth", "sc-dragging-initial-flick", "sc-arm-too-relaxed", "sc-push-flick-speed",
           "sc-scen-pressure-flick", "sc-shortens-deceleration"],
    description=('Chinese weakness-targeted static flowchart: dragging initial flick / arm too relaxed.[nl]Trains '
                 'starting every flick fast instead of easing into it.[nl]Two big targets, never near your crosshair. '
                 'Each is worth 2 points when it appears and drains to 0 over 1 second; you score what is left when '
                 'you hit it.[nl]The faster you get going, the more each kill pays. A miss costs 0.1.'),
    # Score = remaining HP (changed 2026-09-23): kill-count scoring could not tell a fast start from a slow one
    # and left expiries invisible. Now speed is paid directly and hit time shows in the stats (0.1 s steps).
    scenario_overrides=kv(ScoreLossPerMiss="0.1", ScorePerKill="0.0", ScorePerDamage="1.0",
                          EnableOverDamage="false", **COMMON),
    added_bots=["target"] * 2,
    sections=[player(**BLOCK_VIEW),
              char("target", 100, MaxHealth="2.0", HealthRegenPerSec="-2.0", HealthRegenDelay="0.0",
                   BlockedSpawnRadius="1500.0")],
    spawn_volumes=tiles(1300, 700, 200, "target"))

# Committed flick (added 2026-09-23). Found while testing 01's fire delay at 300 ms: the shot fires where the
# crosshair is when it goes off, so the player can click first and then flick. That makes a long delay a
# deadline drill: start the flick fast and be on the target when the shot fires.
add(id="05", scenario_name="Flow Fix Hesitation",
    nodes=["sc-dragging-initial-flick", "sc-push-flick-speed", "sc-preemptive-confirmation", "sc-faster-starts"],
    description=('Chinese weakness-targeted static flowchart: dragging initial flick / pre-emptive hit '
                 'confirmation.[nl]Trains committing to the shot: click as the flick starts instead of aiming first '
                 'and waiting.[nl]One target at a time; it vanishes 0.7 s after it appears. Your shot fires 300 ms '
                 'after you click.[nl]Aiming first and then clicking is too late. Click as you start the flick and be '
                 'on the target when the shot fires. A miss costs half a kill. Use the mouse button.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.5", **COMMON),
    # 1 target that lives 0.7 s (was 3 targets without a lifetime, 2026-09-24). In the user's 6 mouse runs only
    # 7-15% of kills came under 0.55 s: they aimed, clicked and waited out the delay (about 0.62 s per clean kill),
    # and the score rose from fewer misses, not from clicking first. Now aim-then-click (reaction + flick + 0.3 s,
    # about 0.8 s) outlasts the target, while click-first (about 0.55 s) hits it.
    added_bots=["target"],
    sections=[{"section_type": "Weapon Profile", "copy_from_file": BASE, "copy_section_name": "BB Gun",
               "new_name": "BB Gun committed", "overrides": kv(DelayBeforeShot="0.3")},
              player(WeaponProfileNames="BB Gun committed;;;;;;;", BlockSpawnFOV="12.0", BlockSpawnDistance=FAR),
              char("target", 72, BlockedSpawnRadius="900.0", MaxHealth="1.0", HealthRegenPerSec="-1.4286",
                   HealthRegenDelay="0.0")],
    spawn_volumes=tiles(900, 600, 150, "target"))

add(id="06", scenario_name="Flow Fix Early Braking",
    nodes=["sc-decelerating-too-early", "sc-scen-wide-varying", "sc-faster-starts", "sc-better-tension-control"],
    description=('Chinese weakness-targeted static flowchart: decelerating too early (long deceleration).[nl]Trains '
                 'keeping your speed late in the flick and stopping at the end, not halfway.[nl]Two big targets '
                 'anywhere on the wall, so the flicks mix short and very wide.[nl]Keep the speed, then stop. A miss '
                 'costs a quarter kill.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.25", **COMMON),
    # 2 targets (was 3): with 3 there was always a near one, and the user's kill-time spread matched plain sixshot.
    added_bots=["target"] * 2,
    # Spacing 400 (was 1000, 2026-09-24): at 1000 the two targets were always far apart, so every flick was medium to
    # long. The user's 3 runs had a kill-time spread of 0.24-0.31 (sixshot 0.34) and only 10% of kills under 0.35 s
    # (sixshot 37%). Closer spacing allows short flicks between the wide ones.
    sections=[player(BlockSpawnFOV="8.0", BlockSpawnDistance=FAR), char("target", 100, BlockedSpawnRadius="400.0")],
    spawn_volumes=tiles(1250, 750, 250, "target"))

add(id="07", scenario_name="Flow Fix Early Click",
    nodes=["sc-clicking-too-fast", "sc-inconsistent-confirmation", "sc-scen-long-large", "sc-improved-overall-pacing"],
    description=('Chinese weakness-targeted static flowchart: clicking too fast / inconsistent hit '
                 'confirmation.[nl]Trains clicking only once you have landed, with the same rhythm every '
                 'time.[nl]Three large targets far apart, so every flick is long.[nl]A miss costs a whole kill, double'
                 ' taps included. Land, then click.'),
    scenario_overrides=kv(ScoreLossPerMiss="1.0", OvershotProtectionTimer="0.0", **COMMON),
    added_bots=["target"] * 3,
    sections=[player(**BLOCK_VIEW), char("target", 95, BlockedSpawnRadius="2500.0")],
    spawn_volumes=tiles(1250, 750, 250, "target"))

add(id="08", scenario_name="Flow Fix Micro Adjust",
    nodes=["sc-no-micro-adjustments", "sc-scen-long-small", "sc-proper-flicking-motion"],
    description=('Chinese weakness-targeted static flowchart: not doing micro adjustments.[nl]Trains the small '
                 'correction after a long flick.[nl]One small target on an outer ring, always a long flick '
                 'away.[nl]Flick, make the small correction, then click. A miss costs half a kill.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.5", **COMMON),
    added_bots=["target"],
    sections=[player(BlockSpawnFOV="25.0", BlockSpawnDistance=FAR), char("target", 32)],
    spawn_volumes=tiles(1300, 700, 200, "target", hole=(700, 300)))

# Fixed, phase-shifted cycles instead of a random rotation (changed 2026-09-23): every run gets exactly
# 25% big / 50% mid / 25% small, so luck in the size mix no longer moves the score. The player cannot tell
# which slot a target belongs to, so the next size is still unpredictable.
SIZE_CYCLES = {"sizeA": ["big", "mid", "small", "mid"],
               "sizeB": ["mid", "small", "mid", "big"],
               "sizeC": ["small", "mid", "big", "mid"],
               "sizeD": ["mid", "big", "mid", "small"]}
add(id="09", scenario_name="Flow Fix Pacing Drop",
    nodes=["sc-continuous-flicking", "sc-wider-flicks-ruin-pacing", "sc-pacing-keeps-dropping",
           "sc-missing-wider-flicks", "sc-scen-varying-sizes", "sc-improved-pacing-control"],
    description=('Chinese weakness-targeted static flowchart: wider flicks ruin pacing / pacing keeps '
                 'dropping.[nl]Trains keeping a steady pace when target sizes change.[nl]Four targets that respawn as '
                 'big, medium or small (always the same mix) anywhere on the wall. A small target you skip waits for '
                 'you.[nl]Fast on the easy ones, patient on the small ones, never stop. A miss costs a quarter kill.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.25", **COMMON),
    added_bots=[f"{n}.rot" for n in SIZE_CYCLES],
    drop_sections=["Bot Profile|target", "Character Profile|target"],
    sections=[char("big", 100, BlockedSpawnRadius="1200.0"), char("mid", 60, BlockedSpawnRadius="1200.0"),
              # Shrunk 35 -> 30 on 2026-09-23: at 35 the user's small kills were only 5% slower than mid.
              char("small", 30, BlockedSpawnRadius="1200.0"),
              bot("big", "big"), bot("mid", "mid"), bot("small", "small"),
              ] + [rotation(n, c, [1] * len(c), "false") for n, c in SIZE_CYCLES.items()],
    spawn_volumes=tiles(1300, 700, 200, ""))

add(id="10", scenario_name="Flow Fix Pathing",
    nodes=["sc-cluster-approach", "sc-scen-cluster-many", "sc-target-priorities", "sc-improved-fluidity"],
    description=('Chinese weakness-targeted static flowchart: the cluster approach on wide flicks / target '
                 'priorities.[nl]Trains choosing a route: clear a group, then one wide flick to the next.[nl]Thirty '
                 'small targets in four tight clusters near the corners. Killed spots refill after a moment, '
                 'anywhere.[nl]Staying on one side runs dry, so work through all four clusters. A miss costs a quarter'
                 ' kill.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.25", **COMMON),
    # 30 targets of radius 40 (was 14 of radius 45, 2026-09-23): at 14 the user's runs matched plain cA sixshot
    # (score 146-150, 0.36 s per kill). Four clusters (2026-09-24) instead of one even field: in the even field the
    # user's 3 runs still matched sixshot (0.38 s per kill, spread 0.32-0.39), because the next target was always near.
    # Clusters make the route matter: short kills inside a cluster, one wide flick between clusters.
    added_bots=["target"] * 30,
    sections=[char("target", 40, BlockedSpawnRadius="250.0", MinRespawnDelay="0.25", MaxRespawnDelay="0.4")],
    spawn_volumes=cluster_tiles([(-900, -450), (900, -450), (-900, 450), (900, 450)], 200, 150, 100, "target"))

add(id="11", scenario_name="Flow Fix Recovery",
    nodes=["sc-controlled-bursts", "sc-disrupted-pacing", "sc-scen-hard-pressure"],
    description=('Chinese weakness-targeted static flowchart: disrupted pacing / hard pressure.[nl]Trains getting your'
                 ' rhythm back right after a miss instead of slowing down.[nl]Five targets, each gone 3 s after it '
                 'appears. Misses are free.[nl]After a miss, keep going at the same pace.'),
    scenario_overrides=kv(ScoreLossPerMiss="0.0", **COMMON),
    added_bots=["target"] * 5,
    # Lifetime 3 s (was 1.5 s until 2026-09-24). At 1.5 s, 5 slots spawned 3.3 targets/s against the user's
    # 1.5 kills/s: about 60% expired, unseen expiry wasted flicks (6.9% of kills over 1.5 s, 0% in sixshot) and
    # spread was 0.58-0.79 against 0.29, so misses and post-miss slowdowns were partly the mechanic's noise.
    sections=[char("target", 60, HealthRegenPerSec="-0.333", HealthRegenDelay="0.0", BlockedSpawnRadius="900.0")],
    spawn_volumes=tiles(1200, 600, 200, "target"))

# Refill tuned from 607 cA sixshot runs (median 145 = 2.4 kills/s): a median run lasts ~58 s,
# a 161 run ~73 s, and the clock only runs forever above 3.7 kills/s.
add(id="12", scenario_name="Flow Fix Speed Build",
    nodes=["sc-controlled-bursts", "sc-scen-mid-cluster", "sc-active-cluster-farming", "sc-create-clusters"],
    description=('Chinese weakness-targeted static flowchart: controlled bursts / cluster farming.[nl]Trains building '
                 'speed and holding it.[nl]Sixshot dense on a 20 s clock. Every kill adds 0.27 s: at your usual pace a'
                 ' run lasts about a minute, and above 3.7 kills a second it never ends.[nl]The faster you go, the '
                 'longer you play. A miss costs a tenth of a kill.'),
    scenario_overrides=kv(Timelimit="20.0", TimeRefilledByKill="0.27", ScoreLossPerMiss="0.1", **COMMON),
    added_bots=["target"] * 6,
    sections=[char("target", 65)],
    spawn_volumes=base_volumes())

CYCLES = {"mixA": ["cluster", "cluster", "far", "cluster", "pressure"],
          "mixB": ["cluster", "far", "cluster", "pressure", "cluster"],
          "mixC": ["far", "cluster", "pressure", "cluster", "cluster"]}
add(id="13", scenario_name="Flow Fix Check",
    nodes=["sc-flick", "sc-overflick", "sc-too-smooth", "sc-continuous-flicking", "sc-controlled-bursts"],
    description=('All-in-one check for the Chinese weakness-targeted static flowchart: pacing, wide flicks with micro '
                 'adjustments, and fast starts.[nl]Black targets in the middle are worth 1 point. The small black '
                 'target far left or right is worth 1.5; skip it and it waits for you. The dark orange cube is worth '
                 'up to 4, draining to 0 over its 1.5 s life: hit it fast.[nl]Play the other Flow Fix scenarios for '
                 'whichever part scores worst. A miss costs half a point.'),
    # Score = damage dealt, capped at the target's remaining HP (EnableOverDamage off), so HP is the point value.
    scenario_overrides=kv(ScoreLossPerMiss="0.5", ScorePerKill="0.0", ScorePerDamage="1.0",
                          EnableOverDamage="false", **COMMON),
    added_bots=[f"{n}.rot" for n in CYCLES],
    drop_sections=["Bot Profile|target", "Character Profile|target"],
    sections=[char("cluster", 60, BlockedSpawnRadius="600.0"),
              # Worth 1.5: measured 0.64 s per outer kill vs 0.43 s per middle kill (user's runs, 2026-09-23),
              # so points per second match. An ignored outer target waits, so it needs parity, not a premium.
              char("far", 35, MaxHealth="1.5"),
              # Worth its remaining HP: 4 at spawn, draining to 0 over its 1.5 s life (score is per damage).
              # At 1 s the user reached cubes at ~0.8 s (worth ~0.8) and half expired. A skipped cube costs
              # nothing, so it needs a premium: ~1.9 at 0.8 s, ~2.7 at 0.5 s.
              char("pressure", 53, MaxHealth="4.0", HealthRegenPerSec="-2.667", HealthRegenDelay="0.0",
                   EnemyBodyColor=AMBER, **CUBE),
              bot("cluster", "cluster"), bot("far", "far"), bot("pressure", "pressure")]
    + [rotation(n, c, [1] * len(c), "false") for n, c in CYCLES.items()],
    spawn_volumes=tiles(400, 300, 200, "cluster")
    + tiles(900, 700, 200, "pressure", hole=(500, 400))
    + tiles(1300, 700, 200, "far", hole=(900, 700)))

Path("specs.json").write_text(json.dumps(specs, indent=1), encoding="utf-8")
print(len(specs), "specs;", [f"{s['id']}:{len(s['spawn_volumes'])}v" for s in specs])
