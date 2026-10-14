// Stage7b5a: bounded eligibility lists; unbiased power-of-two rejection sampling.
*=$9c00 "Stage7b5a eligible actor collection and uniform rank selection"
.namespace selection {
.label count=$1f96
.label mask=$1f97
.label scan=$1f98
.label kind=$1f99
.label actors=$1f80 //22 entries, after 120-byte projectile state1F00..1F77
collect:
    sta kind
    lda #0
    sta count
    sta scan
    lda level.mode
    bne done
    lda game.c_ps
    cmp #4
    beq done
!actor:
    ldx scan
    lda kind
    bne !fire+
    lda game.c_es,x
    cmp #1
    bne !next+
    lda entry.e_phase,x
    cmp #3
    bne !next+
    beq !add+
!fire:
    jsr fire_eligible
    bcc !next+
!add:
    ldy count
    txa
    sta actors,y
    inc count
!next:
    inc scan
    lda scan
    cmp $7603
    bcc !actor-
done:
    rts
choose:
    lda count
    beq no_choice
    lda #1
!mask:
    cmp count
    bcs !sample+
    asl
    bne !mask-
!sample:
    sec
    sbc #1
    sta mask
    jsr shots.p_random_step
    lda shots.p_random_lo
    and mask
    cmp count
    bcs no_choice // Return; never a busy-loop. Caller retries next frame.
    tax
    lda actors,x
    tax
    sec
    rts
no_choice:
    clc
    rts
fire_eligible:
    lda game.c_es,x
    cmp #3
    beq !visible+
    cmp #2
    bne !no+
    lda entry.e_phase,x
    cmp #1
    bne !no+
!visible:
    jsr entry.e_is_visible
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
// Legacy T path compatibility only: no per-owner quota remains.
owner_room:
    sec
    rts
// Exact8-sprite restoration without enabling IRQ against active game RRB.
restore_sprites:
    php
    sei
    jsr transitionfx.restore_shared
    lda VIC_HOTREG
    pha
    and #$7f
    sta VIC_HOTREG
    sta VIC_HOTREG
    lda #0
    sta $d015
    ldx #42
!register:
    lda shots.register_offsets,x
    cmp #$15
    beq !skip+
    sta restore_write+1
    lda shots.p_saved_registers,x
restore_write:
    sta $d000
!skip:
    dex
    bpl !register-
    pla
    sta VIC_HOTREG
    plp
    rts
.if (*>$9d70) { .error "Selection helpers overlap RRB renderer" }
}

*=$9d30 "Stage7b5a VYSH filename and pinned header"
.namespace fireload {
filename: .text "VYSH.DAT,S,R"
.byte 0
expected: .import binary "VYSH.DAT",0,16
}
.if (*>$9d70) { .error "VYSH loader constants overlap renderer" }

.namespace fireload {
verify_all:
    php
    sei // all channels already closed; never run KERNAL with its mapping changed
    lda $d030
    pha
    and #$ef // ROMA off only for the new RAM-resident validator
    sta $d030
    jsr fireevents.validate_all
    pla
    sta $d030
    plp
    rts
}
.if (*>$9d70) { .error "VYSH verification gate overlaps renderer" }
