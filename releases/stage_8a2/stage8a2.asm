// Stage8a2 standalone; two independent ring streams, NOT game integration.
// Chip buffer A=$4000..4FFF, B=$5000..5FFF; Attic=$08000000..08025ABF.
.import source "archive.inc"
.const STAGE=$6000
.const CHECK=$6100
*=$2001
BasicUpstart($2100)
*=$2100 "Stage8a2 dual PCM controller"
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
 lda $d614
 sta old_query
 lda $dc02
 sta old_ddra
 ldx #3
!save:
 lda $fb,x
 sta old_zp,x
 dex
 bpl !save-
 lda $d701
 sta old_dma
 lda $d702
 sta old_dma+1
 lda $d704
 sta old_dma+2
 lda #0
 sta quit
 sta busy
 sta busy+1
 sta refills
 sta refills+1
 sta completed
 sta underruns
 sta max_gap
 sta max_lines
 sta max_lines+1
 sta monitor_ready
 sta error
 sta configured
 sta active
 sta active+1
 sta load_mode
 sta selected
 sta armed
 sta load_enabled
 sta pauses
 sta requested
 sta requested+1
 lda #13 // ID17
 sta choices
 lda #15 // ID19
 sta choices+1
 lda #120
 sta positions
 sta positions+1
 lda #$ff
 sta crc
 sta crc+1
 jsr check_foreign
 bcc !idle_start+
 lda #2
 sta error
 jmp exit
!idle_start:
 cli
 ldx #<loading_msg
 ldy #>loading_msg
 jsr puts
 jsr load_archive
 sei
 jsr full_speed
 lda error
 beq !audio+
 jmp exit
!audio:
 ldx #0
!idle:
 lda $d720,x
 and #$88
 cmp #$80
 bne !next+
 lda #2
 sta error
 jmp exit
!next:
 txa
 clc
 adc #16
 tax
 cpx #64
 bne !idle-
 jsr audio_save
 jsr audio_init
 lda #0
 sta $dc02
 cli
 ldx #<message
 ldy #>message
 jsr puts
 sei
 jsr full_speed
 lda $d7fa
 sta last_frame
main_loop:
 jsr service_all
 lda error
 beq !input+
 jmp exit
!input:
 jsr inputs
 lda quit
 beq !load+
 jmp exit
!load:
 lda load_enabled
 beq main_loop
 // Sixteen bounded 256-byte DMA jobs, service between EACH job.
 lda #16
 sta load_jobs
!job:
 lda #0
 sta src_mb
 sta dst_mb
 sta src_lo_dma
 sta dst_lo_dma
 sta src_bank_dma
 sta dst_bank_dma
 sta count
 lda #1
 sta count+1
 lda #$70
 sta src_hi_dma
 lda #$71
 sta dst_hi_dma
 jsr dma_copy
 ldx #0
!cpu_load:
 lda $7000,x
 eor $7100,x
 adc #17
 sta $7000,x
 inx
 bne !cpu_load-
 jsr service_all
 dec load_jobs
 bne !job-
 jmp main_loop
check_foreign:
 ldx #0
!channel:
 lda $d720,x
 and #$88
 cmp #$80
 beq !busy+
 txa
 clc
 adc #16
 tax
 cpx #64
 bne !channel-
 clc
 rts
!busy:
 sec
 rts
full_speed:
 lda old_d030
 and #$fe
 sta $d030
 lda old_d031
 ora #$40
 sta $d031
 lda old_d054
 ora #$40
 sta $d054
 rts
// KERNAL receives exact-length SEQ, BEFORE audio starts. No CHROUT on channel.
load_archive:
 lda #0
 sta offset
 sta offset+1
 sta offset+2
 lda #<ARCHIVE_BYTES
 sta remaining
 lda #>(ARCHIVE_BYTES&$ffff)
 sta remaining+1
 lda #ARCHIVE_BYTES>>16
 sta remaining+2
 lda #2
 ldx $ba
 cpx #8
 bcs !device+
 ldx #8
!device:
 ldy #2
 jsr $ffba
 lda #0
 ldx #0
 jsr $ff6b
 lda #filename_end-filename
 ldx #<filename
 ldy #>filename
 jsr $ffbd
 jsr $ffc0
 bcc !open+
 jmp load_failed
!open:
 ldx #2
 jsr $ffc6
 bcc !read+
 jmp load_failed
