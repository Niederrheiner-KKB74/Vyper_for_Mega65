// MEGA65 Stage 3a-2 - independent sequential loader + DMA readback verification.
// BASIC 65 RUN / SYS 8448. Stage 2ja is not modified.
.const SETBNK=$ff6b
.const BUF=$6000
.const CHECK=$6100
.const LEVELCOPY=$7000
*=$2001
.word basic_end
.word 10
.byte $9e
.text "8448"
.byte 0
basic_end:
.word 0
*=$2100
start:
    lda #$93
    jsr $ffd2
    ldx #<title
    ldy #>title
    jsr puts
    lda #0
    sta error
    sta total_crc
    sta total_crc+1
    lda #<level_name
    sta name_ptr
    lda #>level_name
    sta name_ptr+1
    lda #12
    sta name_len
    lda #$81
    sta remain
    lda #$3f
    sta remain+1
    lda #$01
    sta remain+2
    // $20000-$3FFFF holds the (write-protected) ROM on the MEGA65.
    // Free chip RAM is $40000-$5FFFF: VYLV -> $40000..$53F80
    lda #$04
    sta target_bank
    lda #0
    sta target_hi
    jsr load_file
    lda error
    beq first_success
    jmp failed
first_success:
    ldx #<level_ok
    ldy #>level_ok
    jsr puts
    lda #0
    sta total_crc
    sta total_crc+1
    lda #<graphic_name
    sta name_ptr
    lda #>graphic_name
    sta name_ptr+1
    lda #12
    sta name_len
    lda #$a8
    sta remain
    lda #$78
    sta remain+1
    lda #0
    sta remain+2
    // VYGR -> $54000..$5B8A7 (directly after VYLV, still free chip RAM)
    lda #$05
    sta target_bank
    lda #$40
    sta target_hi
    jsr load_file
    lda error
    beq second_success
    jmp failed
second_success:
    ldx #<graphic_ok
    ldy #>graphic_ok
    jsr puts
    // Level 1 directory entry: offset $00000328, length $0351 (849 bytes).
    // Copy the complete Level 1 record into low RAM $7000.
    lda #$28
    sta dma_src_lo
    lda #$03
    sta dma_src_hi
    lda #$04            // VYLV now starts at $40000
    sta dma_src_bank
    lda #<LEVELCOPY
    sta dma_dst_lo
    lda #>LEVELCOPY
    sta dma_dst_hi
    lda #0
    sta dma_dst_bank
    lda #$51
    sta dma_len_lo  // $0351 = 849 bytes
    lda #$03
    sta dma_len_hi
    jsr dma_copy
    ldx #0
check_magic:
    lda LEVELCOPY,x
    cmp level_one_signature,x
    bne magic_bad
    inx
    cpx #8
    bne check_magic
    ldx #<dma_ok
    ldy #>dma_ok
    jsr puts
    jmp finished
magic_bad:
    lda #5
    sta error
failed:
    ldx #<error_msg
    ldy #>error_msg
    jsr puts
    lda error
    jsr hex
    lda #13
    jsr $ffd2
    ldx #<status_msg
    ldy #>status_msg
    jsr puts
    lda io_status
    jsr hex
    lda #13
    jsr $ffd2
finished:
    ldx #<done_msg
    ldy #>done_msg
    jsr puts
    rts

load_file:
    lda #0
    sta chunk_size
    sta io_status
    lda #2
    ldx #8
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
    rts
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
    and #$02            // timeout always fatal
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

level_name: .text "VYLV.DAT,S,R"
graphic_name: .text "VYGR.DAT,S,R"
level_one_signature: .byte 1,0,2,22,16,0,2,0
title: .text "VYPER STAGE 3A-2"
.byte 13
.text "FULL SEQ + DMA TEST"
.byte 13,13,0
level_ok: .text "VYLV LOADED + VERIFIED AT $40000"
.byte 13,0
graphic_ok: .text "VYGR LOADED + VERIFIED AT $54000"
.byte 13,0
dma_ok: .text "DMA LEVEL 1 RECORD OK ($7000)"
.byte 13,0
error_msg: .text "ERROR CODE $"
.byte 0
status_msg: .text "READST $"
.byte 0
done_msg: .text "TEST COMPLETE"
.byte 13,0
name_ptr: .word 0
name_len: .byte 0
remain: .byte 0,0,0
target_hi: .byte 0
target_bank: .byte 0
chunk_size: .byte 0
io_status: .byte 0
error: .byte 0
total_crc: .word 0
