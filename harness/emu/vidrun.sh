#!/bin/bash
# vidrun.sh bios pal frames out
if [ "$2" = 1 ]; then export FORCE_PAL=1; else unset FORCE_PAL; fi
LOGVID=1 VIDDUMP=1 ./fe ../bsnes/bsnes_libretro.so $PWD/sys $1 $PWD/vidlat.gb $3 2>&1 | grep -E "VID F|GB VRESET|GB line 143|SNES V0" > $4
