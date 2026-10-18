// Issue96: channel0 CURRENT-address latch A/B, standalone native BASIC screen.
#import "sample17.inc"
.const TARGET=$016480
.const TARGET_END=TARGET+SAMPLE_BYTES
.const SENTINEL=$018020
.const MAILBOX=$1fd3
.assert "Sample stays within one 64KiB bank", TARGET>>16 == (TARGET_END-1)>>16, true
*=$2001 "BASIC"
BasicUpstart($2100)
*=$2100 "Audio latch controller"
entry:
 php
 sei
 cld
 tsx
 lda $0101,x
 sta old_p
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
 lda $d614
 sta old_query
 lda $dc02
 sta old_ddra
 lda $fb
 sta old_zp
 lda $fc
 sta old_zp+1
 lda MAILBOX
 sta old_mailbox
 lda #0
 sta owned
 sta playing
 sta variant
 sta attempt
 sta attempt+1
 sta phase
 sta armed
 sta init_error
 sta error_before
 sta error_after
 sta seed_error
 sta start_frame
 sta current
 sta current+1
 sta current+2
 sta observed_start
 sta observed_start+1
 sta observed_start+2
 sta log_header+9
 sta log_header+10
 sta log_header+12
 sta log_header+13
 sta log_header+14
 sta log_header+15
 sta log_header+19
 sta log_header+30
 sta MAILBOX
 lda old_mailbox
 sta log_header+18
 lda old_p
 sta log_header+23
 lda #<records
 sta record_put+1
 lda #>records
 sta record_put+2
initial_text:
 // Initial text only; no KERNAL calls while audio is owned.
 cli
 lda #$93
 jsr $ffd2
 ldx #<message
 ldy #>message
 jsr puts
 sei
 lda old_d030
 and #$fe
 sta $d030
 lda old_d031
 ora #$40
 sta $d031
 lda old_d054
 ora #$40
 sta $d054
 lda #0
 sta $dc02
 // Refuse foreign active voices; test audio IRQ enables are saved then disabled.
 ldx #0
!foreign:
 lda $d720,x
 and #$88
 cmp #$80
 beq refuse
 txa
 clc
 adc #16
 tax
 cpx #64
 bne !foreign-
 jsr audio_save
 jsr mixer_init
 lda init_error
 bne start_failed
 jsr copy_sample
 jsr checksum
 lda crc
 cmp #<SAMPLE_CRC
 bne bad_crc
 lda crc+1
 cmp #>SAMPLE_CRC
 bne bad_crc
 jsr reset_pointer
 lda seed_error
 bne reset_failed
 lda #0
 sta init_error
 jsr draw
 jmp main
refuse:
 lda #2
 bne start_failed
bad_crc:
 lda #1
 bne start_failed
reset_failed:
 lda #6
start_failed:
 sta init_error
 sta log_header+19
 sta MAILBOX
 jsr draw
main:
 jsr poll_audio
 lda $d610
 beq trigger
 sta $d610
 cmp #$58
 beq exit_jump
 cmp #$78
 beq exit_jump
 cmp #$31
 beq choose_a
 cmp #$32
 beq choose_b
 cmp #$50
 beq replay
 cmp #$70
 beq replay
 cmp #$53
 beq stop_key
 cmp #$73
 beq stop_key
 cmp #$47
 beq global_key
 cmp #$67
 beq global_key
 jmp trigger
exit_jump:
 jmp exit
choose_a:
 lda #0
 beq choose
choose_b:
 lda #1
choose:
 sta variant
replay:
 lda init_error
 bne trigger
 jsr start_source
 jsr draw
 jmp main
stop_key:
 lda owned
 beq trigger
 jsr stop
 lda #4
 sta phase
 jsr log_event
 jsr draw
 jmp main
global_key:
 lda #5
 sta phase
 jsr log_event // raw/strict/masked D711 observations only, no control write
 jsr draw
trigger:
 lda #7
 sta $d614
 lda $d613
 and #$10
 beq pressed
 lda $dc00
 and #$10
 beq pressed
 lda #1
 sta armed
 jmp main
pressed:
 lda armed
 bne !+
 jmp main
!:
 lda #0
 sta armed
 jmp replay
exit:
 lda owned
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
 lda old_mailbox
 sta MAILBOX
exit_restored:
 plp
 rts

