// Stage5d-1: Stage5d0 Stable FCM renderer, lossless cache relocation and ordered VIC-IV handoff.
// Phase-shared $4000-$47FF becomes the unchanged game HUD charset later.
*=$4000 "Stage5d1 title bootstrap (then private HUD charset)"
.namespace splash {
.const T_SCREEN=$f300
.const T_CHECK=$6900
.const T_CELLS=1320
.const T_REG_COUNT=38
.const T_REG_D016=2
.const T_REG_D031=6
.const T_REG_D011=0
.const T_REG_D07A=30
.const T_REG_D05D=21
// Generated constants are before code: KickAssembler requires constant order.
.import source "title_layout.inc"
t_boot:
    php
    cli
    lda #0
    sta t_shown
    sta titlecache.tc_saved
    sta s3b.error
    sta s3b.total_crc
    sta s3b.total_crc+1
    lda #<t_filename
    sta s3b.name_ptr
    lda #>t_filename
    sta s3b.name_ptr+1
    lda #12
    sta s3b.name_len
    lda #<T_FILE_BYTES
    sta s3b.remain
    lda #>(T_FILE_BYTES & $ffff)
    sta s3b.remain+1
    lda #0
    sta s3b.remain+2
    sta s3b.target_hi
    lda #4
    sta s3b.target_bank
    jsr s3b.load_file
    lda s3b.error
    beq !loaded+
    plp
    rts
!loaded:
    lda s3b.total_crc
    cmp #<T_FILE_SUM
    bne !bad_sum+
    lda s3b.total_crc+1
    cmp #>T_FILE_SUM
    beq !sum_ok+
!bad_sum:
    lda #6
    sta s3b.error
    plp
    rts
!sum_ok:
    lda #0
    sta t_dma_src_mb
    sta t_dma_dst_mb
    sta t_dma_command
    sta t_dma_src_lo
    sta t_dma_src_hi
    sta t_dma_dst_bank
    sta t_dma_len_hi
    lda #4
    sta t_dma_src_bank
    lda #<T_CHECK
    sta t_dma_dst_lo
    lda #>T_CHECK
    sta t_dma_dst_hi
    lda #T_PREFIX_BYTES
    sta t_dma_len_lo
    jsr t_dma_copy
    ldx #T_PREFIX_BYTES-1
!prefix:
    lda T_CHECK,x
    cmp t_prefix,x
    bne !bad_prefix+
    dex
    bpl !prefix-
    sei
    jsr t_save_video
    // These dedicated descriptors never touch game record/pixie/DOS/ROM RAM.
    ldx #<t_tile_copy_0
    ldy #>t_tile_copy_0
    jsr t_transfer
    ldx #<t_tile_copy_1
    ldy #>t_tile_copy_1
    jsr t_transfer
    ldx #<t_tile_copy_2
    ldy #>t_tile_copy_2
    jsr t_transfer
    lda #0
    sta t_dma_src_mb
    sta t_dma_dst_mb
    sta t_dma_dst_bank
    lda #$7d // header26 + palette99 =125
    sta t_dma_src_lo
    lda #0
    sta t_dma_src_hi
    lda #4
    sta t_dma_src_bank
    lda #<T_SCREEN
    sta t_dma_dst_lo
    lda #>T_SCREEN
    sta t_dma_dst_hi
    lda #<T_CELLS*2
    sta t_dma_len_lo
    lda #>T_CELLS*2
    sta t_dma_len_hi
    jsr t_dma_copy
    jsr t_show
    lda #1
    sta t_shown
    plp // IRQ enabled again; cursor is paused, no KERNAL screen output.
    rts
!bad_prefix:
    lda #8
    sta s3b.error
    plp
    rts

t_check_game_headers:
    lda #0
    sta t_dma_command
    sta t_dma_src_mb
    sta t_dma_dst_mb
    sta t_dma_src_lo
    sta t_dma_src_hi
    sta t_dma_dst_bank
    sta t_dma_len_hi
    lda #4
    sta t_dma_src_bank
    lda #<T_CHECK
    sta t_dma_dst_lo
    lda #>T_CHECK
    sta t_dma_dst_hi
    lda #8
    sta t_dma_len_lo
    jsr t_dma_copy
    ldx #7
!level:
    lda T_CHECK,x
    cmp t_level_header,x
    bne !level_bad+
    dex
    bpl !level-
    lda #5
    sta t_dma_src_bank
    lda #$40
    sta t_dma_src_hi
    jsr t_dma_copy
    ldx #7
!graphics:
    lda T_CHECK,x
    cmp t_graphics_header,x
    bne !graphics_bad+
    dex
    bpl !graphics-
    rts
!level_bad:
    lda #<s3b.level_name
    sta s3b.name_ptr
    lda #>s3b.level_name
    sta s3b.name_ptr+1
    jmp t_bad_header
!graphics_bad:
    lda #<s3b.graphic_name
    sta s3b.name_ptr
    lda #>s3b.graphic_name
    sta s3b.name_ptr+1
t_bad_header:
    lda #5
    sta s3b.error
    rts

t_error:
    jsr t_restore_video // channels already closed; return to readable BASIC
    ldx #<s3b.error_msg
    ldy #>s3b.error_msg
    jsr s3b.puts
    lda s3b.error
    jsr s3b.hex
    ldx #<t_file_message
    ldy #>t_file_message
    jsr s3b.puts
    ldx s3b.name_ptr
    ldy s3b.name_ptr+1
    jsr s3b.puts
    lda #13
    jmp $ffd2

t_save_video:
    lda $1120 // ROM V920395 cursor-disable byte, documented by prior ROM tests
    sta t_saved_cursor
    lda #$ff
    sta $1120 // KERNAL IRQ continues for SEQ I/O; cursor cannot write into FCM.
    ldx #T_REG_COUNT-1
save_reg_loop:
    lda t_regs,x
    sta read_vic+1
read_vic:
    lda $d000
    sta t_saved_regs,x
    dex
    bpl save_reg_loop
    // D011 bit7 reads live raster, not IRQ compare. Reconstruct the saved
    // write value from D07A.RASCMP bit0, preserving actual IRQ target bit8.
    lda t_saved_regs+T_REG_D07A
    and #1
    lsr
    ror
    sta t_saved_compare_bit
    lda t_saved_regs+T_REG_D011
    and #$7f
    ora t_saved_compare_bit
    sta t_saved_regs+T_REG_D011
    lda #$40 // map palette bank1 only; do not select it for display yet
    sta $d070
    ldx #32
save_palette_loop:
    lda $d100,x
    sta t_saved_r,x
    lda $d200,x
    sta t_saved_g,x
    lda $d300,x
    sta t_saved_b,x
    dex
    bpl save_palette_loop
    // Backup own Color-RAM window $FF82000..$FF82A4F, never BASIC's window.
    lda #$ff
    sta t_dma_src_mb
    lda #0
    sta t_dma_dst_mb
    sta t_dma_src_lo
    sta t_dma_dst_lo
    lda #$20
    sta t_dma_src_hi
    lda #8
    sta t_dma_src_bank
    lda #$f1
    sta t_dma_dst_hi
    lda #5
    sta t_dma_dst_bank
    lda #<T_CELLS*2
    sta t_dma_len_lo
    lda #>T_CELLS*2
    sta t_dma_len_hi
    jmp t_dma_copy

t_show:
    lda $d05d
    and #$7f // HOTREG OFF before legacy writes; direct geometry follows.
    sta $d05d
    lda $d011
    and #$0f
    sta $d011 // DEN off; no ECM/BMM. Atomic setup only; SEQ phase runs with IRQ.
    lda #0
    sta $d015 // hardware sprites off, other sprite state untouched
    sta $d020
    sta $d021
    lda $d030
    and #$fe // no CRAM2K mapping over hardware I/O
    sta $d030
    lda $d031
    and #$47 // H320 / V200, no VIC-III attributes or bitplanes
    ora #$40 // FAST together with D054.VFAST: full CPU clock
    sta $d031
    lda $d016
    and #$e0
    ora #8 // 40-col legacy CSEL flag; custom count is 44
    sta $d016
    lda #$45 // VFAST + CHR16/FCLRHI; no NCM, RRB/GOTOX, alpha or flips
    sta $d054
    lda $d07a
    and #$ef // CHARY16 off
    sta $d07a
    lda #$50 // mapped bank1, primary bank1
    sta $d070
    ldx #32
apply_palette_loop:
    lda t_red,x
    sta $d100,x
    lda t_green,x
    sta $d200,x
    lda t_blue,x
    sta $d300,x
    dex
    bpl apply_palette_loop
    // All RGB4 expanded channels have identical nibbles; VIC nibble swap
    // leaves exact values unchanged ($A -> $AA, etc.).
    lda #<T_SCREEN
    sta $d060
    lda #>T_SCREEN
    sta $d061
    lda #0
    sta $d062
    sta $d063
    sta $d064
    lda #$20
    sta $d065 // own colour pointer offset $2000
    lda #88
    sta $d058
    lda #0
    sta $d059
    lda #44
    sta $d05e
    lda #29 // count is last row number, 30 rows
    sta $d07b
    lda #120 // H320: one source pixel per two native horizontal pixels
    sta $d05a
    lda #1 // CHRYSCL = physical rasters per pixel minus 1: 2 - 1.
    sta $d05b
    lda #40 // PAL border area; image inside, X=48..751
    sta $d05c
    lda #0
    sta $d05d
    sta $d049
    sta $d04b
    sta $d04d
    sta $d04f
    lda #48
    sta $d04c // X origin; complete 704-pixel-wide image
    sta $d048 // top border at physical raster 48
    sta $d04e // Y origin; complete 480-physical-raster image
    lda #<528
    sta $d04a // bottom is exclusive
    lda #>528
    sta $d04b
    // Fill private Color RAM with zero attributes, no source buffer needed.
    lda #0
    sta t_dma_src_mb
    lda #$ff
    sta t_dma_dst_mb
    lda #3
    sta t_dma_command
    lda #0
    sta t_dma_src_lo
    sta t_dma_src_hi
    lda #0
    sta t_dma_src_bank
    sta t_dma_dst_lo
    lda #$20
    sta t_dma_dst_hi
    lda #8
    sta t_dma_dst_bank
    jsr t_dma_copy
    lda #0
    sta t_dma_command
    lda #$1b
    sta $d011 // DEN on; HOTREG remains off, custom geometry not propagated
    rts

t_restore_video:
    php
    sei
    lda t_shown
    bne !restore+
    plp
    rts
!restore:
    lda #0
    sta t_shown
    sta t_dma_command
    lda #<T_CELLS*2
    sta t_dma_len_lo
    lda #>T_CELLS*2
    sta t_dma_len_hi
    // Deny legacy hot propagation until every saved geometry field is back.
    lda #0
    sta $d05d
    lda $d011
    and #$ef
    sta $d011
    lda #$40
    sta $d070
    ldx #32
restore_palette_loop:
    lda t_saved_r,x
    sta $d100,x
    lda t_saved_g,x
    sta $d200,x
    lda t_saved_b,x
    sta $d300,x
    dex
    bpl restore_palette_loop
    lda #0
    sta t_dma_src_mb
    lda #$ff
    sta t_dma_dst_mb
    lda #0
    sta t_dma_src_lo
    sta t_dma_dst_lo
    lda #$f1
    sta t_dma_src_hi
    lda #5
    sta t_dma_src_bank
    lda #$20
    sta t_dma_dst_hi
    lda #8
    sta t_dma_dst_bank
    jsr t_dma_copy
    // Drain pending legacy updates BEFORE restoring precise geometry.
    // Enabling HOTREG last would recalculate/overwrite the restored VIC-IV
    // borders, origins, stride and pointers (XEMU vic4.c and VIC-IV core).
    lda t_saved_regs+T_REG_D05D
    sta $d05d
    lda t_saved_regs+T_REG_D011
    sta $d011
    lda t_saved_regs+T_REG_D016
    sta $d016
    lda t_saved_regs+T_REG_D031
    sta $d031
    // No further hot-register writes after this point. Restore precise
    // fields with HOTREG disabled; final enable has no pending update.
    lda t_saved_regs+T_REG_D05D
    and #$7f
    sta $d05d
    // Restore all registers except already-restored hot registers/HOTREG.
    ldx #T_REG_COUNT-1
restore_reg_loop:
    lda t_regs,x
    cmp #$5d
    beq restore_next_reg
    cmp #$11
    beq restore_next_reg
    cmp #$16
    beq restore_next_reg
    cmp #$31
    beq restore_next_reg
    sta write_vic+1
    lda t_saved_regs,x
write_vic:
    sta $d000
restore_next_reg:
    dex
    bpl restore_reg_loop
    lda t_saved_regs+T_REG_D07A
    sta $d07a // restore full comparator/source after earlier D011
    lda t_saved_regs+T_REG_D05D
    sta $d05d // original HOTREG value LAST
    lda t_saved_cursor
    sta $1120
    plp
    rts

t_dma_copy:
    ldx #<t_dma_list
    ldy #>t_dma_list
t_transfer:
    lda #0
    sta $d702
    sta $d704
    sty $d701
    stx $d705
    rts
t_dma_list:
    .byte $80
t_dma_src_mb: .byte 0
    .byte $81
t_dma_dst_mb: .byte 0
    .byte $0a,0
t_dma_command: .byte 0
t_dma_len_lo: .byte 0
t_dma_len_hi: .byte 0
t_dma_src_lo: .byte 0
t_dma_src_hi: .byte 0
t_dma_src_bank: .byte 0
t_dma_dst_lo: .byte 0
t_dma_dst_hi: .byte 0
t_dma_dst_bank: .byte 0
    .word 0
t_regs: .byte $11,$15,$16,$20,$21,$30,$31,$48,$49,$4a,$4b,$4c,$4d,$4e,$4f,$54,$58,$59,$5a,$5b,$5c,$5d,$5e,$60,$61,$62,$63,$64,$65,$70,$7a,$7b,$68,$69,$6a,$6c,$6d,$6e
t_saved_regs: .fill T_REG_COUNT,0
t_saved_compare_bit: .byte 0
t_saved_cursor: .byte 0
t_shown: .byte 0
t_saved_r: .fill 33,0
t_saved_g: .fill 33,0
t_saved_b: .fill 33,0
t_prefix: .fill T_PREFIX_BYTES,t_data.get(i)
t_red: .fill 33,t_data.get(26+3*i)
t_green: .fill 33,t_data.get(27+3*i)
t_blue: .fill 33,t_data.get(28+3*i)
t_level_header: .import binary "VYLV.DAT",0,8
t_graphics_header: .import binary "VYGR.DAT",0,8
t_filename: .text "VYTI.DAT,S,R"
.byte 0
t_file_message: .text " FILE "
.byte 0
t_code_end:
}
// Stage10a2: packed-SEQ decoder in the unused bootstrap tail (see stage10a6_unpack.asm).
.import source "stage10a6_unpack.asm"
.if (* > unpack.wptr) { .error "Stage10a2 decoder overlaps its ring pointers" }
.fill unpack.wptr-*,0
.byte 0,0,$0b,$08 // unpack.wptr: Attic $080B0000 + 16-bit ring index
.byte 0,0,$0b,$08 // unpack.rptr
.if (* != $4800) { .error "Title bootstrap must end exactly at $4800" }

