#!/bin/bash
# run.sh bios gb frames [reset_frame] -> log (env passes through)
./fe ../bsnes/bsnes_libretro.so $PWD/sys $1 $PWD/$2 $3 ${4:--1} 2>&1 | grep -v "^\[" 
