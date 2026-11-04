import math
def sim(name,fm,lines,fgb,early17=False):
    ts=1364/fm*1e3; Ts=lines*ts; tl=456/fgb*1e3; Tg=154*tl; trow=2560/fm*1e3  # 320 bytes DMA
    import random
    random.seed(1)
    res={}
    N=20000; phi=0.123
    def tk(k): return k*Tg+phi
    def avail(k,r):          # time row r of GB frame k is readable by SNES
        if r<17 or early17: return tk(k)+(8*r+8)*tl
        return tk(k)+154*tl          # row 17 only seen when next GB frame starts
    def latest(pred,t_hint):
        k=int((t_hint-phi)//Tg)+1
        while not pred(k): k-=1
        return k
    strategies={}
    for strat in ('stock','late','pipelined','tearing'):
        L={0:[],71:[],143:[]}
        for n in range(100,100+N):
            Tirq=n*Ts+223*ts; Tend=(n+1)*Ts
            if strat=='stock':
                k=latest(lambda k: avail(k,17)+0.15<=Tirq, Tirq); ks={r:k for r in range(18)}
            elif strat=='late':
                D=Tend-18*trow-0.1
                k=latest(lambda k: avail(k,17)+0.15<=D, D); ks={r:k for r in range(18)}
            elif strat=='pipelined':
                def ok(k):
                    t=Tirq
                    for r in range(18):
                        t=max(t,avail(k,r)+0.05)+trow
                    return t<=Tend
                k=latest(ok,Tend); ks={r:k for r in range(18)}
            else:
                ks={}
                for r in range(18):
                    tu=Tirq+r*trow
                    ks[r]=latest(lambda k: avail(k,r)+0.05<=tu, tu)
            for y in L:
                k=ks[y//8]
                L[y].append((Tend+(40+y)*ts)-(tk(k)+y*tl))
        strategies[strat]=L
    print(f'== {name}: GB frame {Tg:.2f} ms, SNES frame {Ts:.2f} ms, row DMA {trow*1000:.0f} us, early row17={early17}')
    for s,L in strategies.items():
        print(f'  {s:10s}'+''.join(f'  y={y:3d}: {min(v):5.1f}-{max(v):5.1f} (mean {sum(v)/len(v):5.1f})' for y,v in L.items()))
for e in (False,True):
    sim('SGB1 NTSC',21477272,262,21477272/5,e)
    sim('SGB1 PAL',21281370,312,21281370/5,e)
    sim('SGB2 NTSC',21477272,262,20971520/5,e)
