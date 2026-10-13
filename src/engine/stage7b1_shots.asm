// Stage 3b-5b: independent sprite projectiles. No collision/score/life writes.
*=$8200 "Stage 3b-5b projectile core"
.namespace shots {
.const p_state=$1b00
.label p_active=p_state
.label p_xfrac=p_state+6
.label p_xpos=p_state+12
.label p_yfrac=p_state+18
.label p_ypos=p_state+24
.label p_vxfrac=p_state+30
.label p_vx=p_state+36
.label p_vyfrac=p_state+42
.label p_vy=p_state+48
.label p_target_x=p_state+54
.label p_target_y=p_state+60
.label p_source_enemy=p_state+66
.label p_fire_latch=p_state+72
.label p_random_lo=p_state+73
.label p_random_hi=p_state+74
.label p_cooldown=p_state+75
.label p_test_enabled=p_state+76
.label p_attack_tick=p_state+77
.label p_attacking=p_state+78
.label p_slot=p_state+79
.label p_enabled_mask=p_state+80
.label p_xmsb=p_state+81
.label p_xbit9=p_state+82
.label p_ymsb=p_state+83
.label p_ybit9=p_state+84
.label p_sx=p_state+85
.label p_sy=p_state+87
.label p_dx=p_state+89
.label p_negative=p_state+90
.label p_denominator=p_state+91
.label p_numerator=p_state+92
.label p_remainder=p_state+94
.label p_saved_registers=p_state+96
.const p_player_speed=3
.const p_enemy_speed=1
.const p_fire_cooldown=12
.const p_initial_cooldown=25
.const p_test_enemy=18
.const p_enemy_right=239
.const p_enemy_bottom=197
.const p_pointers=$8900
.const p_player_graphic=$8a00
.const p_enemy_graphic=$8a40

p_startup:
    lda #$47
    sta VIC_KEY
    lda #$53
    sta VIC_KEY
    jsr p_save_registers
    jsr p_disable
    jsr hud.startup
    jsr p_restore_registers
    rts
p_disable:
    lda #0
    sta VIC_SPREN
    rts
p_map_type:
    tax
    lda p_mapping,x
    rts
p_get_key:
    jsr KERNAL_GETIN
    cmp #$54 // T toggles only isolated test attack, other keys retain meaning.
    bne p_key_done
    pha
    lda p_test_enabled
    eor #1
    sta p_test_enabled
    pla
p_key_done:
    rts
p_engine_init:
    jsr hud.hud_init
    jmp p_init
p_init:
    ldx #95
    lda #0
p_init_state:
    sta p_state,x
    dex
    bpl p_init_state
    lda #0 // Explicit T test only; never claim random generator as original entry.
    sta p_test_enabled
    lda #p_initial_cooldown
    sta p_cooldown
    lda $dc04
    eor $d012
    sta p_random_lo
    lda $dc05
    eor $d011
    sta p_random_hi
    ora p_random_lo
    bne p_seed_ok
    lda #$e1
    sta p_random_lo
    lda #$ac
    sta p_random_hi
p_seed_ok:
    lda #0
    sta $d015
    sta $d017
    sta $d01b
    sta $d01c
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
    lda #$3f
    sta $d076 // V400 sprite coords, independent of unchanged V200 RRB.
    lda $d054
    ora #$10 // SPR640: native X; glyph pixels below are doubled explicitly.
    sta $d054
    lda #<p_pointers
    sta $d06c
    lda #>p_pointers
    sta $d06d
    lda #$80
    sta $d06e
    ldx #0
p_init_pointer:
    lda #<(p_player_graphic/64)
    cpx #4
    bcc p_init_pointer_low
    lda #<(p_enemy_graphic/64)
p_init_pointer_low:
    sta p_pointers,x
    lda #>(p_player_graphic/64)
    sta p_pointers+1,x
    inx
    inx
    cpx #12
    bne p_init_pointer
    lda #0
    sta p_pointers+12
    sta p_pointers+13
    sta p_pointers+14
    sta p_pointers+15
    lda #10 // existing HUD white, sprite palette bank 2
    sta $d027
    sta $d028
    lda #10 // invariant HUD white in sprite bank2, same as player
    sta $d029
    sta $d02a
    sta $d02b
    sta $d02c
    rts
p_frame_update:
    jsr p_update
    jsr p_player_fire
    jsr p_test_attack
    jsr p_random_step
    jsr p_enemy_fire
    jsr p_publish
    jmp hud.hud_render
p_player_fire:
    lda v014_joy_sample
    and #$10
    beq p_fire_pressed
    lda #0
    sta p_fire_latch
    rts
p_fire_pressed:
    lda p_fire_latch
    bne p_fire_done
    lda #1
    sta p_fire_latch
    ldx #0
    lda p_active,x
    beq p_player_start
    inx
    lda p_active,x
    bne p_fire_done
p_player_start:
    lda V014_PLAYER+2
    clc
    adc #8
    sta p_xpos,x
    lda V014_PLAYER+4
    sta p_ypos,x
    lda #0
    sta p_xfrac,x
    sta p_yfrac,x
    sta p_vxfrac,x
    sta p_vx,x
    sta p_vyfrac,x
    lda #256-p_player_speed
    sta p_vy,x
    lda #1
    sta p_active,x
p_fire_done:
    rts
// API seam for real attack curves: only this routine currently fabricates status.
// Existing enemy 18 follows its existing animated path; no RRB object added.
p_test_attack:
    lda #0
    sta p_attacking
    lda p_test_enabled
    beq p_attack_done
    inc p_attack_tick
    lda p_attack_tick
    and #$7f
    cmp #96 // 96 p_attacking frames, 32 formation frames per 128-frame cycle.
    bcs p_attack_done
    lda #1
    sta p_attacking
p_attack_done:
    rts
p_random_step:
    lsr p_random_hi
    ror p_random_lo
    bcc p_random_done
    lda p_random_hi
    eor #$b4 // maximal-period nonzero 16-bit Galois LFSR
    sta p_random_hi
p_random_done:
    rts
p_enemy_fire:
    lda p_cooldown
    beq p_enemy_ready
    dec p_cooldown
    rts
p_enemy_ready:
    lda p_attacking
    bne p_enemy_attacking
    rts
p_enemy_attacking:
    lda p_random_lo
    and #7 // probability 1/8 per eligible frame, at least 12 quiet frames.
    beq p_enemy_roll_ok
    rts
p_enemy_roll_ok:
    ldx #2
p_enemy_find:
    lda p_active,x
    beq p_enemy_start
    inx
    cpx #6
    bne p_enemy_find
    rts
p_enemy_start:
    stx p_slot
    lda V014_PLAYER+2
    clc
    adc #8
    sta p_target_x,x
    lda V014_PLAYER+4
    sta p_target_y,x
    lda s2i_x+p_test_enemy // enemy 18, existing original-type-15 animated path pixie
    clc
    adc #8
    sta p_xpos,x
    lda s2i_y+p_test_enemy
    clc
    adc #16
    sta p_ypos,x
    cmp #p_enemy_bottom
    bcs p_enemy_done
    lda p_target_y,x
    sec
    sbc p_ypos,x
    bcc p_enemy_done // delta_y <=0: no backwards/near-horizontal shot.
    beq p_enemy_done
    sta p_denominator
    lda p_target_x,x
    sec
    sbc p_xpos,x
    sta p_dx
    lda #0
    sta p_negative
    bcs p_dx_positive
    inc p_negative
    lda p_dx
    eor #$ff
    clc
    adc #1
    sta p_dx
p_dx_positive:
    jsr p_direction
    ldx p_slot
    lda p_numerator
    sta p_vxfrac,x
    lda p_numerator+1
    sta p_vx,x
    lda #0
    sta p_xfrac,x
    sta p_yfrac,x
    sta p_vyfrac,x
    lda #p_test_enemy
    sta p_source_enemy,x
    lda #p_enemy_speed
    sta p_vy,x
    lda #1
    sta p_active,x
    lda #p_fire_cooldown
    sta p_cooldown
p_enemy_done:
    rts
p_update:
    ldx #0
p_update_slot:
    lda p_active,x
    beq p_update_next
    cpx #2
    bcs p_update_enemy
    lda p_vy,x
    eor #$ff
    clc
    adc #1
    sta p_denominator
    lda p_ypos,x
    cmp p_denominator
    bcc p_kill
    sec
    sbc p_denominator
    sta p_ypos,x
    jmp p_update_next
p_update_enemy:
    clc
    lda p_xfrac,x
    adc p_vxfrac,x
    sta p_xfrac,x
    lda p_xpos,x
    adc p_vx,x
    sta p_xpos,x
    cmp #1
    bcc p_kill
    cmp #p_enemy_right
    bcs p_kill
    clc
    lda p_yfrac,x
    adc p_vyfrac,x
    sta p_yfrac,x
    lda p_ypos,x
    adc p_vy,x
    sta p_ypos,x
    cmp #p_enemy_bottom
    bcc p_update_next
p_kill:
    jsr p_deactivate
p_update_next:
    inx
    cpx #6
    bne p_update_slot
    rts
p_deactivate:
    lda #0
    sta p_active,x
    rts
p_publish:
    lda #0
    sta p_enabled_mask
    sta p_xmsb
    sta p_xbit9
    sta p_ymsb
    sta p_ybit9
    ldx #0
p_publish_slot:
    lda p_active,x
    bne p_publish_active
    jmp p_publish_next
p_publish_active:
    lda p_enabled_mask
    ora p_masks,x
    sta p_enabled_mask
    // Native sprite X = CHARX + logicalX*2 -1 (player), -3 (enemy).
    lda p_xpos,x
    asl
    sta p_sx
    lda #0
    rol
    sta p_sx+1
    lda p_sx
    clc
    adc $d04c
    sta p_sx
    lda $d04d
    and #$0f
    adc p_sx+1
    sta p_sx+1
    lda p_sx
    sec
    sbc #1
    sta p_sx
    lda p_sx+1
    sbc #0
    sta p_sx+1
    cpx #2
    bcc p_x_offset_done
    lda p_sx
    sec
    sbc #2
    sta p_sx
    lda p_sx+1
    sbc #0
    sta p_sx+1
p_x_offset_done:
    // Native sprite Y = CHARY + logicalY*2, V400 origin is zero.
    lda p_ypos,x
    asl
    sta p_sy
    lda #0
    rol
    sta p_sy+1
    lda p_sy
    clc
    adc $d04e
    sta p_sy
    lda $d04f
    and #$0f
    adc p_sy+1
    sta p_sy+1
    txa
    asl
    tay
    lda p_sx
    sta $d000,y
    lda p_sy
    sta $d001,y
    lda p_sx+1
    and #1
    beq p_no_xmsb
    lda p_xmsb
    ora p_masks,x
    sta p_xmsb
p_no_xmsb:
    lda p_sx+1
    and #2
    beq p_no_xbit9
    lda p_xbit9
    ora p_masks,x
    sta p_xbit9
p_no_xbit9:
    lda p_sy+1
    and #1
    beq p_no_ymsb
    lda p_ymsb
    ora p_masks,x
    sta p_ymsb
p_no_ymsb:
    lda p_sy+1
    and #2
    beq p_publish_next
    lda p_ybit9
    ora p_masks,x
    sta p_ybit9
p_publish_next:
    inx
    cpx #6
    beq p_publish_done
    jmp p_publish_slot
p_publish_done:
    lda p_xmsb
    sta $d010
    lda p_xbit9
    sta $d05f
    lda p_ymsb
    sta $d077
    lda p_ybit9
    sta $d078
    lda p_enabled_mask
    sta $d015
    rts
p_masks: .byte 1,2,4,8,16,32
p_core_end:
.if (p_core_end > $8800) { .error "Projectile code overlaps original glyph" }
}
*=$9b00 "Stage 3b-5b direction and BASIC sprite restoration"
.namespace shots {
// Unsigned abs(dx)*256/dy, at spawn only; 16-bit remainder prevents overflow.
// Clamp |vx| to 2 pixels/tick, then two's complement if dx negative.
p_direction:
    lda #0
    sta p_numerator
    sta p_remainder
    sta p_remainder+1
    lda p_dx
    sta p_numerator+1
    ldy #16
p_divide:
    asl p_numerator
    rol p_numerator+1
    rol p_remainder
    rol p_remainder+1
    lda p_remainder+1
    bne p_subtract
    lda p_remainder
    cmp p_denominator
    bcc p_divide_next
p_subtract:
    lda p_remainder
    sec
    sbc p_denominator
    sta p_remainder
    lda p_remainder+1
    sbc #0
    sta p_remainder+1
    inc p_numerator
p_divide_next:
    dey
    bne p_divide
    lda p_numerator+1
    cmp #2
    bcc p_clamp_done
    lda #2
    sta p_numerator+1
    lda #0
    sta p_numerator
p_clamp_done:
    lda p_negative
    beq p_direction_done
    lda p_numerator
    eor #$ff
    clc
    adc #1
    sta p_numerator
    lda p_numerator+1
    eor #$ff
    adc #0
    sta p_numerator+1
p_direction_done:
    rts
// Snapshot BEFORE legacy init_sprites, including positions, modes and colours.
.var p_regs=List()
.for (var r=0; r<17; r++) { .eval p_regs.add($d000+r) }
.for (var r=0; r<6; r++) { .eval p_regs.add($d027+r) }
.eval p_regs.add($d04d,$d04f,$d015,$d017,$d01b,$d01c,$d01d,$d054,$d055,$d057,$d05f,$d06b,$d06c,$d06d,$d06e,$d076,$d077,$d078)
p_save_registers:
    .for (var i=0; i<p_regs.size(); i++) {
        lda p_regs.get(i)
        sta p_saved_registers+i
    }
    rts
p_restore_registers:
    sei
    lda VIC_HOTREG
    pha
    and #$7f
    sta VIC_HOTREG
    sta VIC_HOTREG
    lda #0
    sta $d015
    .for (var i=0; i<p_regs.size(); i++) {
        .if (p_regs.get(i)!=$d015) {
            lda p_saved_registers+i
            sta p_regs.get(i)
        }
    }
    pla
    sta VIC_HOTREG
    cli
    rts
p_extra_end:
.if (p_extra_end > $a000) { .error "Projectile helpers overlap animation assets" }
}
.import source "stage7b1_mapping.asm"
