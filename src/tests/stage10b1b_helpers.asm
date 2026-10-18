// Render exactly96 words per row. A/B/C have the same visible ordinary text;
// B substitutes one16-wide NCM cell for four4-wide mono cells on rows10/11.
plain_screen:
    lda #0
    sta row
    sta row_dest
    sta row_dest+1
    lda #<$7000
    sta text_base
    lda #>$7000
    sta text_base+1
plain_row:
    lda text_base
    sta text_read+1
    lda text_base+1
    sta text_read+2
    lda #0
    sta text_col
    sta slot
    sta ncm_done
    sta hud_goto_done
plain_cell:
    lda #0
    sta cell_value+1
    sta cell_flags
    lda #1
    sta cell_colour
    lda profile
    cmp #$42
    bne plain_check_c
    lda ncm_done
    bne plain_check_c
    lda row
    cmp #10
    beq plain_b_row
    cmp #11
    bne plain_check_c
plain_b_row:
    lda text_col
    cmp #56
    bne plain_check_c
    lda row
    sec
    sbc #10
    clc
    adc #$41
    sta cell_value
    lda #2
    sta cell_value+1
    lda #8
    sta cell_flags
    lda #$10
    sta cell_colour
    lda #60
    sta text_col
    lda #1
    sta ncm_done
    jmp plain_store
plain_check_c:
    lda profile
    cmp #$43
    bne plain_mono
    lda slot
    beq plain_goto_zero
    lda text_col
    cmp #60
    bne plain_mono
    lda hud_goto_done
    bne plain_mono
    lda #$e0
    sta cell_value
    lda #1
    sta cell_value+1
    sta hud_goto_done
    bne plain_goto_flags
plain_goto_zero:
    lda #0
    sta cell_value
plain_goto_flags:
    lda #$10
    sta cell_flags
    lda #0
    sta cell_colour
    jmp plain_store
plain_mono:
    ldx text_col
    cpx #80
    bcs plain_space
text_read:
    lda $7000,x
    inc text_col
    jmp plain_mono_value
plain_space:
    lda #32
plain_mono_value:
    sta cell_value
plain_store:
    lda slot
    asl
    tay
    lda cell_value
    sta $6c00,y
    lda cell_value+1
    sta $6c01,y
    lda cell_flags
    sta $6d00,y
    lda cell_colour
    sta $6d01,y
    inc slot
    lda slot
    cmp #96
    beq plain_commit
    jmp plain_cell
plain_commit:
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_bank
    sta dma_dst_bank
    sta dma_src_lo
    sta dma_len_hi
    lda #$6c
    sta dma_src_hi
    lda #192
    sta dma_len_lo
    lda row_dest
    sta dma_dst_lo
    clc
    lda row_dest+1
    adc #$e0
    sta dma_dst_hi
    jsr dma
    lda #$6d
    sta dma_src_hi
    lda #$ff
    sta dma_dst_mb
    lda #8
    sta dma_dst_bank
    lda row_dest+1
    sta dma_dst_hi
    jsr dma
    clc
    lda row_dest
    adc #192
    sta row_dest
    bcc !+
    inc row_dest+1
!:
    clc
    lda text_base
    adc #80
    sta text_base
    bcc !+
    inc text_base+1
!:
    inc row
    lda row
    cmp #25
    beq plain_done
    jmp plain_row
plain_done:
    rts

// Markers are independent hardware sprites2/3, never additional RRB slots.
marker_draw:
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_bank
    sta dma_dst_bank
    sta dma_len_hi
    lda #64
    sta dma_len_lo
    lda #$92
    sta dma_dst_hi
    lda #$80
    sta dma_dst_lo
    lda profile
    sec
    sbc #$41
    asl
    asl
    asl
    asl
    asl
    asl
    sta dma_src_lo
    lda #$78
    sta dma_src_hi
    jsr dma
    lda #$c0
    sta dma_dst_lo
    lda indicator
    asl
    asl
    asl
    asl
    asl
    asl
    sta dma_src_lo
    lda #$79
    sta dma_src_hi
    jmp dma
wait_vblank:
    lda $d053
    and #$0f
    cmp #2
    bne wait_vblank
    lda $d052
    cmp #16
    bcc wait_vblank
    rts
