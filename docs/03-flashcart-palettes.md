# 3. Built-in palettes for a flashcart loader

The firmware does not use a checksum or hash to pick these palettes. It
compares the game's full 16-byte title (`$134–$143`) exactly against a table.
Both tables are at the same file offsets in v1.0, v1.1, v1.2 and SGB2, and their
contents are identical.

## 3.1 Table locations (raw file offsets)

**Title table: `0x3F000`** (SNES `$07:F000`)

- 17-byte entries: 16 title bytes from `$134–$143`, then 1 palette number.
- 27 entries; terminated by `FF FF` at `0x3F1CB`.
- Exact match over all 16 bytes, including zero padding and byte `$143` — a
  CGB-flagged re-release (e.g. Link's Awakening DX) does not match its DMG entry.
- Used only when the game has no SGB flags (`$146 ≠ $03` or `$14B ≠ $33`) and on
  a cold boot (or after a cartridge change).

**Colour table: `0x10000`** (SNES `$02:8000`)

- 8-byte entries: four little-endian BGR555 colours, lightest to darkest.
- Offset for palette `n` = `0x10000 + (n−1)*8`.
- Menu name: group `((n−1)>>3)+1`, letter `"ABCDEFGH"[(n−1)&7]` (n=17 → 3-A).

Non-SGB games not in the table get **1-A** (`67BF 265B 10B5 2866`). SGB games
also see 1-A until they send their own palette.

Full data: [`data/builtin_palette_titles.csv`](../data/builtin_palette_titles.csv)
and [`data/builtin_palettes.csv`](../data/builtin_palettes.csv).

| Title | Palette | Colours 0–3 (BGR555) |
|---|---|---|
| `ZELDA` | 1-E | 5B7F 3F0F 222D 10EB |
| `SUPER MARIOLAND` | 1-F | 7FBB 2A3C 0015 0900 |
| `MARIOLAND2` | 3-D | 5FFE 3EBC 0321 0000 |
| `SUPERMARIOLAND3` | 1-B | 637B 3AD9 0956 0000 |
| `KIRBY DREAM LAND` (16 chars) | 2-C | 7F1F 463D 74CF 4CA5 |
| `HOSHINOKA-BI` | 2-C | 7F1F 463D 74CF 4CA5 |
| `KIRBY'S PINBALL` | 1-C | 7F1F 2A7D 30F3 4CE7 |
| `YOSSY NO TAMAGO` | 2-D | 53FF 03E0 00DF 2800 |
| `MARIO & YOSHI` | 2-D | 53FF 03E0 00DF 2800 |
| `YOSSY NO COOKIE` | 1-D | 57FF 2618 001F 006A |
| `YOSHI'S COOKIE` | 1-D | 57FF 2618 001F 006A |
| `DR.MARIO` | 3-B | 637B 121C 0140 0840 |
| `TETRIS` | 3-A | 4F5F 630E 159F 3126 |
| `YAKUMAN` | 3-C | 66BC 3FFF 7EE0 2C84 |
| `METROID2` | 4-G | 0F96 2C97 0045 3200 |
| `KAERUNOTAMENI` | 2-A | 533E 2638 01E5 0000 |
| `GOLF` | 3-H | 53FC 1F2F 0E29 0061 |
| `ALLEY WAY` | 3-F | 65EF 7DBF 035F 2108 |
| `BASEBALL` | 2-G | 1EED 215C 42FC 0060 |
| `TENNIS` | 3-G | 2B6C 7FFF 1CD9 0007 |
| `F1RACE` | 4-F | 6B57 6E1B 5010 0007 |
| `KID ICARUS` | 2-F | 7FFA 2A5F 0014 0003 |
| `BALL\xF4\xF4N KID` (raw `F4 F4`) | 1-A | 67BF 265B 10B5 2866 |
| `QIX` | 4-A | 36BE 7EAF 681A 3C00 |
| `SOLARSTRIKER` | 1-G | 2800 7680 01EF 2FFF |
| `X` | 4-D | 5FFF 6732 3DA9 2481 |
| `GBWARS` | 3-E | 63FF 36DC 11F6 392A |

All titles zero-padded to 16 bytes unless noted.

## 3.2 Setting it with SGB commands

Internally the firmware points all four palette slots at a built-in palette
numbered `$2C0+(n−1)`. PAL_SET can't reach those (0–511 only, the PAL_TRN
area), so send the colours directly:

1. **PAL01 and PAL23 with the same four colours**, so all four palettes match
   whatever the attribute map says.
   - PAL01: `01 c0lo c0hi c1lo c1hi c2lo c2hi c3lo c3hi c1lo c1hi c2lo c2hi c3lo c3hi 00`
   - PAL23: same with first byte `09`.
   - Tetris (3-A): `01 5F 4F 0E 63 9F 15 26 31 0E 63 9F 15 26 31 00` and
     `09 5F 4F 0E 63 9F 15 26 31 0E 63 9F 15 26 31 00`.
2. If the loader changed the attribute map, also send ATTR_BLK covering the
   whole screen with palette 0 (or ATTR_SET).

**Restore everything else the loader changed** — the SNES side doesn't notice
the GB reset: MASK_EN 0, MLT_REQ 0, the border, sound settings; never set
ICON_EN bit 2.

Side effects of using commands instead of the firmware's own path:

- The first palette command switches the firmware to "game supplies its own
  palette": it moves the built-in selection to `$0F4A` and clears `$0C05`
  (`$C058`). The SGB menu's palette picker still overrides it.
- On hardware the auto-palette is chosen at power-on; here it appears when the
  loader sends it (brief moment with the previous palette).

Writing `$0C05` with DATA_SND is not recommended: it is covered by the
warm-reset checksum at `$0C06`, and the code that applies changes runs inside
the menu logic.