!read:
 lda #0
 sta chunk
!byte:
 jsr $ffcf
 ldx chunk
 sta STAGE,x
 jsr crc_byte
 jsr $ffb7
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
 cmp #<ARCHIVE_CRC
 bne load_failed
 lda crc+1
 cmp #>ARCHIVE_CRC
 beq load_close
load_failed:
 lda #1
 sta error
load_close:
 jsr $ffcc
 lda #2
 jsr $ffc3
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
 cmp #ARCHIVE_BYTES>>16
 bne !full+
 lda offset+1
 cmp #>(ARCHIVE_BYTES&$ffff)
 bne !full+
 lda #<ARCHIVE_BYTES
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
 lda #$61
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
 cmp #<ARCHIVE_CRC
 bne !bad+
 lda crc+1
 cmp #>ARCHIVE_CRC
 bne !bad+
 rts
!bad:
 lda #3
 sta error
 rts
archive_page:
 // Check exact Attic boundary, copy then read back into CHECK and compare.
 lda offset+2
 cmp #3
 bcc !range+
 lda #3
 sta error
 rts
!range:
 lda #0
 sta src_mb
 sta src_lo_dma
 sta src_bank_dma
 lda #$60
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
 lda #$61
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
 lda #>dma_list
 sta $d701
 lda #<dma_list
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
// Chipset reference: wait >=32 mixer clock cycles before changing selector.
// 32 explicit I/O reads exceed that even with the CPU at full speed; preserve A/X.
mixer_wait:
 pha
 txa
 pha
 ldx #32
!wait:
 lda $d7fa
 dex
 bne !wait-
 pla
 tax
 pla
 rts
audio_save:
 lda $d711
 sta old_global
 lda $d6f4
 sta old_mixer_select
 ldx #63
!ch:
 txa
 and #15
 cmp #13
 bcs !skip+
 lda $d720,x
 sta old_channels,x
!skip:
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
 sta configured
 rts
audio_init:
 lda #2
 sta $d720
 sta $d730
 sta $d740
 sta $d750
 lda #0
 ldx #0
!mute:
 stx $d6f4
 sta $d6f5
 jsr mixer_wait
 cmp $d6f5
 beq !ok+
 lda #4
 sta error
 rts
!ok:
 inx
 bne !mute-
 ldx #7
!master:
 lda master_indices,x
 sta $d6f4
 lda #$ff
 sta $d6f5
 jsr mixer_wait
 cmp $d6f5
 beq !master_ok+
 jmp audio_init_error
!master_ok:
 dex
 bpl !master-
 lda #$80
 sta $d711
 cmp $d711
 bne audio_init_error
 lda $d031
 and $d054
 and #$40
 beq audio_init_error
 lda #0
 sta s
 jsr pan
 inc s
 jsr pan
 rts
audio_init_error:
 lda #4
 sta error
 rts
// Stop only this logical source. Pending/Busy is an explicit test policy.
stop_source:
 ldy s
 ldx hw,y
 lda #2
 sta $d720,x
 lda #0
 sta $d729,x
 sta active,y
 rts
start_source:
 jsr stop_source
 // Deterministic silence in all initially unused ring bytes, including prefix.
 ldy s
 lda buffer_hi,y
 sta dst_hi_dma
 lda #0
 sta src_mb
 sta dst_mb
 sta src_lo_dma
 sta src_hi_dma
 sta src_bank_dma
 sta dst_lo_dma
 sta dst_bank_dma
 sta count
 lda #16
 sta count+1
 lda #3
 sta dma_command
 jsr dma_copy
 lda #0
 sta dma_command
 ldy s
 lda choices,y
 cmp #20
 bcc !valid+
 lda #5
 sta error
 rts
!valid:
 tax
 lda length_lo,x
 sta left_lo,y
 lda length_hi,x
 sta left_hi,y
 lda src_lo,x
 sta cursor_lo,y
 lda src_hi,x
 sta cursor_hi,y
 lda src_bank,x
 sta cursor_bank,y
 lda busy_values,x
 sta busy,y
 lda divisors,x
 sta divs,y
 lda rate_lo,x
 sta rates_lo,y
 lda rate_hi,x
 sta rates_hi,y
 lda rate_bank,x
 sta rates_bank,y
 lda #$ff
 sta final_half,y
 lda #0
 sta half,y
 sta refill_half
 lda #1
 sta first_fill
 jsr fill_half
 lda error
 beq !first_ok+
 rts
