import subprocess,sys,re,os
bios,cart,pal=sys.argv[1],sys.argv[2],sys.argv[3]=='1'
env=dict(os.environ,SINGLEBUF='1'); 
if pal: env['FORCE_PAL']='1'
tag=f'{bios}_{cart}_{pal}'
def run(gap):
    b=f'sw_{tag}.bin'
    subprocess.run(['python3','-I','mkboot2.py',b,cart,str(gap),'0'],check=True)
    env['SGB_BOOT']=os.path.abspath(b)
    p=subprocess.run(['./fe','../bsnes/bsnes_libretro.so',os.path.abspath('sys'),bios,os.path.abspath(cart),'140'],env=env,capture_output=True,text=True)
    t6=res=None;lat=[];over=0
    for l in p.stderr.splitlines():
        m=re.match(r'\s*([\d.]+)ms',l)
        if not m: continue
        t=float(m.group(1))
        if 'OVERRUN' in l or 'WARNING' in l: over+=1
        if 'finished reading' in l: lat.append(float(l.split(': ')[1].split()[0]))
        if 'packet complete: fb' in l and t6 is None: t6=t
        if t6 and '6003 = 01' in l and res is None: res=t-t6
    return res,max(lat) if lat else None,over
pts={}
for g in range(0,640,20): pts[g]=run(g)
gs=sorted(pts)
# find jump
for a,b in zip(gs,gs[1:]):
    if pts[b][0] and pts[a][0] and pts[b][0]>pts[a][0]+5:
        for g in range(a+1,b): pts[g]=run(g)
        break
for g in sorted(pts):
    if pts[g][2]: print("  gap",g,pts[g])
r=[v[0] for v in pts.values() if v[0]]; L=[v[1] for v in pts.values() if v[1]]
print(f'{tag}: react min={min(r):.3f} max={max(r):.3f} ms ; SNES read-complete latency max={max(L):.3f} ms ; overrun/warn total={sum(v[2] for v in pts.values())} ; runs={len(pts)}')
