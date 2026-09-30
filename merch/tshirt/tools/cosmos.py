import math, random, sys
import os
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.environ.get('TEE_OUT', os.path.dirname(HERE))
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen
import pathops
glyphs=open(os.path.join(HERE,'glyphs.txt'),encoding='utf-8').read()
fams=['Noto Sans','Noto Sans JP','Noto Sans KR','Noto Sans SC','Noto Sans Thai','Noto Sans Arabic','Noto Sans Hebrew','Noto Sans Devanagari','Noto Sans Bengali','Noto Sans Tamil','Noto Sans Telugu','Noto Sans Georgian','Noto Sans Armenian','Noto Sans Ethiopic','Noto Sans Cherokee','Noto Sans Canadian Aboriginal']
def _load(f):
    try: return TTFont(os.path.join(HERE,'fonts')+'/'+f.replace(' ','_')+'.ttf')
    except Exception: return None
fonts=[(f,t) for f in fams for t in [_load(f)] if t is not None]
base=dict(fonts)['Noto Sans']; upm0=base['head'].unitsPerEm; asc0=base['hhea'].ascent; desc0=-base['hhea'].descent
FS=9.0; CW=(280-15*2)/16; CH=15.0; R=2.0; K=0.5523*R
line=(asc0+desc0)*FS/upm0; BL=(CH-FS)/2+(FS-line)/2+asc0*FS/upm0
HALF=math.hypot(CW,CH)/2
def rrect(w,h,r):
    k=0.5523*r; p=pathops.Path(); pen=p.getPen()
    pen.moveTo((r,0)); pen.lineTo((w-r,0)); pen.curveTo((w-r+k,0),(w,r-k),(w,r))
    pen.lineTo((w,h-r)); pen.curveTo((w,h-r+k),(w-r+k,h),(w-r,h))
    pen.lineTo((r,h)); pen.curveTo((r-k,h),(0,h-r+k),(0,h-r))
    pen.lineTo((0,r)); pen.curveTo((0,r-k),(r-k,0),(r,0)); pen.closePath(); return p
def keycap(ch):
    """unit keycap (CW x CH at origin) with the glyph cut out"""
    for name,f in fonts:
        g=f.getBestCmap().get(ord(ch))
        if g and g!='.notdef': break
    gs=f.getGlyphSet(); s=FS/f['head'].unitsPerEm; adv=f['hmtx'][g][0]*s
    gp=pathops.Path(); gs[g].draw(TransformPen(gp.getPen(glyphSet=gs),(s,0,0,-s,(CW-adv)/2,BL))); gp.simplify()
    return pathops.op(rrect(CW,CH,R),gp,pathops.PathOp.DIFFERENCE)
BLANK=rrect(CW,CH,R)
def place(unit,cx,cy,scale,rot_deg):
    """scale around the cell centre, rotate, move the centre to (cx,cy)"""
    a=math.radians(rot_deg); c,s=math.cos(a)*scale,math.sin(a)*scale
    ox,oy=CW/2,CH/2
    # x' = c*(x-ox) - s*(y-oy) + cx ; y' = s*(x-ox) + c*(y-oy) + cy
    m=(c,s,-s,c,cx-(c*ox-s*oy),cy-(s*ox+c*oy))
    p=pathops.Path(); unit.draw(TransformPen(p.getPen(),m)); return p
GAP=0.8  # mm kept clear between any two shapes
class Scene:
    def __init__(s): s.items=[]   # (path, halo, cx, cy, radius)
    def try_add(s,unit,cx,cy,scale,rot):
        rad=HALF*scale+GAP/2
        halo=place(BLANK,cx,cy,scale+GAP/min(CW,CH),rot)   # blank shape grown by ~GAP/2 each side
        for p,h,qx,qy,qr in s.items:
            d=math.hypot(cx-qx,cy-qy)
            if d>=rad+qr: continue
            inter=pathops.op(halo,h,pathops.PathOp.INTERSECTION)
            if abs(inter.area)>1e-6: return False
        s.items.append((place(unit,cx,cy,scale,rot),halo,cx,cy,rad)); return True
def write(scene,out,W,H,title):
    ds=[]
    for p,*_ in scene.items:
        sp=SVGPathPen(None,ntos=lambda v:('%.2f'%v).rstrip('0').rstrip('.')); p.draw(sp); ds.append(sp.getCommands())
    open(out,'w',encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">
<title>{title}</title>
<path fill="#2f7bf6" d="{' '.join(ds)}"/>
</svg>
''')
