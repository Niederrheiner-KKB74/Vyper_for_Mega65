// Stage 4b preparation / Issue #12: player geometry on stage4a-stable.
// Original entry-curve semantics still require a verified source.
// Stage 3b-4a: static HUD, H640 with preserved pixie scale; base stage3b3-stable.
// Based exclusively on stage3b3-stable; loader and motion retained, D05A exit restore added.
// Exit/movement algorithms preserved; object/diagnostic operands relocated out of KERNAL RAM.
// Loader at $4800; Level-1 graphics drive 22 path pixies without changing movement.
// Stage 2j: 24 moving pixies; 8 dynamic row slots, no static pixies.
// Stage 2i-a: explicit dynamic RRB slot clearing; original Stage 2i retained.
// Stage 2i: four additional path pixies (source-only, not assembled)
// V0.14 Stage 2h: visible clockwise orbit Pixie, no border diagnosis; V0.13c: two-character diagnostic, original Colour RAM, Y offset retained.
// V0.13a: diagnostic build. Keep V0.13 Y offset and V0.12b RRB layout.
 // Force all three dynamic row masks to $FF to isolate rowmask problems.
// V0.12b: rows 2..20; preserve stationary RRB entries on occupied rows.
// V0.11b: V0.10a baseline; X=32..224 and switch first-row pixie draw order with O.
// V0.10 - six enemy types animation; V0.9c palette and pixel data conventions unchanged
// V0.9c: enemy palette copied exactly from vyperlike_v020.asm; graphics unchanged.
// V0.9a: FIX LEFT GOTOX; RIGHT NIBBLE-SWAPPED TYPE 3; MIDDLE ORIGINAL.
// V0.9: CONTROLLED A/B. Left: deterministic NCM reference glyph; middle/right: unchanged Vyper type 3.
// V0.6 FCM A/B: row 6 plain FCM, row 14 FCM via RRB GOTOX.
// Identical glyph $201 in both cases; test isolates RRB interpretation.
// V0.4 FOUR TILE REFERENCE. Based on V0.3, retains original BASIC startup.
// Reference pattern RRB diagnostic V0.3. A row-major; B side-by-side; C swapped nibbles.
// Vyper Typ 3 (index 2) three-variant RRB reference diagnostic V0.2
// User-validated: row-major, high nibble left.
// V0.3a: fixed graphics origin $8000 (V0.3 erroneously used $0800).
// V0.3 diagnostic: swap low/high NCM pixel nibbles for original enemy glyphs.
// Bullet glyph reduced to 2 pixels. Background right-edge still under investigation.
// RRB STRESS V0.3: 22 enemies in 2 rows of 11 + 8 RRB projectiles.
// Derived from verified V0.14d setup; visual test, not gameplay.
// Vyper-like MEGA65 prototype V0.14d - corrected VIC-IV palette-bank selection
// Stable reference: V0.10 fixed. This branch replaces enemy hardware sprites
// with VIC-IV Raster Rewrite Buffer (RRB) NCM pixies.
//
// 22 logical enemies are displayed as 16x16, 8-colour RRB objects.
// Enemy type 2 uses corrected original Vyper frames 13..19; explosion uses frames 0..7.
// Hardware sprites are now reserved for a 16x16 full-colour player + two projectiles.
//
// Controls: joystick port 2, FIRE supports two shots, X exits to BASIC.

.const VIC_SPR0_X=$d000
.const VIC_SPR0_Y=$d001
.const VIC_SPR1_X=$d002
.const VIC_SPR1_Y=$d003
.const VIC_SPR2_X=$d004
.const VIC_SPR2_Y=$d005
.const VIC_XMSB=$d010
.const VIC_D011=$d011
.const VIC_SPREN=$d015
.const VIC_D016=$d016
.const VIC_D018=$d018
.const VIC_BORDER=$d020
.const VIC_BG=$d021
.const SPR0_COLOR=$d027
.const SPR1_COLOR=$d028
.const SPR2_COLOR=$d029
.const VIC_KEY=$d02f
.const VIC_D030=$d030
.const VIC_D031=$d031
.const VIC_D054=$d054
.const VIC_HOTREG=$d05d
.const VIC_CHRCOUNT=$d05e
.const VIC_LINESTEP_LO=$d058
.const VIC_LINESTEP_HI=$d059
.const VIC_SCRNPTR_LO=$d060
.const VIC_SCRNPTR_MI=$d061
.const VIC_SCRNPTR_HI=$d062
.const VIC_SCRNPTR_XHI=$d063
.const VIC_COLPTR_LO=$d064
.const VIC_COLPTR_HI=$d065
.const VIC_CHARPTR_LO=$d068
.const VIC_CHARPTR_HI=$d069
.const VIC_CHARPTR_BK=$d06a
.const VIC_SPR16EN=$d06b
.const VIC_SPRX64EN=$d057
.const VIC_SPRPTRLO=$d06c
.const VIC_SPRPTRHI=$d06d
.const VIC_SPRPTRBK=$d06e
.const VIC_PALSEL=$d070
.const VIC_DISPROWS=$d07b

.const CIA1_PRA=$dc00
.const CIA2_PRA=$dd00
.const KERNAL_GETIN=$ffe4
.const KEY_X=$58

.const SCREEN_RAM=$5000
.const COLOR_RAM=$d800
.const COLOR_TEMPLATE=$6000
.const SPRPTR_TABLE=$5c80
.const NCM_DATA=$8000
.const NCM_BLANK=NCM_DATA/64
.const NCM_FRAME0_TOP=NCM_BLANK+1
.const NCM_EXPLOSION0_TOP=NCM_BLANK+15

.const PLAYER_PTR16=$3000/64
.const SHOT_PTR16=$30c0/64
.const PLAYER_Y=220
.const SHOT_START_Y=214
.const PLAYFIELD_RIGHT_X=256
.const PLAYER_MIN_X=24
.const PLAYER_MAX_X=232
.const STATE_DEAD=0
.const STATE_FORMATION=1
.const STATE_LEAVING=2
.const STATE_ATTACKING=3
.const STATE_RETURNING=4
.const STATE_EXPLODING=5

*=$2001
BasicUpstart:
    .word BasicEnd
    .word 10
    .byte $9e
    .text "33280"
    .byte 0
BasicEnd:
    .word 0

*=$2100
start:
    sei
    lda VIC_BORDER
    sta saved_border
    lda VIC_BG
    sta saved_bg

    lda #$47
    sta VIC_KEY
    lda #$53
    sta VIC_KEY

    // Save the legacy VIC/CIA registers that HOTREG uses to reconstruct
    // the normal BASIC video mode.
    lda VIC_D011
    sta saved_d011
    lda VIC_D016
    sta saved_d016
    lda VIC_D018
    sta saved_d018
    lda CIA2_PRA
    sta saved_dd00

    lda VIC_D030
    sta saved_d030
    lda VIC_D031
    sta saved_d031
    lda VIC_D054
    sta saved_d054
    lda VIC_HOTREG
    sta saved_d05d
    lda VIC_LINESTEP_LO
    sta saved_d058
    lda VIC_LINESTEP_HI
    sta saved_d059
    lda VIC_CHRCOUNT
    sta saved_d05e
    lda VIC_SCRNPTR_LO
    sta saved_d060
    lda VIC_SCRNPTR_MI
    sta saved_d061
    lda VIC_SCRNPTR_HI
    sta saved_d062
    lda VIC_SCRNPTR_XHI
    sta saved_d063
    lda VIC_COLPTR_LO
    sta saved_d064
    lda VIC_COLPTR_HI
    sta saved_d065
    lda VIC_CHARPTR_LO
    sta saved_d068
    lda VIC_CHARPTR_HI
    sta saved_d069
    lda VIC_CHARPTR_BK
    sta saved_d06a
    lda VIC_SPRPTRLO
    sta saved_d06c
    lda VIC_SPRPTRHI
    sta saved_d06d
    lda VIC_SPRPTRBK
    sta saved_d06e
    lda VIC_SPR16EN
    sta saved_d06b
    lda VIC_SPRX64EN
    sta saved_d057
    lda VIC_PALSEL
    sta saved_d070
    lda VIC_DISPROWS
    sta saved_d07b

    // Disable HOTREG and cancel pending recalculation.
    lda VIC_HOTREG
    and #$7f
    sta VIC_HOTREG
    sta VIC_HOTREG

    // H320 and ATTR off. NCM requires 8-bit colour attributes.
    lda saved_d031
    and #%01011111
    sta VIC_D031

    // CRAM2K + RAM palette enable.
    lda saved_d030
    ora #%00000101
    sta VIC_D030

    // CRAM2K makes the complete $D800-$DFFF CPU window point at Color RAM.
    // Save the BASIC/KERNAL 2KB colour/attribute screen BEFORE overwriting it.
    jsr hud.save_all_colour

    // CHR16 (SEAM) + FCLRHI: chars <256 mono, chars >=256 full-colour/NCM.
    lda saved_d054
    ora #%00000101
    sta VIC_D054

    // 40 RRB entries per row, each entry is two bytes.
    lda #80
    sta VIC_LINESTEP_LO
    lda #0
    sta VIC_LINESTEP_HI
    lda #40
    sta VIC_CHRCOUNT

    // RRB screen at $005000.
    lda #<SCREEN_RAM
    sta VIC_SCRNPTR_LO
    lda #>SCREEN_RAM
    sta VIC_SCRNPTR_MI
    lda #0
    sta VIC_SCRNPTR_HI
    lda saved_d063
    and #%11001111
    sta VIC_SCRNPTR_XHI

    // First 2KB of colour RAM, accessible at $D800-$DFFF.
    lda #0
    sta VIC_COLPTR_LO
    sta VIC_COLPTR_HI

    // Mono character base retained at $4000 for any low character numbers.
    lda #$00
    sta VIC_CHARPTR_LO
    lda #$00
    sta VIC_CHARPTR_HI
    lda #0
    sta VIC_CHARPTR_BK

    lda #25
    sta VIC_DISPROWS

    jsr copy_color_template
    jsr s3b3.player_palette_init
    jsr shots.p_disable
    jsr init_enemy_state
    // Stage 2j: stationary RRB pixies disabled
    // Stage 2j: stationary RRB animations disabled
    jsr v012a_init
    jsr offscreen.r_init
    lda #0
    sta VIC_SPREN // no hardware sprites in this test

    lda #0
    sta VIC_BG
    sta VIC_BORDER

    // IMPORTANT: CRAM2K is only needed while CPU accesses the upper 1KB of
    // Color RAM.  Leaving it set hides CIA1 at $DC00, which makes joystick
    // port 2 impossible to read.  The VIC can continue to use all Color RAM.
    lda VIC_D030
    and #%11111110
    sta VIC_D030

    cli

main_loop:
wait_frame:
    lda $d012
    cmp #250
    bne wait_frame
wait_frame_end:
    lda $d012
    cmp #250
    beq wait_frame_end

    jsr offscreen.r_key
    cmp #KEY_X
    beq v010_exit
    cmp #$4f              // O: switch RRB entry order for upper pair
    bne v011b_not_o
    // O disabled in Y test; V0.11b remains unchanged on disk.
v011b_not_o:
    cmp #$20
    bne v010_not_space
    lda anim_paused
    eor #1
    sta anim_paused
v010_not_space:
    cmp #$2b              // + faster
    bne v010_not_plus
    lda anim_speed
    cmp #1
    beq v010_not_plus
    dec anim_speed
v010_not_plus:
    cmp #$2d              // - slower
    bne v010_not_minus
    lda anim_speed
    cmp #25
    beq v010_not_minus
    inc anim_speed
v010_not_minus:
    lda anim_paused
    bne v010_skip_anim
    inc anim_tick
    lda anim_tick
    cmp anim_speed
    bcc v010_skip_anim
    lda #0
    sta anim_tick
    jsr advance_animation
    .fill 3,$ea // old static-slot capture no longer owns Screen RAM
    jsr s3b2.animate
v010_skip_anim:
    // Stage 2g: snapshot before motion, after motion and after rendering.
    jsr v014_diag_before
    jsr offscreen.r_move
    jsr v014_diag_after_move
    jsr offscreen.r_objects
    jsr v014_diag_before_render
    jsr offscreen.r_tick
    jsr v014_diag_after_render
    jmp main_loop
v010_exit:
    jmp exit_to_basic

// V0.11a: update ONLY the two confirmed GOTOX screen-byte positions
// of the upper-left pixie (rows 4 and 5). No RRB rebuild, no Y offsets.
// CIA1 port A bits 2/3: joystick 2 LEFT/RIGHT, active low.
v011a_move_pixie:
    lda CIA1_PRA
    and #%00000100
    bne v011a_no_left
    lda v011a_x
    cmp #32
    beq v011a_no_left
    dec v011a_x
v011a_no_left:
    lda CIA1_PRA
    and #%00001000
    bne v011a_no_right
    lda v011a_x
    cmp #224
    bcs v011a_no_right
    inc v011a_x
v011a_no_right:
    lda v011a_x
    ldx v011b_reverse
    beq v011b_move_normal
    sta SCREEN_RAM+366
    sta SCREEN_RAM+446
    rts
v011b_move_normal:
    sta SCREEN_RAM+362
    sta SCREEN_RAM+442
    rts
v011a_x: .byte 64
v011b_reverse: .byte 0

// Each upper-row RRB entry = GOTOX (2 bytes) + NCM glyph (2 bytes).
// Swap screen and colour attributes together; do not alter any other RRB entries.
v011b_toggle_order:
    lda v011b_reverse
    eor #1
    sta v011b_reverse
    ldx #0
