// Issue55: 240x200 concentric 8px bands in existing NCM bitmap.
// Spatial outside->inside BLUE,YELLOW,RED,DARKBLUE; screenshot-derived approximation.
.const FX_ACCEL_FRAMES=50
.const FX_RING_FRAMES=3
.const FX_STEP_PIXELS=8 // NCM half-cell grid; one band grows per FX_RING_FRAMES.
.const FX_COLUMNS=240/FX_STEP_PIXELS
.const FX_ROWS=200/FX_STEP_PIXELS
.const FX_RINGS=(FX_ROWS+1)/2
.const FX_BLUE=$44
.const FX_YELLOW=$55
.const FX_RED=$66
.const FX_DARK_BLUE=$77
.const FX_RGB_BLUE=$06e
.const FX_RGB_YELLOW=$dd0
.const FX_RGB_RED=$a00
.const FX_RGB_DARK_BLUE=$00a
.namespace transitionfx {
.label state=$1bc0
.label timer=$1bc1
.label ring=$1bc2
.label next_level=$1bc3
.label row=$1bc4
.label column=$1bc5
.label depth=$1bc6
.label colour=$1bc7
.label covered=$1bc8 //13=no coverage, then12..0 centre->outward
.label scan=$1bc9
.label saved_shared=$1b90 // D025,D026; legacy snapshot ends1B88
.label saved_palette=$1ba0 // bank1 indices52..55 RGB,12 bytes
.label palette_ready=$1bac
.label table=$1bad
}
*=$6650 "Stage7b5b transition setup"
.namespace transitionfx {
init:
    lda #0
    ldx #15
!zero:
    sta state,x
    dex
    bpl !zero-
    lda #13
    sta covered
    jmp palette_init
begin:
    lda #FX_RINGS
    sta covered
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
    jsr audio8.begin_hook
    ldx #7
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
.if (*>$6700) { .error "Transition setup overlaps blank template" }
}

*=$bf10 "Stage7b5b concentric transition FSM"
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
    lda #FX_RINGS-1
    sec
    sbc ring
    sta depth
    lda state
    cmp #2
    bne !black+
    lda depth
    and #3
    tax
    lda colours,x
    bne !paint+
!black:
    lda #0
!paint:
    sta colour
    jsr paint_ring
    lda depth
    sta covered
    inc ring
    lda ring
    cmp #FX_RINGS
    bcc done
    lda #0
    sta ring
    inc state
done:
    rts
accel:
    inc timer
    lda timer
    cmp #FX_ACCEL_FRAMES
    bcc done
    lda #0
    sta timer
    jsr audio8.rect_hook
    .fill 2,$ea
    rts
finish:
    lda #0
    sta state
    jsr starfield_set_speed_mode
    // Keep Y/clock phase; reconstruct current stars, never reset positions.
    php
    sei
    jsr stars.clear
    jsr stars.paint_all
    plp
    lda next_level
    jmp getready.gr_completed
colours: .byte FX_BLUE,FX_YELLOW,FX_RED,FX_DARK_BLUE
.if (*>$c000) { .error "FSM overlaps existing graphics" }
}

*=$b6c0 "Stage7b5b bounded NCM annulus painter"
.namespace transitionfx {
paint_ring:
    php
    sei
    lda #0
    sta row
!row:
    lda #0
    sta column
!cell:
    // Depth=min(x/8,29-x/8,y/8,24-y/8).
    lda column
    jsr cell_depth
    cmp depth
    beq !paint_cell+
    jmp !next+
!paint_cell:
    // 8x8 half-glyph:4 bytes per scanline, packed NCM, stride8.
    lda column
    lsr
    tax
    txa
    .for (var i=0;i<6;i++) { asl }
    sta target
    txa
    lsr
    lsr
    sta target+1
    lda row
    asl
    asl
    asl
    tax
    clc
    lda target
    adc stars.ybase_lo,x
    sta target
    lda target+1
    adc stars.ybase_hi,x
    sta target+1
    lda column
    and #1
    beq !left+
    lda target
    ora #4
    sta target
!left:
    lda colour
    sta value
    lda #8
    sta scan
    lda #4
    sta count
    lda column
    and #1
    bne !line+
    lda column
    clc
    adc #1
    jsr cell_depth
    cmp depth
    bne !line+
    // Both halves belong to this annulus: one64-byte FILL instead of16 jobs.
    lda #64
    sta count
    lda #1
    sta scan
    inc column
!line:
    lda #>fill
    ldx #<fill
    jsr hud.transfer
    clc
    lda target
    adc #8
    sta target
    bcc !carry+
    inc target+1
!carry:
    dec scan
    bne !line-
!next:
    inc column
    lda column
    cmp #FX_COLUMNS
    beq !row_done+
    jmp !cell-
!row_done:
    inc row
    lda row
    cmp #FX_ROWS
    beq !done+
    jmp !row-
!done:
    plp
    rts
cell_depth:
    cmp #15
    bcc !x+
    eor #$ff
    clc
    adc #FX_COLUMNS //29-x
!x:
    sta temp
    lda row
    cmp #FX_RINGS
    bcc !y+
    eor #$ff
    clc
    adc #FX_ROWS //24-y
!y:
    cmp temp
    bcc !end+
    lda temp
!end:
    rts
temp: .byte 0
fill:
    .byte $0a,0,3
count: .word 4
value: .word 0
    .byte 0
target: .word 0
    .byte 1
    .word 0
.if (*>$b800) { .error "Painter overlaps RRB renderer" }
}

