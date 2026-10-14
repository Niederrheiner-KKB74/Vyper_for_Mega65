// Issue81: standalone display only. No engine, loader, sound or disk writes.
.const CELLS=80*25
.const SCREEN=$7000
.const CHARSET=$8000 // avoid VIC legacy WOM aliases $1000/$1800/$9000/$9800
.const REG_COUNT=35
.const REG_D011=0
.const REG_D05D=21
.const REG_D07A=30
.const BAND_STEP_FRAMES=8
*=$2001 "BASIC SYS8448"
BasicUpstart($2100)
*=$2100 "Standalone highscore controller"
entry:
    php
    sei
    cld // private arithmetic is binary; PLP restores the caller status on exit
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    lda $d614
    sta saved_column
    lda $dc02
    sta saved_ddra
    and #$e0 // Joystick Port2 direction/fire pins are inputs throughout test.
    sta $dc02
    jsr title_save_video
    jsr copy_charset
    jsr flush_keys
    lda #0
    sta page
    sta quit
    sta joy_held
    sta fire_armed
    sta key_held
    sta band_phase
    sta band_clock
    sta frame_pending
    sta page_dirty
    sta colour_dirty
    jsr page_draw
    jsr title_show
    jsr cc_init
    jsr cc_publish
// Cooperative raster-edge state: input stays live even while no frame is due.
main_loop:
    jsr input_tick
    lda quit
    bne exit_to_basic
    lda $d012
    cmp #250
    bne !left+
    lda #1
    sta frame_pending
    jmp main_loop
!left:
    lda frame_pending
    beq main_loop
    lda #0
    sta frame_pending
    jsr frame_tick
    jmp main_loop
exit_to_basic:
    jsr title_restore_video
    lda saved_column
    sta $d614
    lda saved_ddra
    sta $dc02
    jsr flush_keys
    plp
    rts
frame_tick:
    jsr cc_tick
    inc band_clock
    lda band_clock
    cmp #BAND_STEP_FRAMES
    bcc !input+
    lda #0
    sta band_clock
    inc band_phase
    lda band_phase
    cmp #12
    bne !publish+
    lda #0
    sta band_phase
!publish:
    lda #1
    sta colour_dirty
!input:
    lda page_dirty
    beq !colours+
    lda #0
    sta page_dirty
    sta colour_dirty
    jmp page_draw
!colours:
    lda colour_dirty
    beq !done+
    lda #0
    sta colour_dirty
    jmp bands_publish
!done:
    rts

page_left:
    lda page
    beq !done+
    dec page
    lda #1
    sta page_dirty
    rts
!done:
    rts
page_right:
    lda page
    cmp #3
    beq !done+
    inc page
    lda #1
    sta page_dirty
    rts
!done:
    rts
page_draw:
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_bank
    sta dma_dst_bank
    sta dma_dst_lo
    ldx page
    lda page_lo,x
    sta dma_src_lo
    lda page_hi,x
    sta dma_src_hi
    lda #>SCREEN
    sta dma_dst_hi
    lda #<CELLS
    sta dma_len_lo
    lda #>CELLS
    sta dma_len_hi
    jsr dma_copy
    jmp bands_publish
bands_publish:
    // Update300 foreground bytes in the private plane, then publish one2KiB DMA.
    // Glyphs and screen remain unchanged.
    lda #0
    sta band_row
!row:
    ldx band_row
    lda band_left_lo,x
    sta band_write_left+1
    lda band_left_hi,x
    sta band_write_left+2
    lda band_right_lo,x
    sta band_write_right+1
    lda band_right_hi,x
    sta band_write_right+2
    txa
    clc
    adc band_phase
    cmp #12
    bcc !index+
    sbc #12
!index:
    tay
    lda band_colours,y
    ldy #14
!pixel:
band_write_left:
    sta band_buffer,y
band_write_right:
    sta band_buffer,y
    dey
    bpl !pixel-
    inc band_row
    lda band_row
    cmp #10
    bne !row-
    lda #0
    sta dma_src_mb
    sta dma_src_bank
    lda #<band_buffer
    sta dma_src_lo
    lda #>band_buffer
    sta dma_src_hi
    lda #$ff
    sta dma_dst_mb
    lda #8
    sta dma_dst_bank
    lda #$20
    sta dma_dst_hi
    lda #0
    sta dma_dst_lo
    lda #<CELLS
    sta dma_len_lo
    lda #>CELLS
    sta dma_len_hi
    jmp dma_copy

