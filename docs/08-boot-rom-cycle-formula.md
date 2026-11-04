# 8. Closed-form boot ROM duration vs. header contents

The header changes the boot time much less than the per-bit costs suggest:
every packet's variable send time is absorbed by the next wait for LY = 144,
and only its value mod 8 M-cycles carries over. Total variation ≤ 7 M-cycles
(28 clocks, ~6.5 µs).

Derived from the boot ROM's instruction timings and checked against SameBoy
(the GB core inside bsnes) run stand-alone ([`harness/sb/`](../harness/sb/)):
cycles from reset release until PC = `$0100` for 350 random headers on the SGB
and SGB2 boot ROMs plus the test ROMs — exact match every time. The SGB2 boot
ROM differs only at byte `$FD` (`LD A,$FF` vs `$01`), so its cycle count is the
same.

## 8.1 Formula

M-cycles from reset release until PC = `$0100`:

**M = 488975 + ((7 − H − S) mod 8)**

- **H** = number of 1 bits in header bytes `$0104–$014F`.
- **S** = number of 1 bits in the six checksum bytes the boot ROM sends: the
  8-bit sums of `$104–$111`, `$112–$11F`, `$120–$12D`, `$12E–$13B`,
  `$13C–$149`, `$14A–$14F`.
- Command bytes `$F1…$FB` (37 ones) and packet 6's zero padding are in the constant.

Equivalently with zero bits: **M = 488975 + ((Z + 4) mod 8)**, Z = number of
0 bits among the 768 bits sent.

**With a valid Nintendo logo** (179 ones; checksums `$70 $60 $59`, 9 ones):

**M = 488975 + ((3 − popcount(`$134–$14F`) − popcount(s₄) − popcount(s₅) − popcount(s₆)) mod 8)**

with s₄ = Σ`$12E–$13B`, s₅ = Σ`$13C–$149`, s₆ = Σ`$14A–$14F` (mod 256).

Real time = M × 4 / f_GB: ~455.34 ms SGB1 NTSC (4.2955 MHz), ~459.5 ms SGB1
PAL (4.2563 MHz), ~466.3 ms SGB2 (4.1943 MHz).

## 8.2 Derivation

1. **Packet send** (`$0089` → `CALL $00C2`): 2577 + Zᵢ M-cycles (Zᵢ = 0 bits in
   the 16-byte packet). A 1 bit costs 19 M-cycles (`JR NZ` taken), a 0 bit 20
   (`JR NZ` not taken + `LD A,$20`); 8 cycles per byte overhead; preamble 10,
   stop bit 8.
2. **`$00C2`** waits for LY = 144 four times with a fixed 1023-cycle delay after
   each match. The poll loop (`LDH A,($44) / CP $90 / JR NZ`) is 8 M-cycles, so
   each wait ends 0–7 M-cycles after LY becomes 144; call that lateness δ.
   Packet sends end around LY 23, so each wait catches the same frame.
3. **Lateness carries over**:
   - within one call the LY-read gap is 1036 and a frame is 17556 M-cycles;
     17556 − 1036 = 16520 ≡ 0 (mod 8), so δ is unchanged over the four waits;
   - between packets: δᵢ₊₁ = (δᵢ + Zᵢ₊₁ + 3630 − 17556) mod 8 = (δᵢ + Zᵢ₊₁ + 2) mod 8;
   - pre-LCD code has no data-dependent branches, so δ₁ = (const + Z₁) mod 8.
4. **Sum**: δ₆ = (const + ΣZᵢ) mod 8; after the last match the remaining code is
   fixed (1036 cycles to the return, 24 more to `$0100`).

## 8.3 Caveats

- The constant 488975 is SameBoy's. Different first-frame timing after LCD
  enable on real hardware (the line-0 quirk) could shift it; the mod-8
  dependence follows from the instruction timings and LCD period alone.
- Individual packet completion times (stop bit, when the ICD2 sees the packet)
  vary much more: packet i completes 2577 + Zᵢ M-cycles after it starts, and
  starts at a fixed LCD position + δᵢ₋₁, i.e. up to ~130 M-cycles (~30 µs) of
  header-dependent movement.
