// Issue93: four isolated scenes, actual PRE/POST state, no engine/audio imports.
.const DUMP=$4800
#import "constants.inc"
*=$2001 "BASIC"
BasicUpstart($2100)
*=$2100 "Isolated scene and export controller"
entry:
    php
    sei
    cld
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    ldx #0
save_vic:
    cpx #$1e
    beq save_skip
    cpx #$1f
    beq save_skip
    cpx #$2f
    beq save_skip
    lda $d000,x
    sta initial_vic,x
save_skip:
    inx
    cpx #$7c
    bne save_vic
    // Refuse active X-IRQ; its original comparator is not readable.
    lda initial_vic+$1a
    and #$10
    beq irq_safe
    plp
    rts
irq_safe:
    lda initial_vic+$51
    and #$c0
    ora #$1f
    sta d051_restore_shadow
    lda #$41
    sta profile
    jsr backup_palettes
    // Preserve the whole physical colour RAM, not just the visible BASIC page.
    lda #$ff
    sta dma_src_mb
    lda #8
    sta dma_src_bank
    lda #0
    sta dma_src_lo
    sta dma_src_hi
    sta dma_dst_mb
    sta dma_dst_lo
    sta dma_dst_hi
    lda #4
    sta dma_dst_bank
    lda #$80
    sta dma_len_hi
    lda #0
    sta dma_len_lo
    jsr dma
    lda #0
    sta sequence
    sta sequence+1
    sta pending_post
    jsr new_scene
main:
    lda $d610
    beq main
    sta key
    sta $d610
    cmp #$58
    beq exit
    cmp #$78
    beq exit
    cmp #$31
    bcc not_scene
    cmp #$35
    bcs not_scene
    lda pending_post
    bne main
    lda key
    clc
    adc #$10
    sta profile
    jsr wait_vblank
    jsr restore_all
    jsr new_scene
    jmp main
not_scene:
    cmp #$48
    beq measure_hw
    cmp #$68
    beq measure_hw
    cmp #$45
    beq measure_xemu
    cmp #$65
    beq measure_xemu
    cmp #$53
    beq save_post_jump
    cmp #$73
    beq save_post_jump
    jmp main
save_post_jump:
    jmp save_post
exit:
    jsr restore_all
exit_restored:
    plp
    rts
measure_hw:
    lda #$48
    bne measure
measure_xemu:
    lda #$58
measure:
    sta requested_env
    lda pending_post
    bne main
    lda requested_env
    sta export_env
    inc sequence
    bne !+
    inc sequence+1
!:
    lda #0
    sta io_status
    sta measured_error
    sta export_kind
    sta indicator
    jsr marker_draw
    lda #1
    sta record_phase
    lda #5
    sta capture_bank
    jsr capture_snapshot // immediately before the measured KERNAL transaction
    jsr export_frozen
    lda io_status
    sta measured_error
    lda #1
    sta indicator // PST: separate photo state, no second file operation yet
    lda measured_error
    beq !+
    lda #3
    sta indicator
!:
    jsr rebuild_scene
    lda #2
    sta record_phase
    lda #4
    sta capture_bank
    jsr capture_snapshot // immediately after first export and scene restoration
    lda #1
    sta pending_post
    jmp main
save_post:
    lda pending_post
    beq save_done
    lda #1
    sta export_kind
    jsr export_frozen // serialize the ALREADY frozen POST state
    lda io_status
    bne save_failed
    lda #0
    sta pending_post
    lda #2
    sta indicator // END is deliberately not the photographed POST state
    lda measured_error
    beq save_rebuild
save_failed:
    lda #3
    sta indicator
save_rebuild:
    jsr rebuild_scene
save_done:
    jmp main
export_frozen:
    jsr restore_all
    cli
    jsr write_file
    sei
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    rts
new_scene:
    lda #0
    sta pending_post
    sta indicator
    sta measured_error
    sta io_status
    lda #$55
    sta export_env
    jsr rebuild_scene
    lda #1
    sta record_phase
    lda #5
    sta capture_bank
    jmp capture_snapshot // provisional PRE exists even if disk export fails
rebuild_scene:
    jsr video_init
    jmp scene
