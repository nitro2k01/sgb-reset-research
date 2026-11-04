import sys; sys.path.insert(0,'.')
from d65 import ROM
r=ROM(sys.argv[1])
base=int(sys.argv[2],16) if len(sys.argv)>2 else 0x1e4d2
for s in range(0x14):
    p=r.rw(base+2*s)|0x10000
    ents=[]
    if (p&0xffff)<0x8000: print(f"state {s:02x} -> {p:04x}"); continue
    for i in range(12):
        v=r.rl(p+3*i)
        if not (0x8000<= (v&0xffff)) or (v>>16)>7: break
        ents.append(f'{v:06x}')
    print(f'state {s:02x} -> {p:04x}: {" ".join(ents)}')
print('cmd table $8000:',' '.join(f'{r.rw(0x8000+2*i):04x}' for i in range(0x20)))
