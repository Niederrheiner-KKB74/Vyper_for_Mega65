// Central level management; all execution remains below ROMA ($A000).
.namespace level {
.label number=$1d80
.label record_end=$1d81 // low16 endpoint in physical bank1
.label record_size=$1d83
.label read_pointer=$1d85
.label y_shift=$1d87
.label attack_allowed=$1d88
.label mode=$1d89 // 0 PLAY,2 TRANSITION; no confirmation state
.label button_armed=$1d8a // legacy padding, no input latch required
.label bonus_progress=$1fd9 // two independent slots; P2 reserved/inactive
.label nav_latch=$1d8b
.label nextdelayhi=$1d8c
.label index=$1d8d
.label temporary=$1d8e
.label saved_speed=$1d8f
.label saved_pause=$1d90
.label requested=$1d91
.label frame_index=$1d92
.label directory=$1d94 // eight bytes
.label gxlo=$6a80
.label gxhi=$6a96
.label gframe=$6ac2
.label gframes=$6aac

*=$6000 "Stage5a central levels and transitions (retired colour template)"
load_record:
    lda number
    bne !guard+
    jmp bad_record
!guard:
    cmp #101
    bcc !guard+
    jmp bad_record
!guard:
    sec
    sbc #1
    sta s3b.dma_src_lo
    lda #0
    sta s3b.dma_src_hi
    .for (var i=0;i<3;i++) { asl s3b.dma_src_lo; rol s3b.dma_src_hi }
    clc
    lda s3b.dma_src_lo
    adc #8
    sta s3b.dma_src_lo
    lda s3b.dma_src_hi
    adc #0
    sta s3b.dma_src_hi
    lda #4
    sta s3b.dma_src_bank
    lda #<directory
    sta s3b.dma_dst_lo
    lda #>directory
    sta s3b.dma_dst_hi
    lda #0
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    lda #8
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    lda directory+3
    ora directory+6
    ora directory+7
    beq !guard+
    jmp bad_record
!guard:
    lda directory+5
    cmp #7 // fixed capacity $700, originals max $6aa
    bcc !guard+
    jmp bad_record
!guard:
    ora directory+4
    bne !guard+
    jmp bad_record
!guard:
    lda directory+2
    cmp #2
    bcc !guard+
    jmp bad_record
!guard:
    // File offset must begin after directory $328.
    bne !range+
    lda directory+1
    cmp #3
    bcs !guard+
    jmp bad_record
!guard:
    bne !range+
    lda directory
    cmp #$28
    bcs !guard+
    jmp bad_record
!guard:
!range:
    jmp load_range
bad_record:
    jmp s3b2.invalid
load_range:
    clc
    lda directory
    adc directory+4
    sta s3b2.new_pointer
    lda directory+1
    adc directory+5
    sta s3b2.new_pointer+1
    lda directory+2
    adc #0
    cmp #1
    bcc !valid+
    beq !guard+
    jmp bad_record
!guard:
    lda s3b2.new_pointer+1
    cmp #$3f
    bcc !valid+
    beq !guard+
    jmp bad_record
!guard:
    lda s3b2.new_pointer
    cmp #$82 // VYLV exclusive file endpoint $13f81
    bcc !guard+
    jmp bad_record
!guard:
!valid:
    lda directory+4
    sta record_size
    sta s3b.dma_len_lo
    lda directory+5
    sta record_size+1
    sta s3b.dma_len_hi
    clc
    lda record_size
    sta record_end
    lda record_size+1
    adc #$20
    sta record_end+1
    lda directory
    sta s3b.dma_src_lo
    lda directory+1
    sta s3b.dma_src_hi
    lda directory+2
    clc
    adc #4
    sta s3b.dma_src_bank
    lda #0
    sta s3b.dma_dst_lo
    lda #$20
    sta s3b.dma_dst_hi
    lda #1
    sta s3b.dma_dst_bank
    jsr s3b.dma_copy
    lda #0
    sta s3b.dma_src_lo
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    lda #$20
    sta s3b.dma_src_hi
    lda #1
    sta s3b.dma_src_bank
    lda #0
    sta s3b.dma_dst_lo
    lda #$76
    sta s3b.dma_dst_hi
    lda #8
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    lda $7600
    cmp number
    beq !guard+
    jmp bad_header
!guard:
    lda $7601
    ora $7607
    beq !guard+
    jmp bad_header
!guard:
    lda $7602
    bne !guard+
    jmp bad_header
!guard:
    cmp #5
    bcc !guard+
    jmp bad_header
!guard:
    lda $7603
    bne !guard+
    jmp bad_header
!guard:
    cmp #23
    bcc !guard+
    jmp bad_header
!guard:
    lda $7604
    ora $7605
    bne !guard+
    jmp bad_header
!guard:
    lda $7606
    bne !guard+
    jmp bad_header
!guard:
    cmp #5
    bcc !guard+
    jmp bad_header
!guard:
    lda #1
    sta attack_allowed
    // Stage10a6: one-byte curves use the existing cyclic decoder.
    .fill 24,$ea // preserve every following Stage10a5 address
!done:
    clc
    rts
bad_header:
    jmp s3b2.invalid

// DMA reads physical bank1 even when ROMA/ROMC/MAP are active; X/Y preserved.
read_record:
    lda read_pointer
    sta s3b.dma_src_lo
    lda read_pointer+1
    sta s3b.dma_src_hi
    lda #1
    sta s3b.dma_src_bank
    sta s3b.dma_len_lo
    lda #0
    sta s3b.dma_len_hi
    sta s3b.dma_dst_bank
    lda #8
    sta s3b.dma_dst_lo
    lda #$6a
    sta s3b.dma_dst_hi
    jsr s3b.dma_copy
    lda $6a08
    rts

validate_enemies:
    lda #$ff
    sta y_shift
    lda #0
    sta index
!enemy:
    jsr s3b2.read_word
    bcc !guard+
    jmp invalid_enemy
!guard:
    lda s3b2.word_value+1
    beq !guard+
    jmp invalid_enemy
!guard:
    lda s3b2.word_value
    cmp #8
    bcs !guard+
    jmp invalid_enemy
!guard:
    cmp #217
    bcc !guard+
    jmp invalid_enemy
!guard:
    jsr s3b2.read_word
    bcc !guard+
    jmp invalid_enemy
!guard:
    lda s3b2.word_value+1
    beq !guard+
    jmp invalid_enemy
!guard:
    lda s3b2.word_value
    cmp y_shift
    bcs !y+
    sta y_shift
!y:
    jsr s3b2.get_byte
    bcc !guard+
    jmp invalid_enemy
!guard:
    cmp #38
    bcc !guard+
    jmp invalid_enemy
!guard:
    tax
    lda shots.p_mapping,x
    sta s3b2.selected_type
    jsr graphics_descriptor
    bcc !guard+
    jmp invalid_enemy
!guard:
    jsr s3b2.get_byte
    bcc !guard+
    jmp invalid_enemy
!guard:
    cmp $7606
    bcc !guard+
    jmp invalid_enemy
!guard:
    inc index
    lda index
    cmp $7603
    bne !enemy-
    // e_init will parse enemies again, now with common original Y minimum.
    clc
    rts
invalid_enemy:
    jmp s3b2.invalid

graphics_descriptor:
    lda s3b2.selected_type
    bne !guard+
    jmp graphics_bad
!guard:
    cmp #39
    bcc !guard+
    jmp graphics_bad
!guard:
    sta s3b.dma_src_lo
    lda #0
    sta s3b.dma_src_hi
    .for (var i=0;i<3;i++) { asl s3b.dma_src_lo; rol s3b.dma_src_hi }
    clc
    lda s3b.dma_src_hi
    adc #$40
    sta s3b.dma_src_hi
    lda #5
    sta s3b.dma_src_bank
    lda #0
    sta s3b.dma_dst_lo
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    lda #$6a
    sta s3b.dma_dst_hi
    lda #8
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    lda $6a02
    ora $6a03
    ora $6a05
    ora $6a06
    ora $6a07
    beq !guard+
    jmp graphics_bad
!guard:
    lda $6a04
    bne !guard+
    jmp graphics_bad
!guard:
    cmp #13
    bcc !guard+
    jmp graphics_bad
!guard:
    ldx index
    sta gframes,x
    lda #0
    sta gframe,x
    lda $6a00
    sta gxlo,x
    lda $6a01
    sta gxhi,x
    // Full range: directory-end <= source < end; complete frames <= VYGR bytes.
    cmp #1
    bcs !guard+
    jmp graphics_bad
!guard:
    bne !offset+
    lda $6a00
    cmp #$38
    bcs !guard+
    jmp graphics_bad
!guard:
!offset:
    lda $6a04
    sta s3b2.word_value
    lda #0
    sta s3b2.word_value+1
    .for (var i=0;i<7;i++) { asl s3b2.word_value; rol s3b2.word_value+1 }
    clc
    lda $6a00
    adc s3b2.word_value
    sta s3b2.new_pointer
    lda $6a01
    adc s3b2.word_value+1
    bcc !guard+
    jmp graphics_bad
!guard:
    cmp #$82
    bcc !ok+
    beq !guard+
    jmp graphics_bad
!guard:
    lda s3b2.new_pointer
    cmp #$b9
    bcc !guard+
    jmp graphics_bad
!guard:
!ok:
    clc
    rts
graphics_bad:
    lda #8
    sta s3b.error
    sec
    rts

// Select and verify original per-enemy frame; copy first to shared staging cache.
enemy_frame:
    ldx entry.e_slot
    lda game.c_es,x
    cmp #4
    bne !frame_ship+
    rts
!frame_ship:
    lda gframes,x
    bne !count_ok+
    jmp frame_invalid
!count_ok:
    cmp #13
    bcc !count_range+
    jmp frame_invalid
!count_range:
    lda gframe,x
!mod:
    cmp gframes,x
    bcc !frame+
    sec
    sbc gframes,x
    jmp !mod-
!frame:
    sta s3b2.word_value
    lda #0
    sta s3b2.word_value+1
    .for (var i=0;i<7;i++) { asl s3b2.word_value; rol s3b2.word_value+1 }
    clc
    lda gxlo,x
    adc s3b2.word_value
    sta s3b2.frame_source
    sta s3b.dma_src_lo
    lda gxhi,x
    adc s3b2.word_value+1
    clc
    adc #$40
    sta s3b2.frame_source+1
    sta s3b.dma_src_hi
    lda #5
    sta s3b.dma_src_bank
    lda #$40
    sta s3b.dma_dst_lo
    lda #$98
    sta s3b.dma_dst_hi
    lda #0
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    lda #128
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    // Read-back target and compare against separately fetched original frame.
    lda #$40
    sta s3b.dma_src_lo
    lda #$98
    sta s3b.dma_src_hi
    lda #0
    sta s3b.dma_src_bank
    lda #0
    sta s3b.dma_dst_lo
    lda #$69
    sta s3b.dma_dst_hi
    jsr s3b.dma_copy
    lda s3b2.frame_source
    sta s3b.dma_src_lo
    lda s3b2.frame_source+1
    sta s3b.dma_src_hi
    lda #5
    sta s3b.dma_src_bank
    lda #$68
    sta s3b.dma_dst_hi
    jsr s3b.dma_copy
    ldx #0
!compare:
    lda $6800,x
    cmp $6900,x
    bne !bad+
    inx
    cpx #128
    bne !compare-
!done:
    rts
!bad:
    lda #4
    sta s3b.error
    rts

frame_invalid:
    lda #8
    sta s3b.error
    rts

transition:
    sta requested
    lda anim_speed
    sta saved_speed
    lda anim_paused
    sta saved_pause
    lda #0
    sta mode
    sta s3b.error
    sta button_armed
    lda requested
    sta number
    jsr shots.p_disable
    jsr s3b2.prepare
    lda s3b.error
    bne !done+
    jsr pal.apply
    jsr v014_init_objects
    jsr shots.p_init
    lda number
    sta hud.player1_level
    lda #0
    sta hud.player1_level+1
    jsr game.c_reset
    lda saved_speed
    sta anim_speed
    lda saved_pause
    sta anim_paused
    ldx #24
!shadow:
    lda #$ff
    sta $1a20,x
    dex
    bpl !shadow-
    jsr hud.hud_draw_static
    jsr getready.gr_begin
    jsr hud.hud_render
!done:
    rts
restart:
    jsr bonus_reset
    jsr audio8.restart
    // Existing R semantics: highscore preserved; score/lives/defaults reset.
    ldx #24
!defaults:
    cpx #4
    bcc !skip+
    lda hud.defaults,x
    sta $1a00,x
!skip:
    dex
    bpl !defaults-
    lda #6
    sta anim_speed
    lda #0
    sta anim_paused
    lda #1
    jsr transition
    inc getready.gr_skip // R arrived after this frame's wait already completed
    rts

key_filter:
    lda offscreen.r_keybyte
    cmp #$58
    beq !pass+
    lda mode
    bne !consume+
    lda attack_allowed
    bne !normal_key+
    lda offscreen.r_keybyte
    cmp #$54
    beq !consume+
    cmp #$45
    beq !consume+
!normal_key:
    lda game.c_ps
    cmp #4
    beq !pass+
    lda offscreen.r_keybyte
    cmp #$2b
    beq !plus+
    cmp #$2d
    beq !minus+
    lda $d614
    pha
    lda #5
    sta $d614
    lda $d613
    and #9 // matrix row5: + bit0, - bit3
    tax
    pla
    sta $d614
    cpx #9
    bne !pass+
    lda #0
    sta nav_latch
!pass:
    clc
    rts
!plus:
    lda nav_latch
    bne !consume+
    inc nav_latch
    lda number
    cmp #100
    beq !consume+
    clc
    adc #1
    jsr transition
    inc getready.gr_skip
    jmp !consume+
!minus:
    lda nav_latch
    bne !consume+
    inc nav_latch
    lda number
    cmp #1
    beq !consume+
    sec
    sbc #1
    jsr transition
    inc getready.gr_skip
!consume:
    sec
    rts
move:
    lda mode
    bne !done+
    jmp offscreen.r_move
!done:
    rts
objects:
    lda mode
    bne !done+
    jmp offscreen.r_objects
!done:
    rts

tick:
    lda mode
    cmp #3
    bne !transition+
    jmp getready.gr_tick
!transition:
    cmp #2
    bne !normal+
    jmp transitionfx.tick
!normal:
    jsr entry.e_error_check
    lda mode
    beq !play+
    rts
!play:
    jmp offscreen.r_tick

// Tail of game.c_tick after timer update and GAME OVER guard. No stack surgery.
continue_combat:
    jsr try_complete
    bcc !continue+
    rts
!continue:
    jsr game.c_formula
    jmp game.c_tick_attack_test

// Called immediately after explosion timers, before projectile/fire/collision work.
try_complete:
    lda mode
    bne !not_complete+
    lda offscreen.r_enabled
    bne !not_complete+
    lda game.c_ps
    cmp #1
    beq !not_complete+
    cmp #2
    beq !not_complete+
    cmp #4
    beq !not_complete+
    ldx #22 // includes every allocated enemy; unused slots are DEAD
!alive:
    lda game.c_es,x
    bne !not_complete+
    dex
    bpl !alive-
    // All assigned WAIT_ENTRY slots and every EXPLOSION must be DEAD.
    // Claim the completion before cleanup/award; mode2 makes it one-shot.
    lda #2
    sta mode
    jsr bonus_completed
    jsr hud.hud_render
    jsr transitionfx.begin
    sec
    rts
!not_complete:
    clc
    rts

bonus_reset:
    lda #0
    sta bonus_progress
    sta bonus_progress+1
    rts
bonus_completed:
    ldx twop.active
    inc bonus_progress,x
    lda bonus_progress,x
    cmp #3
    bcc !done+
    lda #0
    sta bonus_progress,x
    lda hud.player1_lives+1
    bne !done+ // never wrap an unexpected wider legacy count
    lda hud.player1_lives
    beq !done+ // never resurrect GAME OVER
    cmp #BONUS_MAX_LIVES
    bcs !done+
    inc hud.player1_lives
!done:
    rts

}
.if (* > $6700) { .error "Stage5a manager overlaps loader buffers" }

