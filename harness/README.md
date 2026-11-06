# Harness: disassembly tools and instrumented emulator

Everything here runs against **your own** firmware dumps. No ROMs, boot ROMs or
disassembly listings are stored in the repository.

## Layout

The scripts use relative paths, so keep this layout:

```
harness/
  w/          your dumps (see w/README.md)
  bsnes/      libretro/bsnes checkout with bsnes_logging.patch applied (not committed)
  emu/        libretro frontend, test-ROM generators, experiment scripts
  sb/         stand-alone SameBoy boot-ROM cycle counter
  *.py        65816 / SM83 disassemblers and helpers
```

## Static analysis

| Script | Purpose |
|---|---|
| `d65.py` | 65816 recursive disassembler with M/X flag tracking (LoROM). `python3 d65.py w/sgb12.smc 8104:1:1 ...` |
| `full.py` | Traces a firmware from the reset/NMI/IRQ vectors, the state-machine tables at `$01:E4D2` and the command table at `$00:8000`: `python3 full.py w/sgb12.smc ce00 > sgb12.asm` |
| `sm83.py` | Linear SM83 disassembler for the boot ROM: `python3 sm83.py w/boot.bin 0 100` |
| `show.py` | Prints an address range from a listing: `python3 show.py sgb12.asm be3c bf00` |
| `lin.py` | Linear 65816 disassembly of a range (for code the tracer did not reach) |
| `vdiff.py` | Address-normalised diff of two listings (revision comparison) |
| `tbl.py`, `srch.py`, `raw.py` | Dump the state tables; byte-pattern search; disassemble a raw byte range at a given base |
| `latmodel.py` | Timing model of the video pipeline and alternative upload strategies |

## Instrumented emulator

1. `git clone https://github.com/libretro/bsnes.git bsnes && cd bsnes && git checkout $(cat ../BSNES_BASE_COMMIT)`
2. `git apply ../bsnes_logging.patch && make -j$(nproc)` → `bsnes_libretro.so`
3. `cd ../emu && gcc -O1 -o fe fe.c -I../bsnes/bsnes/target-libretro -ldl`
4. `mkdir -p sys && cp ../w/sgb10.smc sys/SGB1_10.sfc && cp ../w/sgb11.smc sys/SGB1_11.sfc && cp ../w/sgb12.smc sys/SGB1_12.sfc && cp ../w/sgb12.smc sys/SGB1.sfc && cp ../w/sgb2.sfc sys/SGB2.sfc`
5. Generate test ROMs, e.g. `python3 mkgb.py ok.gb 03 33 1`, `python3 mkgb.py nosgb.gb 00 33 1`, `python3 mkgb.py badlogo.gb 03 33 0`, `python3 mkvidlat.py`
6. `./run.sh SGB1_12.sfc ok.gb 520` prints the boot timeline.

The patch adds logging only (plus a few switches); it does not change emulation.

| Environment variable | Effect |
|---|---|
| (always on) | `$6003` writes, packet completion / dequeue, GB fetch of `$0000` / `$0100`, per-frame boot state |
| `FORCE_PAL=1` | Run the SGB as a PAL console |
| `SGB_BOOT=file` | Replace the Game Boy boot ROM (for packet-injection experiments) |
| `SINGLEBUF=1` | Model the ICD2 as a single packet buffer and flag overruns (bsnes normally queues 64) |
| `LOGPULSE=1` | Log GB reset pulses (packet starts) |
| `LOGJOY=1` | Log auto-joypad latches, `$4016` strobes, `$4218` reads and `$6004–$6007` writes |
| `LOGVID=1` | Log SNES line-0 and GB frame/line events (video latency) |
| `DUMPAT=f1,f2 DUMPADDR=a,b` | Dump WRAM bytes at given frames |
| `SHOTS=f1,f2` / `VIDDUMP=1` (frontend) | Save PPM screenshots / dump one pixel column per frame |
| `PRESSSEQ=id:from:to,...` (frontend) | Hold libretro joypad button `id` on controller 1 for frames [from, to) |
| `RESETS=f1,f2` (frontend) | Press SNES Reset (WRAM kept) at the given frames |

