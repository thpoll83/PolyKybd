import math, random
from cosmos import *
W=H=300; CX=CY=150; M=3
def inside(cx,cy,s): return M+HALF*s<=cx<=W-M-HALF*s and M+HALF*s<=cy<=H-M-HALF*s
def ray_room(th):
    c,s=abs(math.cos(th)),abs(math.sin(th))
    return min((W/2-M)/c if c>1e-9 else 1e9,(H/2-M)/s if s>1e-9 else 1e9)
units={ch:keycap(ch) for ch in glyphs}
def build(seed,k):
    rng=random.Random(seed)
    NR=30
    angles=[2*math.pi*j/NR+rng.uniform(-0.08,0.08) for j in range(NR)]
    reach=[ray_room(a)*rng.uniform(0.66,1.0) for a in angles]
    order=list(glyphs); rng.shuffle(order)
    mult={ch:(rng.uniform(1.7,2.1) if rng.random()<0.05 else min(1.9,max(0.55,rng.lognormvariate(0,0.38)))) for ch in glyphs}
    def size_at(r,ch): return max(0.45,min(2.2,(0.45+0.8*(r/150)**1.2)*k*mult[ch]))
    sc=Scene(); placed=[]
    pos=[16+rng.uniform(0,30) for _ in range(NR)]; alive=[True]*NR; gi=0
    while gi<len(order) and any(alive):
        for j in range(NR):
            if not alive[j] or gi>=len(order): continue
            while True:
                r=pos[j]; th=angles[j]+rng.uniform(-0.03,0.03); s=size_at(r,order[gi])
                cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
                if r>reach[j] or not inside(cx,cy,s): alive[j]=False; break
                rot=math.degrees(th)+90+rng.uniform(-6,6)
                if sc.try_add(units[order[gi]],cx,cy,s,rot):
                    placed.append((cx,cy,s,th,rot)); gi+=1
                    pos[j]=r+HALF*s*2*rng.uniform(1.0,1.35)+1.5; break
                pos[j]+=1.0
    return sc,placed,gi,rng
k=1.0
while True:
    sc,placed,gi,rng=build(5,k)
    print(f'size factor {k:.2f}: placed {gi}/160')
    if gi==len(glyphs): break
    k*=0.95
# the flash at the centre
flash=0
for _ in range(160):
    a=rng.uniform(0,2*math.pi); r=rng.uniform(1,5); sz=0.34
    while sz>=0.1 and r<18:
        if sc.try_add(units[rng.choice(glyphs)],CX+r*math.cos(a),CY+r*math.sin(a),sz,math.degrees(a)+90): flash+=1
        r+=HALF*sz*2+GAP+0.4; sz*=0.84
# streaks behind every keycap
streak=0
for cx,cy,s,th,rot in placed:
    d=HALF*s; f=rng.uniform(0.22,0.5)
    while s*f>=0.1:
        d+=HALF*s*f*2+GAP+0.6
        px,py=cx-d*math.cos(th),cy-d*math.sin(th)
        if math.hypot(px-CX,py-CY)<14: break
        if sc.try_add(units[rng.choice(glyphs)],px,py,s*f,rot): streak+=1
        f*=rng.uniform(0.6,0.85)
print('streak',streak,'flash',flash,'total shapes',len(sc.items))
write(sc,OUT+'/polykybd-tee-star-explosion.svg',W,H,'PolyKybd tee: star explosion of 160 keycaps')
