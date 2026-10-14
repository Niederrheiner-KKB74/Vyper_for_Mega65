// Runs below ROMA, with exactly the stable KERNAL/IRQ mapping and SETBNK path.
// Shared SEQ code verifies every DMA chunk by bytewise readback.
.namespace fireload {
load:
    jsr pal.load
    lda s3b.error
    bne done
    lda #0
    sta s3b.total_crc
    sta s3b.total_crc+1
    sta s3b.remain+2
    lda #>F_BASE // resident physical RAM B000..B45B, below starfield B480
    sta s3b.target_hi
    lda #0
    sta s3b.target_bank
    lda #<F_BYTES
    sta s3b.remain
    lda #>F_BYTES
    sta s3b.remain+1
    lda #<filename
    sta s3b.name_ptr
    lda #>filename
    sta s3b.name_ptr+1
    lda #12
    sta s3b.name_len
    jsr s3b.load_file
    lda s3b.error
    bne done
    lda s3b.io_status
    and #$40
    beq bad
    lda s3b.total_crc
    cmp #<F_SUM
    bne bad
    lda s3b.total_crc+1
    cmp #>F_SUM
    bne bad
    lda #0
    sta s3b.dma_src_lo
    sta s3b.dma_dst_lo
    sta s3b.dma_dst_bank
    sta s3b.dma_len_hi
    sta s3b.dma_src_bank // A=0: physical bank0, also while ROMA is mapped
    lda #>F_BASE
    sta s3b.dma_src_hi
    lda #$69
    sta s3b.dma_dst_hi
    lda #16
    sta s3b.dma_len_lo
    jsr s3b.dma_copy
    ldx #15
!header:
    lda $6900,x
    cmp expected,x
    bne bad
    dex
    bpl !header-
    jsr verify_all
done:
    rts
bad:
    lda #10 // VYSH checksum/header/exact-length error; same clean common failure exit
    sta s3b.error
    rts
}