video_init:
    jsr wait_vblank
    lda initial_vic+$5d
    and #$7f
    sta $d05d
    lda #0
    sta $d015
    sta $d020
    sta $d021
    lda initial_vic+$11
    and #$6f
    sta $d011
    lda initial_vic+$16
    and #$e0
    ora #8
    sta $d016
    lda initial_vic+$30
    ora #5
    sta $d030
    lda initial_vic+$31
    and #$5f
    ora #$c0
    sta $d031
    lda initial_vic+$54
    ora #$55
    sta $d054
    lda #192
    sta $d058
    lda #0
    sta $d059
    sta $d060
    sta $d062
    sta $d064
    sta $d065
    sta $d068
    sta $d06a
    lda #$e0
    sta $d061
    lda #$40
    sta $d069
    lda initial_vic+$63
    and #$cf
    sta $d063
    lda #96
    sta $d05e
    lda #60
    sta $d05a
    lda #25
    sta $d07b
    // Same sprite-coordinate normalization as the stable engine.
    lda #0
    sta $d017
    sta $d01d
    sta $d055
    sta $d057
    sta $d05f
    sta $d06b
    sta $d077
    sta $d078
    lda $d04d
    and #$0f
    sta $d04d
    lda $d04f
    and #$0f
    sta $d04f
    lda #$ff
    sta $d076
    // Fixed profile E in BOTH variants, never the old S masks.
    // Explicit geometry: output timing (PAL/VGA) remains inherited.
    lda #$c0
    sta $d031
    lda #$55
    sta $d054
    lda #0
    sta $d063
    sta $d049
    sta $d04b
    sta $d04d
    sta $d04f
    sta $d05d
    // D051 contains write-only X-IRQ comparator bits: measure, do not disturb.
    lda #1
    sta $d05b
    lda initial_vic+$5c
    sta $d05c
    lda initial_vic+$5d
    and #$7f
    sta $d05d
    lda #80
    sta $d04c
    // Same PAL80x25 origin as the reference; explicit values come from baseline.
    lda initial_vic+$48
    sta $d048
    lda initial_vic+$49
    sta $d049
    lda initial_vic+$4a
    sta $d04a
    lda initial_vic+$4b
    sta $d04b
    lda initial_vic+$4c
    sta $d04c
    lda initial_vic+$4d
    and #$0f
    sta $d04d
    lda initial_vic+$4e
    sta $d04e
    lda initial_vic+$4f
    and #$0f
    sta $d04f
    lda #25
    sta $d07b
    lda $d07a
    and #$ef
    sta $d07a
video_palette:
    jsr apply_norrdel
    jmp scene_palette
scene:
    lda profile
    cmp #$44
    bne scene_text
    jsr copy_full_reference
    jmp scene_grid
scene_text:
    jsr plain_screen
scene_grid:
    // 375 NCM cells, source is one of sixteen 64-byte grid patterns.
    lda #0
    sta dma_dst_mb
    sta dma_src_mb
    sta dma_src_bank
    lda #1
    sta dma_dst_bank
    lda #$80
    sta dma_dst_hi
    lda #0
    sta dma_dst_lo
    sta row
    sta col
    sta dma_len_hi
    lda #64
    sta dma_len_lo
cell_loop:
    lda #0
    sta flags
    lda col
    bne !+
    inc flags
!:
    cmp #14
    bne !+
    lda flags
    ora #2
    sta flags
!:
    lda row
    bne !+
    lda flags
    ora #4
    sta flags
!:
    lda row
    cmp #24
    bne !+
    lda flags
    ora #8
    sta flags
!:
    lda flags
    lsr
    lsr
    clc
    adc #$88
    sta dma_src_hi
    lda flags
    and #3
    asl
    asl
    asl
    asl
    asl
    asl
    sta dma_src_lo
    jsr dma
    clc
    lda dma_dst_lo
    adc #64
    sta dma_dst_lo
    bcc !+
    inc dma_dst_hi
!:
    inc col
    lda col
    cmp #15
    bne cell_loop
    lda #0
    sta col
    inc row
    lda row
    cmp #25
    bne cell_loop
    // Static mono sprites: coordinate math identical to engine's origin transform.
    lda #0
    sta $d01c
    sta $d01b
    lda #$00
    sta $d06c
    lda #$93
    sta $d06d
    lda #$80
    sta $d06e
    lda #1
    sta $d027
    sta $d028
    sta $d029
    sta $d02a
    lda #0
    sta $d010
    sta $d05f
    sta $d077
    sta $d078
    ldx #0
sprite_loop:
    clc
    lda $d04c
    adc sprite_xlo,x
    sta sprite_add+1
    lda $d04d
    and #$0f
    adc sprite_xhi,x
    sta sprite_high
