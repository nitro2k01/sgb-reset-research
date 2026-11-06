# Super Game Boy reset sequencing and boot validation

Reverse-engineering notes on the SNES-side Super Game Boy firmware (SGB v1.0,
v1.1, v1.2 and SGB2) and the SGB Game Boy boot ROM: how the SNES resets the
Game Boy during startup, what it validates in the cartridge header, how SGB
commands are parsed before and after the boot, and related timing (packets,
controller, video).

Findings come from static disassembly of the firmwares plus an instrumented
bsnes/SameBoy emulator. Emulator-measured numbers are labelled as such; where
hardware behaviour can't be determined from the firmware it is called out.

## AI disclosure

Everything in this repo is produced by Claude.

## Key findings

- **Two Game Boy runs per SNES reset.** Run 1 reads the six header packets and
  does every check, then resets the GB before it leaves the boot ROM. Run 2
  re-reads the packets, compares only the six packet checksum bytes, and the
  game starts at its tail — no further reset.
- **Header usage**: logo (exact 48 bytes), `$146=$03` + `$14B=$33` (SGB
  enable), the 16-byte title (built-in palette lookup for non-SGB games), and
  the six packet sums (run-2 / cartridge-change check). The header checksum
  `$14D` is **not** checked by the boot ROM or any firmware.
- **Locks**: only an SNES reset re-evaluates the SGB flags. ICON_EN bit 2 and
  (SGB2) a power-on button combination are further locks until reset.
- **Packet formats**: during the boot busy-waits only "first byte = `$F1`" is
  enforced; packets 2–6 are stored blindly. The normal parser starts 8 frames
  after run 2's sixth packet. System commands sent mid-boot are either dropped
  or become header data.
- **v1.0 refuses to run on PAL** (frame-length check); removed in v1.1.
- **Boot ROM timing**: total duration depends on the header only mod 8
  M-cycles — closed-form formula in [08](docs/08-boot-rom-cycle-formula.md).
- **Video**: ICD2 4-row ring → WRAM double frame buffer → VRAM in vblank;
  15–42 ms pixel latency depending on line and console.

## Documents

| # | Topic |
|---|---|
| [01](docs/01-boot-sequence.md) | Reset iterations, timeline, header usage, unlocking, packet formats, boot-time command injection, revision/region differences |
| [02](docs/02-boot-rom-reimplementation-timing.md) | What run 2 checks, minimum packet gaps and tail for a reimplemented boot ROM, "only two runs" |
| [03](docs/03-flashcart-palettes.md) | Built-in palette tables (raw ROM offsets) and applying them from a flashcart loader |
| [04](docs/04-border-reset-payload.md) | Restoring the stock border via a RAM-hook payload |
| [05](docs/05-free-memory-notes.md) | First free-RAM notes (superseded by 11) |
| [06](docs/06-controller-polling.md) | Controller polling rate and joypad forwarding to the ICD2 |
| [07](docs/07-video-pipeline-and-latency.md) | ICD2 → VRAM pipeline, buffering, latency, racing-the-beam analysis |
| [08](docs/08-boot-rom-cycle-formula.md) | Closed-form boot ROM cycle count as a function of header contents |
| [09](docs/09-sgb2-dmg-mode-lock.md) | SGB2 L+Left "DMG mode" lock, warm-boot detection, and why it is ignored after Reset |
| [10](docs/10-resident-payload-across-reset.md) | Whether a RAM-resident payload can survive and re-execute across a SNES reset (and the mid-run DMG-mode goal) |
| [11](docs/11-wram-map-for-snes-payloads.md) | Measured WRAM map for uploading SNES programs with DATA_SND/DATA_TRN + JUMP, all firmwares; JUMP/IRQ/NMI rules; SGB1 ATTR_BLK overrun |

## Repository contents

- `docs/` — the write-ups above.
- `data/` — built-in palette title table and colour table as CSV;
  `wram_usage_<fw>.csv`, the per-byte WRAM usage classes behind doc 11.
- `payloads/` — border reset payload (assembly + DATA_SND packets).
- `harness/` — disassemblers, tracers, the bsnes logging patch, libretro
  frontend, test-ROM generators, the SameBoy cycle counter, and analysis
  scripts. See [harness/README.md](harness/README.md).
- `logs/` — emulator logs referenced by the docs.

No Nintendo ROMs, boot ROMs or disassembly listings are included. The tools
regenerate listings from your own dumps placed in `harness/w/`.
