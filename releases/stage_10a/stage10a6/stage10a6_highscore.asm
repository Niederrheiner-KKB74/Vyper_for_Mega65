// Native resident phase gates; never in SEQ buffers6800/6900 or overlay RAM.
.import source "highscore_layout.inc"
.namespace hslink {
.label score=$1fe0
.label reason=$1fe4
.label initial=$1fe5
.label selection=$1fe6
.label over_clock=$1fe7
.label over_done=$1fe8
.label basic_exit=$1fe9
*=$5448 "Stage9c3 transient gate seed and overlay loader"
gate_seed:
.pseudopc $1920 {
    jmp enter
    jmp restore
enter:
    sta reason
    lda #0
    sta basic_exit
    sei
    jsr audio8.stop
    lda reason
    cmp #2
    beq !native+
    cmp #1
    beq !game+
    jsr menubank.restore // restores engine's7000..9FFF before archiving it
    lda menubank.original
    sta $d030
    jmp !native+
!game:
    jsr twop.capture
    jsr exit_to_basic // includes sprites, stars, palettes, audio, BASIC video
!native:
    sei
    ldx #<hs_save
    ldy #>hs_save
    jsr transfer
    ldx #<hs_load0
    ldy #>hs_load0
    jsr transfer
    ldx #<hs_load2
    ldy #>hs_load2
    jsr transfer
    jmp $2100
restore:
    sei
    ldx #<hs_restore
    ldy #>hs_restore
    jsr transfer
    lda basic_exit
    beq !menu+
    // Engine already completed its BASIC restoration before opening the table.
    jsr titlecache.tc_restore
    cli
    rts
!menu:
    jmp twop.hs_return
transfer:
    lda #0
    sta $d702
    sta $d704
    sty $d701
    stx $d705
    rts
.import source "highscore_dma.inc"
hs_prefix: .import binary "highscore_prefix.bin"
gate_end:
.if (*>$1a00) { .error "Highscore gate overlaps HUD state" }
}
boot:
    ldx #gate_end-$1920-1
!copy:
    lda gate_seed,x
    sta $1920,x
    dex
    cpx #$ff
    bne !copy-
    lda #0
    sta over_clock
    sta over_done
    sta selection
    sta basic_exit
    lda #1
    sta initial
    jmp pal.capture_device

load:
    lda #0
    sta s3b.total_crc
    sta s3b.total_crc+1
    lda #<filename
    sta s3b.name_ptr
    lda #>filename
    sta s3b.name_ptr+1
    lda #12
    sta s3b.name_len
    lda #<HS_BYTES
    sta s3b.remain
    lda #>HS_BYTES
    sta s3b.remain+1
    lda #0
    sta s3b.remain+2
    sta s3b.target_hi
    lda #4
    sta s3b.target_bank
    cli
    jsr M_SEQ_LOAD
    sei
    lda s3b.error
    bne !return+
    lda s3b.total_crc
    cmp #<HS_SUM
    bne !bad+
    lda s3b.total_crc+1
    cmp #>HS_SUM
    bne !bad+
    ldx #<hs_archive
    ldy #>hs_archive
    jsr transfer
    ldx #<hs_check
    ldy #>hs_check
    jsr transfer
    ldx #15
!prefix:
    lda $6900,x
    cmp hs_prefix,x
    bne !bad+
    dex
    bpl !prefix-
    jmp menubank.load
!bad:
    lda #6
    sta s3b.error
!return:
    rts
filename: .text "VYHS.DAT,S,R"
    .byte 0
.import source "highscore_archive.inc"
.if (*>$5700) { .error "Transient highscore loader overlaps ENTRY" }
*=$6f00 "Stage9c3 resident GameOver coordinator"
startup:
    lda #2
    jmp enter
key:
    jsr twop.poll
    cmp #KEY_X
    bne !count+
    rts
!count:
    pha
    lda game.c_ps
    cmp #4 // game.c_OVER
    beq !over+
    lda #0
    sta over_clock
    sta over_done
    pla
    rts
!over:
    lda over_done
    bne !done+
    inc over_clock
    lda over_clock
    cmp #150 // 3s of existing50Hz loop, explosion has fully finished beforehand
    bcc !done+
    inc over_done
    ldx #3
!score:
    lda hud.player1_score,x
    sta score,x
    dex
    bpl !score-
    pla // discard saved key, and abandon only the top-level key caller
    pla
    pla
    lda #1
    jmp enter
!done:
    pla
    rts

.if (*>$6f80) { .error "Coordinator overlaps original attack indices" }
}
