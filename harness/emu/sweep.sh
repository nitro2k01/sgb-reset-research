#!/bin/bash
# sweep.sh bios cart pal(0/1) frames
bios=$1; cart=$2; pal=$3; fr=$4
for gap in $(seq 0 17 544); do
  python3 -I mkboot2.py /tmp/claude-0/-home-claude/9b65dac0-328a-5ecb-b0b0-20b7a40f033d/scratchpad/emu/sw_$$.bin $cart $gap 0
  if [ $pal = 1 ]; then export FORCE_PAL=1; else unset FORCE_PAL; fi
  SINGLEBUF=1 SGB_BOOT=$PWD/sw_$$.bin ./fe ../bsnes/bsnes_libretro.so $PWD/sys $bios $PWD/$cart $fr 2>&1 | python3 -I -c "
import sys,re
t6=None;res=None;over=0;lat=[];entry=None
for l in sys.stdin:
    m=re.match(r'\s*([\d.]+)ms',l)
    if not m: continue
    t=float(m.group(1))
    if 'OVERRUN' in l: over+=1
    if 'finished reading' in l: lat.append(float(l.split(': ')[1].split()[0]))
    if 'packet complete: fb' in l and t6 is None: t6=t
    if 'cartridge entry' in l and entry is None and res is None: entry=t
    if t6 and '6003 = 01' in l and res is None: res=t-t6
print('$gap', f'react={res:.3f}ms' if res else 'react=NA', 'maxread=%.3f'%max(lat) if lat else '', 'overruns=%d'%over, f'cart_ran_in_run1_after={entry-t6:.3f}ms' if entry and t6 else '')
"
done
