// Stage7b4: bounded eligibility lists; unbiased power-of-two rejection sampling.
*=$9c00 "Stage7b4 eligible actor collection and uniform rank selection"
.namespace selection {
.label count=$1f96
.label mask=$1f97
.label scan=$1f98
.label kind=$1f99
.label owner_candidate=$1f9a
.label owner_count=$1f9b
.const ENEMY_PROJECTILE_LIMIT=2
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
    jmp owner_room // Carry reflects original shooter quota. X remains actor slot.
!no:
    clc
    rts
// Count only active enemy projectiles, never player slots0/1 or stale owners.
// X=original enemy slot, preserved. A/Y clobbered; C=1 if another shot fits.
owner_room:
    stx owner_candidate
    lda #0
    sta owner_count
    ldy #2
!slot:
    lda shots.p_active,y
    beq !next+
    lda shots.p_source_enemy,y
    cmp owner_candidate
    bne !next+
    inc owner_count
    lda owner_count
    cmp #ENEMY_PROJECTILE_LIMIT
    bcs !full+
!next:
    iny
    cpy #8
    bne !slot-
    sec
    rts
!full:
    clc
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
