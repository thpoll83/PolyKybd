// Export the plate mask the way plate_trace_tool.html does, without a browser window.
//   node export_mask.js TOOL.html SETTINGS.json OUTDIR
// TOOL.html must have the photo embedded (make_trace_tool.py --image). Writes OUTDIR/mask.png
// and OUTDIR/res.txt, the px/mm of that mask (the page clamps the resolution to its range).
// Fails when the page reports an error, the settings do not import, no trace was made with
// the imported values, or the download fails.
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");
(async () => {
  const [tool, settings, outdir] = process.argv.slice(2);
  // an empty output folder, so a failed run cannot leave a new mask beside an old res.txt
  if (fs.existsSync(outdir) && fs.readdirSync(outdir).length) {
    console.error(`output folder ${outdir} is not empty`);
    process.exit(1);
  }
  fs.mkdirSync(outdir, { recursive: true });
  const b = await chromium.launch();
  const errs = [];
  let failure = null;
  try {
    const p = await b.newPage({ viewport: { width: 1500, height: 1000 }, acceptDownloads: true });
    p.on("pageerror", e => errs.push(e.message));
    p.on("dialog", async d => { errs.push("dialog: " + d.message()); await d.dismiss(); });
    await p.goto(pathToFileURL(path.resolve(tool)).href);
    await p.waitForFunction(() => document.getElementById("stats").textContent.includes("px/mm"), null, { timeout: 60000 });
    await p.setInputFiles("#loadSettings", settings);
    const res = await p.waitForFunction(() => window.settingsImport, null, { timeout: 60000 })
      .then(h => h.jsonValue()).catch(() => null);
    if (!res) throw new Error("the page did not report the settings import");
    if (!res.ok) throw new Error("settings import failed: " + res.error);
    if (errs.length) throw new Error("page errors");
    console.log("coverage", await p.textContent("#cover"));
    console.log(await p.textContent("#stats"));
    const [d] = await Promise.all([p.waitForEvent("download"), p.click("#dlMask")]);
    await d.saveAs(path.join(outdir, "mask.png"));
    fs.writeFileSync(path.join(outdir, "res.txt"), String(res.res) + "\n");
  } catch (e) {
    failure = e;
    for (const f of ["mask.png", "res.txt"]) fs.rmSync(path.join(outdir, f), { force: true });
  } finally {
    await b.close();
  }
  if (failure || errs.length) {
    console.error((failure ? failure.message : "export finished") + (errs.length ? "; page errors: " + errs.join("; ") : ""));
    process.exit(1);
  }
})();
