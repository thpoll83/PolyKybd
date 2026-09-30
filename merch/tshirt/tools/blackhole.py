import math, random
from cosmos import *
W=H=300; CX=CY=150; RD=147          # disk radius
RH=30                                # event horizon: left empty, the shirt shows through
RIN=RH+9                             # where the arms end
units={ch:keycap(ch) for ch in glyphs}
NA=3; B=0.26                          # arms, spiral tightness (r = RIN*e^(B*phi))
PHI_MAX=math.log(RD/RIN)/B
def pt(arm,phi,lat):
    th=phi+2*math.pi*arm/NA
    r=RIN*math.exp(B*phi)
    tx,ty=B*math.cos(th)-math.sin(th),B*math.sin(th)+math.cos(th); n=math.hypot(tx,ty); tx,ty=tx/n,ty/n
    # lateral offset across the arm (normal to the tangent)
    x=CX+r*math.cos(th)+lat*(-ty); y=CY+r*math.sin(th)+lat*tx
    rot=math.degrees(math.atan2(-tx,ty))   # keycap 'up' points inward along the arm: falling in
    return x,y,r,rot,(tx,ty)
def build(seed,k):
    rng=random.Random(seed)
    order=list(glyphs); rng.shuffle(order)
    mult={ch:(rng.uniform(1.7,2.1) if rng.random()<0.05 else min(1.9,max(0.55,rng.lognormvariate(0,0.38)))) for ch in glyphs}
    def size_at(r,ch): return max(0.45,min(2.2,(0.45+0.85*((r-RIN)/(RD-RIN))**1.05)*k*mult[ch]))
    sc=Scene(); placed=[]
    lanes=[(a,l) for a in range(NA) for l in (-1,0,1)]
    # march every lane from the outside in, one keycap per lane per round
    phi={ln:PHI_MAX-0.02-rng.uniform(0,0.35) for ln in lanes}; alive={ln:True for ln in lanes}; gi=0
    while gi<len(order) and any(alive.values()):
        for ln in lanes:
            if not alive[ln] or gi>=len(order): continue
            a,l=ln
            while True:
                p=phi[ln]
                if p<0: alive[ln]=False; break
                r=RIN*math.exp(B*p); s=size_at(r,order[gi])
                lat=l*(4+0.16*r)+rng.uniform(-1.5,1.5)
                x,y,rr,rot,_=pt(a,p,lat)
                if math.hypot(x-CX,y-CY)+HALF*s>RD or math.hypot(x-CX,y-CY)-HALF*s<RIN-4:
                    phi[ln]-=0.02; continue
                if sc.try_add(units[order[gi]],x,y,s,rot+rng.uniform(-5,5)):
                    placed.append((x,y,s,rot,a,p)); gi+=1
                    phi[ln]=p-(HALF*s*2*rng.uniform(1.05,1.5)+1.5)/(r*math.sqrt(1+B*B)); break
                phi[ln]-=0.015
    return sc,placed,gi,rng
k=1.0
while True:
    sc,placed,gi,rng=build(3,k)
    print(f'size factor {k:.2f}: placed {gi}/160')
    if gi==len(glyphs): break
    k*=0.95
# photon ring: a circle of tiny squares hugging the event horizon
ring=0; rr=RH+2.5; sz=0.12; n=int(2*math.pi*rr/(HALF*sz*2+GAP+0.3))
for j in range(n):
    a=2*math.pi*j/n
    if sc.try_add(units[rng.choice(glyphs)],CX+rr*math.cos(a),CY+rr*math.sin(a),sz,math.degrees(a)): ring+=1
# trails: a few shrinking squares behind each keycap, further out along the arm
trail=0
for x,y,s,rot,a,p in placed:
    q=p; f=rng.uniform(0.2,0.45)
    for _ in range(3):
        r=RIN*math.exp(B*q); q+=(HALF*s*(1+f)+GAP+1.0)/(r*math.sqrt(1+B*B))
        tx,ty,_,trot,_=pt(a,q,0)
        # follow the keycap's own lane: offset from the arm centre is kept
        dx,dy=x-pt(a,p,0)[0],y-pt(a,p,0)[1]
        if s*f>=0.1 and sc.try_add(units[rng.choice(glyphs)],tx+dx,ty+dy,s*f,trot): trail+=1
        f*=rng.uniform(0.55,0.8)
# infalling debris: tiny squares streaming along the arms into the ring
debris=0
for _ in range(9000):
    a=rng.randrange(NA); p=rng.uniform(-0.9,0.9)**2*math.copysign(1,rng.uniform(-1,1))*1.2
    if p<-1.0: continue
    r=RIN*math.exp(B*p)
    if r<RH+5: continue
    x,y,_,rot,_=pt(a,p,rng.gauss(0,3+0.08*r))
    s=min(0.5,max(0.1,rng.lognormvariate(math.log(0.16),0.45)))
    if math.hypot(x-CX,y-CY)<RH+4.5: continue
    if sc.try_add(units[rng.choice(glyphs)],x,y,s,rot): debris+=1
    if debris>=260: break
print('ring',ring,'trail',trail,'debris',debris,'total shapes',len(sc.items))
write(sc,OUT+'/polykybd-tee-black-hole.svg',W,H,'PolyKybd tee: black hole swallowing 160 keycaps')