!first_ok:
 lda #1
 sta refill_half
 jsr fill_half
 lda error
 beq !second_ok+
 rts
!second_ok:
 ldy s
 ldx hw,y
 lda #0
 sta $d721,x
 sta $d723,x
 sta $d72c,x
 lda initial_lo,y
 sta $d72a,x
 lda initial_hi,y
 sta $d72b,x
 lda buffer_hi,y
 sta $d722,x
 clc
 adc #$10
 sta $d728,x
 lda #0
 sta $d727,x
 lda rates_lo,y
 sta $d724,x
 lda rates_hi,y
 sta $d725,x
 lda rates_bank,y
 sta $d726,x
 lda #$ff
 sta $d729,x
 lda $d724,x
 cmp rates_lo,y
 bne source_init_error
 lda $d725,x
 cmp rates_hi,y
 bne source_init_error
 lda $d726,x
 cmp rates_bank,y
 bne source_init_error
 lda $d72a,x
 cmp initial_lo,y
 bne source_init_error
 lda $d72b,x
 cmp initial_hi,y
 bne source_init_error
 lda #$c2 // signed8 EN LOOP
 sta $d720,x
 lda #1
 sta active,y
 lda $d7fa
 sta service_frame,y
 sta start_frame,y
 jsr finish_config
 jsr pan
 rts
source_init_error:
 lda #4
 sta error
 rts
// Copy min(remaining,2048) into the newly free half. Never alter live half.
fill_half:
 ldy s
 lda left_lo,y
 ora left_hi,y
 bne !fill+
 rts
!fill:
 lda #0
 sta prefix_lo
 sta prefix_hi
 sta count
 lda #8
 sta count+1
 lda first_fill
 beq !regular+
 lda #0
 sta first_fill
 lda left_lo,y
 sta count
 lda left_hi,y
 and #7
 sta count+1
 ora count
 bne !prefix+
 lda #8
 sta count+1
!prefix:
 lda #0
 sec
 sbc count
 sta prefix_lo
 lda #8
 sbc count+1
 sta prefix_hi
 lda prefix_lo
 sta initial_lo,y
 lda prefix_hi
 clc
 adc buffer_hi,y
 sta initial_hi,y
!regular:
 // First block is right-aligned: every final block ends on a half boundary.
 // No short tail can pass the exact endpoint before software notices a wrap.
 lda left_lo,y
 cmp count
 bne !copy+
 lda left_hi,y
 cmp count+1
 bne !copy+
 lda refill_half
 sta final_half,y
 lda #0
 sta final_lo,y
 lda refill_half
 asl
 asl
 asl
 clc
 adc buffer_hi,y
 clc
 adc #8
 sta final_hi,y
!copy:
 lda cursor_lo,y
 sta src_lo_dma
 lda cursor_hi,y
 sta src_hi_dma
 lda cursor_bank,y
 sta src_bank_dma
 cmp #3
 bcc !bounds+
 lda #5
 sta error
 rts
!bounds:
 lda #$80
 sta src_mb
 lda #0
 sta dst_mb
 sta dst_bank_dma
 lda prefix_lo
 sta dst_lo_dma
 lda refill_half
 asl
 asl
 asl
 clc
 adc buffer_hi,y
 clc
 adc prefix_hi
 sta dst_hi_dma
 // Update cursor/remain using exact byte count, before DMA clobbers A.
 lda cursor_lo,y
 clc
 adc count
 sta cursor_lo,y
 lda cursor_hi,y
 adc count+1
 sta cursor_hi,y
 lda cursor_bank,y
 adc #0
 sta cursor_bank,y
 // End-exclusive source bound, includes the partial final Attic page.
 cmp #ARCHIVE_BYTES>>16
 bcc !end_ok+
 bne !bad_end+
 lda cursor_hi,y
 cmp #>(ARCHIVE_BYTES&$ffff)
 bcc !end_ok+
 bne !bad_end+
 lda cursor_lo,y
 cmp #<ARCHIVE_BYTES
 bcc !end_ok+
 beq !end_ok+
!bad_end:
 lda #5
 sta error
 rts
!end_ok:
 lda left_lo,y
 sec
 sbc count
 sta left_lo,y
 lda left_hi,y
 sbc count+1
 sta left_hi,y
 jsr dma_copy
 inc refills
 bne !done+
 inc refills+1
