# 7. Video pipeline: ICD2 → WRAM → VRAM, and latency

Measured end to end with a test ROM ([`harness/emu/mkvidlat.py`](../harness/emu/mkvidlat.py))
that cycles the whole screen through four shades, one per GB frame, while
logging GB and SNES line timing; each displayed SNES line is matched back to
its GB frame ([`vidlat.py`](../harness/emu/vidlat.py), logs in
[`logs/video/`](../logs/video/)). The timing model
[`harness/latmodel.py`](../harness/latmodel.py) reproduces the measured ranges
to within ~0.3 ms.

## 7.1 Buffering

| Stage | Buffering | Code |
|---|---|---|
| **ICD2** | 4 row buffers (8 GB lines, 320 bytes each), filled in a ring by the LCD output. `$6000` reports the current row and write buffer. | hardware |
| **SNES WRAM** | **Double buffer of whole frames** at `$7E:5000` and `$7E:6800`, 5760 bytes each (18 rows × 320). | `$B9BE`, `$BA14`, `$BA84` |
| **VRAM** | single copy (tiles at word `$7000`), rewritten in full every SNES frame | IRQ `$B50A` |

1. **Collecting rows**: `$B9BE` is called from 22 places in the main loop and
   its wait loops, so it runs almost continuously. It reads `$6000` until
   stable, ignores values ≥ `$90` (GB vblank), and for each newly finished row
   selects that buffer via `$6001` and DMAs 320 bytes from `$7800` into the
   back WRAM buffer. If it falls ≥ 4 rows behind it resyncs (drops rows). Copies
   that would land at SNES lines 220–222 are deferred into the IRQ.
2. **Swapping**: when row 17 has been copied, `$BA84` swaps front/back. Row 17
   is only seen as finished when the GB starts its next frame (~1.06 ms after
   line 143), because the firmware ignores `$6000 ≥ $90` (real hardware may also
   keep reporting row `$11` during GB vblank).
3. **Uploading**: the IRQ at SNES line 223 forces blank, DMAs the whole front
   frame (5760 bytes) plus sprite data to VRAM, then re-enables display. ~34
   lines — nearly the whole NTSC vblank (lines 223–261). VRAM is writable only
   in vblank/forced blank.
4. **Display**: SNES lines 40–183 of the following frame.

No frame mixing two GB frames was observed. Rate mismatch drops/repeats frames:

| Unit | GB rate | SNES rate | Effect |
|---|---|---|---|
| SGB1 NTSC | 61.17 Hz | 60.10 Hz | ~1 GB frame dropped/s (measured 2 in 141) |
| SGB1 PAL | 60.61 Hz | 50.00 Hz | ~10.6 dropped/s (measured 30 in 171) |
| SGB2 | 59.73 Hz | 60.10 Hz | one frame repeated every ~2.7 s |

## 7.2 Latency, GB pixel → TV

For GB line *y* (t_gb = GB line time, t_s = SNES line time, N = 262 NTSC / 312 PAL):

L(y) = (154 − y)·t_gb + W + (N − 223 + 40 + y)·t_s, with W ∈ [0, one GB frame)

| | Line 0 | Line 71 | Line 143 | Measured (all lines) |
|---|---|---|---|---|
| SGB1 NTSC (v1.0–v1.2 identical) | 21.5–37.9 ms | 18.5–34.8 | 15.4–31.8 | 15.7–37.9 |
| SGB1 PAL | 24.9–41.4 | 21.9–38.3 | 18.8–35.2 | 19.0–41.3 |
| SGB2 | 22.0–38.6 | 18.7–35.4 | 15.5–32.1 | 20.4–35.1 (1.35 s capture didn't cover the slow beat) |

## 7.3 Could racing the beam help?

VRAM can only be written in vblank (or forced blank, which would black out the
border). So:

- Racing the beam inside the visible picture is impossible; HDMA can't write
  VRAM, and switching tile bases mid-frame only chooses between copies uploaded
  during vblank.
- Using an in-progress frame works only if all its remaining rows can be
  uploaded **before vblank ends**, not before the end of the frame.

Average latency top / middle / bottom (model):

| Strategy | SGB1 NTSC | SGB1 PAL | Consistent frames? |
|---|---|---|---|
| Stock (decide at line 223) | 29.7 / 26.7 / 23.6 | 33.2 / 30.1 / 27.0 | yes |
| Late start of the 34-line upload (NTSC ≈ line 227, PAL ≈ line 277) | 29.5 / 26.4 / 23.4 | 29.7 / 26.7 / 23.6 | yes |
| Pipelined in-progress frame (rows already received at 223, then each remaining row as it arrives; `$7800 → $2118` direct DMA possible) | 27.2 / 24.2 / 21.1 | 27.5 / 24.4 / 21.3 | yes |
| Tearing (always newest version of each row) | 14.1 / 16.9 / 21.5 | 17.4 / 20.3 / 24.9 | no — moving seam |

Reading row 17 as soon as `$6000` shows `$90` (if real ICD2 hardware reports
that) would save another 1.06 ms on top of any strategy.

- NTSC has almost no headroom (upload already uses ~34 of 39 blanked lines):
  late start ≈ 0.2 ms, pipelining ≈ 2.5 ms.
- PAL's 87-line vblank leaves room: late start ≈ 3.5 ms for free, pipelining ≈ 5.7 ms.
- Only tearing gives a large gain (~15 ms at the top), and none at the bottom.
