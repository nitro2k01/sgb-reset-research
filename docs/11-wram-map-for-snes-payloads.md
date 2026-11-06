# 11. WRAM map for uploading SNES programs (DATA_SND / DATA_TRN + JUMP)

Context: a Game Boy program uploads SNES code and data into WRAM with
`DATA_SND` (and/or `DATA_TRN`), then starts it with `JUMP`, as *Space
Invaders* does. The SNES program then owns the machine. This replaces the
rough notes in [05](05-free-memory-notes.md).

All four firmwares (v1.0 J, v1.1 JU, v1.2 UE, SGB2 J) were measured; v1.2 was
also run as PAL. Addresses are `$7E:xxxx`/`$7F:xxxx`; `$7E:0000–$1FFF` is also
visible as `$00:0000–$1FFF`.

## 11.1 Summary

There are two phases with different rules:

1. **Upload** (firmware still running, between packets): use only RAM the
   firmware never touches, or touches only during its own boot. The firmware
   keeps running its main loop, the player can open the SGB menu (border and
   graffiti screens use large buffers), and the game may send other commands.
2. **After `JUMP`**: the firmware is no longer running. All 128 KiB is yours,
   with three caveats (11.5): the NMI pointer at `$00:00BB–00BD`, the
   firmware IRQ, and the stack.

**Safe on all four firmwares, NTSC and PAL, whatever the player does**
(never read or written by the firmware in any test, no static code reference
found):

| Range | Size | Notes |
|---|---|---|
| `$7E:B000–$7E:BFFF` | 4096 | Best single block. SGB1 caveat: see 11.4 (ATTR_BLK overrun). |
| `$7F:E000–$7F:EFFF` | 4096 | |
| `$7E:1720–$7E:1FFF` | 2272 | Also at `$00:1720`. Keep `$1700–$171D` (warm-boot signature and saved header checksums). |
| `$7E:0861–$7E:0BFF` | 927 | v1.0/v1.1: free from `$081D` (v1.2 keeps its patch at `$0810–$0860`). Keep the hooks `$0800–$081B`. |
| `$7E:0D00–$7E:0EFF` | 512 | `$0CA0–$0CFF` was also never touched, but sits after menu tables that are indexed (`$0C62,x`, and on SGB2 `$0C63–$0C8E,x`); avoid. `$0D48` is read once during the boot (CGRAM address). |
| `$7E:F4F8–$7E:F7FF` | 776 | Gap between border buffers; never touched while loading all 11 borders. |
| `$7E:6680–$7E:66FB`, `$6700–$67FF` | 124 + 256 | After frame buffer A. `$66FC–$66FF` is a warm-boot signature. |
| `$7E:7E80–$7E:7EFB` | 124 | After frame buffer B. `$7EFC–$7EFF` is a warm-boot signature. |
| `$7E:7F80–$7E:7FFF` | 128 | After the PCT_TRN palettes. |

Total ≈ 13.0 KiB, **~10.2 KiB of it in three large blocks** (`$7E:B000`,
`$7F:E000`, `$7E:1720`).

Lower confidence (free in every run but next to indexed tables whose index
range was not proven): `$7E:C228–$7E:C4EB` (708 bytes; `$01:C676` reads
`$7E:C200+[$0C6D]`).

Not free although never touched in the tests: `$7E:C9EC–$CBEB` is a 512-byte
menu palette backup written by `$00:EABB` (code no test reached).

Firmware-specific extras (free in every run of that firmware only):

| Firmware | Extra |
|---|---|
| v1.0 | `$7F:F800–$7F:FFFF` |
| v1.1 | `$7F:F000–$7F:F7FF` |
| v1.2 | `$7F:F000–$7F:F7FF` |
| SGB2 | `$7E:DDB8–$7E:F4F7` (5952), `$7E:F800–$7E:FFFF`, `$7F:F000–$7F:FFFF` — SGB2's borders don't use these SGB1 border buffers |

## 11.2 More room during the upload, with conditions

**Boot-only RAM** — used while the SGB starts the Game Boy and plays the intro,
then never again until the next SNES reset. Usable once the game is running
(the game sends commands only after that point, so this is always true for
`DATA_SND`):

| Range | Size | Used at boot for |
|---|---|---|
| `$7E:13B0–$7E:16FF` | 848 | only the reset clear |
| `$7E:1071–$7E:11FF` | 399 | intro animation slots (`$1100–$1117`) |
| `$7E:070A–$7E:07FC` | 243 | reset clear; SGB2 keeps `$07FD–$07FF` across resets |
| `$7E:0620–$7E:06FF` | 224 | header packet buffer of the boot |
| `$7E:0380–$7E:03CF`, `$0305–$032F`, `$082C–$085F` | 80 + 43 + 52 | |

