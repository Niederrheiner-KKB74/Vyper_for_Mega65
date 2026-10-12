// Stage 6a2 / Issue #43. Independent original animated menu; no gameplay imports.
// FCM 40x25, exact snapshot typography/palette, 32 original animated types.
.import source "menu_assets.inc"
.import source "color_cycle.inc"
.const MENU_FRAME_DIVIDER=1 // adjustable global scale; original actor periods retained
.const REG_COUNT=32
.const REG_D011=0
.const REG_D07A=30
.const REG_D05D=21
.const SETBNK=$ff6b
.const BUF=$6800
.const CHECK=$6900
.const SCREEN=$7000
.const CELLS=40*25
*=$2001 "BASIC SYS 8448"
BasicUpstart($2100)
*=$2100 "Standalone menu loader and video"
title_entry:
    php
    cli // SEQ I/O in normal KERNAL/BASIC context, before video changes.
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    lda $ba
    cmp #8
    bcs device_ok
    lda #8
device_ok:
    sta device
    lda #0
    sta error
    sta total_crc
    sta total_crc+1
    sta dma_src_mb
    sta dma_dst_mb
    lda #<title_name
    sta name_ptr
    lda #>title_name
    sta name_ptr+1
    lda #12
    sta name_len
    lda #<titleData.getSize()
    sta remain
    lda #>((titleData.getSize()) & $ffff)
    sta remain+1
    lda #((titleData.getSize() >> 16) & $ff)
    sta remain+2
    lda #4
    sta target_bank
    lda #0
    sta target_hi
    jsr load_file
    lda error
    beq title_loaded
    jmp title_failed
title_loaded:
    lda total_crc
    cmp #<TITLE_SUM
    bne title_sum_bad
    lda total_crc+1
    cmp #>TITLE_SUM
    beq title_sum_good
title_sum_bad:
    lda #6
    sta error
    jmp title_failed
title_sum_good:
    // Exact schema, dimensions, 33 palette RGBs, payload sum16.
    lda #0
    sta dma_src_lo
    sta dma_src_hi
    sta dma_dst_lo
    sta dma_dst_bank
    sta dma_len_hi
    lda #4
    sta dma_src_bank
    lda #>CHECK
    sta dma_dst_hi
    lda #117
    sta dma_len_lo
    jsr dma_copy
    ldx #116
title_prefix_check:
    lda CHECK,x
    cmp title_prefix,x
    bne title_prefix_bad
    dex
    bpl title_prefix_check
    jsr title_align_tiles
    sei // Freeze BASIC IRQ/cursor; hardware ASCII FIFO remains active.
    jsr title_save_video
    jsr menu_init
    jsr cc_init
    jsr title_show
wait_x:
    lda $d610 // IRQ-independent ASCII FIFO; only X has any action.
    beq wait_raster
    sta $d610
    cmp #$78
    beq title_exit
    cmp #$58
    beq title_exit
wait_raster:
    lda $d012
    cmp #250 // logical PAL raster250, physical500: below menu end488
    bne wait_x
    lda $d011
    bmi wait_x
    jsr menu_tick
    jsr cc_tick // shared COLOR02 after animation, in the same blanking tick
wait_raster_leave:
    lda $d012
    cmp #250
    beq wait_raster_leave
    jmp wait_x
title_exit:
    jsr title_restore_video
    plp
    rts
title_prefix_bad:
    lda #5
    sta error
title_failed:
    ldx #<title_error_message
    ldy #>title_error_message
    jsr puts
    lda error
    jsr hex
    lda #13
    jsr $ffd2
    plp
    rts

// Forward copies remove the 117-byte verified asset prefix.
// Lengths bounded to32KiB; physical glyph RAM stays below $60000.
title_align_tiles:
.for (var off=0; off<TITLE_BYTES; off+=32768) {
    lda #<($40075+off)
    sta dma_src_lo
    lda #>(($40075+off)&$ffff)
    sta dma_src_hi
    lda #(($40075+off)>>16)
    sta dma_src_bank
    lda #<($40000+off)
    sta dma_dst_lo
    lda #>(($40000+off)&$ffff)
    sta dma_dst_hi
    lda #(($40000+off)>>16)
    sta dma_dst_bank
    lda #<min(32768,TITLE_BYTES-off)
    sta dma_len_lo
    lda #>min(32768,TITLE_BYTES-off)
    sta dma_len_hi
    jsr dma_copy
}
    rts

