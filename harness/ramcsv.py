"""Writes data/wram_usage_<fw>.csv: runs of WRAM bytes with the same usage class (from ram/final.pkl)."""
import sys,pickle,os
sys.path.insert(0,'.')
from ramanalyze import fmt,N
res=pickle.load(open('ram/final.pkl','rb'))
CLR={0x8143,0x814e}
out=sys.argv[1]
for fw,(f,st,info) in res.items():
    rows=[]
    for a in range(N):
        c=f[a]
        if c=='boot':
            w,r=info[a]
            if set(w)<=CLR and not r: c='reset_clear'
        if rows and rows[-1][2]==c and rows[-1][1]==a-1: rows[-1][1]=a
        else: rows.append([a,a,c])
    with open(os.path.join(out,f'wram_usage_{fw}.csv'),'w') as o:
        o.write('start,end,bytes,class\n')
        for s,e,c in rows: o.write(f'{fmt(s)},{fmt(e)},{e-s+1},{c}\n')
    print(fw,len(rows))
