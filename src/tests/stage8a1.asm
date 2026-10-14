// Issue69: standalone Signed8 PCM DMA channel0. No game/loader imports.
.import source "sample17.inc"
.const SAMPLE=$4000
.const SAMPLE_END=SAMPLE+SAMPLE_BYTES
.if (SAMPLE_BYTES!=6720 || SAMPLE_END>$6000 || SAMPLE_END<=$4000) { .error "Invalid PCM resource range" }
.if ((SAMPLE>>16)!=((SAMPLE_END-1)>>16)) { .error "Sample crosses64KiB end-comparison bank" }
*=$2001 "BASIC SYS8448"
BasicUpstart($2100)
*=$2100 "Stage8a1 PCM controller"
entry:
    php
    sei
    cld
    lda $d02f
    sta old_key
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    lda $d030
    sta old_d030
    lda $d031
    sta old_d031
    lda $d054
    sta old_d054
    cli
    ldx #<message
    ldy #>message
    jsr puts
    sei
    lda #0
    sta error
    sta configured
    sta playing
    sta armed
    sta play_count
    lda old_d030
    and #$fe
    sta $d030
    lda old_d031
    ora #$40 // FAST AND VFAST, not3.5MHz alone
    sta $d031
    lda old_d054
    ora #$40
    sta $d054
    lda $d614
    sta old_query
    lda $dc02
    sta old_ddra
    lda #0 // port2 input; retain CIA output latch, restore DDR on exit
    sta $dc02
    lda $fb
    sta old_zp
    lda $fc
    sta old_zp+1
    jsr checksum
    lda crc
    cmp #<SAMPLE_CRC
    bne bad_crc
    lda crc+1
    cmp #>SAMPLE_CRC
    bne bad_crc
    // Never resume a partially interrupted foreign DMA stream at a false position.
    ldx #0
check_idle:
    lda $d720,x
    and #$88
    cmp #$80
    beq busy_error
    txa
    clc
    adc #16
    tax
    cpx #64
    bne check_idle
    jsr audio_save
    jsr audio_init
    bcc main_loop
    lda #3
    sta error
    jmp exit
bad_crc:
    lda #1
    sta error
    jmp exit
busy_error:
    lda #2
    sta error
    jmp exit
main_loop:
    jsr poll_audio
    lda error
    bne exit
    // Consume ASCII repeat events, but only X acts on the FIFO.
    lda $d610
    beq read_trigger
    sta $d610
    cmp #$58
    beq exit
    cmp #$78
    beq exit
read_trigger:
    lda #7 // documented matrix column7,row4 = SPACE, active-low
    sta $d614
    lda $d613
    and #$10
    beq pressed
    lda $dc00 // joystick PORT2 fire, active-low
    and #$10
    beq pressed
    lda #1
    sta armed
    jmp main_loop
pressed:
    lda armed
    beq main_loop
    lda #0
    sta armed // consume press even if sound still playing; no hidden queued replay
    lda playing
    bne main_loop
    jsr play
    jmp main_loop
exit:
    lda configured
    beq restore_io
    jsr audio_restore
restore_io:
    lda old_ddra
    sta $dc02
    lda old_query
    sta $d614
    lda old_zp
    sta $fb
    lda old_zp+1
    sta $fc
    lda old_d054
    sta $d054
    lda old_d031
    sta $d031
    lda old_d030
    sta $d030
    jsr restore_key
    plp
    lda error
    beq normal_exit
    cmp #1
    beq crc_message
    cmp #2
    beq busy_message
    cmp #3
    beq init_message
    ldx #<timeout_msg
    ldy #>timeout_msg
    jmp puts
crc_message:
    ldx #<crc_msg
    ldy #>crc_msg
    jmp puts
busy_message:
    ldx #<busy_msg
    ldy #>busy_msg
    jmp puts
init_message:
    ldx #<init_msg
    ldy #>init_msg
    jmp puts
normal_exit:
    rts
restore_key:
    lda old_key
    cmp #$53
    bne !eth+
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    rts
!eth:
    cmp #$54
    bne !c65+
    lda #$45
    sta $d02f
    lda #$54
    sta $d02f
    rts
!c65:
    cmp #$96
    bne !legacy+
    lda #$a5
    sta $d02f
    lda #$96
!legacy:
    sta $d02f
    rts
// All256 mixer bytes are readable crossbar coefficients; unity=FFFF is endian-independent.
audio_save:
    lda $d711
    sta old_global
    lda $d6f4
    sta old_mixer_select
    ldx #12
!channel:
    lda $d720,x
    sta old_channel,x
    dex
    bpl !channel-
    ldx #0
!mixer:
    stx $d6f4
    lda $d6f5
    sta old_mixer,x
    inx
    bne !mixer-
    lda #1
    sta configured
    rts
audio_init:
    lda #2 // disabled, Signed8, no loop; bit5 UNSIGNED remains clear
    sta $d720
    ldx #0
    lda #0
!mute:
    stx $d6f4
    sta $d6f5
    cmp $d6f5
    beq !mute_ok+
    sec
    rts
!mute_ok:
    inx
    bne !mute-
    ldx #15
!route:
    lda unity_indices,x
    sta $d6f4
    lda #$ff
    sta $d6f5
    cmp $d6f5
    beq !route_ok+
    sec
    rts
