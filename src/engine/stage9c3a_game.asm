// Issue #8. Per-object states and logical coordinates, never VIC collision bits.
.namespace game {
.const c_DEAD=0
.const c_FORMATION=1
.const c_ENTRY=2
.const c_ATTACK=3
.const c_EXP=4
.const c_ACTIVE=0
.const c_PLAYER_EXP=1
.const c_WAIT=2
.const c_BLINK=3
.const c_OVER=4
.const c_ENEMIES=23
.const c_EXP_TICKS=3
// Source record 7 ($3827A) is the player ship, NOT an explosion.
// User confirms exactly seven explosion frames: source records 0..6.
.const c_EXP_FRAMES=7
.const c_BLINK_TICKS=150
.const c_BLINK_PERIOD=25
.const c_INSET=2
.const c_SHIP_SIZE=16-2*c_INSET
.const c_PLAYER_SHOT_WIDTH=1
.const c_ENEMY_SHOT_WIDTH=3
.const c_SHOT_HEIGHT=4
.const c_RAM=$1c00
.label c_es=c_RAM
.label c_ef=c_RAM+23
.label c_et=c_RAM+46
.label c_ex=c_RAM+69
.label c_ey=c_RAM+92
.label c_ps=c_RAM+115
.label c_pf=c_RAM+116
.label c_pt=c_RAM+117
.label c_px=c_RAM+118
.label c_py=c_RAM+119
.label c_blink=c_RAM+120
.label c_flash=c_RAM+121
.label c_visible=c_RAM+122
.label c_mode=c_RAM+123
.label c_armed=c_RAM+124
.label c_index=c_RAM+125
.label c_slot=c_RAM+126
.label c_ax=c_RAM+127
.label c_ay=c_RAM+128
.label c_ar=c_RAM+129
.label c_ab=c_RAM+130
.label c_bx=c_RAM+131
.label c_by=c_RAM+132
.label c_br=c_RAM+133
.label c_bb=c_RAM+134
.label c_oldstate=c_RAM+135
.label c_add=c_RAM+136 // 32-bit award
.label c_level=c_RAM+140 // formula scratch word
.label c_points=c_RAM+142 // formation 32 bits, attack 32 bits
.label c_lastlevel=c_RAM+150
.label c_ui_row=c_RAM+152
.label c_ui_length=c_RAM+153
.label c_ui_offset=c_RAM+154
.label c_keyvalue=c_RAM+155
.label c_restarted=c_RAM+156

*=$4c40 "Stage 3b-5c states and restart"
c_init:
    jsr shots.p_engine_init
    jmp c_reset
c_reset:
    ldx #0
    lda #0
c_reset_clear:
    sta c_RAM,x
    dex
    bne c_reset_clear
    lda #c_ATTACK
    sta c_mode
    lda #1
    sta c_visible
    ldx #22
c_reset_enemies:
    sta c_es,x
    dex
    bpl c_reset_enemies
    ldx #21
c_reset_paths:
    lda c_phases,x
    sta s2i_phase,x
    tay
    lda v014_orbit_x,y
    sta s2i_x,x
    lda v014_orbit_y,y
    sta s2i_y,x
    dex
    bpl c_reset_paths
    lda #0
    sta anim_paused
    sta anim_tick
    sta anim_frame
    sta s2ja_frame
    sta s3b2.frame
    lda #6
    sta anim_speed
    jsr c_font
    jsr entry.e_init
    jsr level.clear_private
    jsr audio8.reset
    jmp c_formula
c_move:
    lda c_ps
    beq c_move_allowed
    cmp #c_BLINK
    bne c_move_blocked
c_move_allowed:
    jmp v014_move_record
c_move_blocked:
    lda VIC_D030
    and #$fe
    sta VIC_D030
    lda $dc00
    sta v014_joy_sample
    rts
c_key:
    jsr KERNAL_GETIN
    cmp #$61
    bcc c_key_high
    cmp #$7b
    bcs c_key_high
    and #$df
c_key_high:
    cmp #$c1
    bcc c_key_case
    cmp #$db
    bcs c_key_case
    and #$7f
c_key_case:
    sta c_keyvalue
    cmp #$58
    beq c_key_return
    lda c_ps
    cmp #c_OVER
    bne c_key_normal
    lda c_keyvalue
    beq c_key_release
    cmp #$52
    bne c_key_ignore
    lda c_armed
    beq c_key_ignore
    jsr c_restart
    jmp c_key_ignore
c_key_release:
    // Direct keyboard matrix row 2, bit 1 = R (active low).
    // Preserve the query selector, do not disturb CIA joystick ports.
    lda $d614
    pha
    lda #2
    sta $d614
    lda $d613
    and #2
    tax
    pla
    sta $d614
    txa
    beq c_key_ignore
    lda #1
    sta c_armed
    jmp c_key_ignore
c_key_normal:
    lda c_keyvalue
    cmp #$54
    bne c_key_entry
    lda shots.p_test_enabled
    eor #1
    sta shots.p_test_enabled
    jmp c_key_ignore
c_key_entry:
    cmp #$45
    bne c_key_return
    lda c_mode
    eor #1 // 2 ENTRY <-> 3 ATTACK, isolated testing only
    sta c_mode
c_key_ignore:
    lda #0
    rts
c_key_return:
    lda c_keyvalue
    rts
c_restart:
    jmp level.restart
c_timers:
    ldx #0
c_timer_enemy:
    lda c_es,x
    cmp #c_EXP
    bne c_timer_next
    inc c_et,x
    lda c_et,x
    cmp #c_EXP_TICKS
    bcc c_timer_next
    lda #0
    sta c_et,x
    inc c_ef,x
    lda c_ef,x
    cmp #c_EXP_FRAMES
    bcc c_timer_next
    lda #c_DEAD
    sta c_es,x
c_timer_next:
    inx
    cpx #c_ENEMIES
    bne c_timer_enemy
    lda c_ps
    cmp #c_PLAYER_EXP
    bne c_timer_blink
    inc c_pt
    lda c_pt
    cmp #c_EXP_TICKS
    bcc c_timer_done
    lda #0
    sta c_pt
    inc c_pf
    lda c_pf
    cmp #c_EXP_FRAMES
    bcc c_timer_done
    lda hud.player1_lives
    ora hud.player1_lives+1
    beq c_timer_over
    lda #c_WAIT
    sta c_ps
    rts
c_timer_over:
    lda #c_OVER
    sta c_ps
    lda #1
    sta anim_paused
    lda #0
    sta c_armed
    ldx #7
c_over_shots:
    sta shots.p_active,x
    dex
    bpl c_over_shots
    rts
c_timer_blink:
    cmp #c_BLINK
    bne c_timer_done
    dec c_blink
    beq c_blink_end
    dec c_flash
    bne c_timer_done
    lda #c_BLINK_PERIOD
    sta c_flash
    lda c_visible
    eor #1
    sta c_visible
    rts
c_blink_end:
    lda #c_ACTIVE
    sta c_ps
    lda #1
    sta c_visible
c_timer_done:
    rts
c_wait:
    lda c_ps
    cmp #c_WAIT
    bne c_wait_done
    ldx #22
c_wait_scan:
    lda c_es,x
    beq c_wait_next
    cmp #c_FORMATION
    bne c_wait_done
c_wait_next:
    dex
    bpl c_wait_scan
    lda c_px
    sta V014_PLAYER+2
    lda c_py
    sta V014_PLAYER+4
    lda #c_BLINK
    sta c_ps
    lda #c_BLINK_TICKS
    sta c_blink
    lda #c_BLINK_PERIOD
    sta c_flash
    lda #1
    sta c_visible
c_wait_done:
    rts
c_states_end:
.if (c_states_end > $5000) { .error "States exceed $4fff" }

*=$8b00 "Stage 3b-5c software collisions"
c_enemy_xy:
    cpx #22
    beq c_enemy_orbit
    lda s2i_x,x
    sta c_bx
    lda s2i_y,x
    sta c_by
    rts
c_enemy_orbit:
    lda V014_ORBIT+2
    sta c_bx
    lda V014_ORBIT+4
    sta c_by
    rts
c_ship_box:
    lda c_bx
    clc
    adc #c_INSET
    sta c_bx
    adc #c_SHIP_SIZE
    sta c_br
    lda c_by
    clc
    adc #c_INSET
    sta c_by
    adc #c_SHIP_SIZE
    sta c_bb
    rts
c_overlap:
    lda c_ax
    cmp c_br
    bcs c_miss
    lda c_bx
    cmp c_ar
    bcs c_miss
    lda c_ay
    cmp c_bb
    bcs c_miss
    lda c_by
    cmp c_ab
    bcs c_miss
    sec
    rts
c_miss:
    clc
    rts
c_shot_box:
    // Slot position denotes centre X, top Y, in logical pixels.
    lda shots.p_xpos,x
    cpx #2
    bcc c_shot_player
    sec
    sbc #1
c_shot_player:
    sta c_ax
    clc
    adc #c_PLAYER_SHOT_WIDTH
    cpx #2
    bcc c_shot_right
    clc
    adc #c_ENEMY_SHOT_WIDTH-c_PLAYER_SHOT_WIDTH
c_shot_right:
    sta c_ar
    lda shots.p_ypos,x
    sta c_ay
    clc
    adc #c_SHOT_HEIGHT
    sta c_ab
    rts
c_player_box:
    lda V014_PLAYER+2
    sta c_bx
    lda V014_PLAYER+4
    sta c_by
    jmp c_ship_box
c_collisions:
    lda #0
    sta c_slot
c_coll_player_shots:
    ldx c_slot
    lda shots.p_active,x
    beq c_coll_next_shot
    jsr c_shot_box
    ldx #0
c_coll_enemy_scan:
    stx c_index
    lda c_es,x
    beq c_coll_next_enemy
    cmp #c_EXP
    beq c_coll_next_enemy
    jsr entry.e_collision_box
    jsr c_overlap
    bcc c_coll_next_enemy
    ldx c_slot
    jsr shots.p_deactivate
    ldx c_index
    lda c_es,x
    sta c_oldstate
    jsr c_enemy_hit
    jsr c_award
    jmp c_coll_next_shot
c_coll_next_enemy:
    ldx c_index
    inx
    cpx #c_ENEMIES
    bne c_coll_enemy_scan
c_coll_next_shot:
    inc c_slot
    lda c_slot
    cmp #2
    bne c_coll_player_shots
    lda c_ps
    beq c_coll_enemy_shots
    rts
c_coll_enemy_shots:
    lda #2
    sta c_slot
c_coll_enemy_shot_loop:
    ldx c_slot
    jsr motion.visible
    bcc c_coll_enemy_shot_next
    jsr c_shot_box
    jsr c_player_box
    jsr c_overlap
    bcc c_coll_enemy_shot_next
    ldx c_slot
    jsr shots.p_deactivate
    jmp c_player_hit
c_coll_enemy_shot_next:
    inc c_slot
    lda c_slot
    cmp #8
    bne c_coll_enemy_shot_loop
    // Direct ram only ENTRY/ATTACK; FORMATION and invulnerable player ignored.
    jsr c_player_box
    lda c_bx
    sta c_ax
    lda c_by
    sta c_ay
    lda c_br
    sta c_ar
    lda c_bb
    sta c_ab
    ldx #0
c_coll_ram:
    stx c_index
    lda c_es,x
    cmp #c_ENTRY
    beq c_coll_ram_check
    cmp #c_ATTACK
    bne c_coll_ram_next
c_coll_ram_check:
    jsr entry.e_collision_box
    jsr c_overlap
    bcc c_coll_ram_next
    ldx c_index
    jsr c_enemy_hit
    jmp c_player_hit
c_coll_ram_next:
    ldx c_index
    inx
    cpx #c_ENEMIES
    bne c_coll_ram
    rts
c_enemy_hit:
    jsr c_enemy_xy
    lda c_bx
    sta c_ex,x
    lda c_by
    sta c_ey,x
    lda #0
    sta c_ef,x
    sta c_et,x
    lda #c_EXP
    sta c_es,x
    jsr audio8.enemy_death
    rts
c_player_hit:
    lda c_ps
    bne c_player_hit_done
    lda V014_PLAYER+2
    sta c_px
    lda V014_PLAYER+4
    sta c_py
    lda #0
    sta c_pf
    sta c_pt
    lda #c_PLAYER_EXP
    sta c_ps
    jsr audio8.player_death
    lda hud.player1_lives
    ora hud.player1_lives+1
    beq c_player_hit_done
    lda hud.player1_lives
    bne c_life_low
    dec hud.player1_lives+1
c_life_low:
    dec hud.player1_lives
c_player_hit_done:
    rts
c_award:
    ldx #0
    lda c_oldstate
    cmp #c_FORMATION
    beq c_award_copy
    ldx #4
c_award_copy:
    ldy #0
c_award_loop:
    lda c_points,x
    sta c_add,y
    inx
    iny
    cpy #4
    bne c_award_loop
    clc
    ldx #0
    ldy #4
c_score_add:
    lda hud.player1_score,x
    adc c_add,x
    sta hud.player1_score,x
    inx
    dey
    bne c_score_add
    bcc c_score_compare
    lda #$ff // saturate 32-bit unsigned instead of wrapping
    ldx #3
c_score_saturate:
    sta hud.player1_score,x
    dex
    bpl c_score_saturate
c_score_compare:
    ldx #3
c_score_compare_byte:
    lda hud.player1_score,x
    cmp hud.high_score,x
    bcc c_score_done
    bne c_high_copy
    dex
    bpl c_score_compare_byte
c_high_copy:
    ldx #3
c_high_loop:
    lda hud.player1_score,x
    sta hud.high_score,x
    dex
    bpl c_high_loop
c_score_done:
    rts
c_formula:
    lda hud.player1_level
    cmp c_lastlevel
    bne c_formula_new
    lda hud.player1_level+1
    cmp c_lastlevel+1
    bne c_formula_new
    rts
c_formula_new:
    lda hud.player1_level
    sta c_lastlevel
    sta c_level
    lda hud.player1_level+1
    sta c_lastlevel+1
    sta c_level+1
    ora c_level
    bne c_formula_nonzero
    inc c_level // defensive level 0 uses level 1, no unsigned underflow
c_formula_nonzero:
    lda c_level
    bne c_formula_dec
    dec c_level+1
c_formula_dec:
    dec c_level
    ldx #7
    lda #0
c_formula_zero:
    sta c_points,x
    dex
    bpl c_formula_zero
    lda #100
    sta c_points
c_formula_k:
    lda c_level+1
    bne c_formula_step
    lda c_level
    cmp #10
    bcc c_formula_attack
c_formula_step:
    sec
    lda c_level
    sbc #10
    sta c_level
    lda c_level+1
    sbc #0
    sta c_level+1
    clc
    lda c_points
    adc #50
    sta c_points
    ldx #1
    ldy #3
c_formula_carry:
    lda c_points,x
    adc #0
    sta c_points,x
    inx
    dey
    bne c_formula_carry
    jmp c_formula_k
c_formula_attack:
    clc
    lda c_points
    adc #75
    sta c_points+4
    ldx #1
    ldy #3
c_formula_attack_carry:
    lda c_points,x
    adc #0
    sta c_points+4,x
    inx
    dey
    bne c_formula_attack_carry
    // HUD words display low three decimal digits. Full awards remain 32-bit.
    ldx #0
    jsr c_points_display
    lda c_level
    sta hud.formation_points
    lda c_level+1
    sta hud.formation_points+1
    ldx #4
    jsr c_points_display
    lda c_level
    sta hud.attack_points
    lda c_level+1
    sta hud.attack_points+1
    rts
c_points_display:
    lda c_points,x
    sta c_level
    lda c_points+1,x
    sta c_level+1
    // Awards <= 327825 for WORD levels. Reduce high words using 65536%1000.
    lda c_points+2,x
    sta c_add
c_points_high:
    lda c_add
    beq c_points_mod
    dec c_add
    clc
    lda c_level
    adc #<536
    sta c_level
    lda c_level+1
    adc #>536
    sta c_level+1
    bcc c_points_high
    inc c_add
    jmp c_points_high
c_points_mod:
    lda c_level+1
    cmp #>1000
    bcc c_points_return
    bne c_points_sub
    lda c_level
    cmp #<1000
    bcc c_points_return
c_points_sub:
    sec
    lda c_level
    sbc #<1000
    sta c_level
    lda c_level+1
    sbc #>1000
    sta c_level+1
    jmp c_points_mod
c_points_return:
    rts
c_collisions_end:
.if (c_collisions_end > $9000) { .error "Collisions exceed $8fff" }

*=$85b0 "Stage 3b-5c motion and frame coordinator"
c_objects:
    jmp attack.a_objects
c_tick:
    jsr entry.e_error_check
    lda c_ps
    cmp #c_OVER
    beq c_tick_done
    jsr c_timers
    lda c_ps
    cmp #c_OVER
    beq c_tick_over
    jmp level.continue_combat // same-size tail gate; keep packed coordinator layout
c_tick_attack_test:
    jsr entry.e_attack_test
c_tick_update:
    jsr c_wait
    jsr shots.p_update
    jsr c_fire_state
    bne c_tick_no_fire
    jsr shots.p_player_fire
    jmp c_tick_enemy_fire
c_tick_no_fire:
    // Require trigger release before another shot after revival.
    lda #1
    sta shots.p_fire_latch
c_tick_enemy_fire:
    jsr shots.p_random_step
    jsr attack.a_fire
    jsr c_collisions
    jsr shots.p_publish
    jmp hud.hud_render
c_tick_over:
    jsr shots.p_publish
    jsr hud.hud_render
    jmp c_game_over
c_tick_done:
    rts
c_motion_end:
.if (c_motion_end > $8800) { .error "Motion exceeds $87ff" }

*=$8840 "Stage 3b-5c initial path phases and extra thin letters"
c_phases: .fill 22,(i*11)&255
// Only new G/M glyphs of GAME OVER; existing HUD keeps its thin font.
c_letters: .byte $38,$40,$40,$58,$48,$48,$38,0,$44,$6c,$54,$44,$44,$44,$44,0
c_font:
    rts // Full original menu font is already installed, including G/M.
    ldx #7
c_font_loop:
    lda c_letters,x
    sta $4038,x // screen-code 7 G
    lda c_letters+8,x
    sta $4068,x // screen-code 13 M
    dex
    bpl c_font_loop
    rts
c_tables_end:
.if (c_tables_end > $8900) { .error "Tables overlap pointers" }

*=$9d70 "Stage 3b-5c conditional RRB renderer and game-over overlay"
c_render:
    jmp entry.e_render
c_render_enemy:
    lda c_es,x
    beq c_render_enemy_done
    cmp #c_EXP
    beq c_render_explosion
    jsr c_enemy_xy
    lda c_bx
    sta v014_x
    lda c_by
    sta v014_y
    lda #<$261
    ldy #>$261
    cpx #22
    bne c_render_normal
    lda #<$325
    ldy #>$325
c_render_normal:
    jsr c_glyph
    jmp v014_submit_pixie
c_render_explosion:
    lda c_ex,x
    sta v014_x
    lda c_ey,x
    sta v014_y
    lda c_ef,x
    tax
    jsr c_explosion_glyph
    jmp v014_submit_pixie
c_render_enemy_done:
    rts
c_explosion_glyph:
    lda c_exp_low,x
    ldy c_exp_high,x
c_glyph:
    sta v014_top_lo
    sty v014_top_hi
    clc
    adc #1
    sta v014_bot_lo
    tya
    adc #0
    sta v014_bot_hi
    lda v014_bot_lo
    clc
    adc #1
    sta v014_guard_lo
    lda v014_bot_hi
    adc #0
    sta v014_guard_hi
    rts
c_exp_low: .byte <$305,<$309,<$30d,<$311,<$315,<$319,<$31d
c_exp_high: .byte >$305,>$309,>$30d,>$311,>$315,>$319,>$31d

c_game_over:
    // Dynamic screen tail only: original opaque prefix and HUD stay intact.
    lda #9
    sta c_ui_row
    lda #9
    sta c_ui_length
    lda #0
    sta c_ui_offset
    lda #168
    jmp c_message // GAME OVER only; no obsolete restart/exit captions.
c_fire_state:
    lda c_ps
    cmp #c_BLINK
    beq !allowed+
    cmp #c_ACTIVE
    rts
!allowed:
    lda #0 // Z=1 permits the unchanged two-slot fire routine, even when hidden.
    rts
c_message:
    pha
    ldx c_ui_row
    jsr v012a_set_row_pointer
    ldy #0
    pla
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    ldx c_ui_offset
c_message_screen:
    iny
    lda c_message_text,x
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    inx
    dec c_ui_length
    bne c_message_screen
    iny
    lda #$80 // terminating GOTOX at native X=640
    jsr v012a_store
    iny
    lda #2
    jsr v012a_store
    iny
    lda #0
    jsr v012a_store
    iny
    lda #2 // existing blank NCM glyph $200
    jsr v012a_store
    // Direct long colour store avoids CIA/CRAM2K banking side effects.
    tya
    sec
    sbc #5
    lsr
    sta c_ui_length
    ldy #0
    lda #$0f
    sta $1a60+3
    lda #$f8
    sta $1a60+2
    // Physical colour address $FF80000 + RRB_STRIDE*row + 84.
    lda #84
    sta $1a60
    lda #0
    sta $1a60+1
    ldx c_ui_row
c_message_colour_row:
    clc
    lda $1a60
    adc #RRB_STRIDE
    sta $1a60
    bcc !next+
    inc $1a60+1
!next:
    dex
    bne c_message_colour_row
    lda #$10
    sta $1a65
    jsr hud.long_colour_store
    inc $1a60
    lda #0
    jsr hud.long_colour_store
    inc $1a60
c_message_colour:
    lda #0
    sta $1a65
    jsr hud.long_colour_store
    inc $1a60
    lda #2 // bank-1 white, mono attributes
    sta $1a65
    jsr hud.long_colour_store
    inc $1a60
    dec c_ui_length
    bne c_message_colour
    lda #$10
    sta $1a65
    jsr hud.long_colour_store
    inc $1a60
    lda #0
    sta $1a65
    jsr hud.long_colour_store
    inc $1a60
    lda #8
    sta $1a65
    jsr hud.long_colour_store
    inc $1a60
    lda #0
    sta $1a65
    jmp hud.long_colour_store
c_message_text: .byte 7,1,13,5,32,15,22,5,18 // GAME OVER
    .byte 18,32,45,32,18,5,19,20,1,18,20 // R - RESTART
    .byte 24,32,45,32,5,24,9,20 // X - EXIT
c_render_end:
.if (c_render_end > $a000) { .error "Renderer exceeds ROM-safe $9fff" }
}

// Immutable guarded originals; independently addressed by every actor.
*=$c100 "Original explosion frames 0-6, with transparent guards"
.for(var c_f=0;c_f<7;c_f++) {
    .fill 64,0
    .import binary "explosion_assets/explosion_0"+c_f+"_ncm.bin"
    .fill 64,0
}
// Rejected source record 7 is deliberately not embedded in the PRG.