start_source:
 jsr stop
 inc attempt
 bne !+
 inc attempt+1
!:
 lda #0
 sta MAILBOX
 sta error_before
 sta error_after
 // Full disabled reset including a deliberately different, correctly latched pointer.
 jsr reset_pointer
 lda seed_error
 beq !+
 lda #6
 sta MAILBOX
 sta error_after
 jmp failed_attempt
!:
 lda #0
 sta phase
 jsr log_event // BEFORE: seed pointer, status00
 jsr write_target
 jsr settle
 jsr read_current
 ldx #2
!save:
 lda current,x
 sta observed_start,x
 dex
 bpl !save-
 // Same stopped-channel low/high verification as Stage10a1, plus bank check.
 lda current
 cmp #<TARGET
 bne source_init_error
 lda current+1
 cmp #>(TARGET&$ffff)
 bne source_init_error
 lda current+2
 cmp #TARGET>>16
 bne source_init_error
 lda #0
 beq pointer_checked
source_init_error:
 lda #4 // software diagnostic, NOT a hardware-written error register
pointer_checked:
 sta MAILBOX
 sta error_after
 lda #1
 sta phase
 jsr log_event // LATCHED: coherent pointer before enable
 lda MAILBOX
 bne failed_attempt
 lda #$40 // moderate channel volume25%
 sta $d729
 lda #0
 sta $d72d
 sta $d72e
 sta $d72f // explicit timer latch reset; identical in A and B
 lda $d7fa
 sta last_frame
 sta start_frame
 lda #100
 sta watchdog
 lda #1
 sta playing
 lda #$82 // EN, signed8, no LOOP or STP, UNSIGNED clear
 sta $d720
failed_attempt:
 lda #2
 sta phase
 jmp log_event // AFTER START, including suppressed start on error04

// Only this sequence differs. No repair BANK write after variant A.
write_target:
 lda variant
 bne write_b
write_a:
 lda #TARGET>>16
 sta $d72c
 lda #<TARGET
 sta $d72a
 lda #>(TARGET&$ffff)
 sta $d72b
 rts
write_b:
 lda #<TARGET
 sta $d72a
 lda #>(TARGET&$ffff)
 sta $d72b
 lda #TARGET>>16
 sta $d72c
 rts

reset_pointer:
 lda #2
 sta $d720
 lda #0
 sta $d729
 sta playing
 // Non-current parameters are identical, reset before every attempt.
 lda #<TARGET
 sta $d721
 lda #>(TARGET&$ffff)
 sta $d722
 lda #TARGET>>16
 sta $d723
 lda #<SAMPLE_RATE
 sta $d724
 lda #>(SAMPLE_RATE&$ffff)
 sta $d725
 lda #SAMPLE_RATE>>16
 sta $d726
 lda #<TARGET_END
 sta $d727
 lda #>(TARGET_END&$ffff)
 sta $d728
 lda #0
 sta $d72d
 sta $d72e
 sta $d72f
 // Correct seed order creates same divergent staging/current value for every A/B/replay.
 lda #<SENTINEL
 sta $d72a
 lda #>(SENTINEL&$ffff)
 sta $d72b
 lda #SENTINEL>>16
 sta $d72c
 jsr settle
 jsr read_current
 lda #0
 sta seed_error
 lda current
 cmp #<SENTINEL
 bne !bad+
 lda current+1
 cmp #>(SENTINEL&$ffff)
 bne !bad+
 lda current+2
 cmp #SENTINEL>>16
 beq !done+
!bad:
 inc seed_error
!done:
 rts
settle:
 ldx #32
!wait:
 lda $d7fa // supplies audio background bus slots, bounded; not an IRQ wait
 dex
 bne !wait-
 rts
stop:
 lda #2
 sta $d720
 lda #0
 sta $d729
 sta playing
 rts
poll_audio:
 lda playing
 beq !done+
 lda $d720
 and #8
 beq !watch+
 jsr stop
 lda #3
 sta phase
 jsr log_event // natural completion, pointer sampled after disabling
 jmp draw
!watch:
 lda $d7fa
 cmp last_frame
 beq !done+
 sta last_frame
 dec watchdog
 bne !done+
 jsr stop
 lda #5
 sta MAILBOX
 lda #6
 sta phase
 jsr log_event
 jmp draw
!done:
 rts
read_current:
 lda #0
 sta pointer_torn
 ldy #16
