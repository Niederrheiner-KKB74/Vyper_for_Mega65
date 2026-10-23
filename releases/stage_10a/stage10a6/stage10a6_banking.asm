// CPU $C000 ROM mapping can hide the persistent bridge. Low-RAM gates keep
// the original BASIC D030 value and restore it only after leaving bridge code.
*=$7900 "Stage6b1 ROMC-safe phase gates"
.namespace menubank {
load:
    sei // No KERNAL IRQ may run while its ROMC bank is disabled.
    lda $d030
    sta original
    and #$df
    sta $d030
    jsr $cb00 // Configure filename/count only, no KERNAL calls in bridge.
    lda original
    sta $d030
    cli
    jsr M_SEQ_LOAD // Original ROM mapping + IRQs, exactly as stable loader.
    sei
    lda original
    and #$df
    sta $d030
    jsr $cb15 // Verify/copy asset with IRQ masked, no open channels.
    lda original
    sta $d030
    rts // Caller enables IRQs only after returning to its low-RAM code.
enter:
    lda $d030
    sta original // after title restore: preserve exact BASIC bits, including CRAM2K
    and #$df
    sta $d030
    jmp $cb12
restore:
    jsr $cb0f
    jsr M_RESTORE_VIDEO
    lda $d030
    and #$df
    sta $d030
    rts
finish:
    lda original
    sta $d030
    cli
    rts
.label original=$31f0
.if (*>$7951) { .error "ROMC gates overlap aimed shot code" }
}
