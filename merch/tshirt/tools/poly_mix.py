import re, subprocess, urllib.parse
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen
import pathops, sys
import os
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.environ.get('TEE_OUT', os.path.dirname(HERE))
os.makedirs(os.path.join(HERE,'fonts_poly'),exist_ok=True)
KEEP=sys.argv[1:] or ('mix-2','mix-3','mix-5')  # the committed variants; pass names to build others
V=[ # name, letters in reading order (P, O, L, Y), rtl -- every letter from a different script
 ('mix-1', 'ΠოלИ', False),   # Greek, Georgian, Hebrew, Cyrillic
 ('mix-2', 'पஒلኢ', False),   # Devanagari, Tamil, Arabic, Ethiopic
 ('mix-3', 'Պᐅలϒ', False),   # placeholder, fixed below
 ('mix-4', 'პওЛԻ', False),   # Georgian, Bengali, Cyrillic, Armenian
 ('mix-5', 'பኦลই', False),   # Tamil, Ethiopic, Thai, Bengali
 ('mix-6', 'פஒलი', False),   # Hebrew, Tamil, Devanagari, Georgian
]
V[2]=('mix-3','ՊওలΥ',False)  # Armenian, Bengali, Telugu, Greek
allc=''.join(v[1] for v in V)
fams=['Noto Sans','Noto Sans Hebrew','Noto Sans Georgian','Noto Sans Armenian','Noto Sans Arabic','Noto Sans Devanagari','Noto Sans Bengali','Noto Sans Tamil','Noto Sans Telugu','Noto Sans Thai','Noto Sans Ethiopic','Noto Sans Canadian Aboriginal']
for f in fams:
    css=subprocess.run(['curl','-sS','https://fonts.googleapis.com/css2?family='+f.replace(' ','+')+':wght@600&text='+urllib.parse.quote(allc)],capture_output=True,text=True).stdout
    subprocess.run(['curl','-sS','-o',os.path.join(HERE,'fonts_poly')+'/'+f.replace(' ','_')+'.ttf',re.findall(r'url\((https://[^)]+)\)',css)[0]])
# font order: script-specific first so Noto Sans cannot claim Georgian etc. with a fallback shape
def _load(f):
    try: return TTFont(os.path.join(HERE,'fonts_poly')+'/'+f.replace(' ','_')+'.ttf')
    except Exception: return None  # family not needed: Google returns an error page
fonts=[(f,_load(f)) for f in ['Noto Sans Hebrew','Noto Sans Georgian','Noto Sans Armenian','Noto Sans Arabic','Noto Sans Devanagari','Noto Sans Bengali','Noto Sans Tamil','Noto Sans Telugu','Noto Sans Thai','Noto Sans Ethiopic','Noto Sans Canadian Aboriginal','Noto Sans']]
fonts=[(n,f) for n,f in fonts if f is not None]
base=dict(fonts)['Noto Sans']; upm0=base['head'].unitsPerEm; asc0=base['hhea'].ascent; desc0=-base['hhea'].descent
FS=9.0; CW=(280-15*2)/16; CH=15.0; GAP=2.0; R=2.0; K=0.5523*R
line=(asc0+desc0)*FS/upm0; BL=(CH-FS)/2+(FS-line)/2+asc0*FS/upm0
def rrect(x,y,w,h):
    p=pathops.Path(); pen=p.getPen()
    pen.moveTo((x+R,y)); pen.lineTo((x+w-R,y)); pen.curveTo((x+w-R+K,y),(x+w,y+R-K),(x+w,y+R))
    pen.lineTo((x+w,y+h-R)); pen.curveTo((x+w,y+h-R+K),(x+w-R+K,y+h),(x+w-R,y+h))
    pen.lineTo((x+R,y+h)); pen.curveTo((x+R-K,y+h),(x,y+h-R+K),(x,y+h-R))
    pen.lineTo((x,y+R)); pen.curveTo((x,y+R-K),(x+R-K,y),(x+R,y)); pen.closePath(); return p
def cell(ch,x,y):
    for name,f in fonts:
        g=f.getBestCmap().get(ord(ch))
        if g and g!='.notdef': break
    else: raise SystemExit('missing '+ch)
    gs=f.getGlyphSet(); s=FS/f['head'].unitsPerEm; adv=f['hmtx'][g][0]*s
    gp=pathops.Path(); gs[g].draw(TransformPen(gp.getPen(glyphSet=gs),(s,0,0,-s,x+(CW-adv)/2,y+BL))); gp.simplify()
    b=gp.bounds; assert b[0]>=x and b[2]<=x+CW and b[1]>=y and b[3]<=y+CH, ch
    return pathops.op(rrect(x,y,CW,CH),gp,pathops.PathOp.DIFFERENCE), name
W=2*CW+GAP; H=2*CH+GAP
for name,letters,rtl in V:
    # reading order -> grid slots; right-to-left fills top-right first
    slots=[(0,1),(0,0),(1,1),(1,0)] if rtl else [(0,0),(0,1),(1,0),(1,1)]
    ds=[]; used=[]
    for ch,(r,c) in zip(letters,slots):
        p,fn=cell(ch,c*(CW+GAP),r*(CH+GAP)); used.append(fn)
        sp=SVGPathPen(None,ntos=lambda v:('%.3f'%v).rstrip('0').rstrip('.')); p.draw(sp); ds.append(sp.getCommands())
    if name not in KEEP: continue
    out=f'{OUT}/polykybd-tee-poly-{name}.svg'
    open(out,'w',encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" width="{W:g}mm" height="{H:g}mm">
<title>POLY in {name}: {letters}{' (right to left)' if rtl else ''}</title>
<path fill="#2f7bf6" d="{' '.join(ds)}"/>
</svg>
''')
    print(out.split('/')[-1], letters, sorted(set(used)))
