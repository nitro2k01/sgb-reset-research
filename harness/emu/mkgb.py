import sys
# usage: mkgb.py out.gb sgbflag(hex) lic(hex) logo_ok(0/1) [packets: "waitframes:hexbytes" ...]
out=sys.argv[1]; sgb=int(sys.argv[2],16); lic=int(sys.argv[3],16); logo_ok=int(sys.argv[4])
pk=sys.argv[5:]
snes=open('../w/sgb12.smc','rb').read()
logo=snes[0x8000+0x6492:0x8000+0x6492+48]
rom=bytearray(32768)
rom[0x100:0x104]=bytes([0x00,0xc3,0x50,0x01])
rom[0x104:0x134]=logo if logo_ok else bytes([logo[0]^1])+logo[1:]
rom[0x134:0x144]=b'SGBTEST'.ljust(16,b'\0')
rom[0x146]=sgb; rom[0x14b]=lic
c=0
for i in range(0x134,0x14d): c=(c-rom[i]-1)&0xff
rom[0x14d]=c
code=bytearray(); labels={}; fix=[]
def emit(*b): code.extend(b)
def lab(n): labels[n]=0x150+len(code)
def jr(op,n): emit(op,0); fix.append((len(code)-1,n,'rel'))
def call(n): emit(0xcd,0,0); fix.append((len(code)-2,n,'abs'))
def ldhl(n): emit(0x21,0,0); fix.append((len(code)-2,n,'abs'))
emit(0xf3, 0x31,0xfe,0xff)          # di; ld sp,$fffe
data=[]
for i,p in enumerate(pk):
    w,hx=p.split(':'); w=int(w); b=bytes.fromhex(hx).ljust(16,b'\0')
    data.append(b)
    if w>0:
        emit(0x06,w)                 # ld b,w
        lab(f'w1_{i}'); emit(0xf0,0x44,0xfe,0x90); jr(0x20,f'w1_{i}')
        lab(f'w2_{i}'); emit(0xf0,0x44,0xfe,0x90); jr(0x28,f'w2_{i}')
        emit(0x05); jr(0x20,f'w1_{i}')
    ldhl(f'pkt{i}'); call('send')
lab('loop'); jr(0x18,'loop')
lab('send')
emit(0xaf,0xe0,0x00, 0x3e,0x30,0xe0,0x00, 0x06,0x10)
lab('byte'); emit(0x1e,0x08, 0x2a, 0x57)
lab('bit'); emit(0xcb,0x42, 0x3e,0x10); jr(0x20,'one'); emit(0x3e,0x20)
lab('one'); emit(0xe0,0x00, 0x3e,0x30, 0xe0,0x00, 0xcb,0x1a, 0x1d); jr(0x20,'bit')
emit(0x05); jr(0x20,'byte')
emit(0x3e,0x20,0xe0,0x00,0x3e,0x30,0xe0,0x00, 0xc9)
for i,b in enumerate(data): lab(f'pkt{i}'); code.extend(b)
for off,n,k in fix:
    t=labels[n]
    if k=='rel':
        r=t-(0x150+off+1); assert -128<=r<128; code[off]=r&0xff
    else: code[off]=t&0xff; code[off+1]=t>>8
rom[0x150:0x150+len(code)]=code
open(out,'wb').write(rom)
