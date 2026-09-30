import math, os, random, sys
from depth import *
W=H=300; CX=CY=150; M=3
def in_square(cx,cy,s): return M+HALF*s<=cx<=W-M-HALF*s and M+HALF*s<=cy<=H-M-HALF*s
ROT='radial'
def orient(cx,cy,rng,j=6):
    # 180 deg from the first version: glyph tops point at the centre, bottoms face outward
    if ROT=='random': return rng.uniform(0,360)
    return math.degrees(math.atan2(cy-CY,cx-CX))-90+rng.uniform(-j,j)
def jit(rng): return min(1.8,max(0.55,rng.lognormvariate(0,0.32)))
def depth_scale(z): return 0.35+0.95*z

def star(seed=5):
    rng=random.Random(seed); NR=30
    def room(th):
        c,s=abs(math.cos(th)),abs(math.sin(th))
        return min((W/2-M)/c if c>1e-9 else 1e9,(H/2-M)/s if s>1e-9 else 1e9)
    ang=[2*math.pi*j/NR+rng.uniform(-0.08,0.08) for j in range(NR)]
    reach=[min(room(a)-4,138)*rng.uniform(0.62,1.0) for a in ang]
    def sampler(z,rng,min_s):
        j=rng.randrange(NR); r=rng.uniform(10,reach[j])
        th=ang[j]+rng.gauss(0,0.02+0.06*(1-z))
        s=max(min_s,(0.3+0.9*(r/150)**1.1)*depth_scale(z)*jit(rng))
        cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
        if not in_square(cx,cy,s): return None
        return cx,cy,s,orient(cx,cy,rng)
    sc,sp,n=populate(sampler,rng,n_fill=1500,n_spark=320)
    return sc,sp,n
def blackhole(seed=3):
    rng=random.Random(seed); RD=147; RH=30; RIN=RH+6; NA=3; B=0.26; PM=math.log(RD/RIN)/B
    def sampler(z,rng,min_s):
        a=rng.randrange(NA); p=PM*rng.random()**0.8
        th=p+2*math.pi*a/NA; r=RIN*math.exp(B*p)
        tx,ty=B*math.cos(th)-math.sin(th),B*math.sin(th)+math.cos(th); nn=math.hypot(tx,ty); tx,ty=tx/nn,ty/nn
        lat=rng.gauss(0,(3+0.13*r)*(1.6-z))
        cx,cy=CX+r*math.cos(th)-lat*ty,CY+r*math.sin(th)+lat*tx
        s=max(min_s,(0.3+0.85*((r-RIN)/(RD-RIN)))*depth_scale(z)*jit(rng))
        d=math.hypot(cx-CX,cy-CY)
        if d-HALF*s<RH+3 or d+HALF*s>RD: return None
        return cx,cy,s,orient(cx,cy,rng,5)
    sc,sp,n=populate(sampler,rng,n_fill=1500,n_spark=300,spark_ok=lambda x,y: math.hypot(x-CX,y-CY)>RH+1.5)
    return sc,sp,n
def oval(seed=21):
    rng=random.Random(seed); A_,B_,TILT=140,100,math.radians(-17)
    def rmax(th):
        t=th-TILT
        r=1/math.sqrt((math.cos(t)/A_)**2+(math.sin(t)/B_)**2)
        r*=1+0.09*math.sin(3*th+1.1)+0.06*math.sin(5*th+2.3)+0.05*math.sin(2*th+0.4)
        c,s=abs(math.cos(th)),abs(math.sin(th))
        return min(r,(W/2-M)/c if c>1e-9 else 1e9,(H/2-M)/s if s>1e-9 else 1e9)
    def sampler(z,rng,min_s):
        th=rng.uniform(0,2*math.pi)
        esc=rng.random()<0.03
        rho=rng.uniform(1.03,1.18) if esc else math.sqrt(rng.uniform(0.005,1))
        r=rho*rmax(th)
        s=max(min_s,(0.22+0.85*min(rho,1))*depth_scale(z)*jit(rng))
        cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
        if not in_square(cx,cy,s): return None
        if not esc and r+HALF*s>rmax(th): return None
        return cx,cy,s,orient(cx,cy,rng,8)
    sc,sp,n=populate(sampler,rng,n_fill=1600,n_spark=320)
    return sc,sp,n
