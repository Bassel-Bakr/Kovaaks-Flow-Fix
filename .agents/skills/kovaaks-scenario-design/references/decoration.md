# Decorating KovaaK's maps: materials, themes, props, meshes and the Egypt look

This page collects what was learned while building the Flow Fix Egyptian room (September 2026), so it can go into a
wiki later. "Confirmed" means seen in the user's game or stats; "from files" means read from installed scenarios.
Mechanics shared with scenario design (spawn volumes, brush geometry, rotation, custom-mesh format, performance) are
in `mechanics.md`; this page links to them rather than repeating them.

## Materials

- **Material groups.** A map's `materialSets` holds its material groups. Of the user's installed maps, 148 have
  three groups and 39 have two. No installed map has more than three. Each group has four slots, one per surface
  type: `wall`, `ground` (floor), `ceiling`, `ramp`.
  Brushes in installed maps use only groups 0 and 1, so a map has 8 paintable slots. A brush face picks a slot
  with `{"group": g, "surface": s}`.
- **More groups crashed the game.** The first arena build had six groups: the base map's three, then new groups
  3, 4 and 5 after the "None" group. Its materials were ones the base map already uses. The renderer crashed
  after LoadMap (EXCEPTION_ACCESS_VIOLATION reading 0x18). The rebuilt arena repainted groups 0 and 1 instead,
  and it loaded without a crash. Nobody tested a single extra group. We also do not know whether the crash comes
  from the group count or from groups placed after "None". So keep `materialSets` at three groups or fewer, and
  put brushes only on groups 0 and 1. Treat any other group as unsafe. How to recover from a crash is in
  `mechanics.md` ("Crash recovery"). Confirmed.
- **Material entry:** `{"material": "MI_WA_...", "pack": "Default", "properties": [Tint RRGGBBAA, Scale,
  Roughness, Metallic, FullBright]}`. There are no light objects; FullBright is the lighting (0 = lit and shaded,
  1 = flat).
- **Shadows.** Brushes cast real shadows even though a map has no light objects. In the rotation test, a turned
  bar threw a shadow onto the wall behind it (2026-09-23).
- **The base map's materials.** The base map (cA sixshot dense, and every Flow Fix scenario without a look) has
  three groups. Group 0 uses `MI_WA_PureColor` on all four slots, in the blue-grey tint aab4be. Its full-bright
  is about 0.33 on `wall`, `ground` and `ceiling`, and 1.0 on `ramp`. Group 1 holds the SciFi materials:
  SciFiWallD on `wall`, SciFiFloorC on `ground`, SciFiPanelBDark on `ceiling` and SciFiCeilingA on `ramp`. They
  are all white, with roughness 0.5, metallic 0.5 and full-bright 0. Group 2 is "None" on every slot.
- **The base map's target wall.** The base map has only 2 brushes. One is the target wall, in front of which
  the bots spawn. It is one Cube on the group 0 `wall` slot. Its location (minimum corner) is (-2900, -2500,
  -1250), and its scale is (0.1, 50, 25). So it is 10 units thick, 5000 units wide and 2500 units high. The
  other brush is a slab far behind the player, at x = -1,024,000. Code finds the target wall by its location,
  which starts with "-2899.999512". The Egypt window look cuts this brush down to the window opening and
  repaints it.
- **Materials used:** `MI_WA_PureColor` (flat colour), `MI_WA_StoneTilesFacade` (sandstone masonry),
  `MI_WA_BigConcreteTiles`, `MI_WA_ConcretePoured` (limestone), grid and SciFi materials in the base maps.
  Installed maps also use GreyWoodBoard, grid_8, Drywall, WhiteWoodBoard, MarblePolished, BrickGrey, ConcreteTiles,
  BrickClayBeveled on custom meshes. `WA` probably means world-aligned: several installed meshes use textured
  materials without any texture coordinates.
- **Materials in installed maps.** A survey of the user's installed maps counted the material slots that use
  each material:
  - MarblePolished 354, PureColor 197.
  - The four SciFi materials of the base map (SciFiFloorC, SciFiWallD, SciFiPanelBDark and SciFiCeilingA): about
    180 each.
  - grid_8 57, Drywall 44, ConcretePoured 39, ConcreteTiles 25, grid_16 20, WhiteWoodBoard 19, GreyWoodBoard 18,
    BrickClayBeveled 16, grid_32 12, GroundGrass 11.
  - 2 to 7 each: MetalGold, RockSlate, OSB, BrickClayNew, BrickGrey, WoodFloorWalnut, grid_64-2, WoodOak,
    MetalRust, WoodPlank, StoneTilesFacade, BigConcreteTiles, GroundGravel and WoodPine.
  - Once each: groundMoss, Paint, Paint_B, WoodParquet, SciFiPaddingB, MetalSheet and WoodWall.

  Every name starts with `MI_WA_`, and every material is in the Default pack. The one exception is `MI_WA_Door`,
  which is in the Anime pack (2 slots). Every material takes the same five properties: Tint, Scale, Roughness,
  Metallic and FullBright. Unused slots use material "None" in pack "None" and have no properties (644 slots).
- **A tint does not show how light a material looks.** StoneTilesFacade (sandstone masonry) has a light sand
  tint, d9b78a, with full-bright 0.3. In the user's screenshot without a theme, it rendered dark brown. Black
  targets are hard to see on dark brown. So the window look uses limestone (`MI_WA_ConcretePoured`, tint eadbb6)
  for every part that was sandstone. Check every new textured material in game before you use it behind
  targets. Use PureColor where the exact shade matters.
- **Textures are cheap.** Flat colours instead of textures gained only about 10 FPS. The test copy, Egypt Test
  FLAT, had the same blocks as Egypt Test and kept every slot's tint and full-bright value. It only swapped the
  three textured materials (StoneTilesFacade, BigConcreteTiles and ConcretePoured) for PureColor. In one session
  the user measured Overflick at 780 FPS, the textured room at 580 and FLAT at 590.
- **No custom images or materials.** The game reads user images only as crosshairs and user audio only as sounds.
- **Repainting slots per look.** A look may repaint slots it does not otherwise use. The window look repaints
  group 0 `wall` (sandstone, unused there) as the dark sign outline, group 0 `ground` as the lapis headdress, group 1
  `wall` as the light grey backdrop, group 1 `ground` as the navy sign body and group 1 `ramp` as gold. Copy the
  palette before repainting: `m["materialSets"][0] = GROUP0` once aliased the module's palette, so a repaint
  leaked into later builds in the same run.
- **A slot's colour applies to every face that uses the slot.** So list every part that uses a slot before you
  repaint it. For example, the bottom face of the window lining uses group 1 `ramp`. In the full room this slot is
  the pale gold ffe7a8 (see "The room palette" under "History of the look"), so the strip reads as sunlight on the
  window ledge. The window look repaints
  the slot gold (d4a02a) for the pharaoh's face. So the thin strip under the spawn area turned gold too.

## Themes