*=$6700 "Stage5a immutable blank guarded cache template"
.fill 256,0
.namespace level {
*=$3400 "Stage5a private graphics cache helpers"
clear_private:
    lda #0
    sta entry.e_dma_source
    sta entry.e_dma_dest
    sta entry.e_dma_length
    lda #$67
    sta entry.e_dma_source+1
    lda #0
    sta entry.e_dma_source+2
    lda #1
    sta entry.e_dma_dest+2
    sta entry.e_dma_length+1
    lda #$40 // Private pool $14000-$155FF, outside DOS.
    sta entry.e_dma_dest+1
!slot:
    jsr entry.e_copy
    inc entry.e_dma_dest+1
    lda entry.e_dma_dest+1
    cmp #$56
    bne !slot-
    rts
full_frame:
    jsr enemy_frame
    lda #$40
    sta entry.e_dma_source
    lda #$98
    sta entry.e_dma_source+1
    ldx entry.e_slot
    lda game.c_es,x
    cmp #4
    bne !copy+
    lda game.c_ef,x
    clc
    adc #$c1
    sta entry.e_dma_source+1
!copy:
    lda #0
    sta entry.e_dma_source+2
    sta entry.e_dma_length+1
    lda #128
    sta entry.e_dma_length
    lda #$40
    sta entry.e_dma_dest
    lda entry.e_slot
    ora #$40 // Bank1 private pool page, preserve slot indexing.
    sta entry.e_dma_dest+1
    lda #1
    sta entry.e_dma_dest+2
    jsr entry.e_copy
    jmp entry.e_private_glyph
}
.if (* > $3600) { .error "Stage5a cache helpers overlap approved Player source" }