!again:
 lda $d72b
 sta current+1
 lda $d72a
 sta current
 lda $d72b
 cmp current+1
 beq !bank+
 dey
 bne !again-
 lda #1
 sta pointer_torn // bounded even when observing refused foreign fast audio
!bank:
 lda $d72c
 sta current+2 // sample never crosses a64KiB bank
 rts

audio_save:
 lda $d713
 sta old_audio_irq
 lda $d701
 sta old_dma
 lda $d702
 sta old_dma+1
 lda $d704
 sta old_dma+2
 lda $d711
 sta old_global
 lda $d712
 and #2
 sta old_swap
 lda $d6f4
 sta old_selector
 ldx #15
!ch:
 lda $d720,x
 sta old_channel,x
 dex
 bpl !ch-
 ldx #0
!mix:
 stx $d6f4
 lda $d6f5
 sta old_mixer,x
 inx
 bne !mix-
 lda #1
 sta owned
 rts
mixer_wait:
 pha
 txa
 pha
 jsr settle
 pla
 tax
 pla
 rts
mixer_init:
 jsr stop
 lda #0
 sta $d713 // fixed no Audio-DMA IRQs in either variant; raw entry byte is restored
 ldx #0
!mute:
 stx $d6f4
 lda #0
 sta $d6f5
 jsr mixer_wait
 cmp $d6f5
 bne !bad+
 inx
 bne !mute-
 ldx #15
!route:
 lda unity_indices,x
 sta $d6f4
 lda #$ff
 sta $d6f5
 jsr mixer_wait
 cmp $d6f5
 bne !bad+
 dex
 bpl !route-
 lda #0
 sta $d712 // fixed no-swap, restore only writable bit1
 lda #$80
 sta $d711
 // Keep the existing strict initialization check, separately classified as03.
 // G only OBSERVES the masked alternative; it does not change A/B setup.
 lda $d711
 sta log_header+30
 cmp #$80
 beq !done+
!bad:
 lda #3
 sta init_error
!done:
 rts
audio_restore:
 jsr stop
 ldx #0
!mix:
 stx $d6f4
 lda old_mixer,x
 sta $d6f5
 jsr mixer_wait
 inx
 bne !mix-
 // Base/rate/top/volume are plain bytes. CURRENT must be restored low,high,bank.
 ldx #1
!ch:
 lda old_channel,x
 sta $d720,x
 inx
 cpx #10
 bne !ch-
 lda old_channel+10
 sta $d72a
 lda old_channel+11
 sta $d72b
 lda old_channel+12
 sta $d72c
 lda old_channel+13
 sta $d72d
 lda old_channel+14
 sta $d72e
 lda old_channel+15
 sta $d72f // restore saved inactive timing phase, latch on high byte
 jsr settle
 lda old_channel
 and #$fb // sample-valid bit2 is read-only in Core0.97
 sta $d720 // original disabled/stopped control LAST
 lda old_swap
 sta $d712
 lda old_audio_irq
 sta $d713 // Core0.97 exposes writable flags/enables; no comparison to XEMU FF readback
 lda old_global
 and #$b8 // writable bits only, never read-only BLKD/debug flags
 sta $d711
 lda old_selector
 sta $d6f4
 lda old_dma
 sta $d701
 lda old_dma+1
 sta $d702
 lda old_dma+2
 sta $d704
 rts

log_event:
 jsr read_current
 lda attempt
 sta event_record
 sta log_header+14
 lda attempt+1
 sta event_record+1
 sta log_header+15
 lda variant
 clc
 adc #$41
 sta event_record+2
 lda phase
 sta event_record+3
 lda MAILBOX
 sta event_record+4
 lda $d711
 sta event_record+5
 ldx #0
 cmp #$80
 bne !+
 inx
!:
 stx event_record+6 // strict comparison, informational only
 and #$80
 ldx #0
 cmp #$80
 bne !+
 inx
!:
 stx event_record+7 // masked comparison, informational only
 lda $d720
 sta event_record+8
 lda $d712
 sta event_record+9
 lda $d713
 sta event_record+10
 lda $d7fa
 sta event_record+11
 ldx #2
!ptr:
 lda current,x
 sta event_record+12,x
 dex
 bpl !ptr-
 lda $d729
 sta event_record+15
 ldx #8
