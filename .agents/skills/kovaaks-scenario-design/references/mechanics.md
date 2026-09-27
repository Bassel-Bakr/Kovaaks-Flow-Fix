# KovaaK's mechanics reference

"Confirmed" means seen working in the user's game or in their stats. "From files" means observed in
installed scenarios but not tested here.

## .sce anatomy

- **Top section:** INI-like `Key=Value` scenario settings. The builder owns `AddedBots`, `BotCharacters`,
  `BotMaxLives`, `BotTeams` and `MapName`.
- **Profile sections:** `[Aim Profile]`, `[Bot Profile]`, `[Bot Rotation Profile]`, `[Character Profile]`,
  `[Dodge Profile]`, `[Weapon Profile]`. A section is identified by its `Name=` line.
- **Map:** `[Map Data]` followed by the map JSON, with `materialSets` and `objects` (brushes and
  gameObjects).
- **Format:** ASCII with CRLF line endings.
- **Bot lists:** `AddedBots` has one entry per bot slot: `name.bot` for a Bot Profile or `name.rot` for a
  Bot Rotation Profile. `BotMaxLives` and `BotTeams` must have one entry per slot. `BotCharacters` is the
  de-duplicated set: all `.bot` names used, then the `.rot` names.
- **Target size and appearance:** set in the Character Profile. `MainBBRadius` and `MainBBHeight`, and
  `MainBBType` (Spheroid, Cylindrical or Cuboid; a Cuboid's radius is its half-width). A target's colour
  is its own profile's `EnemyBodyColor`.

## Mechanics

| Mechanic | Recipe | Status |
| --- | --- | --- |
| **Spawn zones per type** | SpawnVolume `PermittedCharacterProfiles` = Character Profile name; `""` = any | Confirmed |
| **Rotation** | `[Bot Rotation Profile]` with `ProfileNames`, `ProfileWeights`, `Randomized`, `AllowRepeatEntries`. A skipped target waits in its slot | Confirmed |
| **Pokeball dwell** | Weapon "Poke-Drill" (FullyAuto, 0.2 damage every 0.01 s) + target `HealthRegenPerSec=100`. Dwell = MaxHealth / 0.2 × 10 ms. Clear `ADSShoot` | Confirmed (the fewest hits per kill = MaxHealth/0.2) |
| **Timed target** | `MaxHealth=H`, `HealthRegenPerSec=-H/L` for a lifetime of L s. Drains in 0.1 s steps. Expiry scores nothing | Confirmed |
| **HP as score** | `ScorePerKill=0`, `ScorePerDamage=1`, `EnableOverDamage=false`. A kill scores the target's remaining HP. With a timed target, hit time = L × (1 − value/H) | Confirmed |
| **Fire delay** | Weapon `DelayBeforeShot`. The shot fires where the crosshair is when it goes off. 50 ms forces a stop; 300 ms enables click-first-then-flick (a deadline drill). Depends on input: a mouse click freezes the aiming hand, a keyboard key doesn't | Confirmed |
| **Spawn blocking near the crosshair** | Player profile `BlockSpawnFOV` (full angle) + `BlockSpawnDistance` (must be large, e.g. 100000; 0 disables it) | From files, consistent with runs |
| **Spacing between bots** | Character Profile `BlockedSpawnRadius`, in world units (map units × MapScale) | From files |
| **Time bank** | `TimeRefilledByKill` adds seconds per kill. Break-even rate = 1/refill kills per second. Run length = Timelimit / (1 − refill × kill rate), so the score grows faster than the kill rate | Confirmed (Speed Build, 2026-09-23: 143 kills, run 58.3 s against 20 + 143 × 0.27 = 58.6) |
| **Respawn delay** | `MinRespawnDelay` / `MaxRespawnDelay` on the target | Unconfirmed in game |
| **MBS** | Rewards player movement | Not for static drills |
| **Turned bots** | SpawnVolume `rotation` first value (roll) turns each bot it spawns, head included, and turns the volume's box too. Movement (dodge, dash ability `UpVelocity`) stays on the world axes | Confirmed 2026-09-25 |

- **Wall-bounce bots (confirmed 2026-09-25).** A dodge profile's `BlockedMovementPercent` is the share of the bot's
  top speed below which it counts as blocked. After `BlockedMovementReactionMin/Max` it turns. The speed includes
  vertical speed. So a bot that jumps faster than that share of its top speed can slide along a wall mid-jump
  without turning. Pasu Track Extrasmooth TE (0.95, jump 1200 against a top speed of 1000) did. Jumping at 900
  with gravity 0.197 for the same height fixed it. A lower value (0.1) made it ride more. A strafe timer equal to
  the room-crossing time also fixed it with the original jumps: the strafe timer restarts at every turn, wall
  turns included. Details are in
  scenario-types.md.

## Geometry (base room, MapScale 3.15)

- **Positions:** player at x = −6000 map units, spawn plane at x = −2950, wall front face at x = −2900.
  Every angle is independent of MapScale.
- **Base map brushes:** the base map (cA sixshot dense, and every Flow Fix scenario without a look) has
  only 2 brushes. The first is the target wall: one Cube on the group 0 wall slot. Its minimum corner is
  (−2900, −2500, −1250) and its scale is (0.1, 50, 25). So it is 10 units thick, 5000 across and 2500 high.
  From the eye it fills about 37% of the screen, and the rest is sky. Code finds this brush by its
  location, which starts with `-2899.999512`. The Egypt look cuts it down to the window opening and
  repaints it. The second brush is a slab far behind the player, at x = −1,024,000.
- **Player spawn: a SpawnPoint, never a SpawnVolume.** A SpawnVolume spawns the player at a random
  point inside its box, so the view shifts on every reload. The base map (cA sixshot / cA sixshot dense)
  has a player volume of scale 0.317, about ±32 map units (±100 world), and the shift moves the eye sideways,
  up/down and toward the wall. A `"name": "SpawnPoint"` object with the same location and properties
  (TeamMask 1) spawns at one exact position; 292 installed maps use one. `build.py` does this swap
  (`fixed_spawn`, on by default). Confirmed in game on 2026-09-23. Every angle check (check_view,
  check_frame, check_scene, the arena's parallax) assumes the eye at exactly (−6000, 0, 0), so a random
  spawn also makes those checks slightly optimistic.
  - **SpawnPoint format:** a gameObject named "SpawnPoint" with scale 0.25. It has six properties: Name "",
    TeamMask 1, Path "", LoopingPath false, PermittedCharacterProfiles "" and Weight 1. All 292 player
    SpawnPoints in installed maps have this same set of keys. Some also have a rotation (ClickTrack 3t uses
    0, 3, 0). We have not tested what that rotation does.
- **SpawnVolumes:** a SpawnVolume's location is its centre. Its half-extent is scale × 100, so scale 1 spans
  200 units. To tile with step s, use scale s/200. Every target SpawnVolume is 32 map units deep: `build.py`
  writes x scale 0.16, so a volume spans x = −2966 to −2934 around the spawn plane.
  - **The old tile size (fixed 2026-09-22 23:32 UTC, about 02:30 local time on 2026-09-23):** before the
    fix, `gen_specs.py` tiled spawn areas with scale step/100. It assumed that scale 1 spans 100 units. So
    every tile was twice its intended size, and neighbouring tiles overlapped. Each spawn area reached about
    half a tile past its designed edge on every side. The user saw bots spawn outside the designated area,
    some of them on the arena frame. The fix (scale step/200) rebuilt all 13 scenarios. After it, the user
    saw no more spawns on the frame. Runs played before the fix used the larger spawn areas, so do not pool
    them with later runs.
- **Base target grid (cA sixshot dense):** 41 target SpawnVolumes (TeamMask 2, PermittedCharacterProfiles
  "target", Weight 1) on the spawn plane. Each has scale (0.16, 0.9, 0.9), so it is 32 × 180 × 180 map
  units. The grid's middle is y = −30, z = −80. The user made this grid from cA sixshot by moving each
  volume centre 25% closer to the middle. The outermost centres went from 1580 × 1400 apart to 1185 × 1050
  apart. The volumes kept their size, so neighbours now overlap by about 20 to 60 units. One column is
  uneven: some of its volumes sit at y = −345 and others at y = −330. The whole spawn area is
  1365 × 1230 map units (y −712 to 652, z −695 to 535). From the eye it spans 25.2 × 22.8 degrees.
- **Flow Fix spawn areas:** Speed Build still uses the base grid. Every other scenario replaces it with its
  own rectangle, centred on the grid middle. `tiles()` in `gen_specs.py` fills the rectangle with touching
  square SpawnVolumes of scale (0.16, step/200, step/200). The rectangle must be a whole number of tiles. A
  ring layout, such as Micro Adjust, leaves an inner rectangle empty. Current sizes, in map units:
  - Overflick and Hesitation: 1800 × 1200.
  - Lingering: 2000 × 1200.
  - Recovery: 2400 × 1200.
  - Early Braking and Early Click: 2500 × 1500.
  - Wide Control, Slow Start, Pacing Drop, Micro Adjust and Check: 2600 × 1400.
  - Pathing: 1800 × 1000.
  - Speed Build: the base grid, 1365 × 1230. It is the smallest area.

  check_view.py measures 2600 × 1400 as 46.2 × 25.8 degrees, which is the on-screen cap. 2500 × 1500
  measures 44.6 × 27.6 degrees and also passes. Run check_view.py on any new size.
- **Spawn volumes in the editor:** the in-game map editor draws each spawn volume as a see-through orange
  box. So the spawn area shows there as a grid of boxes. The boxes help with placing and do not show
  in play. The editor also measures a selected brush. That is how the user found the arena frame bars too
  thin: 30 units wide and 6 deep, a sliver from the side. The fix made them 90 wide, standing 40 out from
  the wall (`FRAME_WIDTH` and `FRAME_DEPTH` in `arena.py`).
- **Brushes:** location is the minimum corner, scale 1 = 100 units.
  - **Brushes in installed maps:** installed maps hold 5,992 brushes, and 3,598 of them are rotated. The
    brush meshes, from most to least used: Cube (4,446), Cylinder (410), DoubleRamp (228), Cone (163),
    WideCapsule (155), Tube (104), Torus (100), Ramp (79), RampConcave (73), Pipe (50), Concave (44),
    Sphere (36), Pipe180 (30), RampConvex (29), WedgeB (16), Pipe90 (8), NarrowCapsule (6), WedgeA (6),
    QuadPyramid, TruncatedPyramid and QuarterHemisphere (2 each), and HalfRamp, TriPyramid and StairsB
    (1 each). Flow Fix uses only Cube brushes and custom meshes.
  - **Face materials:** a brush's own `materialSets` list holds one entry per face. Six entries is the most
    common count (3,428 brushes), then 0 (861), 4 (787) and 5 (510).
  - **Thin brushes are normal:** 1,044 Cubes have a scale below 0.1 on at least one axis.
  - **Editor groups:** some objects have an optional top-level `"group"` field (196 brushes and 1,207
    gameObjects). It sets the editor group. The highest id in installed maps is 76.
- **Brush rotation** (`"rotation": "a, b, c"` in degrees; calibrated in game on 2026-09-23 with
  `rotation_test.py`). The pivot is the location corner.
  - **a** turns the brush about the x axis (from the player to the wall), i.e. flat within the front wall. Positive is
    clockwise as the player sees it: local +y (screen right) goes to (cos a, −sin a) in (y, z).
  - **b** turns it about the y axis (along a bar lying horizontally on the wall).
  - **c** turns it about the vertical z axis: positive swings the +y end toward the player.
  - **A stroke from P0 to P1 on the front wall** is one Cube: length |P1 − P0| along local y, thickness T
    along local z, and a = atan2(−(z1 − z0), y1 − y0). Anchor it at P0 − (T/2)(sin a, cos a) so it is
    centred on the line.
  - **How it was calibrated:** from one in-game screenshot of `rotation_test.py`, taken with the theme off.
    Four black bars sat in a row above the targets. Each bar was 300 long, 24 tall and 12 deep. Bar 1 had
    no rotation. Bars 2, 3 and 4 turned 30 degrees by the first, second and third value. A blue unrotated
    copy stood behind each bar, and an orange marker showed its anchor corner. Bar 2 tilted clockwise, flat
    on the wall, around the orange corner. Bar 3 looked unchanged, because it turned about its own length.
    The right end of bar 4 swung toward the player, and its shadow showed this. Later, the stroke-built
    signs looked right in game, which confirmed the first value.
  - **Combined values (the Shapes probe, 2026-09-27).** The game applies the first value first, then the second,
    then the third, each about the fixed world axes (Unreal's roll, pitch, yaw order), turning about the anchor
    corner. A positive second value tips the bar's far end (+x, away from the player) up. Eight bars turned 0,
    (30,0,0), (0,30,0), (0,0,30), (30,30,0), (30,0,30), (0,30,30) and (30,30,30) all matched this model within 1.0 to
    1.3 px in a full-size capture, with the part of (30,30,0) that turns into the wall hidden; every other order
    missed that bar by 13 px. `test_out/shapes_rot.py` holds the fit. check_scene.py still treats a brush with a
    second or third value as a sphere round its box; it could now use the exact box.
- **View:** at 103° horizontal FOV on 16:9, the screen shows ±51.5° horizontally and ±35.3° vertically
  around the crosshair.
- **Parallax:** targets float about 50 units in front of the wall, so on the wall plane they appear
  1.0164 times further out.
- **Volume depth and the checks:** the checks (check_view, check_frame, check_scene and the arena parallax)
  treat every target as if it sits exactly on the plane x = −2950. But a volume is 32 units deep. A target
  at the near face of its volume appears 1.022 times further out on the wall plane, not 1.016 times. At
  1300 units from the centre, that is about 7 map units more than the checks assume. check_scene.py also
  treats any object behind x = −2950 plus the largest target radius (in map units) as unable to cover a
  target. This comes from the files; nobody has tested it in game.
- **Units:** target radii (MainBBRadius) and the target SpawnOffset are in world units. Divide them by
  MapScale (3.15) to get map units. The base target spawns 8 world units (about 2.5 map units) above its
  spawn point.
- **Target envelope:** the area where any part of a target can appear, seen from the eye and projected
  onto the wall plane. To get it, take the outer edges of all the scenario's spawn volumes. Move each edge
  outward by the largest target radius in map units, and raise the top and bottom edges by 2.5. Then
  multiply each edge by 1.0164 for parallax. `arena.target_envelope()` computes it.
- **Window opening:** one rectangle sizes the arena panel and frame and the Egypt window opening. It is the
  target envelope plus 60 map units of clear space on every side (`arena.window_bounds()`). The user asked
  for this margin because the black frame could hide black targets. Each scenario has its own spawn
  volumes, so each scenario gets its own opening size. In the Egypt window look, the navy outline band
  rings this opening.

## Checks

Run check_view.py after every build, check_frame.py when the arena is involved, and check_scene.py on
every room look. check_frame.py and check_scene.py exit with code 1 on a failure. check_view.py only
prints its results, so read them.

- **check_view.py (every target on screen):** it tests whether a spawn area can put a target off screen.
  It uses the user's settings: FOV 103 on the horizontal (Overwatch) scale, on a 16:9 screen. It draws
  20,000 random pairs of spawn points, spread evenly inside the spawn volumes. It aims at the first point
  of each pair. It counts the second point as off screen when it lies past 90% of the half-screen. A
  layout passes only when every scenario shows 0.0%.
- **Where the cap of about 46° × 26° comes from:** on 2026-09-23 the user reported that some targets were
  outside their view. The first check then gave these results:

  | Spawn area (degrees) | Pairs with a target off screen |
  | --- | --- |
  | 72.8 × 36.3 | 15.9% |
  | 61.1 × 36.3 | 9.8% |
  | 59.7 × 32.0 | 4.4% |
  | 55.4 × 29.4 | 2.1 to 3.1% |
  | 52.4 × 29.4 | 0.8% |
  | 46.2 × 25.8 | 0.0% |

  The cap comes from the last row.
- **check_frame.py (arena frame):** it checks every corner of every target spawn volume. At each corner it
  takes the largest target allowed in that volume. It projects the target's outer edge from the eye onto
  the wall plane. Then it measures the gap to the inner edge of the frame. A gap below zero means a target
  can overlap the frame on screen, and the check fails.
- **check_scene.py (any decoration):** it projects every brush and prop in front of the targets onto the
  wall plane. It fails if one overlaps the target envelope (see Geometry). Its rules:
  - A prop counts as a 300-unit cube around its pivot, because its real size is unknown.
  - A brush that uses the 2nd or 3rd rotation value counts as a sphere around its box, because only the
    1st value is calibrated.
  - It tests a custom mesh triangle by triangle (see Custom meshes).
  - It skips objects behind the targets, and objects that reach behind the eye (the room shell).

  We proved the check by adding an overlap on purpose, and it caught the overlap. A part that stands out
  from the wall toward the player appears further out on screen, never further in.

## Custom meshes ("procedural" brushes)

- **Format:** `"procedural": [{"indices": [...], "vertices": [{"location": "x, y, z", "normal": "x, y, z"}]}, ...]`,
  one section per material. The brush's `materialSets` needs one entry per section.
- **Divide vertices by MapScale:** the game multiplies custom-mesh vertices by the scenario's MapScale an extra
  time, then applies the brush scale; the location is the vertex origin. In every installed map, a cube's
  vertex size × MapScale = 100 (50 at MapScale 2, 25 at 4, 16.67 at 6, 10 at 10). Found on 2026-09-23: raw
  coordinates drew signs about 3× too big at MapScale 3.15, and halving them (from a MapScale-2 example)
  still left them about 1.5× too big.
- **Winding:** for each triangle (A, B, C), (B - A) x (C - A) points against the face normal. All 8,116
  triangles in installed maps follow this, and so did ours when they rendered correctly.
- **Clip brushes:** installed maps use brushes named "Clip" as invisible collision blocks. A Clip brush has
  no `materialSets` entries, and the game never draws it. So do not copy drawing rules from a Clip brush
  alone. Our first mesh winding came from a Clip mesh. We then checked it against drawn meshes, and it
  matched: the 8,116 installed triangles above all use the same winding.
- **Vertex keys:** installed custom meshes carry either location and normal, or location, normal, tangent
  and uv0, on every vertex. The tangent's 4th value is sometimes true and sometimes false. Every installed
  procedural brush uses mesh "Cube".
- **What loaded in game:** our all-mesh Mesh Test loaded (the user read 640 FPS) with these values:
  - up to 540 vertices and 810 indices in one section, and up to 1040 vertices in one mesh
  - a mesh 5000 map units long, with raw vertex values up to 1587
  - all tangent flags set to false
  - uv0 values from −42 to 25, while installed maps stay within 0 to 1

  Our uv0 is planar and world-aligned, with 1 unit per 100 map units. The in-game editor can open and
  re-save such a map. The user's re-saved copy kept every procedural brush, its group key and its
  `materialSets` unchanged.
- **Use:** one mesh per sign cut the Egypt room from 587 to 150 objects. The FPS rose from 580 to 660,
  against 780 without the room. That saved about 0.21 ms per frame: the room's cost fell from about
  0.44 ms to about 0.23 ms. With `MESH_DECOR` every decoration element is one mesh too (36 objects). Its
  textured stone sections carry `tangent` ("x, y, z, false") and `uv0` keys like installed maps; a review on
  2026-09-24 found the geometry identical to the block build, face for face.
- **Merging small axis-aligned blocks gained little:** merging 122 decoration blocks into 10 meshes took
  the room from 0.25 ms (850 to 700 FPS) to 0.23 ms (750 to 640 FPS), which is within noise. The sign
  merge saved about 0.21 ms, but it removed 437 rotated blocks. (The 0.17 ms under Performance is the
  enclosed-room term of a rough two-point model. It does not measure the merge.) Mesh Test B (2026-09-24)
  kept the big flat pieces as plain blocks. It read the same FPS as the all-mesh version, so a custom mesh
  and a block that cover the same surface cost the same. Rule: merge rotated strokes into meshes. Leave
  axis-aligned decoration as blocks, which stay editable in the map editor. The room's remaining cost of
  about 0.23 ms is not tied to object count.
- **No fixed cost for decoration (probe, 2026-09-24):** Overflick plus one small block read 810 FPS,
  against 820 for plain Overflick in the same session. So the room's cost of about 0.23 ms is spread
  across its pieces. It is not a switch that flips on for any geometry. The walls, floor and ceiling were
  about free: the user's copy without them read the same as the full room.
- **Checking merged meshes:** test each triangle's bounds, not the mesh's. A merged wall has a hole where the
  targets are, so its overall bounds always overlap them (check_scene.py does this).
- **Smooth statues (2026-09-25).** Sculpted meshes with one normal per vertex, shared by neighbouring triangles, load
  and shade smoothly in game: the lions (about 8,000 triangles each) and the pharaoh's bust (about 16,700). A mesh
  of 7,500 triangles in two sections loaded, and so did 13 meshes above 4,000 vertices in one map.
- **Mesh size is file size.** Our builds write mesh data the way the game does: one number per line, deeply
  indented, with every number to 6 decimals. The window look with the stencils was 12 MB per scenario. The first
  build with the sculpts and the round text was 39 MB (about 100,000 vertices), and the user saw a hitch on every
  restart. Triangle count did not hurt the frame rate: that build read 900 FPS or more.
- **Compact mesh text loads (2026-09-25).** The game read, without complaint:
  - mesh data with one vertex per line (`{"location":...,"normal":...,"tangent":...,"uv0":...}`) and 60 indices
    per line;
  - numbers with 4 decimals instead of 6;
  - `-0.0000` values.

  The rest of the map stayed indented. With these (`COMPACT_MESHES` in `build.py`), the same map took 8.7 MB
  instead of 21.9 MB.
- **Faces the fixed eye cannot see (2026-09-25).** In these scenarios the player never moves (MaxSpeed 0, no jump,
  gravity 0), so a face that points away from the eye is never visible. `SLIM_MESHES` in `build.py` leaves those out
  (with a 20-unit margin round the eye) and drops the vertices only they used. In the Sand Test that cut triangles
  from 53,854 to 30,685 and the file from 8.7 MB to 5.2 MB. It loaded, and the user saw nothing missing. Such a
  mesh looks hollow from behind in the map editor.
- **Unused vertices and slivers.** Sections carry only the vertices their triangles use. Triangles under 0.05 square
  units, left by cutting colour boundaries into a mesh, are dropped. They are far below a pixel, and some were
  wound against their smoothed normals.

## Map materials and themes

- **Groups:** the map's top-level `materialSets` holds its material groups. Installed maps have two or
  three entries: 148 have three and 39 have two. None has more than three. Brushes in installed maps use
  only groups 0 and 1. The build that crashed had six entries: the base map's three, then groups 3, 4 and
  5 after the "None" group. Its new brushes used those groups, with materials the base map already uses. The renderer
  crashed after LoadMap (EXCEPTION_ACCESS_VIOLATION reading 0x18; see Crash recovery). The reworked grey
  arena repainted groups 0 and 1 instead, and it loaded without a crash. Nobody has tested a single extra
  group. We also do not know whether the crash comes from the number of entries or from groups after
  "None". So keep `materialSets` at three entries or fewer, and put brushes only on groups 0 and 1.
- **Surface slots:** each group has four slots: wall, ground, ceiling and ramp. The ground slot is the
  floor type that themes repaint. On Cube faces, installed maps use wall most (10,593 faces), then ground
  (5,068) and ceiling (4,113). Ramp is rare (551 faces).
- **Materials:** `Default` pack, e.g. `MI_WA_PureColor`, `MI_WA_grid_8`, `MI_WA_SciFi*`, concrete, marble.
  Each takes the properties Tint (RRGGBBAA), Scale, Roughness, Metallic and FullBright. Our brush tints
  all use alpha ff, so our brushes are fully opaque. There are no light objects; FullBright is the
  lighting. The game still lights brushes, though, and they cast real shadows. In the rotation test, a
  turned bar threw a shadow onto the wall behind it.
- **Base map materials:** the base map has three groups. Group 0 uses MI_WA_PureColor on all four slots,
  in the blue-grey tint aab4be. Its full-bright is about 0.33 on wall, ground and ceiling, and 1.0 on
  ramp. Group 1 holds the SciFi materials: SciFiWallD on wall, SciFiFloorC on ground, SciFiPanelBDark on
  ceiling and SciFiCeilingA on ramp. They are all white, with roughness 0.5, metallic 0.5 and full-bright
  0. Group 2 is "None" on every slot. The target wall uses the group 0 wall slot.
- **Themes:** a player theme replaces materials per surface type (wall, floor, ceiling, ramp). Across the user's 149 themes (2026-09-24), pairs differ this often: wall/ceiling 105, wall/ramp 96, floor/ramp 88, wall/floor 84, floor/ceiling 79, ceiling/ramp 33. 30 themes paint all four alike; with full-bright on, even relief stops shading there. So put the target backdrop on wall type, the frame on ceiling type, and carvings on floor type with a wall-type outline.

## Performance

- **Block count alone does not set the frame rate.** Every brush is drawn separately. At about 600 blocks
  the user lost about 200 FPS against the 2-brush base map. After the room was cut to about 370 blocks, the
  loss stayed the same: 870 to 670 FPS on high settings (2026-09-23). The cost follows what the geometry
  draws on screen, not the number of objects. Rotated stroke blocks cost the most for their size, and big
  surfaces cost more than their count suggests. Plain blocks still cost a little: removing the window
  header (about 44 blocks) gave back about 10 FPS. To save frame time, remove pieces. Merging plain blocks
  into meshes does not help. The busiest installed map has 960 blocks.
- **Keep decorative rooms to a few hundred blocks.** Merge pixels into rectangles (the greedy cover in
  `egypt.py`) and avoid effects that double every shape: a 1-pixel outline doubled every glyph for 6 extra
  themes.
- **Use `"name": "DefaultNoCollision"` for decoration.** It is the same brush without collision; 148 of them
  appear in 40 installed maps.
- **Test FPS against the same scenario without the decoration.** Report block counts with every look change.
- **Measured (2026-09-23):** textures are nearly free (flat colours gained only about 10 FPS). Geometry is the cost: roughly 0.46 microseconds per block plus about 0.17 ms for an enclosed room. From a 780 FPS baseline, a 587-block room gave 580.
- **The user's FPS limit** was 400 on 2026-09-23 (`Max FPS (config): 400`, `Avg FPS` about 402 in every run) and is
  1000 since 2026-09-24 (about 820 average in play with the window look). Read both fields in the stats: a look costs
  nothing in play while the uncapped rate stays well above the limit.
- **Triangles are cheap, objects and rotated blocks are not (2026-09-25).** The sculpted lions added about 15,000
  triangles in 2 objects, and the user read 850 FPS. The whole 2026-09-25 look read 910 FPS on low settings with
  about 30,500 mesh triangles in 51 meshes. Budget objects and file size, not triangles.
- **Compare frame time, not FPS.** The user's baseline drifts between sessions (plain Overflick read 780 on
  2026-09-23 and 850 on 2026-09-24). Convert to milliseconds (1000 / FPS) and compare against a baseline
  measured in the same session. The mesh-sign Egypt room cost 0.23 ms (780 to 660 FPS) and then 0.25 ms (850 to 700 FPS).
- **Big surfaces cost more than their block count suggests.** The user's editor profiling on 2026-09-24 (remove
  one element, read the FPS, around 700): the two room side walls +50 FPS (about 0.09 ms, a third of the room);
  one inscription column (about 11 sign meshes) +10; the ceiling beams and stars (11 blocks) +10; the window
  header (cornice, flutes and winged sun, about 44 blocks) +10. So 44 small blocks cost the same as 3 long beams.
  A later reading contradicted the side-wall figure: removing the whole shell (both side walls, ceiling, floor) gave
  only +20. Single editor readings at about 700 FPS carry roughly ±10 FPS of noise, so trust repeated readings and
  totals over one removal.

## Crash recovery

KovaaK's reopens the last played scenario at startup, so a crashing scenario makes the game crash on
launch. Read `C:\Users\basse\AppData\Local\FPSAimTrainer\Saved\Logs\FPSAimTrainer.log` for the lines
before "Critical error". The "LogTemp: Warning: JSON Object" lines are normal. Then replace the installed
file with a safe build. Test any map-structure change in a separate test scenario first.

- **Where the logs are:** KovaaK's writes its logs to `C:\Users\basse\AppData\Local\FPSAimTrainer\Saved\Logs`,
  not to the Saved folder in the Steam install. At each launch, the game renames the previous log to
  `FPSAimTrainer-backup-YYYY.MM.DD-HH.MM.SS.log`. The time in the name is UTC.
- **Crash folders:** each crash also leaves a folder
  `C:\Users\basse\AppData\Local\FPSAimTrainer\Saved\Crashes\UE4CC-Windows-<id>_0000`. It holds
  CrashContext.runtime-xml, CrashReportClient.ini, a copy of the log (FPSAimTrainer.log) and
  UE4Minidump.dmp.
- **Normal map-loading lines:** while a map loads, the log prints every material slot it reads. Each slot
  gives a "JSON Object" line with the material and its tint, then "Surface Index" and "Surface Slot" lines.
- **What a crash loop looks like:** several logs a few seconds apart, each with one "Critical error".
- **The material-group crash (2026-09-22 UTC):** the game wrote four logs in about 90 seconds, each with
  one crash. The first log was a play session. The other three were launches that crashed at once. In
  each launch, the game loaded the KovaaKSandbox level and then read the map's material slot lines. The last slot lines
  named a material in the new groups (MI_WA_PureColor with tint 1c2024ff). LoadMap finished, and the log
  showed "Reallocating scene render targets". About 0.3 seconds after the material lines, the rendering
  thread crashed. The log showed "Rendering thread exception" and "EXCEPTION_ACCESS_VIOLATION reading
  address 0x0000000000000018". That build had extra material groups (see Map materials and themes).

- **One-round gun (Flow Fix 2, 2026-09-26, unconfirmed).** Weapon `MagazineMax` 1, `AmmoReloadedOnKill` 1,
  `ReloadTimeFromEmpty` 0.35 and `CancelReloadOnKill` true: a kill refills the round, and a miss empties the gun and
  forces the reload, so a miss costs time instead of points. The keys come from 1w2ts reload smallflicks (3 rounds,
  3 back on a kill). Check in the first runs that a hit never triggers a reload.
- **Forced spawns near the crosshair (the Spawns probe, 2026-09-27, OBS).** The KovaaK's wiki says the Player
  profile's `InvertBlockedSpawn` can force bots to spawn inside `BlockSpawnFOV` instead of outside it; VT ww5t
  Intermediate S5 uses it at 40 with `BlockSpawnDistance` 9999. The probe set it to true with FOV 10 on the player,
  and gave three bots that live 1 s one spawn volume 80 x 40 deg. All 48 spawns in 15 s landed near the crosshair,
  but only up and to the right of it: bot centres 0 to 4.9 deg right and 0 to 7.1 deg up (the centre stands 1.6 deg,
  one bot height, above its spawn point), never left of or below the crosshair. So it works, but lopsided: it cannot
  spread targets evenly round the crosshair. The FOV reads as the full angle (5 deg to each side).

- **A target stands on its spawn point (2026-09-26; corrected the same day).** Its centre sits SpawnOffset Z (8 in the
  base) plus its full `MainBBHeight` above the volume position (first read as half the height; the Blast Test's
  target, discs and bars all sat half a height higher than that). A negative SpawnOffset Z of minus the height puts
  the centre on the point, and the bot then spawns where it stands, which kept a ring of spheres from colliding on
  spawn. `build.py` lowers every spawn volume by the offset plus the full height. The 21 scenarios installed on
  2026-09-26 were built with half the height, so they still sit half a target height (0.2-0.4 deg) high until rebuilt.
- **The one-round gun works (confirmed 2026-09-26).** In all 26 Flow Fix 2 runs the stats' `Reloads` equalled
  `Miss Count` exactly: every miss forced the reload, and no hit did.

- **Blast penalty (Flow Fix 2 Blast Test, 2026-09-26, confirmed by the user).** A bot can punish the player for hitting
  it. It carries a Movement Ability with no velocity, `Hurtbox` true, `HurtboxRadius` 15000 (the player is ~9,600 world
  units away), `HurtboxDamage` 10 and knockback 0. The player has `InvinciblePlayer` false (top and profile), a huge
  `MaxHealth` and regen and `DamageKnockbackFactor` 0 (the view never moved), and the top's `ScoreLossPerDamageTaken`
  0.1 makes each blast cost 1 point.
  - **Trigger:** the damage reaction alone never fired it (both `AIUseInCombat` and `AIUseOutOfCombat` false). With
    either on, the bots blasted with nobody shooting, since they see the player. What works: both on, gated by the
    bot's own health (`AIMaxSelfHealth` 99.9, 100 HP healing 5/s), so it may blast only just after a hit.
  - **Teams:** with every bot on team 0 each blast hurt the other bots, which blasted in turn (a chain reaction).
    Team 0 seems to be "no team". Team 2 (`bot_team` in the spec) plus `BlockTeamDamage` true stopped it.
- **No spin-up (2026-09-26).** `DelayBeforeShot` on a full-auto gun (the Poke-Drill at 0.15) does not delay just the
  first bullet: holding the button fires one shot, not a stream (user). The only charge settings (`IsChargeWeapon`,
  `ChargeTimeToCap`) are hold-to-charge projectile shots, so no setting found makes letting go of the button cost time.
- **A Cuboid is as deep as it is wide.** `MainBBHeight` sets its height apart from the half-width, but depth follows
  the half-width, so a wide flat bar is also deep. One that reached into the wall behind never spawned. Moved clear
  of the wall, flat bars (height 33, half-width 218 world) still showed only as small squares, and tall bars (height
  437, half-width 17) sat about 1 deg higher than the half-height rule predicts (user's screenshot). So keep Cuboids
  true cubes (height = 2 x half-width); a closed ring is many small cubes.
- **DisableCharacterCollision can stop other bots spawning (2026-09-26).** With it true on 36-80 ring cubes, the
  target spheres in their middle never spawned or stopped after a few. With the cubes removed, or with it false (the
  cubes half a map unit apart so none overlap), the spheres spawned normally. The user saw no bot limit: other
  scenarios run 100+ bots.
- **A crosshair-blocked spawn waits (2026-09-26).** One target profile on 3 spots with the Player's `BlockSpawnFOV` 10:
  when the random pick was the spot under the crosshair, the target did not try another spot but waited until the
  crosshair moved away. A fixed rotation, one profile per spot, that never repeats a spot avoids it.
- **Overflick disc (Blast Test v17, works, user 2026-09-26).** A hold-fire stream (Poke-Drill) traces the crosshair's
  path, so a penalty object can see an overflick. Recipe:
  - The target (pokeball sphere, 80 ms of contact, worth 2 via `ScorePerKill`) stands 150 map units in front of the
    wall plane, and one big sphere (radius 1.3 deg) stands 25 units in front of the wall behind it, so shots on the
    target hit it first and shots around it hit the disc.
  - The disc blasts (the blast penalty above, -1 point, at most once per 0.5 s) only after about 5 bullets in a row:
    100 HP healing 5/s, blast allowed below 99% (`AIMaxSelfHealth` 99). The stream crossing it on the way in lasts a
    few ms and is free; an overflick turning on it lasts tens of ms and costs a point.
  - One disc per spot, one target profile per spot in a fixed cycle that never repeats a spot, every bot on team 2
    with `BlockTeamDamage`.
  - Rings of small bots failed: bots with collision cannot stand side by side (29 map units apart failed, 59 worked),
    and with `DisableCharacterCollision` the targets stopped spawning. Non-cube Cuboids misbehave (see above).
  - Open: nothing makes holding the button necessary; an overflick with the button up costs only time.
- **Phases and a second weapon (Flow Fix 2 Phase Test, 2026-09-26, confirmed by the user).**
  - **Phases:** a `Teleporter` gameObject under the player's spawn, with `Target` naming a `Waypoint` and
    `TeleportDelay` 5, moved the player to a second room after 5 s (shimcluster uses 15 s for 4 rooms). Room 2 is
    a wall 20,000 units to the side with its own bots; the build only allows volumes in the wall area, so the test
    script adds room 2 to the built map afterwards (`_phase_test.py`).
  - **Weapon swap:** no setting swaps the player's weapon by itself. Bot weapon randomising (`WeaponsProfileNames`,
    `WeaponProfileWeights`, `WeaponSwitchTime`) is a Bot Profile setting, and damage reactions are AI-only.
  - **A second gun on a key works:** the player's `AbilityProfileNames` = `Track.abilwep;;;` names a Weapon Ability
    Profile whose `WeaponProfile` is the tracking beam (LG). Holding the Ability 1 key fires it while mouse 1 stays
    the clicking gun.
  - **Locking the second gun during phase 1 (in test).** `BlockAbilityOnStartDuration` 5 on the player did not stop
    the weapon ability. `ChargesOnSpawn` 0 with `ChargeTimer` 5 killed it for the whole run. The beam weapon's own
    `DelayAfterSpawn` 5 did not either. What works (confirmed 2026-09-26): lock it by range. The beam's
    `MaxHitscanRange` 6000 (world units) cannot reach the clicking targets 9,608 away, and the tracking bot stands
    3,780 away (1,200 map units from the eye), scaled down in size and speed to look the same.
  - **Scoring both phases:** each gun can hit both kinds of target, so score clicks by kill (`ScorePerKill` 1, the BB
    Gun doing 0.001 damage) and tracking by damage. At 1000 damage per shot, BB Gun hits on the tracking bot scored
    1000 each.
- **No auto-fire for the player (2026-09-26).** The weapon's trigger bot (`TriggerBotEnabled` true,
  `TriggerBotFOV` 360, `TriggerBotDelay` 0) did not make the player's gun fire without a click, with `BlockCheats`
  on or off. `BlockCheats` only gates the cheat keys, and the controls list no trigger-bot key: only the Aimbot (X),
  which aims for you. The trigger-bot settings seen on 26 player weapons in installed and Workshop scenarios are
  most likely leftovers; on bots' weapons they work.

