*=$5100 "Native KERNAL SEQ and recoverable disk transaction"
hi_set_filename:
    sta hi_file_ptr
    sty hi_file_ptr+1
    sta hi_name_read+1
    sty hi_name_read+2
    ldx #0
!length:
hi_name_read:
    lda $ffff,x
    bne !long_skip+
    jmp !done+
!long_skip:
    inx
    beq !long_skip+
    jmp !length-
!long_skip:
!done:
    stx hi_file_len
    rts
hi_open:
    lda hi_lfn
    ldx hi_device
    ldy hi_secondary
    jsr $ffba
    lda #0
    ldx #0
    jsr $ff6b // SETBNK bank0 BEFORE every SETNAM, also command channel.
    lda hi_file_len
    ldx hi_file_ptr
    ldy hi_file_ptr+1
    jsr $ffbd
    jmp $ffc0
hi_close_file:
    jsr $ffcc
    lda #2
    clc // normal disk close: flush data and send DOS CLOSE for secondary2
    jsr $ffc3
    bcc !done+
    lda hi_error
    bne !done+
    lda #2
    sta hi_error
!done:
    jmp $ffcc // KERNAL contract: reset current channels after CLOSE as well
hi_read_named:
    php
    cli
    jsr hi_set_filename
    lda #0
    sta hi_error
    lda #2
    sta hi_lfn
    sta hi_secondary
    jsr hi_open
    bcs !long_skip+
    jmp !opened+
!long_skip:
    lda #1
    sta hi_error
!opened:
    jsr hi_status
    lda hi_error
    beq !long_skip+
    jmp !close+
!long_skip:
    lda hi_dos
    beq !long_skip+
    jmp !dos_bad+
!long_skip:
    ldx #2
    jsr $ffc6
    bcs !long_skip+
    jmp !read_init+
!long_skip:
    lda #2
    sta hi_error
    beq !long_skip+
    jmp !close+
!long_skip:
!dos_bad:
    lda #2
    sta hi_error
    beq !long_skip+
    jmp !close+
!long_skip:
!read_init:
    lda #<hi_io
    sta hi_read_store+1
    lda #>hi_io
    sta hi_read_store+2
    lda #<592
    sta hi_left
    lda #>592
    sta hi_left+1
!byte:
    jsr $ffcf
    sta hi_io_byte
    jsr $ffb7
    sta hi_io_status
    and #$bf
    beq !long_skip+
    jmp !bad+
!long_skip:
    lda hi_io_byte
hi_read_store:
    sta hi_io
    inc hi_read_store+1
    beq !long_skip+
    jmp !pointer+
!long_skip:
    inc hi_read_store+2
!pointer:
    lda hi_left
    beq !long_skip+
    jmp !low+
!long_skip:
    dec hi_left+1
!low:
    dec hi_left
    lda hi_left
    ora hi_left+1
    bne !long_skip+
    jmp !last+
!long_skip:
    lda hi_io_status
    and #$40
    bne !long_skip+
    jmp !byte-
!long_skip:
    beq !long_skip+
    jmp !bad+
!long_skip:
!last:
    lda hi_io_status
    and #$40
    beq !long_skip+
    jmp !close+
!long_skip:
!bad:
    lda #3
    sta hi_error
!close:
    jsr hi_close_file
    plp
    rts
hi_status:
    lda #0
    sta hi_file_len
    jmp hi_status_open
hi_command:
    jsr hi_set_filename
    lda #0
    sta hi_error
hi_status_open:
    lda #15
    sta hi_lfn
    sta hi_secondary
    jsr hi_open
    bcc !long_skip+
    jmp hi_status_bad
!long_skip:
    ldx #15
    jsr $ffc6
    bcc !long_skip+
    jmp hi_status_bad
!long_skip:
    jsr $ffcf
    sec
    sbc #48
    cmp #10
    bcc !long_skip+
    jmp hi_status_bad
!long_skip:
    sta hi_cmd_code
    asl
    asl
    clc
    adc hi_cmd_code
    asl
    sta hi_cmd_code
    jsr $ffcf
    sec
    sbc #48
    cmp #10
    bcc !long_skip+
    jmp hi_status_bad
!long_skip:
    clc
    adc hi_cmd_code
    sta hi_dos
    lda #80
    sta hi_cmd_budget
!drain:
    jsr $ffcf
    cmp #13
    bne !long_skip+
    jmp hi_status_close
!long_skip:
    jsr $ffb7
    and #$bf
    beq !long_skip+
    jmp hi_status_bad
!long_skip:
    dec hi_cmd_budget
    beq !long_skip+
    jmp !drain-
!long_skip:
hi_status_bad:
    lda #255
    sta hi_dos
    lda #2
    sta hi_error
