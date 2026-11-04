; Stock border restore payload for the SNES side of the Super Game Boy.
; Location: $00:1A00, 104 bytes. Installed with DATA_SND, activated by writing
; JMP $1A00 to the main-loop hook at $0818 (send that packet last).
; Entered via the main loop's  LDA #$04 / JSR $0818  (at $00:CEC4, same address
; in v1.0, v1.1, v1.2 and SGB2) with A/X/Y 8-bit, DB=$01, D=$0000.
; Verified in an instrumented bsnes on v1.0/v1.1/v1.2/SGB2, NTSC and PAL.
; Routines marked (copied) are called the way the firmware's own custom-border
; sequence at $01:D4C9-$01:D52A calls them; their internals were not fully traced.

        org $1A00

        cmp #$04            ; C9 04        only the per-frame call site (A=4)
        bne done            ; D0 63
        php                 ; 08
        sep #$30            ; E2 30

        lda #$60            ; A9 60        disarm: $0818 = RTS (run once)
        sta $0818           ; 8D 18 08

        lda #$01            ; A9 01
        sta $0C03           ; 8D 03 0C     border number: 1 = standard SGB frame
        sta $0C47           ; 8D 47 0C     "border currently shown"
        stz $0F0C           ; 9C 0C 0F     no custom border received
        stz $0F4B           ; 9C 4B 0F     re-arm one-time "switch to custom" latch
        stz $0F4C           ; 9C 4C 0F     no custom border pending

        lda #$E8            ; A9 E8
        sta $7EC001         ; 8F 01 C0 7E  OAM buffer: sprite 0 off-screen
        jsl $01D52B         ; 22 2B D5 01  recompute $0C06 (checksum $0C00-$0C05)
        jsl $01D546         ; 22 46 D5 01  recompute $0C07 (checksum $7E:CBF0-CC2B)

        rep #$20            ; C2 20
        lda #$8200          ; A9 00 82     parameter block $02:8200 (assumes $0F06=0)
        sta $C0             ; 85 C0
        sep #$20            ; E2 20
        lda #$02            ; A9 02
        sta $C2             ; 85 C2
        jsl $00FED8         ; 22 D8 FE 00  (copied) fade out

        jsl $00F87B         ; 22 7B F8 00  (copied) wait for / run one frame
        jsl $01DC27         ; 22 27 DC 01  (copied)
        jsl $00F8FD         ; 22 FD F8 00  (copied) one main-loop frame step
        jsl $00F87B         ; 22 7B F8 00  (copied)

        lda #$01            ; A9 01
        sta $0C48           ; 8D 48 0C     flag set by firmware before border load
        jsl $018068         ; 22 68 80 01  load border $0C03 via table $01:8071
                            ;              (SGB2 redirects to its own code in bank $88)

        rep #$20            ; C2 20
        lda #$8210          ; A9 10 82     parameter block $02:8210
        sta $C0             ; 85 C0
        sep #$20            ; E2 20
        lda #$02            ; A9 02
        sta $C2             ; 85 C2
        jsl $00FEDC         ; 22 DC FE 00  (copied) fade in

        plp                 ; 28
done:   rts                 ; 60