- A player theme (`SaveGames/Themes/*.json`) replaces the material of every brush face by surface type: it sets
  material, tint, roughness, metallic, full-bright and texture scale for `wall`, `floor`, `ceiling` and `ramp`, plus
  enemy colours and the sky (`solidSkyColor`, `skyColor`). Group does not matter, only surface type.
- **Theme file values.** Surface tints (for example `wallTint`) are x, y and z values from 0 to 1. The sky colour
  (`skyColor`) is r, g, b and a values from 0 to 255. A theme also sets `skyPresetId`, `cloudCoverId` and
  `sunVisible`.
- **The active theme.** KovaaK's stores the name of the active theme in `SaveGames\PrimaryUserSettings.json`,
  under "EStringSettingId::CurrentThemeName". For this user it is "Bassel 3". The Themes folder also holds a file
  named `unsavedThemeChanges.json`. It is probably the theme editor's copy of unsaved changes. It is one of the 149
  themes counted on this page, so the user has 148 saved themes.
- **Material names.** Themes and maps name materials differently. A theme file uses a display name in capitals,
  such as "PURE COLOR", "GRID 8" or "MARBLE POLISHED". A map uses the asset name, such as `MI_WA_PureColor`,
  `MI_WA_grid_8` or `MI_WA_MarblePolished`. The user's theme files use 26 materials: ANIME WOOD WALL, BIANCA
  CARRARA MARBLE TILES, BLACK MARBLE TILES, BRICK CLAY BEVELED, BRICK CLAY NEW, BRICK DARK, BRICK GREY, COBBLESTONE
  ROUGH, CONCRETE BASIC, CONCRETE POURED, CONCRETE TILES, DRYWALL, GREY WOOD BOARD, GRID 16, GRID 64, GRID 8,
  MARBLE POLISHED, METAL SHEET, METAL STEEL, PURE COLOR, SCIFI WALL, WHITE WOOD BOARD, WOOD PARQUET, WOOD PLANK,
  WOOD PLANK CLEAN and WORN MARBLE FLOOR. Some map materials, such as StoneTilesFacade, MetalGold and GroundGrass,
  appear in none of these theme files.
- **Enemy colours.** A theme can override the scenario's enemy colours with the flags `overrideEnemyHeadColor`
  and `overrideEnemyBodyColor`. Its other enemy colour keys include `enemyBodyColorOnLookAt`. The user's usual
  theme, Bassel 3, turns both flags on and sets the head and the body to black (0, 0, 0). So under Bassel 3 every
  target is black, whatever colour the scenario gives it. A target type that must stand out therefore needs a
  different shape as well as a colour.
- **The sky.** Only 24 of the user's 149 themes use a solid sky colour (`solidSkyColor` is true). The other 125
  use a preset sky (`skyPresetId`, `cloudCoverId`), and that sky can show clouds. The user's screenshot of the
  Window Test under a dark granite theme shows this.
- **How often surface types differ** across the user's 149 themes (material differs, or tint luminance differs by
  more than 0.15): wall/ceiling 105, wall/ramp 96, floor/ramp 88, wall/floor 84, floor/ceiling 79, ceiling/ramp 33.
  30 themes paint all four types alike, including the user's own Bassel 2, 3, 6, 7 and Sky. The user's usual theme
  is Bassel 3: MARBLE POLISHED everywhere, metallic 1, roughness 0.93-1, full-bright 0.76-1, solid grey sky.
- **The counts depend on the test.** The first analysis (2026-09-23) counted two surface types as different when
  their material or tint was not exactly equal. With that test, ceiling differed from wall in 124 of 149 themes,
  ramp in 114 and floor in 107. Signs were readable in about 130 themes when ceiling or floor differed. The counts
  on this page use the looser test above. Compare numbers only when they come from the same test. The older 107,
  114, 124 and 130 do not compare with 79, 105 and 117.
- **Rules that follow:** put the target backdrop on `wall` (themes design their wall to contrast with their enemy
  colour), the frame and stone on `ceiling` (differs from wall most often), and carvings on `floor` with a
  `wall`-type outline (signs then differ from ceiling-type stone in 117 of 149 themes, against 79 with the body on
  `ceiling`). `ramp` is almost always like `ceiling` (only 33 differ), so it is a poor contrast type.
- **Other pairings**, counted on ceiling-type stone out of 149 themes. For signs: a floor body with a wall outline
  is readable in 117 themes, a ramp body with a wall outline in 108, a floor body with a ramp outline in 92, a
  ramp body with a floor outline in 92, and a ceiling body with a floor outline in 79. For a frame against the
  backdrop: stone on ceiling against a wall backdrop (or stone on wall against a ceiling backdrop) differs in 105
  themes, stone on ramp in 96 and stone on floor in 84. A floor backdrop behind ceiling stone differs in only 79.
- **How the rules were found in game.** The user's grid theme painted the wall type plain grey. It painted the
  floor, ceiling and ramp types with the same grid. In the first grey Arena Test, neither the frame nor the target
  wall around the panel used the wall type. So both took the same grid, and the frame vanished. The fix put the
  target wall on the wall type and the frame on the ceiling type, and the frame showed again. Later came the user's
  first screenshots of the window look (2026-09-24). Without a theme, the backdrop had the same colour as the
  pilasters, so the window did not read as a window. These screenshots led to two changes. The backdrop got its
  own light tone. The signs moved to the floor type with a wall-type outline.
- **When every type is alike** nothing painted can show. Relief shading helps only below full-bright 1. Under a
  marble theme that paints all four types the same, the window and the signs vanished. Under flat themes that paint
  all four types the same light grey, the arena's frame, panel and room edges all looked alike. No choice of surface
  type can fix that. Depth helps while the theme still shades. Under the user's dark grid theme, an arena frame 40
  units deep read as a solid raised border. Its edges and sides shade, and the grid breaks where it meets the
  frame. Two things escape the surface-type repaint. A theme sets the **sky** separately (the stencil trick below
  uses it), and it does not repaint **props** at all.
- Theme cost: the user's theme cost nothing on plain Overflick (680 with and without) but took the Window Test
  from 616 to 474 (0.15 to 0.64 ms). Whether that is per object or per covered area was not settled; the window was
  cut down to its outline afterwards.

## Props

- Props (`"type": "prop"`) are fixed models. **They keep their own look under themes** (confirmed on the user's
  themes). They also keep their own colours on a white flat theme. The user first said props keep their look under
  the flat theme "unless it's white". The white-theme sampler showed what that means. Light, thin or flat props
  blend into the white walls. Solid, coloured props stay clearly visible, for example Container, TimmyContainer,
  Crate and Barrel.
- **Properties.** The only prop property seen in installed maps is `EnableCollision` (40 of 222). These props
  carry it: CookieFloorGingerbread, Barrel, Column, HellSingleDoorFrame, AnimeTilesStraight, AnimeWoodenPlank and
  CookieFloorSquaredTiles. There is no colour or material setting.
