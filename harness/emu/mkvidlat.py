# Builds vidlat.gb: a Game Boy test ROM that cycles BGP $00/$55/$AA/$FF once per
# Game Boy frame (written at LY=144), used by vidrun.sh / vidlat.py to measure
# GB-pixel -> SNES-output latency. The Nintendo logo is read from your own SGB
# firmware dump (w/sgb12.smc), so no copyrighted data is stored in this repo.
snes=open('../w/sgb12.smc','rb').read(); logo=snes[0xe492:0xe492+48]
rom=bytearray(32768); rom[0x100:0x104]=bytes([0,0xc3,0x50,0x01]); rom[0x104:0x134]=logo
rom[0x134:0x144]=b'VIDLAT'.ljust(16,b'\0'); rom[0x146]=3; rom[0x14b]=0x33
c=0
for i in range(0x134,0x14d): c=(c-rom[i]-1)&0xff
rom[0x14d]=c
code=bytes([0xf3,0x31,0xfe,0xff, 0x0e,0x00,           # di; ld sp,$fffe; ld c,0
  0xf0,0x44,0xfe,0x90,0x20,0xfa,                      # wait LY==144
  0x79,0xe6,0x03,0x6f,0x26,0x02,0x7e,0xe0,0x47,       # BGP = table[c&3]
  0x0c,                                               # inc c
  0xf0,0x44,0xfe,0x90,0x28,0xfa,                      # wait LY!=144
  0x18,0xe8])                                         # loop
rom[0x150:0x150+len(code)]=code
rom[0x200:0x204]=bytes([0x00,0x55,0xaa,0xff])
open('vidlat.gb','wb').write(rom)
