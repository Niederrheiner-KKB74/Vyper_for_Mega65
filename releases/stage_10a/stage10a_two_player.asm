// Stage10a: working actor fields stay at HUD.P1; two persistent identity records.
.namespace twop {
.label records=$1b00 // two8-byte records: u32 score,u16 level,u16 lives
.label mode=$1b10 // 1 F1,2 F2
.label active=$1b11 // identity0/1, never an object slot
.label handled=$1b12 // two one-shot highscore flags
.label resuming=$1b14
.label action=$1b15
.label scratch=$1b16
.label command=$1b17
.label life_shift=$1b18
.label rendering=$1b19
.label session_best=$1b20 // shared in-memory highscore survives HUD reinitialization
*=$9900 "Stage10a native ROMA gate (retired unused thin-font data)"
init: lda #0
    jmp gate
ready: lda #1
    jmp gate
render:
    jsr offscreen.r_render
    lda #2
    jmp gate
capture: lda #3
    jmp gate
poll:
    jsr offscreen.r_key
    pha
    lda #4
    jsr gate
    lda action
    beq !return+
    pla // saved key, poll caller, and top-level key caller: five bytes
    pla
    pla
    pla
    pla
    jsr exit_to_basic
    jmp resume
!return:
    pla
    rts
hs_return:
    lda hslink.reason
    cmp #1
    bne !menu+
    lda mode
    cmp #2
    bne !menu+
    lda #5
    jsr gate
    lda action
    bne resume
!menu:
    jmp menubank.enter
resume:
    // BASIC video has already been restored; restart only the chosen level.
    lda #1
    sta resuming
    lda #6
    jsr gate
    lda scratch
    sta integration.chosen_level
    sta level.number
    lda $d030
    and #$df
    sta $d030
    jsr s3b2.prepare
    lda s3b.error
    bne !error+
    jsr audio8.install
    jmp start
!error:
    jsr splash.t_error
    cli
    rts
wait_guard:
    lda mode
    cmp #2
    bne !normal+
    lda active
    eor #1
    asl
    asl
    asl
    tax
    lda records+6,x
    ora records+7,x
    bne !wait+
!normal:
    jmp game.c_wait_original
!wait:
    rts
restart:
    lda mode
    cmp #2
    beq !ignore+ // F2 elimination belongs to the highscore/switch coordinator.
    jmp level.restart
!ignore:
    rts
gate:
    sta command
    php
    sei
    lda $d030
    pha
    and #$ef
    sta $d030
    jsr dispatch
    pla
    sta $d030
    plp
    rts
.if (*>$99b9) { .error "Two-player gate overlaps identity labels" }

*=$a000 "Stage10a identity controller (retired unused legacy type1 copies)"
dispatch:
    lda command
    asl
    tax
    lda vector,x
    sta invoke+1
    lda vector+1,x
    sta invoke+2
invoke: jmp $ffff
vector: .word new_game,prepare_ready,draw,captured,decide,choose,selected
new_game:
    lda #0
    ldx #$1f
!clear:
    sta records,x
    dex
    bpl !clear-
    ldx #3
!best:
    lda $1fea,x
    sta session_best,x
    dex
    bpl !best-
    lda #1
    sta mode
    lda hslink.selection
    cmp #2
    bne !single+
    inc mode
!single:
    lda integration.chosen_level
    sta records+4
    sta records+12
    lda hud.defaults+10
    sta records+6
    lda mode
    cmp #2
    bne !done+
    lda hud.defaults+10
    sta records+14
!done:
    jmp level.bonus_reset
index:
    lda active
    asl
    asl
    asl
    tax
    rts
save:
    ldx #3
!best:
    lda hud.high_score,x
    sta session_best,x
    dex
    bpl !best-
    jsr index
    ldy #0
!copy:
    lda hud.player1_score,y
    sta records,x
    inx
    iny
    cpy #8
    bne !copy-
    rts
load:
    jsr index
    ldy #0
!copy:
    lda records,x
    sta hud.player1_score,y
    inx
    iny
    cpy #8
    bne !copy-
    rts
selected:
    jsr index
    lda records+4,x
    sta scratch
    rts
prepare_ready:
    ldx #3
!compare:
    lda session_best,x
    cmp hud.high_score,x
    bcc !best_done+
    bne !copy+
    dex
    bpl !compare-
    bmi !best_done+
!copy:
    ldx #3
!best:
    lda session_best,x
    sta hud.high_score,x
    dex
    bpl !best-
!best_done:
    jsr load
    lda mode
    cmp #2
    bne !single+
    lda #1
    sta hud.player2_active
!single:
    lda #0
    sta hslink.over_clock
    sta hslink.over_done
    lda resuming
    beq !done+
    lda #3
    sta game.c_ps
    lda #150
    sta game.c_blink
    lda #25
    sta game.c_flash
    lda #1
    sta game.c_visible
!done:
    lda #0
    sta resuming
    rts
captured:
    jsr save
    ldx active
    lda #1
    sta handled,x
    rts
choose:
    lda #0
    sta action
    lda active
    eor #1
    sta scratch
    asl
    asl
    asl
    tax
    lda records+6,x
    ora records+7,x
    beq !done+
    lda scratch
    sta active
    inc action
!done:
    rts
decide:
    lda #0
    sta action
    lda offscreen.r_keybyte
    cmp #KEY_X
    beq !done+ // BASIC exit always wins over a switch becoming ready this frame.
    lda rendering
    bne !done+
    lda mode
    cmp #2
    bne !done+
    jsr save
    lda game.c_ps
    cmp #2 // EXP completed; c_wait is held only if the other player lives.
    bne !done+
    lda $d720
    and #$80 // Let forced Player-death audio finish; service continues every frame.
    bne !done+
    jmp choose
!done:
    rts

// Convert actor scratch into identity HUD fields only while drawing.
draw:
    lda mode
    cmp #2
    beq !two+
    jsr hud.hud_update_score
    jsr hud.hud_update_level
    jsr hud.hud_update_lives
    jmp hud.hud_update_points
!two:
    jsr save
    lda #1
    sta rendering
    ldx #15
!identity:
    lda records,x
    sta hud.player1_score,x
    dex
    bpl !identity-
    lda #1
    sta hud.player2_active
    // Scores/levels are rendered for both identities; shadows remain identity-based.
    jsr hud.hud_update_score
    jsr hud.hud_update_level
    ldx #12
    ldy #4
    jsr hud.changed
    beq !level+
    lda #13
    sta hud.draw_row
    ldx #12
    jsr hud.score_work
!level:
    ldx #16
    ldy #2
    jsr hud.changed
    beq !icons+
    lda #14
    sta hud.draw_row
    lda #7
    sta hud.draw_column
    lda #3
    sta hud.digit
    ldx #16
    jsr hud.word_work
!icons:
    // One shared4x2 renderer with an8-row translation for P2.
    lda #0
    sta life_shift
    jsr hud.hud_update_lives
    lda #8
    sta life_shift
    ldx #18
    ldy #2
    jsr hud.changed
    beq !labels+
    lda hud.player2_lives
    sta scratch
    lda hud.player2_lives+1
    jsr hud.lives_value
!labels:
    jsr draw_labels
    jsr hud.hud_update_points
    jsr load // restore active working fields before any game/audio code runs
    lda #0
    sta rendering
    rts
.if (*>$a200) { .error "Identity controller overlaps retained type2 frames" }
*=$99b9 "Stage10a native identity labels"
draw_labels:
    lda #0
    sta life_shift
    // Rewrite small static labels after any level/menu redraw.
    lda #12
    sta hud.draw_row
    lda #<p2_label
    ldx #>p2_label
    jsr label
    lda #21
    sta hud.draw_row
    lda #<controls
    ldx #>controls
    jsr label
    // Active identity marked with '>' beside its existing PLAYER label.
    lda #14
    sta hud.draw_row
    lda #<level_label
    ldx #>level_label
    jsr short_label
    lda #3
    sta hud.draw_row
    lda #$20
    ldx active
    bne !p1+
    lda #$3e
!p1:
    jsr marker
    lda #12
    sta hud.draw_row
    lda #$20
    ldx active
    beq !p2+
    lda #$3e
!p2:
    jsr marker
    rts
.if (*>$9a56) { .error "Identity labels overlap attack start" }
*=$a580 "Stage10a label helpers after retained type2 frames"
label:
    sta read+1
    stx read+2
    ldx hud.draw_row
    jsr hud.set_prefix
    lda #24
    sta label_end+1
    ldy #4
!next:
read: lda $ffff
    jsr hud.long_screen_store
    iny
    lda #0
    jsr hud.long_screen_store
    iny
    inc read+1
    bne !advance+
    inc read+2
!advance:
label_end: cpy #24
    bne !next-
    rts
short_label:
    sta read+1
    stx read+2
    ldx hud.draw_row
    jsr hud.set_prefix
    lda #16 // six prefix characters; preserve three level digits at cols7..9
    sta label_end+1
    ldy #4
    jmp read
marker:
    pha
    ldx hud.draw_row
    jsr hud.set_prefix
    ldy #4
    pla
    jmp hud.long_screen_store
level_label: .byte $0c,$05,$16,$05,$0c,$20
p2_label: .byte $20,$10,$0c,$01,$19,$05,$12,$20,$32,$20
controls: .byte $20,$10,$20,$13,$20,$18,$20,$20,$20,$20
.if (*>$a600) { .error "Two-player controller overlaps fire configuration" }
}