- **"Prop" in the user's words.** The user sometimes says "prop" for any piece of the map, brushes included. On
  2026-09-23 the user asked to "reduce the number of used props overall". The Egypt room was then built from
  blocks, so the request meant fewer blocks. When the user asks about props, check the screenshot or ask which
  pieces they mean before you act.
- **Native size and pivot are unknown**; roughly 600 map units per unit of scale was estimated from a screenshot.
  Use the scales installed maps use as a starting point.
- **Rotation and scale.** Props take any rotation and a non-uniform scale. One installed map (Cata IC Pizz Plz)
  turns a Fence 180 degrees about z, and a Doorway and a Window about 48 degrees about z. Installed maps stretch a
  Banner into a long strip (11.46 x 0.23 x 0.15) and a Column into a thin post (0.0625 x 0.0625 x 0.51). They
  also squash a Barrel flat (0.17 x 0.17 x 0.06).
- **Catalogue** (name: installed scales seen; observed look):
  - Tree (40 uses: 0.44, 0.99), Window (38: 0.24-0.54), Column (22: 0.434, 0.434, 1.095 and smaller),
    CookieFloorSquaredTiles (15), Banner (14: 1.05 x 4.98 x 1.22; 11.46 x 0.23 x 0.15), BannerB (13: 0.5;
    1.0 x 1.79 x 1.48), Crate (13: 0.13-0.2; wood), Barrel (11: 0.17-1.46), Ledge (9: 0.682),
    HellSingleDoorFrame (9: 1.307, 2.386, 0.245), Container (8: 0.09-0.344; teal shipping container, opaque),
    Doorway (4: 0.235-0.34), Signage (4: 0.657-0.866), McCoy (3: 0.312-2.0), Arch (3), AnimeTilesStraight (3),
    AnimeWoodenPlank (3), Fence (2: 0.335), TimmyButton (2: 0.073-0.5), CookieFloorGingerbread (3.93 x 3.94 x 1.41),
    TimmyContainer (0.66; grey box with a black diagonal, opaque), TimmyConsole (0.123), TimmyArrow, JumpPad and
    Teleporter (left out: they may affect gameplay).
  - In the 22-prop sampler on a white flat theme, Container, TimmyContainer, Crate and Barrel looked solid. Most
    others were thin, flat or tiny at the scales used.
- **See-through reports.** The user asked for opaque props, and the Prop Sampler was built so the user could pick
  them. But no prop was ever confirmed to be see-through. The "thin sheet", "too thin" and "see through" reports
  during the frame tests came while the user was looking at the Arena Test, not the Frame Test. The user's editor
  screenshot showed the Arena Test's brush frame bar, which was 30 units wide and 6 units deep. In the Prop Test
  screenshot, Container looked like a solid, chunky teal box. The only thin sheet there was the Banner. Our brush
  materials are fully opaque (alpha ff). The map editor's spawn volume boxes are see-through, but they do not
  show in play (see "The map editor").
- **Samplers:** `prop_test.py` (Prop Test: Column, Banner, Crate and Container above the arena panel, to learn
  whether themes repaint props), `prop_sampler.py` (22 props in two rows), `frame_test.py` (Frame Test: the arena
  frame built from 72 overlapping Containers), `backing_sampler.py` (10 candidates for an always-dark backing plate
  behind the head and lions, 2026-09-24) and `backing_test.py` (one prop, Sandstorm by default, behind the head and
  each lion). The user dropped the backing idea before picking a prop (see "Stencil art").
- **Sandstorm** is a prop too. One installed map (Geometry Dash Lvl 1) uses it at scale 0.032871, 0.0243, 0.001414
  with rotation 0, 90, 0, as a thin plate. The user could not see it in the Backing Test at that scale; it may be
  an effect, or sized for a far background. Earlier prop surveys missed it: that map's file has extra data after
  the map JSON, so `json.loads` fails. Read map JSON with `json.JSONDecoder().raw_decode` so such maps still count. The Container frame was never checked in game,
  because the user asked for the Egyptian look next.

## Brushes

Brush placement (the location is the minimum corner, and scale 1 spans 100 units) is in `mechanics.md`
("Geometry").
This page calls a Cube brush a block.

- **Survey of the installed maps.** They hold 5,992 brushes, and 3,598 of them are rotated. From most to least
  used, the brush meshes are: Cube (4,446), Cylinder (410), DoubleRamp (228), Cone (163), WideCapsule (155), Tube
  (104), Torus (100), Ramp (79), RampConcave (73), Pipe (50), Concave (44), Sphere (36), Pipe180 (30), RampConvex
  (29), WedgeB (16), Pipe90 (8), NarrowCapsule (6), WedgeA (6), QuadPyramid, TruncatedPyramid, QuarterHemisphere
  (2 each), HalfRamp, TriPyramid and StairsB (1 each). Flow Fix uses only Cube brushes and custom meshes.
- **Faces.** A brush's `materialSets` list holds one entry per face. Across all brushes, 6 entries is the most
  common count (3,428). Counts of 0 (861), 4 (787) and 5 (510) are also common. On Cube faces, installed maps use
  the `wall` surface most (10,593 faces), then `ground` (5,068) and `ceiling` (4,113). The `ramp` surface is rare
  (551 faces).
- **Thin brushes are normal.** 1,044 Cubes have a scale below 0.1 on at least one axis.
- **Editor groups.** Some objects have an optional top-level `group` field (196 brushes and 1,207 gameObjects).
  This field sets the editor group. The highest id in the installed maps is 76. The base map uses ids 0 to 5, and
  `egypt.py` starts its own ids at 10. Each sign, the cartouche ring and each decoration section get their own
  group, so they can be selected together in the editor.
- **No collision.** Decoration uses the brush name `DefaultNoCollision`, so the player cannot collide with it.
  Installed maps have 148 such blocks in 40 maps.
- **Clip brushes.** Installed maps use brushes named "Clip" as invisible collision blocks. A Clip brush has no
  `materialSets` entries, and the game never draws it. So do not copy drawing rules from a Clip brush alone.

## Custom meshes

See `mechanics.md` ("Custom meshes"). Key points: sections with `indices` and `vertices` (`location`, `normal`,
optional `tangent` "x, y, z, false" and `uv0` "u, v"); one `materialSets` entry per section; vertices divided by
MapScale; winding (B-A)x(C-A) against the normal; brush name `DefaultNoCollision` and `mesh: "Cube"` as installed
maps use. Our first winding came from a Clip mesh. We then checked it against drawn meshes, and it matched: all
8,116 installed triangles use the same winding.

Merging the rotated sign strokes into meshes saved about 0.21 ms per frame. Egypt Test had 587 blocks and ran at
580 FPS. Mesh Test used one object per sign, 150 objects in all, and ran at 660 FPS. Plain Overflick ran at 780
FPS. So the room's cost fell from about 0.44 ms to about 0.23 ms. (An older figure of 0.17 ms came from a rough
cost model, not from this merge.) Merging axis-aligned blocks saved nothing measurable, and a surface costs the
same as mesh or block. check_scene.py tests each triangle of a mesh.

## Rotation

