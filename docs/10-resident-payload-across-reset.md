# 10. Can a RAM-resident payload survive and re-execute across a SNES reset?

SGB2 unless noted. Context: a flashcart loads a payload (SNES-side code, via
DATA_SND + the `$0818` hook or the NMI pointer), then the cartridge is swapped
to a stock game. Physical WRAM keeps its contents across a Reset press. The
question is whether anything stored in RAM can make the firmware transfer
control to the payload after the reset, with no further SGB command — and, for
the speedrunning goal, whether a mid-run Reset can be made to boot into DMG mode
(see [09](09-sgb2-dmg-mode-lock.md)) purely from RAM state.

Short answer: **no** on both counts. A payload can persist in RAM but is never
executed, and the one data-only lever on the boot (warm vs cold) is single-use
and consumed by the first boot after the swap.

## 10.1 Every firmware control transfer through a RAM pointer

There are exactly three, and the reset code re-secures each one before the
mechanism that uses it becomes active.

| Mechanism | Instruction | RAM pointer |
|---|---|---|
| NMI (vectors `$FFEA`/`$FFFA` → `$8100`) | `$8100: jml [$00bb]` | `$00BB–$00BD`, dereferenced every frame |
| Command hooks | `jsr $0800 / $0808 / $0810 / $0818` | the four hook bytes (code run in place) |
| JUMP command | `$C72C: jml [$00b8]` | `$00B8–$00BA` |

The IRQ vector (`$FFEE`/`$FFFE`) is a flat `$B50A` in ROM — no RAM involved.

The **NMI pointer** is the one an ACE hook normally rides: the per-frame NMI
jumps through `$00BB`, so while the flashcart payload has control, writing a
pointer there makes the next frame's NMI enter the payload. It does not carry
across a reset:

Reset entry `$8104`, in order:

1. `SEI`; `STA $4200 = $00` → **NMI disabled** (second instruction of reset).
2. clear `$0000–$07FC` → `$00BB/$BC/$BD` zeroed (with the whole zero-page
   pointer area).
3. `$8160`: `$BB=$0A`, `$BC=$B5`, `$BD=0` → `$00BB` restored to `$00:B50A`
   (the ROM frame handler).
4. `$8166–$8171`: the four hooks written to `$60` (RTS).
5. only later, `$81CD` (inside `$817A`): `STA $4200 = $31` → **NMI re-enabled**.

So the NMI pointer points back into ROM before NMI is switched on, and the
hooks are RTS before any hook is called. The JUMP pointer `$00B8` is loaded in
ROM immediately before its own `jml`, so it requires the JUMP command to run at
all. No boot-time transfer is left pointing at RAM.

**A resident payload therefore never regains control after a reset without a
fresh SGB command** (JUMP, or DATA_SND installing a hook) — exactly the
interaction the scenario rules out. "Payload exists in RAM" never becomes
"payload executes."

## 10.2 The only data-only lever: the warm/cold decision, and why it is single-use

RAM content affects the boot outcome only through the warm-boot check
(`$81FE`, detailed in [09](09-sgb2-dmg-mode-lock.md)). A **cold** boot
(`$0F0D = 0`) plus L+Left held gives DMG mode. While the flashcart payload has
control you can force a cold boot by poisoning the warm-boot state: corrupt a
signature at `$7E:1700`, `$7E:66FC` or `$7E:7EFC`, or desync `$0C07` from the
palette state at `$7E:CBF0–CC2B` (or `$0C06` from `$0C00–$0C05`).

But the poison is **single-use**:

- The cold boot it triggers rewrites the three signatures (`$823B–$8248`) and
  recomputes `$0C06`/`$0C07` to match whatever `$0C00–$0C05` / `$7E:CBF0–CC2B`
  currently hold. The check never compares against a fixed expected value, so it
  only enforces self-consistency — after any cold boot the state reads warm
  again.
- That single cold boot is spent on the **first boot of the stock game after
  the swap**, not on a later Reset.
- The cartridge then never changes, so every subsequent (mid-run) Reset saves
  matching packet checksums and reads **warm**; L+Left is ignored.

Making a later Reset read cold would require re-poisoning on every boot, which
needs resident *executing* code — ruled out by 10.1.

## 10.3 Consequence for the speedrunning goal

A mid-run Reset into DMG mode is **not achievable on a stock SGB2 with a stock
game from RAM state alone**. The warm-boot design defeats both routes: the
payload cannot re-execute itself, and the one cold boot a data poison buys is
consumed immediately by the swap-in boot.

Options that do work, outside the "pure RAM" constraint:

- **Start the run in DMG mode**: hold L+Left through the first post-swap boot,
  which is cold, so the game runs in DMG mode from the start — but a later Reset
  reverts to SGB mode. Only useful if the route never resets.
- **Reseat the cartridge** before the Reset (cartridge-change → cold). Reliable
  in principle but means pulling the cart mid-run; slow and hard on the
  connector.
- **Hardware**: a device that clears a WRAM signature (or pulses the SGB's own
  GB-reset) on demand, or a flashcart that re-poisons each boot. These re-assert
  the cold condition every time and sidestep both limits above.

## 10.4 Scope

The control-flow argument (10.1) is read from the SGB2 reset code and the
vectors; it was not additionally stress-tested in the emulator here, but it
follows from the ordering of NMI-disable → pointer restore → NMI-enable and
hook→RTS → first hook call. The single-use nature of the poison (10.2) is
consistent with the `$D064`/`$823B` repair paths traced in
[09](09-sgb2-dmg-mode-lock.md). The three "options that work" in 10.3 are design
consequences, not tested procedures, and the cartridge-reseat one carries a real
risk of hardware damage.