sprite_add:
    lda #0
    ldy sprite_offset,x
    sta $d000,y
    lda sprite_high
    and #1
    beq !+
    lda $d010
    ora sprite_bit,x
    sta $d010
!:
    lda sprite_high
    and #2
    beq !+
    lda $d05f
    ora sprite_bit,x
    sta $d05f
!:
    clc
    lda $d04e
    adc sprite_ylo,x
    sta $d001,y
    lda $d04f
    and #$0f
    adc #0
    sta sprite_high
    and #1
    beq !+
    lda $d077
    ora sprite_bit,x
    sta $d077
!:
    lda sprite_high
    and #2
    beq !+
    lda $d078
    ora sprite_bit,x
    sta $d078
!:
    inx
    cpx #4
    bne sprite_loop
    jsr marker_draw
    lda #$0c // only the two independent scene/phase markers
    ldx profile
    cpx #$44
    bne !+
    lda #$0f // full reference additionally enables original sprite and projectile
!:
    sta sprite_mask
    sta $d015
    lda initial_vic+$11
    and #$6f
    ora #$10
    sta $d011
    rts

copy_full_reference:
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_bank
    sta dma_dst_bank
    lda #<$a000
    sta dma_src_lo
    lda #>$a000
    sta dma_src_hi
    lda #<$e000
    sta dma_dst_lo
    lda #>$e000
    sta dma_dst_hi
    lda #<4800
    sta dma_len_lo
    lda #>4800
    sta dma_len_hi
    jsr dma
    lda #<$b300
    sta dma_src_lo
    lda #>$b300
    sta dma_src_hi
    lda #0
    sta dma_dst_lo
    sta dma_dst_hi
    lda #8
    sta dma_dst_bank
    lda #$ff
    sta dma_dst_mb
    jsr dma
    rts
// DMAgic F018A. Descriptor banks are physical: E000 is never CPU-aliased.
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
    .byte $0a,0,0
dma_len_lo: .byte 0
dma_len_hi: .byte 0
dma_src_lo: .byte 0
dma_src_hi: .byte 0
dma_src_bank: .byte 0
dma_dst_lo: .byte 0
dma_dst_hi: .byte 0
dma_dst_bank: .byte 0
    .word 0
// All four palettes backed up/restored, mapped bank is bits7:6 of D070.
backup_palettes:
    lda $d030
    and #$fe
    sta $d030
    .for(var b=0;b<4;b++) {
        lda #(b<<6)
        sta $d070
        ldx #0
    !loop:
        lda $d100,x
        sta $6000+b*$300,x
        lda $d200,x
        sta $6100+b*$300,x
        lda $d300,x
        sta $6200+b*$300,x
        inx
        bne !loop-
    }
    lda initial_vic+$70
    sta $d070
    rts
scene_palette:
    lda $d030
    and #$fe
    sta $d030
    lda #$40
    sta $d070
    ldx #0
!loop:
    lda palette_r,x
    sta $d110,x
    lda palette_g,x
    sta $d210,x
    lda palette_b,x
    sta $d310,x
    inx
    cpx #16
    bne !loop-
    lda #$ff
    sta $d101
    sta $d201
    sta $d301
    sta $d131
    sta $d231
    sta $d331
    sta $d132
    sta $d333
    lda #0
    sta $d100
    sta $d200
    sta $d300
    sta $d130
    sta $d230
    sta $d330
    sta $d232
    sta $d332
    sta $d133
    sta $d233
    lda #$80
    sta $d070
    lda #$ff
    sta $d101
    sta $d201
    sta $d301
    lda #$9a
    sta $d070
    rts
restore_all:
    lda $d030
    and #$fe
    sta $d030
    lda #0
    sta $d015
    .for(var b=0;b<4;b++) {
        lda #(b<<6)
        sta $d070
        ldx #0
    !loop:
        lda $6000+b*$300,x
        sta $d100,x
        lda $6100+b*$300,x
        sta $d200,x
        lda $6200+b*$300,x
        sta $d300,x
        inx
        bne !loop-
    }
    lda #0
    sta dma_src_mb
    sta dma_src_lo
    sta dma_src_hi
    sta dma_dst_lo
    sta dma_dst_hi
    sta dma_len_lo
    lda #4
    sta dma_src_bank
    lda #8
    sta dma_dst_bank
    lda #$ff
    sta dma_dst_mb
    lda #$80
    sta dma_len_hi
    jsr dma