apply_norrdel:
    lda initial_vic+$1a
    and #$0f
    sta $d01a
    lda #$1f // fixed NORRDEL0 DBLRR0; explicit unused comparator high shadow
    sta d051_shadow
    sta $d051
    rts

// Actual palette readback: only mapped-bank bits7:6 change. Display/sprite
// selectors remain fixed. No palette writes and no changes to captured RGB.
read_palettes:
    lda $d030
    sta saved_capture_d030
    and #$fe
    sta $d030
    lda $d070
    sta saved_capture_pal
    .for(var b=0;b<4;b++) {
        lda saved_capture_pal
        and #$3f
        ora #(b<<6)
        sta $d070
        ldx #0
    !loop:
        lda $d100,x
        sta $5400+b*$300,x
        lda $d200,x
        sta $5500+b*$300,x
        lda $d300,x
        sta $5600+b*$300,x
        inx
        bne !loop-
    }
    lda saved_capture_pal
    sta $d070
    lda saved_capture_d030
    sta $d030
    rts
capture_snapshot:
    lda profile
    sta snap_header+9
    lda export_env
    sta snap_header+10
    lda record_phase
    sta snap_header+11
    lda sequence
    sta snap_header+20
    lda sequence+1
    sta snap_header+21
    lda d051_shadow
    sta snap_header+24
    sta write_shadows
    lda d051_restore_shadow
    sta snap_header+25
    sta write_shadows+1
    lda measured_error
    sta snap_header+26
    sta write_shadows+8
    lda initial_vic+$1a
    sta snap_header+27
    sta write_shadows+2
    and #$0f
    sta write_shadows+3
    lda #$55
    sta write_shadows+4
    lda #$c0
    sta write_shadows+5
    lda sprite_mask
    sta write_shadows+6
    lda record_phase
    sta write_shadows+7
    lda profile
    sta write_shadows+9
    lda sequence
    sta write_shadows+10
    lda sequence+1
    sta write_shadows+11
    lda initial_vic+$7a
    sta write_shadows+12
    and #$ef
    sta write_shadows+13
    lda #0
    sta write_shadows+14
    sta write_shadows+15
    sta snap_header+28
    sta snap_header+29
    lda $d012
    sta snap_header+32
    lda $d011
    sta snap_header+33
    lda $d052
    sta snap_header+34
    lda $d053
    sta snap_header+35
    lda $d050
    sta snap_header+36
    lda $d051
    sta snap_header+37
    lda #<(snap_header+48)
    sta put+1
    lda #>(snap_header+48)
    sta put+2
    ldx #0
capture_registers:
    lda reg_lo,x
    sta read_reg+1
    jsr put
    lda reg_hi,x
    sta read_reg+2
    jsr put
read_reg:
    lda $d000
    jsr put
    inx
    cpx #REG_COUNT
    bne capture_registers
    jsr read_palettes
    jsr snapshot_header_copy
    lda #0
    sta region_index
capture_region:
    ldx region_index
    lda ms_lo,x
    sta dma_src_lo
    lda ms_hi,x
    sta dma_src_hi
    lda ms_bank,x
    sta dma_src_bank
    lda ms_mb,x
    sta dma_src_mb
    lda md_lo,x
    sta dma_dst_lo
    lda md_hi,x
    sta dma_dst_hi
    lda ml_lo,x
    sta dma_len_lo
    lda ml_hi,x
    sta dma_len_hi
    lda capture_bank
    sta dma_dst_bank
    lda #0
    sta dma_dst_mb
    jsr store_snapshot
    inc region_index
    lda region_index
    cmp #REGION_COUNT
    bne capture_region
    lda #0
    sta stream_pos
    sta stream_lo
    sta stream_hi
    lda #$ff
    sta mem_sum
    sta mem_sum+1
    lda capture_bank
    sta stream_bank
    lda #<SNAPSHOT_SIZE
    sta remaining
    lda #>SNAPSHOT_SIZE
    sta remaining+1
snapshot_sum:
    jsr stream_byte
    jsr crc_byte
    jsr dec_remaining
    bne snapshot_sum
    lda mem_sum
    sta snap_header+28
    lda mem_sum+1
    sta snap_header+29
