import math, random, sys
from cosmos import OUT, keycap, place, BLANK, HALF, CW, CH, glyphs, pathops
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
GAP=0.8
units={ch:keycap(ch) for ch in glyphs}
COOL=[(0.0,(0x1b,0x16,0x46)),(0.25,(0x2b,0x2f,0x8f)),(0.45,(0x2f,0x5f,0xd6)),(0.65,(0x2f,0x9b,0xf6)),(0.8,(0x45,0xd0,0xf5)),(0.92,(0xa8,0xec,0xff)),(1.0,(0xee,0xfc,0xff))]
WARM=[(0.0,(0x2c,0x10,0x3a)),(0.3,(0x5e,0x1f,0x8a)),(0.55,(0x9b,0x3f,0xd6)),(0.75,(0xd8,0x5c,0xe0)),(0.9,(0xff,0x9b,0xe8)),(1.0,(0xff,0xe4,0xf7))]
def ramp(stops,z):
    z=min(1,max(0,z))
    for (z0,c0),(z1,c1) in zip(stops,stops[1:]):
        if z<=z1:
            t=(z-z0)/(z1-z0); return tuple(round(a+(b-a)*t) for a,b in zip(c0,c1))
    return stops[-1][1]
def colour(z,warm): 
    zq=round(z*16)/16          # 17 depth bins per ramp keeps the file to a few dozen paths
    c=ramp(WARM if warm else COOL,zq); return '#%02x%02x%02x'%c
def sparkle(cx,cy,r,rot):
    # four-pointed star
    p=pathops.Path(); pen=p.getPen(); k=r*0.22
    pts=[]
    for i in range(8):
        a=math.radians(rot)+i*math.pi/4; rr=r if i%2==0 else k
        pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
    pen.moveTo(pts[0])
    for q in pts[1:]: pen.lineTo(q)
    pen.closePath(); return p
