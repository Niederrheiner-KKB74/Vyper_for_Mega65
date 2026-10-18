// Stage10a2: streaming ZX0 (v2) decoder for packed SEQ files.
//
// The two existing load loops (s3b.load_file and the audio loader) keep their
// structure. Only their KERNAL calls are replaced, with identical footprints:
//   SETNAM -> unpack.setnam / unpack.setnam_rom   (resets the decoder)
//   CHRIN  -> unpack.chrin                        (returns the next DECODED byte)
//   READST -> unpack.readst                       (virtual status: $40 exactly
//                                                  after the last decoded byte)
// Decoded bytes are identical to the original DAT files, so every existing
// length, CRC, sum and read-back check stays valid unchanged.
//
// Packed file: "Z0", total(24), plain(24), ZX0 v2 stream (tools/pack_stage10a2.py).
//   total = decoded length, plain = leading bytes that are NOT delta coded;
//   later bytes are delta coded: out[i] = out[i-1] + d[i] (VYSO PCM).
// ZX0 offsets never exceed 32640. A 64 KB ring wraps with plain 16-bit
// arithmetic: free Attic $080B0000-$080BFFFF (Attic is in use up to $080A063F).
//
// Location: unused tail of the title bootstrap ($4000-$47FF). That region is not
// touched before titlecache.tc_save (after the last file load) and is restored
// from Attic on every BASIC exit, so repeated RUN keeps a valid decoder.
// Entries preserve X, Y and Z; IRQs are masked only while B is switched.
.namespace unpack {
.const ST_HEADER=0
.const ST_LIT=1
.const ST_MATCH=2
.const VSTATUS_ERROR=$02 // reported like a read timeout: every loader treats it as fatal
.label ring_bp=$47       // base page of the two 32-bit ring pointers
.label wptr=$47f8        // ring write pointer: lo, hi, $0b, $08
.label rptr=$47fc        // ring read pointer for matches

setnam:
    jsr reset
    jmp $ffbd
setnam_rom:
    jsr reset
    inc rawmode          // audio loader: KERNAL only through audio8.rom_call
    pha
    lda #$bd
    sta audio8.rom_jsr+1
    pla
    jmp audio8.rom_call

reset:
    php
    pha
    .byte $da            // PHX
    lda #0               // ring position is arbitrary: matches are relative to wptr
    ldx #vars_end-vars-1
!clear:
    sta vars,x
    dex
    bpl !clear-
    inc off              // ZX0 initial offset 1
    .byte $fa            // PLX
    pla
    plp
    rts

readst:
    lda left
    ora left+1
    ora left+2
    php
    lda rawst
    and #$bf             // the real EOF belongs to the packed file, not to the data
    ora err
    plp
    bne !more+
    ora #$40
!more:
    rts

chrin:
    php
    .byte $da,$5a        // PHX, PHY (Z leaves as 0, the KERNAL calling convention)
    jsr next
    sta outb
    .byte $7a,$fa        // PLY, PLX
    plp
    lda outb
    rts

next:
    lda state
    bne !running+
    jsr raw_byte         // header: "Z0" (checked by the packer), total(24), plain(24)
    jsr raw_byte
!header:
    jsr raw_byte
    ldx outb
    sta left,x
    inx
    stx outb
    cpx #6
    bne !header-
    ldx #ST_LIT
    jmp new_count
!running:
loop:
    lda err
    bne fail
    lda cnt
    ora cnt+1
    beq decide
    lda cnt
    bne !low+
    dec cnt+1
!low:
    dec cnt
    lda state
    lsr                  // C=1: literal, C=0: match
    ldx #1
    bcc !match+
    jsr raw_byte
    ldx #0
!match:
    jsr ring             // X=0: store A, X=1: copy from rptr
    sta outb
    ldx #plain-left
    jsr dec24            // C=1 while still inside the plain (non-delta) part
    lda outb
    bcs !store+
    adc acc              // C=0 here
!store:
    sta acc
    ldx #0
    jsr dec24
    lda acc
    rts
bad:
    lda #VSTATUS_ERROR
    sta err
fail:
    lda #0
    rts

decide:
    lda state
    pha
    jsr read_bit
    pla
    bcs new_offset
    ldx #ST_LIT          // after a match: 0 = literals
    cmp #ST_LIT
    bne new_count
    ldx #ST_MATCH        // after literals: 0 = repeat last offset
new_count:
    stx state
    lda #0
    jsr gamma
count_ready:
    lda g
    sta cnt
    lda g+1
    sta cnt+1
    lda wptr             // harmless for literals, required for matches
    sec
    sbc off
    sta rptr
    lda wptr+1
    sbc off+1
    sta rptr+1
    jmp loop
new_offset:
    lda #1
    jsr gamma
    lda g+1
    beq !offset+
    jmp bad              // 256 is the end marker: never valid before "total" bytes
!offset:
    lda g
    lsr
    sta off+1
    lda #0
    ror
    sta off              // off = g*128
    jsr raw_byte
    lsr
    sta outb
    lda off
    sec
    sbc outb
    sta off
    bcs !hi+
    dec off+1
!hi:
    inc back             // next bit is bit0 of the offset byte
    lda #ST_MATCH
    sta state
    lda #0
    jsr gamma
    inc g
    bne count_ready
    inc g+1
    bne count_ready
    jmp bad

// Interlaced Elias gamma into g. A=1 inverts the data bits (ZX0 v2 offset MSB).
gamma:
    sta inv
    lda #1
    sta g
    lda #0
    sta g+1
!next:
    jsr read_bit
    bcs !done+
    jsr read_bit
    lda #0
    rol
    eor inv
    lsr
    rol g
    rol g+1
    bcc !next-
    jmp bad              // longer than 16 bits: corrupt stream
!done:
    rts

// Next stream bit in C.
read_bit:
    lsr back
    bcc !normal+
    lda lastraw
    lsr
    rts
!normal:
    lsr mask
    bne !have+
    jsr raw_byte
    sta val
    sec
    ror mask
!have:
    lda val
    and mask
    cmp #1
    rts

// Next byte of the packed file; accumulates the real KERNAL status.
raw_byte:
    bit rawst
    bvc !open+
    jmp bad              // packed file ended too early
!open:
    lda #$cf
    jsr kernal
    sta lastraw
    lda #$b7
    jsr kernal
    ora rawst
    sta rawst
    lda lastraw
    rts
kernal:
    ldx rawmode
    beq !direct+
    sta audio8.rom_jsr+1
    jmp audio8.rom_call
!direct:
    sta kjump+1
kjump:
    jmp $ffcf

// 24-bit decrement of left+X; C=0 (unchanged) if the counter is already zero.
dec24:
    lda left,x
    ora left+1,x
    ora left+2,x
    bne !nz+
    clc
    rts
!nz:
    lda left,x
    bne !l0+
    lda left+1,x
    bne !l1+
    dec left+2,x
!l1:
    dec left+1,x
!l0:
    dec left,x
    sec
    rts

// X=0: ring[wptr++]=A. X=1: A=ring[rptr++], ring[wptr++]=A. Returns A.
ring:
    php
    sei
    sta rbyte
    .byte $7b            // TBA
    pha
    lda #ring_bp
    .byte $5b            // TAB
    .byte $a3,$00        // LDZ #0
    txa
    beq !put+
    .byte $ea,$b2,<rptr  // LDA [rptr],Z
    sta rbyte
    inc rptr
    bne !put+
    inc rptr+1
!put:
    lda rbyte
    .byte $ea,$92,<wptr  // STA [wptr],Z
    inc wptr
    bne !done+
    inc wptr+1
!done:
    pla
    .byte $5b            // TAB
    lda rbyte
    plp
    rts

vars:
state: .byte 0
cnt: .word 0
off: .word 1
g: .word 0
inv: .byte 0
mask: .byte 0
val: .byte 0
back: .byte 0
lastraw: .byte 0
rawst: .byte 0
rawmode: .byte 0
err: .byte 0
left: .fill 3,0
plain: .fill 3,0
acc: .byte 0
outb: .byte 0
vars_end:
rbyte: .byte 0
}
