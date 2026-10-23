// Issue #12, historical Amiga reference. Timing defaults remain explicit parameters.
.namespace entry {
.const e_WAIT=5
.const e_POINT_TICKS=1
.const e_START_POINT_TICK=1
.const e_GROUP_DELAY=0
.const e_RETURN_STEP=1 // historical State-2 rule; Debut-specific binary check pending
.label e_xlo=$1e00
.label e_xhi=$1e16
.label e_ylo=$1e2c
.label e_yhi=$1e42
.label e_tx=$1e58
.label e_ty=$1e6e
.label e_delay=$1e84
.label e_cursor=$1e9a
.label e_group=$1eb0
.label e_phase=$1ec6 // 0 waiting, 1 curve, 2 return, 3 formation
.label e_timer=$1edc
.label e_gxlo=$6a20
.label e_gxhi=$6a24
.label e_gylo=$6a28
.label e_gyhi=$6a2c
.label e_gptrlo=$6a30
.label e_gptrhi=$6a34
.label e_glen=$6a38
.label e_gcount=$6a40
.label e_interval=$1d50
.label e_ticklo=$1d51
.label e_tickhi=$1d52
.label e_slot=$1d53
.label e_g=$1d54
.label e_remaining=$1d55
.label e_nextdelay=$1d56
.label e_byte=$1d57
.label e_dx=$1d58
.label e_dy=$1d59
.label e_delta=$1d5a
.label e_sign=$1d5b
.label e_glyphlo=$1d5c
.label e_glyphhi=$1d5d
.label e_diag=$1d5e
.label e_last=$1d5f
.label e_demo=$1d60
.label e_visible=$1d64 // 23 visibility flags; reset with enemy states
.label e_glenhi=$6a3c
.label e_cursorhi=$6a50
.label e_delayhi=$6a66
*=$5700 "Stage 4b Level-1 parser and motion"
e_init:
    jsr ygeometry.clear
    lda #0
    ldx #0
e_zero:
    sta $1e00,x
    inx
    bne e_zero
    ldx #$1f
e_zero_groups:
    sta $1d40,x
    dex
    bpl e_zero_groups
    // Slot 22 is cleared by e_clear_states below.
    sta shots.p_test_enabled
    sta e_demo
    ldx #22
e_clear_states:
    sta game.c_es,x
    sta e_visible,x
    dex
    bpl e_clear_states
    ldx #$5b
!clear_extra:
    sta $6a20,x
    dex
    bpl !clear_extra-
    lda $7604
    sta e_interval
    // prepare bounded the bank1 record; per-group lengths and delays are WORDs.
    lda #<$2008
    sta s3b2.pointer
    lda #>$2008
    sta s3b2.pointer+1
    ldx #0
e_group_parse:
    stx e_g
    jsr s3b2.read_word
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_g
    lda s3b2.word_value
    sta e_gcount,x
    lda s3b2.word_value+1
    beq !valid+
    jmp e_invalid
!valid:
    jsr s3b2.read_word
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_g
    lda s3b2.word_value
    sta e_gxlo,x
    lda s3b2.word_value+1
    sta e_gxhi,x
    jsr s3b2.read_word
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_g
    lda s3b2.word_value
    sta e_gylo,x
    lda s3b2.word_value+1
    sta e_gyhi,x
    jsr s3b2.read_word
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_g
    lda s3b2.word_value
    sta e_glen,x
    lda s3b2.word_value+1
    sta e_glenhi,x
    lda s3b2.pointer
    sta e_gptrlo,x
    lda s3b2.pointer+1
    sta e_gptrhi,x
    jsr s3b2.skip_curve
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_g
    inx
    cpx $7602
    beq !valid+
    jmp e_group_parse
!valid:
    lda #0
    sta e_g
    sta e_slot
e_assign_group:
    ldx e_g
    lda e_gcount,x
    sta e_remaining
    lda #0
    sta e_nextdelay
    sta level.nextdelayhi
e_assign:
    ldx e_slot
    lda e_g
    sta e_group,x
    lda e_nextdelay
    sta e_delay,x
    lda level.nextdelayhi
    sta e_delayhi,x
    lda #e_WAIT
    sta game.c_es,x
    jsr s3b2.read_word
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_slot
    lda s3b2.word_value
    cmp #225
    bcc !valid+
    jmp e_invalid
!valid:
    sta e_tx,x
    lda s3b2.word_value+1
    beq !valid+
    jmp e_invalid
!valid:
    jsr s3b2.read_word
    bcc !valid+
    jmp e_invalid
!valid:
    ldx e_slot
    lda s3b2.word_value
    jsr attack.a_formation_y
    bcc !valid+
    jmp e_invalid
!valid:
    sta e_ty,x
    lda s3b2.word_value+1
    beq !valid+
    jmp e_invalid
!valid:
    jsr s3b2.get_byte
    bcc !valid+
    jmp e_invalid
!valid: // graphic_type, already verified 14 -> type 15
    jsr s3b2.get_byte
    bcc !valid+
    jmp e_invalid
!valid: // binding VYLV +5 curve assignment: data audit + original-game user observation
    ldx e_slot
    sta attack.a_index,x
    lda e_nextdelay
    clc
    adc e_interval
    sta e_nextdelay
    lda level.nextdelayhi
    adc $7605
    sta level.nextdelayhi
    inc e_slot
    dec e_remaining
    beq !valid+
    jmp e_assign
!valid:    inc e_g
    lda e_g
    cmp $7602
    beq !valid+
    jmp e_assign_group
!valid:
    jsr attack.a_init
    lda s3b.error
    bne e_init_done
    jmp fireevents.init
e_init_done:
    rts
e_invalid:
    lda #7
    sta s3b.error
    rts
e_objects:
    jsr ygeometry.restore
    lda game.c_ps
    cmp #4
    beq e_motion_done
    inc e_ticklo
    bne e_tick_ready
    inc e_tickhi
e_tick_ready:
    lda #0
    sta e_slot
e_motion_loop:
    ldx e_slot
    jsr e_move_one
    inc e_slot
    lda e_slot
    cmp $7603
    bne e_motion_loop
e_motion_done:
    jmp ygeometry.postframe
e_move_one:
    lda game.c_es,x
    bne !skip+
    jmp e_move_done
!skip:
    cmp #4
    bne !skip+
    jmp e_move_done
!skip:
    cmp #e_WAIT
    bne e_entry
    lda e_delay,x
    ora e_delayhi,x
    beq e_spawn
    lda e_delay,x
    bne !low+
    dec e_delayhi,x
!low:
    dec e_delay,x
    rts
e_spawn:
    lda e_group,x
    tay
    lda e_gxlo,y
    sta e_xlo,x
    lda e_gxhi,y
    sta e_xhi,x
    lda e_gylo,y
    sta e_ylo,x
    lda e_gyhi,y
    sta e_yhi,x
    lda #1
    sta e_phase,x
    lda #2
    sta game.c_es,x
    jsr audio8.entry
    .if (e_START_POINT_TICK==0) { jmp e_curve } else { jmp e_mirror }
e_entry:
    jsr attack.a_step
    bcc !normal+
    rts
!normal:
    lda e_phase,x
    cmp #1
    beq e_curve
    cmp #2
    beq !skip+
    jmp e_move_done
!skip:
    jmp e_return
e_curve:
    lda e_timer,x
    beq e_curve_ready
    dec e_timer,x
    rts
e_curve_ready:
    lda #(e_POINT_TICKS-1)
    sta e_timer,x
    lda e_group,x
    tay
    clc
    lda e_gptrlo,y
    adc e_cursor,x
    sta level.read_pointer
    lda e_gptrhi,y
    adc e_cursorhi,x
    sta level.read_pointer+1
e_curve_read:
    jsr level.read_record
    sta e_byte
    lsr
    lsr
    lsr
    lsr
    jsr e_decode
    sta e_dx
    lda e_byte
    and #15
    jsr e_decode_y
    sta e_dy
    lda e_dx
    clc
    adc e_xlo,x
    sta e_xlo,x
    lda #0
    bit e_dx
    bpl e_dx_positive
    lda #$ff
e_dx_positive:
    adc e_xhi,x
    sta e_xhi,x
    lda e_dy
    clc
    adc e_ylo,x
    sta e_ylo,x
    lda #0
    bit e_dy
    bpl e_dy_positive
    lda #$ff
e_dy_positive:
    adc e_yhi,x
    sta e_yhi,x
    inc e_cursor,x
    bne !cursor+
    inc e_cursorhi,x
!cursor:
    jsr fireevents.entry_tick
    lda e_cursorhi,x
    cmp e_glenhi,y
    bne e_mirror
    lda e_cursor,x
    cmp e_glen,y
    bne e_mirror
    jsr ygeometry.finish_entry
    lda #2
    sta e_phase,x
    jmp e_mirror
e_decode:
    cmp #8
    bcc e_decode_done
    and #7
    eor #$ff
    clc
    adc #1
e_decode_done:
    rts
e_move_done:
    rts
e_mirror:
    lda e_xlo,x
    sta s2i_x,x
    lda e_ylo,x
    sta s2i_y,x
    lda e_diag
    beq e_mirror_done
    stx e_last
e_mirror_done:
    rts
e_error_check:
    lda s3b.error
    beq !valid+
    pla
    pla
    pla
    pla
    jmp exit_to_basic
!valid:
    rts
e_key_dispatch:
    lda offscreen.r_keybyte
    cmp #$44
    bne e_key_pass
    lda game.c_ps
    cmp #4
    beq e_key_reload
    lda e_diag
    eor #1
    sta e_diag
    lda #0
    rts
e_key_reload:
    lda offscreen.r_keybyte
e_key_pass:
    jmp game.c_key+3

e_attack_test:
    // T/E remains an isolated legacy demo, never a claimed original attack.
    ldx #18
    lda game.c_es,x
    beq !no+
    cmp #4
    beq !no+
    lda e_phase,x
    cmp #3
    bne !no+
    jsr attack.a_legacy_attack
    lda #1
    ldy shots.p_attacking
    beq !set+
    lda game.c_mode
!set:
    sta game.c_es+18
    rts
!no:
    lda #0
    sta shots.p_attacking
    rts

e_render:
    lda #0
    sta v014_overflow_count
    ldx #0
e_clear_row:
    lda #0
    sta v014_row_count,x
    jsr s2ia_clear_row
    inx
    cpx #25
    bne e_clear_row
    lda game.c_ps
    cmp #2
    beq e_render_enemies
    cmp #4
    beq e_render_enemies
    cmp #3
    bne e_player_draw
    lda game.c_visible
    beq e_render_enemies
e_player_draw:
    lda V014_PLAYER+2
    sta v014_x
    lda V014_PLAYER+4
    sta v014_y
    lda game.c_ps
    cmp #1
    bne e_player_ship
    ldx game.c_pf
    jsr game.c_explosion_glyph
    jmp e_player_submit
e_player_ship:
    lda #<$321
    ldy #>$321
    jsr game.c_glyph
e_player_submit:
    jsr v014_submit_pixie
e_render_enemies:
    lda #0
    sta e_slot
e_draw_loop:
    ldx e_slot
    jsr e_is_visible
    beq e_draw_next
    jsr e_draw_one
e_draw_next:
    inc e_slot
    lda e_slot
    cmp $7603
    bne e_draw_loop
    ldx #0
e_end_rows:
    stx v014_row
    jsr v014_write_terminator
    ldx v014_row
    inx
    cpx #25
    bne e_end_rows
    rts
e_draw_one:
    lda e_xlo,x
    sta offscreen.r_x
    lda e_xhi,x
    sta offscreen.r_x+1
    lda e_ylo,x
    sta offscreen.r_y
    lda e_yhi,x
    sta offscreen.r_y+1
    jsr offscreen.r_clip
    lda offscreen.r_decision
    beq e_draw_done
    lda offscreen.r_draw_x
    sta v014_x
    lda offscreen.r_draw_y
    sta v014_y
    lda offscreen.r_decision
    cmp #2
    beq e_crop_frame
    jmp level.full_frame
e_draw_done:
    rts
e_crop_frame:
    jsr level.enemy_frame
    lda #$40
    sta e_dma_source
    lda #$98
    sta e_dma_source+1
    ldx e_slot
    lda game.c_es,x
    cmp #4
    bne e_stage_frame
    lda game.c_ef,x
    clc
    adc #$c1
    sta e_dma_source+1
e_stage_frame:
    lda #128
    sta e_dma_length
    lda #0
    sta e_dma_length+1
    lda #$40
    sta e_dma_dest
    lda #$56
    sta e_dma_dest+1
    lda #0
    sta e_dma_dest+2
    jsr e_copy
    lda #$56
    sta offscreen.r_high_source+2
    sta offscreen.r_low_source+2
    jsr level.fast_crop
    lda #$98
    sta offscreen.r_high_source+2
    sta offscreen.r_low_source+2
    lda #0
    sta e_dma_source
    sta e_dma_dest
    sta e_dma_length
    lda #$ca
    sta e_dma_source+1
    lda #1
    sta e_dma_length+1
    sta e_dma_dest+2
    lda e_slot
    ora #$40 // Bank1 $14000 + slot*256; never DOS $10000-$11FFF.
    sta e_dma_dest+1
    jsr e_copy
e_private_glyph:
    lda e_slot
    asl
    asl
    clc
    adc #1
    ldy #5 // $14000 + slot*256 + $40; independent guarded NCM per slot
    jsr game.c_glyph
    jmp v014_submit_pixie
e_copy:
    lda #>e_copy_dma
    ldx #<e_copy_dma
    jmp hud.transfer
e_copy_dma:
    .byte $80,0,$81,0,$0a,0,0
e_dma_length: .word 128
e_dma_source: .byte $40,$98,0
e_dma_dest: .byte $40,$56,0
    .word 0

.if (* > $5c80) { .error "Entry parser/motion overlaps lookup data" }

*=$7500 "Stage 4b formation return and colour backup extension"
e_return:
    jsr attack.a_goal
    .for (var i=0;i<e_RETURN_STEP;i++) { jsr e_return_one }
    rts
e_return_one:
    // One step per axis, no teleport. Historical State 2; exact Debut rate open.
    lda e_xhi,x
    bmi e_return_x_inc
    bne e_return_x_dec
    lda e_xlo,x
    cmp attack.a_goalx
    beq e_return_y
    bcc e_return_x_inc
e_return_x_dec:
    lda e_xlo,x
    bne e_return_x_lowdec
    dec e_xhi,x
e_return_x_lowdec:
    dec e_xlo,x
    jmp e_return_y
e_return_x_inc:
    inc e_xlo,x
    bne e_return_y
    inc e_xhi,x
e_return_y:
    lda e_yhi,x
    bmi e_return_y_inc
    bne e_return_y_dec
    lda e_ylo,x
    cmp e_ty,x
    beq e_return_check
    bcc e_return_y_inc
e_return_y_dec:
    lda e_ylo,x
    bne e_return_y_lowdec
    dec e_yhi,x
e_return_y_lowdec:
    dec e_ylo,x
    jmp e_return_check
e_return_y_inc:
    inc e_ylo,x
    bne e_return_check
    inc e_yhi,x
e_return_check:
    lda e_xhi,x
    ora e_yhi,x
    bne e_return_done
    lda e_xlo,x
    cmp attack.a_goalx
    bne e_return_done
    lda e_ylo,x
    cmp e_ty,x
    bne e_return_done
    lda #3
    sta e_phase,x
    lda #1
    sta game.c_es,x
e_return_done:
    jmp e_mirror
e_save_colour:
    lda #>e_save_dma
    ldx #<e_save_dma
    jmp hud.transfer
e_restore_colour:
    lda #>e_restore_dma
    ldx #<e_restore_dma
    jmp hud.transfer
e_save_dma:
    .byte $80,$ff,$81,0,$0a,0,0
    .word $640
    .byte $80,$0c,8,0,$50,0
    .word 0
e_restore_dma:
    .byte $80,0,$81,$ff,$0a,0,0
    .word $640
    .byte 0,$50,0,$80,$0c,8
    .word 0
.if (* > $7600) { .error "Entry return overlaps Level-1 record" }
}
.namespace entry {
*=$7ee2 "Stage 4b signed collision boxes"
e_collision_box:
    cpx $7603
    bcc e_box_signed
    jsr game.c_enemy_xy
    jmp game.c_ship_box
e_box_signed:
    jsr e_is_visible
    beq e_box_empty
    .fill 2,$ea
    stx e_slot
    lda #12
    sta offscreen.r_size
    lda #0
    sta offscreen.r_min
    lda #240
    sta offscreen.r_max
    clc
    lda e_xlo,x
    adc #2
    sta offscreen.r_axis
    lda e_xhi,x
    adc #0
    sta offscreen.r_axis+1
    jsr offscreen.r_clip_axis
    lda offscreen.r_length
    beq e_box_empty
    clc
    adc offscreen.r_draw
    sta game.c_br
    lda offscreen.r_draw
    sta game.c_bx
    lda #200
    sta offscreen.r_max
    ldx e_slot
    clc
    lda e_ylo,x
    adc #2
    sta offscreen.r_axis
    lda e_yhi,x
    adc #0
    sta offscreen.r_axis+1
    jsr offscreen.r_clip_axis
    lda offscreen.r_length
    beq e_box_empty
    clc
    adc offscreen.r_draw
    sta game.c_bb
    lda offscreen.r_draw
    sta game.c_by
    ldx e_slot
    rts
e_box_empty:
    lda #240
    sta game.c_bx
    sta game.c_br
    lda #200
    sta game.c_by
    sta game.c_bb
    ldx e_slot
    rts
.if (* > $8000) { .error "Signed boxes overlap original glyphs" }
}