def starburst(seed=17,thin=0):
    rng=random.Random(seed)
    def room(th):
        c,s=abs(math.cos(th)),abs(math.sin(th))
        return min((W/2-M)/c if c>1e-9 else 1e9,(H/2-M)/s if s>1e-9 else 1e9)
    gaps=[rng.uniform(0.5,1.6) for _ in range(8)]; t=rng.uniform(0,2*math.pi); major=[]
    for g in gaps: t+=g*2*math.pi/sum(gaps); major.append(t)
    lens=[1.0,0.96,0.88,0.8,0.72,0.64,0.56,0.5]; rng.shuffle(lens)
    mreach=[min(room(a)-4,142)*f for a,f in zip(major,lens)]
    mwidth=[rng.uniform(0.75,1.3) for _ in major]      # each big ray has its own thickness
    r2=random.Random(seed+1000); thin_angles=[]
    if thin:
        ms=sorted(m%(2*math.pi) for m in major)
        gaps=sorted(((ms[(i+1)%8]-ms[i])%(2*math.pi),i) for i in range(8))[::-1]
        thin_angles=[ms[i]+w*r2.uniform(0.38,0.62) for w,i in gaps[:thin]]
    minor=[]
    while len(minor)<22:      # minor rays keep clear of the big ones and the thin ones
        a=rng.uniform(0,2*math.pi)
        if all(abs((a-m+math.pi)%(2*math.pi)-math.pi)>0.09 for m in major) and \
           all(abs((a-m+math.pi)%(2*math.pi)-math.pi)>0.07 for m in thin_angles): minor.append(a)
    nreach=[min(room(a)-4,140)*rng.uniform(0.3,0.65) for a in minor]  # minor rays stay in the inner part
    sc=DScene(); order=list(glyphs); rng.shuffle(order); gi=0
    thin_sparks=[]; nthin=0; thin_reach=[]
    tl=[0.3,0.45,0.6,0.8,1.0]; r2.shuffle(tl)
    thin_w=[r2.uniform(0.7,1.5) for _ in thin_angles]
    for k,ang in enumerate(thin_angles):
        reach=(min(room(ang)-4,142))*tl[k%len(tl)]; thin_reach.append(reach); r=4.0
        while r<reach:
            t=r/reach; s=max(0.1,(0.1+0.26*math.sin(math.pi*min(1,t**0.85)))*thin_w[k]*r2.uniform(0.92,1.08))
            cx,cy=CX+r*math.cos(ang),CY+r*math.sin(ang)
            if not in_square(cx,cy,s): break
            z=0.8+0.1*math.sin(math.pi*t)            # pale cyan: bright, but a notch below the brightest keycaps
            if sc.try_add(units[r2.choice(glyphs)],cx,cy,s,orient(cx,cy,r2,2),z,False,dz=1.0):
                nthin+=1; r+=2*HALF*s+0.85
                if r2.random()<0.2:                    # a little glitter along the needle
                    side=r2.choice([-1,1]); off=HALF*s+0.9+r2.uniform(0.3,1.6)
                    thin_sparks.append((cx-side*off*math.sin(ang),cy+side*off*math.cos(ang),r2.uniform(0.35,0.7),r2.choice(['#fff4c2','#d9fbff','#8fe3ff','#ffffff','#c8ffe6'])))
            else: r+=0.4
    if thin: print('thin rays',len(thin_angles),'squares',nthin)
    TP=2/3   # the ray is largest at two thirds of its length
    UMIN=0.38  # smallest unique keycap in this design: ~6 mm, glyph ~3.4 mm
    def profile(t,peak,tip=0.1):
        if t<=TP: return 0.1+(peak-0.1)*(t/TP)**1.15            # starts very small at the core
        return peak-(peak-tip)*((t-TP)/(1-TP))**0.9              # shrinks again toward the tip
    def ray(angle,reach,peak,zpk):
        """one continuous chain from the core to the tip; unique keycaps where the ray is big enough"""
        nonlocal gi
        r=3.0
        while r<reach:
            t=r/reach; s=profile(t,peak)*rng.uniform(0.85,1.15)
            th=angle+rng.gauss(0,0.5/max(r,5))
            cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
            if not in_square(cx,cy,max(s,0.45)): break
            if s>=UMIN and gi<len(order):
                z=0.62+(zpk-0.62)*min(1,s/peak)
                ok=sc.try_add(units[order[gi]],cx,cy,s,orient(cx,cy,rng,4),z,rng.random()<0.025,dz=1.0)
                if ok: sc.items[-1]['unique']=True; gi+=1
            else:
                s=max(0.1,s); z=0.3+0.28*min(1,s/UMIN)       # small links of the chain sit behind the keycaps
                ok=sc.try_add(units[rng.choice(glyphs)],cx,cy,s,orient(cx,cy,rng,4),z,False)
            r+= (2*HALF*s*rng.uniform(0.95,1.1)+0.9) if ok else 0.6
    for j in range(8):
        ray(major[j],mreach[j],min(1.3,(0.72+0.38*(mreach[j]/142))*mwidth[j]),1.0)
    big=gi
    for j in range(len(minor)):
        ray(minor[j],nreach[j],0.62,0.8)
    # 3) anything left sits in a big ray's cloud
    tries=0
    while gi<len(order):
        tries+=1; assert tries<200000, 'no room for '+order[gi]
        j=rng.randrange(8); r=mreach[j]*rng.uniform(0.28,0.76); th=major[j]+rng.gauss(0,(2.5+0.09*r)*mwidth[j]/r)   # only in the swell, never in the fading tip
        cx,cy=CX+r*math.cos(th),CY+r*math.sin(th); s=UMIN
        if in_square(cx,cy,s) and sc.try_add(units[order[gi]],cx,cy,s,orient(cx,cy,rng,4),rng.uniform(0.62,0.9),rng.random()<0.025,dz=1.0):
            sc.items[-1]['unique']=True; gi+=1
    print('unique on big rays',big,'total unique',gi)
    def sampler(z,rng,min_s):
        u=rng.random()
        if u<(0.68 if thin_angles else 0.80):      # cloud hugging a big ray: tiny at the core, fullest at 2/3, shrinking to the tip
            j=rng.randrange(8); t=1.2*rng.random()**0.8; r=mreach[j]*t
            g=profile(min(t,1),1.0,0.1) if t<=1 else 0.1*max(0,1-(t-1)/0.2)
            if rng.random()>0.4+0.6*g or z>0.25+0.47*g: return None
            th=major[j]+rng.gauss(0,(1.2+0.06*r)*mwidth[j]/max(r,4))
            s=max(min_s,0.55*g*mwidth[j]*depth_scale(z)*rng.uniform(0.85,1.15))
            cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
            if not in_square(cx,cy,s): return None
            return cx,cy,s,orient(cx,cy,rng)
        elif thin_angles and u<0.95 and rng.random()<0.6:   # tight cluster around a thin ray
            j=rng.randrange(len(thin_angles)); t=1.15*rng.random()**0.85; r=thin_reach[j]*t
            g=profile(min(t,1),1.0,0.15) if t<=1 else 0.15*max(0,1-(t-1)/0.15)
            if rng.random()>0.3+0.7*g or z>0.2+0.45*g: return None
            th=thin_angles[j]+rng.gauss(0,(1.0+0.035*r)*thin_w[j]/max(r,4))
            s=max(min_s,0.38*g*thin_w[j]*depth_scale(z)*rng.uniform(0.85,1.15))
            cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
            if not in_square(cx,cy,s): return None
            return cx,cy,s,orient(cx,cy,rng)
        elif u<0.95:
            j=rng.randrange(len(minor)); t=rng.random(); r=nreach[j]*t
            th=minor[j]+rng.gauss(0,(1+0.03*r)/max(r,4)); kind=0.6*profile(t,1.0,0.15)
        else:
            th=rng.uniform(0,2*math.pi); r=125*math.sqrt(rng.uniform(0.01,1)); kind=0.3
        s=max(min_s,(0.3+0.9*(r/150)**1.1)*depth_scale(z)*jit(rng)*kind)
        cx,cy=CX+r*math.cos(th),CY+r*math.sin(th)
        if not in_square(cx,cy,s): return None
        return cx,cy,s,orient(cx,cy,rng)
    sc,sp,n=populate(sampler,rng,n_fill=1500,n_spark=320,scene=sc)
    for x,y,rr,col in thin_sparks:
        sp.setdefault(col,[]).append(sparkle(x,y,rr,r2.choice([0,45])))
    return sc,sp,n
which=sys.argv[1]; ROT=sys.argv[2] if len(sys.argv)>2 else 'radial'; TURN=float(sys.argv[3]) if len(sys.argv)>3 else 0
fn={'star-burst-thin-rays':lambda: starburst(thin=5),'star-burst':starburst,'star-explosion':star,'black-hole':blackhole,'oval-explosion':oval}[which]
sc,sp,n=fn()
for bg in ((False,True) if os.environ.get('TEE_PREVIEW') else (False,)):
    out=f'{OUT}/polykybd-tee-{which}-colour'+('-random-rotation' if ROT=='random' else '')+(f'-rot{TURN:g}' if TURN else '')+('-on-black' if bg else '')+'.svg'
    a,b,c=write(sc,sp,out,W,H,f'PolyKybd tee: {which}, colour',bg,rot_deg=TURN)
print(which,'squares',a,'fill',n,'sparkles',b,'colours',c)