v011b_swap_all:
    lda SCREEN_RAM+362,x
    pha
    lda SCREEN_RAM+366,x
    sta SCREEN_RAM+362,x
    pla
    sta SCREEN_RAM+366,x
    lda SCREEN_RAM+442,x
    pha
    lda SCREEN_RAM+446,x
    sta SCREEN_RAM+442,x
    pla
    sta SCREEN_RAM+446,x
    lda COLOR_RAM+362,x
    pha
    lda COLOR_RAM+366,x
    sta COLOR_RAM+362,x
    pla
    sta COLOR_RAM+366,x
    lda COLOR_RAM+442,x
    pha
    lda COLOR_RAM+446,x
    sta COLOR_RAM+442,x
    pla
    sta COLOR_RAM+446,x
    inx
    cpx #4
    bne v011b_swap_all
    rts

// The original V0.10a animation routine updates fixed slots.
// When reversed, swap only the newly written glyph IDs after each animation tick.
v011b_fix_order_after_animation:
    lda v011b_reverse
    beq v011b_fix_done
    ldx #0
v011b_swap_glyphs:
    lda SCREEN_RAM+364,x
    pha
    lda SCREEN_RAM+368,x
    sta SCREEN_RAM+364,x
    pla
    sta SCREEN_RAM+368,x
    lda SCREEN_RAM+444,x
    pha
    lda SCREEN_RAM+448,x
    sta SCREEN_RAM+444,x
    pla
    sta SCREEN_RAM+448,x
    inx
    cpx #2
    bne v011b_swap_glyphs
v011b_fix_done:
    rts

// Documentation-based NCM/RRB reference: 16x16 type-3 original, two stacked 16x8 NCM glyphs.
// Each RRB GOTOX is screen x and attribute $90; each visible NCM glyph uses attribute $08.
// Test at rows 4+5 and 7+8, X positions 64, 160 and 256 (all within CRAM2K window).
install_reference_pixies:
    // row 4, X 64, glyph $201
    lda #$40
    sta SCREEN_RAM+362
    lda #$00
    sta SCREEN_RAM+363
    lda #$90
    sta COLOR_RAM+362
    lda #0
    sta COLOR_RAM+363
    lda #$01
    sta SCREEN_RAM+364
    lda #$02
    sta SCREEN_RAM+365
    lda #$08
    sta COLOR_RAM+364
    lda #$00
    sta COLOR_RAM+365
    // row 4, X 160, glyph $201
    lda #$a0
    sta SCREEN_RAM+366
    lda #$00
    sta SCREEN_RAM+367
    lda #$90
    sta COLOR_RAM+366
    lda #0
    sta COLOR_RAM+367
    lda #$01
    sta SCREEN_RAM+368
    lda #$02
    sta SCREEN_RAM+369
    lda #$08
    sta COLOR_RAM+368
    lda #$00
    sta COLOR_RAM+369
    // row 4, X 256, glyph $201
    lda #$00
    sta SCREEN_RAM+370
    lda #$01
    sta SCREEN_RAM+371
    lda #$90
    sta COLOR_RAM+370
    lda #0
    sta COLOR_RAM+371
    lda #$04
    sta SCREEN_RAM+372
    lda #$02
    sta SCREEN_RAM+373
    lda #$08
    sta COLOR_RAM+372
    lda #$00
    sta COLOR_RAM+373
    lda #$40
    sta SCREEN_RAM+398
    lda #$01
    sta SCREEN_RAM+399
    lda #$10
    sta COLOR_RAM+398
    lda #$00
    sta COLOR_RAM+399
    // row 5, X 64, glyph $202
    lda #$40
    sta SCREEN_RAM+442
    lda #$00
    sta SCREEN_RAM+443
    lda #$90
    sta COLOR_RAM+442
    lda #0
    sta COLOR_RAM+443
    lda #$02
    sta SCREEN_RAM+444
    lda #$02
    sta SCREEN_RAM+445
    lda #$08
    sta COLOR_RAM+444
    lda #$00
    sta COLOR_RAM+445
    // row 5, X 160, glyph $202
    lda #$a0
    sta SCREEN_RAM+446
    lda #$00
    sta SCREEN_RAM+447
    lda #$90
    sta COLOR_RAM+446
    lda #0
    sta COLOR_RAM+447
    lda #$02
    sta SCREEN_RAM+448
    lda #$02
    sta SCREEN_RAM+449
    lda #$08
    sta COLOR_RAM+448
    lda #$00
    sta COLOR_RAM+449
    // row 5, X 256, glyph $202
    lda #$00
    sta SCREEN_RAM+450
    lda #$01
    sta SCREEN_RAM+451
    lda #$90
    sta COLOR_RAM+450
    lda #0
    sta COLOR_RAM+451
    lda #$05
    sta SCREEN_RAM+452
    lda #$02
    sta SCREEN_RAM+453
    lda #$08
    sta COLOR_RAM+452
    lda #$00
    sta COLOR_RAM+453
    lda #$40
    sta SCREEN_RAM+478
    lda #$01
    sta SCREEN_RAM+479
    lda #$10
    sta COLOR_RAM+478
    lda #$00
    sta COLOR_RAM+479
    // row 7, X 64, glyph $201
    lda #$40
    sta SCREEN_RAM+602
    lda #$00
    sta SCREEN_RAM+603
    lda #$90
    sta COLOR_RAM+602
    lda #0
    sta COLOR_RAM+603
    lda #$01
    sta SCREEN_RAM+604
    lda #$02
    sta SCREEN_RAM+605
    lda #$08
    sta COLOR_RAM+604
    lda #$00
    sta COLOR_RAM+605
    // row 7, X 160, glyph $201
    lda #$a0
    sta SCREEN_RAM+606
    lda #$00
    sta SCREEN_RAM+607
    lda #$90
    sta COLOR_RAM+606
    lda #0
    sta COLOR_RAM+607
    lda #$01
    sta SCREEN_RAM+608
    lda #$02
    sta SCREEN_RAM+609
    lda #$08
    sta COLOR_RAM+608
    lda #$00
    sta COLOR_RAM+609
    // row 7, X 256, glyph $201
    lda #$00
    sta SCREEN_RAM+610
    lda #$01
    sta SCREEN_RAM+611
    lda #$90
    sta COLOR_RAM+610
    lda #0
    sta COLOR_RAM+611
    lda #$04
    sta SCREEN_RAM+612
    lda #$02
    sta SCREEN_RAM+613
    lda #$08
    sta COLOR_RAM+612
    lda #$00
    sta COLOR_RAM+613
    lda #$40
    sta SCREEN_RAM+638
    lda #$01
    sta SCREEN_RAM+639
    lda #$10
    sta COLOR_RAM+638
    lda #$00
    sta COLOR_RAM+639
    // row 8, X 64, glyph $202
    lda #$40
    sta SCREEN_RAM+682
    lda #$00
    sta SCREEN_RAM+683
    lda #$90
    sta COLOR_RAM+682
    lda #0
    sta COLOR_RAM+683
    lda #$02
    sta SCREEN_RAM+684
    lda #$02
    sta SCREEN_RAM+685
    lda #$08
    sta COLOR_RAM+684
    lda #$00
    sta COLOR_RAM+685
    // row 8, X 160, glyph $202
    lda #$a0
    sta SCREEN_RAM+686
    lda #$00
    sta SCREEN_RAM+687
    lda #$90
    sta COLOR_RAM+686
    lda #0
    sta COLOR_RAM+687
    lda #$02
    sta SCREEN_RAM+688
    lda #$02
    sta SCREEN_RAM+689
    lda #$08
    sta COLOR_RAM+688
    lda #$00
    sta COLOR_RAM+689
    // row 8, X 256, glyph $202
    lda #$00
    sta SCREEN_RAM+690
    lda #$01
    sta SCREEN_RAM+691
    lda #$90
    sta COLOR_RAM+690
    lda #0
    sta COLOR_RAM+691
    lda #$05
    sta SCREEN_RAM+692
    lda #$02
    sta SCREEN_RAM+693
    lda #$08
    sta COLOR_RAM+692
    lda #$00
    sta COLOR_RAM+693
    lda #$40
    sta SCREEN_RAM+718
    lda #$01
    sta SCREEN_RAM+719
    lda #$10
    sta COLOR_RAM+718
    lda #$00
    sta COLOR_RAM+719
    rts

// V0.10: overwrite ONLY screen glyph IDs, preserving verified RRB positions and attributes.
install_animation_pixies:
    lda #$80
    sta SCREEN_RAM+364
    lda #$02
    sta SCREEN_RAM+365
    lda #$81
    sta SCREEN_RAM+444
    lda #$02
    sta SCREEN_RAM+445
    lda #$88
    sta SCREEN_RAM+368
    lda #$02
    sta SCREEN_RAM+369
    lda #$89
    sta SCREEN_RAM+448
    lda #$02
    sta SCREEN_RAM+449
    lda #$96
    sta SCREEN_RAM+372
    lda #$02
    sta SCREEN_RAM+373
    lda #$97
    sta SCREEN_RAM+452
    lda #$02
    sta SCREEN_RAM+453
    lda #$aa
    sta SCREEN_RAM+604
    lda #$02
    sta SCREEN_RAM+605
    lda #$ab
    sta SCREEN_RAM+684
    lda #$02
    sta SCREEN_RAM+685
    lda #$b6
    sta SCREEN_RAM+608
    lda #$02
    sta SCREEN_RAM+609
    lda #$b7
    sta SCREEN_RAM+688
    lda #$02
    sta SCREEN_RAM+689
    lda #$c6
    sta SCREEN_RAM+612
    lda #$02
    sta SCREEN_RAM+613
    lda #$c7
    sta SCREEN_RAM+692
    lda #$02
    sta SCREEN_RAM+693
    rts

advance_animation:
    inc v010_frame_1
    lda v010_frame_1
    cmp #4
    bcc v010_frame_ok_1
    lda #0
    sta v010_frame_1
v010_frame_ok_1:
    tax
    lda v010_t1_toplo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t1_tophi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t1_botlo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t1_bothi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    inc v010_frame_2
    lda v010_frame_2
    cmp #7
    bcc v010_frame_ok_2
    lda #0
    sta v010_frame_2
v010_frame_ok_2:
    tax
    lda v010_t2_toplo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t2_tophi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t2_botlo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t2_bothi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    inc v010_frame_3
    lda v010_frame_3
    cmp #10
    bcc v010_frame_ok_3
    lda #0
    sta v010_frame_3
v010_frame_ok_3:
    tax
    lda v010_t3_toplo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t3_tophi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t3_botlo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t3_bothi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    inc v010_frame_4
    lda v010_frame_4
    cmp #6
    bcc v010_frame_ok_4
    lda #0
    sta v010_frame_4
v010_frame_ok_4:
    tax
    lda v010_t4_toplo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t4_tophi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t4_botlo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t4_bothi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    inc v010_frame_5
    lda v010_frame_5
    cmp #8
    bcc v010_frame_ok_5
    lda #0
    sta v010_frame_5
v010_frame_ok_5:
    tax
    lda v010_t5_toplo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t5_tophi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t5_botlo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t5_bothi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    inc v010_frame_6
    lda v010_frame_6
    cmp #6
    bcc v010_frame_ok_6
    lda #0
    sta v010_frame_6
v010_frame_ok_6:
    tax
    lda v010_t6_toplo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t6_tophi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t6_botlo,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    lda v010_t6_bothi,x
    .fill 3,$ea // retire unused fixed-slot writes; frame counters remain
    rts

v010_t1_toplo:
.byte $80,$82,$84,$86
v010_t1_tophi:
.byte $02,$02,$02,$02
v010_t1_botlo:
.byte $81,$83,$85,$87
v010_t1_bothi:
.byte $02,$02,$02,$02
v010_t2_toplo:
.byte $88,$8a,$8c,$8e,$90,$92,$94
v010_t2_tophi:
.byte $02,$02,$02,$02,$02,$02,$02
v010_t2_botlo:
.byte $89,$8b,$8d,$8f,$91,$93,$95
v010_t2_bothi:
.byte $02,$02,$02,$02,$02,$02,$02
v010_t3_toplo:
.byte $96,$98,$9a,$9c,$9e,$a0,$a2,$a4,$a6,$a8
v010_t3_tophi:
.byte $02,$02,$02,$02,$02,$02,$02,$02,$02,$02
v010_t3_botlo:
.byte $97,$99,$9b,$9d,$9f,$a1,$a3,$a5,$a7,$a9
v010_t3_bothi:
.byte $02,$02,$02,$02,$02,$02,$02,$02,$02,$02
v010_t4_toplo:
.byte $aa,$ac,$ae,$b0,$b2,$b4
v010_t4_tophi:
.byte $02,$02,$02,$02,$02,$02
v010_t4_botlo:
.byte $ab,$ad,$af,$b1,$b3,$b5
v010_t4_bothi:
.byte $02,$02,$02,$02,$02,$02
v010_t5_toplo:
.byte $b6,$b8,$ba,$bc,$be,$c0,$c2,$c4
v010_t5_tophi:
.byte $02,$02,$02,$02,$02,$02,$02,$02
v010_t5_botlo:
.byte $b7,$b9,$bb,$bd,$bf,$c1,$c3,$c5
v010_t5_bothi:
.byte $02,$02,$02,$02,$02,$02,$02,$02
v010_t6_toplo:
.byte $c6,$c8,$ca,$cc,$ce,$d0
v010_t6_tophi:
.byte $02,$02,$02,$02,$02,$02
v010_t6_botlo:
.byte $c7,$c9,$cb,$cd,$cf,$d1
v010_t6_bothi:
.byte $02,$02,$02,$02,$02,$02

anim_speed: .byte 6
anim_tick: .byte 0
anim_paused: .byte 0
v010_frame_1: .byte 0
v010_frame_2: .byte 0
v010_frame_3: .byte 0
v010_frame_4: .byte 0
v010_frame_5: .byte 0
v010_frame_6: .byte 0

