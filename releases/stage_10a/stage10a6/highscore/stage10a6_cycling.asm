.import source "color_cycle.inc"
// Original Amiga COLOR02 algorithm: signed word deltas, 7 ticks/segment.
// Single parameter for WinUAE comparison; 1 retains derived PAL timing.
.const COLOR_TICK_DIVIDER=1
.if (COLOR_TICK_DIVIDER<1 || COLOR_TICK_DIVIDER>255) { .error "Cycle divider must be1..255" }
*=$3100 "Original COLOR02 cycle and private state"
cc_init:
    lda #<CC_START_WORD
    sta cc_word
    lda #>CC_START_WORD
    sta cc_word+1
    lda #CC_START_PHASE
    sta cc_phase
    lda #CC_START_LEFT
    sta cc_left
    lda #0
    sta cc_clock
    rts
cc_tick:
    php
    pha
    txa
    pha
    tya
    pha
    inc cc_clock
    lda cc_clock
    cmp #COLOR_TICK_DIVIDER
    bcc cc_done
    lda #0
    sta cc_clock
    ldx cc_phase
    clc
    lda cc_word
    adc cc_delta_lo,x
    sta cc_word
    lda cc_word+1
    adc cc_delta_hi,x
    sta cc_word+1
    jsr cc_publish
    dec cc_left
    bne cc_done
    lda #CC_SEGMENT_STEPS
    sta cc_left
    inc cc_phase
    lda cc_phase
    cmp #CC_PHASES
    bne cc_done
    lda #0
    sta cc_phase
cc_done:
    pla
    tay
    pla
    tax
    pla
    plp
    rts
cc_publish:
    ldx cc_index
    lda $d070
    pha
    and #$3f
    ora #$40 // map palette bank1; preserve display-bank selections
    sta $d070
    lda cc_word+1
    and #15
    sta cc_expand
    asl
    asl
    asl
    asl
    ora cc_expand
    sta $d100,x
    lda cc_word
    and #$f0
    sta cc_expand
    lsr
    lsr
    lsr
    lsr
    ora cc_expand
    sta $d200,x
    lda cc_word
    and #15
    sta cc_expand
    asl
    asl
    asl
    asl
    ora cc_expand
    sta $d300,x
    pla
    sta $d070
    rts
cc_index: .byte 2
cc_delta_lo: .byte <CC_DELTA_0,<CC_DELTA_1,<CC_DELTA_2,<CC_DELTA_3,<CC_DELTA_4,<CC_DELTA_5
cc_delta_hi: .byte >CC_DELTA_0,>CC_DELTA_1,>CC_DELTA_2,>CC_DELTA_3,>CC_DELTA_4,>CC_DELTA_5
cc_word: .word 0
cc_phase: .byte 0
cc_left: .byte 0
cc_clock: .byte 0
cc_expand: .byte 0
.if (* > $3200) { .error "Colour cycle exceeds private budget" }
