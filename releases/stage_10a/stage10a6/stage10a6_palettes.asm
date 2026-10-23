// Stage5c: original RGB4, isolated NCM subpalette, no writes to DOS or ROM.
.namespace pal {
.const DATA=$6d00
.const HIGH=$5c300
.label palette_id=$6ef0
.label old_x=$6ef1
.label low_word=$6ef2
.label device=$6ef3
*=$6b00 "Stage5c VYCL loader, validation and level palette"
capture_device:
    lda $ba // KERNAL device used for the program LOAD.
    cmp #8
    bcs !store+
    lda #8 // Direct SYS without a disk LOAD: previous engine default.
!store:
    sta device
    rts
load:
    lda #0
    sta s3b.total_crc
    sta s3b.total_crc+1
    sta s3b.remain+2
    lda #<filename
    sta s3b.name_ptr
    lda #>filename
    sta s3b.name_ptr+1
    lda #12
    sta s3b.name_len
    lda #$dc
    sta s3b.remain
    lda #1
    sta s3b.remain+1
    lda #5
    sta s3b.target_bank
    lda #$c3
    sta s3b.target_hi
    jsr s3b.load_file
    lda s3b.error
    beq !loaded+
    rts
!loaded:
    lda s3b.io_status
    and #$40 // VYCL must end exactly at byte476, no trailing payload.
    bne !length+
    jmp invalid
!length:
    lda s3b.total_crc
    cmp #$1b
    beq !ok+
    jmp invalid
!ok:
    lda s3b.total_crc+1
    cmp #$3a
    beq !ok+
    jmp invalid
!ok:
    lda #0
    sta s3b.dma_src_lo
    sta s3b.dma_dst_bank
    lda #$c3
    sta s3b.dma_src_hi
    lda #5
    sta s3b.dma_src_bank
    lda #<DATA
    sta s3b.dma_dst_lo
    lda #>DATA
    sta s3b.dma_dst_hi
    lda #$dc
    sta s3b.dma_len_lo
    lda #1
    sta s3b.dma_len_hi
    jsr s3b.dma_copy
validate:
    ldx #13
header_loop:
    lda DATA,x
    cmp header,x
    beq !ok+
    jmp invalid
!ok:
    dex
    bpl header_loop
    ldx #99
indices:
    lda DATA+16,x
    cmp #20
    bcc !ok+
    jmp invalid
!ok:
    dex
    bpl indices
    // Every RGB4 word high byte must have its high nibble clear.
    ldx #1
words_first:
    lda DATA+116,x
    and #$f0
    beq !ok+
    jmp invalid
!ok:
    inx
    inx
    cpx #1
    bne words_first
    ldx #1
words_last:
    lda DATA+372,x
    and #$f0
    beq !ok+
    jmp invalid
!ok:
    inx
    inx
    cpx #105
    bne words_last
    // Payload sum checked separately from the pinned full-file sum.
    lda #0
    sta sum
    sta sum+1
    ldx #0
sum_first:
    lda DATA+16,x
    jsr add_sum
    inx
    bne sum_first
sum_last:
    lda DATA+272,x
    jsr add_sum
    inx
    cpx #204
    bne sum_last
    lda sum
    cmp DATA+14
    beq !ok+
    jmp invalid
!ok:
    lda sum+1
    cmp DATA+15
    beq !ok+
    jmp invalid
!ok:
return:
    rts
invalid:
    lda #7 // Invalid VYCL header/index/RGB4/checksum.
    sta s3b.error
    rts
add_sum:
    clc
    adc sum
    sta sum
    bcc !done+
    inc sum+1
!done:
    rts
apply:
    // Called after palette initialization and before every new level is drawn.
    ldx level.number
    dex
    lda DATA+16,x
    sta palette_id // Readable via monitor; no raster-time debug output.
    tax
    lda palette_lo,x
    sta read_word+1
    lda palette_hi,x
    sta read_word+2
    lda VIC_PALSEL
    pha
    and #$3f
    ora #$40 // Map bank1; retain primary, sprite and alternate selectors.
    sta VIC_PALSEL
    ldx #$11
    ldy #0
apply_loop:
    jsr read_word
    sta low_word
    and #15
    jsr expand
    sta $d300,x
    lda low_word
    lsr
    lsr
    lsr
    lsr
    jsr expand
    sta $d200,x
    iny
    jsr read_word
    jsr expand
    sta $d100,x
    iny
    inx
    cpx #$19
    bne apply_loop
    // Transparent nibble0 stays transparent; deterministic unused subpalette entries.
    lda #0
    sta $d110
    sta $d210
    sta $d310
    pla
    sta VIC_PALSEL
    jsr cc_publish // reapply same cycle phase after level palette
    rts
read_word:
    lda $ffff,y
    rts
expand:
    sta nibble
    asl
    asl
    asl
    asl
    ora nibble
    rts
// Glyph colour byte1's upper nibble selects NCM colours16..31.
// Stage10a3: enemy explosions (always staged in private buffers) use the
// current level palette like the original; explosion nibbles 2/5/7/8 follow the
// same plane+1 convention as enemies. Direct explosion glyphs305..31f are only
// used for the player and stay on the fixed grey colours0..15.
glyph_colour:
    lda v014_top_hi
    cmp #5
    bcs enemy // private pixie buffers: enemy frames and enemy explosions
    cmp #2
    beq enemy
    cmp #3
    bne fixed
    lda v014_top_lo
    cmp #$24
    bcs enemy // Test enemy/crop glyphs; player321..323 and explosions305..31f fixed.
fixed:
    lda #0
    rts
enemy:
    lda #$10
    rts
    .fill 16,$ea // removed EXP test; keep Stage10a2 addresses unchanged
filename: .text "VYCL.DAT,S,R"
.byte 0
header: .import binary "VYCL.DAT",0,14
palette_lo: .fill 20, <(DATA+116+i*18)
palette_hi: .fill 20, >(DATA+116+i*18)
sum: .word 0
nibble: .byte 0
.if (* > $6d00) { .error "Stage5c palette code overlaps state/data" }
*=$6ef0 "Stage5c palette state"
.fill 4,0
*=$6d00 "Stage5c validated VYCL low-RAM mirror"
.fill 476,0
.if (DATA+476 > $6f80) { .error "VYCL mirror overlaps attack metadata" }
}
