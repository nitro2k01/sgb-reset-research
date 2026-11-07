# Space Invaders-style stage-1 loop test: upload the loop to $7E:1800 and JUMP to $00:1800,
# then send every SGB command through it, then JUMP to a stage-2 stub at $00:1900.
import random, mkscript, sys
VAR = sys.argv[1] if len(sys.argv) > 1 else 'orig'
# orig : short LDA $FFDB with the DB that JUMP leaves ($01)
# fixdb: PHK/PLB first, so LDA $FFDB reads bank $00 (but firmware code then runs with DB=$00)
# long : LDA $00FFDB (long), DB left at $01 -- byte-identical to Space Invaders' loop (ROM $C175)
FIXDB = VAR == 'fixdb'
random.seed(1)
snes=open('../w/sgb12.smc','rb').read()
rnd=bytes(random.randrange(256) for _ in range(4096))
o=7*0x8000+0x5000; n=snes[o]|snes[o+1]<<8
sou=(bytes(snes[o:o+4+n])+bytes([0,0,0x00,0x04])).ljust(4096,b'\0')
pct=bytearray(rnd)
for i in range(0,0x800,2): pct[i+1]=(pct[i+1]&0x03)|0x10
blocks=[rnd,sou,bytes(pct)]
P=lambda *b: ('pkt',bytes(b)); W=lambda n: ('wait',n); X=lambda i: ('xfer',i)
def dsnd(addr,data):
    out=[]
    for i in range(0,len(data),11):
        ch=data[i:i+11]; a=addr+i
        out+=[P(0x79,a&0xff,(a>>8)&0xff,a>>16,len(ch),*ch),W(2)]
    return out
if VAR == 'long':
    stage1=bytes([0x9c,0x00,0x17,  0x9c,0x00,0x42,  0xaf,0xdb,0xff,0x00,  0xf0,0x05,
                  0x20,0xed,0xbb,  0x80,0xf2,  0x20,0xf0,0xbb,  0x80,0xed])
else:
    stage1=(bytes([0x4b,0xab]) if FIXDB else b'')+bytes([0x9c,0x00,0x17,  0x9c,0x00,0x42,  0xad,0xdb,0xff,  0xf0,0x05,
              0x20,0xed,0xbb,  0x80,0xf3,  0x20,0xf0,0xbb,  0x80,0xee])
stage2=bytes([0xa9,0x5a, 0x8f,0x80,0x1a,0x7e, 0x80,0xfe])     # lda #$5a; sta $7e1a80; bra *
col=[0xff,0x7f, 0x1f,0x00, 0xe0,0x03, 0x00,0x7c, 0x10,0x42, 0x08,0x21, 0x00,0x00]
s=[W(255),W(45)]
s+=dsnd(0x7e1800,stage1)+dsnd(0x7e1900,stage2)
s+=[P(0x91,0x00,0x18,0x00,0,0,0), W(10)]                                      # JUMP $00:1800
for cmd in (0x01,0x09,0x11,0x19): s+= [P(cmd,*col), W(6)]
s+= [P(0x21,1, 0x07,0x12, 2,2,10,10), W(6)]
s+= [P(0x29,3, 0x85,0xa3,0x42), W(6), P(0x31,0x5b,9), W(6), P(0x39,2,3,10,0,0, 0x1b,0xe4,0x55), W(6)]
s+= [P(0x41,0x01,0x02,0x0f,0x00), W(30), P(0x41,0x80,0x80,0,0), W(10)]        # SOUND
s+= [P(0x51,1,0,2,0,3,0,4,0,0x00), W(6)]                                      # PAL_SET
s+= [X(0), P(0x59), W(12)]                                                    # PAL_TRN
s+= [X(0), P(0xa9), W(12), P(0xb1,0x05), W(6)]                                # ATTR_TRN, ATTR_SET
s+= [P(0x61,1), W(6), P(0x71,0x04), W(6)]                                     # ATRC_EN, ICON_EN 4
s+= [P(0x79,0xf0,0xff,0x7f,4,0xde,0xad,0xbe,0xef), W(6)]                      # DATA_SND (after ICON_EN bit2)
s+= [X(0), P(0x81,0x00,0xe0,0x7f), W(12)]                                     # DATA_TRN
s+= [P(0x89,1), W(30), P(0x89,0), W(10)]                                      # MLT_REQ
s+= [X(0), P(0x99,0), W(12)]                                                  # CHR_TRN
s+= [X(2), P(0xa1), W(60)]                                                    # PCT_TRN
s+= [P(0xb9,1), W(10), P(0xb9,0), W(10)]                                      # MASK_EN
s+= [X(0), P(0xc1,0x01), W(30), P(0xc1,0x00), W(10)]                          # OBJ_TRN
s+= [P(0xc9,1), W(6)]                                                         # PAL_PRI
s+= [X(1), P(0x49), W(60)]                                                    # SOU_TRN
s+= [P(0x91,0x00,0x19,0x00,0,0,0), W(255)]                                    # JUMP $00:1900
mkscript.build({'orig':'siloop.gb','fixdb':'siloop_fixdb.gb','long':'siloop_long.gb'}[VAR], s, blocks)
