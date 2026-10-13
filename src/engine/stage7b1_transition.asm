// Issue53: bounded 50Hz FSM, existing NCM prefix; geometry is a test approximation.
.const FX_ACCEL_FRAMES=50
.const FX_RING_FRAMES=3
.const FX_RINGS=8
.const FX_SOLID_BASE=$1de00
.namespace transitionfx {
.label state=$1bc0 // 0 idle,1 accel,2 colour,3 black,4 level init
.label timer=$1bc1
.label ring=$1bc2
.label next_level=$1bc3
.label row=$1bc4
.label column=$1bc5
.label glyph=$1bc6 // word
.label pool_index=$1bc8
}

*=$6650 "Stage7b1 transition setup and confirmation"
.namespace transitionfx {
init:
    lda #0
    ldx #15
!state:
    sta $1bc0,x
    dex
    bpl !state-
    php
    sei
    ldx #0
!tile:
    stx pool_index
    lda pool_bytes,x
    sta pool_value
    txa
    .for (var i=0;i<6;i++) { asl }
    sta pool_target
    lda #>pool_dma
    ldx #<pool_dma
    jsr hud.transfer
    ldx pool_index
    inx
    cpx #4
    bne !tile-
    plp
    rts
begin:
    lda level.number
    cmp #100
    bne !next+
    lda #0
!next:
    clc
    adc #1
    sta next_level
    lda #1
    sta state
    jsr starfield_set_speed_mode
    lda #2
    sta level.mode // Existing move/objects/key filters freeze gameplay, X passes.
    lda #0
    sta timer
    sta ring
    jsr shots.p_disable
    ldx #5
    lda #0
!shots:
    sta shots.p_active,x
    dex
    bpl !shots-
    ldx #0
!scene:
    stx row
    lda #0
    sta v014_row_count,x
    jsr s2ia_clear_row // Only dynamic tail; retain background and HUD prefix.
    ldx row
    inx
    cpx #25
    bne !scene-
    rts
.if (*>$6700) { .error "Transition setup overlaps guarded blank cache" }
}

*=$b6c0 "Stage7b1 nonblocking transition tick"
.namespace transitionfx {
tick:
    lda state
    cmp #1
    beq accel
    cmp #4
    beq finish
    inc timer
    lda timer
    cmp #FX_RING_FRAMES
    bcc done
    lda #0
    sta timer
    lda state
    cmp #2
    bne !black+
    ldx ring
    lda colour_order,x
    clc
    adc #<(FX_SOLID_BASE/64)
    bne !paint+
!black:
    lda #<(FX_SOLID_BASE/64)
!paint:
    sta glyph
    lda #>(FX_SOLID_BASE/64)
    sta glyph+1
    jsr paint_ring
    inc ring
    lda ring
    cmp #FX_RINGS
    bcc done
    lda #0
    sta ring
    inc state // Colour complete -> black; black complete -> level initialization.
done:
    rts
accel:
    inc timer
    lda timer
    cmp #FX_ACCEL_FRAMES
    bcc done
    lda #0
    sta timer
    lda #2
    sta state
    rts
finish:
    lda #0
    sta state
    jsr starfield_set_speed_mode
    jsr starfield_bind // Remove every solid overlay reference, no bitmap reset.
    lda next_level
    jmp level.transition // Score/lives/highscore unchanged; original palette/entry.
paint_ring:
    lda #7
    sec
    sbc ring
    jsr draw_column
    lda ring
    beq done
    clc
    adc #7
    jmp draw_column
colour_order: .byte 3,1,2,3,1,2,3,1 // Yellow,blue,red; isolated approximation.
.if (*>$b800) { .error "Transition tick overlaps existing RRB renderer" }
}

*=$b760 "Stage7b1 existing-prefix overlay columns"
.namespace transitionfx {
draw_column:
    sta column
    php
    sei
    lda #0
    sta hud.row_pointer+2
    sta hud.row_pointer+3
    ldx #0
!row:
    stx row
    lda hud.colour_lo,x // row*192+42 -> actual row origin
    sec
    sbc #42
    sta hud.row_pointer
    lda hud.colour_hi,x
    sbc #0
    ora #$e0
    sta hud.row_pointer+1
    lda column
    asl
    clc
    adc #2
    tay
    lda glyph
    jsr hud.store
    iny
    lda glyph+1
    jsr hud.store
    ldx row
    inx
    cpx #25
    bne !row-
    plp
    rts
pool_bytes: .byte $00,$11,$22,$33 // Existing dedicated star subpalette48..51.
pool_dma:
    .byte $0a,0,3
    .word 64
pool_value: .word 0
    .byte 0
pool_target: .word $de00
    .byte 1
    .word 0
.if (*>$b800) { .error "Overlay column helper overlaps RRB renderer" }
}