class DScene:
    def __init__(s,cell=12.0): s.items=[]; s.grid={}; s.cell=cell
    def _near(s,cx,cy,rad):
        c=s.cell; out=[]
        for gx in range(int((cx-rad-30)//c),int((cx+rad+30)//c)+1):
            for gy in range(int((cy-rad-30)//c),int((cy+rad+30)//c)+1):
                out.extend(s.grid.get((gx,gy),()))
        return out
    def try_add(s,unit,cx,cy,scale,rot,z,warm,dz=0.12):
        rad=HALF*scale+GAP/2
        halo=place(BLANK,cx,cy,scale+GAP/min(CW,CH),rot)
        for it in s._near(cx,cy,rad):
            if abs(it['z']-z)>=dz: continue      # different depth: overlap allowed
            if math.hypot(cx-it['cx'],cy-it['cy'])>=rad+it['rad']: continue
            if abs(pathops.op(halo,it['halo'],pathops.PathOp.INTERSECTION).area)>1e-6: return False
        it=dict(path=place(unit,cx,cy,scale,rot),halo=halo,cx=cx,cy=cy,rad=rad,z=z,warm=warm)
        s.items.append(it); s.grid.setdefault((int(cx//s.cell),int(cy//s.cell)),[]).append(it); return True
def write(scene,sparkles,out,W,H,title,bg=False,rot_deg=0):
    # back to front; each shape loses whatever the shapes in front of it cover (plus a thin gap)
    items=sorted(scene.items,key=lambda i:i['z'])
    by_colour={}
    for idx,it in enumerate(items):
        p=it['path']
        for jt in scene._near(it['cx'],it['cy'],it['rad']):
            if jt['z']<=it['z'] or jt is it: continue
            if math.hypot(it['cx']-jt['cx'],it['cy']-jt['cy'])>=it['rad']+jt['rad']: continue
            p=pathops.op(p,jt['halo'],pathops.PathOp.DIFFERENCE)
        by_colour.setdefault(colour(it['z'],it['warm']),[]).append(p)
    # rotate everything about the centre (clockwise on screen), then centre and fit it inside the print area
    ca,sa=math.cos(math.radians(rot_deg)),math.sin(math.radians(rot_deg))
    cx0,cy0=W/2,H/2
    ROT=(ca,sa,-sa,ca,cx0-ca*cx0+sa*cy0,cy0-sa*cx0-ca*cy0)
    groups=[]
    for src in (by_colour,sparkles):
        for col,ps in sorted(src.items()):
            rotated=[]
            for p in ps:
                if rot_deg:
                    q=pathops.Path(); p.draw(TransformPen(q.getPen(),ROT)); p=q
                rotated.append(p)
            groups.append((col,rotated))
    bx=[1e9,1e9,-1e9,-1e9]
    for col,ps in groups:
        for p in ps:
            b=p.bounds
            if b==(0,0,0,0): continue
            bx=[min(bx[0],b[0]),min(bx[1],b[1]),max(bx[2],b[2]),max(bx[3],b[3])]
    MARGIN=3
    # never scale: centre the rotated design and grow the print area if it needs more room
    W2=max(W,math.ceil(bx[2]-bx[0]+2*MARGIN)); H2=max(H,math.ceil(bx[3]-bx[1]+2*MARGIN))
    mx,my=(bx[0]+bx[2])/2,(bx[1]+bx[3])/2
    FIT=(1,0,0,1,W2/2-mx,H2/2-my) if rot_deg else (1,0,0,1,0,0)
    if not rot_deg: W2,H2=W,H
    k=1.0
    out_paths=[]; fb=[1e9,1e9,-1e9,-1e9]
    for col,ps in groups:
        dd=[]
        for p in ps:
            q=pathops.Path(); p.draw(TransformPen(q.getPen(),FIT))
            b=q.bounds
            if b!=(0,0,0,0): fb=[min(fb[0],b[0]),min(fb[1],b[1]),max(fb[2],b[2]),max(fb[3],b[3])]
            sp=SVGPathPen(None,ntos=lambda v:('%.2f'%v).rstrip('0').rstrip('.')); q.draw(sp); dd.append(sp.getCommands())
        d=' '.join(x for x in dd if x.strip())
        if d: out_paths.append(f'<path fill="{col}" d="{d}"/>')  # a colour whose shapes were all occluded draws nothing
    assert fb[0]>=0 and fb[1]>=0 and fb[2]<=W2 and fb[3]<=H2, ('outside the print area',fb)
    print('  print area %gx%g mm, drawn extent x %.1f..%.1f  y %.1f..%.1f mm (scale 1)'%(W2,H2,fb[0],fb[2],fb[1],fb[3]))
    bgr=f'<rect width="{W2}" height="{H2}" fill="#000"/>\n' if bg else ''
    open(out,'w',encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {H2}" width="{W2}mm" height="{H2}mm">
<title>{title}</title>
{bgr}{chr(10).join(out_paths)}
</svg>
''')
    return len(items), sum(len(v) for v in sparkles.values()), len(by_colour)
def populate(sampler,rng,n_fill=1500,n_spark=200,spark_ok=None,W=300,H=300,scene=None):
    """sampler(z, rng) -> (cx,cy,scale,rot) or None. Places 160 unique front keycaps, then fill, then sparkles."""
    sc=scene or DScene()
    order=[] if scene else list(glyphs); rng.shuffle(order)
    for ch in order:
        for t in range(12000):
            z=rng.uniform(0.62,1.0); smp=sampler(z,rng,0.45)
            if smp and sc.try_add(units[ch],*smp,z,rng.random()<0.025,dz=1.0): sc.items[-1]['unique']=True; break
        else: raise SystemExit('could not place '+ch)
    placed=0
    for t in range(n_fill*6):
        z=rng.random()**1.4*0.72          # most filler sits toward the back
        smp=sampler(z,rng,0.1)
        if smp and sc.try_add(units[rng.choice(glyphs)],*smp,z,rng.random()<0.025): placed+=1
        if placed>=n_fill: break
    sp={}; ns=0; items=sc.items
    CXc,CYc=W/2,H/2
    for t in range(n_spark*40):
        it=rng.choice(items)
        ang=rng.uniform(0,2*math.pi); d=it['rad']+abs(rng.gauss(0,5))
        # push outward more often than inward, so the halo fades away from the design
        ox,oy=it['cx']-CXc,it['cy']-CYc; on=math.hypot(ox,oy) or 1
        if rng.random()<0.6: ang=math.atan2(oy,ox)+rng.gauss(0,0.7)
        x,y=it['cx']+d*math.cos(ang),it['cy']+d*math.sin(ang)
        if not (6<=x<=W-6 and 6<=y<=H-6): continue
        if spark_ok and not spark_ok(x,y): continue
        r=rng.choice([0.35,0.45,0.55,0.7,0.85,1.0,1.2]) if rng.random()<0.95 else rng.uniform(1.4,2.1)
        if any(jt['z']>=0.62 and math.hypot(x-jt['cx'],y-jt['cy'])<jt['rad']+r for jt in sc._near(x,y,r)): continue
        col=rng.choices(['#ffffff','#fff4c2','#ffd97a','#d9fbff','#8fe3ff','#b8d4ff','#c8ffe6','#ffd1ef'],weights=[5,3,2,3,2,2,1.5,0.6])[0]
        sp.setdefault(col,[]).append(sparkle(x,y,r,rng.choice([0,45])+rng.uniform(-8,8))); ns+=1
        if ns>=n_spark: break
    # proof: nothing drawn in front of a unique keycap touches it
    for it in sc.items:
        if not it.get('unique'): continue
        for jt in sc._near(it['cx'],it['cy'],it['rad']):
            if jt is it or jt['z']<=it['z']: continue
            if math.hypot(it['cx']-jt['cx'],it['cy']-jt['cy'])>=it['rad']+jt['rad']: continue
            assert abs(pathops.op(it['halo'],jt['halo'],pathops.PathOp.INTERSECTION).area)<1e-6, 'unique keycap covered'
    assert sum(1 for it in sc.items if it.get('unique'))==len(glyphs)
    return sc,sp,placed
