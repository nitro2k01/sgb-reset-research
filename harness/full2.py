import sys; sys.path.insert(0,'.')
from d65 import ROM, trace, listing
r=ROM(sys.argv[1])
ents={(0x8104,1,1),(0x8100,1,1),(r.rw(0xffee),1,1),(0xce00,1,1)}
for s in range(0x10):
    p=r.rw(0x1e4d2+2*s)|0x10000
    if (p&0xffff)<0x8000: continue
    for i in range(12):
        v=r.rl(p+3*i)
        if (v&0xffff)>=0x8000 and (v>>16)<8: ents.add((v,1,1))
for i in range(0x20): ents.add((r.rw(0x8000+2*i),1,1))
for i in range(16): ents.add((r.rw(0x1df01+2*i),1,1))      # text-script control codes ($9083)
done=set()
for it in range(8):
    code=trace(r,list(ents))
    new=0
    for a,(m,x,ln,mn,s,t) in code.items():
        if mn in ('jmp','jsr') and s.startswith('($') and s.endswith(',x)') and a not in done:
            done.add(a); tb=(a&0xff0000)|int(s[2:6],16)
            for i in range(64):
                if r.rb(tb+2*i) is None or r.rb(tb+2*i+1) is None: break
                v=r.rw(tb+2*i)
                if v<0x8000: break
                e=((a&0xff0000)|v,m,x)
                if e not in ents: ents.add(e); new+=1
    if not new: break
print(listing(r,code))