restore_video:
    lda d051_restore_shadow
    sta $d051 // documented comparator high shadow, NOT live raster readback
    // Drain HOTREG recalculation before precise geometry restoration.
    lda initial_vic+$5d
    sta $d05d
    lda initial_vic+$11
    and #$7f
    sta hot11+1
    lda initial_vic+$7a
    and #1
    beq !+
    lda hot11+1
    ora #$80
    sta hot11+1
!:
hot11:
    lda #0
    sta $d011
    lda initial_vic+$16
    sta $d016
    lda initial_vic+$31
    sta $d031
    lda initial_vic+$5d
    and #$7f
    sta $d05d
    ldx #0
restore_loop:
    ldy restore_regs,x
    lda initial_vic,y
    sta $d000,y
    inx
    cpx #RESTORE_COUNT
    bne restore_loop
    lda initial_vic+$5d
    sta $d05d
    lda initial_vic+$1a
    sta $d01a
    rts
write_file:
    lda #0
    sta io_status
    sta file_open
    sta dos_open
    lda profile
    sec
    sbc #$41
    asl
    tax
    lda export_env
    cmp #$58
    bne !+
    inx
!:
    lda export_kind
    beq !+
    txa
    clc
    adc #8
    tax
!:
    lda scratch_lo,x
    sta scratch_name+1
    lda scratch_hi,x
    sta scratch_name+3
    lda name_lo,x
    sta filename+1
    lda name_hi,x
    sta filename+3
    jsr scratch_output
    bcc !+
    rts
!:
    lda #0
    tax
    jsr $ff6b // SETBNK before SETNAM, bank0 strings
filename:
    ldx #0
    ldy #0
    lda #15
    jsr $ffbd
    lda #2
export_device:
    ldx #8
    ldy #2
    jsr $ffba
    jsr $ffc0
    bcs io_fail
    lda #1
    sta file_open
    ldx #2
    jsr $ffc9
    bcs io_fail
    lda #5
    sec
    sbc export_kind
    sta stream_bank
    lda #0
    sta stream_lo
    sta stream_hi
    lda #<SNAPSHOT_SIZE
    sta remaining
    lda #>SNAPSHOT_SIZE
    sta remaining+1
stream_ready:
    lda #0
    sta stream_pos
file_loop:
    jsr stream_byte
    jsr $ffd2
    jsr $ffb7
    bne io_fail
    jsr dec_remaining
    bne file_loop
    jmp io_cleanup
io_fail:
    lda #1
    sta io_status
io_cleanup:
    jsr $ffcc
    lda #2
    clc // MEGA65 normal DOS CLOSE: flush, not merely retire logical channel
    jsr $ffc3
    bcc !+
    lda #1
    sta io_status
!:
    jsr $ffcc
    // DOS error channel catches disk-full/write-protect even after successful OPEN.
    lda #0
    tax
    jsr $ff6b
    lda #0
    ldx #0
    ldy #0
    jsr $ffbd
    lda #15
    ldx #8
    ldy #15
    jsr $ffba
    jsr $ffc0
    bcs dos_fail
    lda #1
    sta dos_open
    ldx #15
    jsr $ffc6
    bcs dos_fail
    jsr $ffcf
    sta dos_code
    jsr $ffb7
    bne dos_fail
    jsr $ffcf
    sta dos_code+1
    jsr $ffb7
    bne dos_fail
    lda dos_code
    cmp #$30
    bne dos_fail
    lda dos_code+1
    cmp #$30
    beq dos_cleanup
dos_fail:
    lda #2
    sta io_status
dos_cleanup:
    jsr $ffcc
    lda dos_open
    beq !+
    lda #15
    sec // retire status channel without closing unrelated DOS channels
    jsr $ffc3
!:
    rts
// MEGA65 DOS does not support @0: replacement reliably (observed DOS63).
// Only our selected diagnostic filename is scratched; no game files are touched.
scratch_output:
    lda #0
    tax
    jsr $ff6b
scratch_name:
    ldx #0
    ldy #0
    lda #12
    jsr $ffbd
    lda #15
    ldx #8
    ldy #15
    jsr $ffba
    jsr $ffc0
    bcs scratch_bad
    ldx #15
    jsr $ffc6
    bcs scratch_bad
    jsr $ffcf
    sta dos_code
    jsr $ffb7
    bne scratch_bad
    jsr $ffcf
    sta dos_code+1
    jsr $ffb7
    bne scratch_bad
    // Drain a bounded DOS response; no unbounded parser on malformed replies.
    lda #80
    sta dos_budget
