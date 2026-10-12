// Private fixed-position menu renderer. Six complete FCM cells per actor.
*=$2800 "32 independent menu animations"
menu_init:
    ldx #31
!loop:
    lda menu_initial_frames,x
    sta menu_frames,x
    lda menu_initial_delays,x
    sta menu_delays,x
    dex
    bpl !loop-
    lda #0
    sta menu_clock
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_lo
    sta dma_src_bank
    sta dma_dst_lo
    sta dma_dst_bank
    lda #$50
    sta dma_src_hi
    lda #$70
    sta dma_dst_hi
    lda #<CELLS*2
    sta dma_len_lo
    lda #>CELLS*2
    sta dma_len_hi
    jsr dma_copy
    rts
menu_tick:
    inc menu_clock
    lda menu_clock
    cmp #MENU_FRAME_DIVIDER
    bcs !animate+
    rts
!animate:
    lda #0
    sta menu_clock
menu_animate:
    ldx #31
!actor:
    dec menu_delays,x
    bne !next+
    lda menu_periods,x
    sta menu_delays,x
    lda menu_frames,x
    clc
    adc #1
    cmp menu_counts,x
    bcc !frame+
    lda #0
!frame:
    sta menu_frames,x
    asl
    sta menu_offset
    asl
    clc
    adc menu_offset
    asl // frame *12 bytes, <=132
    clc
    adc menu_base_lo,x
    sta menu_read+1
    lda menu_base_hi,x
    adc #0
    sta menu_read+2
    lda menu_dst_lo,x
    sta menu_write+1
    lda menu_dst_hi,x
    sta menu_write+2
    lda #3
    sta menu_rows
!row:
    ldy #3
!byte:
menu_read:
    lda $ffff,y
menu_write:
    sta $ffff,y
    dey
    bpl !byte-
    clc
    lda menu_read+1
    adc #4
    sta menu_read+1
    bcc !src+
    inc menu_read+2
!src:
    clc
    lda menu_write+1
    adc #80
    sta menu_write+1
    bcc !dst+
    inc menu_write+2
!dst:
    dec menu_rows
    bne !row-
!next:
    dex
    bmi !done+
    jmp !actor-
!done:
    rts
menu_offset: .byte 0
menu_rows: .byte 0
.if (* > $3000) { .error "Menu animator exceeds private code budget" }
