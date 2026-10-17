// Issue95: isolated H640/60 versus H320/120. No active-scene KERNAL I/O.
#import "constants.inc"
*=$2001 "BASIC"
BasicUpstart($2100)
*=$2100 "H320 GOTOX diagnostic"
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
    jsr backup_palettes
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
    sta dma_len_lo
    lda #4
    sta dma_dst_bank
    lda #$80
    sta dma_len_hi
    jsr dma
    lda #0
    sta mode
    sta sequence
    sta sequence+1
    jsr rebuild
main:
    lda $d610
    beq main
    sta $d610
    cmp #$58
    beq exit
    cmp #$78
    beq exit
    cmp #$31
    beq select_a
    cmp #$32
    beq select_b
    cmp #$52
    beq repeat
    cmp #$72
    beq repeat
    cmp #$44
    beq sample_only
    cmp #$64
    beq sample_only
    jmp main
select_a:
    lda #0
    beq select
select_b:
    lda #1
select:
    sta mode
repeat:
    jsr rebuild
    jmp main
sample_only:
    jsr capture
    jmp main
exit:
    jsr restore_all
exit_restored:
    plp
    rts
rebuild:
    jsr video_init
    jsr build_screen
    jsr scene_grid
    inc sequence
    bne !+
    inc sequence+1
!:
    jmp capture
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
    lda #96
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
    lda #48
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
    lda mode
    beq !+
    lda #$40
    bne !done+
!:
    lda #$c0
!done:
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
    lda #0
    sta $d07a // deterministic compare source, sprite pointer monitoring, CHARY16
    sta $d079
    sta $d053 // write only output-control bits5/6, never live raster bits
    sta $d01a // no diagnostic IRQ sources enabled
    lda #$1f
    sta $d051 // NORRDEL0 DBLRR0, known unused X comparator high bits
    lda mode
    beq !+
    lda #120
    bne !done+
!:
    lda #60
!done:
    sta $d05a
    lda #104
    sta $d048
    sta $d04e
    lda #0
    sta $d049
    sta $d04b
    sta $d04d
    sta $d04f
    lda #<504
    sta $d04a
    lda #>504
    sta $d04b
    lda #80
    sta $d04c
    lda #0
    sta $d05c
    sta $d05d // HOTREG0 and rasterdelay0; side-border low is set below
    lda #80
    sta $d05c
    jsr init_palettes
    jmp scene_palette

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
    adc sprite_yhi,x
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
    jsr variant_marker
    lda #$0f
    sta $d015
    lda initial_vic+$11
    and #$6f
    ora #$10
    sta $d011
    rts

build_screen:
    // Generated command slots only. B takes the raw logical word; no ASL.
    .for(var base=0; base<PATCH_COUNT; base+=240) {
    ldx #0
!patch_loop:
    lda patch_lo+base,x
    sta !patch_low+ +1
    sta !patch_high+ +1
    lda patch_hi+base,x
    sta !patch_low+ +2
    sta !patch_high+ +2
    inc !patch_high+ +1
    bne !+
    inc !patch_high+ +2
!:
    lda mode
    beq !patch_a+
    lda goto_b_lo+base,x
    sta patch_value_lo
    lda goto_b_hi+base,x
    jmp !patch_store+
!patch_a:
    lda goto_a_lo+base,x
    sta patch_value_lo
    lda goto_a_hi+base,x
!patch_store:
!patch_high:
    sta $a001
    lda patch_value_lo
!patch_low:
    sta $a000
    inx
    cpx #min(240,PATCH_COUNT-base)
    bne !patch_loop-
    }
    lda #0
    sta dma_src_mb
    sta dma_dst_mb
    sta dma_src_bank
    sta dma_dst_bank
    sta dma_len_hi
    lda #<$a000
    sta dma_src_lo
    lda #>$a000
    sta dma_src_hi
    lda #<$e000
    sta dma_dst_lo
    lda #>$e000
    sta dma_dst_hi
    lda #<2400
    sta dma_len_lo
    lda #>2400
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
    // Initialize the extra row identically rather than inherit random CRAM.
    lda #0
    sta dma_src_mb
    sta dma_src_bank
    lda #<zero_row
    sta dma_src_lo
    lda #>zero_row
    sta dma_src_hi
    lda #<2400
    sta dma_dst_lo
    lda #>2400
    sta dma_dst_hi
    lda #96
    sta dma_len_lo
    lda #0
    sta dma_len_hi
    jsr dma
    lda #0
    sta dma_dst_mb
    sta dma_dst_bank
    lda #<($e000+2400)
    sta dma_dst_lo
    lda #>($e000+2400)
    sta dma_dst_hi
    jmp dma
