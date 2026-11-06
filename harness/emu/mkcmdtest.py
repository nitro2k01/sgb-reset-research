# Generates cmdtest.gb: exercises every SGB command (incl. all *_TRN transfers)
import random, mkscript
random.seed(1)
snes=open('../w/sgb12.smc','rb').read()
rnd=bytes(random.randrange(256) for _ in range(4096))
# SOU_TRN block: the firmware's own boot upload ($07:D000: $9E3 bytes -> SPC $2B00, then jump $0400)
o=7*0x8000+0x5000; n=snes[o]|snes[o+1]<<8
sou=bytes(snes[o:o+4+n])+bytes([0,0,0x00,0x04]); sou=sou.ljust(4096,b'\0')
pct=bytearray(rnd); 
for i in range(0,0x800,2): pct[i+1]=(pct[i+1]&0x03)|0x10   # map entries: palette 4, tile 0-3FF
blocks=[rnd,sou,bytes(pct)]
P=lambda *b: ('pkt',bytes(b))
W=lambda n: ('wait',n)
X=lambda i: ('xfer',i)
col=[0xff,0x7f, 0x1f,0x00, 0xe0,0x03, 0x00,0x7c, 0x10,0x42, 0x08,0x21, 0x00,0x00]
s=[W(90)]
for cmd in (0x01,0x09,0x11,0x19): s+= [P(cmd,*col), W(6)]
s+= [P(0x21,1, 0x07,0x12, 2,2,10,10), W(6)]                                   # ATTR_BLK 1 set
s+= [P(0x22,3, 0x07,0x00,0,0,19,17, 0x03,0x05,1,1,5,5, 0x07), P(0,0x1b,3,3,8,8,0,0,0,0,0,0,0,0,0,0), W(6)]  # ATTR_BLK 2 packets
s+= [P(0x29,3, 0x85,0xa3,0x42), W(6)]                                         # ATTR_LIN
s+= [P(0x31,0x5b,9), W(6), P(0x31,0x24,4), W(6)]                              # ATTR_DIV
s+= [P(0x39,2,3,10,0,0, 0x1b,0xe4,0x55), W(6)]                                # ATTR_CHR
s+= [P(0x41,0x01,0x02,0x0f,0x00), W(30), P(0x41,0x80,0x80,0,0), W(10)]        # SOUND
s+= [P(0x51,1,0,2,0,3,0,4,0,0x00), W(6)]                                      # PAL_SET
s+= [X(0), P(0x59), W(12)]                                                    # PAL_TRN
s+= [P(0x51,5,0,6,0,7,0,8,0,0xc0), W(6)]                                      # PAL_SET with ATF/cancel bits
s+= [X(0), P(0xa9), W(12)]                                                    # ATTR_TRN
s+= [P(0xb1,0x05), W(6), P(0xb1,0x43), W(6)]                                  # ATTR_SET
s+= [P(0x61,1), W(6), P(0x61,0), W(6)]                                        # ATRC_EN
s+= [P(0x69,1), W(6), P(0x69,0), W(6)]                                        # TEST_EN
s+= [P(0x71,0x00), W(6)]                                                      # ICON_EN 0
s+= [P(0x79,0xf0,0xff,0x7f,4,0xde,0xad,0xbe,0xef), W(6)]                      # DATA_SND -> $7F:FFF0
s+= [X(0), P(0x81,0x00,0xe0,0x7f), W(12)]                                     # DATA_TRN -> $7F:E000
s+= [P(0x89,1), W(30), P(0x89,3), W(30), P(0x89,0), W(10)]                    # MLT_REQ
s+= [X(0), P(0x99,0), W(12), X(0), P(0x99,1), W(12)]                          # CHR_TRN both halves
s+= [X(2), P(0xa1), W(60)]                                                    # PCT_TRN
s+= [P(0xb9,1), W(10), P(0xb9,2), W(10), P(0xb9,3), W(10), P(0xb9,0), W(10)]  # MASK_EN
s+= [X(0), P(0xc1,0x01), W(30), P(0xc1,0x00), W(10)]                          # OBJ_TRN on/off
s+= [P(0xc9,1), W(6), P(0xc9,0), W(6)]                                        # PAL_PRI
s+= [X(1), P(0x49), W(60)]                                                    # SOU_TRN (stock data)
s+= [P(0x41,0x05,0x06,0x05,0x01), W(60), P(0x41,0x80,0x80,0,0)]               # SOUND after SOU_TRN
lab=mkscript.build('cmdtest.gb', s, blocks)
print('script ok, blk0 at', hex(lab['blk0']))
