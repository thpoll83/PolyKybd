#!/usr/bin/env python3
import xlrd, os, io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Image as RLImage)
from reportlab.pdfgen import canvas as rl_canvas
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

A4W, A4H = 595.275591, 841.889764   # A4 portrait in points
import argparse, ce_common
SECTION = "RoHS Compliance Appendix"
_ap = argparse.ArgumentParser(); _ap.add_argument("--start", type=int, default=1)
START = _ap.parse_args().start
def a4_page(src):
    return ce_common.a4_fit(src)     # scale into the shared header/footer content band

RD = "/sessions/bold-festive-carson/mnt/PolyKybd/RoHS"
OUT = "/sessions/bold-festive-carson/mnt/outputs/PolyKybd-RoHS-Appendix.pdf"
STD = "Directive 2011/65/EU (RoHS) as amended by (EU) 2015/863"
PAGE = A4
MARGIN = 16*mm

# ---------- load BOM ----------
b = xlrd.open_workbook(os.path.join(RD, "parts-to-pdf-reference.xls"))
s = b.sheet_by_index(0)
rows = []
for r in range(1, s.nrows):
    ref = s.cell_value(r,0).strip()
    part = s.cell_value(r,1).strip()
    doc = s.cell_value(r,2).strip()
    qty = s.cell_value(r,3)
    try: qty = str(int(qty))
    except: qty = str(qty)
    manu = s.cell_value(r,4).strip()
    if not doc: continue
    rows.append({"ref":ref,"part":part,"doc":doc,"qty":qty,"manu":manu})

# ---------- group by unique doc, first-appearance order ----------
sections = []   # list of dict: doc, members[list of row], manus
index = {}
for row in rows:
    d = row["doc"]
    if d not in index:
        index[d] = len(sections)
        sections.append({"doc":d, "members":[], "manus":[]})
    sec = sections[index[d]]
    sec["members"].append(row)
    if row["manu"] and row["manu"] not in sec["manus"]:
        sec["manus"].append(row["manu"])

# add PCB substrate section (not in BOM)
sections.append({
    "doc":"rohs-certificate-of-conformity.pdf",
    "members":[{"ref":"PCB / bare board","part":"Printed circuit board (ENIG & lead-free HASL finish); incl. exposed copper of mounting holes & test points","qty":"-","manu":"JLCPCB"}],
    "manus":["JLCPCB"],
})
for i, sec in enumerate(sections, 1):
    sec["num"] = i

# ---------- page selection: read from the xls 'Appendix Pages' column ----------
# The spreadsheet is the reproducible source of truth. Edit that column to change
# which pages of a certificate appear in the appendix, then re-run this script.
_xb = xlrd.open_workbook(os.path.join(RD, "parts-to-pdf-reference.xls"))
_xs = _xb.sheet_by_index(0)
docpages = {}
for r in range(1, _xs.nrows):
    d = _xs.cell_value(r,2).strip()
    if d and d not in docpages:
        v = _xs.cell_value(r,7) if _xs.ncols > 7 else "all"
        docpages[d] = (v.strip() if isinstance(v,str) else str(v)).strip()
def parse_sel(sel, n):
    sel = (sel or "").strip().lower()
    if sel in ("all",""): return list(range(1,n+1))
    if sel == "image": return None
    pages = []
    for tok in sel.split(","):
        tok = tok.strip()
        if tok.isdigit():
            p = int(tok)
            if 1 <= p <= n: pages.append(p)
    return sorted(set(pages)) or list(range(1,n+1))
for sec in sections:
    doc = sec["doc"]; path = os.path.join(RD, doc)
    if doc.lower().endswith(".png"):
        sec.update(n=1, kept=None, trimmed=False); continue
    n = len(PdfReader(path).pages)
    kept = parse_sel(docpages.get(doc, "all"), n)
    sec.update(n=n, kept=kept, trimmed=(len(kept) < n))

# ---------- styles ----------
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#1F4E78"), spaceAfter=6)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#404040"))
CELL = ParagraphStyle("CELL", parent=ss["Normal"], fontName="Helvetica", fontSize=7.3, leading=9)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")
TOCC = ParagraphStyle("TOCC", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5, leading=14)
DIVH = ParagraphStyle("DIVH", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=16, textColor=colors.HexColor("#1F4E78"), spaceAfter=4)
DIVM = ParagraphStyle("DIVM", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=13, spaceAfter=2)
DIVN = ParagraphStyle("DIVN", parent=ss["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#606060"))