check_exit_key:
    jsr KERNAL_GETIN
    cmp #KEY_X
    beq exit_requested
    clc
    rts
exit_requested:
    sec
    rts

read_joystick:
    // Reliable MEGA65 joystick port 2 read.
    // CRAM2K MUST be clear here or $DC00 is Color RAM instead of CIA1.
    sei
    lda #$ff
    sta CIA1_PRA
    lda CIA1_PRA
    sta joy_state
    lda #$7f
    sta CIA1_PRA
    cli

    lda joy_state
    and #%00000100
    bne not_left
    lda player_x
    cmp #PLAYER_MIN_X
    beq not_left
    dec player_x
    dec player_x
not_left:
    lda joy_state
    and #%00001000
    bne not_right
    lda player_x
    cmp #PLAYER_MAX_X
    bcs not_right
    inc player_x
    inc player_x
not_right:
    lda joy_state
    and #%00010000
    bne fire_released
    lda fire_latch
    bne fire_done
    lda #1
    sta fire_latch
    lda shot1_active
    beq start_shot1
    lda shot2_active
    beq start_shot2
    jmp fire_done
start_shot1:
    lda #1
    sta shot1_active
    lda player_x
    sec
    sbc #4
    sta shot1_x
    lda #SHOT_START_Y
    sta shot1_y
    jmp fire_done
start_shot2:
    lda #1
    sta shot2_active
    lda player_x
    sec
    sbc #4
    sta shot2_x
    lda #SHOT_START_Y
    sta shot2_y
    jmp fire_done
fire_released:
    lda #0
    sta fire_latch
fire_done:
    rts

update_shots:
    lda shot1_active
    beq us1_off
    lda shot1_y
    cmp #34
    bcc us1_kill
    sec
    sbc #2
    sta shot1_y
    lda shot1_x
    sta VIC_SPR1_X
    lda shot1_y
    sta VIC_SPR1_Y
    jmp us1_done
us1_kill:
    lda #0
    sta shot1_active
us1_off:
    lda #0
    sta VIC_SPR1_Y
us1_done:
    lda shot2_active
    beq us2_off
    lda shot2_y
    cmp #34
    bcc us2_kill
    sec
    sbc #2
    sta shot2_y
    lda shot2_x
    sta VIC_SPR2_X
    lda shot2_y
    sta VIC_SPR2_Y
    rts
us2_kill:
    lda #0
    sta shot2_active
us2_off:
    lda #0
    sta VIC_SPR2_Y
    rts

update_player_sprite:
    lda player_x
    sta VIC_SPR0_X
    lda #PLAYER_Y
    sta VIC_SPR0_Y
    rts

// -----------------------------------------------------------------------------
// Projectile vs 16x16 RRB pixie collision.
//
// enemy_x/enemy_y are RRB screen coordinates. Hardware sprite coordinates use
// the VIC visible-area origin, hence +24 X and +50 Y for this 40-column mode.
// The projectile graphic is centred in its 24-pixel sprite: centre X = shot_x+12.
// Its visible beam occupies the first five sprite rows.
//
// A hit changes only the struck actor to STATE_EXPLODING. Its current enemy_x
// is retained, so the explosion remains at the collision position while the
// rest of the formation continues to move.
// -----------------------------------------------------------------------------
check_shot_collisions:
    lda shot1_active
    beq csc_shot2
    lda shot1_x
    clc
    adc #12
    sta collision_x
    lda shot1_y
    sta collision_y
    lda #1
    sta collision_shot
    jsr collision_scan
csc_shot2:
    lda shot2_active
    beq csc_done
    lda shot2_x
    clc
    adc #12
    sta collision_x
    lda shot2_y
    sta collision_y
    lda #2
    sta collision_shot
    jsr collision_scan
csc_done:
    rts

collision_scan:
    ldx #0
cs_loop:
    lda enemy_state,x
    cmp #STATE_FORMATION
    bne cs_next

    // Y: use an inset hitbox inside the 16x16 pixie.
    // Visible test range is enemy_y+52 .. enemy_y+62.  This deliberately
    // ignores transparent outer rows, so an upward shot is not registered
    // several pixels before it visibly reaches the enemy.
    lda enemy_y,x
    clc
    adc #52
    sta collision_enemy_y
    lda collision_y
    clc
    adc #4
    cmp collision_enemy_y
    bcc cs_next
    lda collision_y
    sec
    sbc collision_enemy_y
    cmp #11
    bcs cs_next

    // X: projectile centre must be within enemy_x+24 .. enemy_x+39.
    lda enemy_x,x
    clc
    adc #24
    sta collision_enemy_x
    lda collision_x
    cmp collision_enemy_x
    bcc cs_next
    sec
    sbc collision_enemy_x
    cmp #16
    bcs cs_next

    // HIT
    lda #STATE_EXPLODING
    sta enemy_state,x
    lda #0
    sta enemy_explosion_frame,x
    sta enemy_explosion_delay,x

    lda collision_shot
    cmp #1
    bne cs_kill_shot2
    lda #0
    sta shot1_active
    sta VIC_SPR1_Y
    rts
cs_kill_shot2:
    lda #0
    sta shot2_active
    sta VIC_SPR2_Y
    rts

cs_next:
    inx
    cpx #16
    bne cs_loop
    rts

// Original Vyper explosion frames 0..7.
// One explosion frame every 3 game frames; afterwards the actor becomes DEAD.
update_explosions:
    ldx #0
uxe_loop:
    lda enemy_state,x
    cmp #STATE_EXPLODING
    bne uxe_next
    inc enemy_explosion_delay,x
    lda enemy_explosion_delay,x
    cmp #3
    bcc uxe_next
    lda #0
    sta enemy_explosion_delay,x
    inc enemy_explosion_frame,x
    lda enemy_explosion_frame,x
    cmp #8
    bcc uxe_next
    lda #STATE_DEAD
    sta enemy_state,x
uxe_next:
    inx
    cpx #16
    bne uxe_loop
    rts

update_formation:
    // V0.14b diagnostic mode: keep all enemies fixed for animation inspection.
    rts
    lda formation_dir
    beq formation_left
    inc formation_origin_x
    lda formation_origin_x
    cmp #12
    bcc uf_done
    lda #0
    sta formation_dir
    rts
formation_left:
    dec formation_origin_x
    lda formation_origin_x
    cmp #8
    bcs uf_done
    lda #1
    sta formation_dir
uf_done:
    rts

update_animation:
    inc anim_delay
    lda anim_delay
    cmp #6
    bcc ua_done
    lda #0
    sta anim_delay
    inc anim_frame
    lda anim_frame
    cmp #7
    bcc ua_done
    lda #0
    sta anim_frame
ua_done:
    rts

stress_phase: .byte 0
stress_dir: .byte 1
stress_advance:
    lda stress_dir
    beq stress_left
    inc stress_phase
    lda stress_phase
    cmp #16
    bne stress_done
    lda #0
    sta stress_dir
    jmp stress_done
stress_left:
    dec stress_phase
    bne stress_done
    lda #1
    sta stress_dir
stress_done:
    rts
render_enemies:
    lda stress_phase
    clc
    adc #10
    sta $5200
    lda stress_phase
    clc
    adc #10
    sta $5250
    lda stress_phase
    clc
    adc #31
    sta $5204
    lda stress_phase
    clc
    adc #31
    sta $5254
    lda stress_phase
    clc
    adc #52
    sta $5208
    lda stress_phase
    clc
    adc #52
    sta $5258
    lda stress_phase
    clc
    adc #73
    sta $520c
    lda stress_phase
    clc
    adc #73
    sta $525c
    lda stress_phase
    clc
    adc #94
    sta $5210
    lda stress_phase
    clc
    adc #94
    sta $5260
    lda stress_phase
    clc
    adc #115
    sta $5214
    lda stress_phase
    clc
    adc #115
    sta $5264
    lda stress_phase
    clc
    adc #136
    sta $5218
    lda stress_phase
    clc
    adc #136
    sta $5268
    lda stress_phase
    clc
    adc #157
    sta $521c
    lda stress_phase
    clc
    adc #157
    sta $526c
    lda stress_phase
    clc
    adc #178
    sta $5220
    lda stress_phase
    clc
    adc #178
    sta $5270
    lda stress_phase
    clc
    adc #199
    sta $5224
    lda stress_phase
    clc
    adc #199
    sta $5274
    lda stress_phase
    clc
    adc #220
    sta $5228
    lda stress_phase
    clc
    adc #220
    sta $5278
    lda stress_phase
    clc
    adc #10
    sta $5340
    lda stress_phase
    clc
    adc #10
    sta $5390
    lda stress_phase
    clc
    adc #31
    sta $5344
    lda stress_phase
    clc
    adc #31
    sta $5394
    lda stress_phase
    clc
    adc #52
    sta $5348
    lda stress_phase
    clc
    adc #52
    sta $5398
    lda stress_phase
    clc
    adc #73
    sta $534c
    lda stress_phase
    clc
    adc #73
    sta $539c
    lda stress_phase
    clc
    adc #94
    sta $5350
    lda stress_phase
    clc
    adc #94
    sta $53a0
    lda stress_phase
    clc
    adc #115
    sta $5354
    lda stress_phase
    clc
    adc #115
    sta $53a4
    lda stress_phase
    clc
    adc #136
    sta $5358
    lda stress_phase
    clc
    adc #136
    sta $53a8
    lda stress_phase
    clc
    adc #157
    sta $535c
    lda stress_phase
    clc
    adc #157
    sta $53ac
    lda stress_phase
    clc
    adc #178
    sta $5360
    lda stress_phase
    clc
    adc #178
    sta $53b0
    lda stress_phase
    clc
    adc #199
    sta $5364
    lda stress_phase
    clc
    adc #199
    sta $53b4
    lda stress_phase
    clc
    adc #220
    sta $5368
    lda stress_phase
    clc
    adc #220
    sta $53b8
    lda stress_phase
    clc
    adc #10
    sta $5480
    lda stress_phase
    clc
    adc #37
    sta $54d0
    lda stress_phase
    clc
    adc #64
    sta $5520
    lda stress_phase
    clc
    adc #91
    sta $5570
    lda stress_phase
    clc
    adc #118
    sta $55c0
    lda stress_phase
    clc
    adc #145
    sta $5610
    lda stress_phase
    clc
    adc #172
    sta $5660
    lda stress_phase
    clc
    adc #199
    sta $56b0
    rts
init_enemy_state:
    ldx #0
ies_loop:
    lda #STATE_FORMATION
    sta enemy_state,x
    lda formation_slot_y,x
    sta enemy_y,x
    inx
    cpx #16
    bne ies_loop
    rts

// Save/restore the complete 2KB Color RAM window used by the normal
// 80-column BASIC screen.  These routines are called only with CRAM2K enabled.
save_basic_color_ram:
    ldx #0
sbcr_loop:
    lda $d800,x
    sta BASIC_COLOR_BACKUP+$000,x
    lda $d900,x
    sta BASIC_COLOR_BACKUP+$100,x
    lda $da00,x
    sta BASIC_COLOR_BACKUP+$200,x
    lda $db00,x
    sta BASIC_COLOR_BACKUP+$300,x
    lda $dc00,x
    sta BASIC_COLOR_BACKUP+$400,x
    lda $dd00,x
    sta BASIC_COLOR_BACKUP+$500,x
    lda $de00,x
    sta BASIC_COLOR_BACKUP+$600,x
    lda $df00,x
    sta BASIC_COLOR_BACKUP+$700,x
    inx
    bne sbcr_loop
    rts

restore_basic_color_ram:
    ldx #0
rbcr_loop:
    lda BASIC_COLOR_BACKUP+$000,x
    sta $d800,x
    lda BASIC_COLOR_BACKUP+$100,x
    sta $d900,x
    lda BASIC_COLOR_BACKUP+$200,x
    sta $da00,x
    lda BASIC_COLOR_BACKUP+$300,x
    sta $db00,x
    lda BASIC_COLOR_BACKUP+$400,x
    sta $dc00,x
    lda BASIC_COLOR_BACKUP+$500,x
    sta $dd00,x
    lda BASIC_COLOR_BACKUP+$600,x
    sta $de00,x
    lda BASIC_COLOR_BACKUP+$700,x
    sta $df00,x
    inx
    bne rbcr_loop
    rts

copy_color_template:
    ldx #0
cct0:
    lda COLOR_TEMPLATE+$000,x
    sta COLOR_RAM+$000,x
    lda COLOR_TEMPLATE+$100,x
    sta COLOR_RAM+$100,x
    lda COLOR_TEMPLATE+$200,x
    sta COLOR_RAM+$200,x
    lda COLOR_TEMPLATE+$300,x
    sta COLOR_RAM+$300,x
    lda COLOR_TEMPLATE+$400,x
    sta COLOR_RAM+$400,x
    lda COLOR_TEMPLATE+$500,x
    sta COLOR_RAM+$500,x
    lda COLOR_TEMPLATE+$600,x
    sta COLOR_RAM+$600,x
    inx
    bne cct0
    ldx #0
cct1:
    cpx #208
    beq cct_done
    lda COLOR_TEMPLATE+$700,x
    sta COLOR_RAM+$700,x
    inx
    bne cct1
cct_done:
    rts

