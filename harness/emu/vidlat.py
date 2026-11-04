import sys,re,collections
fn=sys.argv[1]; pal=sys.argv[2]=='1'; sgb2=len(sys.argv)>3 and sys.argv[3]=='sgb2'
fm=21281370.0 if pal else 21477272.0
fgb=20971520.0/5 if sgb2 else fm/5
LINE=1364/fm*1000; GBLINE=456/fgb*1000
v0={}; gbv=[]; vids={}; g143=[]
for l in open(fn):
    if l.startswith('VID F'):
        f=int(l[5:10]); vals=l.split(':')[1].split(); vids[f]=vals; continue
    m=re.match(r'\s*([\d.]+)ms F(\d+)',l)
    t=float(m.group(1)); f=int(m.group(2))
    if 'SNES V0' in l: v0[f]=t
    elif 'VRESET' in l: gbv.append(t)
    elif 'line 143' in l: g143.append(t)
fr=[f for f in sorted(vids) if f in v0 and f>=560]
# GB area rows
def snesline(j): return j//2+1
cnt=collections.Counter()
for f in fr:
    vals=vids[f]
    for j in range(0,len(vals),2):
        cnt[vals[j]]+=1
# GB area = rows whose value changes across frames
rows=[j for j in range(0,len(vids[fr[0]]),2) if len(set(vids[f][j] for f in fr))>1]
y0=snesline(rows[0]); y1=snesline(rows[-1])
colors=collections.Counter(vids[f][j] for f in fr for j in rows)
cols=[c for c,_ in colors.most_common(4)]
def lum(c):
    v=int(c,16); return ((v>>11)&31)*2+((v>>5)&63)+(v&31)*2
cols.sort(key=lum,reverse=True)   # lightest = BGP $00
idx={c:i for i,c in enumerate(cols)}
best=None
for phi in range(4):
    lat=[];bad=0;torn=0
    for f in fr:
        T0=v0[f]; seen=set()
        for j in rows:
            Y=snesline(j); y=Y-y0
            td=T0+Y*LINE
            c=vids[f][j]; seen.add(c)
            if c not in idx: bad+=1; continue
            # most recent GB frame k with shade idx[c] whose line y output before td
            cand=[k for k,tg in enumerate(gbv) if k+1<len(gbv) and gbv[k+1]<T0 and (k+phi)%4==idx[c]]
            if not cand: bad+=1; continue
            k=cand[-1]; lat.append((y,td-(gbv[k]+y*GBLINE),f,k))
        if len(seen)>1: torn+=1
    # consistency: within each SNES frame all lines should come from one GB frame; prefer phi where the chosen frame completed latest (tightest) yet before display
    mx=max(l[1] for l in lat) if lat else 1e9
    if best is None or (bad,mx)<(best[0],best[1]): best=(bad,mx,phi,lat,torn)
bad,mx,phi,lat,torn=best
print(f'{fn}: GB area SNES lines {y0}-{y1}, frames analysed {len(fr)}, unmatched {bad}, torn frames {torn}')
for yy in (0,71,143):
    L=[l for y,l,f,k in lat if y==yy]
    print(f'  GB line {yy:3d}: latency min {min(L):6.2f} ms  max {max(L):6.2f} ms  mean {sum(L)/len(L):6.2f}')
L=[l for y,l,f,k in lat]; print(f'  all lines: min {min(L):.2f} max {max(L):.2f} ms')
# GB frames never displayed / displayed twice
shown=collections.Counter()
for f in fr:
    ks={k for y,l,ff,k in lat if ff==f}; 
    for k in ks: shown[k]+=1
ks=range(min(shown),max(shown)+1)
print('  GB frames in range',len(ks),'never shown',sum(1 for k in ks if shown[k]==0),'shown twice+',sum(1 for k in ks if shown[k]>1))
