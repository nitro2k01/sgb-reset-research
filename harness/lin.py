import sys; sys.path.insert(0,'.')
from d65 import ROM, decode
r=ROM(sys.argv[1]); a=int(sys.argv[2],16); e=int(sys.argv[3],16); m=x=1
if len(sys.argv)>4: m=int(sys.argv[4]); x=int(sys.argv[5])
while a<e:
    op,mn,md,ln,v,s,t=decode(r,a,m,x)
    print(f'{a>>16:02x}:{a&0xffff:04x} {"M" if m else "m"}{"X" if x else "x"} {" ".join("%02x"%r.rb(a+i) for i in range(ln)):12s} {mn} {s}')
    if mn=='rep': m=0 if v&0x20 else m; x=0 if v&0x10 else x
    if mn=='sep': m=1 if v&0x20 else m; x=1 if v&0x10 else x
    a+=ln