def esc(t):
    return (t or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# ---------- render helpers (each returns bytes of a PDF) ----------
def render_story(story):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=14*mm)
    doc.build(story)
    return buf.getvalue()

def title_story():
    st = []
    st.append(Spacer(1, 55*mm))
    st.append(Paragraph("PolyKybd", H1))
    st.append(Paragraph("RoHS Compliance Appendix", ParagraphStyle("t2",parent=H1,fontSize=17)))
    st.append(Spacer(1, 6*mm))
    st.append(Paragraph(esc(STD), SUB))
    st.append(Spacer(1, 3*mm))
    st.append(Paragraph("CE Technical File — Restriction of Hazardous Substances evidence for all "
                        "populated components and the bare printed circuit board.", SUB))
    st.append(Spacer(1, 3*mm))
    st.append(Paragraph("Prepared: 2026-07-12", SUB))
    return render_story(st)

def reftable_story():
    st = [Paragraph("Parts → Certificate Reference", ParagraphStyle("rt",parent=H1,fontSize=15))]
    st.append(Spacer(1,3*mm))
    head = [Paragraph(h,CELLB) for h in ["Sec.","Designators","Part / Value","Qty","Manufacturer","Certificate document"]]
    data = [head]
    for sec in sections:
        first = True
        for m in sec["members"]:
            data.append([
                Paragraph(str(sec["num"]) if first else "", CELL),
                Paragraph(esc(m["ref"]), CELL),
                Paragraph(esc(m["part"]), CELL),
                Paragraph(esc(m["qty"]), CELL),
                Paragraph(esc(m["manu"]), CELL),
                Paragraph(esc(sec["doc"]) if first else "", CELL),
            ])
            first = False
    avail = PAGE[0]-2*MARGIN
    w = [10*mm, 34*mm, 40*mm, 9*mm, 24*mm, avail-(10+34+40+9+24)*mm]
    t = Table(data, colWidths=w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F4E78")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#BFBFBF")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F2F5FA")]),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))
    st.append(t)
    return render_story(st)

def toc_story(page_of_section):
    st = [Paragraph("Table of Contents", ParagraphStyle("tc",parent=H1,fontSize=15))]
    st.append(Spacer(1,4*mm))
    for sec in sections:
        parts = ", ".join(m["ref"] for m in sec["members"])   # every part, no truncation
        manu = ", ".join(sec["manus"])
        pg = page_of_section.get(sec["num"], "")
        line = (f'<b>Section {sec["num"]} &nbsp;(p.{pg})</b> &nbsp;&mdash;&nbsp; '
                f'{esc(manu)} &nbsp;&mdash;&nbsp; {esc(parts)}')
        st.append(Paragraph(line, TOCC))
        st.append(Spacer(1,1.6*mm))
    return render_story(st)

def divider_story(sec):
    st = [Spacer(1, 6*mm)]
    st.append(Paragraph(f'Section {sec["num"]}', DIVH))
    st.append(Paragraph(esc(", ".join(sec["manus"])), DIVM))
    st.append(Spacer(1, 2*mm))
    # mini table of members
    head = [Paragraph(h,CELLB) for h in ["Designators","Part / Value","Qty"]]
    data=[head]
    for m in sec["members"]:
        data.append([Paragraph(esc(m["ref"]),CELL), Paragraph(esc(m["part"]),CELL), Paragraph(esc(m["qty"]),CELL)])
    avail = PAGE[0]-2*MARGIN
    t=Table(data, colWidths=[45*mm, avail-65*mm, 20*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9E1F2")),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#BFBFBF")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))
    st.append(t)
    st.append(Spacer(1, 3*mm))
    st.append(Paragraph("RoHS evidence document: <b>%s</b>" % esc(sec["doc"]), DIVN))
    st.append(Paragraph("Standard: %s" % esc(STD), DIVN))
    if sec.get("trimmed"):
        kp = ", ".join(str(x) for x in sec["kept"])
        st.append(Paragraph("Excerpt: page(s) %s of %d — RoHS-relevant pages only; "
                            "the complete document is retained in the project repository."
                            % (kp, sec["n"]), DIVN))
    return render_story(st)

