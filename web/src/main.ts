// Entry point: window.TraceTrack, and every element with data-trace-track gets the tool.
import { mount } from "./ui.ts";
import { buildFromSvg, buildTrack, DEFAULTS } from "./scenario.ts";

(window as any).TraceTrack = { mount, buildFromSvg, buildTrack, DEFAULTS };

function autoMount(): void {
  document.querySelectorAll<HTMLElement>("[data-trace-track]").forEach((el) => mount(el));
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", autoMount);
else autoMount();
