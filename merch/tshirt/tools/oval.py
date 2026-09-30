import math, random
from cosmos import *
W=H=300; CX=CY=150; M=3
rng=random.Random(21)
units={ch:keycap(ch) for ch in glyphs}
A_,B_,TILT=138,98,math.radians(-17)
def rmax(th):
    # tilted ellipse, bent by slow waves so the outline is lopsided
    t=th-TILT
    r=1/math.sqrt((math.cos(t)/A_)**2+(math.sin(t)/B_)**2)
    r*=1+0.09*math.sin(3*th+1.1)+0.06*math.sin(5*th+2.3)+0.05*math.sin(2*th+0.4)
    c,s=abs(math.cos(th)),abs(math.sin(th))
    return min(r,(W/2-M)/c if c>1e-9 else 1e9,(H/2-M)/s if s>1e-9 else 1e9)
def fits_oval(cx,cy,s):
    dx,dy=cx-CX,cy-CY; r=math.hypot(dx,dy); th=math.atan2(dy,dx)
    return r+HALF*s<=rmax(th)
def attempt(k):
    sc=Scene()
    order=list(glyphs); rng.shuffle(order)
    sizes=[]
    for ch in order:
        m=rng.uniform(1.5,1.9) if rng.random()<0.06 else min(1.5,max(0.45,rng.lognormvariate(-0.35,0.42)))
        sizes.append((max(0.45,min(2.3,m*k)),ch))
    sizes.sort(reverse=True)
    for rank,(s,ch) in enumerate(sizes):
        pos_bias=1-rank/len(sizes)            # big keycaps sit toward the rim
        ok=False
        for tries in range(2500):
            th=rng.uniform(0,2*math.pi)
            rho=min(0.97,max(0.12,0.28+0.66*pos_bias**0.8+rng.gauss(0,0.1)))
            r=rho*rmax(th)
            cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
            if not fits_oval(cx,cy,s): continue
            if sc.try_add(units[ch],cx,cy,s,math.degrees(th)+90+rng.uniform(-10,10)): ok=True; break
            if tries%500==499: s=max(0.45,s*0.93)
        if not ok: return None
    return sc
k=1.0
while True:
    sc=attempt(k); print(f'size factor {k:.2f}:', 'ok' if sc else 'no room')
    if sc: break
    k*=0.94
# the flash: micro-rays of tiny squares at the core
flash=0
for _ in range(160):
    a=rng.uniform(0,2*math.pi); r=rng.uniform(1,5); sz=rng.uniform(0.2,0.34)
    while sz>=0.1 and r<22:
        if sc.try_add(units[rng.choice(glyphs)],CX+r*math.cos(a),CY+r*math.sin(a),sz,math.degrees(a)+90): flash+=1
        r+=HALF*sz*2+GAP+0.4; sz*=rng.uniform(0.8,0.9)
# fill along radial lanes only, so dark rays stay open between them
lanes=[2*math.pi*j/44+rng.uniform(-0.03,0.03) for j in range(44)]
fill=0
for _ in range(14000):
    th=rng.choice(lanes)+rng.uniform(-0.025,0.025); rho=math.sqrt(rng.uniform(0.01,1)); r=rho*rmax(th)
    s=min(0.8,max(0.1,rng.lognormvariate(math.log(0.14+0.34*rho),0.4)))
    cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
    if not fits_oval(cx,cy,s): continue
    if sc.try_add(units[rng.choice(glyphs)],cx,cy,s,math.degrees(th)+90+rng.uniform(-6,6)): fill+=1
# escapees: a few pieces already past the rim, breaking the outline
esc=0
for _ in range(4000):
    th=rng.uniform(0,2*math.pi); r=rmax(th)*rng.uniform(1.04,1.2); s=rng.uniform(0.25,0.7)
    cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
    if not (M+HALF*s<=cx<=W-M-HALF*s and M+HALF*s<=cy<=H-M-HALF*s): continue
    if sc.try_add(units[rng.choice(glyphs)],cx,cy,s,math.degrees(th)+90+rng.uniform(-6,6)): esc+=1
    if esc>=14: break
print('flash',flash,'fill',fill,'escapees',esc,'total shapes',len(sc.items))
write(sc,OUT+'/polykybd-tee-oval-explosion.svg',W,H,'PolyKybd tee: oval explosion of 160 keycaps')