## Flying bots, waypoint paths and measuring through OBS (2026-09-27)

- **Up and down for a flying dodge bot.** A flyer's dodge moves it up by jumping and down by crouching:
  `JumpFrequency` above 0 with `AlterateJumpCrouchInput` true, as in Aether Bot 2 and Silo. With `JumpFrequency` 0
  the `ToggleUpDown` timers did nothing (React Track v2: no vertical movement at all). With `CanCrouch` false the
  bot flew up and stayed at the top (v3). Aether and Silo set `CanCrouch` true, with `MaxCrouchSpeed` and
  `CrouchingAcceleration` equal to the normal speed and acceleration (React Track v4 copies this; not played yet).
- **Long waypoint paths load and run.** A SpawnPoint `Path` of 1,034 names (6,879 characters) and a map with 2,257
  waypoints worked (Split Track v2). The longest seen elsewhere is 288 characters and 46 waypoints. A path may list
  the same waypoint more than once.
- **How a bot flies waypoints** (the Wobble Probe, six rounds, measured through OBS). With `WaypointLogic`
  `FollowAimAtWaypoint` and `FlightObeysPitch` true, the bot aims at the next waypoint and flies where it aims.
  - **Each waypoint costs about 0.09 s.** The bot overshoots it a little, steps back, then moves on. With waypoints
    0.4 deg apart at 20 deg/s the bots made only 1-4 deg/s, stepping back about every 0.09 s (the user: "wobbling
    back and forth").
  - **Smooth:** waypoints about 0.125 s of travel apart (2.5 deg at 20 deg/s), acceleration 12 x speed, the Default
    aim profile and VAI 1 Grandmaster TE's dodge profile. Measured: 18.2 of 20 deg/s (91%), speed steady within the
    measurement noise, 0.44 deg spread from a 3.5 deg circle. The spacing is a time: a slower bot keeps the same
    smoothness with waypoints proportionally closer.
  - **The aim profile shows in the path.** The Default aim profile aims with errors (`TrackError` 3.5, `FlickError`
    15, `MaxError` 40, reactions 0.3-0.4 s); with dense waypoints this showed as wobble. An aim profile with every
    error and delay at 0 helped with dense waypoints but jittered with sparse ones. `BlockedMovementPercent` 0 made
    no difference, and `WaypointTurnRate` 1500 made it worse.
  - **No reversals.** Where a path doubles back, the bot overshoots and loops. A drawn path must never cross or touch
    itself; the calligraphy and one-line art tests failed on this, a generated island coast worked "perfectly".
  - **The Waypoints probe (2026-09-27, measured through OBS at 116 frames a second).** Nine flyers with the World
    Map's settings (Default aim, acceleration 12 x speed, `FollowAimAtWaypoint`, turn rate 100,000) flew straight
    24-deg lines at 20 deg/s, one setting changed each:
    - Waypoints 2.5 deg apart (0.125 s of travel) and 6 deg apart: straight and clean, 19.5 and 19.9 deg/s in the
      middle of the line, no back steps.
    - 1 deg apart (0.05 s): half speed (10 deg/s), with a small loop at each waypoint. 0.5 deg apart (0.025 s): the
      bot never gets past, circling one spot in a small loop every 0.4 s. So a waypoint that comes up sooner than
      about 0.1 s after the last one gets overshot and circled back to: that is the "0.09 s per waypoint".
    - Only the two ends (24 deg, 1.2 s apart): the bot strays up to 5 deg off the line and loops, so waypoints can
      also be too far apart. Keep them 0.125 to 0.3 s of travel apart.
    - `WaypointTurnRate` 200 (the common value): loops everywhere, 5.5 deg/s. Paths need a high turn rate.
    - `FollowUntilCombat`: the bot never leaves its spawn point (it sees the player at once).
    - `FollowAimAtTarget`: it follows the line for a few seconds, then drifts toward the player's eye level.
    - A 0.5 s pause at each end (`BotPauseTimeMin/Max`): the bot wobbles on the spot during the pause and loops after
      it.
    - **Waypoint bots ride above their line.** Every clean lane sat 0.21 to 0.23 deg (about 0.45 of the bot's
      radius) above its waypoints; the still bot sat on its design height (0.07 deg low). A carved path shows the
      bot about 0.2 deg high unless its waypoints are lowered by that much.
      Applied to World Map (v10, 2026-09-27): waypoints lowered by 0.45 of the bot's radius (9.27 map units, 0.18 deg).
      Measured through OBS over 25 s (`test_out/wm_offset.py`), the bot ran 0.058 deg above the projected line and the
      chalk itself 0.029 deg above it, so the bot now rides within about 0.03 deg of the chalk.
    - The capture's view was turned 5.9 deg right and 2.8 deg down (the mouse had moved); `test_out/calib_view.py`
      fits the turn from the base wall's corners (0.67 px) and `test_out/waypoint_probe.py` undoes it.
- **The Movement probe (2026-09-27, OBS).** Eight flyers facing the player (an aim profile with no error) strafed left
  and right, 1 s each way at 10 deg/s, one setting changed each:
  - **Flyers ignore `BrakingDeceleration`.** The lane with braking 4 x speed drifted exactly like the reference.
  - **Zero friction lets a strafing flyer spiral in.** With acceleration 2 x speed and `Friction` 0 both bots came
    closer every second (to about 0.57 of their distance in 6 s) and rose out of view. `Friction` 8 kept its bot at
    its distance for the whole 20 s. Instant acceleration (100 x speed) kept its distance while reversing every
    second, but a bot strafing one way without stopping still closed in (28% nearer over 28 deg of travel). A bot
    meant to circle the player at a fixed distance needs friction.
  - **Reversals.** Instant acceleration swung the full 10.4 deg each second. Acceleration 2 x speed with friction 8
    swung only 4.8 deg (90% of top speed 0.38 s after each turn).
  - **A pause between strafes does not stop the bot.** With `StrafeSwapMin/MaxPause` 0.3 the bot coasted through
    the pause (nearly still 6-8% of the time, not 23%), with or without braking, friction and braking friction.
  - **`LeftStrafeTimeMult` counts the bot's own left**, which is the player's right while it faces the player: 2
    made the bot drift right, 0.00001 switched its left strafes off, so it strafed to the player's left without
    stopping (9.3 deg/s). The first strafe goes to the bot's right (`InitialRightMovementState` Right).
- **How each hitbox type is drawn (the Shapes probe, 2026-09-27).** Three still bots, `MainBBRadius` 1.2 deg and
  `MainBBHeight` 6 deg, `MainBBHide` false, measured in a full-size capture:
  - `Spheroid` is a sphere of `MainBBRadius` (2.47 x 2.42 deg); it ignores `MainBBHeight`.
  - `Cylindrical` is a capsule: 2.36 deg wide and 6.00 deg tall, so `MainBBHeight` is the whole height including
    the round ends.
  - `Cuboid` is a box `MainBBHeight` tall and 2 x `MainBBRadius` wide (it looked 2.76 deg wide at 8 deg off centre,
    as a square box seen slightly from the side does).
  - All three centres sat where designed (within 0.6 px, the box 2 px): a bot's centre is its spawn point plus its
    full `MainBBHeight`, whatever the type, even for a sphere that is drawn smaller than that height.
  - **Hits are tested against the same shapes (the Hitbox probe, 2026-09-27, two challenge runs plus OBS).** Bots of
    each type (radius 1.2 deg, `MainBBHeight` 6 deg, `ProjBB` the same) strafed across the still crosshair at 4 deg/s
    (0.04 deg a beam tick of 0.01 s) at set heights, with set health, so a kill meant at least that many ticks inside
    the shape:
    - Spheroid: killed when crossed through the centre; no hits at all when crossed 1.5, 2.7 or 3.45 deg above it.
      A sphere of `MainBBRadius`.
    - Cylindrical: killed at the centre and 2.7 deg above it (health 1); survived 2.7 deg above and below with
      health 50 after about 39 hits each (a capsule gives 40, a cylinder 60); no hits 3.45 deg above; health 45 at
      the centre died (60 ticks). A capsule `MainBBHeight` tall, `MainBBRadius` round.
    - Cuboid: killed at the centre; killed 2.7 deg above it with health 50 (full width up to the top); no hits 3.45
      deg above. A box `MainBBHeight` tall and 2 x `MainBBRadius` wide.
    - Stats notes: a kill row's Hits and Shots count everything since the previous kill, on any bot; the bots
      started about 1 s after the challenge start. `OverShots` was 25 on every kill.
    - One Spheroid bot drifted toward the player during the run, even with friction 8, and passed close by the
      camera; the others kept their distance.
- **Score settings (the score probes, 2026-09-27, challenge runs, LG beam of 0.01 s, 1 damage a tick).** Checked
  against the stats to the decimal:
  - `ScoreMultAccuracy` true multiplies the score by the square root of accuracy (hits / shots): 5 kills x 100 x
    sqrt(50 / 1217) = 101.35, the run's score.
  - `ScoreMultDamageEfficiency` true multiplies by damage done / damage possible: 14 x 100 x 140 / 862 = 227.38.
  - `ScoreMultKillEfficiency` true multiplies by kills / (kills + deaths); with no deaths it changes nothing (11 kills
    scored 1,100).
  - The square root comes from the scenario's own `MultSqrtAcc=true` (set in cA sixshot dense and so in every Flow
    Fix build); installed scenarios without the key multiply by plain accuracy, as far as the survey shows.
  - **`ScorePerTime` pays for the time left when a run ends early** (the Score Time Left probe): with
    `EndChallengeAfterKills` 3 and a 30 s limit, three quick kills ended the run at 2.58 s and it scored 30.42 = 3 kills
    + 27.42 s left. A run that ends at its time limit gets nothing from it (10 s idle scored 0; 20 s of beam scored
    only its damage; 3.8 s of fight time paid nothing). The scenarios that use it end early by kills or `ScoreToWin`.
    `Fight Time` in the stats is the sum of the kill times.
