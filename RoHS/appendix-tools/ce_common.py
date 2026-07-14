#!/usr/bin/env python3
"""Shared styling + header/footer for the PolyKybd CE technical-file PDFs, so every
generated PDF looks the same and can be bundled with continuous page numbers.

Header:  left = overall document name, right = section name.
Footer:  left = section name, right = "Page N"  (N = --start offset + local page index).
Pass --start when bundling so each section continues the numbering of the previous one.
"""
import io
from reportlab.pdfgen import canvas as _canvas
from reportlab.lib import colors
from pypdf import PdfReader, PageObject, Transformation

A4W, A4H = 595.275591, 841.889764
BLUE = colors.HexColor("#1F4E78")
GREY = colors.HexColor("#707070")
RULE = colors.HexColor("#CCCCCC")
FONT, FONTB = "Helvetica", "Helvetica-Bold"
DOC_NAME = "PolyKybd — CE Technical File"

ML = MR = 28
HEADER_Y   = A4H - 22
HEADER_RULE = A4H - 28
FOOTER_RULE = 32
FOOTER_Y   = 20
CONTENT_TOP    = HEADER_RULE - 10     # usable content band top
CONTENT_BOTTOM = FOOTER_RULE + 8      # usable content band bottom

def draw_frame(c, section, page_no):
    """Draw header/footer directly on a reportlab canvas page (call before showPage)."""
    c.setFont(FONT, 8); c.setFillColor(GREY)
    c.drawString(ML, HEADER_Y, DOC_NAME)
    c.setFont(FONTB, 8); c.setFillColor(BLUE)
    c.drawRightString(A4W-MR, HEADER_Y, section)
    c.setStrokeColor(RULE); c.setLineWidth(0.4)
    c.line(ML, HEADER_RULE, A4W-MR, HEADER_RULE)
    c.line(ML, FOOTER_RULE, A4W-MR, FOOTER_RULE)
    c.setFont(FONT, 8); c.setFillColor(GREY)
    c.drawString(ML, FOOTER_Y, section)
    c.drawRightString(A4W-MR, FOOTER_Y, f"Page {page_no}")

def _frame_overlay(section, page_no):
    buf = io.BytesIO(); c = _canvas.Canvas(buf, pagesize=(A4W, A4H))
    draw_frame(c, section, page_no); c.save()
    return PdfReader(io.BytesIO(buf.getvalue())).pages[0]

def stamp(writer, section, start_page):
    """Merge header/footer onto every page of a PdfWriter, numbering from start_page."""
    for i, pg in enumerate(writer.pages):
        pg.merge_page(_frame_overlay(section, start_page + i))

def a4_fit(src_page, rotate_landscape=True):
    """Return a fresh A4 page with src scaled/centred inside the content band
    (leaving room for header/footer); landscape sources rotated to portrait."""
    page = PageObject.create_blank_page(width=A4W, height=A4H)
    if src_page is not None:
        if int(src_page.get("/Rotate", 0)):
            try: src_page.transfer_rotation_to_content()
            except Exception: pass
        pw = float(src_page.mediabox.width); ph = float(src_page.mediabox.height)
        m = 26; top = CONTENT_TOP; bottom = CONTENT_BOTTOM
        boxW = A4W - 2*m; boxH = top - bottom
        land = pw > ph and rotate_landscape
        ew, eh = (ph, pw) if land else (pw, ph)
        s = min(boxW/ew, boxH/eh)
        if land:
            t = (Transformation().rotate(90).translate(ph, 0).scale(s)
                 .translate(m+(boxW-ph*s)/2, bottom+(boxH-pw*s)/2))
        else:
            t = Transformation().scale(s).translate(m+(boxW-pw*s)/2, bottom+(boxH-ph*s)/2)
        page.merge_transformed_page(src_page, t)
    return page