These are zeroed or rewritten by the next SNES reset. Leave
`$7E:0F00–$0FFF` alone: `$0F00–$0F4F` are variables and the stack grows down
from `$0FFF` (deepest seen: `$0FD4`; `$0F50–$0FCF` is reserve).

**Buffers owned by commands** — written only when the game sends that command.
A game that never sends it can use the buffer:

| Range | Size | Written by |
|---|---|---|
| `$7E:3000–$7E:3FFF` | 4096 | PAL_TRN |
| `$7E:4000–$7E:4FFF` | 4096 | ATTR_TRN |
| `$7E:8000–$7E:9FFF` | 8192 | CHR_TRN |
| `$7E:A000–$7E:A7FF`, `$7E:7F00–$7F7F` | 2048 + 128 | PCT_TRN (map, palettes) |

That is another 18.4 KiB, contiguous with the free block at
`$7E:B000`: if the game avoids PAL_TRN/ATTR_TRN/CHR_TRN/PCT_TRN, then
`$7E:3000–$4FFF` (8 KiB) and `$7E:8000–$9FFF` (8 KiB) are free for the upload.
`$7E:A800–$AFFF` is **not** free: it is the GB-screen map built at boot and
changed by every ATTR_* command.

**Buffers owned by the menu** — not usable during the upload, because the
player can open the menu (L+R) at any time. ICON_EN does not prevent this: its
bits (`$0F07`) are tested only by the palette icon (`$D8A9`) and two other icon
handlers (`$E0AD`, `$E317`); the graffiti handler (`$F3FD`) and the border
loader don't check it.

| Range | Used by |
|---|---|
| `$7E:2000–$2FFF`, `$7F:0000–$BFFF`, `$7E:C4E0–$C6EF` | graffiti (paint) screen: canvas `$7F:0000–$5FFF`, backup `$7F:6000–$BFFF` |
| `$7E:CC40–$F4F7`, `$7E:F800–$FFFF`, `$7F:0000–$5FFF`, `$7F:C000–$DFFF`, `$7F:F000–$FFFF` (SGB1) | border loading/decompression and border screen savers |
| `$7E:CD00–$DDBF` | menus, credits |

These become free after `JUMP`.

**Always in use while the firmware runs**: most of `$7E:0000–$03FF` (direct
page and variables, interleaved with boot-only bytes), `$0C00–$0C6F`, `$0F00–$0F4F`, `$1200–$12FF`, `$1700–$171D`,
`$7E:5000–$667F` and `$7E:6800–$7E7F` (GB frame double buffer, rewritten every
frame), `$7E:C000–$C227` (OAM and palette buffers), `$7E:CBF0–$CC3F` (palette
state). Per-byte detail: `data/wram_usage_<fw>.csv`.

## 11.3 DATA_SND and DATA_TRN behaviour

`DATA_SND` (`$0F`, handler `$C6A2` on v1.1/v1.2):

```
C6A2  LDA $0601 / STA $B0      ; dest low
      LDA $0602 / STA $B1      ; dest high
      LDA $0603 / STA $B2      ; dest bank (any bank; WRAM is $7E/$7F)
      LDA $0604 / STA $08      ; count
      LDX #0 / LDY #0
loop  LDA $0605,X / STA [$B0],Y / INX / INY / DEC $08 / BNE loop
```

- Up to **11 data bytes** per packet (bytes 5–15). The count isn't checked:
  12–255 copy whatever follows the packet in RAM (`$0610+`), and 0 copies 256.
- The 16-bit address plus `Y` carries into the bank, so a packet may cross
  `$7E:FFFF → $7F:0000`.
- Bytes land immediately; nothing is buffered or acknowledged.
- The packet parser runs twice per SNES frame and the ICD2 holds one packet, so
  one packet per GB frame is safe: ~11 bytes per frame, ~660 bytes/s. A 4 KiB
  program takes ~6 s this way.

`DATA_TRN` (`$10`, `$C6C6`) copies the 4 KiB currently on the GB screen (the
front frame buffer) to any 24-bit address in one command — ~370× fewer
packets. Use it for bulk data and `DATA_SND` for small pieces. Both were
verified writing to `$7F:E000` and `$7F:FFF0`.

## 11.4 SGB1 ATTR_BLK overrun

