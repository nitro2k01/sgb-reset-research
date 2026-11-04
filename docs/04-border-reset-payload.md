# 4. Resetting the stock SGB border

There is no single variable or `JUMP` target that does this; a small payload
in RAM is needed. The one below restores the stock border on v1.0, v1.1, v1.2
and SGB2, NTSC and PAL. In every case the final screen was pixel-identical to a
run where no custom border was ever loaded.

Files: [`payloads/border_reset.asm`](../payloads/border_reset.asm),
[`payloads/border_reset_packets.txt`](../payloads/border_reset_packets.txt),
test generator [`harness/emu/mkborder2.py`](../harness/emu/mkborder2.py).

## 4.1 Why a variable alone isn't enough

- **Border number `$0C03`**: 0 = custom (game's PCT_TRN), 1 = standard SGB
  frame, 2–9 = the menu's other frames, `$0A` = special. Each has its own
  loader in the table at `$01:8071`, called through `JSL $01:8068`.
- **PCT_TRN sets three flags**: `$0F0C` (custom border exists), `$0F4C` (new
  custom border waiting to be drawn), `$0F04` (colours need updating).
- **`$0F4B` is a one-time latch**: the main loop (`$01:D4A8`) switches border
  1 → 0 only while `$0F4B` is 0, then sets it. Leave it set and the next game's
  custom border won't appear automatically.
- **Nothing redraws a stock border when the variables change** — the main loop
  only redraws the custom border. Confirmed: with `$0C03=1` and the flags
  cleared, the screen stayed on the custom border.
- **The menu's border routine `$DEA6`** isn't usable: it leaves the menu's
  screen layout on screen.

## 4.2 Why not `JUMP`

The `JUMP` handler (`$C70D`) disables interrupts and jumps out from deep inside
packet handling. The border loader waits on the frame interrupt (it would hang)
and itself processes incoming packets (it would re-enter the packet handler).

## 4.3 The `$0818` hook

The main loop runs `LDA #$04 / JSR $0818` once per frame at `$CEC4` (same
address in all four firmwares). Normally `$0818` is an RTS (v1.2's own patch
occupies `$0810–$0860` but leaves `$0818` as RTS + NOPs).

The payload lives at `$00:1A00`. Page `$1A` is not referenced by the code that
was traced and isn't cleared by the firmware; it only needs to survive until
the payload runs once (see [05](05-free-memory-notes.md) for the limits of
that claim). It:

1. returns immediately unless A = 4;
2. puts the RTS back at `$0818` (runs once);
3. sets `$0C03` and `$0C47` to 1;
4. clears `$0F0C`, `$0F4B` and `$0F4C`;
5. recomputes the firmware's checksums (used by the warm-reset check);
6. runs the firmware's own custom-border sequence but with the generic loader
   `JSL $01:8068`: fade out, wait for the frame, load border `$0C03`, fade in.

DATA_SND packets (the last one arms the hook and must be sent last):

```
79 00 1A 00 0B C9 04 D0 63 08 E2 30 A9 60 8D 18
79 0B 1A 00 0B 08 A9 01 8D 03 0C 8D 47 0C 9C 0C
79 16 1A 00 0B 0F 9C 4B 0F 9C 4C 0F A9 E8 8F 01
79 21 1A 00 0B C0 7E 22 2B D5 01 22 46 D5 01 C2
79 2C 1A 00 0B 20 A9 00 82 85 C0 E2 20 A9 02 85
79 37 1A 00 0B C2 22 D8 FE 00 22 7B F8 00 22 27
79 42 1A 00 0B DC 01 22 FD F8 00 22 7B F8 00 A9
79 4D 1A 00 0B 01 8D 48 0C 22 68 80 01 C2 20 A9
79 58 1A 00 0B 10 82 85 C0 E2 20 A9 02 85 C2 22
79 63 1A 00 05 DC FE 00 28 60
79 18 08 00 03 4C 00 1A          ; $0818 = JMP $1A00
```

## 4.4 Assembly

See [`payloads/border_reset.asm`](../payloads/border_reset.asm) for the
annotated listing. Two simplifications versus the firmware sequence:

- **Fade-out pointer**: the firmware uses `$8210` instead of `$8200` when
  `$0F06 ≠ 0`. The payload hard-codes `$8200` (normal gameplay value
  `$0F06 = 0`).
- **Skipped menu step**: the firmware also calls `$00:DFA7` when `$0C4F = 1`
  (a menu is open). Omitted because the loader runs with no menu open
  (`$0C4F = $FF`).

## 4.5 Notes

- SGB2 shows its own default frame (its border loader is redirected into bank
  `$88`); that is the stock border for that unit.
- The "Super" logo colour animation plays again, as after power-on, and settles
  after a second or two.
- Wait ~1 s after the last packet before sending palette commands or resetting
  the GB (fade out/in takes several frames; packets sent meanwhile are handled
  mid-sequence). Do the border reset first, then the palettes from
  [03](03-flashcart-palettes.md).
- With `$0F4B` cleared, the next game's custom border should appear
  automatically, as after power-on. This follows from the main-loop code but
  was not tested with a second border.
- The test simulated the custom border by writing the flags with DATA_SND (no
  real PCT_TRN); the restore path itself is what was checked.
