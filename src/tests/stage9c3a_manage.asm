*=$8800 "Highscore management, validation and input"
hi_boot:
    lda $ba
    cmp #8
    bcc !long_skip+
    jmp !device+
!long_skip:
    lda #8
!device:
    sta hi_device
    lda #0
    sta hi_blocked
    sta hi_present
    sta hi_recovered
    sta hi_mode
    lda #<hi_filename
    ldy #>hi_filename
    jsr hi_read_named
    lda hi_error
    beq !long_skip+
    jmp !fallback+
!long_skip:
    jsr hi_validate
    bcc !long_skip+
    jmp !bad+
!long_skip:
    jsr hi_io_to_table
    lda #1
    sta hi_present
    sta hi_recovered
    ldx #<hi_msg_ready
    ldy #>hi_msg_ready
    jmp hi_message
!bad:
    lda #1
    sta hi_blocked
!fallback:
    lda hi_dos
    cmp #62
    bne !long_skip+
    jmp !backup+
!long_skip:
    lda #1
    sta hi_blocked
!backup:
    lda #<hi_bak_read
    ldy #>hi_bak_read
    jsr hi_read_named
    lda hi_error
    beq !long_skip+
    jmp !empty+
!long_skip:
    jsr hi_validate
    bcc !long_skip+
    jmp !empty+
!long_skip:
    jsr hi_io_to_table
    lda #1
    sta hi_recovered
    sta hi_blocked // never replace a damaged/missing primary with silent recovery
    beq !long_skip+
    jmp !bad_message+
!long_skip:
!empty:
    lda hi_dos
    cmp #62
    bne !long_skip+
    jmp !init+
!long_skip:
    lda #1
    sta hi_blocked
!init:
    jsr hi_empty
    lda hi_blocked
    beq !long_skip+
    jmp !bad_message+
!long_skip:
    ldx #<hi_msg_missing
    ldy #>hi_msg_missing
    jmp hi_message
!bad_message:
    ldx #<hi_msg_bad
    ldy #>hi_msg_bad
    jmp hi_message
hi_empty:
    lda #0
    ldx #0
!zero:
    sta hi_table,x
    sta hi_table+256,x
    inx
    beq !long_skip+
    jmp !zero-
!long_skip:
    ldx #79
!tail:
    sta hi_table+512,x
    dex
    bmi !long_skip+
    jmp !tail-
!long_skip:
    ldx #6
!magic:
    lda hi_magic,x
    sta hi_table,x
    dex
    bmi !long_skip+
    jmp !magic-
!long_skip:
    jmp hi_seal
hi_message:
    stx hi_status_lo
    sty hi_status_hi
    lda #1
    sta page_dirty
    rts
hi_release:
    lda #0
    sta $d614
    lda $d613
    and #2
    bne !long_skip+
    jmp !done+
!long_skip:
    lda #0
    sta hi_return_lock
!done:
    rts
hi_key:
    cmp #$c1 // PETSCII shifted uppercase letters normalize to stored ASCII
    bcc !ascii+
    cmp #$db
    bcs !ascii+
    and #$7f
!ascii:
    sta hi_key_byte
    cmp #13
    beq !long_skip+
    jmp !mode+
!long_skip:
    lda hi_return_lock
    bne !long_skip+
    jmp !mode+
!long_skip:
    clc
    rts
!mode:
    lda hi_mode
    beq !long_skip+
    jmp hi_edit_key
!long_skip:
    lda hi_key_byte
    cmp #$53
    bne !long_skip+
    jmp !simulate+
!long_skip:
    cmp #$73
    bne !long_skip+
    jmp !simulate+
!long_skip:
    sec
    rts
!simulate:
    lda #0
    sta fire_armed
    lda hi_blocked
    bne !long_skip+
    jmp !start+
!long_skip:
    lda #3
    sta hi_mode
    ldx #<hi_msg_readonly
    ldy #>hi_msg_readonly
    jsr hi_message
    clc
    rts
