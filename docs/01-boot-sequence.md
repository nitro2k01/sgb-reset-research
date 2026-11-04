# 1. Boot sequence, header validation and SGB command handling

Addresses are bank `$00` of v1.1/v1.2 unless noted. In v1.0 most of bank 0 sits
3 bytes higher from `$8286` onwards; SGB2 uses the same addresses as v1.2 for
all the boot code. Timings come from the instrumented bsnes (see
[`harness/`](../harness/README.md)); frame counts come from the code.

## 1.1 The reset iterations

There are exactly **two runs** of the Game Boy per SNES reset. Each run collects
the same six header packets; what differs is what the SNES does with them.

| Phase | Code | `$6003` | What happens |
|---|---|---|---|
| Power-on | reset vector, `$8132` | `$01` | GB held in reset |
| **Run 1** | state `$0F/1` (`$B88F`), when its frame counter `$0102` reaches `$0B` | `$81`, then `$01` | Busy-waits in `$BE3C` for six packets and does every check. The GB is reset again ~8 ms after packet 6, so in run 1 it never leaves the boot ROM. |
| Intro animation | `$0F/2` (`$AEEB`) | held | 289 frames (SGB2 ≈ 222). Skipped on a warm reset with the same cartridge. |
| **Run 2** | `$0F/4` (`$B0B1`), first frame | `$81`, and it stays there | Collects the packets again (`$B107`) and compares only the six checksum bytes with run 1 (`$B119`). The GB then finishes the boot ROM and runs the game. |
| Error | `$0F/3` (`$B07F`) | `$01` | Bad logo or run-2 mismatch: error screen, GB held in reset until the SNES is reset. |

Run 1 does its checks in this order:

1. Collect packets (`$BE57`).
2. Warm-reset "was the cartridge changed?" check (`$BFF8`).
3. SGB enable flags (`$BE8C`).
4. Built-in palette lookup by title (`$BF56`).
5. Logo comparison (`$BEAC`).
6. Save the six checksum bytes to `$1718–$171D` (`$BFD3`).

The complete list of `$6003` writes in all four ROMs: `$8132`, `$B09D`, `$B0EE`,
`$B8A3`, `$B8B3`, `$BB8B`, `$01:8491` (plus `$08:C34E/C4A7/CE1D` in SGB2). The
only other GB resets are in the credits easter egg (GB held in reset, SNES
hangs). Game-time writes (MLT_REQ and the speed change, `$BB7B`) always keep
bit 7 set.

## 1.2 Timeline

Milliseconds after SNES power-on (emulator):

| | Run 1 release | Run 1 reset | Run 2 release | GB reaches `$0100` |
|---|---|---|---|---|
| v1.1 / v1.2 NTSC | 1945.4 | 2346.1 | 7170.1 | 7625.5 |
| v1.0 NTSC | 1978.7 | 2379.3 | 7203.4 | 7658.8 |
| SGB2 (first `$6003` write at 14.5 ms) | 1729.1 | 2146.4 | 5855.6 | 6322.0 |
| v1.2 PAL | 1995.1 | 2396.4 | 8194.2 | 8653.8 |
| v1.0 PAL | never released | – | – | – |
| v1.2 SNES reset, same cart (ms after reset) | +1912.1 | +2312.8 | +2344.8 | +2800.1 |

Inside each run:

- First packet ~65.6 ms after release (mostly the boot ROM clearing VRAM).
- Then one packet every 4 GB frames: 65.4 ms NTSC, 66.0 ms PAL, 67.0 ms SGB2.
- Packet 6 arrives ~392 ms after release.
- In run 2 the boot ROM waits 4 more frames and jumps to `$0100`, ~455 ms after release.

The ~1.9 s before run 1 is initialisation (sound-driver uploads, graphics
setup). During both busy-waits the SNES main loop is frozen. Absolute times
before run 1 depend on how accurately bsnes emulates the SPC uploads.

## 1.3 Header bytes the firmware uses

The packets carry `$104–$14F`. Packets 1–5 hold 14 header bytes each, packet 6
holds 6, and byte 1 of each packet is the 8-bit sum of its slice (computed by
the GB boot ROM).

- **Logo `$104–$133`**: all 48 bytes must match the table at `$01:E492`.
  Mismatch → error screen, GB stays in reset.
- **`$146 = $03` and `$14B = $33`**: set the SGB-enable flag `$02F6`. Decided in
  run 1 only.
- **Title `$134–$143`** (all 16 bytes, so including byte `$143`): if SGB is not
  enabled and this is a cold boot (or the cartridge changed), looked up in a
  27-entry table at `$07:F000` → built-in palette. See
  [03](03-flashcart-palettes.md).