// Persistent helper, survives the HUD overwriting the title bootstrap.
*=$3340 "Stage5d1 bootstrap backup and repeated RUN restoration"
.namespace titlecache {
tc_save:
    jsr bootstrapcache.save
    lda #0
    sta tc_src_mb
    lda #$80
    sta tc_dst_mb
    lda #0
    sta tc_src_lo
    sta tc_src_bank
    sta tc_dst_lo
    lda #$40
    sta tc_src_hi
    lda #0
    sta tc_dst_hi
    sta tc_dst_bank
    lda #1
    sta tc_saved
    jmp tc_transfer
tc_restore:
    jsr bootstrapcache.restore
    lda tc_saved
    beq !done+
    lda #0
    sta tc_saved
    sta tc_src_lo
    sta tc_dst_lo
    sta tc_dst_bank
    sta tc_src_hi
    sta tc_src_bank
    sta tc_dst_mb
    lda #$80
    sta tc_src_mb
    lda #$40
    sta tc_dst_hi
    jsr tc_transfer
!done:
    rts
tc_transfer:
    lda #0
    sta $d702
    sta $d704
    lda #>tc_list
    sta $d701
    lda #<tc_list
    sta $d705
    rts
tc_saved: .byte 0
tc_list:
    .byte $80
tc_src_mb: .byte 0
    .byte $81
tc_dst_mb: .byte 0
    .byte $0a,0,0
    .word $800
tc_src_lo: .byte 0
tc_src_hi: .byte 0
tc_src_bank: .byte 0
tc_dst_lo: .byte 0
tc_dst_hi: .byte 0
tc_dst_bank: .byte 0
    .word 0
.if (* > $3400) { .error "Title persistent helper overlaps graphics cache code" }
}