!start:
    lda #1
    sta hi_mode
    lda #0
    sta hi_len
    sta hi_name_len
    ldx #3
!score:
    sta hi_score,x
    dex
    bmi !long_skip+
    jmp !score-
!long_skip:
    ldx #<hi_msg_score
    ldy #>hi_msg_score
    jsr hi_message
    clc
    rts
hi_edit_key:
    cmp #3
    beq !long_skip+
    jmp !edit+
!long_skip:
    lda hi_key_byte
    cmp #$58
    bne !long_skip+
    jmp !exit+
!long_skip:
    cmp #$78
    bne !long_skip+
    jmp !exit+
!long_skip:
    cmp #13
    bne !long_skip+
    jmp hi_cancel
!long_skip:
    cmp #27
    bne !long_skip+
    jmp hi_cancel
!long_skip:
    clc
    rts
!exit:
    lda #1
    sta quit
    clc
    rts
!edit:
    lda hi_key_byte
    cmp #27
    bne !long_skip+
    jmp hi_cancel
!long_skip:
    cmp #13
    beq !long_skip+
    jmp !delete+
!long_skip:
    jmp hi_confirm
!delete:
    cmp #20
    bne !long_skip+
    jmp hi_delete
!long_skip:
    cmp #8
    bne !long_skip+
    jmp hi_delete
!long_skip:
    lda hi_mode
    cmp #1
    beq !long_skip+
    jmp hi_name_key
!long_skip:
    lda hi_key_byte
    cmp #48
    bcs !long_skip+
    jmp hi_invalid_input
!long_skip:
    cmp #58
    bcc !long_skip+
    jmp hi_invalid_input
!long_skip:
    ldx hi_len
    cpx #10
    bcc !long_skip+
    jmp hi_invalid_input
!long_skip:
    sta hi_digits,x
    inc hi_len
    jsr hi_parse
    bcs !long_skip+
    jmp !ok+
!long_skip:
    dec hi_len
    jmp hi_invalid_input
!ok:
    ldx #<hi_msg_score
    ldy #>hi_msg_score
    jsr hi_message
    clc
    rts
hi_cancel:
    lda #0
    sta hi_mode
    sta fire_armed
    ldx #<hi_msg_ready
    ldy #>hi_msg_ready
    jsr hi_message
    clc
    rts
hi_delete:
    lda hi_mode
    cmp #1
    beq !long_skip+
    jmp !name+
!long_skip:
    lda hi_len
    bne !long_skip+
    jmp !done+
!long_skip:
    dec hi_len
    jsr hi_parse
    jmp !done+
!name:
    lda hi_name_len
    bne !long_skip+
    jmp !done+
!long_skip:
    dec hi_name_len
!done:
    lda #1
    sta page_dirty
    clc
    rts
hi_name_key:
    lda hi_key_byte
    cmp #$61
    bcs !long_skip+
    jmp !upper+
!long_skip:
    cmp #$7b
    bcc !long_skip+
    jmp !upper+
!long_skip:
    and #$df
!upper:
    pha
    jsr hi_allowed
    pla
    bcs !long_skip+
    jmp hi_invalid_input
!long_skip:
    ldx hi_name_len
    cpx #3
    bcc !long_skip+
    jmp hi_invalid_input
!long_skip:
    sta hi_name,x
    inc hi_name_len
    lda #1
    sta page_dirty
    clc
    rts
hi_invalid_input:
    ldx #<hi_msg_input
    ldy #>hi_msg_input
    jsr hi_message
    clc
    rts
hi_confirm:
    lda #1
    sta hi_return_lock
    lda hi_mode
    cmp #2
    bne !long_skip+
    jmp !name+
!long_skip:
    lda hi_len
    bne !long_skip+
    jmp hi_invalid_input
!long_skip:
    jsr hi_qualify
    lda hi_rank
    cmp #80
    bcs !long_skip+
    jmp !qualified+
