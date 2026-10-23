// Issue65. Original per-update mathematics; projected engine-world coordinates.
.namespace motion {
.label xhi=$1f9a // signed WORD high bytes; low arrays remain baseline
.label yhi=xhi+8
.label targethi=yhi+8
.label sign=targethi+8
.label seed=sign+8
.label dx=seed+2
.label dxhi=dx+1
.label denom=dxhi+1
.label rem=denom+1 //16bit long-division remainder
.label quot=rem+2 //16bit quotient, floor before multiplication by DY
.label spread=quot+2
.label integer=spread+1
.label format=integer+1 //0 legacy-T8.8;1 original16.16, retained per projectile
.if (format+8>$2000) { .error "Motion state overlaps BASIC PRG" }

*=$76b5 "Stage7b5b independent motion reset"
reset:
    lda #0
    ldx #(format+7-xhi)
!clear:
    sta xhi,x
    dex
    bpl !clear-
    lda #$5b
    sta seed
    lda #$7b
    sta seed+1
    rts
mark_legacy:
    stx shots.p_slot
    lda #0
    sta format,x
    rts
.if (*>$7700) { .error "Motion reset overlaps entry projection" }

*=$4fb2 "Stage7b5b independent spread RNG"
random:
    lsr seed+1
    ror seed
    bcc !value+
    lda seed+1
    eor #$b4
    sta seed+1
!value:
    lda seed
!mod:
    cmp #20
    bcc !done+
    sec
    sbc #20
    bcs !mod-
!done:
    sta spread
    rts
.if (*>$5000) { .error "Spread RNG overlaps BASIC backup" }

*=$2f50 "Stage7b5b native shot origin and spread"
spawn:
    stx shots.p_slot // caller already reserved a free global slot2..7
    jsr random // only successful admissions consume motion RNG
    lda #0
    sta targethi,x
    sta shots.p_xfrac,x
    sta shots.p_yfrac,x
    sta shots.p_vxfrac,x
    sta shots.p_vyfrac,x
    lda entry.e_ticklo // original update-counter parity: odd plus, even minus
    and #1
    beq !minus+
    lda V014_PLAYER+2
    clc
    adc spread
    sta shots.p_target_x,x
    jmp !centre+
!minus:
    lda V014_PLAYER+2
    sec
    sbc spread
    sta shots.p_target_x,x
    lda #0
    sbc #0
    sta targethi,x
!centre:
    // Native record is left edge; engine state is projectile centre: +1 both sides.
    inc shots.p_target_x,x
    bne !target+
    inc targethi,x
!target:
    lda V014_PLAYER+4
    sta shots.p_target_y,x
    ldy attack.a_source
    lda entry.e_xlo,y
    clc
    adc #8 // native enemyX+7 left edge, plus centre offset1
    sta shots.p_xpos,x
    lda entry.e_xhi,y
    adc #0
    sta xhi,x
    lda entry.e_ylo,y
    sec
    sbc #7 // native enemyY-7, in the SAME projected engine-world space
    sta shots.p_ypos,x
    lda entry.e_yhi,y
    sbc #0
    sta yhi,x
    lda fireevents.dy_original
    sta shots.p_vy,x
    lda attack.a_source
    sta shots.p_source_enemy,x
    jmp aim
.if (*>$3000) { .error "Shot spawn overlaps backup" }

*=$3558 "Stage7b5b signed native aim delta"
aim:
    lda shots.p_target_x,x
    sec
    sbc shots.p_xpos,x
    sta dx
    lda targethi,x
    sbc xhi,x
    sta dxhi
    and #$80
    beq !positive+
    lda #$ff
    sta sign,x
    lda #0
    sec
    sbc dx
    sta dx
    lda #0
    sbc dxhi
    sta dxhi
    jmp !distance+
!positive:
    lda #0
    sta sign,x
!distance:
    lda shots.p_target_y,x
    sec
    sbc shots.p_ypos,x
    sta denom
    lda #0
    sbc yhi,x
    bne cap // nonpositive or >255 separation cannot arise through normal admission
    lda denom
    beq cap
    lda dxhi
    bne cap
    lda dx
    cmp denom
    bcs cap
    sta rem
    lda #0
    sta rem+1
    sta quot
    sta quot+1
    ldy #16
    jmp divide
cap:
    lda shots.p_vy,x
    sta shots.p_vx,x
    lda #0
    sta shots.p_vxfrac,x
    sta shots.p_vyfrac,x
    jmp activate
.if (*>$3600) { .error "Aim overlaps player original" }

*=$3768 "Stage7b5b native16.16 quotient"
divide:
    asl rem
    rol rem+1
    asl quot
    rol quot+1
    lda rem+1
    bne !subtract+
    lda rem
    cmp denom
    bcc !next+
!subtract:
    lda rem
    sec
    sbc denom
    sta rem
    lda rem+1
    sbc #0
    sta rem+1
    inc quot // low bit was cleared by ASL
!next:
    dey
    bne divide
    // Native DIVU floor is taken BEFORE multiplying the fraction by DY.
    lda #0
    sta shots.p_vx,x
    ldy shots.p_vy,x
!multiply:
    clc
    lda shots.p_vyfrac,x
    adc quot
    sta shots.p_vyfrac,x
    lda shots.p_vxfrac,x
    adc quot+1
    sta shots.p_vxfrac,x
    lda shots.p_vx,x
    adc #0
    sta shots.p_vx,x
    dey
    bne !multiply-
activate:
    lda #1
    sta shots.p_active,x
    sta format,x
    jsr audio8.enemy_shot
    jmp attack.a_fire_count
.if (*>$3800) { .error "Direction overlaps HUD" }

*=$788a "Stage7b5b native projectile update"
update:
    clc
    lda shots.p_ypos,x
    adc shots.p_vy,x
    sta shots.p_ypos,x
    lda yhi,x
    adc #0
    sta yhi,x
    bmi !x+
    bne !kill+
    lda shots.p_ypos,x
    cmp #200
    bcc !x+
!kill:
    jsr shots.p_deactivate
    jmp shots.p_update_next
!x:
    clc
    lda shots.p_yfrac,x
    adc shots.p_vyfrac,x
    sta shots.p_yfrac,x
    lda shots.p_xfrac,x
    adc shots.p_vxfrac,x
    sta shots.p_xfrac,x
    lda shots.p_vx,x
    adc #0
    sta integer
    lda sign,x
    bpl !positive+
    jmp negative
!positive:
    lda shots.p_xpos,x
    clc
    adc integer
    sta shots.p_xpos,x
    lda xhi,x
    adc #0
    sta xhi,x
    jmp shots.p_update_next
.if (*>$7900) { .error "Update overlaps phase gate" }

*=$85fc "Stage7b5b signed negative projectile step"
negative:
    lda shots.p_xpos,x
    sec
    sbc integer
    sta shots.p_xpos,x
    lda xhi,x
    sbc #0
    sta xhi,x
    jmp shots.p_update_next
.if (*>$8660) { .error "Signed step overlaps offscreen movement" }

*=$9cee "Stage7b5b signed sprite and collision gate"
visible:
    lda shots.p_active,x
    beq !no+
    lda format,x
    beq !yes+ // per-shot format survives T toggles
    cpx #2
    bcc !yes+ // player path and bounds unchanged
    lda xhi,x
    ora yhi,x
    bne !no+
    lda shots.p_xpos,x
    cmp #1
    bcc !no+
    cmp #239
    bcs !no+
    lda shots.p_ypos,x
    cmp #200
    bcs !no+
!yes:
    sec
    rts
!no:
    clc
    rts
.if (*>$9d30) { .error "Signed gate overlaps VYSH filename" }
*=$7954 "Stage7b5b isolated historical-T8.8 update"
legacy_update:
    clc
    lda shots.p_xfrac,x
    adc shots.p_vxfrac,x
    sta shots.p_xfrac,x
    lda shots.p_xpos,x
    adc shots.p_vx,x
    sta shots.p_xpos,x
    cmp #1
    bcc !kill+
    cmp #239
    bcs !kill+
    clc
    lda shots.p_yfrac,x
    adc shots.p_vyfrac,x
    sta shots.p_yfrac,x
    lda shots.p_ypos,x
    adc shots.p_vy,x
    sta shots.p_ypos,x
    cmp #197
    bcc !done+
!kill:
    jsr shots.p_deactivate
!done:
    jmp shots.p_update_next
.if (*>$79dd) { .error "Legacy update overlaps global shot count" }

}
