// Bundle web/src/*.ts into one browser script, web/dist/trace_track.js, with no dependencies: Node's own TypeScript
// type stripping (node:module stripTypeScriptTypes, Node 22.13+), then each module in its own function scope, in
// import order, its exports returned and its imports taken from the modules it names.
//   node web/build.mjs
import { stripTypeScriptTypes } from "node:module";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "src");
const order = [];
const seen = new Set();
const IMPORT = /^import\s+(type\s+)?\{([^}]*)\}\s+from\s+"(\.\/[^"]+)";/gms;

function visit(file) {
  if (seen.has(file)) return;
  seen.add(file);
  const text = readFileSync(file, "utf8");
  for (const m of text.matchAll(IMPORT)) visit(resolve(dirname(file), m[3]));
  order.push(file);
}
visit(join(src, "main.ts"));

const id = (file) => "__" + relative(src, file).replace(/\W/g, "_");
const exportsOf = (file) => [...readFileSync(file, "utf8").matchAll(
  /^export\s+(?:async\s+)?(?:function\*?|const|let|class)\s+([A-Za-z_$][\w$]*)/gm)].map((m) => m[1]);
const parts = order.map((file) => {
  const ts = readFileSync(file, "utf8");
  const exported = [...ts.matchAll(/^export\s+(?:async\s+)?(?:function\*?|const|let|class)\s+([A-Za-z_$][\w$]*)/gm)]
    .map((m) => m[1]);
  const imports = [];
  for (const m of ts.matchAll(IMPORT)) {
    if (m[1]) continue;                                // import type { ... }: types only
    const names = m[2].split(",").map((s) => s.trim()).filter((s) => s && !s.startsWith("type "))
      .map((s) => s.replace(/\s+as\s+/, ": "));
    const target = resolve(dirname(file), m[3]);
    for (const nm of names) {                          // an import must name one of the module's exports
      if (!exportsOf(target).includes(nm.split(":")[0].trim())) throw new Error(`${file}: ${nm} is not exported by ${m[3]}`);
    }
    if (/^export\s+const\s[^;]*,\s*[A-Za-z_$][\w$]*\s*(:[^=;]*)?=/m.test(ts)) {
      throw new Error(`${file}: declare one exported const per statement`);
    }
    if (names.length) imports.push(`const { ${names.join(", ")} } = ${id(resolve(dirname(file), m[3]))};`);
  }
  let js = stripTypeScriptTypes(ts, { mode: "strip" });
  js = js.replace(/^import\s[^;]*?from\s+"[^"]+";[ \t]*$/gms, "");
  js = js.replace(/^export\s+(?=(async\s+)?(function|const|let|class)\b)/gm, "");
  if (/^export\b/m.test(js)) throw new Error(`${file}: an export the bundler does not handle`);
  return `// ---- ${relative(src, file)}\nconst ${id(file)} = (() => {\n${imports.join("\n")}\n${js.trim()}\n`
    + `return { ${exported.join(", ")} };\n})();\n`;
});
const banner = "// trace_track.js: a KovaaK's tracking scenario from a drawing. Built from web/src by web/build.mjs; do not edit.\n"
  + "// Include it and add <div data-trace-track></div> where the tool should appear.\n";
const out = `${banner}(function () {\n"use strict";\n${parts.join("\n")}})();\n`;
mkdirSync(join(here, "dist"), { recursive: true });
writeFileSync(join(here, "dist", "trace_track.js"), out);
console.log(`web/dist/trace_track.js: ${order.length} modules, ${(out.length / 1000).toFixed(0)} kB`);