!long_skip:
    lda #3
    sta hi_mode
    ldx #<hi_msg_reject
    ldy #>hi_msg_reject
    jsr hi_message
    clc
    rts
!qualified:
    lda #2
    sta hi_mode
    lda #0
    sta hi_name_len
    ldx #<hi_msg_name
    ldy #>hi_msg_name
    jsr hi_message
    clc
    rts
!name:
    lda hi_name_len
    cmp #3
    beq !long_skip+
    jmp hi_invalid_input
!long_skip:
    jsr hi_commit
    clc
    rts
hi_allowed:
    ldx #0
!char:
    cmp hi_alphabet,x
    bne !long_skip+
    jmp !yes+
!long_skip:
    inx
    ldy hi_alphabet,x
    beq !long_skip+
    jmp !char-
!long_skip:
    clc
    rts
!yes:
    sec
    rts
hi_parse:
    lda #0
    ldx #3
!clear:
    sta hi_work,x
    dex
    bmi !long_skip+
    jmp !clear-
!long_skip:
    sta hi_col
!digit:
    lda hi_col
    cmp hi_len
    bne !long_skip+
    jmp !success+
!long_skip:
    ldx #3
!old:
    lda hi_work,x
    sta hi_old,x
    lda #0
    sta hi_work,x
    dex
    bmi !long_skip+
    jmp !old-
!long_skip:
    lda #10
    sta hi_count
!multiply:
    clc
    ldx #0
    ldy #4
!add:
    lda hi_work,x
    adc hi_old,x
    sta hi_work,x
    inx
    dey
    beq !long_skip+
    jmp !add-
!long_skip:
    bcc !long_skip+
    jmp !overflow+
!long_skip:
    dec hi_count
    beq !long_skip+
    jmp !multiply-
!long_skip:
    ldx hi_col
    lda hi_digits,x
    sec
    sbc #48
    clc
    adc hi_work
    sta hi_work
    ldx #1
    ldy #3
!carry:
    lda hi_work,x
    adc #0
    sta hi_work,x
    inx
    dey
    beq !long_skip+
    jmp !carry-
!long_skip:
    bcc !long_skip+
    jmp !overflow+
!long_skip:
    inc hi_col
    jmp !digit-
!success:
    ldx #3
!copy:
    lda hi_work,x
    sta hi_score,x
    dex
    bmi !long_skip+
    jmp !copy-
!long_skip:
    clc
    rts
!overflow:
    sec
    rts
hi_record:
    lda hi_rec_lo,x
    sta hi_get+1
    sta hi_put+1
    lda hi_rec_hi,x
    sta hi_get+2
    sta hi_put+2
    rts
hi_io_record:
    jsr hi_record
    lda hi_get+2
    clc
    adc #6
    sta hi_get+2
    rts
hi_get:
    lda $ffff,y
    rts
hi_put:
    sta $ffff,y
    rts
hi_qualify:
    lda #0
    sta hi_rank
!slot:
    lda hi_rank
    cmp hi_table+7
    bne !long_skip+
    jmp !done+
!long_skip:
    tax
    jsr hi_record
    ldy #6
    ldx #3
!compare:
    jsr hi_get
    sta hi_io_byte
    lda hi_score,x
    cmp hi_io_byte
    bcs !long_skip+
    jmp !next+
!long_skip:
    beq !long_skip+
    jmp !done+
!long_skip:
    dey
    dex
    bmi !long_skip+
    jmp !compare-
!long_skip:
    rts // equality: first equal position, not after the existing tie group
!next:
    inc hi_rank
    jmp !slot-
!done:
    rts
hi_insert:
    jsr hi_qualify
    lda hi_rank
    cmp #80
    bcc !long_skip+
    jmp !done+
!long_skip:
    lda hi_table+7
    cmp #80
    bcs !long_skip+
    jmp !target+
!long_skip:
    lda #79