- **The Open Questions probe (2026-09-27, one challenge run at a 60 FPS cap, theme off, OBS).**
  - **Beam ticks at 60 FPS count as at 1000.** A beam ticking every 0.01 s fires about 1.7 times a frame at 60 FPS,
    and the ticks still add up: the capsule crossing took 39 and 41 ticks (39 at 1000 FPS), the box needed its 50.
    `OverShots` read 26-27 (the 0.25 s window rounded to whole frames).
  - **`TargetStrafeOverride`.** Three bots with the same 1.5 s strafe timer moved as one until the player strafed
    (A and D, 2 s each). Then `Ignore` kept its timer, `Mimic` dropped its timer and moved to the same side of the
    screen as the player, and `Oppose` moved to the other side, both switching with each of the player's switches.
    A bot facing the player therefore mirrors the player's keys: player's left is the bot's right.
  - **`DamageReactionChangesDirection` works.** Two bots on the same 4 s timer stayed together until the player
    started tapping them; from then on the reacting bot kept turning away from the control, and the control kept
    its timer. The delay after a hit was not measured: `EnemyBodyColorOnHit` red never showed, so hits were not
    visible in the capture.
  - **`LOSReact` fires while the bot is in the player's sight, not when it hides.** The control swung normally and
    vanished behind a block each swing. `ReturnToSpawn` kept its bot at its spawn point the whole run (it never swung),
    and `LOSReactKillBot` killed its bot 0.4 s after the start, in plain view, before it reached the block.
  - The capture now starts over when the player restarts the scenario (`obs_capture.mjs onstart`), so it always
    holds the last attempt; the first try caught only aborted attempts.