!reg:
 lda $d721,x
 sta event_record+16,x
 dex
 bpl !reg-
 lda variant
 sta event_record+25
 lda seed_error
 sta event_record+26
 lda playing
 sta event_record+27
 lda error_before
 sta event_record+28
 lda error_after
 sta event_record+29
 lda start_frame
 sta event_record+30
 lda pointer_torn
 sta event_record+31
 ldx #31
!copy:
 lda event_record,x
record_put:
 sta records,x
 dex
 bpl !copy-
 inc log_header+12
 bne !+
 inc log_header+13
!:
 lda log_header+9
 cmp #64
 beq !+
 inc log_header+9
!:
 inc log_header+10
 lda log_header+10
 cmp #64
 bne !next+
 lda #0
 sta log_header+10
 lda #<records
 sta record_put+1
 lda #>records
 sta record_put+2
 rts
!next:
 clc
 lda record_put+1
 adc #32
 sta record_put+1
 bcc !+
 inc record_put+2
!:
 rts

.var ui_addresses=List().add($0800+4*80+12,$0800+5*80+12,$0800+5*80+24,$0800+8*80+12,$0800+9*80+12,$0800+10*80+12,$0800+10*80+14,$0800+11*80+12,$0800+12*80+12,$0800+13*80+12,$0800+20*80+12,$0800+20*80+24)
.var ui_values=List().add(MAILBOX,error_before,error_after,$d711,phase,attempt+1,attempt,log_header+9,playing,$d720,ui_strict,ui_masked)
// Direct native80-column BASIC screen update. No VIC geometry or font writes.
draw:
 lda $d711
 ldx #0
 cmp #$80
 bne !+
 inx
!:
 stx ui_strict
 and #$80
 ldx #0
 cmp #$80
 bne !+
 inx
!:
 stx ui_masked
 lda variant
 clc
 adc #1
 sta $0800+3*80+12 // screen codes A/B
 .for(var pair=0;pair<12;pair++) {
    lda #<(ui_addresses.get(pair))
    sta hex_put+1
    lda #>(ui_addresses.get(pair))
    sta hex_put+2
    lda ui_values.get(pair)
    jsr hex8
 }
 lda observed_start+2
 ldx #<($0800+6*80+12)
 ldy #>($0800+6*80+12)
 jsr hex_at
 lda observed_start+1
 jsr hex8
 lda observed_start
 jsr hex8
 jsr read_current
 lda current+2
 ldx #<($0800+7*80+12)
 ldy #>($0800+7*80+12)
 jsr hex_at
 lda current+1
 jsr hex8
 lda current
 jsr hex8
 rts
hex_at:
 stx hex_put+1
 sty hex_put+2
hex8:
 pha
 lsr
 lsr
 lsr
 lsr
 tax
 lda digits,x
 jsr hex_store
 pla
 and #15
 tax
 lda digits,x
hex_store:
hex_put:
 sta $0800
 inc hex_put+1
 bne !+
 inc hex_put+2
!:
 rts
puts:
 stx text_read+1
 sty text_read+2
!loop:
text_read:
 lda $ffff
 beq !done+
 jsr $ffd2
 inc text_read+1
 bne !loop-
 inc text_read+2
 jmp !loop-
!done:
 rts

copy_sample:
 lda #0
 sta dma_src_mb
 sta dma_dst_mb
 sta dma_src_bank
 sta dma_command
 lda #<$a000
 sta dma_src_lo
 lda #>$a000
 sta dma_src_hi
 lda #<TARGET
 sta dma_dst_lo
 lda #>(TARGET&$ffff)
 sta dma_dst_hi
 lda #TARGET>>16
 sta dma_dst_bank
 lda #<SAMPLE_BYTES
 sta dma_len_lo
 lda #>SAMPLE_BYTES
 sta dma_len_hi
 jsr dma
 lda #<TARGET
 sta dma_src_lo
 lda #>(TARGET&$ffff)
 sta dma_src_hi
 lda #TARGET>>16
 sta dma_src_bank
 lda #0
 sta dma_dst_bank
 sta dma_dst_lo
 lda #$60
 sta dma_dst_hi
 jsr dma
 // Silent sentinel page, never enabled for playback on mismatch.
 lda #3
 sta dma_command
 lda #0
 sta dma_src_lo
 sta dma_src_hi
 sta dma_src_bank
 sta dma_dst_lo
 sta dma_len_lo
 lda #1
 sta dma_dst_bank
 sta dma_len_hi
 lda #$80
 sta dma_dst_hi
 jsr dma
 lda #0
 sta dma_command
 rts
