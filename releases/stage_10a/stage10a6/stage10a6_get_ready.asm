// PR88 corrected original rules: 100 complete PAL waits before any ENTRY tick.
.namespace getready {
.label gr_timer=$1b1c
.label gr_saved_pause=$1b1d
.label gr_row=$1b1e
.label gr_skip=$1b1f // input-triggered starts must not count their already-running frame
*=$9a2a "Stage10a1 native ready and completion gates"
gr_scene:
    lda level.mode
    cmp #3
    beq !done+
    jmp offscreen.r_render
!done:
    rts
gr_begin:
    lda #8
    jmp twop.gate
gr_tick:
    lda #4
    jmp twop.gate
gr_completed:
    lda #7
    jsr twop.gate
    lda hud.player1_level
    jmp level.transition
.if (*>$9a56) { .error "Ready gates overlap attack start" }

*=$af08 "Stage10a1 mapped ready FSM and original-font prompt"
gr_prepare:
    lda anim_paused
    sta gr_saved_pause
    lda #1
    sta anim_paused
    lda #3
    sta level.mode
    lda #100
    sta gr_timer
    jsr shots.p_disable
    lda #0
    sta gr_skip
    sta gr_row
!clear:
    ldx gr_row
    lda #0
    sta v014_row_count,x
    jsr s2ia_clear_row
    inc gr_row
    lda gr_row
    cmp #25
    bne !clear-
    jsr cc_publish
    lda cc_index // exact same bank1 palette entry as enemy highlight COLOR02
    sta game.c_message_ink
    lda #<gr_ready_text
    sta game.c_message_read
    lda #>gr_ready_text
    sta game.c_message_read+1
    lda #17 // Y136, lower third; HUD begins beyond logical X240
    sta game.c_ui_row
    lda #9
    sta game.c_ui_length
    lda #0
    sta game.c_ui_offset
    lda #102 // logical X (former native H640 value 204 / 2)
    jsr game.c_message
    lda twop.active
    clc
    adc #$31
    sta gr_player_text+7
    lda #<gr_player_text
    sta game.c_message_read
    lda #>gr_player_text
    sta game.c_message_read+1
    lda #19 // Y152
    sta game.c_ui_row
    lda #8
    sta game.c_ui_length
    lda #0
    sta game.c_ui_offset
    lda #104 // logical X (former native 208 / 2)
    jsr game.c_message
    // Restore ordinary GAME OVER source/ink before leaving the IRQ-masked gate.
    lda #<game.c_message_text
    sta game.c_message_read
    lda #>game.c_message_text
    sta game.c_message_read+1
    lda #2
    sta game.c_message_ink
    rts
gr_countdown:
    lda gr_skip
    beq !count+
    dec gr_skip
    rts
!count:
    dec gr_timer
    bne !done+
    lda gr_saved_pause
    sta anim_paused
    lda #0
    sta level.mode
    ldx #17
    jsr s2ia_clear_row // restore screen AND standard NCM colour attributes
    ldx #19
    jsr s2ia_clear_row
    lda #1
    sta shots.p_fire_latch // held fire must be released, no queued shot
!done:
    rts
gr_ready_text: .byte 7,$65,$74,$20,$72,$65,$61,$64,$79
gr_player_text: .byte 16,$6c,$61,$79,$65,$72,$20,$31
.if (*>$b000) { .error "Get ready overlaps resident shot parameters" }
}
