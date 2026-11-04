# 6. Controller polling and joypad forwarding

The SNES reads the controller once per frame and writes it to the SGB once per
frame — v1.0, v1.1, v1.2 and SGB2, NTSC and PAL — so the update rate is 60 Hz
NTSC / 50 Hz PAL. Logs: [`logs/joypad/`](../logs/joypad/).

## 6.1 Reading the controller

The main loop's frame step (`$F8FD → $FF6C → $BD8E`) calls `$8712` once per
iteration. The physical controller is latched twice per frame:

| What | When | Purpose |
|---|---|---|
| Hardware auto-read (`$4200=$31`, bit 0) | start of vblank, V=225 | Normal 16-bit read. `$CA04` waits for completion (`$4212` bit 0) and reads `$4218–$421F`. |
| Extra reads in `$CA04` | same routine | Bit 16 of each port, then `$4201=$7F`, 16 manual reads of `$4017`, `$4201=$FF` — pads 3/4 through a multitap. |
| Manual latch in `$CAE4` | ~V=13–18 of the next frame | `$4016` 0→1→0, then 8+8 reads of bit 1 on both ports. Only detects a multitap (`$0F10`). |

Before the game starts, the boot state machine also calls `$8712` every frame
from `$86CE` (intro button codes); those reads are not sent to the GB.

## 6.2 Writing to the ICD2 (`$6004–$6007`)

`$BC7F` (via `$BAA4`) runs once per frame step, after the controller read, and
converts/writes each pad (`$BD27`):

| Mode (`$02F2`, set by MLT_REQ) | Writes per frame, in order |
|---|---|
| 1 player | `$6004` |
| 2 players | `$6005`, `$6004` |
| 4 players | `$6005`, `$6006`, `$6007`, `$6004` |

| Firmware / region | Write interval | Auto-read latch → ICD2 write | Write position |
|---|---|---|---|
| v1.0, v1.2, SGB2 (NTSC) | 16.64 ms | 3.1–4.0 ms | V≈20–25 |
| v1.2 PAL | 20.00 ms | 3.1–4.0 ms | V≈282–285 |

- A press reaches the GB's joypad register ~3–4 ms after the SNES samples the
  pad; total delay from a physical press is up to one SNES frame + ~4 ms.
- Updates drift against GB frames (16.35 ms SGB1 NTSC, 16.50 PAL, 16.74 SGB2):
  some GB frames see no new value, occasionally one sees two.
- Before the first write the GB sees all buttons released: writes start in
  state `$0F/4` at frame counter 9 (~78 ms after the game starts, NTSC). Until
  then `$6004` holds the `$FF` written at run 1 (`$B924`).

## 6.3 Button mapping (`$BCDE`)

- SNES A → GB A; SNES B and Y → GB B; SNES B → GB A instead when `$0C04 ≠ 0`
  (a controller-setup option; ICON_EN bit 1 clears it). Start, Select and the
  d-pad map straight across. X, L, R are not forwarded.
- Non-standard pads (low 4 bits of `$4218` ≠ 0, e.g. a mouse): `$FF` sent for
  that player.
- While the SGB menu is open (`$0F01=1`) only Start and Select are forwarded
  (from the code; not tested).

Verified in the emulator: the 2P/4P write order, and A changing `$6004` to
`$EF` on the next write.
