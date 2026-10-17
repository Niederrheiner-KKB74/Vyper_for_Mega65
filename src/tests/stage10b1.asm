// Issue89: isolated, static VIC-IV/RRB diagnostic. No engine imports or audio writes.
.const DUMP=$4800
#import "constants.inc"
*=$2001 "BASIC"
BasicUpstart($2100)
*=$2100 "Diagnostic controller"
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
    lda #$53
    sta profile
    jsr init_dump
    lda #0
    jsr snapshot
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
    jsr run_profiles
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
    beq stage_mode
    cmp #$32
    beq explicit_mode
    cmp #$48
    beq export_hw
    cmp #$68
    beq export_hw
    cmp #$45
    beq export_xemu
    cmp #$65
    beq export_xemu
    jmp main
exit:
    jsr restore_all
exit_restored:
    plp
    rts
stage_mode:
    lda #$53
    bne change_mode
explicit_mode:
    lda #$45
change_mode:
    sta profile
    jsr restore_all
    jsr init_dump
    lda #0
    jsr snapshot
    jsr run_profiles
    jmp main
export_hw:
    lda #$48
    bne export
export_xemu:
    lda #$58
export:
    sta DUMP+10
    jsr checksum
    jsr restore_all
    cli
    jsr write_file
    sei
    lda #$47
    sta $d02f
    lda #$53
    sta $d02f
    jsr video_init
    jsr scene
    lda io_status
    beq export_ok
    lda #2
    bne export_border
export_ok:
    lda #5
export_border:
    sta $d020
    jmp main
run_profiles:
    jsr video_init
    lda #1
    jsr snapshot
    jsr simulate_title_menu
    jsr restore_video
    jsr video_init
    lda #2
    jsr snapshot
    jsr scene
    lda #3
    jsr snapshot
    jmp checksum
// Exact header and three-byte address/value records. No zero-page clobber.
init_dump:
    lda #<DUMP
    sta put+1
    lda #>DUMP
    sta put+2
    ldx #0
header_loop:
    lda header,x
    jsr put
    inx
    cpx #32
    bne header_loop
    lda profile
    sta DUMP+9
    rts
snapshot:
    sta phase
    tax
    lda block_lo,x
    sta put+1
    lda block_hi,x
    sta put+2
    txa
    clc
    adc #1
    jsr put
    lda profile
    jsr put
    lda $d012
    jsr put
    lda $d011
    jsr put
    ldx #0
snapshot_loop:
    lda reg_lo,x
    sta read_reg+1
    jsr put
    lda reg_hi,x
    sta read_reg+2
    jsr put
read_reg:
    lda $d000
    jsr put
    inx
    cpx #REG_COUNT
    bne snapshot_loop
    rts
put:
    sta DUMP
    inc put+1
    bne !+
    inc put+2
!:
    rts
checksum:
    lda #0
    sta DUMP+28
    sta DUMP+29
    sta sum_lo
    sta sum_hi
    lda #<DUMP
    sta sum_read+1
    lda #>DUMP
    sta sum_read+2
    lda #<DUMP_SIZE
    sta remaining
    lda #>DUMP_SIZE
    sta remaining+1
sum_loop:
sum_read:
    lda DUMP
    clc
    adc sum_lo
    sta sum_lo
    bcc !+
    inc sum_hi
!:
    inc sum_read+1
    bne !+
    inc sum_read+2
!:
    jsr dec_remaining
    bne sum_loop
    lda sum_lo
    sta DUMP+28
    lda sum_hi
    sta DUMP+29
    rts
dec_remaining:
    lda remaining
    bne !+
    dec remaining+1
!:
    dec remaining
    lda remaining
    ora remaining+1
    rts
// Mirror the stable game's final HUD geometry masks, without running gameplay.
video_init:
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
    lda profile
    cmp #$45
    bne video_palette
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
    jmp scene_palette
