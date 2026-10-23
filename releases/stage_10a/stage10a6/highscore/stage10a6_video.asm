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
    lda #<CELLS
    sta dma_len_lo
    lda #>CELLS
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
    and #$40 // preserve FAST only; no attributes, bitplanes, V400/H1280/interlace
    ora #$80 // H640,80 columns at normal character width
    sta $d031
    lda $d016
    and #$e0
    ora #8 // CSEL enabled; H640 supplies80 columns
    sta $d016
    lda #0 // mono8-bit text; no CHR16/FCM/NCM/RRB/alpha
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
    lda #80
    sta $d05e
    lda #24 // 25 rows
    sta $d07b
    lda #120 // H640: normal one-pixel native horizontal size
    sta $d05a
    lda #1 // CHRYSCL = physical rasters per pixel minus 1: 2 - 1.
    sta $d05b
    lda #40 // Side border width; custom text origin is set separately
    sta $d05c
    lda #0
    sta $d05d
    sta $d049
    sta $d04b
    sta $d04d
    sta $d04f
    lda #80
    sta $d04c // X origin;640 native horizontal pixels
    lda #100
    sta $d048 // standard400-pixel physical height
    sta $d04e
    lda #<500
    sta $d04a // bottom is exclusive
    lda #>500
    sta $d04b
    lda #0
    sta $d068
    sta $d06a
    lda #>CHARSET
    sta $d069
    // Explicit normal foreground colours for all cells.
    lda #0
    sta dma_src_mb
    lda #$ff
    sta dma_dst_mb
    lda #<band_buffer
    sta dma_src_lo
    lda #>band_buffer
    sta dma_src_hi
    lda #0
    sta dma_src_bank
    sta dma_dst_lo
    lda #$20
    sta dma_dst_hi
    lda #8
    sta dma_dst_bank
    lda #<CELLS
    sta dma_len_lo
    lda #>CELLS
    sta dma_len_hi
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
    lda #<CELLS
    sta dma_len_lo
    lda #>CELLS
    sta dma_len_hi
    jsr dma_copy
    // Restore all registers except HOTREG and DEN first.
    ldx #REG_COUNT-1
restore_reg_loop:
    lda title_regs,x
    cmp #$5d
    beq restore_next_reg
    cmp #$11
    beq restore_next_reg
    sta write_vic+1
    lda title_saved_regs,x
write_vic:
    sta $d000
restore_next_reg:
    dex
    bpl restore_reg_loop
    lda title_saved_regs+REG_D011
    sta $d011
    lda title_saved_regs+REG_D07A
    sta $d07a // restore full comparator/source after D011
    lda title_saved_regs+REG_D05D
    sta $d05d // original HOTREG value LAST
    rts

// F018A COPY only; no engine loader or disk channel is used.
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
    .byte $0a,0,0
dma_len_lo: .byte 0
dma_len_hi: .byte 0
dma_src_lo: .byte 0
dma_src_hi: .byte 0
dma_src_bank: .byte 0
dma_dst_lo: .byte 0
dma_dst_hi: .byte 0
dma_dst_bank: .byte 0
    .word 0