!done:
 rts
// When the FINAL block becomes live, change exclusive end and turn off LOOP.
// End HIGH first, LOW second; guard >40ms service gap, half lasts >=180ms.
finish_config:
 ldy s
 lda final_half,y
 cmp half,y
 bne !done+
 ldx hw,y
 lda final_hi,y
 sta $d728,x
 lda final_lo,y
 sta $d727,x
 lda #$82
 sta $d720,x
!done:
 rts
service_all:
 jsr measure_gap
 lda #0
 sta s
 jsr service
 inc s
 jsr service
 // Frame ticks only Busy; streaming above is continuous, independent of ticks.
 lda $d7fa
 cmp last_frame
 beq !done+
 sec
 sbc last_frame
 sta frame_delta
 lda $d7fa
 sta last_frame
 ldx #1
!busy:
 lda busy,x
 sec
 sbc frame_delta
 bcs !save+
 lda #0
!save:
 sta busy,x
 dex
 bpl !busy-
 jsr status
!done:
 rts
// PAL raster instrumentation. Snap frame/line coherently, max gap in lines.
measure_gap:
!snapshot:
 lda $d7fa
 sta now_frame
 lda $d011
 and #$80
 sta line_bit
 lda $d012
 sta now_line
 lda $d011
 and #$80
 cmp line_bit
 bne !snapshot-
 lda $d7fa
 cmp now_frame
 bne !snapshot-
 lda #0
 sta now_line+1
 lda line_bit
 beq !low+
 inc now_line+1
!low:
 lda monitor_ready
 beq !save+
 lda now_frame
 sec
 sbc monitor_frame
 cmp #3
 bcs !save+
 tax
 lda #0
 sta elapsed
 sta elapsed+1
 cpx #0
 beq !subtract+
!frame:
 lda elapsed
 clc
 adc #<312
 sta elapsed
 lda elapsed+1
 adc #>312
 sta elapsed+1
 dex
 bne !frame-
!subtract:
 lda elapsed
 clc
 adc now_line
 sta elapsed
 lda elapsed+1
 adc now_line+1
 sta elapsed+1
 lda elapsed
 sec
 sbc monitor_line
 sta elapsed
 lda elapsed+1
 sbc monitor_line+1
 sta elapsed+1
 cmp max_lines+1
 bcc !save+
 bne !max+
 lda elapsed
 cmp max_lines
 bcc !save+
!max:
 lda elapsed
 sta max_lines
 lda elapsed+1
 sta max_lines+1
!save:
 lda now_frame
 sta monitor_frame
 lda now_line
 sta monitor_line
 lda now_line+1
 sta monitor_line+1
 lda #1
 sta monitor_ready
 rts
service:
 ldy s
 lda active,y
 bne !active+
 rts
!active:
 ldx hw,y
 lda $d720,x
 and #8
 beq !alive+
 jsr stop_source
 inc completed
 rts
!alive:
 lda $d7fa
 sec
 sbc start_frame,y
 cmp #200 // 4s PAL, longer than every original sample including ID19
 bcc !watchdog_ok+
 lda #7
 sta error
 jsr stop_source
 rts
!watchdog_ok:
 lda $d7fa
 sec
 sbc service_frame,y
 cmp max_gap
 bcc !gap+
 sta max_gap
!gap:
 cmp #3 // >=3 frame boundaries can mean >=40ms: safe fail, NOT replay stale data
 bcc !timely+
 lda #6
 sta error
 inc underruns
 jsr stop_source
 rts
!timely:
 lda $d7fa
 sta service_frame,y
 // High/low/high snapshot; retry torn low-byte rollover.
!snapshot:
 lda $d72b,x
 sta pointer_hi
 lda $d72a,x
 sta pointer_lo
 lda $d72b,x
 cmp pointer_hi
 bne !snapshot-
 lda $d72c,x
 bne pointer_error
 lda pointer_hi
 sec
 sbc buffer_hi,y
 cmp #16
 bcs pointer_error
 and #8
 beq !half0+
 lda #1
!half0:
 cmp half,y
 beq !done+
 sta half,y
 jsr finish_config
 ldy s
 lda final_half,y
 cmp half,y
 beq !done+
 lda half,y
 eor #1
 sta refill_half
 jsr fill_half
!done:
 rts