input_tick:
    // Matrix is used only to release the typematic latch. FIFO captures short taps.
    lda #0
    sta $d614
    lda $d613
    and #4
    beq !held+
    lda $d60f
    and #1
    bne !held+
    lda #0
    sta key_held
!held:
    lda #16 // bounded queue drain, never blocks animation
    sta key_budget
!key:
    lda $d610
    beq !joystick+
    lda $d619
    sta $d619
    cmp #$1d
    beq !right+
    cmp #$9d
    beq !left+
    lda #1 // RETURN/X/any other typing event exits
    sta quit
    rts
!right:
    lda key_held
    bne !next+
    inc key_held
    jsr page_right
    jmp !next+
!left:
    lda key_held
    bne !next+
    inc key_held
    jsr page_left
!next:
    dec key_budget
    bne !key-
!joystick:
    lda $dc00
    sta joy_sample
    and #$10
    beq !fire+
    lda #1
    sta fire_armed
    bne !direction+
!fire:
    lda fire_armed
    beq !direction+
    lda #1
    sta quit
    rts
!direction:
    lda joy_sample
    eor #$ff
    and #$0c
    beq !release+
    cmp #$0c
    beq !done+ // contradictory directions never turn a page
    ldx joy_held
    bne !done+
    sta joy_held
    cmp #4
    bne !right+
    jmp page_left
!right:
    jmp page_right
!release:
    lda #0
    sta joy_held
!done:
    rts
flush_keys:
    ldx #16
!next:
    lda $d610
    beq !done+
    sta $d610
    dex
    bne !next-
!done:
    rts

copy_charset:
    lda #$ff
    sta dma_src_mb
    lda #7
    sta dma_src_bank
    lda #$e0
    sta dma_src_hi
    lda #0
    sta dma_src_lo
    sta dma_dst_mb
    sta dma_dst_bank
    sta dma_dst_lo
    sta dma_len_lo
    lda #>CHARSET
    sta dma_dst_hi
    lda #8
    sta dma_len_hi
    jsr dma_copy
    ldx #47
!frame:
    lda frame_glyphs,x
    sta CHARSET+128*8,x
    dex
    bpl !frame-
    rts

.import source "stage9c1_video.asm"
.if (*>$3000) { .error "Controller/video exceed code budget" }
.import source "stage9c1_cycling.asm"
*=$3200 "Private registers, palette and animation state"
page: .byte 0
quit: .byte 0
joy_held: .byte 0
fire_armed: .byte 0
joy_sample: .byte 0
key_held: .byte 0
key_budget: .byte 0
saved_column: .byte 0
saved_ddra: .byte 0
band_phase: .byte 0
band_clock: .byte 0
band_row: .byte 0
frame_pending: .byte 0
page_dirty: .byte 0
colour_dirty: .byte 0
band_colours: .byte 3,3,3,3,4,4,4,4,5,5,5,5
page_lo: .byte <pages,<(pages+2000),<(pages+4000),<(pages+6000)
page_hi: .byte >pages,>(pages+2000),>(pages+4000),>(pages+6000)
band_left_lo: .fill 10,<(band_buffer+80*(7+i)+16)
band_left_hi: .fill 10,>(band_buffer+80*(7+i)+16)
band_right_lo: .fill 10,<(band_buffer+80*(7+i)+49)
band_right_hi: .fill 10,>(band_buffer+80*(7+i)+49)
title_regs: .byte $11,$15,$16,$20,$21,$30,$31,$48,$49,$4a,$4b,$4c,$4d,$4e,$4f,$54,$58,$59,$5a,$5b,$5c,$5d,$5e,$60,$61,$62,$63,$64,$65,$70,$7a,$7b,$68,$69,$6a
title_saved_compare_bit: .byte 0
title_saved_regs: .fill REG_COUNT,0
title_saved_r: .fill 33,0
title_saved_g: .fill 33,0
title_saved_b: .fill 33,0
title_red: .byte $00,$ff,$00,$00,$ff,$ff,$88
.fill 26,0
title_green: .byte $00,$ff,$ee,$00,$ff,$00,$88
.fill 26,0
title_blue: .byte $00,$ff,$cc,$ff,$00,$00,$88
.fill 26,0
.if (*>$4000) { .error "State overlaps page assets" }
*=$4000 "Four deterministic highscore pages"
pages: .import binary "pages.bin"
*=$6000 "Colour plane and private frame tiles"
band_buffer: .import binary "colours.bin"
frame_glyphs: .import binary "frame.bin"
.if (*>$7000) { .error "Assets overlap private screen" }
