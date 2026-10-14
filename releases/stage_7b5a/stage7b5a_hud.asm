// HUD extension: 128-byte rows, opaque background, full font, eight dynamic slots.
// Logical playfield [0,240); H640 GOTOX doubles logical X. Glyphs keep 2x width.
*=$3800 "Stage 3b-4a HUD code"
.namespace hud {
.const state=$1a00
.label high_score=state
.label player1_score=state+4
.label player1_level=state+8
.label player1_lives=state+10
.label player2_score=state+12
.label player2_level=state+16
.label player2_lives=state+18
.label player2_active=state+20
.label formation_points=state+21
.label attack_points=state+23
.const shadow=state+$20
.const work=state+$40
.const remainder=state+$44
.const digit=state+$45
.const draw_row=state+$46
.const draw_column=state+$47
.const count=state+$48
.const saved_scale=state+$49
.const lives_count=state+$4a
.const life_row=state+$4b
.const life_column=state+$4c
.const life_offset=state+$4d
.const life_glyph=state+$4e
.const life_ybits=state+$4f
.const life_x=state+$50
.const colour_pointer=state+$60
.const screen_pointer=state+$6c
.label row_pointer=state+$70
.const background_pointer=state+$74
.const store_value=state+$65
.const startup_bg=state+$66
.const hud_start=480
.const max_lives=8

startup:
    // Clear the actual BASIC screen through KERNAL before the unchanged loader.
    lda VIC_BG
    sta startup_bg
    lda #0
    sta VIC_BG
    lda #$93
    jsr $ffd2
    jsr s3b.entry
    lda startup_bg
    sta VIC_BG
    rts

hud_init:
    jsr s3b3.player_init
    lda startup_bg
    sta saved_bg
    lda $d05a
    sta saved_scale
    lda saved_d031
    and #$5f
    ora #$c0 // H640 + FAST; HUD setup must retain full CPU clock.
    sta VIC_D031
    lda #60
    sta $d05a
    lda #0
    sta VIC_CHARPTR_LO
    sta VIC_CHARPTR_BK
    lda #$40
    sta VIC_CHARPTR_HI
    lda #RRB_STRIDE
    sta VIC_LINESTEP_LO
    lda #(RRB_STRIDE/2)
    sta VIC_CHRCOUNT
    jsr hud_copy_font
    // HUD uses unused indices $0A-$0F in the existing player bank 2.
    lda #$9a
    sta VIC_PALSEL
    lda #0
    sta $d100 // transparent player index 0 becomes black for opaque HUD cells
    sta $d200
    sta $d300
    ldx #5
hud_palette_loop:
    lda colours_r,x
    sta $d10a,x
    lda colours_g,x
    sta $d20a,x
    lda colours_b,x
    sta $d30a,x
    dex
    bpl hud_palette_loop
    ldx #24
hud_defaults:
    lda defaults,x
    sta state,x
    lda #$ff
    sta shadow,x
    dex
    bpl hud_defaults
    jsr hud_draw_static
    jsr hud_update_score
    jsr hud_update_level
    jsr hud_update_lives
    jmp hud_update_points

hud_restore_scale:
    sei
    jsr restore_extended_colour
    lda saved_scale
    sta $d05a
    lda #0
    sta VIC_SPREN
    rts

hud_render:
    jsr offscreen.r_render
    jsr hud_update_score
    jsr hud_update_level
    jsr hud_update_lives
    jmp hud_update_points

hud_write_x:
    // Carry supplies GOTOX bit 8 without changing sub-row/Y bits.
    lda v014_x
    asl
    jsr v012a_store
    iny
    lda v014_ybits
    adc #0
    jmp v012a_store

hud_copy_font:
    jmp integration.hud_font
    // Use the actual saved BASIC charset, never ship ROM data.
    lda saved_d068
    sta font_source
    lda saved_d069
    sta font_source+1
    lda saved_d06a
    sta font_source+2
    lda #0
    sta font_mb
    // VIC legacy charset aliases resolve to character WOM $0FF7E000.
    lda saved_d06a
    bne font_dma_start
    lda saved_d068
    bne font_dma_start
    lda saved_d069
    and #$f7
    cmp #$10
    beq font_wom
    cmp #$90
    bne font_dma_start
font_wom:
    lda #$ff
    sta font_mb
    lda saved_d069
    and #8
    ora #$e0
    sta font_source+1
    lda #7
    sta font_source+2
font_dma_start:
    lda #0
    sta $d702
    sta $d704
    lda #>font_dma
    sta $d701
    lda #<font_dma
    sta $d705
    // Overlay only HUD glyphs in the private charset; BASIC/WOM stays intact.
    lda #<font_glyphs
    sta thin_read+1
    lda #>font_glyphs
    sta thin_read+2
    ldx #0
thin_next:
    lda font_codes,x
    asl
    asl
    asl
    sta thin_write+1
    lda font_codes,x
    lsr
    lsr
    lsr
    lsr
    lsr
    clc
    adc #$40
    sta thin_write+2
    ldy #7
thin_copy:
thin_read:
    lda $ffff,y
thin_write:
    sta $ffff,y
    dey
    bpl thin_copy
    clc
    lda thin_read+1
    adc #8
    sta thin_read+1
    bcc thin_advance
    inc thin_read+2
thin_advance:
    inx
    cpx #(font_glyphs-font_codes)
    bne thin_next
    // Ordinary mono frame cells; the right edge has an extra blank margin.
    ldx #7
font_frame:
    lda #$f0
    sta $4400,x
    lda #$ff
    sta $4408,x
    dex
    bpl font_frame
    rts

hud_draw_static:
    lda VIC_D030
    ora #1
    sta VIC_D030
    ldx #0
hud_static_row:
    stx draw_row
    jsr set_prefix
    lda stars.ready
    bne hud_static_keep_background // Existing stars stay bound even mid-redraw.
    jsr draw_background
hud_static_keep_background:
    ldx draw_row
    jsr set_prefix
    lda template_lo,x
    sta template_read+1
    lda template_hi,x
    sta template_read+2
    lda attributes_lo,x
    sta attribute_read+1
    lda attributes_hi,x
    sta attribute_read+2
    ldy #0
hud_static_byte:
template_read:
    lda $ffff,y
screen_store:
    jsr long_screen_store
attribute_read:
    lda $ffff,y
colour_store:
    jsr long_colour_store
    iny
    cpy #42
    bne hud_static_byte
    // Rows 0/1/23/24 are not visited by the moving renderer. Retire their
    // old H320 sentinels too, so no later blank can erase the HUD at X=480.
hud_static_suffix:
    lda #$80
    jsr life_store
    lda #$10
    jsr life_colour
    iny
    lda #2
    jsr life_store
    lda #0
    jsr life_colour
    iny
    cpy #150
    bne hud_static_suffix
    ldx draw_row
    inx
    cpx #25
    bne hud_static_row
    lda VIC_D030
    and #$fe
    sta VIC_D030
    jsr starfield_bind
    rts

set_prefix:
    lda prefix_lo,x
    sta screen_pointer
    lda prefix_hi,x
    sta screen_pointer+1
    lda #0
    sta screen_pointer+2
    sta screen_pointer+3
    lda colour_lo,x
    sta colour_pointer
    lda colour_hi,x
    sta colour_pointer+1
    lda #$f8
    sta colour_pointer+2
    lda #$0f
    sta colour_pointer+3
    rts

// X=state byte offset, Y=byte length. Z=1 means no change.
changed:
    sty count
    lda #0
    sta remainder
changed_byte:
    lda state,x
    cmp shadow,x
    beq changed_next
    sta shadow,x
    inc remainder
changed_next:
    inx
    dec count
    bne changed_byte
    lda remainder
    rts

hud_update_score:
    ldx #0
    ldy #4
    jsr changed
    beq score_p1
    lda #1
    sta draw_row
    ldx #0
    jsr score_work
score_p1:
    ldx #4
    ldy #4
    jsr changed
    beq score_p2
    lda #4
    sta draw_row
    ldx #4
    jsr score_work
score_p2:
    // Player 2 is deliberately inactive; future fields are stored, not enabled.
    rts
score_work:
    lda #7
    sta digit
    lda #2
    sta draw_column
    txa
    clc
    adc #3
    tax
    ldy #3
score_copy:
    lda state,x
    sta work,y
    dex
    dey
    bpl score_copy
    jmp decimal

hud_update_level:
    ldx #8
    ldy #2
    jsr changed
    beq level_done
    lda #5
    sta draw_row
    lda #7
    sta draw_column
    lda #3
    sta digit
    ldx #8
    jmp word_work
level_done:
    rts

hud_update_points:
    ldx #21
    ldy #2
    jsr changed
    beq points_attack
    lda #22
    sta draw_row
    lda #7
    sta draw_column
    lda #3
    sta digit
    ldx #21
    jsr word_work
points_attack:
    ldx #23
    ldy #2
    jsr changed
    beq points_done
    lda #24
    sta draw_row
    lda #7
    sta draw_column
    lda #3
    sta digit
    ldx #23
    jmp word_work
points_done:
    rts
word_work:
    lda state,x
    sta work
    lda state+1,x
    sta work+1
    lda #0
    sta work+2
    sta work+3
    jmp decimal

// 32-bit unsigned division, seven display digits do not limit stored scores.
// Display is low N decimal digits. Only invoked when a field changes.
decimal:
    ldx draw_row
    jsr set_prefix
    lda draw_column
    clc
    adc digit
    asl
    tay
next_digit:
    lda #0
    sta remainder
    ldx #32
divide_bit:
    asl work
    rol work+1
    rol work+2
    rol work+3
    rol remainder
    lda remainder
    cmp #10
    bcc divide_next
    sbc #10
    sta remainder
    inc work
divide_next:
    dex
    bne divide_bit
    lda remainder
    clc
    adc #$30
number_store:
    jsr long_screen_store
    dey
    dey
    dec digit
    bne next_digit
    rts

hud_update_lives:
    ldx #10
    ldy #2
    jsr changed
    bne lives_changed
    rts
lives_changed:
    lda player1_lives+1
    bne lives_max
    lda player1_lives
    cmp #9
    bcc lives_limit
lives_max:
    lda #8
lives_limit:
    sta lives_count
    lda VIC_D030
    ora #1
    sta VIC_D030
    lda #7
    sta life_row
life_next_row:
    ldx life_row
    jsr set_prefix
    // Clear prefix with invisible GOTOX 640 tokens; preserve dynamic bytes.
    ldy #0
life_clear:
    lda #$80
    jsr life_store
    lda #$10
    jsr life_colour
    iny
    lda #2
    jsr life_store
    lda #$60
    jsr life_colour
    iny
    cpy #42
    bne life_clear
    ldy #0
    lda #<hud_start
    ldx #>hud_start
    jsr life_goto_opaque
    lda #$80
    ldx #$80
    jsr life_character_mono
    lda #<632
    ldx #>632
    jsr life_goto_opaque
    lda #$80
    ldx #$80
    jsr life_character_mono
    sty life_offset
    lda #0
    sta life_column
life_each_symbol:
    lda life_column
    cmp lives_count
    bcs life_row_done
    // Group 0 starts at Y=58; group 1 at Y=75, exactly one pixel gap.
    ldx #0
    cmp #4
    bcc life_first_group
    ldx #1
life_first_group:
    lda life_row
    sec
    sbc life_top_rows,x
    cmp #3
    bcs life_symbol_done
    clc
    adc #$21
    sta life_glyph
    lda life_yoffsets,x
    sta life_ybits
    lda life_column
    and #3
    tax
    lda life_positions_lo,x
    sta life_x
    lda life_positions_hi,x
    tax
    ldy life_offset
    lda life_x
    jsr life_store
    lda #$90 // transparent GOTOX, avoids erasing the other group in row 9
    jsr life_colour
    iny
    txa
    ora life_ybits
    jsr life_store
    lda #$60
    jsr life_colour
    iny
    lda life_glyph
    jsr life_store
    lda #$08
    jsr life_colour
    iny
    lda #3
    jsr life_store
    lda #0
    jsr life_colour
    iny
    sty life_offset
life_symbol_done:
    inc life_column
    jmp life_each_symbol
life_row_done:
    // Prefix ends with primary-palette GOTOX 0, then normal eight moving slots.
    ldy #40
    lda #0
    jsr life_store
    lda #$10
    jsr life_colour
    iny
    lda #0
    jsr life_store
    jsr life_colour
    inc life_row
    lda life_row
    cmp #12
    beq lives_done
    jmp life_next_row
lives_done:
    lda VIC_D030
    and #$fe
    sta VIC_D030
    rts
life_goto_opaque:
    jsr life_store
    lda #$10
    jsr life_colour
    iny
    txa
    jsr life_store
    lda #$60
    jsr life_colour
    iny
    rts
life_character_mono:
    jsr life_store
    lda #0
    jsr life_colour
    iny
    txa
    jsr life_store
    lda #$0b
    jsr life_colour
    iny
    rts
life_store:
    jmp long_screen_store
life_colour:
    jmp long_colour_store

// Preserve A/X/Y/flags/B/Z. Temporary base page $1A exposes the long pointer
// without borrowing any KERNAL zero-page bytes. IRQs stay masked while B differs.
long_colour_store:
    php
    pha
    sei
    sta store_value
    .byte $7b // TBA
    pha
    .byte $6b // TZA
    pha
    lda #$1a
    .byte $5b // TAB
    tya
    .byte $4b // TAZ
    lda store_value
    .byte $ea,$92,$60 // EOM; physical 32-bit store in base page $1A
    pla
    .byte $4b // TAZ
    pla
    .byte $5b // TAB
    pla
    plp
    rts

// SYS keeps E000-FFFF MAPped to bank-3 KERNAL. Long stores bypass MAP.
long_screen_store:
    php
    pha
    sei
    sta store_value
    .byte $7b // TBA
    pha
    .byte $6b // TZA
    pha
    lda #$1a
    .byte $5b // TAB
    tya
    .byte $4b // TAZ
    lda store_value
    .byte $ea,$92,$6c // EOM; physical 32-bit store in base page $1A
    pla
    .byte $4b // TAZ
    pla
    .byte $5b // TAB
    pla
    plp
    rts

long_row_store:
    php
    pha
    sei
    sta store_value
    .byte $7b // TBA
    pha
    .byte $6b // TZA
    pha
    lda #$1a
    .byte $5b // TAB
    tya
    .byte $4b // TAZ
    lda store_value
    .byte $ea,$92,$70 // EOM; physical 32-bit store in base page $1A
    pla
    .byte $4b // TAZ
    pla
    .byte $5b // TAB
    pla
    plp
    rts

long_background_store:
    php
    pha
    sei
    sta store_value
    .byte $7b // TBA
    pha
    .byte $6b // TZA
    pha
    lda #$1a
    .byte $5b // TAB
    tya
    .byte $4b // TAZ
    lda store_value
    .byte $ea,$92,$74 // EOM; physical 32-bit store in base page $1A
    pla
    .byte $4b // TAZ
    pla
    .byte $5b // TAB
    pla
    plp
    rts


set_row_pointer:
    lda v012a_screen_lo,x
    sta row_pointer
    lda v012a_screen_hi,x
    sta row_pointer+1
    lda #0
    sta row_pointer+2
    sta row_pointer+3
    lda #<direct_store
    sta v012a_store+1
    lda #>direct_store
    sta v012a_store+2
    rts
set_colour_pointer:
    lda v012a_color_lo,x
    sta colour_pointer
    lda v012a_color_hi,x
    sta colour_pointer+1
    lda #$f8
    sta colour_pointer+2
    lda #$0f
    sta colour_pointer+3
    lda #<long_colour_store
    sta v012a_store+1
    lda #>long_colour_store
    sta v012a_store+2
    rts
store:
direct_store:
    jmp long_row_store

draw_background:
    // Every raster starts with opaque black covering the entire 640-pixel raster.
    // The prefix pointers are 42 bytes beyond the row origin.
    sec
    lda screen_pointer
    sbc #42
    sta background_pointer
    lda screen_pointer+1
    sbc #0
    sta background_pointer+1
    lda #0
    sta background_pointer+2
    sta background_pointer+3
    sec
    lda colour_pointer
    sbc #42
    sta colour_pointer
    lda colour_pointer+1
    sbc #0
    sta colour_pointer+1
    ldy #0
    lda #0
    jsr background_store
    lda #$10
    jsr long_colour_store
    iny
    lda #0
    jsr background_store
    jsr long_colour_store
    iny
background_blank:
    lda #0
    jsr background_store
    lda #8
    jsr long_colour_store
    iny
    lda #2
    jsr background_store
    lda #0
    jsr long_colour_store
    iny
    cpy #42
    bne background_blank
    rts
background_store:
    jmp long_background_store

save_all_colour:
    jsr save_basic_color_ram
    jsr entry.e_save_colour
save_extended_colour:
    lda #>colour_backup_dma
    ldx #<colour_backup_dma
    jmp transfer
restore_extended_colour:
    jsr entry.e_restore_colour
    lda #>colour_restore_dma
    ldx #<colour_restore_dma
transfer:
    sta $d701
    lda #0
    sta $d702
    sta $d704
    stx $d705
    rts
clear_colour_dma:
    php
    pha
    txa
    pha
    lda colour_pointer
    sta clear_destination
    lda colour_pointer+1
    sta clear_destination+1
    lda #>clear_dma
    ldx #<clear_dma
    jsr transfer
    pla
    tax
    pla
    plp
    rts
clear_dma:
    .byte $80,0,$81,$ff,$0a,0,0
    .word RRB_BYTES
    .byte <zero_colours,>zero_colours,0
clear_destination: .byte 0,0,8
    .word 0
// Empty records are GOTOX 640 / transparent NCM $200, never zero/mono tails.
zero_colours: .fill RRB_BYTES, (mod(i,4)==0) ? $10 : ((mod(i,4)==2) ? $08 : 0)
colour_backup_dma:
    .byte $80,$ff,$81,0,$0a,0,0
    .word $480
    .byte 0,8,8
    .byte 0,$56,1 // Stage5c: extended colour backup $15600-$15A7F, after private pixies.
    .word 0
colour_restore_dma:
    .byte $80,0,$81,$ff,$0a,0,0
    .word $480
    .byte 0,$56,1 // Stage5c: extended colour backup $15600-$15A7F, after private pixies.
    .byte 0,8,8
    .word 0

font_dma:
    .byte $80
font_mb: .byte 0
    .byte $0a,0,0
    .word $800
font_source: .byte 0,0,0
    .byte 0,$40,0
    .word 0
screen_init:
    ldx #0
    jmp v014_prepare_row
code_end:
.if (code_end > $3e80) { .error "HUD code overlaps defaults" }
}
.import source "stage7b5a_templates.asm"