!target:
    sta hi_slot
!shift:
    lda hi_slot
    cmp hi_rank
    bne !long_skip+
    jmp !write+
!long_skip:
    tax
    dex
    jsr hi_record
    ldy #6
!read:
    jsr hi_get
    sta hi_shift,y
    dey
    bmi !long_skip+
    jmp !read-
!long_skip:
    ldx hi_slot
    jsr hi_record
    ldy #6
!put:
    lda hi_shift,y
    jsr hi_put
    dey
    bmi !long_skip+
    jmp !put-
!long_skip:
    dec hi_slot
    jmp !shift-
!write:
    ldx hi_rank
    jsr hi_record
    ldy #0
!name:
    lda hi_name,y
    jsr hi_put
    iny
    cpy #3
    beq !long_skip+
    jmp !name-
!long_skip:
    ldx #0
!score:
    lda hi_score,x
    jsr hi_put
    iny
    inx
    cpx #4
    beq !long_skip+
    jmp !score-
!long_skip:
    lda hi_table+7
    cmp #80
    bcc !long_skip+
    jmp !done+
!long_skip:
    inc hi_table+7
!done:
    rts
hi_commit:
    lda hi_blocked
    beq !long_skip+
    jmp !blocked+
!long_skip:
    jsr hi_qualify
    lda hi_rank
    cmp #80
    bcc !qualifies+
    lda #3
    sta hi_mode
    ldx #<hi_msg_reject
    ldy #>hi_msg_reject
    jmp hi_message
!qualifies:
    jsr hi_table_to_backup
    jsr hi_insert
    jsr hi_seal
    jsr hi_suspend
    jsr hi_disk_save
    lda hi_error
    pha
    jsr hi_resume
    pla
    beq !long_skip+
    jmp !failed+
!long_skip:
    lda hi_rank
    ldx #0
!page:
    cmp #20
    bcs !long_skip+
    jmp !page_done+
!long_skip:
    sbc #20
    inx
    beq !long_skip+
    jmp !page-
!long_skip:
!page_done:
    stx page
    ldx #<hi_msg_saved
    ldy #>hi_msg_saved
    jmp !message+
!failed:
    jsr hi_backup_to_table
    lda #1
    sta hi_blocked
    ldx #<hi_msg_failed
    ldy #>hi_msg_failed
    jmp !message+
!blocked:
    ldx #<hi_msg_readonly
    ldy #>hi_msg_readonly
!message:
    txa
    pha
    tya
    pha
    jsr hi_cache_scores
    pla
    tay
    pla
    tax
    lda #0
    sta hi_mode
    sta fire_armed
    jsr hi_message
    rts
hi_suspend:
    jsr title_restore_video
    lda saved_column
    sta $d614
    lda saved_ddra
    sta $dc02
    cli // Native BASIC/ROM mapping, no open channels during video restoration.
    rts
hi_resume:
    sei
    cld
    jsr title_save_video
    lda saved_ddra
    and #$e0
    sta $dc02
    jsr flush_keys
    jsr title_show
    jsr cc_publish // retain cycle phase and band phase across disk access
    lda #0
    sta frame_pending
    rts
hi_seal:
    jsr hi_table_to_io
    jsr hi_crc16
    lda hi_crc
    sta hi_io+8
    lda hi_crc+1
    sta hi_io+9
    jmp hi_io_to_table
hi_crc16:
    lda #$ff
    sta hi_crc
    sta hi_crc+1
    lda #<hi_io
    sta hi_crc_read+1
    lda #>hi_io
    sta hi_crc_read+2
!byte:
    lda hi_crc_read+2
    cmp #>hi_io
    beq !long_skip+
    jmp !feed+
!long_skip:
    lda hi_crc_read+1
    cmp #8
    bne !long_skip+
    jmp !advance+
!long_skip:
    cmp #9
    bne !long_skip+
    jmp !advance+