init_palette:
    // D070 (VIC-IV):
    // bits 7-6 MAPEDPAL  : palette bank mapped at $D100-$D3FF
    // bits 5-4 BTPALSEL  : bitmap/text (therefore RRB/NCM) palette bank
    // bits 3-2 SPRPALSEL : sprite palette bank
    // bits 1-0 ABTPALSEL : alternate bitmap/text palette bank
    //
    // RRB/NCM shall use bank 1, sprites bank 2.
    // First map bank 1 while selecting BTPAL=1 and SPRPAL=2:
    //   MAPEDPAL=1 ($40) + BTPALSEL=1 ($10) + SPRPALSEL=2 ($08) = $58.
    lda #$58
    sta VIC_PALSEL
    ldx #0
ip_enemy_loop:
    lda enemy_palette_r,x
    sta $d100,x
    lda enemy_palette_g,x
    sta $d200,x
    lda enemy_palette_b,x
    sta $d300,x
    inx
    cpx #16
    bne ip_enemy_loop

    // Then map bank 2 while leaving the display selections unchanged:
    //   MAPEDPAL=2 ($80) + BTPALSEL=1 ($10) + SPRPALSEL=2 ($08) = $98.
    lda #$98
    sta VIC_PALSEL
    ldx #0
ip_player_loop:
    lda player_palette_r,x
    sta $d100,x
    lda player_palette_g,x
    sta $d200,x
    lda player_palette_b,x
    sta $d300,x
    inx
    cpx #16
    bne ip_player_loop
    rts

init_sprites:
    // Sprite 0: VIC-IV full-colour + extra-wide => true 16x16 pixels, 4 bpp.
    // Sprites 1/2 remain the existing monochrome projectile sprites.
    lda VIC_SPR16EN
    ora #%00000001
    sta VIC_SPR16EN
    lda VIC_SPRX64EN
    ora #%00000001
    sta VIC_SPRX64EN

    // Dedicated 16-bit pointer table.
    lda #<SPRPTR_TABLE
    sta VIC_SPRPTRLO
    lda #>SPRPTR_TABLE
    sta VIC_SPRPTRHI
    lda #$80
    sta VIC_SPRPTRBK

    lda #<PLAYER_PTR16
    sta SPRPTR_TABLE+0
    lda #>PLAYER_PTR16
    sta SPRPTR_TABLE+1
    lda #<SHOT_PTR16
    sta SPRPTR_TABLE+2
    sta SPRPTR_TABLE+4
    lda #>SHOT_PTR16
    sta SPRPTR_TABLE+3
    sta SPRPTR_TABLE+5

    lda #1
    sta SPR0_COLOR
    lda #5
    sta SPR1_COLOR
    sta SPR2_COLOR

    lda #0
    sta VIC_XMSB
    lda #%00000111
    sta VIC_SPREN
    jsr update_player_sprite
    lda #0
    sta VIC_SPR1_Y
    sta VIC_SPR2_Y
    rts

exit_to_basic:
    jsr hud.hud_restore_scale
    sei
    lda #0
    sta VIC_XMSB

    // First expose the complete 2KB Color RAM window and put back the exact
    // BASIC/KERNAL colour + attribute bytes that RRB/SEAM overwrote.
    lda VIC_D030
    ora #%00000001
    sta VIC_D030
    jsr restore_basic_color_ram

    // Now use the restoration strategy already proven by V0.10:
    // HOTREG disabled, restore the exact saved VIC-IV state directly,
    // and restore HOTREG last.
    lda VIC_HOTREG
    and #%01111111
    sta VIC_HOTREG
    sta VIC_HOTREG

    lda saved_d030
    sta VIC_D030
    lda saved_d031
    sta VIC_D031
    lda saved_d054
    sta VIC_D054

    lda saved_d058
    sta VIC_LINESTEP_LO
    lda saved_d059
    sta VIC_LINESTEP_HI
    lda saved_d05e
    sta VIC_CHRCOUNT

    lda saved_d060
    sta VIC_SCRNPTR_LO
    lda saved_d061
    sta VIC_SCRNPTR_MI
    lda saved_d062
    sta VIC_SCRNPTR_HI
    lda saved_d063
    sta VIC_SCRNPTR_XHI

    lda saved_d064
    sta VIC_COLPTR_LO
    lda saved_d065
    sta VIC_COLPTR_HI

    lda saved_d068
    sta VIC_CHARPTR_LO
    lda saved_d069
    sta VIC_CHARPTR_HI
    lda saved_d06a
    sta VIC_CHARPTR_BK

    lda saved_d07b
    sta VIC_DISPROWS

    lda saved_d06b
    sta VIC_SPR16EN
    lda saved_d057
    sta VIC_SPRX64EN

    lda saved_d06c
    sta VIC_SPRPTRLO
    lda saved_d06d
    sta VIC_SPRPTRHI
    lda saved_d06e
    sta VIC_SPRPTRBK

    lda saved_d070
    sta VIC_PALSEL

    // HOTREG last: do not replay the legacy registers here.
    lda saved_d05d
    sta VIC_HOTREG

    lda saved_border
    sta VIC_BORDER
    lda saved_bg
    sta VIC_BG
    cli
    rts

// -----------------------------------------------------------------------------
// Runtime state. Actor fields already separate formation identity from render data.
// Future attack states can change enemy_x/enemy_y while formation_slot_x/y remain.
// -----------------------------------------------------------------------------
player_x: .byte 150
joy_state: .byte $ff
fire_latch: .byte 0
shot1_active: .byte 0
shot1_x: .byte 0
shot1_y: .byte 0
shot2_active: .byte 0
shot2_x: .byte 0
shot2_y: .byte 0
formation_origin_x: .byte 0
formation_dir: .byte 1
anim_frame: .byte 0
anim_delay: .byte 0

enemy_state: .fill 16,STATE_FORMATION
enemy_x: .fill 16,0
enemy_y: .fill 16,0
enemy_vx_lo: .fill 16,0
enemy_vx_hi: .fill 16,0
enemy_vy_lo: .fill 16,0
enemy_vy_hi: .fill 16,0
enemy_attack_type: .fill 16,0
enemy_attack_phase: .fill 16,0
enemy_attack_timer: .fill 16,0
enemy_explosion_frame: .fill 16,0
enemy_explosion_delay: .fill 16,0
collision_x: .byte 0
collision_y: .byte 0
collision_enemy_x: .byte 0
collision_enemy_y: .byte 0
collision_shot: .byte 0
enemy_formation_slot:
.byte 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
formation_slot_x:
.byte 0,28,56,84,112,140,168,196
.byte 0,28,56,84,112,140,168,196
formation_slot_y:
.byte 40,40,40,40,40,40,40,40
.byte 72,72,72,72,72,72,72,72

enemy_top_char_lo:
.byte $01,$03,$05,$07,$09,$0b,$0d
enemy_bottom_char_lo:
.byte $02,$04,$06,$08,$0a,$0c,$0e
explosion_top_char_lo:
.byte $0f,$11,$13,$15,$17,$19,$1b,$1d
explosion_bottom_char_lo:
.byte $10,$12,$14,$16,$18,$1a,$1c,$1e

// V0.9c: enemy palette copied verbatim from vyperlike_v020.asm.
// Indices 3/4 are approximate in original source; indices 0..8 are used by enemy.
// NCM geometry and byte order are unchanged from V0.9b.
enemy_palette_r:
.byte $00,$00,$ff,$ee,$77,$88,$33,$55,$aa,$00,$ff,$22,$ff,$ff,$00,$00
enemy_palette_g:
.byte $00,$00,$ff,$00,$22,$99,$44,$66,$bb,$00,$ff,$66,$00,$ff,$00,$00
enemy_palette_b:
.byte $00,$00,$ff,$88,$33,$99,$44,$66,$bb,$0c,$00,$ff,$00,$ff,$00,$00

// Player palette bank 2. Index 0 is transparent.
// Grey/white hull, blue cockpit and warm engine colours.
player_palette_r:
.byte $00,$02,$04,$06,$08,$0a,$0c,$0e,$0f,$0f,$0f,$0d,$09,$05,$02,$0f
player_palette_g:
.byte $00,$02,$04,$06,$08,$0a,$0c,$0e,$0f,$0b,$07,$04,$08,$0b,$0e,$0f
player_palette_b:
.byte $00,$02,$04,$06,$08,$0a,$0c,$0e,$0f,$02,$00,$00,$0f,$0f,$0f,$08

saved_border: .byte 0
saved_bg: .byte 0
saved_d011: .byte 0
saved_d016: .byte 0
saved_d018: .byte 0
saved_dd00: .byte 0
saved_d030: .byte 0
saved_d031: .byte 0
saved_d054: .byte 0
saved_d05d: .byte 0
saved_d058: .byte 0
saved_d059: .byte 0
saved_d05e: .byte 0
saved_d060: .byte 0
saved_d061: .byte 0
saved_d062: .byte 0
saved_d063: .byte 0
saved_d064: .byte 0
saved_d065: .byte 0
saved_d068: .byte 0
saved_d069: .byte 0
saved_d06a: .byte 0
saved_d057: .byte 0
saved_d06b: .byte 0
saved_d06c: .byte 0
saved_d06d: .byte 0
saved_d06e: .byte 0
saved_d070: .byte 0
saved_d07b: .byte 0

// -----------------------------------------------------------------------------
// Hardware sprite graphics: 16x16 VIC-IV full-colour player + projectile.
// -----------------------------------------------------------------------------
*=$3000
player_sprite_16colour:
.byte $00,$00,$00,$07,$70,$00,$00,$00
.byte $00,$00,$00,$7a,$a7,$00,$00,$00
.byte $00,$00,$07,$ab,$ba,$70,$00,$00
.byte $00,$00,$07,$ab,$ba,$70,$00,$00
.byte $00,$00,$7a,$ab,$ba,$a7,$00,$00
.byte $00,$00,$7a,$ac,$ca,$a7,$00,$00
.byte $00,$07,$aa,$ac,$ca,$aa,$70,$00
.byte $00,$7a,$aa,$bc,$cb,$aa,$a7,$00
.byte $07,$aa,$aa,$bc,$cb,$aa,$aa,$70
.byte $7a,$aa,$ab,$bb,$bb,$ba,$aa,$a7
.byte $77,$aa,$ab,$bb,$bb,$ba,$aa,$77
.byte $00,$7a,$ab,$bb,$bb,$bb,$a7,$00
.byte $00,$07,$aa,$bb,$bb,$aa,$70,$00
.byte $00,$07,$7a,$ab,$ba,$a7,$70,$00
.byte $00,$0d,$7a,$77,$77,$a7,$e0,$00
.byte $00,$dd,$70,$00,$00,$7e,$e0,$00

// Full-colour sprite 0 is still fetched through the VIC sprite engine.
// Keep bytes 128..168 transparent so its visible image is exactly 16x16.
.fill 41,0

// Next safe 64-byte boundary after the full player sprite fetch area.
*=$30c0
shot_sprite:
.byte 0,$18,0
.byte 0,$18,0
.byte 0,$18,0
.byte 0,$18,0
.byte 0,$18,0
.fill 48,0
.byte 0

*=$4000
.fill $800,0

// -----------------------------------------------------------------------------
// RRB screen data. 25 rows * 40 SEAM entries * 2 bytes = 2000 bytes.
// Each row starts with GOTOX 0 + 15 opaque blank NCM chars (240px background).
// Formation rows then append transparent GOTOX + NCM pixie pairs.
// Each row ends with GOTOX 320 plus one NCM char.
// GOTOX high bits are in screen byte 1 bits 0..1 (NOT constant 1).
// -----------------------------------------------------------------------------
*=$5000
// Row 6 no GOTOX; row 14 with GOTOX.
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0040,$0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0000,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0140,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200
.word $0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200,$0200

*=$5c80
.fill 16,0

*=$6000
// Row 6 all FCM; row 14 RRB GOTOX + FCM.
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
.word $0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
.word $0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
.word $0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000,$0000
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0090,$0000,$0010,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0010,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008
.word $0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008,$0008

*=$8000
// glyph $200 blank, $201 upper 16x8, $202 lower 16x8
 .fill 64,0
.byte $00,$00,$00,$55,$55,$70,$00,$00
.byte $00,$00,$55,$88,$38,$55,$70,$00
.byte $00,$05,$88,$87,$77,$85,$57,$00
.byte $00,$05,$85,$58,$88,$76,$57,$00
.byte $00,$58,$25,$28,$68,$86,$57,$70
.byte $00,$58,$52,$28,$88,$88,$67,$60
.byte $00,$53,$58,$68,$88,$68,$63,$60
.byte $00,$58,$58,$88,$88,$88,$67,$60
.byte $00,$58,$85,$88,$68,$86,$77,$60
.byte $00,$05,$87,$78,$88,$66,$76,$00
.byte $00,$07,$55,$56,$66,$77,$76,$00
.byte $00,$00,$77,$77,$37,$66,$60,$00
.byte $00,$00,$80,$77,$66,$60,$70,$00
.byte $00,$00,$72,$11,$01,$26,$60,$00
.byte $00,$00,$00,$00,$00,$00,$00,$00
.byte $00,$00,$00,$00,$00,$00,$00,$00

// Glyph $204/$205: same pixels as $201/$202, each byte nibble-swapped.
*=$8100
.byte $00,$00,$00,$55,$55,$07,$00,$00
.byte $00,$00,$55,$88,$83,$55,$07,$00
.byte $00,$50,$88,$78,$77,$58,$75,$00
.byte $00,$50,$58,$85,$88,$67,$75,$00
.byte $00,$85,$52,$82,$86,$68,$75,$07
.byte $00,$85,$25,$82,$88,$88,$76,$06
.byte $00,$35,$85,$86,$88,$86,$36,$06
.byte $00,$85,$85,$88,$88,$88,$76,$06
.byte $00,$85,$58,$88,$86,$68,$77,$06
.byte $00,$50,$78,$87,$88,$66,$67,$00
.byte $00,$70,$55,$65,$66,$77,$67,$00
.byte $00,$00,$77,$77,$73,$66,$06,$00
.byte $00,$00,$08,$77,$66,$06,$07,$00
.byte $00,$00,$27,$11,$10,$62,$06,$00
.byte $00,$00,$00,$00,$00,$00,$00,$00
.byte $00,$00,$00,$00,$00,$00,$00,$00