See `mechanics.md` ("Brush rotation"): the first value turns within the front wall, clockwise as the player sees
it, pivoting at the location corner. Calibrated in game with `rotation_test.py` (retired). The stroke-built signs
later confirmed the first value in game. Only the first value is calibrated for placement, so check_scene.py
treats a brush that uses the second or third value as a sphere around its box.

## The map editor

- **Spawn volumes.** In the in-game map editor, each target spawn volume shows as a see-through orange box. So the
  spawn area (the rectangle where the bots spawn) shows as a grid of boxes. The editor draws them only so you can
  place them. They do not show in play, so they are not see-through objects you need to fix.
- **Measuring.** The editor measures a selected brush. That is how the user found that the arena frame bars were
  too thin. They were 30 units wide and 6 units deep, which looks like a sliver from the side.

## Art pipeline

- **Hieroglyph signs as strokes** (`strokes.py`, `make_inscriptions.py`): render the sign from Segoe UI Historic
  (`C:\Windows\Fonts\seguihis.ttf`), thin it (Zhang-Suen), trace it, simplify it (RDP, EPS 4.0), and carve one
  rotated block per stroke, 6 units wide, with a 2.5-unit dark backing stroke behind it. Every stroke sign in the
  room comes from the font except the water sign, which `strokes.py` draws by hand as a zigzag. Each sign becomes
  one custom mesh (`MESH_SIGNS`) and its own editor group.
- **Text layout.** `strokes.py` renders each sign at a 120-pixel em, and `egypt.py` places it at 1.05 map units
  per pixel. So one em is about 125 units. A text block shrinks in 7% steps until it fits its space. On a
  pilaster, that space is the shaft face less 20 units on each side. On the lintel, it is the space between the
  capitals less 70 units on each side. In the Window Test, the lintel line and the maker line keep full size, and
  the cartouche shrinks to 0.977.
- **The cartouche** is drawn with strokes. It is an 8-stroke ring with cut corners and a tie bar below it. The
  signs of the name stack from top to bottom inside the ring. Each sign and the ring are separate editor groups.
- **Pixel reliefs** (`Scene.relief`): a bitmap of rows, `#` main colour, `o` accent carved 2 units prouder, `.`
  empty; a greedy rectangle cover merges pixels into blocks, and a 1-pixel outline (the shape grown by one pixel)
  sits behind. Blocks = cover('#', '#o') + cover('o', 'o') + cover(grow, '#').
- **Free-standing art** (`standing_relief`): the head and lions stand against the sky as cut-outs. Each is merged
  into one mesh.
- **Stencil art** (`STENCIL_ART`): thin flat plates (6 units, one plane, no outline) so every gap is a hole that
  shows the sky, which themes set separately from surfaces. The plates must be thin: the player sees the head from
  about 24 degrees below, and a 42-unit plate closes 1-pixel slits at that angle. Under a solid-sky theme the
  holes show one flat colour. Under a preset sky (most themes, see "Themes") they show part of that sky. The user
  checked the Stencil Test in game and said it looks good. The user still wanted a black or grey backing behind
  the head and the lions that looks the same under every theme. Themes repaint every brush, so only a prop can
  keep a fixed colour. The Backing Sampler and a Sandstorm Backing Test were built for that, but no prop's colour
  is stored in the map files, so a pick needed the user's eyes. The user then chose to stop at the stencil without
  any prop behind it (2026-09-24). The stencil is now part of the Window Test.
- **Mirrored text** (`LINTEL_MIRROR`): a line carved twice from the centre outward, the left copy mirrored, so every
  sign faces the middle, as on real lintels.
- **Hand art** lives in `egypt_glyphs.json`: hand-drawn pixel signs, the winged sun and frieze tile (both
  retired), and `pharaoh` (44 x 40) and `lion` (58 x 28) from the art workflow (2026-09-24). The pixel signs that
  `make_inscriptions.py` uses are the ankh, djed, was sceptre, vulture, owl, reed, water, mouth and bread. They
  were made for the old pixel build, because the filled font versions turned into look-alike blobs, and the owl
  and the vulture could not be told apart. `make_inscriptions.py` still writes them into the pixel keys of
  `inscriptions.json` ("signs", "cartouche" and "lines"). But `egypt.py` reads only the "strokes" and "text" keys,
  so the room does not use them.
- **The art workflow** (2026-09-24) had two designers draw each piece. A judge then compared the drawings at game
  scale. One art pixel is 7 map units, which is about 1.7 screen pixels at 1080p (103 FOV, about 3100 units away).
  - Lion: the judge chose designer B's drawing. At game size it reads as a maned lion. It has a sloping forehead, a
    blunt muzzle, a standing ear, flame-shaped mane locks, and a raised tail loop with sky showing through it.
    Designer A's round mane looked like a hood or helmet, and A's tail looked like a mace.
  - Pharaoh: the judge merged B's face with A's collar. The merged face is taller than wide and tapers to the
    chin. It has almond eyes, a small nose, ears and a narrower beard. A's face was square, with slit eyes and a
    long bar beard. A's head was installed first. The user then approved the merged head ("yes, swap in the
    merged head").
- **Line art as ribbons** (World Map, 2026-09-27). A round-ended stroke (`ROUND_STROKES`) costs 24 vertices and 22
  triangles per segment, and repeats the points at every joint. The World Map's chalk lines are flat ribbons
  instead: one per coast, dash or letter stroke, two vertices per point shared by the triangles on both sides
  (mitred joins, the mitre capped at twice the half-width), two triangles per segment, 2 units proud of the board.
  At the user's request ("combine triangles so that their coordinates aren't repeated", as in the pharaoh's bust)
  this cut the map's mesh from 31,590 vertices and 28,730 triangles to 3,240 and 2,860, and the file from 6.68 MB
  to 1.37 MB. The old strokes stood 14 units proud; at the board's edges their side walls showed, so the lines
  looked thicker there. Flat chalk keeps one width. The code is `ribbon()` in the scratch script
  `_lecture_hall_test.py`; the Egyptian text still uses round strokes.

## The grey arena (2026-09-23, retired)

Built by `arena.py`, now retired (`"arena": True`). The default look is the window look (`ARENA_DEFAULT = "window"`).

- **Why.** The user asked for it because the target wall floated in a void, had no depth or framing, and looked
  plain and tiring.
- **First version.** A sci-fi room (SciFiCeilingA, SciFiFloorC, SciFiWallD, SciFiPanelBDark). It used three extra
  material groups, and the game crashed on load (see "Materials").
- **The rework** uses only groups 0 and 1 and flat PureColor greys, because the user prefers a grey or dark grey
  look. The ceiling is 26282b, the floor 2e3033, and the side walls and target wall 3a3d41. A mid-grey panel
  (9a9ea3, full-bright 0.35) marks the spawn area. It sits 4 units in front of the wall, so black targets stand out
  against it. A near-black frame (16181b, full-bright 0.1) surrounds the panel. The room is a closed box 5,000
  wide and 2,500 tall. It reaches from behind the player (x = -7100) to the target wall.