*=$b668 "Stage7b5b covered-star write filter"
.namespace transitionfx {
star_visible:
    lda state
    cmp #2
    bcc !visible+
    cmp #3
    bcs !hidden+
    // xHalf = xbase/32 +(xbase&4)/4. xbase=col*64+byteWithinGlyph.
    ldx stars.slot
    lda stars.xbase_lo,x
    .for (var i=0;i<5;i++) { lsr }
    sta star_x
    lda stars.xbase_hi,x
    asl
    asl
    asl
    ora star_x
    sta star_x
    lda stars.xbase_lo,x
    and #4
    beq !x+
    inc star_x
!x:
    lda stars.ys,x
    lsr
    lsr
    lsr
    // cell_depth uses painter row; safe because both execute synchronously.
    sta row
    lda star_x
    jsr cell_depth
    cmp covered
    bcs !hidden+
!visible:
    sec
    rts
!hidden:
    clc
    rts
star_x: .byte 0
.if (*>$b6c0) { .error "Star filter overlaps painter" }
}

*=$8180 "Stage7b5b isolated transition palette"
.namespace transitionfx {
palette_init:
    lda palette_ready
    bne !done+
    jsr map
    ldx #3
!save:
    lda $d134,x
    sta saved_palette,x
    lda $d234,x
    sta saved_palette+4,x
    lda $d334,x
    sta saved_palette+8,x
    lda red,x
    sta $d134,x
    lda green,x
    sta $d234,x
    lda blue,x
    sta $d334,x
    dex
    bpl !save-
    lda #1
    sta palette_ready
    jmp unmap
!done:
    rts
palette_restore:
    lda palette_ready
    beq !done+
    jsr map
    ldx #3
!restore:
    lda saved_palette,x
    sta $d134,x
    lda saved_palette+4,x
    sta $d234,x
    lda saved_palette+8,x
    sta $d334,x
    dex
    bpl !restore-
    lda #0
    sta palette_ready
    jmp unmap
!done:
    rts
.if (*>$8200) { .error "Palette saves overlap projectile core" }
*=$87a0 "Stage7b5b palette mapping and screenshot RGB approximation"
map:
    lda $d070
    sta table
    and #$3f
    ora #$40
    sta $d070
    rts
unmap:
    lda table
    sta $d070
    rts
red: .byte (FX_RGB_BLUE>>8)*17,(FX_RGB_YELLOW>>8)*17,(FX_RGB_RED>>8)*17,(FX_RGB_DARK_BLUE>>8)*17
green: .byte ((FX_RGB_BLUE>>4)&15)*17,((FX_RGB_YELLOW>>4)&15)*17,((FX_RGB_RED>>4)&15)*17,((FX_RGB_DARK_BLUE>>4)&15)*17
blue: .byte (FX_RGB_BLUE&15)*17,(FX_RGB_YELLOW&15)*17,(FX_RGB_RED&15)*17,(FX_RGB_DARK_BLUE&15)*17
.if (*>$8800) { .error "Palette map overlaps original glyphs" }
}

*=$80c0 "Stage7b5b shared multicolour sprite register helpers"
.namespace transitionfx {
save_shared:
    jsr save_sprite_palette
    lda #0
    sta palette_ready
    sta state // Filter must be idle before stars.init, even with stale low RAM.
    lda $d025
    sta saved_shared
    lda $d026
    sta saved_shared+1
    jmp shots.p_save_registers
restore_shared:
    jsr restore_sprite_palette
    lda shots.p_saved_registers+30 // Original D01C, index in expanded p_regs.
    sta $d01c
    lda saved_shared
    sta $d025
    lda saved_shared+1
    sta $d026
    rts
sprite_map:
    lda $d070
    sta table
    and #$3f
    ora #$80
    sta $d070
    rts
.if (*>$8100) { .error "Sprite helpers overlap original glyphs" }
}
*=$bf96 "Stage7b5b Original projectile palette and multicolour mode"
.namespace transitionfx {
.label saved_sprite_palette=$1b92
save_sprite_palette:
    php
    sei
    jsr sprite_map
    lda $d110
    sta saved_sprite_palette
    lda $d210
    sta saved_sprite_palette+1
    lda $d310
    sta saved_sprite_palette+2
    jsr unmap
    plp
    rts
restore_sprite_palette:
    php
    sei
    jsr sprite_map
    lda saved_sprite_palette
    sta $d110
    lda saved_sprite_palette+1
    sta $d210
    lda saved_sprite_palette+2
    sta $d310
    jsr unmap
    plp
    rts
sprite_mode:
    lda #$ff // All eight channels now MCM3x7; codes01 white,11 red,10 grey.
    sta $d01c
    lda #10
    sta $d025
    lda #13
    sta $d026
    jsr sprite_map
    lda #$33
    sta $d110
    lda #$44
    sta $d210
    sta $d310
    jsr unmap
    lda #0
    rts
.if (*>$c000) { .error "Projectile palette helpers overlap original graphics" }
}
