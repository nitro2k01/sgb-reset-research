import sys; sys.path.insert(0,'.')
import d65
class R(d65.ROM):
    def __init__(s,data,base): s.d=data; s.base=base; s.labels={}
    def off(s,a):
        o=a-s.base
        return o if 0<=o<len(s.d) else None
f=sys.argv[1]; fo=int(sys.argv[2],16); n=int(sys.argv[3],16); base=int(sys.argv[4],16)
d=open(f,'rb').read()[fo:fo+n]
r=R(d,base)
ents=[(int(x,16),1,1) for x in sys.argv[5:]] or [(base,1,1)]
print(d65.listing(r,d65.trace(r,ents)))
