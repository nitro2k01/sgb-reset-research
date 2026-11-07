# 12. A Space Invaders-style stage-1 loop: what it runs, and the version check

The loop as it is in *Space Invaders* (U/S), sent by DATA_SND packets at ROM
offset `$C170`/`$C180` to `$7E:1800` and started by the JUMP packet at `$C190`
(`91 00 18 00 00 18 00`: target `$00:1800`, NMI pointer `$00:1800`):

```
1800    9C 00 17       STZ $1700
1803    9C 00 42 loop: STZ $4200          ; NMITIMEN = 0
1806    AF DB FF 00    LDA $00FFDB        ; ROM version byte (long)
180A    F0 05          BEQ v10
180C    20 ED BB       JSR $BBED          ; v1.1+
180F    80 F2          BRA loop
1811    20 F0 BB  v10: JSR $BBF0          ; v1.0
1814    80 ED          BRA loop
```

## 12.1 What `$BBED` / `$BBF0` is

Both are the same point in the firmware's packet poll routine (`$BBD9` on
v1.1/v1.2/SGB2, `$BBDC` on v1.0; v1.0's code here sits 3 bytes higher):

```
BBD9  JSR $BC59            ; menu/palette-refresh flag handshake ($0F4F -> $0F0A/$0F4E)
      LDA #$00 / BNE +5    ; constant, never taken
      LDA $02F6 / BEQ rts  ; SGB enabled? (set by the boot)
      LDA $02F0 / LSR x3 / BCS rts   ; ICON_EN bit 2 = stop receiving commands
BBED  LDA $006002 / LSR / BCC rts    ; <- entry used by the loop: packet waiting?
      LDA $02C0 / BNE more
      JSR $BC07            ; copy 16 bytes $7000 -> $0600 + 16*$02C0
      JSR $BC1E            ; first packet: cmd = byte0>>3, count = byte0&7
      RTS                  ;   (single packet -> $BC73)
more: JSR $BC07 / JSR $BC47 ; further packets; last one -> $BC73
BC73  JSR $0800            ; RAM hook
      LDA $02C2 / ASL / TAX / JMP ($8000,X)   ; command table
```

So the loop skips only the three gate checks and keeps the whole receive →
`$0800` hook → command table path. Consequences of the skipped checks:
commands are accepted even after `ICON_EN` bit 2 (which makes the stock
firmware ignore all later packets), and the `$0F4F` flag handshake doesn't run.

## 12.2 How it differs from the stock main loop

In the stock firmware the parser is one of the per-frame tasks. `$BD8E` runs
once per SNES frame (after `$BD6F` waits for the IRQ's vblank flag while copying
GB rows):

| Task | Stock | Stage-1 loop |
|---|---|---|
| packet parse (`$BBD9`) | 2× per frame (`$BAB0`, `$BAB3`) | **≥ ~220× per frame** (measured average incl. TRN waits; ≤ ~76 µs per pass) |
| GB rows → WRAM frame buffers (`$B9BE`) | continuously | only inside `*_TRN` commands |
| frame IRQ `$B50A` (VRAM upload, OAM, `$22` vblank flag) | every frame | **off** (`$4200 = 0`); the screen keeps showing the last uploaded frame |
| SNES pad → ICD2 `$6004–$6007` (`$BC7F`) | every frame | **off**, auto-joypad also off: the GB sees the last pad value forever |
| L+R menu, borders, screen saver (`$BD98`, `$BD2C`, bank `$01` tasks) | yes | no |
| SPC port flush (`$BABA`) | every frame | **no**: `SOUND` packets are accepted (`$0340–$0342` set) but never reach the SPC |
| hooks `$0808`, `$0810`, `$0818` | per frame | not called (`$0800` still is) |

So it is neither "the frame handler without delays" nor a trimmed main loop:
it is only the command receiver, polled as fast as possible, with everything
else (video, input, sound ports, menu, IRQ) stopped. The firmware's own work is
reduced to what a command handler does when called.

`*_TRN` commands still work: they call `$C58D`, which sets `$0215 = 1` (so
`$B9BE` copies rows directly instead of waiting for the IRQ near SNES line
220) and pumps `$B9BE` until the frame buffers have swapped twice, i.e. until
one complete fresh GB frame has been captured. Each TRN therefore takes 1–2
GB frames, as in the stock firmware.

Other details:

- `STZ $1700` destroys the first warm-boot signature (`A5 C3 0F F0`), so the
  next SNES reset is a **cold** boot — the stage-2 program will have
  overwritten firmware RAM, and a warm boot would trust it.
- `STZ $4200` in every pass is redundant after the first: no command handler
  writes `$4200` (the only writers are the reset code and the credits). Some
  handlers end with `CLI` (palette apply `$C4BF`, TRN wait `$C58D`, when
  `$02CA` is set), which is harmless with `$4200 = 0`.
- `JUMP` enters the payload with **DB = `$01`, D = `$0000`, P = `$36`** (8-bit
  A/X, I set) and S = `$0FF0` (measured, all four firmwares).

## 12.3 The version check

| Firmware | `$00:FFDB` | Entry needed | Taken by the loop |
|---|---|---|---|
| v1.0 | `$00` | `$BBF0` | `$BBF0` ✓ |
| v1.1 | `$01` | `$BBED` | `$BBED` ✓ |
| v1.2 | `$02` | `$BBED` | `$BBED` ✓ |
| SGB2 | `$10` | `$BBED` | `$BBED` ✓ |

Correct on all four, and the code at `$BBED` (v1.1/v1.2/SGB2) and `$BBF0`
(v1.0) is identical. Calling the other one would crash: on v1.1+ `$BBF0` is
the last operand byte of `LDA $006002` (`$00` = `BRK`).

The **long** read matters. JUMP's three-byte target sets only the program
bank (`JML [$00B8]`); it doesn't touch DB, which the firmware sets to `$01`
at reset (`$8116: LDA #$01 / PHA / PLB`) and keeps, since its absolute-addressed
tables are in bank `$01`. Measured on entry to a JUMP payload, all four
firmwares: DB = `$01`, D = `$0000`, P = `$36`, S = `$0FF0`
([`mkdbprobe.py`](../harness/emu/mkdbprobe.py)). So:

- `LDA $00FFDB` (what the game does) reads the real version byte, and DB stays
  `$01`, which the firmware routines it calls need.
- A short `LDA $FFDB` would read `$01:FFDB` = `$00` on every revision and
  always take the v1.0 branch (crash on v1.1+).
- Setting DB = `$00` to make a short read work breaks the command handlers
  (bank-`$01` tables read from bank `$00`); only DATA_SND and JUMP still work.

Emulator results (`harness/emu/mksiloop.py`: upload the loop, JUMP to it,
send PAL01–12, ATTR_*, SOUND, PAL_SET, PAL_TRN, ATTR_TRN/SET, ATRC_EN,
ICON_EN 4, DATA_SND, DATA_TRN, MLT_REQ, CHR_TRN, PCT_TRN, MASK_EN, OBJ_TRN,
PAL_PRI, SOU_TRN, then JUMP to a stub):

| Variant | v1.0 | v1.1 | v1.2 | SGB2 |
|---|---|---|---|---|
| Space Invaders' bytes (`long`) | all commands, stage 2 runs | all | all | all |
| short `LDA $FFDB` (`orig`) | all | crash on first pass | crash | crash |
| `PHK/PLB` + short read (`fixdb`) | TRN/palette commands fail | same | same | same |