pointer_error:
 lda #5
 sta error
 jsr stop_source
 rts
// Exact original integer panning, crossbar quantized to nearest 8bit/255.
// Both coefficient bytes identical: immune to documented mixer endian conflict.
pan:
 ldy s
 lda divs,y
 bne !div+
 lda #4
 sta divs,y
!div:
 sta divisor
 lda positions,y
 cmp #241
 bcc !clamped+
 lda #240
 sta positions,y
!clamped:
 ldx #0
!divide:
 cmp divisor
 bcc !quotient+
 sec
 sbc divisor
 inx
 bne !divide-
!quotient:
 stx right_volume
 lda #240
 ldx #0
!total:
 cmp divisor
 bcc !left+
 sec
 sbc divisor
 inx
 bne !total-
!left:
 txa
 sec
 sbc right_volume
 tax
 lda gains,x
 sta left_gain
 ldx right_volume
 lda gains,x
 sta right_gain
 lda s
 asl
 clc
 adc #$10
 sta mix_base
 // Four outputs: headphone L/R, speaker L/R, all use same coefficients.
 ldx #0
!output:
 lda output_offsets,x
 clc
 adc mix_base
 sta $d6f4
 lda left_gain
 jsr coefficient
 lda output_offsets,x
 clc
 adc mix_base
 clc
 adc #$20
 sta $d6f4
 lda right_gain
 jsr coefficient
 inx
 cpx #2
 bne !output-
 rts
coefficient:
 sta $d6f5
 jsr mixer_wait
 cmp $d6f5
 beq !ok+
 pha
 lda #4
 sta error
 pla
!ok:
 pha
 lda $d6f4
 clc
 adc #1
 sta $d6f4
 pla
 sta $d6f5
 jsr mixer_wait
 cmp $d6f5
 beq !done+
 lda #4
 sta error
!done:
 rts
// Explicit event categories: normal requests are rejected while Busy, T forces
// preemption (Player-style). One pending ID per source, last admitted writer wins.
request_source:
 lda selected
 sta s
request_s:
 ldy s
 lda busy,y
 bne !done+
 lda choices,y
 sta pending_choice,y
 lda #1
 sta requested,y
!done:
 rts
force_source:
 lda selected
 sta s
 jsr stop_source
 ldy s
 lda #0
 sta busy,y
 jmp request_s
requests:
 lda #0
 sta s
!source:
 ldy s
 lda requested,y
 beq !next+
 lda busy,y
 bne !next+
 lda #0
 sta requested,y
 lda pauses
 bne !next+
 lda choices,y
 sta restore_choice
 lda pending_choice,y
 sta choices,y
 jsr start_source // after Busy expires, a new admitted event may replace long PCM
 ldy s
 lda restore_choice
 sta choices,y
!next:
 inc s
 lda s
 cmp #2
 bne !source-
 rts
inputs:
 lda $d610
 bne !key+
 jmp !joy+
!key:
 sta $d610
 // X; TAB select A/B; A/B trigger; SPACE both; N next; V previous
 and #$df
 cmp #$58
 bne !tab+
 lda #1
 sta quit
 rts
!tab:
 cmp #9
 bne !a+
 lda selected
 eor #1
 sta selected
 jmp status
!a:
 cmp #$41
 bne !b+
 lda #0
 sta s
 jsr request_s
 jmp !joy+
!b:
 cmp #$42
 bne !both+
 lda #1
 sta s
 jsr request_s
 jmp !joy+
!both:
 cmp #0 // SPACE AND DF =0
 bne !n+
 lda #0
 sta s
 jsr request_s
 inc s
 jsr request_s
 jmp !joy+
!n:
 cmp #$4e
 bne !v+
 ldy selected
 lda choices,y
 clc
 adc #1
 cmp #20
 bcc !store+
 lda #0
!store:
 sta choices,y
 jmp status
!v:
 cmp #$56
 bne !left+
 ldy selected
 lda choices,y
 bne !prev+
 lda #20
!prev:
 sec
 sbc #1
 sta choices,y
 jmp status
!left:
 cmp #$4a // J left / K centre / L right
 bne !centre+
 lda #0
 jmp !position+
!centre:
 cmp #$4b
 bne !right+
 lda #120
 jmp !position+
!right:
 cmp #$4c
 bne !stop+
 lda #240
!position:
 ldy selected
 sta positions,y
 sty s
 jsr pan
 jmp status
