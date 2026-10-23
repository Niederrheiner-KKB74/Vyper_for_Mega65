// Stage8b banked audio core, CPU A000..B7FF => physical1E000..1F7FF.
.import source "audio_constants.inc"
.import source "audio_engine.inc"
*=$a000
.namespace sound {
 jmp dispatch
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
 bit $d711 // only AUDEN; bits 6 and 0-2 are hardware status bits
 bpl audio_init_error
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
 sta count
 lda buffer_bank,y
 sta dst_bank_dma
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
 // Hardware: $D72A/$D72B only latch; writing $D72C commits all three bytes.
 lda initial_lo,y
 sta $d72a,x
 lda initial_hi,y
 sta $d72b,x
 lda buffer_bank,y
 sta $d723,x
 sta $d72c,x
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
 bcc !bad_source+
 bne !upper_source+
 lda cursor_hi,y
 cmp #$1a // PCM begins at Attic031A00, never play header/code bytes
 bcc !bad_source+
 lda cursor_bank,y
!upper_source:
 cmp #6
 bcc !bounds+
!bad_source:
 lda #5
 sta error
 rts
!bounds:
 lda #$80
 sta src_mb
 lda #0
 sta dst_mb
 lda buffer_bank,y
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
service_complete:
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
 // DMA may finish AFTER the first CTRL read. Its exclusive end pointer is
 // deliberately outside the ring when the final block was in half1.
 lda $d720,x
 and #8
 beq !pointer_live+
 jmp service_complete
!pointer_live:
 lda $d72c,x
 cmp buffer_bank,y
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
 // Also close the smaller race during validation, before declaring corruption.
 lda $d720,x
 and #8
 beq !invalid+
 jmp service_complete
!invalid:
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

// Enhanced F018A DMA, synchronous and IRQ-masked by the resident gate.
dma_copy:
 lda #1
 sta $d702
 lda #0
 sta $d704
 lda #>((dma_list+$14000)&$ffff)
 sta $d701
 lda #<(dma_list+$14000)
 sta $d705
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
hw: .byte 0,32
buffer_hi: .byte $64,$c5
buffer_bank: .byte 1,5
output_offsets: .byte 0,$c0
master_indices: .byte $1e,$1f,$3e,$3f,$de,$df,$fe,$ff
old_dma: .fill 3,0
old_global: .byte 0
old_mixer_select: .byte 0
old_channels: .fill 64,0
old_mixer: .fill 256,0
error: .byte 0
configured: .byte 0
remaining: .fill 3,0
offset: .fill 3,0
s: .byte 0
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

.import source "audio_samples.inc"
.import source "audio_events.inc"
// Dispatch command is passed in a resident mailbox, all gameplay registers preserved.
dispatch:
 lda configured
 bne !owned+
 lda $1fd0
 cmp #12
 beq !owned+
 cmp #13
 beq !owned+
 cmp #15 // retain50Hz frame gating even when audio ownership was refused
 beq !owned+
 rts
!owned:
 lda $d701
 sta old_dma
 lda $d702
 sta old_dma+1
 lda $d704
 sta old_dma+2
 lda $1fd0
 cmp #16
 bcc !valid+
 rts
!valid:
 asl
 tax
 lda command_table,x
 sta dispatch_jump+1
 lda command_table+1,x
 sta dispatch_jump+2
dispatch_jump:
 jsr $ffff
 jsr stream
 lda error
 sta $1fd3
 beq !ok+
 // Runtime audio errors silence owned voices; gameplay remains intact.
 lda configured
 beq !ok+
 lda #0
 sta s
 jsr stop_source
 inc s
 jsr stop_source
!ok:
 lda old_dma
 sta $d701
 lda old_dma+1
 sta $d702
 lda old_dma+2
 sta $d704
 rts
command_table:
 .word stream,tick,enemy_entry,enemy_attack,enemy_shot,enemy_death,player_shot,player_death,transition_early,transition_rect,reset_level,stop_all,initialize,finish_exit,stop_all,frame_wait
frame_wait:
!wait:
 lda $d012
 cmp #250
 beq !leave+
 cmp #192
 bcs !wait-
 jsr stream
 jmp !wait-
!leave:
 lda $d012
 cmp #250
 beq !leave-
 jmp tick
initialize:
 lda #0
 sta error
 sta configured
 sta active
 sta active+1
 sta pending_id
 sta pending_id+1
 sta busy
 sta busy+1
 sta underruns
 sta max_gap
 sta max_lines
 sta max_lines+1
 sta monitor_ready
 sta refills
 sta refills+1
 sta completed
 sta s
 sta pan_kind
 sta pan_kind+1
 lda #$ff
 sta stream_line
 sta stream_stamp
 lda #120
 sta positions
 sta positions+1
 lda #4
 sta divs
 sta divs+1
 // Do not take ownership of a foreign active channel.
 ldx #0
!foreign:
 lda $d720,x
 and #$88
 cmp #$80
 beq !busy+
 txa
 clc
 adc #16
 tax
 cpx #64
 bne !foreign-
 jsr audio_save
 jmp audio_init
!busy:
 lda #2
 sta error
 rts
stream:
 lda configured
 beq !done+
 // Engine byte readers can submit thousands of tiny DMA jobs. A64us raster
 // granularity avoids refill bookkeeping for every byte, independently
 // of gameplay ticks. Frame stamp distinguishes an unchanged raster on next frame.
 lda $d012
 cmp stream_line
 bne !due+
 lda $d7fa
 cmp stream_stamp
 beq !done+
!due:
 lda $d012
 sta stream_line
 lda $d7fa
 sta stream_stamp
 jsr measure_gap
 lda error
 bne !done+
 lda #0
 sta s
 jsr service
 jsr position
 inc s
 jsr service
 jsr position
!done:
 rts
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

// Original logical soundtick, not the high-frequency streaming service.
tick:
 jsr stream
 lda error
 bne tick_done
 lda $1d89 // level.mode
 beq !play+
 cmp #2
 bne tick_done // LEVEL CLEAR freezes logical Busy, PCM still streams
 lda $1bc0 // transition state
 cmp #1
 beq !play+
 cmp #2
 bne tick_done
 lda $1bc2 // first ring's three frames model the three WaitTOFs
 bne tick_done
!play:
 lda $1c73 // player state
 cmp #4
 beq tick_done
 lda anim_pause_address
 bne tick_done
 lda #0
 sta s
!voice:
 ldy s
 lda busy,y
 beq !pending+
 sec
 sbc #1
 sta busy,y
!pending:
 lda pending_id,y
 beq !next+
 ldx #0
!find:
 cmp ids,x
 beq !found+
 inx
 cpx #20
 bne !find-
 lda #5
 sta error
 rts
!found:
 txa
 sta choices,y
 lda #0
 sta pending_id,y
 jsr position
 jsr start_source
!next:
 inc s
 lda s
 cmp #2
 bne !voice-
tick_done:
 rts
// Packed mapping is keyed by actual VYGR source-offset, never actor slot number.
find_type:
 ldx $1fd5
 cpx #22
 bcs !bad+
 lda $6a80,x
 sta type_lo
 lda $6a96,x
 sta type_hi
 ldx #0
!search:
 lda gfx_lo,x
 cmp type_lo
 bne !next+
 lda gfx_hi,x
 cmp type_hi
 beq !found+
!next:
 inx
 cpx #38
 bne !search-
!bad:
 sec
 rts
!found:
 clc
 rts
enemy_entry:
 jsr find_type
 bcs event_done
 lda entry_ids,x
 ldy #0
 jmp enemy_request
enemy_attack:
 jsr find_type
 bcs event_done
 lda attack_ids,x
 ldy #0
 jmp enemy_request
enemy_death:
 jsr find_type
 bcs event_done
 lda death_ids,x
 ldy #1
 jmp enemy_request
enemy_request:
 sta event_id
 lda busy,y
 bne event_done
 lda #1
 sta pan_kind,y
 lda $1fd5
 sta pan_owner,y
 lda event_id
 sta pending_id,y
event_done:
 rts
enemy_shot:
 // Hook receives newly admitted projectile X; source actor comes from its owner.
 ldx $1fd5
 cpx #2
 bcc event_done
 cpx #8
 bcs event_done
 stx event_slot
 lda shooter_address,x
 sta $1fd5
 jsr find_type
 bcs event_done
 lda shot_ids,x
 sta event_id
 // Original updates projectile panning pointer EVEN WHEN Busy rejects new ID.
 lda #3
 sta pan_kind+1
 lda event_slot
 sta pan_owner+1
 lda busy+1
 bne event_done
 lda event_id
 sta pending_id+1
 rts
player_shot:
 lda #2
 sta pan_kind
 lda $1fd5
 sta pan_owner
 lda #17
 jmp forced
player_death:
 lda #4
 sta pan_kind
 lda #19
 jmp forced
transition_early:
 lda #24
 jmp centre_forced
transition_rect:
 lda #22
centre_forced:
 pha
 lda #0
 sta pan_kind
 pla
forced:
 sta pending_id
 lda #0
 sta s
 jmp stop_source
reset_level:
 // Prevent slot reuse retargeting a still-playing enemy sound across level changes.
 lda #1
 sta s
 jsr stop_source
 lda #0
 sta pending_id+1
 sta busy+1
 lda pan_kind
 beq !keep+
 cmp #4
 beq !keep+
 jmp stop_all
!keep:
 rts
stop_all:
 lda #0
 sta s
 sta pending_id
 sta pending_id+1
 sta busy
 sta busy+1
 jsr stop_source
 inc s
 jmp stop_source
position:
 ldy s
 lda pan_kind,y
 beq pan_centre
 cmp #1
 beq pan_enemy
 cmp #4
 beq pan_player
 lda pan_owner,y
 tax
 lda shots_x_address,x
 sta pos_low
 lda pan_kind,y
 cmp #3
 bne !positive+
 lda motion_xhi_address,x
 jmp pan_signed
!positive:
 lda #0
 jmp pan_signed
pan_enemy:
 ldx pan_owner,y
 lda $1e00,x
 sta pos_low
 lda $1e16,x
 jmp pan_signed
pan_player:
 lda $1662
 sta pos_low
 lda #0
pan_signed:
 beq !clamp+
 bmi !left+
 lda #240
 bne pan_value
!left:
 lda #0
 beq pan_value
!clamp:
 lda pos_low
 cmp #241
 bcc pan_value
 lda #240
 bne pan_value
pan_centre:
 lda #120
pan_value:
 cmp positions,y
 beq !done+
 sta positions,y
 jsr pan
!done:
 rts
// Restore source/mixer ownership and the transient E000 loader after BASIC video.
finish_exit:
 lda configured
 beq !bootstrap+
 jsr audio_restore
 lda #0
 sta configured
!bootstrap:
 lda #$80
 sta src_mb
 lda #0
 sta src_lo_dma
 sta dst_mb
 sta dst_lo_dma
 sta dst_bank_dma
 sta count
 lda #$c0
 sta src_hi_dma
 lda #2
 sta src_bank_dma
 lda #$e0
 sta dst_hi_dma
 lda #16
 sta count+1
 jmp dma_copy
stream_line: .byte 0
stream_stamp: .byte 0
pending_id: .byte 0,0
pan_kind: .byte 0,0
pan_owner: .byte 0,0
event_id: .byte 0
event_slot: .byte 0
type_lo: .byte 0
type_hi: .byte 0
pos_low: .byte 0
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

.if (*>$b800) { .error "Audio core exceeds reserved chip RAM" }
.fill $b800-*,0
}
