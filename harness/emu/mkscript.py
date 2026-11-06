"""Builds a Game Boy test ROM that runs a script of SGB actions:
   ('wait', frames)            wait N GB frames (N <= 255; repeat for longer)
   ('pkt', bytes16)            send one 16-byte SGB packet
   ('xfer', block_index)       show 4 KiB data block on screen for a *_TRN command
Data blocks are appended after the code (each 4096 bytes).
The Nintendo logo is read from your own firmware dump (../w/sgb12.smc)."""
import sys

class Asm:
    def __init__(s, org): s.org=org; s.b=bytearray(); s.lab={}; s.fix=[]
    def pc(s): return s.org+len(s.b)
    def L(s,n): s.lab[n]=s.pc()
    def e(s,*x): s.b.extend(x)
    def jr(s,op,n): s.e(op,0); s.fix.append((len(s.b)-1,n,'r'))
    def w16(s,op,n): s.e(op,0,0); s.fix.append((len(s.b)-2,n,'a'))
    def done(s):
        for o,n,k in s.fix:
            t=s.lab[n]
            if k=='r':
                r=t-(s.org+o+1); assert -128<=r<128,(n,r); s.b[o]=r&0xff
            else: s.b[o]=t&0xff; s.b[o+1]=t>>8
        return bytes(s.b)

def build(out, script, blocks, sgbflag=0x03, title=b'RAMTEST'):
    a=Asm(0x150)
    a.e(0xf3,0x31,0xfe,0xff)                 # di; ld sp,$fffe
    a.w16(0x21,'script')                      # ld hl,script
    a.L('next'); a.e(0x2a)                    # ld a,(hl+)
    a.e(0xfe,1); a.jr(0x28,'waitf')
    a.e(0xfe,2); a.jr(0x28,'pkt')
    a.e(0xfe,3); a.jr(0x28,'vx')
    a.L('forever'); a.jr(0x18,'forever')
    # wait b frames
    a.L('waitf'); a.e(0x46,0x23)              # ld b,(hl); inc hl
    a.L('wf1'); a.e(0xf0,0x44,0xfe,0x90); a.jr(0x20,'wf1')
    a.L('wf2'); a.e(0xf0,0x44,0xfe,0x90); a.jr(0x28,'wf2')
    a.e(0x05); a.jr(0x20,'wf1'); a.w16(0xc3,'next')
    # send packet at hl (hl advances 16)
    a.L('pkt')
    a.e(0xaf,0xe0,0x00,0x3e,0x30,0xe0,0x00,0x06,0x10)
    a.L('byte'); a.e(0x1e,0x08,0x2a,0x57)
    a.L('bit'); a.e(0xcb,0x42,0x3e,0x10,0x20,0x02,0x3e,0x20,0xe0,0x00,0x3e,0x30,0xe0,0x00,0xcb,0x1a,0x1d); a.jr(0x20,'bit')
    a.e(0x05); a.jr(0x20,'byte')
    a.e(0x3e,0x20,0xe0,0x00,0x3e,0x30,0xe0,0x00)
    a.w16(0xc3,'next')
    # vram transfer: next byte = block index
    a.L('vx'); a.e(0x7e,0x23,0xe5)            # ld a,(hl); inc hl; push hl
    a.e(0x87,0x87,0x87,0x87)                  # a*=16  (block*$1000 -> high byte)
    a.w16(0x21,'blk0')                        # ld hl,blk0  (page aligned)
    a.e(0x84,0x57,0x5d)                       # add h; ld d,a; ld e,l
    a.L('vw'); a.e(0xf0,0x44,0xfe,0x90); a.jr(0x20,'vw')
    a.e(0xaf,0xe0,0x40)                       # LCD off
    a.e(0x21,0x00,0x80,0x01,0x00,0x10)        # hl=$8000 bc=$1000
    a.L('vc'); a.e(0x1a,0x13,0x22,0x0b,0x78,0xb1); a.jr(0x20,'vc')
    a.e(0x21,0x00,0x98,0x1e,0x00,0x16,13)     # hl=$9800 e=0 d=13
    a.L('vr'); a.e(0x0e,20)
    a.L('vcl'); a.e(0x73,0x23,0x1c,0x0d); a.jr(0x20,'vcl')
    a.e(0x7d,0xc6,12,0x6f); a.jr(0x30,'vnc'); a.e(0x24)
    a.L('vnc'); a.e(0x15); a.jr(0x20,'vr')
    a.e(0x3e,0xe4,0xe0,0x47,0x3e,0x91,0xe0,0x40)
    a.e(0xe1); a.w16(0xc3,'next')              # pop hl
    # script
    a.L('script')
    for st in script:
        if st[0]=='wait':
            n=st[1]
            while n>0: k=min(n,255); a.e(1,k); n-=k
        elif st[0]=='pkt': a.e(2,*bytes(st[1]).ljust(16,b'\0'))
        elif st[0]=='xfer': a.e(3,st[1])
    a.e(0)
    # align blocks to $1000
    while a.pc()%0x1000: a.e(0)
    a.L('blk0')
    code=a.done()
    rom=bytearray(32768)
    snes=open('../w/sgb12.smc','rb').read()
    rom[0x100:0x104]=bytes([0,0xc3,0x50,0x01]); rom[0x104:0x134]=snes[0xe492:0xe492+48]
    rom[0x134:0x144]=title.ljust(16,b'\0'); rom[0x146]=sgbflag; rom[0x14b]=0x33
    c=0
    for i in range(0x134,0x14d): c=(c-rom[i]-1)&0xff
    rom[0x14d]=c
    rom[0x150:0x150+len(code)]=code
    base=0x150+len(code)
    for i,blk in enumerate(blocks):
        assert base+0x1000*(i+1)<=0x8000
        rom[base+0x1000*i:base+0x1000*(i+1)]=blk
    open(out,'wb').write(rom)
    return a.lab
