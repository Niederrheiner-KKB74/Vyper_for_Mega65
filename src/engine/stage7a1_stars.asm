// Independent starfield in existing opaque background prefix, behind transparent RRB.
.import source "stars_layout.inc"
*=$b480 "Stage7a1 sparse NCM starfield core"
.namespace stars {
.label ready=$cfd8
.label enabled=$cfd9
.label clock=$cfda
.label slot=$cfdb
.label bits=$cfdc
.label mask=$cfdd
.label marker=$cfde
.label border_saved=$cfdf
.label palette_saved=$cfe0 // 12 RGB bytes for bank1 indices48..51
.label raster=$cfec // start low/high, end low/high
.label span=$cff0 // raw 9-bit raster delta
.label max_span=$cff2
.label frames=$cff4 // number of measured star updates, WORD
.label row=$cff6
.label glyph=$cff7 // temporary word for prefix binding
.label col=$cff9
.label table_saved=$cffa // saved D070 during palette access

init:
    php
    sei
    lda #0
    sta ready
    sta clock
    sta marker
    sta max_span
    sta max_span+1
    sta frames
    sta frames+1
    lda #1
    sta enabled
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
    ldx #STAR_COUNT-1
!positions:
    lda initial_y,x
    sta ys,x
    dex
    bpl !positions-
    jsr clear
    lda #1
    sta ready
    jsr paint_all
    jsr bind
    plp
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
key:
    ldx ready
    beq !pass+
    cmp #$42 // B: background on/off, independent of engine controls.
    bne !marker+
    php
    sei
    lda enabled
    eor #1
    sta enabled
    jsr clear
    lda enabled
    beq !off+
    jsr paint_all
!off:
    plp
    lda #0
    rts
!marker:
    cmp #$56 // V: border profiling marker. Geometry and HUD untouched.
    bne !pass+
    lda marker
    eor #1
    sta marker
    lda #0
!pass:
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
    ldx #0
    jsr read_raster
    lda $d020
    sta border_saved
    lda marker
    beq !marker_off+
    lda #2
    sta $d020
!marker_off:
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
    lda clock
    and period_masks,y
    bne !next+
    lda enabled
    beq !move+
    jsr address
    lda #0
    sta bits
    jsr pixel
!move:
    ldx slot
    inc ys,x
    lda ys,x
    cmp #200
    bcc !visible+
    lda #0
    sta ys,x
!visible:
    lda enabled
    beq !next+
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
    lda border_saved
    sta $d020
    ldx #2
    jsr read_raster
    sec
    lda raster+2
    sbc raster
    sta span
    lda raster+3
    sbc raster+1
    sta span+1
    bcs !delta+
    clc // PAL312 lines: correct real frame wrap, not arbitrary 256 wrap.
    lda span
    adc #<312
    sta span
    lda span+1
    adc #>312
    sta span+1
!delta:
    lda span+1
    cmp max_span+1
    bcc !count+
    bne !maximum+
    lda span
    cmp max_span
    bcc !count+
!maximum:
    lda span
    sta max_span
    lda span+1
    sta max_span+1
!count:
    inc frames
    bne frame_done
    inc frames+1
frame_done:
    pla
    tay
    pla
    tax
    pla
    plp
    rts
// Coherent classic VIC raster9 reading; IRQ compare bit7 is read as live raster.
read_raster:
!again:
    lda $d011
    and #$80
    sta raster+1,x
    lda $d012
    sta raster,x
    lda $d011
    and #$80
    cmp raster+1,x
    bne !again-
    lda raster+1,x
    asl
    lda #0
    rol
    sta raster+1,x
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
.if (*>$b800) { .error "Starfield core overlaps existing RRB renderer" }
}
*=$4e10 "Stage7a1 star Y state"
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
