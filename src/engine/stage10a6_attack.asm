// Issue #19: local Stage 4b-3 Stable; two-frame drift, fixed enemy curve descriptors.
.namespace attack {
.const a_FORM_STEP_TICKS=2
.const a_MAX_CURVES=4
.const a_FORM_Y_SHIFT=25 // min original Level-1 top-left Y, independently checked by builder
.const a_FORM_MIN=-8
.const a_FORM_MAX=8
.const a_START_INTERVAL=30 // Test tuning, not reconstructed Amiga timing
.const a_SHOT_RANDOM_MASK=1 // legacy T demo only; normal shots are events
.const a_INITIAL_INTERVAL=100
.const a_SEED=$c3a5 // reproducible, nonzero Galois LFSR shared with projectile rolls
.label a_index=$6F80 // 22 original raw attack indices
.label a_anchorx=$6F96
.label a_anchory=$6FAC
.label a_hidden=$6FC2 // bottom-crossing latch; cyclic ATTACK stops at port Y>=200
.label a_ptrlo=$6FEC // four bounded descriptor pointers; no new RAM allocation
.label a_ptrhi=$6FF0
.label a_length=$6FF4 // packed byte lengths 1..255; originals max217
.label a_curve_count=$6FF8
.label a_enabled=$6FDE
.label a_ready=$6FDF
.label a_offset=$6FE0 // signed -8..8
.label a_direction=$6FE1 // +1 or -1
.label a_form_tick=$6FE2
.label a_start_tick=$6FE3
.label a_count=$6FE4
.label a_shots=$6FE5
.label a_last=$6FE6
.label a_goalx=$6FE7
.label a_candidate=$6FE8
.label a_source=$6FE9
.label a_event=$6FEA // 1 attack start, 2 bottom crossing, 3 top return
.label a_event_enemy=$6FEB

*=$7608 "Stage 6b1 bounded attack parser"
a_init:
    lda #0
    ldx #($6FFF-$6F96)
!clear:
    sta $6F96,x
    dex
    bpl !clear-
    lda $7606
    beq !bad_count+
    cmp #a_MAX_CURVES+1
    bcc !valid_count+
!bad_count:
    jmp a_invalid
!valid_count:
    sta a_curve_count
    lda $7607
    beq !near+
    jmp a_invalid
!near:
    ldx #0
!indices:
    lda a_index,x
    cmp a_curve_count
    bcc !near+
    jmp a_invalid
!near:
    inx
    cpx $7603
    bne !indices-
    ldx #0
!curve:
    stx a_candidate
    jsr s3b2.read_word
    bcc !near+
    jmp a_invalid
!near:
    lda s3b2.word_value+1
    beq !near+
    jmp a_invalid
!near:
    lda s3b2.word_value
    bne !near+
    jmp a_invalid
!near:
    ldx a_candidate
    sta a_length,x
    lda s3b2.pointer
    sta a_ptrlo,x
    lda s3b2.pointer+1
    sta a_ptrhi,x
    jsr s3b2.skip_curve
    bcc !near+
    jmp a_invalid
!near:
    ldx a_candidate
    inx
    cpx a_curve_count
    bne !curve-
    lda s3b2.pointer
    cmp level.record_end
    beq !near+
    jmp a_invalid
!near:
    lda s3b2.pointer+1
    cmp level.record_end+1
    beq !near+
    jmp a_invalid
!near:
    lda #1
    sta a_enabled
    sta a_direction
    lda #a_FORM_STEP_TICKS
    sta a_form_tick
    lda #a_INITIAL_INTERVAL
    sta a_start_tick
    lda #<a_SEED
    sta shots.p_random_lo
    lda #>a_SEED
    sta shots.p_random_hi
    jsr motion.reset
    rts
a_invalid:
    jmp entry.e_invalid

.if (* > $7800) { .error "Attack parser overlaps game state code" }
*=$4f00 "Stage 6b1 formation and selection"
a_objects:
    jsr a_preframe
    jmp entry.e_objects

a_preframe:
    lda game.c_ps
    cmp #4
    beq !done+
    lda shots.p_test_enabled
    bne !done+
    lda a_enabled
    beq !done+
    lda a_ready
    beq !done+
    dec a_form_tick
    bne !done+
    lda #a_FORM_STEP_TICKS
    sta a_form_tick
    lda a_offset
    clc
    adc a_direction
    sta a_offset
    cmp #a_FORM_MAX
    beq !left+
    cmp #(256+a_FORM_MIN)
    bne !done+
    lda #1
    sta a_direction
    rts
!left:
    lda #$ff
    sta a_direction
!done:
    rts

a_postframe:
    lda game.c_ps
    cmp #4
    beq !done+
    lda shots.p_test_enabled
    bne !done+
    lda a_enabled
    beq !done+
    lda a_ready
    bne !schedule+
    // Stage10a3 (original behaviour): drift and the attack countdown start as
    // soon as the FIRST live enemy has reached its formation slot, not after the
    // whole entry. Enemies still entering home onto e_tx+a_offset via RETURN.
    ldx #0
!barrier:
    lda game.c_es,x
    cmp #1
    bne !next+
    lda entry.e_phase,x
    cmp #3
    beq !ready+
!next:
    inx
    cpx $7603
    bne !barrier-
    rts
!ready:
    lda #1
    sta a_ready
    rts // first movement/attack countdown begins on the next update
    .fill 1,$ea // keep all following Stage10a2 addresses unchanged (30-byte barrier)
!schedule:
    lda level.attack_allowed
    beq !done+
    // Stage10a4 (original $C0D17E): no new attack while the player explodes
    // or during the death-respawn window; running attacks finish and return.
    jsr game.respawn_attack_blocked
    bcs !done+
    .fill 6,$ea // keep following addresses identical to Stage10a3
    jsr a_recount
    lda a_start_tick
    beq !select+
    dec a_start_tick
    bne !done+
!select:
    lda a_count
    cmp #3
    bcs !done+
    lda #0
    jsr selection.collect
    jsr selection.choose
    bcc !done+ // No eligible actor/rejected rank: keep due timer, retry next frame.
    jsr a_start
    lda #a_START_INTERVAL
    sta a_start_tick
    jsr a_recount
!done:
    rts

.if (* > $5000) { .error "Scheduler overlaps BASIC colour backup" }
*=$9a56 "Stage 6b1 attack start and visibility"
a_recount:
    lda #0
    sta a_count
    ldx #0
!enemy:
    lda game.c_es,x
    cmp #3
    bne !next+
    inc a_count
!next:
    inx
    cpx $7603
    bne !enemy-
    rts

a_start:
    lda a_index,x
    cmp a_curve_count
    bcc !valid+
    jmp a_invalid
!valid:
    stx a_last
    stx a_event_enemy
    lda #1
    sta a_event
    lda entry.e_xlo,x
    sta a_anchorx,x
    lda entry.e_ylo,x
    sta a_anchory,x
    lda #0
    sta entry.e_cursor,x
    sta a_hidden,x
    lda #4
    sta entry.e_phase,x
    lda #3
    sta game.c_es,x
    jsr audio8.attack
    jmp fireevents.attack_plan

a_formation_y:
    cmp level.y_shift
    bcc !bad+
    sec
    sbc level.y_shift
    cmp #185
    bcs !bad+
    clc
    rts
!bad:
    sec
    rts

a_goal:
    lda entry.e_tx,x
    clc
    adc a_offset
    sta a_goalx
    rts

a_visible:
    lda game.c_es,x
    cmp #3
    bne !yes+
    lda a_hidden,x
    bne !no+
!yes:
    lda #1
    rts
!no:
    lda #0
    rts
// The explicit old T demo shares the same global ATTACK cap.
a_legacy_attack:
    lda game.c_ps
    cmp #1
    beq !blocked+
    cmp #2
    beq !blocked+
    jsr a_recount
    lda a_count
    cmp #3
    bcc !allow+
    lda game.c_es+18
    cmp #3
    beq !allow+ // already one of the three; caller verified legacy phase 3
!blocked:
    lda #0
    sta shots.p_attacking
    rts
!allow:
    jmp shots.p_test_attack
.if (* > $9b00) { .error "Attack helpers overlap projectile direction code" }

*=$9f10 "Stage 6b1 original attack motion"
a_step:
    jsr entry.e_demo_step
    bcs a_handled
    lda entry.e_phase,x
    cmp #4
    beq a_curve
    cmp #5
    bne !near+
    jmp a_exit
!near:
    cmp #3
    bne a_unhandled
    lda shots.p_test_enabled
    bne a_unhandled
    jsr a_goal
    lda a_goalx
    sta entry.e_xlo,x
    lda #0
    sta entry.e_xhi,x
    jsr entry.e_mirror
    sec
    rts
a_unhandled:
    clc
    rts
a_handled:
    sec
    rts

a_curve:
    lda a_index,x
    cmp a_curve_count
    bcc !valid+
    jmp a_invalid
!valid:
    tay
    lda entry.e_cursor,x
    cmp a_length,y
    bcc !bounded+
    jmp a_invalid
!bounded:
    clc
    lda a_ptrlo,y
    adc entry.e_cursor,x
    sta level.read_pointer
    lda a_ptrhi,y
    adc #0
    sta level.read_pointer+1
a_read:
    jsr level.read_record
    sta entry.e_byte
    lsr
    lsr
    lsr
    lsr
    jsr entry.e_decode
    sta entry.e_dx
    lda entry.e_byte
    and #15
    jsr entry.e_decode
    sta entry.e_dy
    clc
    lda entry.e_xlo,x
    adc entry.e_dx
    sta entry.e_xlo,x
    lda #0
    bit entry.e_dx
    bpl !xp+
    lda #$ff
!xp:
    adc entry.e_xhi,x
    sta entry.e_xhi,x
    clc
    lda entry.e_ylo,x
    adc entry.e_dy
    sta entry.e_ylo,x
    lda #0
    bit entry.e_dy
    bpl !yp+
    lda #$ff
!yp:
    adc entry.e_yhi,x
    sta entry.e_yhi,x
    inc entry.e_cursor,x
    jsr fireevents.attack_tick
    jsr a_bottom
    jmp a_finish_point

a_bottom:
    lda entry.e_yhi,x
    bmi !done+
    bne !outside+
    lda entry.e_ylo,x
    cmp #200
    bcc !done+
!outside:
    lda a_hidden,x
    bne !done+
    lda #1
    sta a_hidden,x
    lda #2
    sta a_event
    stx a_event_enemy
!done:
    rts

.if (* > $a000) { .error "Attack motion enters ROM-overlay range" }
*=$36b0 "Stage 6b1 bottom exit and top reentry"
// Reuse the removed fallback bytes; do not grow motion into $A000.
a_finish_point:
    lda a_hidden,x
    beq !cycle+
    lda #5
    sta entry.e_phase,x
    bne !mirror+ // bottom exit wins even before the first wrap
!cycle:
    lda a_index,x
    tay
    lda entry.e_cursor,x
    cmp a_length,y
    bne !mirror+
    lda #0
    sta entry.e_cursor,x
!mirror:
    jsr entry.e_mirror
    sec
    rts

a_exit:
    // Only reached after a_bottom latched a fully offscreen Y>=200.
    // No visible fixed-X fallback; retain the established top RETURN path.
a_reentry:
    // One completely invisible bottom frame, then Y=-16 above the visible area.
    lda #$f0
    sta entry.e_ylo,x
    lda #$ff
    sta entry.e_yhi,x
    lda #2
    sta entry.e_phase,x
    sta game.c_es,x
    lda #0
    sta a_hidden,x
    lda #3
    sta a_event
    stx a_event_enemy
    jsr entry.e_mirror
    sec
    rts

// Reuse the existing 8.8 direction calculation, global slots 2..5 and publisher.
.if (* > $3700) { .error "Attack reentry overlaps player integration" }
*=$895c "Stage 6b1 enemy fire selection"
a_fire:
    jmp fireevents.flush

.import source "stage10a6_fire_loader.asm"

.if (* > $8a00) { .error "Fire selection overlaps projectile graphics" }
*=$7951 "Stage 6b1 aimed shot initialization"
a_fire_start:
    jmp motion.spawn
*=$79dd // keep the shared count gate; gap holds isolated legacy-T update

a_fire_count:
    lda #0
    sta a_shots
    ldx #2
!count:
    lda shots.p_active,x
    beq !next+
    inc a_shots
!next:
    inx
    cpx #8
    bne !count-
a_fire_done:
    rts
.if (* > $7a00) { .error "Shot initialization overlaps HUD tables" }
.if (a_SEED<1 || a_SEED>65535) { .error "LFSR seed must be nonzero 16-bit" }
.if (a_FORM_STEP_TICKS<1 || a_FORM_STEP_TICKS>255) { .error "Invalid formation cadence" }
}