*=$8800
// 2-pixel wide NCM test shot (one packed byte per raster line)
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00
.byte $00,$00,$00,$66,$00,$00,$00,$00

*=$9000
BASIC_COLOR_BACKUP:
.fill $800,0

// Alternate base $4000 -> glyph $201 starts at $C040.
// Deliberately reversed: $201 red, $202 white.
*=$a000
// First six original Vyper enemy types: packed NCM, 128 bytes per frame
.import binary "vyper_original_animation_assets_v010/type_01/anim_00_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_01/anim_01_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_01/anim_02_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_01/anim_03_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_00_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_01_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_02_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_03_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_04_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_05_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_02/anim_06_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_00_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_01_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_02_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_03_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_04_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_05_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_06_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_07_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_08_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_03/anim_09_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_04/anim_00_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_04/anim_01_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_04/anim_02_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_04/anim_03_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_04/anim_04_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_04/anim_05_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_00_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_01_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_02_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_03_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_04_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_05_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_06_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_05/anim_07_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_06/anim_00_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_06/anim_01_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_06/anim_02_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_06/anim_03_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_06/anim_04_ncm.bin"
.import binary "vyper_original_animation_assets_v010/type_06/anim_05_ncm.bin"

*=$b800

// V0.12a: move one type-1 pixie using validated RRB structure.
// Rows 2..21 use dedicated dynamic slots. On occupied formation rows
// 4,5,7,8 use byte offset 54, AFTER all three existing static pixies.
// On other rows use byte offset 42, replacing the old terminator.
// All other entries, including the 15 opaque background chars, stay intact.
// Rows 4/5 contain the five stationary pixies (type 1 is blanked).
// Screen RAM is modified only; Color RAM setup happens before CRAM2K is disabled.
// Movement starts on row 10 and is constrained to top rows 2..20.
// Direction UP/DOWN triggers once per press; horizontal remains 1px/frame.
v012a_init:
    lda #64
    sta v011a_x
    lda #10
    sta v012a_row
    sta v012a_prev_row
    lda #0
    sta v013_suby
    sta v012a_y_latch
    // Initialise two animation glyphs from original fixed positions.
    lda SCREEN_RAM+364
    sta v012a_top_lo
    lda SCREEN_RAM+365
    sta v012a_top_hi
    lda SCREEN_RAM+444
    sta v012a_bot_lo
    lda SCREEN_RAM+445
    sta v012a_bot_hi
    jsr v013d_copy_glyphs
    jsr v012a_blank_original
    // Prepare each candidate row's 4-byte slot and its GOTOX 320 sentinel.
    // This avoids overwriting the end-of-row marker (V0.12 regression).
    // Row 6 in the original diagnostic uses plain FCM without RRB.
    // Replace its screen and colour template with a known-good empty RRB row.
    ldx #0
v012b_copy_row6:
    lda SCREEN_RAM+9*80,x
    sta SCREEN_RAM+6*80,x
    lda COLOR_RAM+9*80,x
    sta COLOR_RAM+6*80,x
    inx
    cpx #80
    bne v012b_copy_row6
    ldx #0
v012a_init_loop:
    jsr v012a_set_row_pointer
    ldy #0
    lda #0
    jsr v012a_store
    iny
    jsr v012a_store
    iny
    jsr v012a_store
    iny
    lda #2
    jsr v012a_store
    iny
    lda #$40              // GOTOX 320 = $0140
    jsr v012a_store
    iny
    lda #$01
    jsr v012a_store
    iny
    lda #0                // blank NCM $0200
    jsr v012a_store
    iny
    lda #2
    jsr v012a_store
    // Color RAM is $D800 + same 80-byte row stride, slot at byte 42.
    // While CRAM2K is still on, the entire 2KB color RAM is CPU-visible.
    jsr v012a_set_color_pointer
    ldy #0
    lda #$90              // GOTOX
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    iny
    lda #$08              // NCM
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    iny
    lda #$10              // GOTOX 320 terminal (same as base)
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    iny
    lda #$08
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    inx
    cpx #25
    bne v012a_init_loop
    // Stage 2c: initialise each row with ZERO active dynamic fragments.
    // Do not emit any placeholder GOTOX records at X=0.
    // A single terminator is placed at the FIRST available slot.
    ldx #0
v014_prepare_row:
    stx v014_row
    lda #0
    sta v014_row_count,x
    jsr v014_write_terminator
    ldx v014_row
    inx
    cpx #25
    bne v014_prepare_row
    jsr v014_render_all
    rts

v012a_blank_original:
    lda #0
    sta SCREEN_RAM+364
    sta SCREEN_RAM+444
    lda #2
    sta SCREEN_RAM+365
    sta SCREEN_RAM+445
    rts

v012a_capture_animation:
    lda SCREEN_RAM+364
    sta v012a_top_lo
    lda SCREEN_RAM+365
    sta v012a_top_hi
    lda SCREEN_RAM+444
    sta v012a_bot_lo
    lda SCREEN_RAM+445
    sta v012a_bot_hi
    .fill 3,$ea  // keep original player NCM; retain all other animation bookkeeping
    jsr v012a_blank_original
    rts

v012a_move:
    lda CIA1_PRA
    sta v012a_joy
    and #$04
    bne v012a_not_left
    lda v011a_x
    cmp #32
    beq v012a_not_left
    dec v011a_x
v012a_not_left:
    lda v012a_joy
    and #$08
    bne v012a_not_right
    lda v011a_x
    cmp #224
    bcs v012a_not_right
    inc v011a_x
v012a_not_right:
    // V0.13: continuous one-pixel vertical steps (one per main-loop frame).
    lda v012a_joy
    and #$01
    bne v013_down
    lda v012a_row
    cmp #2
    bne v013_up_step
    lda v013_suby
    beq v012a_move_done
v013_up_step:
    lda v013_suby
    bne v013_up_sub
    dec v012a_row
    lda #7
    sta v013_suby
    rts
v013_up_sub:
    dec v013_suby
    rts
v013_down:
    lda v012a_joy
    and #$02
    bne v012a_move_done
    lda v012a_row
    cmp #20
    bcc v013_down_step
    lda v013_suby
    cmp #7
    bcs v012a_move_done
v013_down_step:
    inc v013_suby
    lda v013_suby
    cmp #8
    bcc v012a_move_done
    lda #0
    sta v013_suby
    inc v012a_row
v012a_move_done:
    rts

v012a_render:
    jmp v014_render_all

v013_clear_slot:
    lda #0
    sta v012a_lo
    sta v013_mask
    lda #2
    sta v012a_hi
    lda #0
    sta v013_gotox_hi
    jmp v013_draw_slot

v013_draw_slot:
    // CPU-visible Colour RAM requires CRAM2K; joystick was read beforehand.
    // Preserve the $D030 configuration, restoring CIA access afterwards.
    jsr v012a_write_row
    lda VIC_D030
    ora #1
    sta VIC_D030
    jsr v012a_set_color_pointer
    ldy #0
    lda #$90              // V0.13c: original GOTOX attribute, no row mask
    jsr v012a_store
    iny
    lda #0                // V0.13c: original GOTOX colour byte 1
    jsr v012a_store
    lda VIC_D030
    and #$fe
    sta VIC_D030
    rts

// X = screen row, pointer = $5000 + row*80 + 42.
v012a_set_row_pointer:
    jmp hud.set_row_pointer
    .fill 10,$ea
v012a_set_color_pointer:
    jmp hud.set_colour_pointer
    .fill 10,$ea
v012a_write_row:
    jsr v012a_set_row_pointer
    ldy #0
    lda v011a_x
    jsr v012a_store
    iny
    lda v013_gotox_hi
    jsr v012a_store
    iny
    lda v012a_lo
    jsr v012a_store
    iny
    lda v012a_hi
    jsr v012a_store
    rts

v012a_store:
    jmp hud.store
    rts

// V0.13e: copy original animated NCM glyphs into a four-glyph
// contiguous guard region: blank / top / bottom / blank.
// Character index times 64 is the absolute VIC-IV NCM byte address.
v013d_copy_glyphs:
    lda v012a_top_lo
    sta v013d_glyph_lo
    lda v012a_top_hi
    sta v013d_glyph_hi
    jsr v013d_set_source
    ldy #0
v013d_copy_top:
v013d_src_top:
    lda $ffff,y
    sta $c840,y
    iny
    cpy #64
    bne v013d_copy_top
    lda v012a_bot_lo
    sta v013d_glyph_lo
    lda v012a_bot_hi
    sta v013d_glyph_hi
    jsr v013d_set_source
    ldy #0
v013d_copy_bottom:
v013d_src_bottom:
    lda $ffff,y
    sta $c880,y
    iny
    cpy #64
    bne v013d_copy_bottom
    rts
v013d_set_source:
    // 16-bit glyph index * 64, no zero-page use.
    lda v013d_glyph_lo
    sta v013d_addr_lo
    lda v013d_glyph_hi
    sta v013d_addr_hi
    ldx #6
v013d_shift:
    asl v013d_addr_lo
    rol v013d_addr_hi
    dex
    bne v013d_shift
    lda v013d_addr_lo
    sta v013d_src_top+1
    sta v013d_src_bottom+1
    lda v013d_addr_hi
    sta v013d_src_top+2
    sta v013d_src_bottom+2
    rts
v013d_glyph_lo: .byte 0
v013d_glyph_hi: .byte 0
v013d_addr_lo: .byte 0
v013d_addr_hi: .byte 0

v013_suby: .byte 0
v013_gotox_hi: .byte 0
v013_mask: .byte $ff
v013_yhi: .fill 8, $10+(i<<5)
v013_topmask: .fill 8, ($ff<<i)&$ff
v013_bottommask: .fill 8, (1<<i)-1
v012a_row: .byte 10
v012a_prev_row: .byte 10
v012a_y_latch: .byte 0
v012a_joy: .byte $ff
v012a_lo: .byte 0
v012a_hi: .byte 2
v012a_top_lo: .byte $80
v012a_top_hi: .byte 2
v012a_bot_lo: .byte $81
v012a_bot_hi: .byte 2
// Occupied rows: three static RRB pixies at offsets 42..53.
// Reserve offset 54 for the moving pixie; otherwise use offset 42.
v012a_screen_lo: .fill 25, <(SCREEN_RAM+i*128+84)
v012a_screen_hi: .fill 25, >(SCREEN_RAM+i*128+84)
v012a_color_lo: .fill 25, <(i*128+84)
v012a_color_hi: .fill 25, >(i*128+84)


// Stage 3b-2 exit fix: $1000-$15FF belongs to the KERNAL, including
// ROM V920395 cursor state at $111F-$1123. Use documented free $1600-$1EFF.
// $A000-$BFFF and $C000-$CFFF may be ROM-mapped depending on banking;
// all MUTABLE objects/diagnostics now live below $2000.
.const OBJ_BASE=$1600
.const OBJ_SIZE=24
.const OBJ_COUNT=32
.const OBJ_END=OBJ_BASE+OBJ_SIZE*OBJ_COUNT
.const PLAYER_OBJ=OBJ_BASE+4*OBJ_SIZE
.const ORBIT_OBJ=OBJ_BASE+5*OBJ_SIZE
.const DIAG_BASE=$1900
.const DIAG_SIZE=$20
.const PATH_WORK=$1a00
.const RRB_WORK=$1b00
.const V014_OBJ=OBJ_BASE
.const V014_SIZE=OBJ_SIZE
.const V014_PLAYER=PLAYER_OBJ
.const V014_ORBIT=ORBIT_OBJ
.const V014_PATH=PATH_WORK
.const V014_DIAG=DIAG_BASE
.const V014_DIAG_MAGIC=$5f
// Assembly-time memory guards. Workspaces are reserved, currently unused.
.if (OBJ_BASE < $1600) { .error "Stage3b2: objects overlap KERNAL RAM" }
.if (OBJ_END > DIAG_BASE) { .error "Stage2g: object RAM overlaps diagnostics" }
.if (DIAG_BASE+DIAG_SIZE > PATH_WORK) { .error "Stage2g: diagnostics overlap path workspace" }
.if (PATH_WORK+$100 > RRB_WORK) { .error "Stage3b2: path workspace overlaps RRB workspace" }
.if (RRB_WORK+$400 > $1f00) { .error "Stage3b2: workspace exceeds documented free RAM" }
// ROM-safe source table in $7000 RAM (not $CA00, which may be ROM-mapped).
.const OBJ_INITIAL=$7000
v014_copy_records:
    ldx #0
v014_copy_page0:
    lda OBJ_INITIAL,x
    sta OBJ_BASE,x
    lda OBJ_INITIAL+$100,x
    sta OBJ_BASE+$100,x
    lda OBJ_INITIAL+$200,x
    sta OBJ_BASE+$200,x
    inx
    bne v014_copy_page0
    rts
v014_init_objects:
    jsr v014_copy_records
    lda #112 // (240-16)/2: centred top-left
    sta V014_PLAYER+2
    lda #184 // 200-16: bottom-aligned top-left
    sta V014_PLAYER+4
    lda #0
    sta V014_PLAYER+3
    sta V014_PLAYER+5
    // Orbit sprite: four guarded NCM glyphs at $C900-$C9FF.
    // Type 2, first frame from original graphics at $A200.
    ldx #0
v014_copy_orbit:
    lda $a200,x
    sta $c940,x
    lda $a240,x
    sta $c980,x
    inx
    cpx #64
    bne v014_copy_orbit
    rts