.namespace level {
.label crop_left=$1d9c
.label crop_low=$1d9d
*=$34a0 "Stage5a byte-pair crop (same pixels, no RRB architecture change)"
fast_crop:
    // Clear all guarded glyph bytes through physical DMA, safe with ROMC.
    lda #0
    sta entry.e_dma_source
    sta entry.e_dma_dest
    sta entry.e_dma_length
    sta entry.e_dma_source+2
    sta entry.e_dma_dest+2
    lda #$67
    sta entry.e_dma_source+1
    lda #$ca
    sta entry.e_dma_dest+1
    lda #1
    sta entry.e_dma_length+1
    jsr entry.e_copy
    lda #0
    sta offscreen.r_row
!row:
    lda offscreen.r_row
    clc
    adc offscreen.r_src_y
    asl
    asl
    asl
    sta offscreen.r_source
    lda offscreen.r_src_x
    lsr
    clc
    adc offscreen.r_source
    tay
    lda offscreen.r_row
    asl
    asl
    asl
    tax
    lda offscreen.r_width
    sta crop_left
!pair:
    lda $5640,y
    sta crop_low
    lda offscreen.r_src_x
    and #1
    bne !odd+
    lda crop_left
    cmp #1
    bne !even_byte+
    lda crop_low
    and #15
    sta crop_low
!even_byte:
    iny
    lda crop_low
    jmp !write+
!odd:
    lda crop_low
    lsr
    lsr
    lsr
    lsr
    sta crop_low
    lda crop_left
    cmp #1
    beq !single_odd+
    iny
    lda $5640,y
    and #15
    asl
    asl
    asl
    asl
    ora crop_low
    jmp !write+
!single_odd:
    lda crop_low
!write:
    sta $ca40,x
    inx
    lda crop_left
    cmp #3
    bcc !row_done+
    sec
    sbc #2
    sta crop_left
    jmp !pair-
!row_done:
    inc offscreen.r_row
    lda offscreen.r_row
    cmp offscreen.r_height
    beq !done_crop+
    jmp !row-
!done_crop:
    rts
}
.if (* > $3600) { .error "Stage5a byte crop overlaps approved Player source" }