On SGB1 (all revisions) the ATTR_BLK fill (`$C1DE`) does not clip its
rectangle. A block whose y1 > y2 (or out-of-range coordinates) wraps the row
count and writes every second byte from the map at `$7E:A94D` up to
**`$7E:EA33`** (measured with a malformed two-packet ATTR_BLK). That overwrites
the free block at `$7E:B000` and the OAM buffer at `$7E:C000`. SGB2 replaced
the fill with a clipped version in bank `$88` (`$88:C453`), which stops at the
end of `$7E:Axxx`. So a game that sends only valid ATTR_* packets is safe.

## 11.5 After JUMP

`JUMP` (`$12`, `$C70D`):

```
C70D  $BB-$BD := bytes 4-6     ; NMI pointer, always written
      $B8-$BA := bytes 1-3     ; target
      SEI
      JML [$00B8]
```

- **Interrupts**: `SEI` is set, but `$4200` is still `$31` (H+V IRQ at line
  223, auto-joypad). The firmware never enables NMI itself (bit 7 of every
  `$4200` write is 0). Before `CLI`, write `$4200` yourself; otherwise the
  firmware's frame IRQ (`$B50A`, fixed in ROM) runs, which DMAs the GB frame to
  VRAM and touches its variables.
- **NMI**: if you enable NMI, the vector goes to `$00:8100: JML [$00BB]`, i.e.
  to the address you gave in bytes 4–6. Keep `$00:00BB–00BD` intact (it is in
  the direct page the firmware used), or point it at your handler before
  enabling NMI. A zero pointer jumps to `$00:0000`.
- **Stack**: you inherit the firmware's stack (S a few dozen bytes below
  `$0FFF`, direct page 0). Load your own S and D.
- **RAM**: everything not holding your program is free, including the frame
  buffers, the menu buffers and the whole of bank `$7F`. The SNES cartridge
  side is the SGB ROM; your code runs from WRAM.
- **Game Boy**: keeps running (`$6003` unchanged). The ICD2 registers stay
  usable if you want GB video or joypad passthrough.

Recommended layout: code at `$7E:1720–$1FFF` or `$7E:B000–$BFFF` (both
uploadable at any time), bulk data via `DATA_TRN` into `$7F:E000–$EFFF`
and, if the game avoids those commands, `$7E:3000–$4FFF` and
`$7E:8000–$9FFF`; then after `JUMP` move or decompress it anywhere.

If you need to return to the firmware later, everything in 11.2 "always in
use" plus the menu/border buffers you want to keep must be left intact; that
case was not tested.

## 11.6 Method

- **Write/read logging**: bsnes (libretro, patch in
  [`harness/bsnes_logging.patch`](../harness/bsnes_logging.patch)) records, for
  every WRAM byte, read/write counts, first/last access frame and up to six
  reading and writing PCs. DMA source/destination accesses go through the same
  path, so DMA is included.
- **Scenarios**, each on every firmware
  ([`harness/emu/`](../harness/emu/), input files `in_*.txt`):
  idle game; every SGB command including all `*_TRN` transfers, MLT_REQ and
  SOU_TRN (`mkcmdtest.py`); random controller input including the menus
  (21800 frames); screen saver (65000 frames); credits easter egg; graffiti
  screen with random painting; graffiti then Reset; loading each of the 11
  borders through `JSL $01:8068` (`mkborders012.py`, and a payload for borders
  3–10); Reset during a game; bad logo. PAL: idle, commands, random input.
- **Classification** ([`harness/ram/`](../harness/ram/)): a byte is
  *runtime* if accessed after the main loop starts in the idle run,
  *feature* if accessed after that only in some scenarios, *boot* if only
  before it, *free* if never. Writes made by DATA_SND/DATA_TRN and by the test
  payloads were excluded. The ATTR_BLK overrun found in the command test was
  excluded from the map and documented in 11.4 instead.
- **End-to-end check** (`mkjumptest.py`, v1.0, v1.2, SGB2, with random
  controller input running through the menus during the upload): DATA_SND to
  `$7F:E000`, `$7E:1720` and a program to `$7E:B000`, then JUMP. The program
  ran (writing `$4200=0` first) and no firmware code wrote to the uploaded
  bytes.
- **Static references**: all direct WRAM operands in the traced code of each
  firmware (including SGB2 bank `$88`) were collected; free bytes with a
  reference are counted as used, and indexed references next to free ranges
  were checked by hand.

Limits: pointer-based writes in code no test reached can't be found
statically; the large buffers in 11.1 have no references at all, and every
nearby indexed table was checked, but this is a measurement, not a proof. The
tests can't cover hardware differences (e.g. power-on RAM contents).