// Stage 2e: ONE authoritative X/Y source: the 24-byte object record.
// Joystick port 2 is sampled once, after explicitly clearing CRAM2K.
// Raw CIA bits and live coordinates are mirrored for memory-monitor diagnosis.
v014_move_record:
    lda VIC_D030
    and #$fe
    sta VIC_D030
    lda CIA1_PRA
    sta v014_joy_sample
    and #$04
    bne v014_no_left
    lda V014_PLAYER+2
    cmp #0
    bcc v014_no_left
    beq v014_no_left
    dec V014_PLAYER+2
v014_no_left:
    lda v014_joy_sample
    and #$08
    bne v014_no_right
    lda V014_PLAYER+2
    cmp #224
    bcs v014_no_right
    inc V014_PLAYER+2
v014_no_right:
    .fill 19,$ea // old vertical-up block, fixed Y=184
v014_no_up:
    .fill 17,$ea // old vertical-down block
v014_no_down:
    // Stage 2g: no writes to spare object-table records.
    rts

// Stage 3b-2: memory-monitor snapshots relocated to $1900..$191F.
// No changes to the RRB writer or object update logic.
v014_diag_before:
    lda #V014_DIAG_MAGIC
    sta V014_DIAG+0
    inc V014_DIAG+1
    lda VIC_D030
    sta V014_DIAG+2
    lda V014_PLAYER+2
    sta V014_DIAG+3
    lda V014_PLAYER+4
    sta V014_DIAG+4
    lda V014_PLAYER+3
    sta V014_DIAG+5
    lda V014_PLAYER+5
    sta V014_DIAG+6
    rts
v014_diag_after_move:
    lda v014_joy_sample
    sta V014_DIAG+7
    lda VIC_D030
    sta V014_DIAG+8
    lda V014_PLAYER+2
    sta V014_DIAG+9
    lda V014_PLAYER+4
    sta V014_DIAG+10
    rts
v014_diag_before_render:
    lda VIC_D030
    sta V014_DIAG+11
    lda V014_PLAYER+2
    sta V014_DIAG+12
    lda V014_PLAYER+4
    sta V014_DIAG+13
    rts
v014_diag_after_render:
    lda VIC_D030
    sta V014_DIAG+14
    lda V014_PLAYER+2
    sta V014_DIAG+15
    lda V014_PLAYER+4
    sta V014_DIAG+16
    lda v014_x
    sta V014_DIAG+17
    lda v014_y
    sta V014_DIAG+18
    lda v014_overflow_count
    sta V014_DIAG+19
    rts

v014_update_objects:
    // No player position copy! The record is the only authoritative source.
    // Clockwise orbit updates the second visible Pixie.
    inc V014_ORBIT+12
    ldx V014_ORBIT+12
    lda v014_orbit_x,x
    sta V014_ORBIT+2
    lda v014_orbit_y,x
    sta V014_ORBIT+4
    // Stage 2ja: 22 phase-offset paths, one update per frame.
    ldx #0
s2i_update:
    stx s2i_index
    lda s2i_phase,x
    clc
    adc s2i_speed,x
    sta s2i_phase,x
    tay
    lda v014_orbit_x,y
    sta s2i_x,x
    lda v014_orbit_y,y
    sta s2i_y,x
    ldx s2i_index
    inx
    cpx #22
    bne s2i_update
    rts

// Stage 2ja: original Vyper type-2 animation, seven 128-byte frames.
// Update only two shared 16x16 glyph pairs; all 23 automatic pixies
// reference $325/$326 and joystick uses its own $321/$322 pair.
// Frame switching runs on the existing animation clock (+/- and SPACE).
s2ja_animate_pixies:
    inc s2ja_frame
    lda s2ja_frame
    cmp #7
    bcc s2ja_frame_valid
    lda #0
    sta s2ja_frame
s2ja_frame_valid:
    tax
    lda s2ja_frame_lo,x
    sta s2ja_source_top+1
    sta s2ja_source_bottom+1
    lda s2ja_frame_hi,x
    sta s2ja_source_top+2
    clc
    adc #$00
    sta s2ja_source_bottom+2
    // Bottom glyph is 64 bytes after top: patch 16-bit address.
    lda s2ja_frame_lo,x
    clc
    adc #64
    sta s2ja_source_bottom+1
    lda s2ja_frame_hi,x
    adc #0
    sta s2ja_source_bottom+2
    ldx #0
s2ja_copy_frame:
s2ja_source_top:
    lda $a200,x
    sta $c940,x
    .fill 3,$ea  // retain orbit animation; player is static original artwork
s2ja_source_bottom:
    lda $a240,x
    sta $c980,x
    .fill 3,$ea  // player bottom glyph must not be animated
    inx
    cpx #64
    bne s2ja_copy_frame
    rts
s2ja_frame: .byte 0
s2ja_frame_lo: .byte <$a200,<$a280,<$a300,<$a380,<$a400,<$a480,<$a500
s2ja_frame_hi: .byte >$a200,>$a280,>$a300,>$a380,>$a400,>$a480,>$a500

v014_joy_sample: .byte $ff


// V0.14 Stage 2e: joystick-record-driven row-bucket compositor.
// Four dynamic slots per row, each slot = GOTOX + one NCM glyph.
// Each sprite submits 2 or 3 row fragments; renderer does not have
// separate fixed paths for joystick and orbit objects.
// Existing stationary entries at byte offsets 42..53 remain untouched.
// Max 4 dynamic fragments per 8-pixel row (capacity, not a performance claim).
.const V014_CAPACITY=8
v014_render_all:
    // Stage 2h: two moving Pixies share the existing row-list renderer.
    // Both have separate guarded NCM glyphs; four static Pixies unchanged.
    lda #0
    sta v014_overflow_count
    ldx #2
v014_reset_row:
    lda #0
    sta v014_row_count,x
    // Stage 2i-a: remove all previous dynamic records, including stale
    // records behind the current end marker. Static prefix untouched.
    jsr s2ia_clear_row
    inx
    cpx #23
    bne v014_reset_row

    // Stage 2d: position from the 24-byte joystick Pixie record.
    // v014_update_objects synchronises this record with the confirmed
    // V0.13e pixel-accurate joystick movement each main-loop iteration.
    lda V014_PLAYER+2
    sta v014_x
    lda V014_PLAYER+4
    sta v014_y
    lda #<$0321
    sta v014_top_lo
    lda #>$0321
    sta v014_top_hi
    lda #<$0322
    sta v014_bot_lo
    lda #>$0322
    sta v014_bot_hi
    lda #<$0323
    sta v014_guard_lo
    lda #>$0323
    sta v014_guard_hi
    jsr v014_submit_pixie

    // Second moving Pixie: clockwise orbit around playfield centre.
    // Its dedicated NCM glyphs were already prepared at $C940/$C980.
    lda V014_ORBIT+2
    sta v014_x
    lda V014_ORBIT+4
    sta v014_y
    lda #<$0325
    sta v014_top_lo
    lda #>$0325
    sta v014_top_hi
    lda #<$0326
    sta v014_bot_lo
    lda #>$0326
    sta v014_bot_hi
    lda #<$0327
    sta v014_guard_lo
    lda #>$0327
    sta v014_guard_hi
    jsr v014_submit_pixie

    // Stage 2i: submit four additional moving Pixies.
    // Reuse orbit glyphs and original 4-slot row capacity.
    ldx #0
s2i_submit:
    stx s2i_index
    lda s2i_x,x
    sta v014_x
    lda s2i_y,x
    sta v014_y
    lda #<$0261
    sta v014_top_lo
    lda #>$0261
    sta v014_top_hi
    lda #<$0262
    sta v014_bot_lo
    lda #>$0262
    sta v014_bot_hi
    lda #<$0263
    sta v014_guard_lo
    lda #>$0263
    sta v014_guard_hi
    jsr v014_submit_pixie
    ldx s2i_index
    inx
    cpx #22
    bne s2i_submit

    ldx #2
v014_finish_rows:
    stx v014_row
    jsr v014_write_terminator
    ldx v014_row
    inx
    cpx #23
    bne v014_finish_rows
    rts

// Stage 2i-a: clear four dynamic slots AND the reserved end marker.
// The existing row pointer tables already point past the stationary Pixies
// (offset 42 or 54). 20 bytes fit in the original 80-byte row.
// No changes to the RRB capacity, tables, or memory layout.
s2ia_clear_row:
    jsr v012a_set_row_pointer
    ldy #0
s2ia_clear_screen:
    lda #0
    jsr v012a_store
    iny
    cpy #36
    bne s2ia_clear_screen
    // Colour RAM is accessed in the same mode as the existing renderer.
    lda VIC_D030
    ora #1
    sta VIC_D030
    jsr v012a_set_color_pointer
    ldy #0
s2ia_clear_color:
    jsr hud.clear_colour_dma
    .fill 7,$ea // same addresses; one DMA copy replaces 36 long byte stores
    lda VIC_D030
    and #$fe
    sta VIC_D030
    rts

v014_submit_pixie:
    // Object Y is top-left pixel coordinate.
    lda v014_y
    and #7
    tax
    lda v013_yhi,x
    sta v014_ybits
    lda v014_y
    lsr
    lsr
    lsr
    sta v014_row
    lda v014_top_lo
    sta v014_glyph_lo
    lda v014_top_hi
    sta v014_glyph_hi
    jsr v014_append
    inc v014_row
    lda v014_bot_lo
    sta v014_glyph_lo
    lda v014_bot_hi
    sta v014_glyph_hi
    jsr v014_append
    lda v014_y
    and #7
    beq v014_no_third
    inc v014_row
    lda v014_guard_lo
    sta v014_glyph_lo
    lda v014_guard_hi
    sta v014_glyph_hi
    jsr v014_append
v014_no_third:
    rts

v014_append:
    ldx v014_row
    cpx #25
    bcs v014_append_done
    .fill 4,$ea // Rows 0..24 valid; preserve every subsequent symbol address.
    lda v014_row_count,x
    cmp #V014_CAPACITY
    bcs v014_append_overflow
    jsr s3b3.player_write_slot
    inc v014_row_count,x
v014_append_done:
    rts
v014_append_overflow:
    inc v014_overflow_count
    rts

v014_write_slot:
    // X = row; offset = 4 * row_count, slot base supplied by V0.13e.
    lda v014_row_count,x
    asl
    asl
    sta v014_offset
    jsr v012a_set_row_pointer
    ldy v014_offset
    jsr hud.hud_write_x
    .fill 10,$ea
    iny
    lda v014_glyph_lo
    jsr v012a_store
    iny
    lda v014_glyph_hi
    jsr v012a_store
    // Colour RAM attribute for GOTOX and NCM glyph.
    lda VIC_D030
    ora #1
    sta VIC_D030
    ldx v014_row
    jsr v012a_set_color_pointer
    ldy v014_offset
    lda #$90
    jsr v012a_store
    iny
s3b3_palette_operand:
    lda #0
    jsr v012a_store
    iny
    lda #$08
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    lda VIC_D030
    and #$fe
    sta VIC_D030
    ldx v014_row
    rts
// Write end-of-row GOTOX at first free slot, with valid Colour RAM.
// The reserved marker slot is always within the 80-byte screen row.
v014_write_terminator:
    ldx v014_row
    lda v014_row_count,x
    asl
    asl
    tay
    jsr v012a_set_row_pointer
    lda #$80              // H640 GOTOX X=640
    jsr v012a_store
    iny
    lda #2
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    iny
    lda #2                // blank glyph
    jsr v012a_store
    lda VIC_D030
    ora #1
    sta VIC_D030
    ldx v014_row
    jsr v012a_set_color_pointer
    ldy v014_row
    lda v014_row_count,y
    asl
    asl
    tay
    lda #$10              // confirmed end marker attribute
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    iny
    lda #8
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    lda VIC_D030
    and #$fe
    sta VIC_D030
    rts

s2i_index: .byte 0
s2i_phase: .fill 22, (i*11)&255
s2i_speed: .fill 22, 1+mod(i,3)
s2i_x: .fill 22,0
s2i_y: .fill 22,0
v014_overflow_count: .byte 0
v014_row: .byte 0
v014_offset: .byte 0
v014_x: .byte 0
v014_y: .byte 0
v014_ybits: .byte 0
v014_glyph_lo: .byte 0
v014_glyph_hi: .byte 0
v014_top_lo: .byte 0
v014_top_hi: .byte 0
v014_bot_lo: .byte 0
v014_bot_hi: .byte 0
v014_guard_lo: .byte 0
v014_guard_hi: .byte 0
v014_row_count: .fill 25,0

*=$c000
.fill 64,$00
// Glyph $301/$302 at $C040/$C080, 16x16 asymmetric control pattern
.byte $11,$11,$11,$11,$11,$11,$11,$11
.byte $12,$44,$44,$44,$66,$66,$66,$31
.byte $14,$24,$44,$44,$66,$66,$63,$61
.byte $14,$42,$44,$44,$66,$66,$36,$61
.byte $14,$44,$24,$44,$66,$63,$66,$61
.byte $14,$44,$42,$44,$66,$36,$66,$61
.byte $14,$44,$44,$24,$63,$66,$66,$61
.byte $14,$44,$44,$42,$36,$66,$66,$61
.byte $14,$44,$44,$43,$26,$66,$66,$61
.byte $14,$44,$44,$34,$62,$66,$66,$61
.byte $14,$44,$43,$44,$66,$26,$66,$61
.byte $14,$44,$34,$44,$66,$62,$66,$61
.byte $14,$43,$44,$44,$66,$66,$26,$61
.byte $14,$34,$44,$44,$66,$66,$62,$61
.byte $13,$44,$44,$44,$66,$66,$66,$21
.byte $11,$11,$11,$11,$11,$11,$11,$11


