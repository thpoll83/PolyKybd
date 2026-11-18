// Export the plate mask the way plate_trace_tool.html does, without a browser window.
//   node export_mask.js TOOL.html SETTINGS.json OUTDIR
// TOOL.html must have the photo embedded (make_trace_tool.py --image). Writes OUTDIR/mask.png.
// Fails when the page reports an error, the settings do not import, or no trace was made
// with the imported values.
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");
(async () => {
  const [tool, settings, outdir] = process.argv.slice(2);
  const b = await chromium.launch();
  const fail = async msg => { console.error(msg); await b.close(); process.exit(1); };
  const p = await b.newPage({ viewport: { width: 1500, height: 1000 }, acceptDownloads: true });
  const errs = [];
  p.on("pageerror", e => errs.push(e.message));
  p.on("dialog", async d => { errs.push("dialog: " + d.message()); await d.dismiss(); });
  await p.goto(pathToFileURL(path.resolve(tool)).href);
  await p.waitForFunction(() => document.getElementById("stats").textContent.includes("px/mm"), null, { timeout: 60000 });
  await p.setInputFiles("#loadSettings", settings);
  const res = await p.waitForFunction(() => window.settingsImport, null, { timeout: 60000 })
    .then(h => h.jsonValue()).catch(() => null);
  if (!res) return fail("the page did not report the settings import");
  if (!res.ok) return fail("settings import failed: " + res.error);
  if (errs.length) return fail("page errors: " + errs.join("; "));
  console.log("coverage", await p.textContent("#cover"));
  console.log(await p.textContent("#stats"));
  const [d] = await Promise.all([p.waitForEvent("download"), p.click("#dlMask")]);
  await d.saveAs(path.join(outdir, "mask.png"));
  if (errs.length) return fail("page errors: " + errs.join("; "));
  await b.close();
})();
