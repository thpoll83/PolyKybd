#!/usr/bin/env python3
"""Compute the RoHS page selection for each certificate and record it as an
'Appendix Pages' column in parts-to-pdf-reference.xls, so the appendix PDF can be
reproduced (and the selection edited) directly from the spreadsheet."""
import xlrd, os, warnings
warnings.filterwarnings("ignore")
import pdfplumber
from pypdf import PdfReader
from xlutils.copy import copy
from xlwt import easyxf

RD = "/sessions/bold-festive-carson/mnt/PolyKybd/RoHS"
XLS = os.path.join(RD, "parts-to-pdf-reference.xls")
COL = 7  # new 'Appendix Pages' column

KW = ['rohs','2011/65','2015/863','restricted','hazardous','cadmium','mercury','pbb','pbde',
      'phthalate','halogen','not detected','n.d.','deha','dehp','無鹵','绿色','有害','限用','reach']

def rohs_pages(path):
    hits=[]
    with pdfplumber.open(path) as pdf:
        for i,p in enumerate(pdf.pages):
            t=(p.extract_text() or '').lower()
            if any(k in t for k in KW): hits.append(i+1)
    return hits

def kept_for(doc):
    if doc.lower().endswith(".png"):
        return "image"
    path=os.path.join(RD,doc)
    n=len(PdfReader(path).pages)
    if n<=3:
        return "all"
    rp=rohs_pages(path)
    if not rp:                       # image-only scan -> keep whole
        return "all"
    s=set([1])                       # page 1 = identity
    for p in rp:                     # +/-1 neighbour for context
        for q in (p-1,p,p+1):
            if 1<=q<=n: s.add(q)
    kept=sorted(s)
    return "all" if len(kept)==n else ",".join(map(str,kept))

# unique doc -> selection
rb=xlrd.open_workbook(XLS, formatting_info=True)
rs=rb.sheet_by_index(0)
docmap={}
for r in range(1,rs.nrows):
    d=rs.cell_value(r,2).strip()
    if d and d not in docmap:
        docmap[d]=kept_for(d)

wb=copy(rb); ws=wb.get_sheet(0)
hdr=easyxf('font: bold on; align: wrap on')
ws.write(0,COL,"Appendix Pages",hdr)
for r in range(1,rs.nrows):
    d=rs.cell_value(r,2).strip()
    if d:
        ws.write(r,COL,docmap[d])
wb.save(XLS)

print("wrote 'Appendix Pages' column. Unique certs:")
for d,v in docmap.items():
    print(f"  {v:20} {d}")