hi_status_close:
    jsr $ffcc
    lda #15
    sec // MEGA65 CLOSE15: retire logical channel without closing other DOS files
    jsr $ffc3
    bcc !done+
    lda hi_error
    bne !done+
    lda #2
    sta hi_error
!done:
    jmp $ffcc
hi_scratch:
    jsr hi_command
    lda hi_error
    beq !long_skip+
    jmp !done+
!long_skip:
    lda hi_dos
    bne !long_skip+
    jmp !done+
!long_skip:
    cmp #1
    bne !long_skip+
    jmp !done+
!long_skip:
    cmp #62
    bne !long_skip+
    jmp !done+
!long_skip:
    lda #2
    sta hi_error
!done:
    rts
hi_rename:
    jsr hi_command
    lda hi_error
    beq !long_skip+
    jmp !done+
!long_skip:
    lda hi_dos
    bne !long_skip+
    jmp !done+
!long_skip:
    lda #2
    sta hi_error
!done:
    rts
hi_write_temp:
    lda #<hi_tmp_write
    ldy #>hi_tmp_write
    jsr hi_set_filename
    lda #0
    sta hi_error
    lda #2
    sta hi_lfn
    sta hi_secondary
    jsr hi_open
    bcs !long_skip+
    jmp !opened+
!long_skip:
    lda #1
    sta hi_error
!opened:
    jsr hi_status
    lda hi_error
    beq !long_skip+
    jmp !close+
!long_skip:
    lda hi_dos
    beq !long_skip+
    jmp !bad+
!long_skip:
    ldx #2
    jsr $ffc9 // CHKOUT
    bcc !long_skip+
    jmp !bad+
!long_skip:
    lda #<hi_table
    sta hi_write_load+1
    lda #>hi_table
    sta hi_write_load+2
    lda #<592
    sta hi_left
    lda #>592
    sta hi_left+1
!byte:
hi_write_load:
    lda hi_table
    jsr $ffd2 // CHROUT only while output file2 selected; never screen text.
    bcc !written+
    jmp !bad+
!written:
    jsr $ffb7
    and #$bf // EOF belongs to input/status reads, not to an output error
    beq !long_skip+
    jmp !bad+
!long_skip:
    inc hi_write_load+1
    beq !long_skip+
    jmp !pointer+
!long_skip:
    inc hi_write_load+2
!pointer:
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
    jsr hi_close_file // flush before DOS-status check and readback
    jsr hi_status
    lda hi_dos
    bne !long_skip+
    jmp !done+
!long_skip:
!bad:
    lda #4
    sta hi_error
!close:
    lda hi_dos
    pha
    jsr hi_close_file
    lda hi_error
    pha
    jsr hi_status
    pla
    sta hi_error
    pla
    beq !keep_new_dos+
    sta hi_dos
!keep_new_dos:
!done:
    rts
hi_disk_save:
    lda #0
    sta hi_stage
    jsr hi_write_temp
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    lda #<hi_tmp_read
    ldy #>hi_tmp_read
    jsr hi_read_named
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    jsr hi_validate
    bcc !long_skip+
    jmp hi_save_verify_bad
!long_skip:
    jsr hi_compare_table
    bcc !long_skip+
    jmp hi_save_verify_bad
!long_skip:
    lda hi_present
    bne !long_skip+
    jmp !promote+
!long_skip:
    // Check the old authoritative file against the pre-insertion snapshot
    // before retiring any backup. Concurrent/external edits cause safe refusal.
    lda #<hi_filename
    ldy #>hi_filename
    jsr hi_read_named
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    jsr hi_validate
    bcc !long_skip+
    jmp hi_save_verify_bad
!long_skip:
    jsr hi_compare_backup
    bcc !long_skip+
    jmp hi_save_verify_bad
!long_skip:
    lda #<hi_scratch_bak
    ldy #>hi_scratch_bak
    jsr hi_scratch
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    lda #<hi_rename_bak
    ldy #>hi_rename_bak
    jsr hi_rename
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    lda #1
    sta hi_stage
!promote:
    lda #<hi_rename_dat
    ldy #>hi_rename_dat
    jsr hi_rename
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    lda #<hi_filename
    ldy #>hi_filename
    jsr hi_read_named
    lda hi_error
    beq !long_skip+
    jmp hi_save_done
!long_skip:
    jsr hi_validate
    bcc !long_skip+
    jmp hi_save_verify_bad
!long_skip:
    jsr hi_compare_table
    bcc !long_skip+
    jmp hi_save_verify_bad
!long_skip:
    lda #1
    sta hi_present
    rts
hi_save_verify_bad:
    lda #5
    sta hi_error
hi_save_done:
    rts
.if (*>$6000) { .error "Disk code overlaps colour plane" }

.if (*>$5500) { .error "Disk code overlaps score text cache" }
*=$5500 "Nonpersistent decimal score cache"
hi_cache_ascii: .fill 800,32
