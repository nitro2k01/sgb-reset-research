# 2. Run 2, and timing limits for a reimplemented boot ROM

## 2.1 What run 2 checks

Run 2 is `$B0EC → $B107 → $B119`, byte-identical in v1.0 (+3 address offset),
v1.1, v1.2 and SGB2:

1. **Gate**: the boot-format parser is reset and waits for a packet whose byte 0
   is `$F1`. Anything earlier is silently discarded (not an error).
2. It stores the next five packets blindly.
3. **Comparison**: `$0601, $0611, $0621, $0631, $0641, $0651` (byte 1 of each
   packet) against `$1718–$171D`, saved from run 1 (or from the previous boot,
   after an SNES reset). Any mismatch sets `$02FA` → error state, GB held in
   reset.

Nothing else is checked in run 2: not the logo, flags, title, packet command
bytes, nor the sums against the data. The SGB flag, logo result and palette
selection all come from run 1, and run 2 does not update the saved sums. A
cartridge can present a completely different header in run 2 as long as the
six byte-1 values match.

## 2.2 Minimum gap between packets

Measured with a parametric test boot ROM ([`harness/emu/mkboot2.py`](../harness/emu/mkboot2.py))
and an ICD2 modelled as a single packet buffer that logs overruns.

In both runs the SNES sits in a tight polling loop with interrupts, NMI and HDMA
off. From packet completion to the SNES having read `$700F` takes ~2,600 master
clocks (hand count and emulator agree). The code is identical in every
revision, so only the master clock differs:

| | Packet complete → `$700F` read (max) | Stock gap (4 GB frames) |
|---|---|---|
| v1.0 / v1.1 / v1.2 NTSC | 0.122 ms | 65.4 ms |
| v1.1 / v1.2 PAL | 0.123 ms | 66.0 ms |
| SGB2 (NTSC only) | 0.122 ms | 67.0 ms |
| v1.0 PAL | n/a (GB never released) | – |

- **No gap at all** (next reset pulse right after the stop bit): all 12 packets
  read correctly in every configuration. Sending one packet with stock bit
  timing takes ~2.7 ms, so the next can't finish before the SNES has emptied
  the buffer.
- **If the ICD2 writes incoming bits straight into the readable buffer**
  (unknown on hardware), the only risk is starting the next packet within
  0.12 ms. Waiting ≥ 0.125 ms removes it. Recommended: ~0.25 ms (two GB lines),
  ~260× shorter than stock.
- Whether the ICD2 re-arms instantly after a stop bit is a hardware question the
  firmware can't answer.

## 2.3 The tail after the 6th packet in run 1

This is the delay that actually constrains a reimplementation. The SNES resets
the GB only after its checks and after waiting for the next line-223 IRQ.
Sweeping packet 6's arrival over more than a frame:

| | Packet 6 → `$6003=$01` | Non-SGB carts (title lookup) |
|---|---|---|
| v1.0 / v1.1 / v1.2 / SGB2 NTSC | 3.98 – 20.56 ms | +0.57 ms → max 21.13 ms |
| v1.1 / v1.2 PAL | 4.02 – 23.96 ms | +0.58 ms → max 24.53 ms |

If the tail is shorter than ~21.2 ms (NTSC) / ~24.6 ms (PAL), cartridge code
starts running in run 1 and is then reset part-way. The stock ~65 ms tail
prevents that. Safe minimum with ~2 ms margin: ~23 ms NTSC, ~27 ms PAL (two GB
frames cover both).

**Run-2 tail**: no SNES-side requirement; the comparison finishes within
microseconds. The SNES starts reading commands again 140.8 ms after packet 6 on
NTSC (v1.0–v1.2), 164.7 ms on PAL, 148.0 ms on SGB2 (±1 frame by phase). With
the stock boot ROM the game starts 63–65 ms after packet 6; shortening the tail
only makes the game wait longer for its first command to be read.

A faster boot ROM saves only ~0.3–0.35 s per run; the ~1.9 s before run 1 and
the intro are paced by the SNES.

Results: [`logs/timing/timing_sweeps.txt`](../logs/timing/timing_sweeps.txt).

## 2.4 Only two runs

At most two per SNES reset; the game starts at the tail of run 2. The same
boot-ROM instance waits its 4 frames, writes `FF50` and falls through to
`$0100` — the GB is not reset again. So the game inherits the state left by the
run-2 boot ROM (registers, logo in VRAM, …).

Evidence: after run 2's `$81` (`$B0EE`) the only `$6003` writes keep bit 7 set
(`$BB7B`), and no bit-7=0 write followed run 2 in any emulator configuration
over 900 frames. Exceptions: error path, credits easter egg, SNES reset (which
restarts the two-run sequence).