!stop:
 cmp #$53
 bne !pause+
 lda #0
 sta requested
 sta requested+1
 sta s
 jsr stop_source
 inc s
 jsr stop_source
 jmp !joy+
!pause:
 cmp #$50
 bne !load+
 // Pause is explicit STOP+position reset; no false sample-accurate resume claim.
 lda pauses
 eor #1
 sta pauses
 lda #0
 sta s
 jsr stop_source
 inc s
 jsr stop_source
 jmp status
!load:
 cmp #$54
 bne !g+
 jsr force_source
 jmp !joy+
!g:
 cmp #$47
 bne !joy+
 lda load_enabled
 eor #1
 sta load_enabled
 jsr status
!joy:
 lda $dc00
 and #$10
 beq !pressed+
 lda #1
 sta armed
 jmp requests
!pressed:
 lda armed
 beq !requests+
 lda #0
 sta armed
 jsr request_source
!requests:
 jmp requests
// Update text only; do not call ROM while audio runs. 80x25 BASIC text mode.
// Obtain the current screen pointer, never assume $0800.
status:
 lda $d062
 beq !bank+
 rts
!bank:
 lda $d058
 cmp #80
 beq !width+
 rts
!width:
 lda $d059
 beq !stride+
 rts
!stride:
 lda $d060
 clc
 adc #<480
 sta $fb
 lda $d061
 adc #>480
 sta $fc
 lda #0
 sta ui_source
!source:
 ldx ui_source
 ldy #0
 lda #32
 cpx selected
 bne !mark+
 lda #42 // '*' screen code
!mark:
 sta ($fb),y
 lda choices,x
 tax
 lda ids,x
 ldy #12
 jsr decimal
 ldx ui_source
 lda positions,x
 ldy #21
 jsr decimal
 ldx ui_source
 lda active,x
 clc
 adc #48
 ldy #32
 sta ($fb),y
 ldx ui_source
 lda busy,x
 ldy #41
 jsr decimal
 lda $fb
 clc
 adc #80
 sta $fb
 bcc !ptr+
 inc $fc
!ptr:
 inc ui_source
 lda ui_source
 cmp #2
 bne !source-
 lda load_enabled
 clc
 adc #48
 ldy #5
 sta ($fb),y
 lda pauses
 clc
 adc #48
 ldy #13
 sta ($fb),y
 lda max_gap
 ldy #23
 jsr decimal
 lda underruns
 ldy #34
 jsr decimal
 lda refills
 ldy #46
 jsr decimal
 lda $fb
 clc
 adc #80
 sta $fb
 bcc !raster+
 inc $fc
!raster:
 ldy #26
 lda max_lines+1
 jsr hex_byte
 lda max_lines
 jsr hex_byte
!unsupported:
 rts
hex_byte:
 pha
 lsr
 lsr
 lsr
 lsr
 jsr nibble
 pla
 and #15
nibble:
 tax
 lda hex_digits,x
 sta ($fb),y
 iny
 rts
hex_digits: .byte 48,49,50,51,52,53,54,55,56,57,1,2,3,4,5,6
decimal:
 ldx #48
!hundred:
 cmp #100
 bcc !tens+
 sec
 sbc #100
 inx
 bne !hundred-
!tens:
 pha
 txa
 sta ($fb),y
 iny
 pla
 ldx #48
!ten:
 cmp #10
 bcc !ones+
 sec
 sbc #10
 inx
 bne !ten-
!ones:
 pha
 txa
 sta ($fb),y
 iny
 pla
 clc
 adc #48
 sta ($fb),y
 rts
exit:
 lda configured
 beq !io+
 jsr audio_restore
!io:
 lda old_dma
 sta $d701
 lda old_dma+1
 sta $d702
 lda old_dma+2
 sta $d704
 lda old_ddra
 sta $dc02
 lda old_query
 sta $d614
 ldx #3
!zp:
 lda old_zp,x
 sta $fb,x
 dex
 bpl !zp-
 lda old_d054
 sta $d054
 lda old_d031
 sta $d031
 lda old_d030
 sta $d030
 jsr restore_key
 plp
 lda error
 beq !ok+
 pha
 ldx #<error_msg
 ldy #>error_msg
 jsr puts
 pla
 clc
 adc #$30
 jsr $ffd2
 lda #13
 jsr $ffd2
!ok:
 rts
