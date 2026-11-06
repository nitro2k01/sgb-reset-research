# Stores DB, D, P, S and the stack at the moment JUMP enters the payload into $7E:1A90.. ; then loops.
import mkscript
P=lambda *b: ('pkt',bytes(b)); W=lambda n: ('wait',n)
def dsnd(addr,data):
    out=[]
    for i in range(0,len(data),11):
        ch=data[i:i+11]; a=addr+i
        out+=[P(0x79,a&0xff,(a>>8)&0xff,a>>16,len(ch),*ch),W(2)]
    return out
probe=bytes([0x08,                      # php
             0x8b,                      # phb
             0xe2,0x20,                 # sep #$20
             0x68, 0x8f,0x90,0x1a,0x7e, # pla (DB) -> $1A90
             0x68, 0x8f,0x91,0x1a,0x7e, # pla (P)  -> $1A91
             0xc2,0x20, 0x3b, 0x8f,0x92,0x1a,0x7e,   # rep #$20; tsc -> $1A92/93
             0x7b, 0x8f,0x94,0x1a,0x7e,              # tdc -> $1A94/95
             0xe2,0x20, 0x80,0xfe])
s=[W(255),W(45)]+dsnd(0x7e1800,probe)+[P(0x91,0x00,0x18,0x00,0,0,0),W(60)]
mkscript.build('dbprobe.gb',s,[])