// All changed VIC registers captured before first video write.
// No CPU writes to KERNAL workspace $1000-$15FF, screen or cursor state.
title_save_video:
    ldx #REG_COUNT-1
save_reg_loop:
    lda title_regs,x
    sta read_vic+1
read_vic:
    lda $d000
    sta title_saved_regs,x
    dex
    bpl save_reg_loop
    // D011 bit7 reads live raster, not IRQ compare. Reconstruct the saved
    // write value from D07A.RASCMP bit0, preserving actual IRQ target bit8.
    lda title_saved_regs+REG_D07A
    and #1
    lsr
    ror
    sta title_saved_compare_bit
    lda title_saved_regs+REG_D011
    and #$7f
    ora title_saved_compare_bit
    sta title_saved_regs+REG_D011
    lda #$40 // map palette bank1 only; do not select it for display yet
    sta $d070
    ldx #32
save_palette_loop:
    lda $d100,x
    sta title_saved_r,x
    lda $d200,x
    sta title_saved_g,x
    lda $d300,x
    sta title_saved_b,x
    dex
    bpl save_palette_loop
    // Backup own Color-RAM window $FF82000..$FF827CF, never BASIC's window.
    lda #$ff
    sta dma_src_mb
    lda #0
    sta dma_dst_mb
    sta dma_src_lo
    sta dma_dst_lo
    lda #$20
    sta dma_src_hi
    lda #8
    sta dma_src_bank
    lda #$50
    sta dma_dst_hi
    lda #1
    sta dma_dst_bank
    lda #<CELLS*2
    sta dma_len_lo
    lda #>CELLS*2
    sta dma_len_hi
    jmp dma_copy

title_show:
    lda $d05d
    and #$7f // HOTREG OFF before legacy writes; direct geometry follows.
    sta $d05d
    lda $d011
    and #$0f
    sta $d011 // DEN off; no ECM/BMM. IRQ disabled throughout image display.
    lda #0
    sta $d015 // hardware sprites off, other sprite state untouched
    sta $d020
    sta $d021
    lda $d030
    and #$fe // no CRAM2K mapping over hardware I/O
    sta $d030
    lda $d031
    and #$47 // H320 / V200, no VIC-III attributes or bitplanes
    ora #$40 // guaranteed 3.5MHz FAST; saved original D031 restored on X
    sta $d031
    lda $d016
    and #$e0
    ora #8 // 40-col legacy CSEL flag; custom count is40
    sta $d016
    lda #5 // CHR16 and FCLRHI; no NCM, RRB/GOTOX, alpha or flips
    sta $d054
    lda $d07a
    and #$ef // CHARY16 off
    sta $d07a
    lda #$50 // mapped bank1, primary bank1
    sta $d070
    ldx #32
apply_palette_loop:
    lda title_red,x
    sta $d100,x
    lda title_green,x
    sta $d200,x
    lda title_blue,x
    sta $d300,x
    dex
    bpl apply_palette_loop
    // All RGB4 expanded channels have identical nibbles; VIC nibble swap
    // leaves exact values unchanged ($A -> $AA, etc.).
    lda #<SCREEN
    sta $d060
    lda #>SCREEN
    sta $d061
    lda #0
    sta $d062
    sta $d063
    sta $d064
    lda #$20
    sta $d065 // own colour pointer offset $2000
    lda #80
    sta $d058
    lda #0
    sta $d059
    lda #40
    sta $d05e
    lda #24 // 25 original320x200 menu rows
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
    lda #80
    sta $d04c // 640 native pixels, horizontally centered
    lda #88
    sta $d048
    sta $d04e // 400 native rows, centered in PAL display
    lda #<488
    sta $d04a // bottom is exclusive
    lda #>488
    sta $d04b
    // Explicit empty FCM attributes for all cells.
    lda #0
    sta dma_src_mb
    lda #$ff
    sta dma_dst_mb
    lda #<title_zero_colours
    sta dma_src_lo
    lda #>title_zero_colours
    sta dma_src_hi
    lda #0
    sta dma_src_bank
    sta dma_dst_lo
    lda #$20
    sta dma_dst_hi
    lda #8
    sta dma_dst_bank
    jsr dma_copy
    lda #$1b
    sta $d011 // DEN on; HOTREG remains off, custom geometry not propagated
    rts