.namespace entry {
*=$874b "Stage 4b optional legacy attack demo"
e_demo_step:
    cpx #18
    bne e_demo_no
    lda e_phase,x
    cmp #3
    bne e_demo_no
    lda shots.p_test_enabled
    beq e_demo_stop
    lda #1
    sta e_demo
    lda s2i_phase,x
    clc
    adc s2i_speed,x
    sta s2i_phase,x
    tay
    lda v014_orbit_x,y
    sta e_xlo,x
    lda v014_orbit_y,y
    sta e_ylo,x
    lda #0
    sta e_xhi,x
    sta e_yhi,x
    sec
    jmp e_mirror
e_demo_stop:
    lda e_demo
    beq e_demo_no
    lda #0
    sta e_demo
    lda #2
    sta e_phase,x
    sta game.c_es,x
e_demo_no:
    clc
    rts
.if (* > $8800) { .error "Legacy demo exceeds free slot" }
*=$5b80 "Stage 4b fast valid RRB row retirement"
e_clear_screen:
    php
    pha
    txa
    pha
    lda hud.row_pointer
    sta e_screen_destination
    lda hud.row_pointer+1
    sta e_screen_destination+1
    lda #>e_screen_dma
    ldx #<e_screen_dma
    jsr hud.transfer
    pla
    tax
    pla
    plp
    rts
e_screen_dma:
    .byte $80,0,$81,0,$0a,0,0
    .word RRB_BYTES
    .byte <e_empty_screen,>e_empty_screen,0
e_screen_destination: .byte 0,0,0
    .word 0
e_empty_screen:
    .fill RRB_BYTES, (mod(i,4)==0) ? $80 : ((mod(i,4)==2) ? 0 : 2)
.if (* > $5c80) { .error "Row retirement overlaps legacy table" }

*=$5c20 "Stage 4b-1 entry visibility"
e_decode_y:
    jsr e_decode
    pha
    ora e_dx
    beq !still+
    lda #1
    sta e_visible,x
!still:
    pla
    rts
e_is_visible:
    jsr attack.a_visible
    beq !hidden+
    lda game.c_es,x
    beq !hidden+
    cmp #e_WAIT
    beq !hidden+
    lda e_phase,x
    cmp #1
    bne !shown+
    lda e_visible,x
    rts
!shown:
    lda #1
    rts
!hidden:
    lda #0
    rts
.if (* > $5c80) { .error "Visibility helper overlaps lookup table" }

}
