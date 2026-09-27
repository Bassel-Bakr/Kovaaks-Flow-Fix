// The page: an SVG in, a picture of the board and the tour, a KovaaK's scenario out.
import { type Pt } from "./geometry.ts";
import { buildFromSvg, DEFAULTS, type Result } from "./scenario.ts";

const CSS = `
.tt-root{font:14px/1.45 system-ui,sans-serif;color:inherit;max-width:1100px}
.tt-root h3{margin:.2em 0 .6em;font-size:1.15em}
.tt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.6em 1em;margin:.6em 0}
.tt-root label{display:flex;flex-direction:column;gap:.2em;font-size:.9em}
.tt-root input,.tt-root textarea{font:inherit;padding:.35em .5em;border:1px solid #8888;border-radius:6px;background:transparent;color:inherit}
.tt-root textarea{width:100%;min-height:110px;font-family:ui-monospace,monospace;font-size:12px;box-sizing:border-box}
.tt-row{display:flex;gap:.6em;align-items:center;flex-wrap:wrap;margin:.6em 0}
.tt-root button,.tt-root a.tt-btn{font:inherit;padding:.45em 1em;border-radius:6px;border:1px solid #2e6b4f;background:#2e6b4f;color:#fff;cursor:pointer;text-decoration:none}
.tt-root button[disabled]{opacity:.5;cursor:default}
.tt-root canvas{width:100%;border-radius:8px;display:block;margin:.6em 0;background:#2d5741}
.tt-out{font-size:.9em;margin:.4em 0}
.tt-warn{color:#c77a14}
.tt-err{color:#c0392b}
`;

const SAMPLE = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <path d="M 150 140 C 150 80, 60 80, 60 150 C 60 210, 150 250, 150 290 C 150 250, 240 210, 240 150 C 240 80, 150 80, 150 140 Z"/>
  <circle cx="410" cy="200" r="80"/>
  <rect x="580" y="120" width="160" height="160" rx="30"/>
</svg>`;

export function mount(host: HTMLElement): void {
  if (host.dataset.ttMounted) return;
  host.dataset.ttMounted = "1";
  if (!document.getElementById("tt-style")) {
    const st = document.createElement("style");
    st.id = "tt-style";
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  host.innerHTML = `
  <div class="tt-root">
    <h3>Trace track: a KovaaK's tracking scenario from a drawing</h3>
    <div>Give it an SVG. The bot traces every line of the drawing on a lecture hall's chalkboard, flying a dashed route
    from one line to the next. Download the scenario and put it in KovaaK's Scenarios folder.</div>
    <div class="tt-row"><input type="file" accept=".svg,image/svg+xml" class="tt-file"> <span>or paste the SVG below</span></div>
    <textarea class="tt-svg" spellcheck="false"></textarea>
    <div class="tt-grid">
      <label>Scenario name<input class="tt-name"></label>
      <label>Bot speed (deg/s)<input class="tt-speed" type="number" min="1" max="30" step="0.5"></label>
      <label>Bot radius (deg)<input class="tt-radius" type="number" min="0.1" max="3" step="0.05"></label>
      <label>Search tags<input class="tt-tags"></label>
    </div>
    <label>Description ({tour} becomes the lines in the order the bot visits them)<textarea class="tt-desc" style="min-height:60px"></textarea></label>
    <div class="tt-row"><button class="tt-build">Build</button><a class="tt-btn tt-dl" style="display:none">Download .sce</a><span class="tt-status"></span></div>
    <canvas class="tt-canvas" width="1640" height="840"></canvas>
    <div class="tt-out"></div>
  </div>`;
  const q = <T extends Element>(sel: string) => host.querySelector(sel) as T;
  const svgBox = q<HTMLTextAreaElement>(".tt-svg"), nameBox = q<HTMLInputElement>(".tt-name");
  const speedBox = q<HTMLInputElement>(".tt-speed"), radiusBox = q<HTMLInputElement>(".tt-radius");
  const tagsBox = q<HTMLInputElement>(".tt-tags"), descBox = q<HTMLTextAreaElement>(".tt-desc");
  const btn = q<HTMLButtonElement>(".tt-build"), dl = q<HTMLAnchorElement>(".tt-dl");
  const status = q<HTMLSpanElement>(".tt-status"), out = q<HTMLDivElement>(".tt-out");
  const canvas = q<HTMLCanvasElement>(".tt-canvas");
  svgBox.value = SAMPLE;
  nameBox.value = DEFAULTS.name;
  speedBox.value = String(DEFAULTS.speed);
  radiusBox.value = String(DEFAULTS.rBot);
  tagsBox.value = DEFAULTS.tags;
  descBox.value = DEFAULTS.description;
  q<HTMLInputElement>(".tt-file").addEventListener("change", async (ev) => {
    const file = (ev.target as HTMLInputElement).files?.[0];
    if (file) {
      svgBox.value = await file.text();
      nameBox.value = file.name.replace(/\.svg$/i, "");
    }
  });
  btn.addEventListener("click", () => {
    btn.disabled = true;
    status.textContent = "building…";
    dl.style.display = "none";
    setTimeout(() => {                                 // let the page repaint first: a big drawing takes a while
      try {
        const res = buildFromSvg(svgBox.value, {
          name: nameBox.value.trim() || DEFAULTS.name, description: descBox.value, tags: tagsBox.value,
          speed: +speedBox.value || DEFAULTS.speed, rBot: +radiusBox.value || DEFAULTS.rBot,
        });
        draw(canvas, res);
        const blob = new Blob([res.sce], { type: "text/plain" });
        dl.href = URL.createObjectURL(blob);
        dl.download = `${nameBox.value.trim() || DEFAULTS.name}.sce`;
        dl.style.display = "";
        out.innerHTML = `${res.shapes.length} lines · run ${res.seconds.toFixed(0)} s · ${res.waypoints} waypoints · `
          + `${res.objects} map objects · ${(res.sce.length / 1e6).toFixed(2)} MB`
          + res.warnings.map((w) => `<div class="tt-warn">${escapeHtml(w)}</div>`).join("");
        status.textContent = "";
        (host as any).ttLast = res;
      } catch (e) {
        out.innerHTML = `<div class="tt-err">${escapeHtml(String((e as Error).message || e))}</div>`;
        status.textContent = "";
      } finally {
        btn.disabled = false;
      }
    }, 30);
  });
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
}

function draw(canvas: HTMLCanvasElement, res: Result): void {
  const ctx = canvas.getContext("2d")!;
  const box: Pt = [41, 20], f = 20;
  ctx.fillStyle = "#2d5741";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const P = (p: Pt): Pt => [20 + (p[0] + box[0]) * f, 20 + (box[1] - p[1]) * f];
  ctx.lineCap = ctx.lineJoin = "round";
  ctx.strokeStyle = "#ecece4";
  ctx.lineWidth = 3;
  for (const s of res.shapes) {
    ctx.beginPath();
    s.points.forEach((p, i) => { const [x, y] = P(p); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
    if (s.closed) ctx.closePath();
    ctx.stroke();
  }
  ctx.setLineDash([10, 10]);
  ctx.lineWidth = 2;
  for (const r of res.routes) {
    ctx.beginPath();
    r.forEach((p, i) => { const [x, y] = P(p); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
    ctx.stroke();
  }
  ctx.setLineDash([]);
  const [sx, sy] = P(res.path[0]);
  ctx.fillStyle = "#e0533c";
  ctx.beginPath();
  ctx.arc(sx, sy, 8, 0, 2 * Math.PI);
  ctx.fill();
}