!route_ok:
    dex
    bpl !route-
    lda #$80 // AUDEN, NOMIX=0; crossbar supplies fixed mono on L/R
    sta $d711
    jsr parameters
    // Readback while disabled: reject unsupported or mis-mapped I/O before enabling.
    ldx #12
!verify:
    lda $d720,x
    cpx #0
    bne !compare+
    and #$f7 // tolerate a read-only STP flag on disabled hardware
!compare:
    cmp parameters_image,x
    bne !bad+
    dex
    bpl !verify-
    lda $d711
    cmp #$80
    bne !bad+
    lda $d031
    and #$40
    beq !bad+
    lda $d054
    and #$40
    beq !bad+
    clc
    rts
!bad:
    sec
    rts
parameters:
    ldx #12
!copy:
    lda parameters_image,x
    sta $d720,x // CTRL is written last; disabled throughout configuration
    dex
    bpl !copy-
    rts
play:
    lda #2
    sta $d720
    jsr parameters
    lda $d7fa // physical frame count, not IRQ-driven software clock
    sta last_frame
    lda #100 // ~2s PAL watchdog; expected sample duration0.6745s
    sta timeout
    lda #1
    sta playing
    inc play_count
    lda #$82 // EN |8bit; no UNSIGNED/no LOOP/no STP
    sta $d720
    rts
poll_audio:
    lda playing
    beq !done+
    lda $d720
    and #8
    beq !watch+
    lda #2
    sta $d720
    lda #0
    sta $d729
    sta playing
!done:
    rts
!watch:
    lda $d7fa
    cmp last_frame
    beq !done-
    sta last_frame
    dec timeout
    bne !done-
    lda #4
    sta error
    rts
audio_restore:
    lda #2
    sta $d720 // stop owned channel FIRST, then restore saved disabled/stopped state
    lda #0
    sta $d729
    ldx #0
!mixer:
    stx $d6f4
    lda old_mixer,x
    sta $d6f5
    inx
    bne !mixer-
    ldx #12
!channel:
    lda old_channel,x
    sta $d720,x // CTRL last; active foreign streams were rejected before save
    dex
    bpl !channel-
    lda old_global
    sta $d711
    lda old_mixer_select
    sta $d6f4
    rts
checksum:
    lda #<SAMPLE
    sta $fb
    lda #>SAMPLE
    sta $fc
    lda #$ff
    sta crc
    sta crc+1
    ldy #0
!byte:
    lda ($fb),y
    eor crc+1
    sta crc+1
    ldx #8
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
    dex
    bne !bit-
    inc $fb
    bne !pointer+
    inc $fc
!pointer:
    lda $fb
    cmp #<SAMPLE_END
    bne !byte-
    lda $fc
    cmp #>SAMPLE_END
    bne !byte-
    rts
puts:
    stx text_read+1
    sty text_read+2
    ldy #0
text_read:
    lda $ffff,y
    beq !done+
    jsr $ffd2
    iny
    bne text_read
!done:
    rts
parameters_image:
    .byte $02 // disabled Signed8, no loop
    .byte <SAMPLE,>SAMPLE,0 // loop pointer defined, unused
    .byte <SAMPLE_RATE,>(SAMPLE_RATE&$ffff),SAMPLE_RATE>>16
    .word SAMPLE_END // exclusive end; final fetch is5A3F, stop at5A40
    .byte $40 // moderate25% channel volume
    .byte <SAMPLE,>SAMPLE,0 // current sample position
unity_indices: .byte $10,$11,$30,$31,$d0,$d1,$f0,$f1,$1e,$1f,$3e,$3f,$de,$df,$fe,$ff
.encoding "petscii_upper"
message: .text "STAGE 8A1 - ORIGINAL VYPER PCM"
    .byte 13
    .text "SOUND 17 / PAULA PER 356 / 9963 HZ"
    .byte 13
    .text "SPACE OR JOYSTICK PORT2 FIRE: PLAY ONCE"
    .byte 13
    .text "RELEASE BEFORE REPLAY. X: BASIC"
    .byte 13
    .byte 0
crc_msg: .byte 13
    .text "PCM CRC ERROR - RELOAD ORIGINAL PRG"
    .byte 13
    .byte 0
busy_msg: .byte 13
    .text "DMA BUSY - STOP OTHER AUDIO FIRST"
    .byte 13
    .byte 0
init_msg: .byte 13
    .text "AUDIO DMA REGISTER INIT ERROR"
    .byte 13
    .byte 0
timeout_msg: .byte 13
    .text "AUDIO DMA TIMEOUT - CHECK CORE/SPEED"
    .byte 13
    .byte 0
old_key: .byte 0
old_d030: .byte 0
old_d031: .byte 0
old_d054: .byte 0
old_query: .byte 0
old_ddra: .byte 0
old_zp: .word 0
old_global: .byte 0
old_mixer_select: .byte 0
old_channel: .fill 13,0
old_mixer: .fill 256,0
error: .byte 0
configured: .byte 0
playing: .byte 0
armed: .byte 0
last_frame: .byte 0
timeout: .byte 0
play_count: .byte 0
crc: .word 0
.if (*>$3000) { .error "Controller overlaps reserved gap/sample" }
* = SAMPLE "Original sound17: Signed8 PCM,6720 unchanged bytes"
sample_data: .import binary "sound17.s8"
.if (*!=SAMPLE_END) { .error "PCM resource length mismatch" }
