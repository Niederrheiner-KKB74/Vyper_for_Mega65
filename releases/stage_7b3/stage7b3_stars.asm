// Confirmed Stage7a1 NCM field in the full Stage6b1 game, no runtime diagnostics.
.import source "stars_layout.inc"
*=$b480 "Stage7a2 sparse NCM starfield core"
.namespace stars {
.label speed_mode=$cfd9 // normal0, eightfold parallax1
.label ready=$cfd8
.label clock=$cfda
.label slot=$cfdb
.label bits=$cfdc
.label step=$cfde // per-class displacement,1/2/4 in fast mode
.label mask=$cfdd
.label palette_saved=$cfe0 // 12 RGB bytes for bank1 indices48..51
.label row=$cff6
.label glyph=$cff7 // temporary word for prefix binding
.label col=$cff9
.label table_saved=$cffa // saved D070 during palette access

init:
    php
    sei
    lda ready
    beq !new+
    plp
    jmp bind // Idempotent init does not restart an existing starfield.
!new:
    jsr palette_map
    ldx #3
!save:
    lda $d130,x
    sta palette_saved,x
    lda $d230,x
    sta palette_saved+4,x
    lda $d330,x
    sta palette_saved+8,x
    lda red,x
    sta $d130,x
    lda green,x
    sta $d230,x
    lda blue,x
    sta $d330,x
    dex
    bpl !save-
    jsr palette_unmap
    lda #1
    sta ready
    jsr reset
    plp
    rts
// Explicit fresh-game reset; NEVER called by level transitions or R restart.
reset:
    lda ready
    beq !done+
    php
    sei
    lda #0
    sta clock
    sta speed_mode
    ldx #STAR_COUNT-1
!positions:
    lda initial_y,x
    sta ys,x
    dex
    bpl !positions-
    jsr clear
    jsr paint_all
    jsr bind
    plp
!done:
    rts
// A=0 normal, A=1 accelerated eightfold. Carry0 success; others carry1.
// Positions and existing clock phase are preserved across mode changes.
set_speed_mode:
    cmp #2
    bcs !unsupported+
    sta speed_mode
    clc
    rts
!unsupported:
    sec
    rts
restore:
    php
    sei
    lda ready
    beq !done+
    jsr palette_map
    ldx #3
!restore:
    lda palette_saved,x
    sta $d130,x
    lda palette_saved+4,x
    sta $d230,x
    lda palette_saved+8,x
    sta $d330,x
    dex
    bpl !restore-
    jsr palette_unmap
    lda #0
    sta ready
!done:
    plp
    rts
palette_map:
    lda $d070
    sta table_saved
    and #$3f
    ora #$40
    sta $d070
    rts
palette_unmap:
    lda table_saved
    sta $d070
    rts
clear:
    lda #>fill_dma
    ldx #<fill_dma
    jmp hud.transfer
paint_all:
    ldx #0
!star:
    stx slot
    jsr address
    ldx slot
    lda draw_bits,x
    sta bits
    jsr pixel
    ldx slot
    inx
    cpx #STAR_COUNT
    bne !star-
    rts
frame:
    php
    pha
    txa
    pha
    tya
    pha
    sei // DMA descriptors and single-byte scratch are not reentrant.
    lda ready
    bne !start+
    jmp frame_done
!start:
    inc clock
    ldx #0
!star:
    stx slot
    // Independent power-of-two rates; no grouping/star collisions by Y.
    cpx #STAR_GROUP
    bcs !red+
    ldy #0
    beq !rate+
!red:
    cpx #STAR_GROUP*2
    bcs !yellow+
    ldy #1
    bne !rate+
!yellow:
    ldy #2
!rate:
    lda speed_mode
    beq !normal+
    lda fast_steps,y
    sta step
    jmp !due+
!normal:
    lda #1
    sta step
    lda clock
    and period_masks,y
    bne !next+
!due:
    jsr address
    lda #0
    sta bits
    jsr pixel
    ldx slot
    clc
    lda ys,x
    adc step
    cmp #200
    bcc !visible+
    sbc #200 // largest sum203; exact modulo200 without wrap artifacts
!visible:
    sta ys,x
    jsr address
    ldx slot
    lda draw_bits,x
    sta bits
    jsr pixel
!next:
    ldx slot
    inx
    cpx #STAR_COUNT
    bne !star-
frame_done:
    pla
    tay
    pla
    tax
    pla
    plp
    rts
address:
    ldx slot
    ldy ys,x
    clc
    lda xbase_lo,x
    adc ybase_lo,y
    sta read_source
    sta write_target
    lda xbase_hi,x
    adc ybase_hi,y
    sta read_source+1
    sta write_target+1
    lda draw_bits,x
    and #$f0
    beq !low+
    lda #$0f // clear only high nibble, retaining neighbouring star.
    bne !mask+
!low:
    lda #$f0
!mask:
    sta mask
    rts
pixel:
    jsr transitionfx.star_visible
    bcc !covered+
    lda #>read_dma
    ldx #<read_dma
    jsr hud.transfer
    lda $6800
    and mask
    ora bits
    sta $6800
    lda #>write_dma
    ldx #<write_dma
    jmp hud.transfer
!covered:
    rts
fast_steps: .byte 1,2,4
red:   .byte STAR_R0,STAR_R1,STAR_R2,STAR_R3
green: .byte STAR_G0,STAR_G1,STAR_G2,STAR_G3
blue:  .byte STAR_B0,STAR_B1,STAR_B2,STAR_B3
read_dma:
    .byte $0a,0,0
    .word 1
read_source: .word 0
    .byte 1
    .word $6800
    .byte 0
    .word 0
write_dma:
    .byte $0a,0,0
    .word 1
    .word $6800
    .byte 0
write_target: .word 0
    .byte 1
    .word 0
fill_dma:
    .byte $0a,0,3
    .word STAR_BYTES
    .word 0
    .byte 0
    .word $8000
    .byte 1
    .word 0
star_core_end:
.if (*>$b6c0) { .error "Starfield core overlaps transition state machine" }
}
*=$4e10 "Stage7a2 star Y state"
.namespace stars {
ys: .fill STAR_COUNT,0
.if (*>$4e40) { .error "Star Y state exceeds budget" }
*=$4e40 "Star background prefix binding, no additional RRB pixie slots"
bind:
    lda ready
    bne !ready+
    rts
!ready:
    php
    sei
    lda #0
    sta row
!row:
    ldx row
    lda #0
    sta hud.row_pointer+2
    sta hud.row_pointer+3
    lda hud.colour_lo,x // lookup points at prefix42, subtract42 for row origin
    sec
    sbc #42
    sta $1a60
    sta hud.row_pointer // true row origin, NOT the dynamic-tail lookup (+84)
    lda hud.colour_hi,x
    sbc #0
    sta $1a61
    ora #$e0 // screen $E000 + the same row offset (0..$1200)
    sta hud.row_pointer+1
    lda #$f8
    sta $1a62
    lda #$0f
    sta $1a63
    // ybase at first scanline of each char row: glyph index$600+row*15.
    txa
    asl
    asl
    asl
    tax
    lda ybase_lo,x
    sta glyph
    lda ybase_hi,x
    sta glyph+1
    .for (var i=0;i<6;i++) { lsr glyph+1; ror glyph }
    lda glyph+1
    ora #4 // physical bank1 contributes $400 glyphs, not bank0
    sta glyph+1
    lda #0
    sta col
    ldy #2
!cell:
    lda glyph
    jsr hud.store
    lda #8 // NCM
    jsr hud.long_colour_store
    iny
    lda glyph+1
    jsr hud.store
    lda #$30 // palette48..63, separate from original palettes
    jsr hud.long_colour_store
    iny
    inc glyph
    bne !carry+
    inc glyph+1
!carry:
    inc col
    lda col
    cmp #15
    bne !cell-
    inc row
    lda row
    cmp #25
    beq bind_done
    jmp !row-
bind_done:
    plp
    rts
.if (*>$4f00) { .error "Starfield binding overlaps attack scheduler" }
}

*=$cfd8 "Starfield state, initialized even before menu/game handoff"
.fill $d000-*,0

// Integration API, no user-facing diagnostic controls.
.label starfield_init=stars.init
.label starfield_tick=stars.frame
.label starfield_bind=stars.bind
.label starfield_restore=stars.restore
.label starfield_reset=stars.reset
.label starfield_set_speed_mode=stars.set_speed_mode
