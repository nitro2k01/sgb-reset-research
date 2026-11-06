# 9. SGB2 "DMG mode" (L+Left at power-on) and why it fails after a reset

SGB2 only. Addresses are SGB2 (bank `$88` code exists only in SGB2).

## 9.1 What the combination does

At every reset, before anything else, the SGB2 firmware jumps to `$88:C3D7`:

1. forced blank, enable auto-joypad (`$4200=$01`), wait for the next auto-read;
2. read `($4218 & $F0) | $4219` and compare with `$22`;
3. equal → `$07FD = 1`, otherwise `$07FD = 0`.

`$22` is not a unique button set, because the high nibble of `$4218`
(A, X, L, R) and all of `$4219` (B, Y, Select, Start, Up, Down, Left, Right) are
ORed together:

| Held on controller 1 | Value | Result |
|---|---|---|
| L + Left | `$20 \| $02` | lock |
| Select + Left | `$20 \| $02` | lock (alias) |
| L + Select + Left | `$22` | lock |
| anything else (any extra button) | ≠ `$22` | no lock |

The buttons must already be held when the first auto-joypad read after the
reset completes (within about one frame of power-on / releasing reset).

`$07FD` is checked in the command dispatcher (`$00:AF3C`, reached from the
`$0800` hook for every SGB command):

```
AF3C  LDA $0F0D     ; warm-boot flag
      BNE dispatch  ; warm boot: always execute
      LDA $07FD
      BEQ dispatch
      RTS           ; cold boot + combo: drop the command
```

So the lock does not change how the Game Boy is booted, the header checks, the
border or the palette. Every SGB command is received but not executed. Games
detect the SGB with MLT_REQ and then reading the joypad ID; because MLT_REQ is
dropped, the game sees a plain Game Boy and runs in its DMG mode. The SGB2
border and the menu (palette selection etc.) still work.

**Verified in the emulator** with a test cartridge that sends MLT_REQ at start:

| Experiment | `$07FD` | `$0F0D` | `$02F2` (MLT mode) | Commands |
|---|---|---|---|---|
| normal power-on | 0 | 0 | 3 | executed |
| power-on holding L+Left | 1 | 0 | 0 | dropped |
| power-on holding Select+Left | 1 | 0 | 0 | dropped |
| normal boot, then Reset holding L+Left | 1 | 1 | 3 | executed |

## 9.2 Why it is ignored after the Reset button

The lock only applies when `$0F0D` (warm-boot flag) is 0. `$0F0D` is decided at
every reset by `$81FE`; the boot counts as warm (`$0F0D = 1`) only if **all** of
these hold:

- the signature `A5 C3 0F F0` is intact at `$7E:1700`, `$7E:66FC` and `$7E:7EFC`
  (rewritten right after the check);
- `$0C06` = 8-bit sum of `$0C00–$0C05` (border/palette/settings variables);
- `$0C07` = 8-bit sum of `$7E:CBF0–$7E:CC2B` (palette slot numbers and related
  colour state).

The reset clears only `$0000–$07FC` and `$0F00–$16FF`, so after a normal boot
all of this survives a Reset press and the boot is warm. `$07FD` is re-sampled
on every reset, but the dispatcher ignores it on a warm boot.

The only other place `$0F0D` is cleared is the cartridge-change check in run 1
(`$BFF8 → $C00C`): if the six packet checksums differ from the ones saved at
`$1718–$171D` by the previous boot, the boot is treated as cold.

## 9.3 Can a Reset press be turned into a cold boot with a stock cartridge?

No controller-only method was found.

- **Button combinations at reset**: the reset code reads the pad only for
  `$07FD` (and SGB2's `$07FE` reset-sequence unlock); nothing a button can do
  affects `$0F0D`. Tested: Reset with L+Left held → warm, commands executed.
- **Firmware features that might break the checks**: `$0C06` is recomputed
  every main-loop frame (`$CEFC`), and all traced writers of `$7E:CBF0–CC2B`
  recompute `$0C07` except the warm-boot path at `$D064` (see below). No traced code writes near the three signatures. Tested in
  the emulator, all still warm afterwards:
  - the credits easter egg (R R R L L L R R R R R R R), then Reset;
  - SGB palette commands from the game, then two Resets;
  - choosing a different built-in palette in the SGB menu after the game sent
    its own palette, then two Resets (the most promising candidate on paper:
    the main-loop init at `$D064` rewrites the palette slots without
    recomputing `$0C07` on a warm boot — but the checksum was recomputed before
    the next reset).
- **Cartridge-change detection** (from the code, not tested): make the previous
  boot save different packet checksums, then reset with the real cartridge.
  E.g. remove the Game Boy cartridge, press Reset (no cartridge → `$FF` header →
  error screen, GB held in reset, checksums from the `$FF` header saved),
  insert the cartridge, then press Reset holding L+Left. Run 1 sees different
  checksums, clears `$0F0D`, and the lock applies. This means inserting and
  removing a cartridge with the console powered, which risks damage; it is not
  recommended.
- **Holding Reset for a long time** (untested hypothesis): whether the S-CPU
  keeps refreshing WRAM while reset is held is not determined here. If it does
  not, a long enough hold would let the signatures decay and produce a cold
  boot. This needs a hardware test (and an emulator would not show it).

A power cycle remains the reliable way.
