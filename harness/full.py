import sys; sys.path.insert(0,'.')
from d65 import ROM, trace, listing
r=ROM(sys.argv[1])
ents=[(int(x,16),1,1) for x in sys.argv[2:]]
ents+=[(0x8104,1,1),(0x8100,1,1),(r.rw(0xffee),1,1)]
# state tables
st=set()
for s in range(0x10):
    p=r.rw(0x1e4d2+2*s)|0x10000
    if (p&0xffff)<0x8000: continue
    for i in range(12):
        v=r.rl(p+3*i)
        if (v&0xffff)>=0x8000 and (v>>16)<8: st.add(v)
ents+=[(v,1,1) for v in st]
ents+=[(r.rw(0x8000+2*i),1,1) for i in range(0x20)]
code=trace(r,ents)
print(listing(r,code))