// V0.13d isolated guarded animation area. Not used by static pixies.
*=$c800
.fill 64,0 // $320 blank guard
.fill 64,0 // $321 upper glyph (copied dynamically)
.fill 64,0 // $322 lower glyph (copied dynamically)
.fill 64,0 // $323 blank guard

*=$c900
.fill 64,0 // orbit preceding guard $324
.fill 64,0 // orbit upper glyph $325
.fill 64,0 // orbit lower glyph $326
.fill 64,0 // orbit following guard $327

*=OBJ_INITIAL
v014_initial_records:
    .byte 1,1
    .word 40,12,40,12,65535,0
    .byte 0,0,1,0
    .word 0,0
    .byte 0,0
    .byte 1,2
    .word 200,12,200,12,65535,0
    .byte 0,0,1,0
    .word 0,0
    .byte 1,0
    .byte 1,3
    .word 40,172,40,172,65535,0
    .byte 0,0,1,0
    .word 0,0
    .byte 2,0
    .byte 1,4
    .word 200,172,200,172,65535,0
    .byte 0,0,1,0
    .word 0,0
    .byte 3,0
    .byte 4,1
    .word 64,80,64,80,65535,0
    .byte 0,0,1,0
    .word 0,0
    .byte 4,0
    .byte 2,2
    .word 170,92,170,92,0,0
    .byte 0,0,1,0
    .word 0,0
    .byte 5,0
    .fill (32-6)*24,0
v014_orbit_x:
    .byte 170,170,170,170,170,170,169,169,169,169,169,168,168,167,167,167,166,166,165,165,164,164,163,162,162,161,160,159,159,158,157,156,155,154,154,153,152,151,150,149,148,147,146,145,144,142,141,140,139,138,137,136,135,133,132,131,130,129,127,126,125,124,122,121,120,119,118,116,115,114,113,111,110,109,108,107,105,104,103,102,101,100,99,98,96,95,94,93,92,91,90,89,88,87,86,86,85,84,83,82,81,81,80,79,78,78,77,76,76,75,75,74,74,73,73,73,72,72,71,71,71,71,71,70,70,70,70,70,70,70,70,70,70,70,71,71,71,71,71,72,72,73,73,73,74,74,75,75,76,76,77,78,78,79,80,81,81,82,83,84,85,86,86,87,88,89,90,91,92,93,94,95,96,98,99,100,101,102,103,104,105,107,108,109,110,111,113,114,115,116,118,119,120,121,122,124,125,126,127,129,130,131,132,133,135,136,137,138,139,140,141,142,144,145,146,147,148,149,150,151,152,153,154,154,155,156,157,158,159,159,160,161,162,162,163,164,164,165,165,166,166,167,167,167,168,168,169,169,169,169,169,170,170,170,170,170
v014_orbit_y:
    .byte 92,93,94,96,97,98,99,101,102,103,104,105,107,108,109,110,111,112,113,114,116,117,118,119,120,121,122,123,124,125,126,126,127,128,129,130,131,131,132,133,134,134,135,136,136,137,137,138,138,139,139,139,140,140,141,141,141,141,141,142,142,142,142,142,142,142,142,142,142,142,141,141,141,141,141,140,140,139,139,139,138,138,137,137,136,136,135,134,134,133,132,131,131,130,129,128,127,126,126,125,124,123,122,121,120,119,118,117,116,114,113,112,111,110,109,108,107,105,104,103,102,101,99,98,97,96,94,93,92,91,90,88,87,86,85,83,82,81,80,79,77,76,75,74,73,72,71,70,68,67,66,65,64,63,62,61,60,59,58,58,57,56,55,54,53,53,52,51,50,50,49,48,48,47,47,46,46,45,45,45,44,44,43,43,43,43,43,42,42,42,42,42,42,42,42,42,42,42,43,43,43,43,43,44,44,45,45,45,46,46,47,47,48,48,49,50,50,51,52,53,53,54,55,56,57,58,58,59,60,61,62,63,64,65,66,67,68,70,71,72,73,74,75,76,77,79,80,81,82,83,85,86,87,88,90,91


// Stage 3b-1 loader: runs only before the engine saves VIC/Color RAM state.
// $6000/$6100 and $7000 from Stage 3a-2 overlap engine templates/tables.
// Engine origins and movement tables are retained; graphics wrappers/references are patched.
*=$4800 "Stage 3b-2 preload"
.namespace s3b {
.const SETBNK=$ff6b
.const BUF=$6800
.const CHECK=$6900
.const LEVELCOPY=$7600
entry:
    // KERNAL SEQ I/O runs in the normal BASIC video/IRQ context.
    php
    cli
    ldx #<title
    ldy #>title
    jsr puts
    lda #0
    sta error
    sta total_crc
    sta total_crc+1
    lda #<level_name
    sta name_ptr
    lda #>level_name
    sta name_ptr+1
    lda #12
    sta name_len
    lda #$81
    sta remain
    lda #$3f
    sta remain+1
    lda #$01
    sta remain+2
    // $20000-$3FFFF holds the (write-protected) ROM on the MEGA65.
    // Free chip RAM is $40000-$5FFFF: VYLV -> $40000..$53F80
    lda #$04
    sta target_bank
    lda #0
    sta target_hi
    jsr load_file
    lda error
    beq first_success
    jmp failed
first_success:
    lda total_crc
    cmp #$a2
    bne checksum_bad
    lda total_crc+1
    cmp #$5c
    beq level_sum_ok
checksum_bad:
    lda #6
    sta error
    jmp failed
level_sum_ok:
    lda #0
    sta total_crc
    sta total_crc+1
    lda #<graphic_name
    sta name_ptr
    lda #>graphic_name
    sta name_ptr+1
    lda #12
    sta name_len
    lda #$a8
    sta remain
    lda #$78
    sta remain+1
    lda #0
    sta remain+2
    // VYGR -> $54000..$5B8A7 (directly after VYLV, still free chip RAM)
    lda #$05
    sta target_bank
    lda #$40
    sta target_hi
    jsr load_file
    lda error
    beq second_success
    jmp failed
second_success:
    lda total_crc
    cmp #$e9
    bne graphic_sum_bad
    lda total_crc+1
    cmp #$1f
    beq graphic_sum_ok
graphic_sum_bad:
    lda #6
    sta error
    jmp failed
graphic_sum_ok:
    // Level 1 directory entry: offset $00000328, length $0351 (849 bytes).
    // Copy the complete Level 1 record into low RAM $7600.
    lda #$28
    sta dma_src_lo
    lda #$03
    sta dma_src_hi
    lda #$04            // VYLV now starts at $40000
    sta dma_src_bank
    lda #<LEVELCOPY
    sta dma_dst_lo
    lda #>LEVELCOPY
    sta dma_dst_hi
    lda #0
    sta dma_dst_bank
    lda #$51
    sta dma_len_lo  // $0351 = 849 bytes
    lda #$03
    sta dma_len_hi
    jsr dma_copy
    ldx #0
check_magic:
    lda LEVELCOPY,x
    cmp level_one_signature,x
    bne magic_bad
    inx
    cpx #8
    bne check_magic
    jsr s3b2.prepare
    lda error
    beq preparation_ok
    jmp failed
preparation_ok:
    ldx #<success_msg
    ldy #>success_msg
    jsr puts
    // Keep the message visible for 60 raster frames, before RRB starts.
    lda #60
    sta message_frames
message_frame:
    lda $d012
    cmp #250
    bne message_frame
message_frame_end:
    lda $d012
    cmp #250
    beq message_frame_end
    dec message_frames
    bne message_frame
    plp
    jmp start             // unchanged Stage-2ja entry at $2100
magic_bad:
    lda #5
    sta error
failed:
    ldx #<error_msg
    ldy #>error_msg
    jsr puts
    lda error
    jsr hex
    lda #13
    jsr $ffd2
    ldx #<status_msg
    ldy #>status_msg
    jsr puts
    lda io_status
    jsr hex
    lda #13
    jsr $ffd2
    // Failure: input channel has been closed; RRB never initialized.
    plp
    rts

load_file:
    lda #0
    sta chunk_size
    sta io_status
    lda #2
    ldx #8
    ldy #2
    jsr $ffba           // SETLFS
    lda #0
    ldx #0
    jsr SETBNK         // critical: filename in bank zero
    lda name_len
    ldx name_ptr
    ldy name_ptr+1
    jsr $ffbd           // SETNAM
    jsr $ffc0           // OPEN
    bcc opened
    lda #1
    sta error
    jmp close_input
opened:
    ldx #2
    jsr $ffc6           // CHKIN
    bcc channel_ready
    lda #2
    sta error
    jmp close_input
channel_ready:
read_byte:
    jsr $ffcf           // CHRIN, do not print while channel active
    ldx chunk_size
    sta BUF,x
    jsr $ffb7           // READST
    sta io_status
    and #$bf            // every READST error is fatal; EOF is handled below
    beq no_timeout
    lda #3
    sta error
    jmp close_input
no_timeout:
    // count down 24-bit expected bytes
    lda remain
    bne dec_low
    lda remain+1
    bne dec_middle
    dec remain+2
 dec_middle:
    dec remain+1
 dec_low:
    dec remain
    inc chunk_size
    // $40 EOF before all expected bytes is an error.
    lda remain
    ora remain+1
    ora remain+2
    beq last_byte
    lda io_status
    and #$40
    beq check_chunk
    lda #3
    sta error
    jmp close_input
last_byte:
    // process last (possibly partial) chunk
    jsr flush_chunk
    jmp close_input
check_chunk:
    lda chunk_size
    bne read_byte
    // chunk_size wrapped 256 -> flush a full page
    jsr flush_chunk
    lda error
    bne close_input
    jmp read_byte
close_input:
    jsr $ffcc
    lda #2
    jsr $ffc3
    rts

// chunk_size=0 means 256, otherwise 1..255.
// DMA BUF -> high RAM, DMA high RAM -> CHECK, compare all bytes.
flush_chunk:
    lda #<BUF
    sta dma_src_lo
    lda #>BUF
    sta dma_src_hi
    lda #0
    sta dma_src_bank
    sta dma_dst_lo
    lda target_hi
    sta dma_dst_hi
    lda target_bank
    sta dma_dst_bank
    lda chunk_size
    sta dma_len_lo
    lda #0
    sta dma_len_hi
    lda chunk_size
    bne partial_len
    inc dma_len_hi
partial_len:
    jsr dma_copy
    // swap source and destination to read back into CHECK
    lda #<CHECK
    sta dma_dst_lo
    lda #>CHECK
    sta dma_dst_hi
    lda #0
    sta dma_dst_bank
    lda target_hi
    sta dma_src_hi
    lda target_bank
    sta dma_src_bank
    lda #0
    sta dma_src_lo
    jsr dma_copy
    ldx #0
verify_loop:
    lda BUF,x
    cmp CHECK,x
    bne verify_fail
    clc
    adc total_crc
    sta total_crc
    bcc no_carry
    inc total_crc+1
no_carry:
    inx
    cpx chunk_size
    bne verify_loop
    // one DMA chunk occupies one full high-RAM page, including final partial.
    inc target_hi
    bne flush_done
    inc target_bank
flush_done:
    rts
verify_fail:
    lda #4
    sta error
    rts

// F018A enhanced DMA list in CPU bank zero, source and target banks 64K.
// The $0a option explicitly selects F018A (11-byte descriptor).
dma_copy:
    lda #0
    sta $d702
    sta $d704
    lda #>dma_list
    sta $d701
    lda #<dma_list
    sta $d705
    rts

dma_list:
    .byte $0a,$00
    .byte $00          // copy
 dma_len_lo: .byte 0
 dma_len_hi: .byte 1
 dma_src_lo: .byte 0
 dma_src_hi: .byte 0
 dma_src_bank: .byte 0
 dma_dst_lo: .byte 0
 dma_dst_hi: .byte 0
 dma_dst_bank: .byte 2
    .word 0           // modulo

puts:
    stx p+1
    sty p+2
    ldx #0
p:  lda $ffff,x
    beq puts_end
    jsr $ffd2
    inx
    bne p
puts_end:
    rts
hex:
    pha
    lsr
    lsr
    lsr
    lsr
    jsr nibble
    pla
    and #15
nibble:
    cmp #10
    bcc num
    adc #6
num:
    adc #$30
    jmp $ffd2

level_name: .text "VYLV.DAT,S,R"
graphic_name: .text "VYGR.DAT,S,R"
level_one_signature: .byte 1,0,2,22,16,0,2,0
title: .text "STAGE 3B-2: LOADING ORIGINAL DATA"
.byte 13,0
success_msg: .text "VYLV + VYGR LOADED AND VERIFIED"
.byte 13,0
error_msg: .text "STAGE 3B-2 LOAD ERROR $"
.byte 0
status_msg: .text "READST $"
.byte 0
message_frames: .byte 0
name_ptr: .word 0
name_len: .byte 0
remain: .byte 0,0,0
target_hi: .byte 0
target_bank: .byte 0
chunk_size: .byte 0
io_status: .byte 0
error: .byte 0
total_crc: .word 0

loader_end:
.if (loader_end > SCREEN_RAM) { .error "Stage3b1: loader overlaps RRB screen" }
.if (COLOR_TEMPLATE+2000 > BUF) { .error "Stage3b1: SEQ buffer overlaps color template" }
.if (CHECK+256 > OBJ_INITIAL) { .error "Stage3b1: DMA buffer overlaps object tables" }
.if (v014_orbit_y+256 > LEVELCOPY) { .error "Stage3b1: level copy overlaps orbit tables" }
.if (LEVELCOPY+$351 > NCM_DATA) { .error "Stage3b1: level copy overlaps NCM graphics" }
}

