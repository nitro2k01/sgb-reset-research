import sys,pickle,json,collections
sys.path.insert(0,'.')
from ramanalyze import fmt,N,ranges
res=pickle.load(open('ram/final.pkl','rb'))
SN={'SGB1_10':'sgb10','SGB1_11':'sgb11','SGB1_12':'sgb12','SGB2':'sgb2'}
CLR={0x8143,0x814e}
def refine(fw):
    f,st,info=res[fw]; out={}
    for a in range(N):
        c=f[a]
        if c=='boot':
            w,r=info[a]
            if set(w)<=CLR and not r: c='resetclr'
        out[a]=c
    return out
R={fw:refine(fw) for fw in res}
stat={fw:{int(k,16):v for k,v in json.load(open(f'ram/static_{SN[fw]}.json')).items()} for fw in res}
def okset(fw,allowed):
    return {a for a in range(N) if R[fw][a] in allowed}
for label,allowed in [('free',{'free'}),('upload',{'free','resetclr','boot'})]:
    s=set(range(N))
    for fw in res: s&=okset(fw,allowed)
    s-=set(range(0xF00,0x1000))
    print('==',label)
    tot=0
    for a,b in ranges(s):
        n=b-a+1
        if n<32: continue
        tot+=n
        refs=sorted({hex(x) for fw in res for x in stat[fw] if a<=x<=b})
        print(f'  {fmt(a)}-{fmt(b)} {n:6d}', refs[:8])
    print('  total>=32:',tot)

# PAL check
from ramanalyze import scan, payload_pcs
s=set(range(N))
for fw in res: s&=okset(fw,{'free','resetclr','boot'})
ex=payload_pcs('SGB1_12')
for sc in ('idle','cmd','monkey'):
    m,ml=scan('SGB1_12pal',sc,ex)
    bad=[a for a,(b,run,rp,wp) in m.items() if run and a in s]
    print('PAL',sc,len(bad),[fmt(x) for x in bad[:10]])
# per-fw extra free
for fw in res:
    own=okset(fw,{'free'})-set(range(0xF00,0x1000))
    others=set(range(N))
    for g in res: others&=okset(g,{'free'})
    extra=[(fmt(a),b-a+1) for a,b in ranges(own-others) if b-a+1>=64]
    print(fw,'extra free',extra)
