# Extracts the SGB2 boot ROM array from the bsnes source tree (bsnes/sfc/coprocessor/icd/boot-roms.cpp)
# into sgb2_boot.bin, for fit.py's SGB2 runs. It differs from the SGB1 boot ROM only at $FD ($01 -> $FF).
import re
s=open('../bsnes/bsnes/sfc/coprocessor/icd/boot-roms.cpp').read()
b=bytes(int(x) for x in re.findall(r'\d+',s.split('SGB2BootROM[256] = {')[1].split('}')[0]))
assert len(b)==256
open('sgb2_boot.bin','wb').write(b)
