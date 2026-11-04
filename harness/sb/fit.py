import sys
BOOT='sgb2_boot.bin' if sys.argv[1]=='2' else '../w/boot.bin'
import random,subprocess,os,collections,sys
model=sys.argv[1] if len(sys.argv)>1 else '1'
random.seed(int(sys.argv[2]) if len(sys.argv)>2 else 7)
def packets(h):   # h = bytes $104..$14F (76 bytes)
    P=[]
    for k,cmd in enumerate([0xf1,0xf3,0xf5,0xf7,0xf9,0xfb]):
        n=14 if k<5 else 6; d=h[14*k:14*k+n]
        P.append(bytes([cmd,sum(d)&0xff])+d+bytes(16-2-n))
    return P
pc=lambda b: sum(bin(x).count('1') for x in b)
rows=[]
for i in range(int(sys.argv[3]) if len(sys.argv)>3 else 120):
    rom=bytearray(32768)
    mode=i%3
    h=bytes(random.randrange(256) for _ in range(76)) if mode==0 else bytes(random.choice([0,0xff,random.randrange(256)]) for _ in range(76))
    h=bytearray(h); h[0x147-0x104]=0; h[0x148-0x104]=0; h[0x149-0x104]=0; h=bytes(h)
    rom[0x104:0x150]=h
    open('t.gb','wb').write(rom)
    out=subprocess.run(['./boottime',BOOT,'t.gb',model],capture_output=True,text=True).stdout.split('\n')[-2].split()
    M=int(out[1]); u=int(out[0])
    P=[pc(p) for p in packets(h)]
    a=-P[0]+P[1]-P[2]+P[3]-P[4]+P[5]
    rows.append((M,u,a,P))
Ms=[r[0] for r in rows]
print('model',model,'M-cycles min',min(Ms),'max',max(Ms),'distinct',len(set(Ms)), 'units%8 set',set(r[1]%8 for r in rows))
# fit M = K + ((C + a) mod 8)
best=None
for C in range(8):
    ks=collections.Counter(M-((C+a)%8) for M,u,a,P in rows)
    K,cnt=ks.most_common(1)[0]
    if best is None or cnt>best[2]: best=(C,K,cnt)
print('fit: C=%d K=%d matches %d' % best, 'of', len(rows))
ok=0
for M,u,a,P in rows:
    S=sum(P)+sum(bin(p).count('1') for p in b'')  # P already includes cmd+checksum+data
    pred=488975+((4-S)%8)
    ok+= pred==M
print('closed form M = 488975 + ((4 - total_ones) mod 8): exact for',ok,'of',len(rows))
