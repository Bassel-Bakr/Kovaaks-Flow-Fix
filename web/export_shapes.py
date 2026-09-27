"""Write World Map's prepared coasts to test_out/wm_shapes.json for web/check.mjs (run from the repository root)."""
import json
import sys

sys.path.insert(0, ".")
import world_map as W  # noqa: E402
shapes = []
for name, names, labels in W.ORDER:
    loop, *_ = W.continent(name, names)
    shapes.append({"name": name, "points": loop, "closed": True})
json.dump(shapes, open("test_out/wm_shapes.json", "w"))
print(len(shapes), "shapes")