scratch_drain:
    jsr $ffcf
    cmp #13
    beq scratch_checked
    jsr $ffb7
    and #$bf
    bne scratch_bad
    dec dos_budget
    bne scratch_drain
    jmp scratch_bad
scratch_checked:
    lda dos_code
    cmp #$30
    bne scratch_missing
    lda dos_code+1
    cmp #$30
    beq scratch_close
    cmp #$31
    beq scratch_close
scratch_missing:
    lda dos_code
    cmp #$36
    bne scratch_bad
    lda dos_code+1
    cmp #$32
    beq scratch_close
scratch_bad:
    lda #2
    sta io_status
scratch_close:
    jsr $ffcc
    lda #15
    sec
    jsr $ffc3
    jsr $ffcc
    lda io_status
    beq scratch_good
    sec
    rts
scratch_good:
    clc
    rts

#import "stage10b1b_helpers.asm"

profile: .byte $41
key: .byte 0
pending_post: .byte 0
indicator: .byte 0
record_phase: .byte 1
capture_bank: .byte 5
export_env: .byte $55
requested_env: .byte $55
sequence: .word 0
measured_error: .byte 0
sprite_mask: .byte $0c
remaining: .word 0
row: .byte 0
col: .byte 0
flags: .byte 0
sprite_high: .byte 0
io_status: .byte 0
file_open: .byte 0
dos_open: .byte 0
dos_code: .word 0
dos_budget: .byte 0
export_kind: .byte 0
d051_restore_shadow: .byte $1f
d051_shadow: .byte $1f
stream_bank: .byte 0
stream_lo: .byte 0
stream_hi: .byte 0
stream_pos: .byte 0
region_index: .byte 0
mem_sum: .word 0
saved_capture_pal: .byte 0
saved_capture_d030: .byte 0
text_base: .word $7000
row_dest: .word 0
text_col: .byte 0
slot: .byte 0
ncm_done: .byte 0
hud_goto_done: .byte 0
cell_value: .word 32
cell_flags: .byte 0
cell_colour: .byte 1
sprite_offset: .byte 0,2,4,6
sprite_bit: .byte 1,2,4,8
sprite_xlo: .byte <(112*2-3),<(232*2-3),<(8*2-3),<(24*2-3)
sprite_xhi: .byte >(112*2-3),>(232*2-3),>(8*2-3),>(24*2-3)
sprite_ylo: .byte 224,128,16,16
initial_vic: .fill 128,0
#import "tables.inc"
#import "names.inc"
.print "Controller end: " + toHexString(*)
.assert "Controller must end below charset", * < $4000, true
*=$4000 "Original menu charset"
.import binary "font.bin"
*=$4800 "Explicit write shadows"
write_shadows: .fill 16,0
*=$5000 "DMA streaming cache"
.fill 256,0
*=$5100 "Snapshot header and directory"
snap_header: .import binary "snapshot_header.bin"
*=$5400 "Actual four-bank palette readback"
.fill $c00,0
*=$6000 "Four original palette backups"
.fill $c00,0
*=$6c00 "CPU screen row"
.fill 192,0
*=$6d00 "CPU attribute row"
.fill 192,0
*=$7000 "Ordinary text source"
.import binary "scene_text.bin"
*=$7800 "Independent scene markers"
.import binary "scene_markers.bin"
*=$7900 "Independent phase markers"
.import binary "phase_markers.bin"
*=$8000 "Transparent NCM guard"
.fill 64,0
*=$8800 "Raster atlas"
.import binary "grid_atlas.bin"
*=$9040 "Original player NCM"
.import binary "player_ncm.bin"
*=$90c0 "Second guard"
.fill 64,0
*=$9200 "Reference and marker sprites"
.import binary "sprites.bin"
*=$9300 "16-bit sprite pointers"
.word $9200/64,$9240/64,$9280/64,$92c0/64
palette_r: .import binary "player_palette_r.bin"
palette_g: .import binary "player_palette_g.bin"
palette_b: .import binary "player_palette_b.bin"
*=$a000 "Full reference screen source"
.import binary "scene_screen.bin"
*=$b300 "Full reference colour source"
.import binary "scene_colour.bin"