Frontend usage: `./fe core.so <sysdir> <bios.sfc> <game.gb> <frames> [reset_frame] [button_id from to]`.

Experiments used in the docs:

| Script | Document |
|---|---|
| `mkboot.py`, `mkboot2.py`, `sweep2.py` | packet injection during boot, minimum packet gaps ([docs/02](../docs/02-boot-rom-reimplementation-timing.md)) |
| `mkborder2.py` | border reset payload test ([docs/04](../docs/04-border-reset-payload.md)) |
| `mkvidlat.py`, `vidrun.sh`, `vidlat.py` | video latency ([docs/07](../docs/07-video-pipeline-and-latency.md)) |

## SameBoy boot-ROM cycle counter (`sb/`)

Links against the SameBoy objects built inside `bsnes/bsnes/gb/Core`:

```
cd sb
C=../bsnes/bsnes/gb/Core
gcc -O1 -I$C -I../bsnes/bsnes -DGB_INTERNAL -DDISABLE_DEBUGGER -D__LIBRETRO__ -o boottime boottime.c $C/*.o -lm
./boottime ../w/boot.bin some.gb 1      # prints 8 MHz units and M-cycles until PC=$0100
python3 extract_sgb2_boot.py            # for SGB2 runs of fit.py
python3 fit.py 1 7 200                  # random headers vs. the closed-form formula
```

## WRAM usage map (doc 11)

The patched core records per-byte WRAM statistics when `WRAMLOG=<file>` and
`WRAMDUMPAT=<frame>` are set (counts, first/last frame, up to six reader and
writer PCs; 80 bytes per byte of WRAM).

1. Test ROMs: `cd emu && python3 mkcmdtest.py && python3 mkborders012.py && python3 mkjumptest.py`
   (plus `python3 mkgb.py ok.gb 03 33 1` and `badlogo.gb` as above).
2. Runs (from `emu/`, writes `../ram/<tag>.bin`/`.log`):
   `./ramrun.sh <fw>_<scenario> <fw>.sfc <rom> <frames> [pal] [pressfile] [reset_frames]`
   for `<fw>` in `SGB1_10 SGB1_11 SGB1_12 SGB2`:

   | Scenario | ROM | Frames | Extra |
   |---|---|---|---|
   | idle | ok.gb | 3000 | |
   | cmd | cmdtest.gb | 2200 | |
   | monkey | ok.gb | 21800 | `0 in_monkey.txt` |
   | saver | ok.gb | 65000 | `0 in_saver.txt` |
   | credits | ok.gb | 1100 | `0 in_credits.txt` |
   | paint | ok.gb | 6000 | `0 in_paint.txt` |
   | paintreset | ok.gb | 7500 | `0 in_paint.txt 6100` |
   | borders | borders ROM (DATA_SND payload loading borders 3–10) | 9600 | |
   | borders012 | borders012.gb | 2400 | |
   | reset | ok.gb | 1800 | `0 "" 900` |
   | badlogo | badlogo.gb | 700 | |

   PAL: `SGB1_12pal_{idle,cmd,monkey}` with `pal=1`.
3. Static references: `python3 full2.py w/sgb12.smc > sgb12_full.asm` (likewise
   for each dump; listings stay local), then
   `python3 staticram.py sgb12_full.asm ram/static_sgb12.json`.
4. `python3 ramfinal.py` (classifies, → `ram/final.pkl`), `python3 ramblk.py`
   (16-byte block map, intersection of all firmwares), `python3 ramsafe.py`
   (safe ranges, PAL check, per-firmware extras),
   `python3 ramcsv.py ../data` (per-byte CSVs).
