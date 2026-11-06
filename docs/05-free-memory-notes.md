# 5. Free memory for payloads — what is (and isn't) known

**Superseded by [11](11-wram-map-for-snes-payloads.md)**, which has a measured
map for all firmwares. This page is the quick check that was done to pick
`$1A00` for the border payload (still inside a free range).

## What was checked

- A scan of the code reached by the tracer (banks 0 and 1 of v1.2) for direct
  references into `$0800–$1FFF`: pages `$08`, `$0C`, `$0D`, `$0F`, `$11`, `$12`,
  `$13` and `$17` are used. Nothing pointed at `$14xx–$16xx` or `$18xx–$1Fxx`.
- From the reset code:
  - stack starts at `$0FFF` and grows down;
  - a reset clears `$0000–$07FF` and `$0F00–$16FF`; `$1700–$171F` holds data
    that survives a reset (signatures, saved packet checksums);
  - `$0800/$0808/$0810/$0818` are RAM hooks (all RTS by default); v1.2's own
    patch occupies `$0810–$0860`.
- SGB2 preserves `$07FD–$07FF` across resets (the RAM clear stops at `$07FD`).
- In the emulator runs `$1A00–$1A67` survived until the payload ran.

## What it doesn't cover

- Indirect writes (pointers, indexed long writes, block moves, DMA, the WRAM
  port `$2180`).
- Untraced code: menu screens, screen savers, credits, sound code in other
  banks, SGB2's bank `$88`, and the data-transfer commands that fill large
  buffers in `$7E:xxxx`.
- High WRAM `$7E:2000–$7F:FFFF`, where most large buffers live (e.g. the frame
  buffers at `$7E:5000`/`$7E:6800`, border buffers at `$7E:8000–$AFFF`).
- Maximum stack depth.
- Revisions other than v1.2.

A dependable map would need (1) WRAM write logging with writer PC in the
emulator across all firmwares, regions and features (menus, borders, screen
saver, all commands, multiplayer, warm reset), and (2) further tracing to cover
paths a test doesn't hit.