audio_restore:
 lda #2
 sta $d720
 sta $d740
 ldx #0
!mix:
 stx $d6f4
 lda old_mixer,x
 sta $d6f5
 jsr mixer_wait
 inx
 bne !mix-
 ldx #63
!channel:
 txa
 and #15
 cmp #13
 bcs !skip+
 lda old_channels,x
 sta $d720,x
!skip:
 dex
 bpl !channel-
 lda old_global
 sta $d711
 lda old_mixer_select
 sta $d6f4
 rts
hw: .byte 0,32
buffer_hi: .byte $40,$50
output_offsets: .byte 0,$c0
master_indices: .byte $1e,$1f,$3e,$3f,$de,$df,$fe,$ff
.encoding "petscii_upper"
filename: .text "VYAU.DAT,S,R"
filename_end:
loading_msg: .text "STAGE 8A2: LOADING 20 ORIGINAL SAMPLES"
 .byte 13,0
message:
 .byte 147
 .text "STAGE8A2  A=17 B=19  TAB: SELECT SOURCE"
 .byte 13
 .text "A/B: PLAY A/B   SPACE: BOTH   N/V: SAMPLE"
 .byte 13
 .text "J/K/L: LEFT/CENTRE/RIGHT  JOY2 FIRE: PLAY"
 .byte 13
 .text "S: STOP P: PAUSE(STOP) G: DMA LOAD X: BASIC"
 .byte 13
 .text "T: FORCE RESTART SELECTED (IGNORES BUSY)"
 .byte 13,13
 .text " A SAMPLE:  017   X: 120   LIVE:0  BUSY: 000"
 .byte 13
 .text " B SAMPLE:  019   X: 120   LIVE:0  BUSY: 000"
 .byte 13
 .text "LOAD:0 PAUSE:0 MAX GAP:000 ERRORS:000 REFILLS:000"
 .byte 13
 .text "MAX SERVICE GAP PAL LINES: 0000 (HEX)"
 .byte 13,0
error_msg: .text "STAGE8A2 ERROR "
 .byte 0
old_key: .byte 0
old_d030: .byte 0
old_d031: .byte 0
old_d054: .byte 0
old_query: .byte 0
old_ddra: .byte 0
old_zp: .fill 4,0
old_dma: .fill 3,0
old_global: .byte 0
old_mixer_select: .byte 0
old_channels: .fill 64,0
old_mixer: .fill 256,0
error: .byte 0
configured: .byte 0
crc: .word 0
chunk: .byte 0
io_status: .byte 0
remaining: .fill 3,0
offset: .fill 3,0
s: .byte 0
ui_source: .byte 0
selected: .byte 0
quit: .byte 0
armed: .byte 0
pauses: .byte 0
load_enabled: .byte 0
load_jobs: .byte 0
load_mode: .byte 0
last_frame: .byte 0
frame_delta: .byte 0
pointer_hi: .byte 0
pointer_lo: .byte 0
first_fill: .byte 0
prefix_lo: .byte 0
prefix_hi: .byte 0
initial_lo: .fill 2,0
initial_hi: .fill 2,0
refill_half: .byte 0
divisor: .byte 0
right_volume: .byte 0
left_gain: .byte 0
right_gain: .byte 0
mix_base: .byte 0
refills: .word 0
completed: .byte 0
underruns: .byte 0
max_gap: .byte 0
max_lines: .word 0
monitor_ready: .byte 0
monitor_frame: .byte 0
monitor_line: .word 0
now_frame: .byte 0
now_line: .word 0
line_bit: .byte 0
elapsed: .word 0
choices: .byte 13,15
positions: .byte 120,120
active: .fill 2,0
pending_choice: .fill 2,0
restore_choice: .byte 0
requested: .fill 2,0
busy: .fill 2,0
divs: .byte 4,4
rates_lo: .fill 2,0
rates_hi: .fill 2,0
rates_bank: .fill 2,0
cursor_lo: .fill 2,0
cursor_hi: .fill 2,0
cursor_bank: .fill 2,0
left_lo: .fill 2,0
left_hi: .fill 2,0
half: .fill 2,0
final_half: .fill 2,0
final_lo: .fill 2,0
final_hi: .fill 2,0
service_frame: .fill 2,0
start_frame: .fill 2,0
.import source "samples.inc"
.if (*>$4000) { .error "Controller overlaps ring A" }
