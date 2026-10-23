// Issue #39: B presentation with last submitted signed ENTRY position handoff.
.const TEST_VARIANT=2 // Confirmed B2: ENTRY only, original Y minus 16
*=$7700 "Isolated Debut Y projection and private state"
.namespace ygeometry {
clear:
    ldx #21
    lda #0
!loop:
    sta projected,x
    sta last_valid,x
    dex
    bpl !loop-
    rts
restore:
    ldx #21
!loop:
    lda projected,x
    beq !next+
    lda #0
    sta projected,x
    lda game.c_es,x
    cmp #2
    bne !next+ // An explosion retains its visible hit coordinate.
    lda entry.e_phase,x
    cmp #1
    bne !next+
    lda logical_lo,x
    sta entry.e_ylo,x
    sta s2i_y,x
    lda logical_hi,x
    sta entry.e_yhi,x
!next:
    dex
    bpl !loop-
    rts
postframe:
    jsr attack.a_postframe // Selection/drift operate on original coordinates.
    ldx #21
!loop:
    lda game.c_es,x
    cmp #2
    bne !next+
    lda entry.e_phase,x
    cmp #1
    bne !next+
    lda entry.e_ylo,x
    sta logical_lo,x
    lda entry.e_yhi,x
    sta logical_hi,x
    tay
    lda logical_lo,x
    jsr transform
    sta entry.e_ylo,x
    sta s2i_y,x
    tya
    sta entry.e_yhi,x
    lda entry.e_xlo,x
    sta last_xlo,x
    lda entry.e_xhi,x
    sta last_xhi,x
    lda entry.e_ylo,x
    sta last_ylo,x
    lda entry.e_yhi,x
    sta last_yhi,x
    lda #1
    sta last_valid,x
    sta projected,x
!next:
    dex
    bpl !loop-
    rts
// Called only after the final original ENTRY byte has been consumed.
// Preserve its timing/cursor; publish the preceding submitted position.
finish_entry:
    lda last_valid,x
    beq !fallback+
    lda last_xlo,x
    sta entry.e_xlo,x
    lda last_xhi,x
    sta entry.e_xhi,x
    lda last_ylo,x
    sta entry.e_ylo,x
    lda last_yhi,x
    sta entry.e_yhi,x
    rts
!fallback:
    lda entry.e_ylo,x
    ldy entry.e_yhi,x
    jsr transform
    sta entry.e_ylo,x
    tya
    sta entry.e_yhi,x
    rts
// Signed 16-bit input A/Y, output A/Y, X preserved. C = floor(Y*25/29).
transform:
.if (TEST_VARIANT==1) {
    rts
} else .if (TEST_VARIANT==2) {
    sta value
    sty value+1
    sec
    sbc #16
    sta value
    tya
    sbc #0
    tay
    lda value
    rts
} else {
    sta value
    sty value+1
    sty negative
    tya
    bpl !positive+
    sec
    lda #0
    sbc value
    sta value
    lda #0
    sbc value+1
    sta value+1
!positive:
    lda #0
    sta product
    sta product+1
    sta product+2
    sta remainder
    lda #25
    sta counter
!multiply:
    clc
    lda product
    adc value
    sta product
    lda product+1
    adc value+1
    sta product+1
    lda product+2
    adc #0
    sta product+2
    dec counter
    bne !multiply-
    lda #24
    sta counter
!divide:
    asl product
    rol product+1
    rol product+2
    rol remainder
    lda remainder
    cmp #29
    bcc !bit+
    sbc #29
    sta remainder
    inc product
!bit:
    dec counter
    bne !divide-
    lda negative
    bpl !done+
    lda remainder
    beq !negate+
    inc product
    bne !negate+
    inc product+1
!negate:
    sec
    lda #0
    sbc product
    sta product
    lda #0
    sbc product+1
    sta product+1
!done:
    ldy product+1
    lda product
    rts
}
value: .word 0
product: .fill 3,0
negative: .byte 0
remainder: .byte 0
counter: .byte 0
logical_lo: .fill 22,0
logical_hi: .fill 22,0
projected: .fill 22,0
last_valid: .fill 22,0
last_xlo: .fill 22,0
last_xhi: .fill 22,0
last_ylo: .fill 22,0
last_yhi: .fill 22,0
.if (* > $7951) { .error "Debut projection overlaps aimed shot initialization" }
}