// Geometry-only simulation of stable title/menu, followed by the same restore
// ordering. No title assets or files are loaded by this diagnostic.
simulate_title_menu:
    lda $d016
    and #$e0
    ora #8
    sta $d016
    lda $d07a
    and #$ef
    sta $d07a
    lda $d031
    and #$47
    ora #$40
    sta $d031
    lda #$45
    sta $d054
    lda #$50
    sta $d070
    lda #0
    sta $d060
    sta $d062
    sta $d063
    sta $d064
    sta $d059
    sta $d049
    sta $d04d
    sta $d04f
    sta $d05d
    lda #$70
    sta $d061
    lda #$20
    sta $d065
    lda #88
    sta $d058
    lda #44
    sta $d05e
    lda #29
    sta $d07b
    lda #120
    sta $d05a
    lda #1
    sta $d05b
    lda #40
    sta $d05c
    lda #48
    sta $d04c
    sta $d04e
    sta $d048
    lda #<528
    sta $d04a
    lda #>528
    sta $d04b
    // Menu geometry, as distinct from title geometry.
    lda #$90
    sta $d061
    lda #80
    sta $d058
    sta $d04c
    lda #40
    sta $d05e
    lda #24
    sta $d07b
    lda #88
    sta $d04e
    sta $d048
    lda #<488
    sta $d04a
    lda #>488
    sta $d04b
    rts
scene:
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
    cpx #2
    bne sprite_loop
    lda #3
    sta $d015
    lda initial_vic+$11
    and #$6f
    ora #$10
    sta $d011
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
    rts
// SEQ export. Caller restores BASIC geometry and enables IRQ before KERNAL I/O.
write_file:
    lda #0
    sta io_status
    sta file_open
    sta dos_open
    ldx #0
    lda profile
    cmp #$45
    bne !+
    ldx #2
!:
    lda DUMP+10
    cmp #$58
    bne !+
    inx
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
    lda #16
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
    lda #<DUMP
    sta file_read+1
    lda #>DUMP
    sta file_read+2
    lda #<DUMP_SIZE
    sta remaining
    lda #>DUMP_SIZE
    sta remaining+1
file_loop:
file_read:
    lda DUMP
    jsr $ffd2
    jsr $ffb7
    bne io_fail
    inc file_read+1
    bne !+
    inc file_read+2
!:
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
    lda #13
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
header:
    .text "VYDG10B1"
    .byte 1,$53,$55,4
    .word REG_COUNT,BLOCK_SIZE
    .dword DUMP_SIZE
    .fill 8,0
    .word 0
    .byte 1,1
profile: .byte $53
phase: .byte 0
key: .byte 0
remaining: .word 0
sum_lo: .byte 0
sum_hi: .byte 0
row: .byte 0
col: .byte 0
flags: .byte 0
sprite_high: .byte 0
io_status: .byte 0
file_open: .byte 0
dos_open: .byte 0
dos_code: .word 0
dos_budget: .byte 0
sprite_offset: .byte 0,2
sprite_bit: .byte 1,2
sprite_xlo: .byte <(112*2-3),<(232*2-3)
sprite_xhi: .byte >(112*2-3),>(232*2-3)
sprite_ylo: .byte 224,128
name_lo: .byte <nsh,<nsx,<neh,<nex
name_hi: .byte >nsh,>nsx,>neh,>nex
nsh: .text "0:V10BSH.DAT,S,W"
nsx: .text "0:V10BSX.DAT,S,W"
neh: .text "0:V10BEH.DAT,S,W"
nex: .text "0:V10BEX.DAT,S,W"
scratch_lo: .byte <ssh,<ssx,<seh,<sex
scratch_hi: .byte >ssh,>ssx,>seh,>sex
ssh: .text "S0:V10BSH.DAT"
ssx: .text "S0:V10BSX.DAT"
seh: .text "S0:V10BEH.DAT"
sex: .text "S0:V10BEX.DAT"
initial_vic: .fill 128,0
#import "registers.inc"
.print "Controller end: " + toHexString(*)
.assert "Controller must end below charset", * < $4000, true
*=$4000 "Original menu charset"
.import binary "font.bin"
*=$4800 "Persistent diagnostic buffer"
.fill DUMP_SIZE,0
*=$6000 "Four palette backups"
.fill $c00,0
*=$8000 "Transparent NCM guard"
.fill 64,0
*=$8800 "Grid pattern atlas"
.import binary "grid_atlas.bin"
*=$9040 "Original player NCM (diagnostic pixie)"
.import binary "player_ncm.bin"
*=$90c0 "Transparent NCM guard 2"
.fill 64,0
*=$9200 "Mono sprite test patterns"
.import binary "sprites.bin"
*=$9300 "16bit sprite pointers"
.word $9200/64,$9240/64
palette_r: .import binary "player_palette_r.bin"
palette_g: .import binary "player_palette_g.bin"
palette_b: .import binary "player_palette_b.bin"
*=$a000 "Physical scene screen source"
.import binary "scene_screen.bin"
*=$b300 "Physical scene colour source"
.import binary "scene_colour.bin"
