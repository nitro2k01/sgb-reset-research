# Uploads a tiny SNES program to $7E:B000 with DATA_SND, data to $7F:E000 and $7E:1720 with DATA_SND,
# then JUMPs to it. The program disables the firmware IRQ and copies $7F:E000 -> $7E:0100 forever.
import mkscript
P=lambda *b: ('pkt',bytes(b)); W=lambda n: ('wait',n)
def dsnd(addr,data):
    out=[]
    for i in range(0,len(data),11):
        ch=data[i:i+11]; a=addr+i
        out+=[P(0x79,a&0xff,(a>>8)&0xff,a>>16,len(ch),*ch),W(2)]
    return out
prog=bytes([0xe2,0x30, 0x9c,0x00,0x42,            # sep #$30; stz $4200
            0xaf,0x00,0xe0,0x7f,                  # loop: lda $7fe000
            0x8f,0x00,0x01,0x7e,                  # sta $7e0100
            0xaf,0x20,0x17,0x7e,                  # lda $7e1720
            0x8f,0x01,0x01,0x7e,                  # sta $7e0101
            0x80,0xee])                           # bra loop
s=[W(255),W(45)]
s+=dsnd(0x7fe000,bytes([0x5a]*44))
s+=dsnd(0x7e1720,bytes([0xa5]*44))
s+=dsnd(0x7eb000,prog)
s+=[W(30), P(0x91,0x00,0xb0,0x7e,0,0,0), W(255)]
mkscript.build('jumptest.gb',s,[])