!long_skip:
!feed:
hi_crc_read:
    lda hi_io
    eor hi_crc+1
    sta hi_crc+1
    ldy #8
!bit:
    asl hi_crc
    rol hi_crc+1
    bcs !long_skip+
    jmp !next+
!long_skip:
    lda hi_crc
    eor #$21
    sta hi_crc
    lda hi_crc+1
    eor #$10
    sta hi_crc+1
!next:
    dey
    beq !long_skip+
    jmp !bit-
!long_skip:
!advance:
    inc hi_crc_read+1
    beq !long_skip+
    jmp !end+
!long_skip:
    inc hi_crc_read+2
!end:
    lda hi_crc_read+2
    cmp #>(hi_io+592)
    beq !long_skip+
    jmp !byte-
!long_skip:
    lda hi_crc_read+1
    cmp #<(hi_io+592)
    beq !long_skip+
    jmp !byte-
!long_skip:
    rts
hi_validate:
    ldx #6
!magic:
    lda hi_io,x
    cmp hi_magic,x
    beq !long_skip+
    jmp hi_validate_bad
!long_skip:
    dex
    bmi !long_skip+
    jmp !magic-
!long_skip:
    lda hi_io+7
    cmp #81
    bcc !long_skip+
    jmp hi_validate_bad
!long_skip:
    ldx #31
!reserved:
    lda hi_io,x
    beq !long_skip+
    jmp hi_validate_bad
!long_skip:
    dex
    cpx #9
    beq !long_skip+
    jmp !reserved-
!long_skip:
    jsr hi_crc16
    lda hi_crc
    cmp hi_io+8
    beq !long_skip+
    jmp hi_validate_bad
!long_skip:
    lda hi_crc+1
    cmp hi_io+9
    beq !long_skip+
    jmp hi_validate_bad
!long_skip:
    lda #$ff
    ldx #3
!previous:
    sta hi_previous,x
    dex
    bmi !long_skip+
    jmp !previous-
!long_skip:
    lda #0
    sta hi_slot
!record:
    ldx hi_slot
    jsr hi_io_record
    cpx hi_io+7
    bcc !long_skip+
    jmp !empty+
!long_skip:
    lda #0
    sta hi_col
!name:
    ldy hi_col
    jsr hi_get
    jsr hi_allowed
    bcs !long_skip+
    jmp hi_validate_bad
!long_skip:
    inc hi_col
    lda hi_col
    cmp #3
    beq !long_skip+
    jmp !name-
!long_skip:
    ldx #3
    ldy #6
!order:
    jsr hi_get
    cmp hi_previous,x
    bcs !long_skip+
    jmp !ordered+
!long_skip:
    beq !long_skip+
    jmp hi_validate_bad
!long_skip:
    dey
    dex
    bmi !long_skip+
    jmp !order-
!long_skip:
!ordered:
    ldy #3
    ldx #0
!remember:
    jsr hi_get
    sta hi_previous,x
    iny
    inx
    cpx #4
    beq !long_skip+
    jmp !remember-
!long_skip:
    jmp !next+
!empty:
    ldy #6
!zero:
    jsr hi_get
    beq !long_skip+
    jmp hi_validate_bad
!long_skip:
    dey
    bmi !long_skip+
    jmp !zero-
!long_skip:
!next:
    inc hi_slot
    lda hi_slot
    cmp #80
    beq !long_skip+
    jmp !record-
!long_skip:
    clc
    rts
hi_validate_bad:
    sec
    rts
