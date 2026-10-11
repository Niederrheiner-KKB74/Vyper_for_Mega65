// Issue #10: signed coordinates, private transparent clipping, existing RRB rows.
.namespace offscreen {
.label r_enabled=$1d00
.label r_paused=$1d01
.label r_case=$1d02
.label r_hold=$1d03
.label r_x=$1d04
.label r_y=$1d06
.label r_draw_x=$1d08
.label r_draw_y=$1d09
.label r_src_x=$1d0a
.label r_src_y=$1d0b
.label r_width=$1d0c
.label r_height=$1d0d
.label r_decision=$1d0e // 0=cull, 1=original glyph, 2=private crop
.label r_axis=$1d10
.label r_min=$1d12
.label r_max=$1d13
.label r_draw=$1d14
.label r_src=$1d15
.label r_length=$1d16
.label r_delta=$1d17
.label r_row=$1d19
.label r_col=$1d1a
.label r_low=$1d1b
.label r_dest=$1d1c
.label r_source=$1d1d
.label r_keybyte=$1d1e
*=$4e30 "Stage 4a mode and RRB hook"
r_init:
    lda #0
    ldx #63
r_zero:
    sta $1d00,x
    dex
    bpl r_zero
    jmp game.c_init
r_key:
    jsr KERNAL_GETIN
    cmp #$61
    bcc r_upper
    cmp #$7b
    bcs r_upper
    and #$df
r_upper:
    cmp #$c1
    bcc r_dispatch
    cmp #$db
    bcs r_dispatch
    and #$7f
r_dispatch:
    sta r_keybyte
    cmp #$46 // F: toggle test; never enter a death/respawn/GAME OVER state.
    bne r_other
    lda game.c_ps
    bne r_consumed
    lda r_enabled
    eor #1
    sta r_enabled
    beq r_consumed
    lda #0
    sta r_case
    sta r_paused
    jsr r_begin
    jmp r_consumed
r_other:
    lda r_enabled
    beq r_passthrough
    lda r_keybyte
    cmp #$54 // T/E change gameplay test states: leave the frozen game intact.
    beq r_consumed
    cmp #$45
    beq r_consumed
    cmp #$4e // N: next approach
    beq r_next_key
    cmp #$50 // P: freeze signed test position (animation keeps running)
    bne r_passthrough
    lda r_paused
    eor #1
    sta r_paused
    jmp r_consumed
r_next_key:
    jsr r_next
r_consumed:
    lda #0
    rts
r_passthrough:
    lda r_keybyte
    // Tail jump after GETIN retains the exact original restart-error stack depth.
    jmp game.c_key+3
r_render:
    lda r_enabled
    bne r_test_render
    jmp game.c_render
r_test_render:
    lda #0
    sta v014_overflow_count
    ldx #0
r_clear:
    lda #0
    sta v014_row_count,x
    jsr s2ia_clear_row
    inx
    cpx #25
    bne r_clear
    jsr r_clip
    lda r_decision
    beq r_finish
    cmp #2
    bne r_original
    jsr r_crop
    lda #<$329
    ldy #>$329
    bne r_submit
r_original:
    lda #<$261
    ldy #>$261
r_submit:
    jsr game.c_glyph
    lda r_draw_x
    sta v014_x
    lda r_draw_y
    sta v014_y
    jsr v014_submit_pixie
r_finish:
    ldx #0
r_terminators:
    stx v014_row
    jsr v014_write_terminator
    ldx v014_row
    inx
    cpx #25
    bne r_terminators
    rts
.if (* > $5000) { .error "Stage 4a mode overlaps screen" }

*=$8660 "Stage 4a isolated movement"
r_move:
    lda r_enabled
    bne r_return
    jmp game.c_move
r_objects:
    lda r_enabled
    bne r_motion
    jmp game.c_objects
r_tick:
    lda r_enabled
    beq r_normal_tick
    jsr shots.p_disable
    jmp hud.hud_render
r_normal_tick:
    jmp game.c_tick
r_return:
    rts
r_motion:
    lda r_paused
    bne r_return
    lda r_hold
    beq r_step
    dec r_hold
    rts
r_step:
    ldx r_case
    lda r_x
    cmp r_end_x_lo,x
    bne r_step_now
    lda r_x+1
    cmp r_end_x_hi,x
    bne r_step_now
    lda r_y
    cmp r_end_y_lo,x
    bne r_step_now
    lda r_y+1
    cmp r_end_y_hi,x
    beq r_next
r_step_now:
    lda r_dx,x
    beq r_step_y
    bmi r_left
    inc r_x
    bne r_step_y
    inc r_x+1
    jmp r_step_y
r_left:
    lda r_x
    bne r_left_low
    dec r_x+1
r_left_low:
    dec r_x
r_step_y:
    lda r_dy,x
    beq r_return
    bmi r_up
    inc r_y
    bne r_return
    inc r_y+1
    rts
r_up:
    lda r_y
    bne r_up_low
    dec r_y+1
r_up_low:
    dec r_y
    rts
r_next:
    inc r_case
    lda r_case
    cmp #5
    bcc r_begin
    lda #0
    sta r_case
r_begin:
    ldx r_case
    lda r_start_x_lo,x
    sta r_x
    lda r_start_x_hi,x
    sta r_x+1
    lda r_start_y_lo,x
    sta r_y
    lda r_start_y_hi,x
    sta r_y+1
    lda #1
    sta r_hold
    rts
r_start_x_lo: .byte 112,112,$f0,240,$f0
r_start_x_hi: .byte 0,0,$ff,0,$ff
r_start_y_lo: .byte $f0,200,92,92,$f0
r_start_y_hi: .byte $ff,0,0,0,$ff
r_end_x_lo: .byte 112,112,240,$f0,240
r_end_x_hi: .byte 0,0,0,$ff,0
r_end_y_lo: .byte 200,$f0,92,92,240
r_end_y_hi: .byte 0,$ff,0,0,0
r_dx: .byte 0,0,1,$ff,1
r_dy: .byte 1,$ff,0,0,1
.if (* > $8800) { .error "Stage 4a motion overlaps existing glyph" }

*=$8e20 "Stage 4a signed clip and NCM crop"
r_clip:
    lda #0
    sta r_decision
    lda r_x
    sta r_axis
    lda r_x+1
    sta r_axis+1
    lda #0
    sta r_min
    lda #240
    sta r_max
    jsr r_clip_axis
    lda r_draw
    sta r_draw_x
    lda r_src
    sta r_src_x
    lda r_length
    sta r_width
    lda r_y
    sta r_axis
    lda r_y+1
    sta r_axis+1
    lda #0
    sta r_min
    lda #200
    sta r_max
    jsr r_clip_axis
    lda r_draw
    sta r_draw_y
    lda r_src
    sta r_src_y
    lda r_length
    sta r_height
    beq r_clip_done
    lda r_width
    beq r_clip_done
    cmp #16
    bne r_partial
    lda r_height
    cmp #16
    bne r_partial
    lda #1
    sta r_decision
    rts
r_partial:
    lda #2
    sta r_decision
r_clip_done:
    rts
r_clip_axis:
    lda #0
    sta r_length
    sta r_src
    sta r_draw
    sec
    lda r_axis
    sbc r_min
    sta r_delta
    lda r_axis+1
    sbc #0
    sta r_delta+1
    bpl r_positive
    cmp #$ff
    bne r_axis_done
    lda r_delta
    cmp #$f1 // -15..-1; <=-16 fully outside
    bcc r_axis_done
    eor #$ff
    clc
    adc #1
    sta r_src
    lda r_min
    sta r_draw
    lda #16
    sec
    sbc r_src
    sta r_length
    rts
r_positive:
    lda r_axis+1
    bne r_axis_done
    lda r_axis
    cmp r_max
    bcs r_axis_done
    sta r_draw
    lda r_max
    sec
    sbc r_axis
    cmp #16
    bcc r_axis_length
    lda #16
r_axis_length:
    sta r_length
r_axis_done:
    rts
r_crop:
    lda #0
    sta r_row
    sta r_dest
r_crop_row:
    lda #0
    sta r_col
r_crop_pixel:
    lda r_row
    cmp r_height
    bcs r_transparent
    lda r_col
    cmp r_width
    bcs r_transparent
    clc
    adc r_src_x
    pha
    lsr
    sta r_source
    lda r_row
    clc
    adc r_src_y
    asl
    asl
    asl
    clc
    adc r_source
    tay
    pla
    and #1
    beq r_low_source
    lda $9840,y
    lsr
    lsr
    lsr
    lsr
    jmp r_pixel
r_low_source:
    lda $9840,y
    and #15
    jmp r_pixel
r_transparent:
    lda #0
r_pixel:
    tay
    lda r_col
    and #1
    bne r_pack
    sty r_low
    jmp r_pixel_next
r_pack:
    tya
    asl
    asl
    asl
    asl
    ora r_low
    ldx r_dest
    sta $ca40,x // no CPU reads under BASIC ROM; guards never touched
    inc r_dest
r_pixel_next:
    inc r_col
    lda r_col
    cmp #16
    bne r_crop_pixel
    inc r_row
    lda r_row
    cmp #16
    bne r_crop_row
    rts
.if (* > $9000) { .error "Stage 4a crop overlaps BASIC colour backup" }
*=$ca00 "Stage 4a private guarded NCM crop"
.fill 256,0
}
