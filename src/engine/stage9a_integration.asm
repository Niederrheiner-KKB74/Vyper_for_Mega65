// Persistent bridge. The menu owns $7000-$9FFF only until game/exit handoff.
.import source "menu_layout.inc"
*=$cb00 "Stage6b1 phase bridge"
    jmp integration.load_menu
    jmp integration.start_game
    jmp integration.exit_menu
    jmp cc_tick
    jmp cc_publish
    jmp integration.restore_data
    jmp integration.enter_menu
    jmp integration.finish_menu_load
.namespace integration {
load_menu:
    lda #0
    sta s3b.total_crc
    sta s3b.total_crc+1
    lda #<filename
    sta s3b.name_ptr
    lda #>filename
    sta s3b.name_ptr+1
    lda #12
    sta s3b.name_len
    lda #<M_FILE_BYTES
    sta s3b.remain
    lda #>((M_FILE_BYTES)&$ffff)
    sta s3b.remain+1
    lda #M_FILE_BYTES>>16
    sta s3b.remain+2
    lda #0
    sta s3b.target_hi
    lda #4
    sta s3b.target_bank
    rts
finish_menu_load:
    lda s3b.error
    beq !sum+
    rts
!sum:
    lda s3b.total_crc
    cmp #<M_FILE_SUM
    bne bad
    lda s3b.total_crc+1
    cmp #>M_FILE_SUM
    bne bad
    ldx #<header_copy
    ldy #>header_copy
    jsr transfer
    ldx #31
!header:
    lda $6900,x
    cmp expected_header,x
    bne bad
    dex
    bpl !header-
    // Entire menu to Attic, verified SEQ chunks already compared on read-back.
    ldx #<asset_save0
    ldy #>asset_save0
    jsr transfer
    ldx #<asset_save1
    ldy #>asset_save1
    jsr transfer
    ldx #<asset_header
    ldy #>asset_header
    jsr transfer
    ldx #31
!attic_header:
    lda $6900,x
    cmp expected_header,x
    bne bad
    dex
    bpl !attic_header-
    rts
bad:
    lda #9
    sta s3b.error
    rts
enter_menu:
    sei
    jsr cc_init
    lda #2
    sta cc_index
    lda $d011
    and #$ef
    sta $d011
    ldx #<engine_save
    ldy #>engine_save
    jsr transfer
    // Keep the title's original own-colour backup before atlas reuse.
    ldx #<colour_save
    ldy #>colour_save
    jsr transfer
    ldx #<overlay_load
    ldy #>overlay_load
    jsr transfer
    ldx #<atlas_low
    ldy #>atlas_low
    jsr transfer
    ldx #<atlas_high
    ldy #>atlas_high
    jsr transfer
    lda #1
    sta splash.t_shown // use exact Stage5d1a saved BASIC restoration state
    jmp $7000
restore_data:
    lda $d011
    and #$ef
    sta $d011
    ldx #<engine_restore
    ldy #>engine_restore
    jsr transfer
    ldx #<colour_restore
    ldy #>colour_restore
    jsr transfer
    rts
start_game:
    sta chosen_level
    jsr menubank.restore
    lda #$13 // NCM original COLOR02: colour2+1, subpalette16
    sta cc_index
    lda chosen_level
    sta level.number
    jsr s3b2.prepare // menu atlas replaced private frame/record buffers
    lda s3b.error
    beq !start+
    jsr splash.t_error
    cli
    rts
!start:
    jsr audio8.install
    jmp start
exit_menu:
    jsr menubank.restore
    jsr titlecache.tc_restore
    jmp menubank.finish
start_ready:
    jsr level.bonus_reset
    lda menubank.original
    sta saved_d030
    // HUD initialization resets its default level to1: selected record wins.
    lda chosen_level
    sta hud.player1_level
    lda #0
    sta hud.player1_level+1
    jsr hud.hud_draw_static
    jsr hud.hud_render
    jsr starfield_init
    jsr transitionfx.init
    jsr audio8.init
    jmp cc_publish
hud_font:
    ldx #<font_load
    ldy #>font_load
    jsr transfer
    // Keep established mono frame glyphs; remaining font is original menu font.
    ldx #7
!frame:
    lda #$f0
    sta $4400,x
    lda #$ff
    sta $4408,x
    dex
    bpl !frame-
    rts
transfer:
    tya
    jmp hud.transfer
filename: .text "VYMN.DAT,S,R"
    .byte 0
chosen_level: .byte 1
expected_header:
.import binary "menu_header.bin"
.import source "menu_dma.inc"
.if (*>$d000) { .error "Phase bridge exceeds CPU-accessible RAM" }
}