title_restore_video:
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
    lda title_saved_r,x
    sta $d100,x
    lda title_saved_g,x
    sta $d200,x
    lda title_saved_b,x
    sta $d300,x
    dex
    bpl restore_palette_loop
    lda #0
    sta dma_src_mb
    lda #$ff
    sta dma_dst_mb
    lda #0
    sta dma_src_lo
    sta dma_dst_lo
    lda #$50
    sta dma_src_hi
    lda #1
    sta dma_src_bank
    lda #$20
    sta dma_dst_hi
    lda #8
    sta dma_dst_bank
    jsr dma_copy
    // Drain legacy HOTREG writes before restoring precise geometry.
    lda title_saved_regs+REG_D05D
    sta $d05d
    lda title_saved_regs+REG_D011
    sta $d011
    lda title_saved_regs+2 // D016
    sta $d016
    lda title_saved_regs+6 // D031
    sta $d031
    lda title_saved_regs+REG_D05D
    and #$7f
    sta $d05d
    ldx #REG_COUNT-1
restore_reg_loop:
    lda title_regs,x
    cmp #$5d
    beq restore_next_reg
    cmp #$11
    beq restore_next_reg
    cmp #$16
    beq restore_next_reg
    cmp #$31
    beq restore_next_reg
    sta write_vic+1
    lda title_saved_regs,x
write_vic:
    sta $d000
restore_next_reg:
    dex
    bpl restore_reg_loop
    lda title_saved_regs+REG_D07A
    sta $d07a // restore full comparator/source after D011
    lda title_saved_regs+REG_D05D
    sta $d05d // original HOTREG value LAST
    rts

load_file:
    lda #0
    sta chunk_size
    sta io_status
    lda #2
    ldx device
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
    lda io_status
    and #$40
    bne exact_eof
    lda #3 // Oversized file: expected last byte must be EOF.
    sta error
    jmp close_input
exact_eof:
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
    .byte $80
dma_src_mb: .byte 0
    .byte $81
dma_dst_mb: .byte 0
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


title_regs: .byte $11,$15,$16,$20,$21,$30,$31,$48,$49,$4a,$4b,$4c,$4d,$4e,$4f,$54,$58,$59,$5a,$5b,$5c,$5d,$5e,$60,$61,$62,$63,$64,$65,$70,$7a,$7b
title_saved_compare_bit: .byte 0
title_saved_regs: .fill REG_COUNT,0
title_saved_r: .fill 33,0
title_saved_g: .fill 33,0
title_saved_b: .fill 33,0
title_prefix: .fill 117,titleData.get(i)
title_red: .fill 33,titleData.get(18+3*i)
title_green: .fill 33,titleData.get(19+3*i)
title_blue: .fill 33,titleData.get(20+3*i)
title_name: .text "VYMN.DAT,S,R"
title_error_message: .text "STAGE 6A2 LOAD ERROR $"
.byte 0
device: .byte 8
name_ptr: .word 0
name_len: .byte 0
remain: .byte 0,0,0
target_hi: .byte 0
target_bank: .byte 0
chunk_size: .byte 0
io_status: .byte 0
error: .byte 0
total_crc: .word 0
title_code_end:
.if (title_code_end > $2800) { .error "Menu code overlaps animation budget" }
*=$4000 "FCM zero attributes source"
title_zero_colours: .fill CELLS*2,0
.if (* > BUF) { .error "Attribute template overlaps loader buffers" }
*=$5000 "Persistent initial menu screen, for repeated RUN"
.import binary "menu_screen.bin"
.if (* > BUF) { .error "Menu template overlaps SEQ buffer" }
*=$7000 "Independent FCM 40x25 screen"
title_screen: .fill CELLS*2,menuScreen.get(i)
.if (* != $77d0) { .error "Unexpected FCM screen extent" }
.if ($40000+TITLE_BYTES > $60000) { .error "Menu exceeds free high chip RAM" }

.import source "stage6a2_animation.asm"

.import source "stage6a2_cycling.asm"
