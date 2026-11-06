#!/bin/bash
# ramrun.sh tag bios rom frames [pal] [pressfile] [resets]
tag=$1; bios=$2; rom=$3; fr=$4; pal=${5:-0}; pf=$6; rs=$7
if [ "$pal" = 1 ]; then export FORCE_PAL=1; else unset FORCE_PAL; fi
[ -n "$pf" ] && export PRESSFILE=$PWD/$pf || unset PRESSFILE
[ -n "$rs" ] && export RESETS=$rs || unset RESETS
WRAMLOG=../ram/$tag.bin WRAMDUMPAT=$fr ./fe ../bsnes/bsnes_libretro.so $PWD/sys $bios $PWD/$rom $((fr+1)) 2>&1 | grep -E "end of F|RESET at|WRAM log|6003" > ../ram/$tag.log