// Fixed packet copies never touch DOS/ROM memory or zero page.
hi_table_to_io:
.for (var off=0;off<592;off+=256) {
    ldx #0
!copy:
    lda hi_table+off,x
    sta hi_io+off,x
    inx
    .if (off==512) { cpx #80 }
    beq !long_skip+
    jmp !copy-
!long_skip:
}
    rts
hi_io_to_table:
.for (var off=0;off<592;off+=256) {
    ldx #0
!copy:
    lda hi_io+off,x
    sta hi_table+off,x
    inx
    .if (off==512) { cpx #80 }
    beq !long_skip+
    jmp !copy-
!long_skip:
}
    rts
hi_table_to_backup:
.for (var off=0;off<592;off+=256) {
    ldx #0
!copy:
    lda hi_table+off,x
    sta hi_backup+off,x
    inx
    .if (off==512) { cpx #80 }
    beq !long_skip+
    jmp !copy-
!long_skip:
}
    rts
hi_backup_to_table:
.for (var off=0;off<592;off+=256) {
    ldx #0
!copy:
    lda hi_backup+off,x
    sta hi_table+off,x
    inx
    .if (off==512) { cpx #80 }
    beq !long_skip+
    jmp !copy-
!long_skip:
}
    rts
hi_compare_table:
    lda #<hi_table
    ldy #>hi_table
    jmp hi_compare
hi_compare_backup:
    lda #<hi_backup
    ldy #>hi_backup
hi_compare:
    sta hi_cmp_read+1
    sty hi_cmp_read+2
    lda #<hi_io
    sta hi_cmp_io+1
    lda #>hi_io
    sta hi_cmp_io+2
    lda #<592
    sta hi_left
    lda #>592
    sta hi_left+1
!byte:
hi_cmp_read:
    lda hi_table
hi_cmp_io:
    cmp hi_io
    beq !long_skip+
    jmp !bad+
!long_skip:
    inc hi_cmp_read+1
    beq !long_skip+
    jmp !a+
!long_skip:
    inc hi_cmp_read+2
!a:
    inc hi_cmp_io+1
    beq !long_skip+
    jmp !b+
!long_skip:
    inc hi_cmp_io+2
!b:
    lda hi_left
    beq !long_skip+
    jmp !low+
!long_skip:
    dec hi_left+1
!low:
    dec hi_left
    lda hi_left
    ora hi_left+1
    beq !long_skip+
    jmp !byte-
!long_skip:
    clc
    rts
!bad:
    sec
    rts
.if (*>$a000) { .error "Highscore manager enters ROM" }
hi_render:
    lda page
    asl
    asl
    sta hi_display_rank
    asl
    asl
    clc
    adc hi_display_rank
    sta hi_display_rank
    lda #0
    sta hi_display_slot
!slot:
    ldx hi_display_slot
    lda hi_screen_lo,x
    ldy hi_screen_hi,x
    jsr hi_screen_set
    lda hi_display_rank
    clc
    adc #1
    ldx #48
!ten:
    cmp #10
    bcs !long_skip+
    jmp !rank+
!long_skip:
    sbc #10
    inx
    beq !long_skip+
    jmp !ten-
!long_skip:
!rank:
    pha
    txa
    jsr hi_char
    pla
    clc
    adc #48
    jsr hi_char
    lda #58
    jsr hi_char
    lda #32
    jsr hi_char
    lda hi_display_rank
    cmp hi_table+7
    bcc !long_skip+
    jmp !empty+
!long_skip:
    tax
    jsr hi_record
    ldy #0
!name:
    jsr hi_get
    jsr hi_char
    iny
    cpy #3
    beq !long_skip+
    jmp !name-
!long_skip:
    lda #32
    jsr hi_char
    ldx hi_display_rank
    lda hi_cache_lo,x
    sta hi_cache_read+1
    lda hi_cache_hi,x
    sta hi_cache_read+2
    ldy #0
!number:
hi_cache_read:
    lda hi_cache_ascii,y
    jsr hi_char
    iny
    cpy #10
    bne !number-
    jmp !next+
!empty:
    ldx #14
!dash:
    lda #45
    jsr hi_char
    dex
    beq !long_skip+
    jmp !dash-
!long_skip:
!next:
    inc hi_display_rank
    inc hi_display_slot
    lda hi_display_slot
    cmp #20
    bne !long_skip+
    jmp !ui+
!long_skip:
    jmp !slot-
!ui:
    lda #1
    ldx #67
!clear_cursor:
    sta band_buffer+19*80+6,x
    dex
    bpl !clear_cursor-
    lda hi_mode
    cmp #2
    beq !status+
    lda hi_blocked
    beq !view+
!status:
    lda #<($a000+17*80+6)
    ldy #>($a000+17*80+6)
    jsr hi_screen_set
    lda hi_status_lo
    ldy hi_status_hi
    jsr hi_string
!view:
    lda hi_mode
    cmp #2
    beq !edit_ui+
    lda hi_blocked
    bne !diagnostics+
    jmp !done+
!diagnostics:
    lda #<($a000+19*80+6)
    ldy #>($a000+19*80+6)
    jsr hi_screen_set
    lda #<hi_error_label
    ldy #>hi_error_label
    jsr hi_string
    lda hi_error
    jsr hi_u8_decimal
    lda #<hi_dos_label
    ldy #>hi_dos_label
    jsr hi_string
    lda hi_dos
    jsr hi_u8_decimal
    jmp !done+
!edit_ui:
    lda #<($a000+19*80+18)
    ldy #>($a000+19*80+18)
    jsr hi_screen_set
    lda hi_mode
    cmp #2
    bne !long_skip+
    jmp !name_ui+
!long_skip:
    lda #<hi_score_label
    ldy #>hi_score_label
    jsr hi_string
    ldy #0
!digit:
    cpy hi_len
    bcc !long_skip+
    jmp !blank+
!long_skip:
    lda hi_digits,y
    jmp !draw+
!blank:
    lda #45
!draw:
    jsr hi_char
    iny
    cpy #10
    beq !long_skip+
    jmp !digit-
!long_skip:
    jmp !bracket+
!name_ui:
    lda #<hi_name_label
    ldy #>hi_name_label
    jsr hi_string
    ldy #0
!name_char:
    cpy hi_name_len
    bcc !long_skip+
    jmp !missing+
!long_skip:
    lda hi_name,y
    jmp !letter+
!missing:
    lda #45
!letter:
    jsr hi_char
    iny
    cpy #3
    beq !long_skip+
    jmp !name_char-
!long_skip:
!bracket:
    lda #93
    jsr hi_char
    // Explicit position marker, independent of ROM cursor/IRQ state.
    lda #32
    jsr hi_char
    lda #40
    jsr hi_char
    lda hi_mode
    cmp #2
    beq !long_skip+
    jmp !score_len+
!long_skip:
    lda hi_name_len
    cmp #3
    bcc !name_position+
    lda #2
!name_position:
    tax
    pha
    lda #2
    sta band_buffer+19*80+24,x
    pla
    jmp !position+
!score_len:
    lda hi_len
    cmp #10
    bcs !long_skip+
    jmp !position+
!long_skip:
    lda #9
!position:
    clc
    adc #1
    cmp #10
    bne !single+
    lda #49
    jsr hi_char
    lda #48
    jmp !pos_emit+
!single:
    clc
    adc #48
!pos_emit:
    jsr hi_char
    lda #41
    jsr hi_char
!done:
    rts
hi_screen_set:
    sta hi_screen_write+1
    sty hi_screen_write+2
    rts
hi_char:
    cmp #64
    bcs !long_skip+
    jmp hi_screen_write
!long_skip:
    cmp #96
    bcc !long_skip+
    jmp hi_screen_write
!long_skip:
    sec
    sbc #64
hi_screen_write:
    sta $a000
    inc hi_screen_write+1
    beq !long_skip+
    jmp !done+
!long_skip:
    inc hi_screen_write+2
!done:
    rts
hi_string:
    sta hi_string_read+1
    sty hi_string_read+2
    ldx #0
!char:
hi_string_read:
    lda $ffff,x
    bne !long_skip+
    jmp !done+
!long_skip:
    jsr hi_char
    inx
    beq !long_skip+
    jmp !char-
!long_skip:
!done:
    rts
hi_format_number:
    lda #0
    sta hi_col
    sta hi_leading
!power:
    lda #0
    sta hi_digit_value
!subtract:
    lda hi_col
    asl
    asl
    clc
    adc #3
    tay
    ldx #3
!compare:
    lda hi_work,x
    cmp hi_powers,y
    bcs !long_skip+
    jmp !emit+
!long_skip:
    beq !long_skip+
    jmp !can+
!long_skip:
    dey
    dex
    bmi !long_skip+
    jmp !compare-
!long_skip:
!can:
    lda hi_col
    asl
    asl
    tay
    ldx #0
    lda #4
    sta hi_math_left
    sec
!sub:
    lda hi_work,x
    sbc hi_powers,y
    sta hi_work,x
    iny
    inx
    dec hi_math_left
    beq !long_skip+
    jmp !sub-
!long_skip:
    inc hi_digit_value
    jmp !subtract-
!emit:
    lda hi_digit_value
    beq !long_skip+
    jmp !nonzero+
!long_skip:
    lda hi_leading
    beq !long_skip+
    jmp !number+
!long_skip:
    lda hi_col
    cmp #9
    bne !long_skip+
    jmp !number+
!long_skip:
    lda #32
    beq !long_skip+
    jmp !store+
!long_skip:
!nonzero:
    lda #1
    sta hi_leading
!number:
    lda hi_digit_value
    clc
    adc #48
!store:
    ldx hi_col
    sta hi_number,x
    inc hi_col
    lda hi_col
    cmp #10
    beq !long_skip+
    jmp !power-
!long_skip:
    rts
.if (*>$a000) { .error "Highscore renderer enters ROM" }

hi_cache_scores:
    lda #0
    sta hi_cache_slot
!entry:
    lda hi_cache_slot
    cmp hi_table+7
    beq !done+
    tax
    jsr hi_record
    ldy #3
    ldx #0
!score:
    jsr hi_get
    sta hi_work,x
    iny
    inx
    cpx #4
    bne !score-
    jsr hi_format_number
    ldx hi_cache_slot
    lda hi_cache_lo,x
    sta hi_cache_write+1
    lda hi_cache_hi,x
    sta hi_cache_write+2
    ldy #9
!write:
    lda hi_number,y
hi_cache_write:
    sta hi_cache_ascii,y
    dey
    bpl !write-
    inc hi_cache_slot
    jmp !entry-
!done:
    rts
.if (*>$a000) { .error "Highscore cache generator enters ROM" }

hi_check_temp:
    lda hi_error
    sta hi_probe_error
    lda hi_dos
    sta hi_probe_dos
    lda #<hi_tmp_read
    ldy #>hi_tmp_read
    jsr hi_read_named
    lda hi_error
    beq !exists+
    lda hi_dos
    cmp #62
    bne !pending+
    lda hi_probe_error
    sta hi_error
    lda hi_probe_dos
    sta hi_dos
    rts
!exists:
    jsr hi_validate
    bcs !pending+
    lda hi_recovered
    bne !pending+
    jsr hi_io_to_table // valid temp is the last resort, but is never auto-promoted
!pending:
    lda #1
    sta hi_blocked
    ldx #<hi_msg_pending
    ldy #>hi_msg_pending
    jmp hi_message
.if (*>$a000) { .error "Temp recovery enters ROM" }

hi_u8_decimal:
    cmp #100
    bcc !normal+
    lda #63
    jsr hi_char
    jmp hi_char
!normal:
    ldx #48
!tens:
    cmp #10
    bcc !emit+
    sbc #10
    inx
    bne !tens-
!emit:
    pha
    txa
    jsr hi_char
    pla
    clc
    adc #48
    jmp hi_char
.if (*>$a000) { .error "Diagnostic formatter enters ROM" }