dma:
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
 .byte $0a,0
dma_command: .byte 0
dma_len_lo: .byte 0
dma_len_hi: .byte 0
dma_src_lo: .byte 0
dma_src_hi: .byte 0
dma_src_bank: .byte 0
dma_dst_lo: .byte 0
dma_dst_hi: .byte 0
dma_dst_bank: .byte 0
 .word 0
checksum:
    lda #<$6000
    sta $fb
    lda  #>$6000
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
    cmp #<($6000+SAMPLE_BYTES)
    bne !byte-
    lda $fc
    cmp #>($6000+SAMPLE_BYTES)
    bne !byte-
    rts

variant: .byte 0
attempt: .word 0
phase: .byte 0
playing: .byte 0
armed: .byte 0
owned: .byte 0
init_error: .byte 0
seed_error: .byte 0
pointer_torn: .byte 0
ui_strict: .byte 0
ui_masked: .byte 0
error_before: .byte 0
error_after: .byte 0
current: .fill 3,0
observed_start: .fill 3,0
start_frame: .byte 0
last_frame: .byte 0
watchdog: .byte 0
old_p: .byte 0
old_mailbox: .byte 0
old_d030: .byte 0
old_d031: .byte 0
old_d054: .byte 0
old_query: .byte 0
old_ddra: .byte 0
old_zp: .word 0
old_dma: .fill 3,0
old_global: .byte 0
old_audio_irq: .byte 0
old_swap: .byte 0
old_selector: .byte 0
old_channel: .fill 16,0
old_mixer: .fill 256,0
crc: .word $ffff
event_record: .fill 32,0
digits: .byte 48,49,50,51,52,53,54,55,56,57,1,2,3,4,5,6
unity_indices: .byte $10,$11,$30,$31,$d0,$d1,$f0,$f1,$1e,$1f,$3e,$3f,$de,$df,$fe,$ff
.encoding "petscii_upper"
message:
.text "STAGE10B1D AUDIO CURRENT-ADDRESS LATCH"
.byte 13
.text "1=A BANK/LOW/HIGH   2=B LOW/HIGH/BANK"
.byte 13
.text "P/SPACE/FIRE REPLAY  S STOP  G D711  X BASIC"
.byte 13
.text "VARIANT   : A"
.byte 13
.text "1FD3      : 00"
.byte 13
.text "BEFORE/AF : 00          00"
.byte 13
.text "LATCHED   : 000000"
.byte 13
.text "CURRENT   : 000000"
.byte 13
.text "D711 RAW  : 00"
.byte 13
.text "PHASE     : 00"
.byte 13
.text "ATTEMPT   : 0000"
.byte 13
.text "LOG COUNT : 00"
.byte 13
.text "PLAYING   : 00"
.byte 13
.text "CTRL      : 00"
.byte 13
.text "TARGET=016480  SEED=018020  END=017EC0"
.byte 13
.text "SOUND17 SIGNED8 PER356 VOL40  ONE SHOT"
.byte 13
.text "PHASE0=BEFORE 1=LATCH 2=START 3=DONE"
.byte 13
.text "4=STOP 5=D711-ONLY 6=TIMEOUT"
.byte 13
.text "ERR04=POINTER MISMATCH; NO AUDIO ENABLE"
.byte 13
.text "CAPTURE A1 B A2 AND REPLAY. MODERATE VOLUME."
.byte 13
.text "D711 EQ80 : 00 MASK80 : 00"
.byte 13,0
.assert "Code must stay below4000", *<$4000, true
*=$5000 "Versioned64-record RAM log, persists after X"
log_header:
.text "VYAL1B1D"
.byte 1,0,0,0
.word 0,0,32
.byte 0,0,17
.word 356
.byte 0
.byte <TARGET,>(TARGET&$ffff),TARGET>>16
.byte <SENTINEL,>(SENTINEL&$ffff),SENTINEL>>16
.word 0
records: .fill 64*32,0
*=$6000 "DMA readback for sample CRC"
.fill SAMPLE_BYTES,0
*=$a000 "Unmodified original Amiga sound17"
.import binary "sound17.s8"