// Stage 3b-2: bounded Level-1 parser and loaded VYGR animation source.
*=$3200 "Stage 3b-2 graphics and parser"
.namespace s3b2 {
.const RECORD_END=$7951
.const DIRECTORY=$6a00
.const GRAPHICS=$9800
prepare:
    lda #<$7600
    sta pointer
    lda #>$7600
    sta pointer+1
    lda #0
    sta selected_type
    sta group_total
    sta group_total+1
    sta frame
    jsr read_word
    bcc branch_ok_1
    jmp invalid
branch_ok_1:
    lda word_value
    cmp #1
    beq branch_ok_2
    jmp invalid
branch_ok_2:
    lda word_value+1
    beq branch_ok_3
    jmp invalid
branch_ok_3:
    jsr get_byte
    sta groups_left
    jsr get_byte
    cmp #22                 // retain the 22 existing path pixies
    beq branch_ok_4
    jmp invalid
branch_ok_4:
    sta enemies_left
    jsr read_word           // interval: movements remain unchanged
    bcc branch_ok_5
    jmp invalid
branch_ok_5:
    jsr read_word
    bcc branch_ok_6
    jmp invalid
branch_ok_6:
    lda word_value
    sta attacks_left
    lda word_value+1
    sta attacks_left+1
    lda groups_left
    beq groups_done
next_group:
    jsr read_word           // group enemy count
    bcc branch_ok_7
    jmp invalid
branch_ok_7:
    clc
    lda group_total
    adc word_value
    sta group_total
    lda group_total+1
    adc word_value+1
    sta group_total+1
    bcc branch_ok_8
    jmp invalid
branch_ok_8:
    jsr read_word           // start X: not used for motion
    bcc branch_ok_9
    jmp invalid
branch_ok_9:
    jsr read_word           // start Y
    bcc branch_ok_10
    jmp invalid
branch_ok_10:
    jsr read_word           // variable curve length
    bcc branch_ok_11
    jmp invalid
branch_ok_11:
    jsr skip_curve
    bcc branch_ok_12
    jmp invalid
branch_ok_12:
    dec groups_left
    bne next_group
groups_done:
    lda group_total
    cmp #22
    beq branch_ok_13
    jmp invalid
branch_ok_13:
    lda group_total+1
    beq branch_ok_14
    jmp invalid
branch_ok_14:
    // Enemy location is the cursor after all variable-length entry curves.
    lda pointer
    sta enemy_start
    lda pointer+1
    sta enemy_start+1
next_enemy:
    jsr read_word           // formation X: deliberately unused
    bcc branch_ok_15
    jmp invalid
branch_ok_15:
    jsr read_word           // formation Y
    bcc branch_ok_16
    jmp invalid
branch_ok_16:
    jsr get_byte            // graphic_type
    bcc branch_ok_17
    jmp invalid
branch_ok_17:
    cmp #38
    bcc branch_ok_18
    jmp invalid
branch_ok_18:
    jsr shots.p_map_type
    .fill 13,$ea
mapped:
    ldx selected_type
    beq first_type
    cmp selected_type
    beq branch_ok_19
    jmp invalid
branch_ok_19:
first_type:
    sta selected_type
    jsr get_byte            // attack_index: retain existing movement logic
    bcc branch_ok_20
    jmp invalid
branch_ok_20:
    dec enemies_left
    bne next_enemy
next_attack:
    lda attacks_left
    ora attacks_left+1
    beq attacks_done
    jsr read_word
    bcc branch_ok_21
    jmp invalid
branch_ok_21:
    jsr skip_curve
    bcc branch_ok_22
    jmp invalid
branch_ok_22:
    lda attacks_left
    bne attack_dec_low
    dec attacks_left+1
attack_dec_low:
    dec attacks_left
    jmp next_attack
attacks_done:
    lda pointer
    cmp #<RECORD_END
    beq branch_ok_23
    jmp invalid
branch_ok_23:
    lda pointer+1
    cmp #>RECORD_END
    beq branch_ok_24
    jmp invalid
branch_ok_24:
    jmp select_graphics
invalid:
    lda #7
    sta s3b.error
    sec
    rts

get_byte:
    lda pointer+1
    cmp #>RECORD_END
    bcc read_allowed
    beq branch_ok_25
    jmp truncated
branch_ok_25:
    lda pointer
    cmp #<RECORD_END
    bcc branch_ok_26
    jmp truncated
branch_ok_26:
read_allowed:
    lda pointer
    sta read_instruction+1
    lda pointer+1
    sta read_instruction+2
read_instruction:
    lda $7600
    inc pointer
    bne byte_done
    inc pointer+1
byte_done:
    clc
    rts
truncated:
    lda #7
    sta s3b.error
    sec
    rts
read_word:
    jsr get_byte
    bcs word_done
    sta word_value
    jsr get_byte
    bcs word_done
    sta word_value+1
word_done:
    rts
skip_curve:
    clc
    lda pointer
    adc word_value
    sta new_pointer
    lda pointer+1
    adc word_value+1
    sta new_pointer+1
    bcc branch_ok_27
    jmp truncated
branch_ok_27:
    cmp #>RECORD_END
    bcc skip_allowed
    beq branch_ok_28
    jmp truncated
branch_ok_28:
    lda new_pointer
    cmp #<RECORD_END
    bcc skip_allowed
    beq branch_ok_29
    jmp truncated
branch_ok_29:
skip_allowed:
    lda new_pointer
    sta pointer
    lda new_pointer+1
    sta pointer+1
    clc
    rts

select_graphics:
    // Type N is entry N-1: file offset 8 + (N-1)*8 = N*8.
    lda selected_type
    sta word_value
    lda #0
    sta word_value+1
    .for (var i=0; i<3; i++) {
        asl word_value
        rol word_value+1
    }
    lda word_value
    sta s3b.dma_src_lo
    lda word_value+1
    clc
    adc #$40
    sta s3b.dma_src_hi
    lda #5
    sta s3b.dma_src_bank
    lda #<DIRECTORY
    sta s3b.dma_dst_lo
    lda #>DIRECTORY
    sta s3b.dma_dst_hi
    lda #0
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    lda #8
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    lda DIRECTORY+2
    ora DIRECTORY+3
    ora DIRECTORY+5
    ora DIRECTORY+6
    ora DIRECTORY+7
    beq branch_ok_30
    jmp graphics_invalid
branch_ok_30:
    lda DIRECTORY+4
    bne branch_ok_31
    jmp graphics_invalid
branch_ok_31:
    cmp #13                // original archive: maximum 12 frames per type
    bcc branch_ok_32
    jmp graphics_invalid
branch_ok_32:
    sta frame_count
    lda DIRECTORY+1
    cmp #1
    bcs branch_ok_33
    jmp graphics_invalid
branch_ok_33:
    bne offset_valid
    lda DIRECTORY
    cmp #$28
    bcs branch_ok_34
    jmp graphics_invalid
branch_ok_34:
offset_valid:
    clc
    lda DIRECTORY
    sta source_base
    lda DIRECTORY+1
    adc #$40
    sta source_base+1
    bcc branch_ok_35
    jmp graphics_invalid
branch_ok_35:
    // Check the complete type range against the loaded VYGR end ($5B8A8).
    lda frame_count
    sta word_value
    lda #0
    sta word_value+1
    .for (var i=0; i<7; i++) {
        asl word_value
        rol word_value+1
    }
    clc
    lda source_base
    adc word_value
    sta new_pointer
    lda source_base+1
    adc word_value+1
    bcc branch_ok_36
    jmp graphics_invalid
branch_ok_36:
    cmp #$b8
    bcc graphics_valid
    beq branch_ok_37
    jmp graphics_invalid
branch_ok_37:
    lda new_pointer
    cmp #$a9
    bcc branch_ok_38
    jmp graphics_invalid
branch_ok_38:
graphics_valid:
    clc
    rts
graphics_invalid:
    lda #8
    sta s3b.error
    sec
    rts

init_objects:
    jsr v014_init_objects
    php
    sei
    jsr draw_frame
    plp
    jmp check_runtime_error
animate:
    jsr s2ja_animate_pixies  // unchanged seven-frame joystick/orbit animation
    php
    sei
    inc frame
    lda frame
    cmp frame_count
    bcc frame_ready
    lda #0
    sta frame
frame_ready:
    jsr draw_frame
    plp
check_runtime_error:
    lda s3b.error
    beq runtime_ok
    // Discard this wrapper's JSR return, then use the original BASIC exit.
    // No CHROUT in RRB mode; error code remains available for inspection.
    pla
    pla
    jmp exit_to_basic
runtime_ok:
    rts

draw_frame:
    lda frame
    sta word_value
    lda #0
    sta word_value+1
    .for (var i=0; i<7; i++) {
        asl word_value
        rol word_value+1
    }
    clc
    lda source_base
    adc word_value
    sta frame_source
    lda source_base+1
    adc word_value+1
    sta frame_source+1
    jsr set_frame_source
    lda #<(GRAPHICS+64)
    sta s3b.dma_dst_lo
    lda #>(GRAPHICS+64)
    sta s3b.dma_dst_hi
    lda #0
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    lda #128
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    // Read target back and separately fetch original high-RAM frame for comparison.
    lda #<(GRAPHICS+64)
    sta s3b.dma_src_lo
    lda #>(GRAPHICS+64)
    sta s3b.dma_src_hi
    lda #0
    sta s3b.dma_src_bank
    lda #<$6900
    sta s3b.dma_dst_lo
    lda #>$6900
    sta s3b.dma_dst_hi
    jsr s3b.dma_copy
    jsr set_frame_source
    lda #<$6800
    sta s3b.dma_dst_lo
    lda #>$6800
    sta s3b.dma_dst_hi
    jsr s3b.dma_copy
    ldx #0
compare_frame:
    lda $6800,x
    cmp $6900,x
    bne frame_bad
    inx
    cpx #128
    bne compare_frame
    rts
frame_bad:
    lda #4
    sta s3b.error
    rts
set_frame_source:
    lda frame_source
    sta s3b.dma_src_lo
    lda frame_source+1
    sta s3b.dma_src_hi
    lda #5
    sta s3b.dma_src_bank
    rts

pointer: .word 0
new_pointer: .word 0
word_value: .word 0
enemy_start: .word 0
source_base: .word 0
frame_source: .word 0
group_total: .word 0
groups_left: .byte 0
enemies_left: .byte 0
attacks_left: .word 0
selected_type: .byte 0
frame: .byte 0
frame_count: .byte 0
code_end:
.if (code_end > $4000) { .error "Stage3b2 code overlaps mono graphics" }
.if (DIRECTORY+8 > OBJ_INITIAL) { .error "Stage3b2 directory overlaps object tables" }
.if (GRAPHICS < BASIC_COLOR_BACKUP+$800) { .error "Stage3b2 graphics overlap BASIC backup" }
.if (GRAPHICS+$100 > $a000) { .error "Stage3b2 graphics overlap original animation assets" }
}
*=$9800 "Stage 3b-2 loaded path-pixie glyphs"
.fill 256,0             // $260 guard, $261 top, $262 bottom, $263 guard


// Stage 3b-3 immutable source data in the free gap following Stage-3b-2 code.
*=$3600 "Stage 3b-3 approved player source"
.namespace s3b3 {
player_pixels:
    .import binary "player_assets/player_ncm.bin"
player_red:
    .import binary "player_assets/player_palette_r.bin"
player_green:
    .import binary "player_assets/player_palette_g.bin"
player_blue:
    .import binary "player_assets/player_palette_b.bin"
player_source_end:
.if (player_source_end > $3700) { .error "Player source overlaps player code" }
}

*=$3700 "Stage 3b-3 player integration"
.namespace s3b3 {
player_palette_init:
    jsr init_palette  // unchanged enemy bank 1; replace unused hardware-sprite bank 2
    // Bank 3 entries 0..15 also back the C65 ROM palette: never overwrite them.
    // MAPEDPAL=2, BTPALSEL=1, SPRPALSEL=2, ABTPALSEL=2.
    lda #$9a
    sta VIC_PALSEL
    ldx #0
player_palette_loop:
    lda player_red,x
    sta $d100,x
    lda player_green,x
    sta $d200,x
    lda player_blue,x
    sta $d300,x
    inx
    cpx #16
    bne player_palette_loop
    rts

player_init:
    jsr s3b2.init_objects  // unchanged records and original enemy frame DMA
    ldx #0
player_copy:
    lda player_pixels,x
    sta $c840,x
    lda player_pixels+64,x
    sta $c880,x
    lda #0
    sta $c800,x
    sta $c8c0,x
    inx
    cpx #64
    bne player_copy
    rts

player_write_slot:
    // The joystick player is the only user of $321/$322/$323.
    // Every GOTOX explicitly selects a palette, so subsequent enemy slots reset it.
    lda v014_glyph_hi
    cmp #3
    bne enemy_palette
    lda v014_glyph_lo
    cmp #$21
    bcc enemy_palette
    cmp #$24
    bcs enemy_palette
    // Colour byte 1 BOLD ($40) + REVERSE ($20), with ATTR off,
    // selects ABTPALSEL for following NCM glyphs in this RRB fragment.
    lda #$60
    bne write_palette
 enemy_palette:
    lda #0
 write_palette:
    sta s3b3_palette_operand+1
    jmp v014_write_slot
player_code_end:
.if (player_code_end > $4000) { .error "Player code overlaps mono glyph region" }
.if (s3b2.code_end > $3600) { .error "Player source overlaps original parser" }
}

.import source "stage4b_hud.asm"

.import source "stage4b_shots.asm"

.import source "stage4b_game.asm"

.import source "stage4b_offscreen.asm"