snapshot_header_copy:
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_bank
    sta dma_dst_lo
    sta dma_dst_hi
    sta dma_len_lo
    lda capture_bank
    sta dma_dst_bank
    lda #3
    sta dma_len_hi
    lda #<snap_header
    sta dma_src_lo
    lda #>snap_header
    sta dma_src_hi
    jmp store_snapshot
// CRC16-CCITT-FALSE: initFFFF, poly1021, checksum bytes zero in source.
crc_byte:
    eor mem_sum+1
    sta mem_sum+1
    ldx #8
crc_bit:
    asl mem_sum
    rol mem_sum+1
    bcc crc_shifted
    lda mem_sum
    eor #$21
    sta mem_sum
    lda mem_sum+1
    eor #$10
    sta mem_sum+1
crc_shifted:
    dex
    bne crc_bit
    rts
put:
    sta $5100
    inc put+1
    bne !+
    inc put+2
!:
    rts
stream_byte:
    lda stream_pos
    bne stream_cached
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_dst_bank
    sta dma_dst_lo
    sta dma_len_lo
    lda #$50
    sta dma_dst_hi
    lda #1
    sta dma_len_hi
    lda stream_bank
    cmp #4
    beq stream_post
    sta dma_src_bank
    lda stream_hi
    sta dma_src_hi
    jmp stream_addressed
stream_post:
    lda stream_hi
    cmp #$80
    bcs stream_post_upper
    clc
    adc #$80
    sta dma_src_hi
    lda #4
    sta dma_src_bank
    jmp stream_addressed
stream_post_upper:
    clc
    adc #$20
    sta dma_src_hi
    lda #5
    sta dma_src_bank
stream_addressed:
    lda stream_lo
    sta dma_src_lo
    jsr dma
    inc stream_hi
stream_cached:
    ldx stream_pos
    lda $5000,x
    inc stream_pos
    rts
dec_remaining:
    lda remaining
    bne !+
    dec remaining+1
!:
    dec remaining
    lda remaining
    ora remaining+1
    rts

// Logical PRE is bank5:0000..9c57. Logical POST is split at8000:
// bank4:8000..ffff and bank5:a000..bc57. Never use unmapped bank6.
store_snapshot:
    lda capture_bank
    cmp #4
    beq store_post
    lda #5
    sta dma_dst_bank
    jmp dma
store_post:
    lda dma_dst_hi
    cmp #$80
    bcc !+
    jmp store_post_upper
!:
    // First portion may cross the logical8000 boundary (grid region).
    sec
    lda #0
    sbc dma_dst_lo
    sta split_length
    lda #$80
    sbc dma_dst_hi
    sta split_length+1
    lda dma_len_hi
    cmp split_length+1
    bcs !+
    jmp store_post_low
!:
    bne store_split
    lda dma_len_lo
    cmp split_length
    bcs !+
    jmp store_post_low
!:
store_split:
    sec
    lda dma_len_lo
    sbc split_length
    sta split_rest
    lda dma_len_hi
    sbc split_length+1
    sta split_rest+1
    lda split_length
    sta dma_len_lo
    lda split_length+1
    sta dma_len_hi
    lda dma_dst_hi
    clc
    adc #$80
    sta dma_dst_hi
    lda #4
    sta dma_dst_bank
    jsr dma
    lda split_rest
    ora split_rest+1
    beq store_finished
    clc
    lda dma_src_lo
    adc split_length
    sta dma_src_lo
    lda dma_src_hi
    adc split_length+1
    sta dma_src_hi
    bcc !+
    inc dma_src_bank
!:
    lda split_rest
    sta dma_len_lo
    lda split_rest+1
    sta dma_len_hi
    lda #0
    sta dma_dst_lo
    lda #$a0
    sta dma_dst_hi
    lda #5
    sta dma_dst_bank
    jmp dma
store_post_low:
    lda dma_dst_hi
    clc
    adc #$80
    sta dma_dst_hi
    lda #4
    sta dma_dst_bank
    jmp dma
store_post_upper:
    clc
    adc #$20
    sta dma_dst_hi
    lda #5
    sta dma_dst_bank
    jmp dma
store_finished:
    rts
split_length: .word 0
split_rest: .word 0
