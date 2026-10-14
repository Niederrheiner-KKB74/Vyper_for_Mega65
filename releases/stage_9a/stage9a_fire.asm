// Issue63 / PR62: original event schedule, independent RNG, unchanged shot motion.
// Private bitmaps memoize the exact original logical Y[t]<=148 predicate.
.namespace fireevents {
*=$a600 "Stage7b5b current VYSH record (retired unused legacy frames)"
.label record=*
.fill 256,0
*=$a700 "Stage7b5b per-actor events and independent planning state"
.label first_lo=*; .fill 22,0
.label first_hi=*; .fill 22,0
.label second_lo=*; .fill 22,0
.label second_hi=*; .fill 22,0
.label pending=*; .fill 22,0
actor: .byte 0
group: .byte 0
ordinal: .byte 0
nth: .byte 0
mode: .byte 0
dy_original: .byte 0 // Original+6C; Stage7b5b motion applies DY1/2/3
bitmap_base: .fill 4,0
seed: .word $79b5
range: .word 0
lower: .word 0
value: .word 0
dividend: .word 0
remainder: .word 0
original_y: .word 0
sample_bit: .byte 0
scan: .byte 0
curve_index: .word 0
curve_y: .word 0
curve_byte: .byte 0
curve_delta: .byte 0
mask: .byte 0
.if (*>$a800) { .error "Event state exceeds retired legacy allocation" }
*=$a800 "Stage7b5b original ENTRY/ATTACK shot events"
init:
    // Called after complete bounded ENTRY/attack parsing on every level/reset.
    lda #0
    ldx #109
!clear:
    sta first_lo,x
    dex
    bpl !clear-
    lda #$b5
    sta seed
    lda #$79
    sta seed+1
    lda level.number
    sec
    sbc #1
    sta scan
    jsr fetch_record
    lda record
    sta dy_original
    lda record+1
    sta mode
    lda record+2
    sta nth
    lda #0
    ldx #11
!blank_maps:
    sta record,x
    inx
    bne !blank_maps-
    lda #12
    sta value
    ldx #0
!group:
    lda value
    sta bitmap_base,x
    // ceil(N/8), preserving 16-bit lengths up to469.
    clc
    lda entry.e_glen,x
    adc #7
    sta remainder
    lda entry.e_glenhi,x
    adc #0
    sta remainder+1
    .for (var i=0;i<3;i++) { lsr remainder+1; ror remainder }
    clc
    lda value
    adc remainder
    sta value
    inx
    cpx $7602
    bne !group-
    jsr build_maps
    lda #0
    sta actor
    sta ordinal
!actor:
    inc ordinal // global across groups, selection is every Nth enemy (1-based)
    lda ordinal
    cmp nth
    beq !selected+
    jmp !next+
!selected:
    lda #0
    sta ordinal
    ldx actor
    lda entry.e_group,x
    sta group
    tay
    tya
    asl
    tax
    lda record+3,x
    sta lower
    lda record+4,x
    sta lower+1
    ldx group
    sec
    lda entry.e_glen,x
    sbc lower
    sta range
    lda entry.e_glenhi,x
    sbc lower+1
    sta range+1
!sample:
    jsr random_range
    clc
    lda value
    adc lower
    sta value
    lda value+1
    adc lower+1
    sta value+1
    // Test memoized original Debut-Y, never the projected renderer coordinate.
    lda value
    and #7
    tax
    lda bit_table,x
    sta sample_bit
    lda value
    sta remainder
    lda value+1
    sta remainder+1
    .for (var i=0;i<3;i++) { lsr remainder+1; ror remainder }
    ldx group
    clc
    lda bitmap_base,x
    adc remainder
    tay
    lda record,y
    and sample_bit
    beq !sample-
    ldx actor
    lda value
    sta first_lo,x
    lda value+1
    sta first_hi,x
    lda mode
    cmp #2
    bne !next+
    // t2=(t1+15)%N, including one-byte ENTRY curves in special levels.
    clc
    lda value
    adc #15
    sta value
    lda value+1
    adc #0
    sta value+1
    ldy group
!modulo:
    lda value+1
    cmp entry.e_glenhi,y
    bcc !second+
    bne !subtract+
    lda value
    cmp entry.e_glen,y
    bcc !second+
!subtract:
    sec
    lda value
    sbc entry.e_glen,y
    sta value
    lda value+1
    sbc entry.e_glenhi,y
    sta value+1
    jmp !modulo-
!second:
    lda value
    sta second_lo,x
    lda value+1
    sta second_hi,x
!next:
    inc actor
    lda actor
    cmp $7603
    beq !done+
    jmp !actor-
!done:
    rts

// Reconstruct eligibility once per group from the actual loaded original bytes.
// This costs one bank1 byte-read per packed point, not one scan per sample/actor.
// Logical Y starts at the original group start and is never B2-projected here.
build_maps:
    lda #0
    sta group
!group:
    ldx group
    lda entry.e_gylo,x
    sta curve_y
    lda entry.e_gyhi,x
    sta curve_y+1
    lda entry.e_gptrlo,x
    sta level.read_pointer
    lda entry.e_gptrhi,x
    sta level.read_pointer+1
    lda #0
    sta curve_index
    sta curve_index+1
!point:
    jsr level.read_record
    and #15
    jsr entry.e_decode
    sta curve_delta
    clc
    adc curve_y
    sta curve_y
    lda #0
    bit curve_delta
    bpl !positive+
    lda #$ff
!positive:
    adc curve_y+1
    sta curve_y+1
    bmi !admit+
    bne !next+
    lda curve_y
    cmp #149
    bcs !next+
!admit:
    lda curve_index
    and #7
    tax
    lda bit_table,x
    sta sample_bit
    lda curve_index
    sta remainder
    lda curve_index+1
    sta remainder+1
    .for (var i=0;i<3;i++) { lsr remainder+1; ror remainder }
    ldx group
    clc
    lda bitmap_base,x
    adc remainder
    tay
    lda record,y
    ora sample_bit
    sta record,y
!next:
    inc level.read_pointer
    bne !pointer+
    inc level.read_pointer+1
!pointer:
    inc curve_index
    bne !index+
    inc curve_index+1
!index:
    ldx group
    lda curve_index+1
    cmp entry.e_glenhi,x
    beq !low+
    jmp !point-
!low:
    lda curve_index
    cmp entry.e_glen,x
    beq !end+
    jmp !point-
!end:
    inc group
    lda group
    cmp $7602
    beq !done+
    jmp !group-
!done:
    rts

// Verify every fixed-size original parameter record before entering the menu. CRC-16/CCITT-FALSE
// is pinned to the original-derived record, not merely a sum of received bytes.
validate_all:
    lda #0
    sta scan
!record:
    jsr fetch_record
    lda #$ff
    sta remainder
    sta remainder+1
    ldy #0
!byte:
    lda record,y
    eor remainder+1
    sta remainder+1
    ldx #8
!bit:
    asl remainder
    rol remainder+1
    bcc !next+
    lda remainder
    eor #$21
    sta remainder
    lda remainder+1
    eor #$10
    sta remainder+1
!next:
    dex
    bne !bit-
    iny
    cpy s3b.dma_len_lo
    bne !byte-
    ldx scan
    lda remainder
    cmp f_crc_lo,x
    bne invalid
    lda remainder+1
    cmp f_crc_hi,x
    bne invalid
    inc scan
    lda scan
    cmp #100
    bne !record-
    rts
!invalid:
invalid:
    lda #10
    sta s3b.error
    rts
fetch_record:
    ldx scan
    lda f_record_lo,x
    sta s3b.dma_src_lo
    lda f_record_hi,x
    clc
    adc #>F_BASE
    sta s3b.dma_src_hi
    lda f_record_size,x
    sta s3b.dma_len_lo
    lda #0
    sta s3b.dma_src_bank
    lda #0
    sta s3b.dma_dst_bank
    sta s3b.dma_dst_lo
    sta s3b.dma_len_hi
    lda #$a6
    sta s3b.dma_dst_hi
    jsr s3b.dma_copy
    rts

// 16-bit LFSR, modulo positive range in exactly16 division steps.
// This deliberately does NOT consume shots.p_random_*, used by attack selection.
random_range:
    lsr seed+1
    ror seed
    bcc !seed+
    lda seed+1
    eor #$b4
    sta seed+1
!seed:
    lda seed
    sta dividend
    lda seed+1
    sta dividend+1
    lda #0
    sta value
    sta value+1
    ldy #16
!divide:
    asl dividend
    rol dividend+1
    rol value
    rol value+1
    lda value+1
    cmp range+1
    bcc !next+
    bne !sub+
    lda value
    cmp range
    bcc !next+
!sub:
    sec
    lda value
    sbc range
    sta value
    lda value+1
    sbc range+1
    sta value+1
!next:
    dey
    bne !divide-
    rts

// Called only after an actual packed ENTRY step; zero countdown means inactive.
// Queue after decrement so initial t fires after t steps, at curve index t-1.
entry_tick:
    pha
    tya
    pha
    lda first_lo,x
    ora first_hi,x
    beq !second+
    lda first_lo,x
    bne !dec+
    dec first_hi,x
!dec:
    dec first_lo,x
    lda first_lo,x
    ora first_hi,x
    bne !second+
    lda pending,x
    ora #1
    sta pending,x
!second:
    lda second_lo,x
    ora second_hi,x
    beq tick_done
    lda second_lo,x
    bne !dec+
    dec second_hi,x
!dec:
    dec second_lo,x
    lda second_lo,x
    ora second_hi,x
    bne tick_done
    lda pending,x
    ora #2
    sta pending,x
tick_done:
    pla
    tay
    pla
    rts

// Restore the original formation coordinate basis for threshold planning/checks.
get_original_y:
    clc
    lda entry.e_ylo,x
    adc level.y_shift
    sta original_y
    lda entry.e_yhi,x
    adc #0
    sta original_y+1
    rts
attack_plan:
    stx actor
    lda #0
    sta first_lo,x
    sta first_hi,x
    sta second_lo,x
    sta second_hi,x
    sta pending,x
    jsr get_original_y
    lda original_y+1
    bne !done+ // Guard negative / >=256; no invalid modulus, no fallback event.
    lda original_y
    cmp #168
    bcs !done+ // Original random(168-Y) is undefined at/above168.
    sta lower
    lda #0
    sta range+1
    lda #168
    sec
    sbc lower
    sta range
    jsr random_range
    ldx actor
    clc
    lda value
    adc lower
    sta first_lo,x
    lda mode
    cmp #2
    bne !done+
    clc
    lda first_lo,x
    adc #20
    cmp #169
    bcc !second+
    sec
    sbc #32
!second:
    sta second_lo,x
!done:
    rts

attack_tick:
    pha
    tya
    pha
    jsr get_original_y
    lda original_y+1
    bpl !positive+
    jmp tick_done // Original negative-Y endmarker is not a shot event.
!positive:
    bne !first+ // positive 16-bit Y is beyond both thresholds
    lda first_lo,x
    beq !second+
    cmp original_y
    bcc !first+
    beq !first+
    bcs !second+
!first:
    lda first_lo,x
    beq !second+
    lda #0
    sta first_lo,x // consume BEFORE checking slot or spawn origin
    sta first_hi,x
    lda pending,x
    ora #1
    sta pending,x
!second:
    lda second_lo,x
    beq !done+
    lda original_y+1
    bne !second_fire+
    lda second_lo,x
    cmp original_y
    bcc !second_fire+
    beq !second_fire+
    bcs !done+
!second_fire:
    lda #0
    sta second_lo,x
    sta second_hi,x
    lda pending,x
    ora #2
    sta pending,x
!done:
    jmp tick_done

// Runs after B2 postframe: spawn from the actually displayed signed position.
// Two pending bits may independently consume two pool slots in the same frame.
flush:
    lda shots.p_test_enabled
    beq !normal+
    jmp shots.p_enemy_fire // optional historical T demo remains isolated
!normal:
    lda #0
    sta scan
!actor:
    ldx scan
    lda pending,x
    sta mask
    lda #0
    sta pending,x // no retries, including dead/hidden/invalid origins/full pool
    lda mask
    beq !next+
    lda level.mode
    bne !next+
    lda game.c_ps
    cmp #4
    beq !next+
    lda game.c_es,x
    cmp #3
    beq !eligible+
    cmp #2
    bne !next+
    lda entry.e_phase,x
    cmp #1
    beq !eligible+
    cmp #2 // final ENTRY point may already have handed off to RETURN this frame
    bne !next+
!eligible:
    jsr origin_ok
    bcc !next+
    stx attack.a_source
    lsr mask
    bcc !second+
    jsr attempt
!second:
    lsr mask
    bcc !next+
    jsr attempt
!next:
    inc scan
    lda scan
    cmp $7603
    bcc !actor-
    jmp attack.a_fire_count
origin_ok:
    // Same Stage7b4 signed muzzle bounds, now without per-owner quota.
    jsr entry.e_is_visible
    beq !no+
    ldx scan
    jsr attack.a_visible
    beq !no+
    clc
    lda entry.e_xlo,x
    adc #8
    tay
    lda entry.e_xhi,x
    adc #0
    bne !no+
    tya
    cmp #238
    bcs !no+
    clc
    lda entry.e_ylo,x
    adc #16
    tay
    lda entry.e_yhi,x
    adc #0
    bne !no+
    tya
    cmp #16
    bcc !no+
    cmp #184
    bcs !no+
    sec
    rts
!no:
    clc
    rts
attempt:
    ldx #2
!slot:
    lda shots.p_active,x
    beq !spawn+
    inx
    cpx #8
    bne !slot-
    rts
!spawn:
    jmp attack.a_fire_start // Stage7b5b original16.16 movement; event admission unchanged
bit_table: .byte 1,2,4,8,16,32,64,128
.import source "fire_layout.inc"
.if (*>F_BASE) { .error "Event engine overlaps resident VYSH file" }
.if ((F_BASE & $ff)!=0) { .error "SEQ destination must be page-aligned" }
*=F_BASE "Stage7b5b resident VYSH DAT in mapped physical chip RAM"
.fill F_BYTES,0
.if (*>$b480) { .error "Resident VYSH file overlaps unchanged starfield code" }
}
