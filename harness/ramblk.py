import sys,pickle,collections
sys.path.insert(0,'.')
from ramanalyze import fmt,N
res=pickle.load(open('ram/final.pkl','rb'))
B=16
PRI=['runtime','static','feature','special','boot','free']
def rank(c):
    for i,p in enumerate(PRI):
        if c.startswith(p): return i
def blk(final):
    out=[]
    for b in range(N//B):
        cs=[final[b*B+i] for i in range(B)]
        out.append(min(cs,key=rank))
    return out
allb={fw:blk(f) for fw,(f,_,_) in res.items()}
inter=[min((allb[fw][b] for fw in allb),key=rank) for b in range(N//B)]
def show(bl,title,minlen=64):
    print('==',title)
    runs=[]
    for b,c in enumerate(bl):
        k=c.split(':')[0] if not c.startswith('feature') else c
        if runs and runs[-1][2]==k and runs[-1][1]==b-1: runs[-1][1]=b
        else: runs.append([b,b,k])
    for s,e,k in runs:
        ln=(e-s+1)*B
        if k=='runtime' and ln<minlen: pass
        print(f'  {fmt(s*B)}-{fmt(e*B+B-1)} {ln:6d} {k}')
show(inter,'intersection all fw')