- **Leaderboards (web research, 2026-09-27; not tested).** Only Workshop scenarios have leaderboards (the podium
  button); local scenarios log `LeaderboardId=0`. When an author updates a Workshop scenario, the upload offers
  "Invalidate Old Scores": old scores stay on the server but are hidden or marked with an asterisk (Game Options, LBs),
  and a player's first new score replaces an invalidated one even if it is lower. No source says a changed file
  resets a board by itself, though the stats record a hash (the MD5 of the `.sce` file) with every run. Sources: the
  KovaaK's patch notes on Steam (https://store.steampowered.com/news/posts/?feed=steam_community_announcements&appids=824270&enddate=1559689156)
  and the wiki's Performance Files page (https://wiki.kovaaks.com/home/KovaaK's/PerformanceFiles).
- **Knowing when a run started.** KovaaK's logs every start to
  `%LOCALAPPDATA%\FPSAimTrainer\Saved\Logs\FPSAimTrainer.log` as "Scenario start broadcast: '<name>'", stamped in
  UTC (the user's `D:\Projects\kovaaks-events` tool is built on this). `obs_capture.mjs onstart` waits for that line
  and then captures, so the user starts the probe after "go" and every frame time counts from the start.
- **The player's starting view.** The player SpawnPoint's `rotation` ("roll, pitch, yaw", degrees) sets where the
  player looks at the start (confirmed through OBS). VAI 1 Grandmaster TE uses a pitch of 1.75 there.
- **Teleport chains.** A pad fires when the player moves into it. With player gravity 0 only the pad under the spawn
  fires: a player teleported into the next pad floats inside it and nothing happens (Continents v1 played two of
  five phases). shimcluster's way works: player `Gravity` 10, the landing Waypoint a few units above a thin pad, a
  floor under it, so the player drops into the pad. The player's collision is tiny (the eye ends about 1 unit above
  what it stands on), so the floor must be tiny (1 x 1, its top 1 below the design eye height), the pad 2 x 2 just
  under the eye, and the drop about 3 units; a 300-unit floor filled half the view. A teleport keeps the view
  direction. Chained teleports and bots that wait (a Waypoint pause) drift apart by fractions of a second per phase;
  the user found it too slow and the bot off the crosshair, and one room (the Lecture Hall) replaced them.
- **.sce files are ASCII.** A description with Arabic letters stopped the build (`build.py` writes ASCII). Carved
  text is geometry and can be in any script.
- **Headshot scoring on an all-head bot.** A bot whose head is as big as its body and centred on it
  (`MainBBHasHead` true, head radius 1.03 x body, `MainBBHeadOffset` minus the height, as in the Pokeball scenarios)
  takes the weapon's `HeadshotMultiplier` on every hit: in Split Track the damage beat the hit count by 2 per hit
  on the small bot.
- **Measuring in game through OBS.** `obs_capture.mjs` connects to OBS (obs-websocket 5, settings from KovOBS's
  config, the password never printed) and grabs the KovaaK's game capture; `fast <dir> <seconds>` saves about 100
  JPEG frames a second. Tell the user before capturing, and ask for a still view when positions matter. Small
  scripts then find the bots (the darkest blobs) and the carved lines (darker than the wall around them) in each
  frame. This found the 0.09 s waypoint cost and the World Map bot's hairpin loops.