- **Frame size.** The frame was first 30 units wide and 6 deep. The user measured it in the editor and found it too
  thin. It is now 90 wide and stands 40 out from the wall (`FRAME_WIDTH` and `FRAME_DEPTH` in `arena.py`).
- **Frame and themes.** See "Themes". The frame vanished under the grid theme until the target wall moved to the
  wall type and the frame to the ceiling type. Flat themes that paint every type alike still hide it.
- **Outcome.** The arena loaded without crashing. After the spawn-volume size fix (see `mechanics.md`,
  "Geometry"), the user confirmed that no target spawns on its frame. But the arena never went into the 13
  scenarios. Some themes hid its frame, so the user moved on to props and then to the Egypt look. Its test
  scenarios (Arena Test, Prop Test and Frame Test) are in `retired/tests/`.

## The Egypt window look (current, 2026-09-24)

Built by `egypt.py` with `WINDOW_ONLY`. `egypt_test.py` builds the test scenarios. Most switches in `egypt.py`
are off by default (`OUTLINES` is on). The Window Test turns on `WINDOW_ONLY`, `WINDOW_HEAD = "top"`, `WINDOW_LIONS`,
`LINTEL_MIRROR`, `STENCIL_ART`, `MESH_SIGNS` and `DARK_TEXT`. All 13 Flow Fix scenarios use this look since 2026-09-24 (the user's request):
`ARENA_DEFAULT = "window"` in `build.py` calls `egypt.add_window`, which applies `egypt.WINDOW_LOOK` (the same
switches) and restores the module's settings afterwards. The installed maps were checked identical to the window
builds that check_scene.py passed.

- **Test scenarios.** `egypt_test.py` builds five look tests into `test_out/`: Flow Fix Egypt Test (the full room),
  Mesh Test (each sign one custom mesh, with navy text), Window Test (this look, with the stencil head
  and lions; the separate Stencil Test was folded into it and retired) and Egypt Test FLAT (flat colours, for an FPS comparison). It also
  builds all 13 layouts in each look into `test_out/egypt_all`, `test_out/egypt_mesh_all` and
  `test_out/egypt_window_all`, so check_scene.py can test every spawn area. `window_mockups.py` builds the head
  placement options and renders them side by side into one image ("window mockups.png"). It installs nothing.
  `backing_sampler.py` builds Flow Fix Backing Sampler: the Stencil Test plus a numbered row of candidate props
  above the gateway.
- **Structure:** the target backdrop is the base map's wall cut to the opening, plain light grey (c8c8c8). Around
  it: a jamb lining, a limestone frame band with a red-ochre torus bead, a sill, two limestone pilasters 190 wide
  set 8 from the frame, and a stepped cavetto cornice. The stone wall only fills the outline between the pilasters,
  from the pilaster bases just under the sill up to the cornice; sky shows everywhere else.
- **Depth.** The window wall is 120 units deep. Its carved face is at x = -3020, and the backdrop is at x = -2900.
  The targets spawn at x = -2950. So the spawn area sits inside the window recess, 50 units in front of the
  backdrop. Seen from the player, any part that stands out from the backdrop shows further out on screen, never
  further in. So once the opening is wider on screen than the spawn area, the lining, frame and sill cannot cover
  a target.
- **The opening.** Each scenario's own spawn volumes set the opening's size. The builder takes the box around all
  the spawn volumes. It grows the box by the largest target radius and raises it by the targets' SpawnOffset Z of 8
  world units. Both values are divided by the MapScale of 3.15 first. It then scales the box by a parallax factor of
  about 1.016, because the targets float in front of the wall. Last, it adds 60 map units of clear space on every
  side (`arena.window_bounds`). The margin is 60 units because at 20 the targets looked like they touched the
  frame. The margin first came from the arena, where the black frame could hide black targets. The full method is
  in `mechanics.md` ("Geometry"). The narrowest opening is about 1550 x 1410 map units (Speed Build). The widest
  is about 2830 x 1610 (Pacing Drop and Slow Start). Heights range from about 1160 (Pathing) to about 1710 (Early
  Braking). Overflick, which the test scenarios use, gets about 2000 x 1390.
- **The backdrop** is the base map's own target wall, one Cube cut down to the window opening. It is plain light
  grey: PureColor c8c8c8 at full-bright 0.4, on the group 1 `wall` slot. It took several steps to get there:
  - In the base map the target wall is a blue-grey PureColor (aab4be).
  - The grey arena used a mid-grey panel (9a9ea3, full-bright 0.35) on the wall type, inside a near-black frame
    (16181b) on the ceiling type.
  - The first Egypt room used a pale window view (PureColor ebe4d2, full-bright 0.55), so black targets stood out.
    The user read this pale panel as "the wall behind the window is missing".
  - It then became textured limestone. The user asked for it plain.
  - It then became plain limestone (PureColor eadbb6, full-bright 0.35). That colour matched the pilasters
    exactly, and the window no longer read as a window.
  - The user then chose plain light grey.

  A dark sandstone backdrop was also considered and dropped, because that stone renders dark brown and black
  targets are hard to see on it. Keep the backdrop plain, light, and a different colour from the stone around it.
- **Outlines:** a navy band (floor type) on the lining's face rings the opening, and a navy line runs round the
  outside of the frame, between it and the pilasters and under the lintel. Before the outlines, the window, frame
  and pilasters merged into one surface under the user's grey theme. The user said they looked "mushed together"
  (2026-09-24). The user asked for outlines "especially the rect where the bots spawn". So the band round the
  opening matters most. It uses the floor type, because floor differs from the wall-type backdrop in 84 of 149
  themes and from the ceiling-type stone in 79. Ramp would differ from the stone in only 33. The band covers the
  lining's face, 16 units wide. The line is 8 units wide and fills the gap between the torus bead and the
  pilasters. Both stand 3 units proud. The outlines are installed, but the user has not checked them in game yet.
- **Text:** the user's welcome line mirrored across the lintel; their full maker line down the left pilaster; the
  name "Bassel Bakr" in a cartouche on the right pilaster. Signs are navy with a dark outline. The signs and
  their meaning are in "The text".
- **Why navy.** Signs are navy (dark blue) rather than black. The targets are black, and black line art beside the
  window could pull the player's eye. Dark blue is also the traditional colour of Egyptian inscriptions. The user
  asked whether dark text could drop the outline. It could not. A theme repaints signs by surface type, so the
  chosen colour does not survive under a theme, and the outline keeps the sign readable. In a sign mesh the
  outline is a second section of the same object, so it costs no extra object. The `DARK_TEXT` switch paints
  group 1 `ceiling` 0f2a4d. That slot holds the signs in the full room, and the window look copies its colour to
  its own sign slot (group 1 `ground`). The switch is off by default, because in the full room that slot also
  paints the ceiling.
- **Art (until 2026-09-25):** a pharaoh's head (golden face, lapis nemes, no uraeus) standing on the cornice in the
  middle; a recumbent lion on a plinth beside each pilaster, facing the window. Both became sculpts on 2026-09-25
  (see "The 2026-09-25 look").
- **Head placement.** The user asked to see the head placements side by side before choosing. So
  `window_mockups.py` rendered three options (`WINDOW_HEAD` in `egypt.py`) in one image:
  - A (`"lintel_split"`): the head sits in the middle of a raised lintel. The welcome line is split beside it, 2
    words on the left and 1 on the right.
  - B (`"top"`): the head stands on the cornice against the sky. The lintel and the welcome line stay as they were.
  - C (`"lintel_alone"`): the head sits alone on a raised lintel. The welcome line moves to the left pilaster. The
    maker line and the cartouche share the right pilaster, so their signs get smaller.

  For A and C, the research proposed a lintel about 320 units tall, with a face about 300 units tall in its
  centre. Each mockup had a lion on a plinth beside each pilaster. The user picked B with the lions. The user then
  asked for golden skin and a blue headdress ("hair"). Each mockup was built from plain blocks and came to about
  303 objects, against 63 before. The head alone was about 100 blocks. After the head and each lion were merged
  into one mesh each, the room came to 68 objects. The mirrored welcome line (9 more sign meshes) and the outlines
  (7 blocks) later brought it to 84 (see "Objects" below).
- **Lions** (`WINDOW_LIONS`). Each lion lies flat in profile, with its belly on the ground line and its head
  raised. The design follows the lion sign E23 and the lions that guard gateways. The head does not turn, because
  a turned head only reads on a statue seen in 3D. The tail rises from the rump, loops up and back, and ends in a
  tuft. A crescent ruff mane frames the face. The art faces right. The left lion uses the art as drawn, and the
  right lion is a mirror copy, so both lions face the window. Each lion lies on a limestone plinth that is 70 units
  tall. The lion starts 40 units out from the outer edge of its pilaster base. The body uses the navy sign colour
  (group 1 `ground`, floor type). The mane uses red ochre (group 0 `ramp`, ramp type).
- **The art under a theme.** Under the user's grey stone theme, the text and the lions read well. The text and the
  lion bodies (floor type) turned black, and the lion manes (ramp type) stayed light. But the pharaoh's head
  became one plain grey shape. Its lapis headdress used the ceiling type, the same as the stone around it. Its gold
  face uses the ramp type, and this theme painted the ramp grey too. (Ramp differs from ceiling in only 33 of the
  user's 149 themes.) So the whole head took one colour, and the face disappeared. The fix moved the headdress to
  the free floor-type slot (group 0 `ground`, lapis 1e4c9a). It costs no extra material group. Without a theme the
  head looks the same. Under a theme the headdress now turns dark like the text and the lion bodies, and the face
  shows against it. The user approved this change.
- **Palette.** Every slot uses roughness 0.9 and metallic 0. The number after each colour is the full-bright value.
  - Group 0 `wall`: PureColor 2b1d12, 0.2. The dark umber outline of the signs, the head and the lions.
  - Group 0 `ground`: PureColor 1e4c9a, 0.35. The lapis-blue headdress of the pharaoh.
  - Group 0 `ceiling`: ConcretePoured eadbb6, 0.35. The limestone. It is the only textured material in this look.
  - Group 0 `ramp`: PureColor 9a3f22, 0.3. The red ochre of the bead, the pilaster binding bands, the lowest
    cornice step and the lion manes.
  - Group 1 `wall`: PureColor c8c8c8, 0.4. The target backdrop.
  - Group 1 `ground`: PureColor 0f2a4d, 0.3. The navy of the sign bodies, the lion bodies, the outline band and
    the outline line.
  - Group 1 `ceiling`: PureColor 0f2a4d, 0.3. `DARK_TEXT` sets this colour. No face in the Window Test uses it.
  - Group 1 `ramp`: PureColor d4a02a, 0.5. The gold of the pharaoh's face and of the strip along the bottom of the
    opening.
- **Removed at the user's request:** the room (walls, floor, ceiling, benches, beams, stars), the dado, the frieze,
  the text columns, the side labels, the winged sun, the cornice flutes, the sandstone.
- **User rules:** no religious or cult symbols (no winged sun, uraeus, gods, ankh, djed, was, Eye of Horus, scarab,
  sphinx). Reproduce the user's hieroglyph text faithfully and never add meaningless signs.
- **Objects:** 84 room objects (43 meshes). The Window Test has 86 brushes in all, 2 of them from the base map.
  The 43 meshes are 40 for the signs and the cartouche ring (the mirrored welcome line counts twice), one for the
  head and one for each lion. The sign outlines are on.

## The palace courtyard (2026-09-24, in all 13 scenarios)

The user asked for the whole map around the window, something fitting for ancient Egypt, inspired by the castle in
thundah's scenarios (not installed locally, so its layout could not be copied). The user picked a palace courtyard
and allowed pyramids as distant landmarks.

- **How it was designed.** A multi-agent design run researched real palace courts (Medinet Habu's palace behind
  its Window of Appearances, the Amarna palaces, Malqata) and how detailed KovaaK's maps build their surroundings.
  Three designers drew concepts with plans and player-view renders: lean (15 objects), atmosphere (10) and
  authentic (19). A judge compared the renders and merged lean with authentic's skyline heights and pool. The renders
  and the full spec are in `docs/courtyard/` (`courtyard designs.png`, `final_view.png`, `final_plan.png`, `workflow_result.json`).
- **What it is.** A paved court at the window's lowest point, a navy pool with a limestone kerb, a dark grey palace
  wall with round "Egyptian merlons", a red palm-column portico with gold capitals on each side, two battered corner
  towers (Medinet Habu's migdol towers, the castle nod) cut off by the screen edge, grey palm stencils (a date palm
  and a doum palm) in the garden behind, and the Giza trio and two Dahshur pyramids on the horizon. Skyline heights
  are absolute, so the skyline sits at the same screen height in every scenario; the floor follows each window.
- **Cost.** 18 objects: 10 blocks and 8 custom meshes, about 2,400 triangles. The user read 875 FPS without a theme
  override and 880 with one on the test scenario (no Overflick reading that session).
- **Palette.** Two slots repainted, as the user approved: group 0 `wall` from dark umber to palace grey 5d6066 (the
  sign outlines turn dark grey too), and the free group 1 `ceiling` to paving grey 77736b. On 2026-09-25 the walls
  turned sandstone and the two slots swapped roles (see "The 2026-09-25 look").
- **Safety.** Nothing stands in front of the targets closer than about 194 wall-plane units outside the envelope;
  every tall piece is at least 26 degrees off-centre; nothing stands behind the head or in front of the lions.
  check_scene.py passes on all 13 scenarios.
- **Code.** `egypt.COURTYARD` (in `WINDOW_LOOK`) calls `courtyard/final_geo.court()` with the window's floor, axis,
  cornice edges and lion plinth edges, and `courtyard/court_export.py` turns the pieces into brushes. The built
  Overflick matches the checked test scenario to within 0.00005 units.
- **The authentic concept** was also built for comparison (`python courtyard_test.py authentic`): a long palace front
  with eight palm columns and doorways, an enclosure wall and the pyramid field, 19 objects and about 6,200
  triangles. The user preferred the judge's pick. The judge had noted that the doorways make the palace look like a
  doll's house and that the concept lacks the castle feel.

## The 2026-09-25 look: sandy walls, sculpts, smooth text (in all 13 scenarios)

The user refined the look one step at a time in a single test scenario, `Flow Fix Sand Test` (Overflick with each
change). They checked it in game and then asked for it in all 13. The earlier builds are in `retired/window look
with stencil art (installed until 2026-09-25)/`, and each Sand Test version is in `retired/tests/`.

- **Sandy walls.** The user asked for "the walls of atmosphere". A render of the atmosphere concept's palace front
  (flat cavetto coping, limestone dado, buttress strips) showed that they meant its colour, not its shape: "No, I
  want the sandy walls". A comparison offered three options: limestone walls, sandstone walls on a grey floor, and
  sandstone walls with a sand floor. The user picked "A floor, C walls": sandstone c9a877 walls on the grey court.
  - All eight slots were taken, so two slots swapped. Group 1 `ceiling` (the paving grey) became sandstone for the
    palace walls, portico roofs and towers.
  - Group 0 `wall` (the palace grey 5d6066) became the paving grey 77736b for the court floor. The palms and the
    sign outlines share that slot, so they turned a slightly lighter grey.
  - Under a theme, the walls now take the ceiling paint, like the window stone, and the floor takes the wall paint.
  - Code: `courtyard/final_geo.py` has `WALL` and `FLOOR`, the slots of the walls and the floor.
- **The window centred on the crosshair.** The user asked for "the player crosshair dead center of the frame". The
  cause was the base map's target grid, centred 0.6° left of and 1.5° below the crosshair, and all 13 scenarios
  inherited it. `gen_specs.py` now centres every spawn area on the crosshair, and the window follows.
- **The pharaoh's head, placement.** The user asked for the head "lowered and moved in front of the stone". Two
  options were rendered:
  - `front_cornice`: in front of the cornice, the chin at the cornice base.
  - `front_lintel`: lowered onto the lintel, with the two welcome lines moved apart to clear it.

  The user tried `front_lintel`. The text gets smaller in five scenarios: Overflick and Hesitation 0.91 to 0.79,
  Lingering 0.98 to 0.85, Pathing 1.05 to 0.91, Speed Build 0.68 to 0.55. The research answer to "where would the
  head go in real life" was:
  - A front-facing head on a gate has no real model.
  - Real gates put a centrepiece on the lintel's centre line: the winged sun (ruled out) or the king's cartouches.
  - The king also appeared in the Window of Appearances itself, or as statues flanking the gate.
- **The lions, facing the player.** Guardian lions face whoever approaches a gate, so the user asked for the lions to
  face the player. Three versions followed:
  1. A front-view stencil drawing. The user rejected it: "I want the same lion from before just rotated. I don't
     want a stencil lion".
  2. The profile art extruded into a block statue, head toward the player, shaped across by part. Seen from the
     player, it read as a blocky mass.
  3. After the user asked about detail ("what if change distance snap size to 2"), a smooth sculpted statue. Snap
     size is an editor setting only; builds write exact coordinates.

  The user said the first sculpt "looks like a dog", because the mane sat too far back. The mane now starts just
  behind the eyes, wraps the cheeks, rises past the ears and runs back over the shoulders.
- **How the sculpts are made** (`sculpt.py`, `make_lion.py`, `make_pharaoh.py`; the JSON files carry the result):
  - Each statue is a signed distance field. Its parts are ellipsoids, tapered capsules and rounded boxes. Parts in
    one group blend with a smooth minimum (radius 16 for the lion's body, 10 to 14 on the bust); groups meet with a
    smaller one, so the mane stays a distinct mass. Small ellipsoids cut the eyes, nostrils and mouth.
  - Naive surface nets turn the field into quads: one vertex per crossed cell, at the mean of its edge crossings.
    The lion uses 9-unit cells, the bust 7.
  - Every vertex takes the field's gradient as its normal, so the statue shades smoothly.
  - Each quad is wound outward by the grid edge it crosses. The smoothed normals are wrong at a few sharp folds.
  - Colour is read at the vertices. A triangle whose vertices differ in colour is cut along the colour boundary,
    found by bisection on its edges, so stripes, collar rings and painted eyes get clean edges. The first bust gave
    each quad one colour, and the user called it "pixelated".
  - Hidden flat faces (the bust's back, the lions' undersides) and slivers under 0.05 square units are dropped.
- **The lion sculpt:** a torso, chest, rump and haunches; folded hind legs and hind paws beside the body; forelegs
  stretched forward with paws; a head, muzzle and chin; two ears; a tail curled up over the rump. The accent group
  (ochre) is a mane ruff behind the face, the mane over the shoulders, ruffs round the cheeks, the chest bib and the
  tail tuft. The right lion is a mirror image, so both tails lean outward. It lies on a limestone plinth that runs
  under it toward the player.
- **The bust:** after Tutankhamun's mask. It has:
  - a golden face, jaw, nose, ears and neck, with lapis eyes, brows and mouth painted as colour regions;
  - a lapis beard with gold braid bands;
  - a nemes (dome, side flaps, lappets) in lapis and gold stripes 14 units high;
  - a broad collar in 15-unit lapis and gold rings.

  There is no cobra. Its back is flat, 100 units in front of the lintel, just clear of the cornice's 96-unit step.
  Its lapis is group 0 `ground` and its gold group 1 `ramp`.
- **Smooth text.** The user asked whether the text could be smoothed like the statues.
  - Every stroke of a sign and of its outline is now a stadium (round ends) in the sign's mesh (`ROUND_STROKES`), so
    strokes meet in round joints. The ends use 2 facets on the 6-unit body strokes and 3 on the 11-unit outline.
  - The traced skeleton is averaged over 5 pixels before simplification (`strokes.SMOOTH`), so curves stay curves.
    `EPS` went from 4 to 1.5, but the user saw that "lines aren't straight". It settled at 3: of the joints that
    bend less than 20° (wobbles in straight lines), 1.5 left 29 and 3 leaves 9. There are 174 strokes, up from 158.
- **Cost and file size.** The Sand Test with every change read 910 FPS on low settings. On the way there:
  - Its file first reached 39 MB and about 100,000 vertices, most of them in the text (one vertex set per
    triangle), and the user saw a hitch on every restart.
  - Shared stroke vertices, compact mesh text and dropping faces the fixed eye cannot see brought it to 5.2 MB,
    30,685 triangles and 31,433 vertices (see mechanics.md, Custom meshes).

  Each scenario is now 104 objects, 51 of them meshes, and about 5 MB.
- **Credits.** Every asset JSON starts with a `"credits"` entry naming the user, from `credits.py`.
- **Screenshots.** `make_screenshots.py` rendered all 13, centred now (`Y_SHIFT` 0). The user's own in-game
  screenshot of Check, which showed the old look, is in `retired/screenshots (installed until 2026-09-25)/`.

## The text

The user reads and writes hieroglyphs and supplied the room's text on 2026-09-23. `make_inscriptions.py` holds it
in `TEXT`, and `inscriptions.json` carries it to the build. The Gardiner codes below come from the Unicode sign
names.

| Meaning | Signs | Gardiner codes | Place |
| --- | --- | --- | --- |
| "Welcome to my humble home" | 𓉐𓏏𓊖 𓎡𓄿𓂋𓇋 𓈖𓎡 | O1 X1 O49, V31 G1 D21 M17, N35 V31 | the lintel, mirrored |
| "This place was made by" | 𓏏𓏭 𓇋𓅓 𓊪𓏏𓏭 𓅓𓄿𓂋𓎡𓄿 | X1 Z4, M17 G17, Q3 X1 Z4, G17 G1 D21 V31 G1 | the left pilaster |
| "Bassel Bakr", spelled by sound | 𓃀𓄿𓋴𓇋𓃭 𓃀𓄿𓎡𓂋 | D58 G1 S29 M17 E23, D58 G1 V31 D21 | a cartouche on the right pilaster |
| "Left side" | 𓂋𓂝 𓎡𓃏𓏏 | D21 D36, V31 D67F X1 | dropped |
| "Right side" | 𓇋𓃀 𓎡𓃏𓏏 | M17 D58, V31 D67F X1 | dropped |

The sign 𓃏 is D67F, a sign of seven dots. The user dropped the "Left side" and "Right side" labels, so the side
walls carry no text.

Two texts from the room version are now retired:
- **The filler.** The room filled spare column space with the ankh, djed and was signs (𓋹𓊽𓌀, S34 R11 S40),
  "life, stability, dominion", a common temple formula. These signs now break the rule against religious symbols.
- **iri.n.** The user asked for one column per side with the text "Made by Bassel Bakr". The right column then held
  𓁹𓈖 (iri.n, D4 N35) above "Bassel Bakr" in a cartouche. Egyptians wrote this formula before a craftsman's name.
  the agent chose iri.n, because the user's own maker line does not mark which signs mean "made by". The window look
  drops iri.n and puts the user's full maker line on the left pilaster instead.

## History of the look

- **The grey arena** (2026-09-23) came first (see "The grey arena"). Some themes hid its frame, so the user tried
  props and then asked for the Egyptian look.
- **The first room** (2026-09-23). The user sent a reference image of a sandstone room with relief figures, a
  bright window onto a desert, and sunlight on the floor. The user asked for the shapes to be carved from geometry,
  in stone materials. The first test room, Flow Fix Egypt Test, had these parts:
  - a window set 120 units deep into a thick wall, with a limestone frame and a red-ochre bead
  - pilasters with papyrus capitals, and a fluted cavetto cornice
  - a winged sun disk with hanging cobras over the window
  - two columns of carved blue hieroglyphs on each side of the window
  - a knotted-reed frieze and a red-ochre dado
  - stone benches, and a blue ceiling with gold stars

  It used 670 blocks.
- **Meaningless signs.** The user then asked what the writing said. It said nothing. The same 16 signs repeated in
  a fixed order down each column, all signs faced the same way, and the cartouches were empty. After this, the
  user supplied real text for the room (see "The text"). This is the origin of the rule never to add meaningless
  signs.
- **The room palette** is still `GROUP0` and `GROUP1` in `egypt.py`. Group 0 holds sandstone (StoneTilesFacade
  d9b78a, full-bright 0.3), floor slabs (BigConcreteTiles c4a171, 0.25), limestone (ConcretePoured eadbb6, 0.35) and
  red ochre (9a3f22, 0.3). Group 1 holds the window view (ebe4d2, 0.55), dark umber (2b1d12, 0.2), Egyptian blue
  (1d4d7a, 0.3) and gold (ffe7a8, 0.85).
- **Fewer blocks.** The user asked for fewer "props", which meant blocks. Cutting the room from about 600 to about
  370 blocks did not change the user's FPS drop, which stayed at about 200. Merging the sign strokes into custom
  meshes then saved about 0.21 ms (see "Custom meshes").
- **The window look** came from the user, in a series of requests on 2026-09-24:
  1. Keep only the "window" part, and move the writing onto the two pilasters.
  2. Make the window tight, with the pilasters close around the spawn area and frame, and no banner behind the
     text.
  3. Keep "just this section" of the stone.
  4. Drop the winged sun disk, and put the welcome text on top instead.
  5. Add a pharaoh's face and two lions at the sides (the user's suggestion).
  6. Use "just non religious or cult symbols", and take real gate and temple entrances as reference.
  7. Shorten the walls, and remove the wall material behind the top writing, so that the top matches the left
     and right sides.
  8. Drop the blue and red cornice strips (the flutes).
- **Other changes that day** are described above: the head mockups, the art workflow and the merged head, the
  mirrored lintel line, the headdress on the floor type, the navy outlines, the light grey backdrop, the Stencil
  Test and the Backing Sampler.
- **Final choice that day:** the stencil head and lions, with no prop behind them, became the Window Test. The
  Stencil Test, Backing Sampler and Backing Test were retired to `retired/tests/`.

## Art research (multi-agent research run, 2026-09-24)

Religious elements (left out) are marked R.

- **Overall advice:** make the window read as a royal palace gateway, not a temple. A palace gateway fits the
  no-religion rule. Real gates also put a large centrepiece on the centre line of the lintel.
- **Gateways:** pylon towers with a lower framed gateway (Luxor, Philae, Karnak); free-standing Ptolemaic propylons
  such as Bab el-Amara, where the zone above the opening is about 48% of its height
  (https://digitalkarnak.ucsc.edu/bab-el-amara-gate/); Merenptah's palace door at Memphis, a wide squat opening
  with a heavy lintel carrying royal names (https://www.penn.museum/sites/journal/897/); the Window of Appearances
  at Medinet Habu. Cavetto cornice with leaf flutes (https://en.wikipedia.org/wiki/Cavetto) and torus moulding
  (https://www.metmuseum.org/art/collection/search/552997). R: winged sun, offering scenes, flagstaffs, obelisks,
  sphinx avenues, smiting scenes.
- **Lintel text** starts at the centre and runs outward, with every sign facing the axis
  (https://www.penn.museum/sites/bulletin/3289/). Jambs carry vertical text columns.
- **Pharaoh:** nemes headcloth and straight royal beard (https://en.wikipedia.org/wiki/Nemes); broad collar;
  idealised face (Tutankhamun's mask, Menkaure, Khafre). R: uraeus cobra, vulture, curled divine beard, the Horus
  falcon, Hathor/Bes-type frontal faces.
- **Lions:** paired recumbent lions flank gateways at ground level (Prudhoe lions,
  https://en.wikipedia.org/wiki/Prudhoe_Lions; Nectanebo's lions at the Louvre and the Vatican; Philae's first
  pylon). R: sphinxes, lion-headed deities, the Aker double lion.
