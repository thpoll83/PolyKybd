from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen
import pathops, sys
import os
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.environ.get('TEE_OUT', os.path.dirname(HERE))
glyphs=open(os.path.join(HERE,'glyphs.txt'),encoding='utf-8').read()
fams=['Noto Sans','Noto Sans JP','Noto Sans KR','Noto Sans SC','Noto Sans Thai','Noto Sans Arabic','Noto Sans Hebrew','Noto Sans Devanagari','Noto Sans Bengali','Noto Sans Tamil','Noto Sans Telugu','Noto Sans Georgian','Noto Sans Armenian','Noto Sans Ethiopic','Noto Sans Cherokee','Noto Sans Canadian Aboriginal']
fonts=[(f,TTFont(os.path.join(HERE,'fonts')+'/'+f.replace(' ','_')+'.ttf')) for f in fams]
base=dict(fonts)['Noto Sans']
upm0=base['head'].unitsPerEm; asc0=base['hhea'].ascent; desc0=-base['hhea'].descent
FS=9.0; CW=(280-15*2)/16; CH=15.0; GAP=2.0; R=2.0
line=(asc0+desc0)*FS/upm0
baseline_in_cell=(CH-FS)/2 + (FS-line)/2 + asc0*FS/upm0
K=0.5523*R
def rrect(x,y,w,h):
    p=pathops.Path(); pen=p.getPen()
    pen.moveTo((x+R,y)); pen.lineTo((x+w-R,y)); pen.curveTo((x+w-R+K,y),(x+w,y+R-K),(x+w,y+R))
    pen.lineTo((x+w,y+h-R)); pen.curveTo((x+w,y+h-R+K),(x+w-R+K,y+h),(x+w-R,y+h))
    pen.lineTo((x+R,y+h)); pen.curveTo((x+R-K,y+h),(x,y+h-R+K),(x,y+h-R))
    pen.lineTo((x,y+R)); pen.curveTo((x,y+R-K),(x+R-K,y),(x+R,y)); pen.closePath()
    return p
used={}; ds=[]; issues=[]
for i,ch in enumerate(glyphs):
    col,row=i%16,i//16
    x=col*(CW+GAP); y=row*(CH+GAP)
    for name,f in fonts:
        g=f.getBestCmap().get(ord(ch))
        if g and g!='.notdef': break
    else:
        issues.append(ch); continue
    used[name]=used.get(name,0)+1
    gs=f.getGlyphSet(); upm=f['head'].unitsPerEm; s=FS/upm
    adv=f['hmtx'][g][0]*s
    gx=x+(CW-adv)/2; gy=y+baseline_in_cell
    gp=pathops.Path(); tp=TransformPen(gp.getPen(glyphSet=gs),(s,0,0,-s,gx,gy))
    gs[g].draw(tp)
    gp.simplify()
    if abs(gp.area)<0.5: issues.append(ch+'(empty)')
    b=gp.bounds
    if b[0]<x or b[2]>x+CW or b[1]<y or b[3]>y+CH: issues.append(ch+'(overflows cell)')
    cell=pathops.op(rrect(x,y,CW,CH),gp,pathops.PathOp.DIFFERENCE)
    sp=SVGPathPen(None,ntos=lambda v:('%.3f'%v).rstrip('0').rstrip('.'))
    cell.draw(sp); ds.append(sp.getCommands())
W=280; H=10*CH+9*GAP
svg=f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:g}" width="{W}mm" height="{H:g}mm">
<title>PolyKybd tee 2g: 160 keycaps, knockout glyphs</title>
<path fill="#2f7bf6" fill-rule="nonzero" d="{' '.join(ds)}"/>
</svg>
'''
open(os.path.join(OUT,'polykybd-tee-2g-keycap-grid.svg'),'w',encoding='utf-8').write(svg)
print('cells',len(ds),'issues',issues); print(used); print(len(svg)//1024,'KB')