variant_marker:
    ldx #0
    lda mode
    beq !+
    ldx #64
!:
    ldy #0
!loop:
    lda variant_markers,x
    sta $9280,y
    inx
    iny
    cpy #64
    bne !loop-
    rts
init_palettes:
    // Every bank deterministic; original palettes are preserved at6000.
    lda $d030
    and #$fe
    sta $d030
    .for(var b=0;b<4;b++) {
        lda #(b<<6)
        sta $d070
        ldx #0
        lda #0
    !loop:
        sta $d100,x
        sta $d200,x
        sta $d300,x
        inx
        bne !loop-
    }
    rts
wait_vblank:
    lda $d053
    and #7
    cmp #2
    bne wait_vblank
    lda $d052
    cmp #16
    bcc wait_vblank
    rts
capture:
    lda mode
    clc
    adc #$41
    sta snapshot+9
    lda sequence
    sta snapshot+10
    lda sequence+1
    sta snapshot+11
    lda #$1f
    sta snapshot+12
    lda d051_restore_shadow
    sta snapshot+13
    lda #0
    sta snapshot+14 // explicit D07A write shadow
    sta snapshot+15 // explicit IRQ mask
    lda #<(snapshot+32)
    sta put+1
    lda #>(snapshot+32)
    sta put+2
    ldx #0
capture_loop:
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
    bne capture_loop
    rts
put:
    sta snapshot+32
    inc put+1
    bne !+
    inc put+2
!:
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
    lda initial_vic+$53
    and #$60
    sta $d053
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

mode: .byte 0
sequence: .word 0
row: .byte 0
col: .byte 0
flags: .byte 0
sprite_high: .byte 0
patch_value_lo: .byte 0
d051_restore_shadow: .byte $1f
sprite_offset: .byte 0,2,4,6
sprite_bit: .byte 1,2,4,8
sprite_xlo: .byte <(112*2-3),<(224*2-3),<(8*2-3),<(24*2-3)
sprite_xhi: .byte >(112*2-3),>(224*2-3),>(8*2-3),>(24*2-3)
sprite_ylo: .byte <320,<352,16,16
sprite_yhi: .byte >320,>352,0,0
initial_vic: .fill 128,0
zero_row: .fill 96,0
#import "tables.inc"
.assert "Code below charset", * < $4000, true
*=$4000 "Original menu font"
.import binary "font.bin"
*=$4800 "Read-only diagnostic register sample"
snapshot:
.text "VYDG1B1C"
.byte 1,$41,0,0,$1f,$1f,0,0
.word REG_COUNT,SNAPSHOT_SIZE
.fill 12,0
.fill REG_COUNT*3,0
*=$6000 "Original palette backup"
.fill $c00,0
*=$7800 "Independent A B variant markers"
variant_markers: .import binary "variant_markers.bin"
*=$8000 "Transparent NCM guard"
.fill 64,0
*=$8100 "One logical pixel probe line"
.import binary "probe.bin"
*=$8800 "Raster atlas"
.import binary "grid_atlas.bin"
*=$9040 "Original player NCM"
.import binary "player_ncm.bin"
*=$9200 "Reference sprites and independent variant/NOIO markers"
.import binary "sprites.bin"
*=$9300 "Sprite pointers"
.word $9200/64,$9240/64,$9280/64,$92c0/64
palette_r: .import binary "player_palette_r.bin"
palette_g: .import binary "player_palette_g.bin"
palette_b: .import binary "player_palette_b.bin"
*=$a000 "Screen template with patched GOTOX words"
.import binary "scene_screen.bin"
*=$b300 "Common attributes"
.import binary "scene_colour.bin"
