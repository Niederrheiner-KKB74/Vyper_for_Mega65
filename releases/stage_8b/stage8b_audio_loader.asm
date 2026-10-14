// Transient sound loader in future RRB screen; invoked only before game init.
// Saved in Attic2C000 and restored after BASIC video on exit for repeated RUN.
.import source "audio_file.inc"
.const STAGE=$6800
.const CHECK=$6900
*=$5000 "Stage8b phase-shared loader image, then BASIC colour backup"
.pseudopc $a000 {
.namespace audioboot {
 jmp enter
 jmp install
enter:
 lda #0
 sta error
 lda #$ff
 sta crc
 sta crc+1
 jsr probe_attic
 lda error
 bne !failed+
 jsr load_archive
!failed:
 lda error
 beq !ok+
 lda #10
 sta s3b.error
 lda #<$9d61
 sta s3b.name_ptr
 lda #>$9d61
 sta s3b.name_ptr+1
 lda error
 sta audio8.error
 rts
!ok:
 // Save bootstrap only after all its descriptor/selfmodified fields are coherent.
 lda #0
 sta src_mb
 sta src_lo_dma
 sta src_bank_dma
 sta dst_lo_dma
 sta count
 lda #$e0
 sta src_hi_dma
 lda #$80
 sta dst_mb
 lda #$c0
 sta dst_hi_dma
 lda #2
 sta dst_bank_dma
 lda #16
 sta count+1
 jsr dma_copy
 rts
install:
 lda #$80
 sta src_mb
 lda #0
 sta src_lo_dma
 sta dst_mb
 sta dst_lo_dma
 sta count
 lda #2
 sta src_hi_dma
 lda #3
 sta src_bank_dma
 lda #$e0
 sta dst_hi_dma
 lda #1
 sta dst_bank_dma
 lda #24
 sta count+1
 jsr dma_copy
 rts
// Distinct sentinels above/below256KiB detect aliasing with the existing menu.
probe_attic:
 lda #0
 sta src_mb
 sta src_bank_dma
 sta dst_lo_dma
 sta count+1
 lda #32
 sta count
 lda #$80
 sta dst_mb
 lda #<(probe_low+$4000)
 sta src_lo_dma
 lda #>(probe_low+$4000)
 sta src_hi_dma
 lda #$b0
 sta dst_hi_dma
 lda #2
 sta dst_bank_dma
 jsr dma_copy
 lda #<(probe_high+$4000)
 sta src_lo_dma
 lda #>(probe_high+$4000)
 sta src_hi_dma
 lda #6
 sta dst_bank_dma
 jsr dma_copy
 lda #$80
 sta src_mb
 lda #0
 sta dst_mb
 sta src_lo_dma
 sta dst_lo_dma
 sta dst_bank_dma
 lda #$b0
 sta src_hi_dma
 lda #2
 sta src_bank_dma
 lda #>CHECK
 sta dst_hi_dma
 jsr dma_copy
 ldx #31
!low:
 lda CHECK,x
 cmp probe_low,x
 bne !bad+
 dex
 bpl !low-
 lda #6
 sta src_bank_dma
 jsr dma_copy
 ldx #31
!high:
 lda CHECK,x
 cmp probe_high,x
 bne !bad+
 dex
 bpl !high-
 rts
!bad:
 lda #3
 sta error
 rts
probe_low: .fill 32,i+1
probe_high: .fill 32,255-i
full_speed:
 lda $d031
 ora #$40
 sta $d031
 lda $d054
 ora #$40
 sta $d054
 rts
load_archive:
 lda #0
 sta offset
 sta offset+1
 lda #3
 sta offset+2
 lda #<AUDIO_FILE_BYTES
 sta remaining
 lda #>(AUDIO_FILE_BYTES&$ffff)
 sta remaining+1
 lda #AUDIO_FILE_BYTES>>16
 sta remaining+2
 lda #2
 ldx pal.device
 cpx #8
 bcs !device+
 ldx #8
!device:
 ldy #2

 pha
 lda #$ba
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 lda #0
 ldx #0

 pha
 lda #$6b
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 lda #12
 ldx #<$9d61
 ldy #>$9d61

 pha
 lda #$bd
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call

 pha
 lda #$c0
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 bcc !open+
 jmp load_failed
!open:
 ldx #2

 pha
 lda #$c6
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 bcc !read+
 jmp load_failed
!read:
 lda #0
 sta chunk
!byte:

 pha
 lda #$cf
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 ldx chunk
 sta STAGE,x
 jsr crc_byte

 pha
 lda #$b7
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 sta io_status
 and #$bf
 beq !status+
 jmp load_failed
!status:
 lda remaining
 bne !dec+
 lda remaining+1
 bne !middle+
 dec remaining+2
!middle:
 dec remaining+1
!dec:
 dec remaining
 inc chunk
 lda remaining
 ora remaining+1
 ora remaining+2
 beq !last+
 lda io_status
 and #$40
 beq !more+
 jmp load_failed
!more:
 lda chunk
 bne !byte-
 jsr archive_page
 lda error
 bne load_close
 jmp !read-
!last:
 lda io_status
 and #$40
 beq load_failed
 jsr archive_page
 lda crc
 cmp #<AUDIO_FILE_CRC
 bne load_failed
 lda crc+1
 cmp #>AUDIO_FILE_CRC
 beq load_close
load_failed:
 lda #1
 sta error
load_close:

 pha
 lda #$cc
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 lda #2

 pha
 lda #$c3
 sta audio8.rom_jsr+1
 pla
 jsr audio8.rom_call
 lda error
 bne !done+
 jsr full_speed
 jsr verify_archive
!done:
 rts
// Second whole-archive pass catches capacity aliasing between pages/banks.
verify_archive:
 lda #0
 sta offset
 sta offset+1
 lda #3
 sta offset+2
 lda #$ff
 sta crc
 sta crc+1
!page:
 lda #0
 sta count
 lda #1
 sta count+1
 lda offset+2
 cmp #(AUDIO_FILE_BYTES+$30000)>>16
 bne !full+
 lda offset+1
 cmp #>(AUDIO_FILE_BYTES&$ffff)
 bne !full+
 lda #<AUDIO_FILE_BYTES
 sta count
 lda #0
 sta count+1
!full:
 lda #$80
 sta src_mb
 lda #0
 sta src_lo_dma
 sta dst_mb
 sta dst_lo_dma
 sta dst_bank_dma
 lda offset+1
 sta src_hi_dma
 lda offset+2
 sta src_bank_dma
 lda #>CHECK
 sta dst_hi_dma
 jsr dma_copy
 ldx #0
!byte:
 lda CHECK,x
 jsr crc_byte
 inx
 cpx count
 bne !byte-
 lda count
 bne !finish+
 inc offset+1
 bne !page-
 inc offset+2
 jmp !page-
!finish:
 lda crc
 cmp #<AUDIO_FILE_CRC
 bne !bad+
 lda crc+1
 cmp #>AUDIO_FILE_CRC
 bne !bad+
 rts
!bad:
 lda #3
 sta error
 rts
archive_page:
 lda offset+2
 cmp #3
 bne !data+
 lda offset+1
 bne !data+
 ldx #31
!header:
 lda STAGE,x
 cmp expected_header,x
 beq !next+
 lda #1
 sta error
 rts
!next:
 dex
 bpl !header-
!data:
 // Check exact Attic boundary, copy then read back into CHECK and compare.
 lda offset+2
 cmp #6
 bcc !range+
 lda #3
 sta error
 rts
!range:
 lda #0
 sta src_mb
 sta src_lo_dma
 sta src_bank_dma
 lda #>STAGE
 sta src_hi_dma
 lda #$80
 sta dst_mb
 lda offset
 sta dst_lo_dma
 lda offset+1
 sta dst_hi_dma
 lda offset+2
 sta dst_bank_dma
 lda chunk
 sta count
 lda #0
 sta count+1
 lda chunk
 bne !partial+
 inc count+1
!partial:
 jsr dma_copy
 lda #$80
 sta src_mb
 lda offset
 sta src_lo_dma
 lda offset+1
 sta src_hi_dma
 lda offset+2
 sta src_bank_dma
 lda #0
 sta dst_mb
 sta dst_lo_dma
 sta dst_bank_dma
 lda #>CHECK
 sta dst_hi_dma
 jsr dma_copy
 ldx #0
!verify:
 lda STAGE,x
 cmp CHECK,x
 bne !bad+
 inx
 cpx chunk
 bne !verify-
 inc offset+1
 bne !done+
 inc offset+2
!done:
 rts
!bad:
 lda #3
 sta error
 rts
crc_byte:
 eor crc+1
 sta crc+1
 ldy #8
!bit:
 asl crc
 rol crc+1
 bcc !next+
 lda crc
 eor #$21
 sta crc
 lda crc+1
 eor #$10
 sta crc+1
!next:
 dey
 bne !bit-
 rts
// Enhanced F018A: explicit source/destination MB, no stale descriptor options.
dma_copy:
 php
 sei
 lda #0
 sta $d702
 sta $d704
 lda #>(dma_list+$4000)
 sta $d701
 lda #<(dma_list+$4000)
 sta $d705
 plp
 rts
dma_list:
 .byte $80
src_mb: .byte 0
 .byte $81
dst_mb: .byte 0
 .byte $0a,0
dma_command: .byte 0
count: .word 0
src_lo_dma: .byte 0
src_hi_dma: .byte 0
src_bank_dma: .byte 0
dst_lo_dma: .byte 0
dst_hi_dma: .byte 0
dst_bank_dma: .byte 0
 .word 0

expected_header: .import binary "audio_header.bin"
error: .byte 0
crc: .word 0
chunk: .byte 0
io_status: .byte 0
remaining: .fill 3,0
offset: .fill 3,0
.if (*>$a700) { .error "Transient audio loader image overlaps Level parser" }
}

}
