# Trace track in the browser

A KovaaK's tracking scenario from a drawing, built in the browser: the port of `trace_track.py`. Give it an SVG; the
bot traces every line on a lecture hall's chalkboard, and the page offers the `.sce` to download.

- `src/*.ts`: the builder in TypeScript. `geometry.ts` (lines on the board), `svg.ts` (the browser samples every SVG
  element, so all path commands, arcs and transforms work), `tour.ts` (the shortest tour and its routes),
  `carve.ts` (blocks and the chalk mesh), `hall.ts` (the room), `scenario.ts` (the `.sce` file), `ui.ts` (the page),
  `main.ts` (`window.TraceTrack` and the auto-mount). `template.ts` is generated.
- `make_template.py`: writes `src/template.ts` from `trace_track.base_scenario` (profiles and base map). Rerun after
  changing the scenario settings in `trace_track.py`.
- `build.mjs`: bundles `src` into `dist/trace_track.js` with no dependencies (Node 22.13 or newer strips the types; each
  module keeps its own scope). `node web/build.mjs`
- `test.html`: the test page. `python -m http.server 8765 --directory web`, then open http://localhost:8765/test.html.
- `check.mjs` and `export_shapes.py`: the regression check. `python web/export_shapes.py`, `python world_map.py`, then
  `node web/check.mjs`: the browser builder must lay World Map's tour exactly as the Python one does.

To put it on a page, include the script and mark where the tool goes:

```html
<div data-trace-track></div>
<script src="trace_track.js"></script>
```

Not yet in the browser version: labels (names carved inside shapes).