- **The six checksum bytes**: never checked against the data. Used to compare
  run 2 with run 1 and, after an SNES reset, to detect a changed cartridge
  (treated as a cold boot: intro, palette lookup, palette reset).
- **Not used at all**: `$147–$14A`, `$14C`, `$144–$145`, the global checksum,
  and **the header checksum `$14D`** — neither the SGB boot ROM nor any of the
  firmwares checks it.

## 1.4 Re-enabling commands after a failed flag check

Not possible from the Game Boy side. `$02F6` is written only by `$BE8C`, which
runs only in run 1; while it is 0, the command handler never reads `$6002`.

Pressing the SNES Reset button is enough (no power-cycle needed): reset clears
`$0000–$07FF` (holding `$02F6` and `$02F0`) and re-runs run 1, which re-reads
the header. It only unlocks if the header presented at that boot has valid
flags.

Two other locks behave the same way:

- ICON_EN with bit 2 set (`$02F0`) stops packet reception until the next reset.
- **SGB2 only**: holding a pad value of `$22` at power-on (L or Select, plus
  Left) sets `$07FD`, which drops all commands on a cold boot (not applied on a
  warm reset with the same cartridge).

## 1.5 The two packet formats and when the switch happens

There is no mode flag; the format depends on which routine reads `$6002`.

**Boot format (`$BE57`)** — only inside the run-1 and run-2 busy-waits:

- A packet is accepted as the first only if byte 0 is exactly `$F1`; anything
  else is discarded.
- The next five are stored blindly; their command bytes and sums are not
  checked.

**Normal format (`$BBD9`)** — command = byte0 >> 3, length = byte0 & 7 (0 counts as 1):

- Called twice per frame.
- Commands `$1E` and above are dropped (that covers all header packets
  `$F1–$FB`). Commands `$1A–$1D` point to an RTS.
- Every command passes through the RAM hook `$0800` before dispatch.

**The switch**: the first normal-format poll is in state `$0F/4` when `$0102`
reaches 9 — 8 frames after the frame in which run 2's sixth packet was read
(emulator: 533 ms after run-2 release, ~78 ms after the game started). From
there it continues in `$0F/5` and then in the main loop. Between the two runs
nothing reads packets.

The ICD2 buffers only one packet, so a game that sends several packets in its
first frames will likely lose some. bsnes queues up to 64, which is not
hardware-accurate.

## 1.6 Commands sent during the boot (modified boot ROM experiments)

- **System command (MLT_REQ) before `$F1`**: read and discarded. No handler runs;
  `$6003` unchanged.
- **Same command after `$F1`**: stored as header packet #2 → logo comparison
  fails → error screen with `$02F6=0`. In general, by slot:
  - packets 2–4 overwrite logo bytes → error screen;
  - packet 4 bytes 8–15 and packet 5 bytes 2–9 are the title → palette lookup changes;
  - byte 12 of packet 5 and byte 3 of packet 6 become the SGB flags.
- **Garbage command bytes `00/89/01/00/00` in packets 2–6** with forced
  `$03`/`$33` and a wrong sum: SGB still enabled.
- **Header packets after the switch**: ignored (command `$1E`/`$1F`), except as
  the continuation of a multi-packet command, where they are taken as data.

Logs: [`logs/boot/run_bootinject_*.txt`](../logs/boot/).

## 1.7 Revision and region differences

- **v1.0** measures the frame length at reset (`$8286`; loop count ≥ `$1694`
  means PAL). On PAL it enters state `$0F/6` (a screen that never advances) and
  never releases the GB. v1.1 removed this; it is the only code change between
  v1.0 and v1.1. No other region checks exist (`$213F` reads only reset a latch).
- **v1.2** adds a game-time sprite fix copied to the `$0810` hook
  (`$07:F400` → `$0810`, 81 bytes). Boot identical to v1.1.
- **SGB2**:
  - shorter intro (~222 frames);
  - reads the pad first, so the first `$6003` write is at ~14.5 ms;
  - the `$07FD` command lock (1.4);
  - keeps `$07FD–$07FF` across resets (`$07FE`/`$07FF` hold a reset-sequence
    unlock whose purpose was not fully traced);
  - GB clock 4.194 MHz vs 4.296 MHz (SGB1 NTSC) / 4.256 MHz (SGB1 PAL), i.e.
    SNES master clock ÷ 5 on SGB1.
- **PAL**: every frame-counted delay takes 20 % longer (intro 5.8 s instead of
  4.8 s) and the GB runs slower.

Open question: the ICD2's reset state before the firmware's first `$6003`
write. bsnes assumes the GB is held in reset.
