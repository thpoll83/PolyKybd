// Export the plate mask the way plate_trace_tool.html does, without a browser window.
//   node export_mask.js TOOL.html SETTINGS.json OUTDIR
// TOOL.html must have the photo embedded (make_trace_tool.py --image). Writes OUTDIR/mask.png.
const { chromium } = require("playwright");
(async () => {
  const [tool, settings, outdir] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1500, height: 1000 }, acceptDownloads: true });
  const errs = [];
  p.on("pageerror", e => errs.push(e.message));
  await p.goto("file://" + require("path").resolve(tool));
  await p.waitForFunction(() => document.getElementById("stats").textContent.includes("px/mm"), null, { timeout: 60000 });
  await p.setInputFiles("#loadSettings", settings);
  await p.waitForTimeout(4000);                 // the trace re-runs after the settings load
  console.log("coverage", await p.textContent("#cover"));
  console.log(await p.textContent("#stats"));
  const [d] = await Promise.all([p.waitForEvent("download"), p.click("#dlMask")]);
  await d.saveAs(require("path").join(outdir, "mask.png"));
  await b.close();
  if (errs.length) { console.error(errs); process.exit(1); }
})();
