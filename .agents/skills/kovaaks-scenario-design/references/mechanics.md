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
  - **Combined values are untested.** We tested one value at a time, so we do not know how the game
    combines two or three values. For this reason, check_scene.py uses the exact box only for brushes that
    use the first value alone. It treats any brush with a second or third value as a sphere around the box.
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