def png_to_pdf_bytes(path):
    img = PILImage.open(path).convert("RGB")
    iw, ih = img.size
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=PAGE)
    aw, ah = PAGE[0]-2*MARGIN, PAGE[1]-2*MARGIN
    scale = min(aw/iw, ah/ih)
    w, h = iw*scale, ih*scale
    x = (PAGE[0]-w)/2; y = (PAGE[1]-h)/2
    tmp = io.BytesIO(); img.save(tmp, format="PNG"); tmp.seek(0)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(tmp), x, y, w, h, preserveAspectRatio=True)
    c.showPage(); c.save()
    return buf.getvalue()

def cert_bytes(sec):
    doc = sec["doc"]; path = os.path.join(RD, doc)
    if doc.lower().endswith(".png"):
        return png_to_pdf_bytes(path)
    reader = PdfReader(path)
    if not sec.get("trimmed"):
        with open(path,"rb") as f:
            return f.read()
    w = PdfWriter()
    for pg in sec["kept"]:
        w.add_page(reader.pages[pg-1])
    buf = io.BytesIO(); w.write(buf)
    return buf.getvalue()

def npages(pdf_bytes):
    return len(PdfReader(io.BytesIO(pdf_bytes)).pages)

# ---------- pass 1: build fixed parts, count pages ----------
title_b = title_story()
ref_b = reftable_story()
div_bytes = {sec["num"]: divider_story(sec) for sec in sections}
cert_bytes_map = {sec["num"]: cert_bytes(sec) for sec in sections}
# TOC page count (dummy)
toc_dummy = toc_story({sec["num"]:0 for sec in sections})

n_title = npages(title_b); n_ref = npages(ref_b); n_toc = npages(toc_dummy)
front = n_title + n_ref + n_toc
running = front
page_of_section = {}
for sec in sections:
    dstart = running + 1           # 1-based page of the divider
    page_of_section[sec["num"]] = dstart
    running += npages(div_bytes[sec["num"]]) + npages(cert_bytes_map[sec["num"]])

# ---------- pass 2: real TOC, assemble ----------
toc_b = toc_story(page_of_section)
assert npages(toc_b) == n_toc, f"TOC page count changed {npages(toc_b)} vs {n_toc}"

writer = PdfWriter()
def add_all(pdf_bytes):
    for p in PdfReader(io.BytesIO(pdf_bytes)).pages:
        writer.add_page(a4_page(p))   # normalise every page to A4 portrait

add_all(title_b)
ref_start = len(writer.pages)   # 0-based index where ref table begins
add_all(ref_b)
toc_start = len(writer.pages)
add_all(toc_b)
sec_page_index = {}
for sec in sections:
    sec_page_index[sec["num"]] = len(writer.pages)  # 0-based divider index
    add_all(div_bytes[sec["num"]])
    add_all(cert_bytes_map[sec["num"]])

# ---------- bookmarks / outline ----------
writer.add_outline_item("Parts → Certificate Reference", ref_start)
writer.add_outline_item("Table of Contents", toc_start)
certs_root = writer.add_outline_item("Certificates", sec_page_index[sections[0]["num"]])
for sec in sections:
    label = ", ".join(sec["manus"])
    writer.add_outline_item(f'Section {sec["num"]} — {label}', sec_page_index[sec["num"]], parent=certs_root)

ce_common.stamp(writer, SECTION, START)   # header/footer + page numbers
writer.add_metadata({"/Title":"PolyKybd RoHS Compliance Appendix","/Subject":STD})
with open(OUT,"wb") as f:
    writer.write(f)
print("start page:", START, "-> next section starts at page", START+len(writer.pages))

print("saved", OUT)
print("sections:", len(sections), "| total pages:", len(writer.pages))
print("front pages: title=%d ref=%d toc=%d" % (n_title,n_ref,n_toc))
print("--- trimmed certificates ---")
for sec in sections:
    if sec.get("trimmed"):
        print("  Sec %2d %-48s kept %s of %d" % (sec["num"], sec["doc"][:48],
              sec["kept"], sec["n"]))
# sanity: verify every referenced doc exists
missing = [sec["doc"] for sec in sections if not os.path.exists(os.path.join(RD,sec["doc"]))]
print("missing docs:", missing)
