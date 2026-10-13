// Phase-private menu program, loaded from verified VYMN.DAT into $7000-$9FFF.
.import source "menu_layout.inc"
.const MENU_FRAME_DIVIDER=1
*=$7000 "Stage6b1 menu controller"
menu_enter:
    jsr menu_init
    lda #0
    sta selection
    sta placeholder
    sta previous_joy
    sta repeat_timer
    sta fire_armed
    sta key_previous
    sta key_timer
    sta start_pending
    lda #1
    sta initial_level
    jsr menu_screen
    jsr menu_show
    jsr $cb0c // Publish continuous cycle to menu index2.
menu_loop:
    lda $d012
    cmp #250
    beq wide_skip_1
    jmp menu_loop
wide_skip_1:
!leave:
    lda $d012
    cmp #250
    bne wide_skip_2
    jmp !leave-
wide_skip_2:
    jsr $cb09
    jsr menu_tick
    jsr menu_input
    jmp menu_loop
menu_input:
    lda start_pending
    beq input_normal
    lda $d610
    beq pending_fire
    lda $d619
    sta $d619
    cmp #$58
    bne pending_lower
    jmp menu_quit
pending_lower:
    cmp #$78
    bne pending_fire
    jmp menu_quit
pending_fire:
    lda $dc00
    and #$10
    beq pending_wait
    jmp menu_launch
pending_wait:
    rts
input_normal:
    lda key_timer
    beq key_clock_done
    dec key_timer
key_clock_done:
    lda #0
    sta $d614
    lda $d613
    and #$b6 // C65 col0: cursor, F1/F2, F3, RETURN; active low
    cmp #$b6
    bne key_still_held
    lda #0
    sta key_previous
key_still_held:
    lda $d610
    bne wide_skip_3
    jmp !joy+
wide_skip_3:
    lda $d619 // PETSCII; no KERNAL function-key macro expansion.
    pha
    sta $d619
    pla
    sta key_event
    cmp key_previous
    bne key_new
    cmp #13
    beq key_ignore
    cmp #$85
    beq key_ignore
    cmp #$89
    beq key_ignore
    cmp #$86
    beq key_ignore
    lda key_timer
    bne key_ignore
    lda #5
    sta key_timer
    jmp key_accept
key_new:
    sta key_previous
    lda #20
    sta key_timer
key_accept:
    lda key_event
    jmp key_dispatch
key_ignore:
    jmp keyboard_joy
key_dispatch:
    cmp #$58
    bne wide_skip_4
    jmp menu_quit
wide_skip_4:
    cmp #$78
    bne wide_skip_5
    jmp menu_quit
wide_skip_5:
    cmp #$85 // F1
    beq wide_skip_6
    jmp !f2+
wide_skip_6:
    lda #1
    jmp shortcut
!f2:
    cmp #$89 // F2, verified MEGA65 PETSCII table
    beq wide_skip_7
    jmp !f3+
wide_skip_7:
    lda #2
    jmp shortcut
!f3:
    cmp #$86 // F3
    beq wide_skip_8
    jmp !return+
wide_skip_8:
    lda #3
shortcut:
    ldx placeholder
    beq wide_skip_9
    jmp !done+
wide_skip_9:
    sta selection
    jsr menu_colours
    jmp confirm
!return:
    cmp #13
    bne wide_skip_10
    jmp confirm
wide_skip_10:
    cmp #$91
    bne wide_skip_11
    jmp select_up
wide_skip_11:
    cmp #$11
    bne wide_skip_12
    jmp select_down
wide_skip_12:
    cmp #$9d
    bne wide_skip_13
    jmp level_left
wide_skip_13:
    cmp #$1d
    bne wide_skip_14
    jmp level_right
wide_skip_14:
!joy:
keyboard_joy:
    lda $dc00
    eor #$ff
    and #$1f
    sta joystick
    and #$10
    beq wide_skip_15
    jmp !fire+
wide_skip_15:
    lda #1
    sta fire_armed
    jmp !direction+
!fire:
    lda fire_armed
    bne wide_skip_16
    jmp !direction+
wide_skip_16:
    lda #0
    sta fire_armed
    jmp confirm
!direction:
    lda joystick
    and #15
    cmp previous_joy
    bne wide_skip_17
    jmp !held+
wide_skip_17:
    sta previous_joy
    lda #20 // first repeat after400ms, later every100ms
    sta repeat_timer
    jmp joy_direction
!held:
    cmp #0
    bne wide_skip_18
    jmp !done+
wide_skip_18:
    dec repeat_timer
    beq wide_skip_19
    jmp !done+
wide_skip_19:
    lda #5
    sta repeat_timer
joy_direction:
    lda previous_joy
    and #1
    beq wide_skip_20
    jmp select_up
wide_skip_20:
    lda previous_joy
    and #2
    beq wide_skip_21
    jmp select_down
wide_skip_21:
    lda previous_joy
    and #4
    beq wide_skip_22
    jmp level_left
wide_skip_22:
    lda previous_joy
    and #8
    beq wide_skip_23
    jmp level_right
wide_skip_23:
!done:
    rts
menu_quit:
    pla
    pla // discard menu_input JSR; return through original loader caller
    jmp $cb06
select_up:
    lda placeholder
    beq wide_skip_24
    jmp input_done
wide_skip_24:
    lda selection
    sec
    sbc #1
    and #3
    sta selection
    jmp menu_colours
select_down:
    lda placeholder
    beq wide_skip_25
    jmp input_done
wide_skip_25:
    inc selection
    lda selection
    and #3
    sta selection
    jmp menu_colours
level_left:
    lda placeholder
    ora selection
    beq wide_skip_26
    jmp input_done
wide_skip_26:
    dec initial_level
    beq wide_skip_27
    jmp !draw+
wide_skip_27:
    lda #100
    sta initial_level
!draw:
    jmp menu_digits
level_right:
    lda placeholder
    ora selection
    beq wide_skip_28
    jmp input_done
wide_skip_28:
    inc initial_level
    lda initial_level
    cmp #101
    beq wide_skip_29
    jmp !draw+
wide_skip_29:
    lda #1
    sta initial_level
!draw:
    jmp menu_digits
input_done:
    rts
confirm:
    lda placeholder
    bne wide_skip_30
    jmp !option+
wide_skip_30:
    lda #0
    sta placeholder
    jmp menu_screen
!option:
    lda selection
    bne wide_skip_31
    jmp input_done
wide_skip_31:
    cmp #1
    beq wide_skip_32
    jmp !placeholder+
wide_skip_32:
    // Keep animation, cycle and X responsive while waiting for fire release.
    lda $dc00
    and #$10
    bne menu_launch
    lda #1
    sta start_pending
    rts
menu_launch:
!drain:
    lda $d610
    beq !start+
    sta $d610
    jmp !drain-
!start:
    pla
    pla // menu controller must not remain on the game exit stack
    lda initial_level
    jmp $cb03
!placeholder:
    sec
    sbc #1 // F2 -> screen1, F3 -> screen2
    sta placeholder
    lda #0
    sta fire_armed
    jmp menu_screen
menu_screen:
    ldx placeholder
    lda screen_lo,x
    sta screen_copy+9
    lda screen_hi,x
    sta screen_copy+10
    lda screen_bank,x
    sta screen_copy+11
    ldx #<screen_copy
    ldy #>screen_copy
    jsr transfer
    lda placeholder
    beq wide_skip_35
    jmp !done+
wide_skip_35:
    jsr menu_digits
!done:
    jmp menu_colours
menu_colours:
    lda $d070
    pha
    and #$3f
    ora #$40
    sta $d070
    ldx #3
!option:
    lda #$ff
    sta $d108,x
    cpx selection
    bne wide_skip_36
    jmp !selected+
wide_skip_36:
    sta $d208,x
    sta $d308,x
    jmp !next+
!selected:
    lda #0
    sta $d208,x
    sta $d308,x
!next:
    dex
    bmi wide_skip_37
    jmp !option-
wide_skip_37:
    pla
    sta $d070
    rts
menu_digits:
    // Original 6x7 digits at X94,Y146; three FCM columns, two rows.
    ldx #0
!clear:
    lda digit_background,x
    sta $8c00,x
    cpx #128
    bcc wide_skip_38
    jmp !first+
wide_skip_38:
    lda digit_background+256,x
    sta $8d00,x
!first:
    inx
    beq wide_skip_39
    jmp !clear-
wide_skip_39:
    lda initial_level
    ldx #0
!hundreds:
    cmp #100
    bcs wide_skip_40
    jmp !tens+
wide_skip_40:
    sbc #100 // CMP left carry set
    inx
    beq wide_skip_41
    jmp !hundreds-
wide_skip_41:
!tens:
    stx digits
    ldx #0
!ten:
    cmp #10
    bcs wide_skip_42
    jmp !ones+
wide_skip_42:
    sbc #10
    inx
    beq wide_skip_43
    jmp !ten-
wide_skip_43:
!ones:
    stx digits+1
    sta digits+2
    lda #0
    sta digit_no
!digit:
    ldx digit_no
    lda digits,x
    asl
    asl
    asl
    sta digit_read+1
    lda #$99 // charset digit codes48..57 => $9980..$99C8
    sta digit_read+2
    lda digit_read+1
    clc
    adc #$80
    sta digit_read+1
    bcs wide_skip_44
    jmp !glyph+
wide_skip_44:
    inc digit_read+2
!glyph:
    lda #0
    sta digit_row
!row:
    ldy digit_row
digit_read:
    lda $ffff,y
    sta digit_bits
    lda #0
    sta digit_col
!pixel:
    asl digit_bits
    bcs wide_skip_45
    jmp !blank+
wide_skip_45:
    ldx digit_no
    lda digit_x,x
    clc
    adc digit_col
    tay
    lsr
    lsr
    lsr
    tax
    tya
    and #7
    clc
    adc pixel_lo,x
    sta pixel_write+1
    lda pixel_hi,x
    sta pixel_write+2
    lda digit_row
    clc
    adc #2
    cmp #8
    bcs wide_skip_46
    jmp !top+
wide_skip_46:
    // second tile row begins at $8CC0
    lda pixel_write+1
    clc
    adc #$c0
    sta pixel_write+1
    bcs wide_skip_47
    jmp !bottom+
wide_skip_47:
    inc pixel_write+2
!bottom:
    lda digit_row
    sec
    sbc #6
    jmp !offset+
!top:
    lda digit_row
    clc
    adc #2
!offset:
    asl
    asl
    asl
    clc
    adc pixel_write+1
    sta pixel_write+1
    bcs wide_skip_48
    jmp !colour+
wide_skip_48:
    inc pixel_write+2
!colour:
    lda #8
pixel_write:
    sta $ffff
!blank:
    inc digit_col
    lda digit_col
    cmp #6
    beq wide_skip_49
    jmp !pixel-
wide_skip_49:
    inc digit_row
    lda digit_row
    cmp #7
    beq wide_skip_50
    jmp !row-
wide_skip_50:
    inc digit_no
    lda digit_no
    cmp #3
    beq wide_skip_51
    jmp !digit-
wide_skip_51:
    ldx #<digit_copy
    ldy #>digit_copy
    jsr transfer
    ldx #0
!pointers:
    lda digit_screen,x
    sta $95b6,x // row18,col11: Y144, X88
    lda digit_screen+6,x
    sta $9606,x // row19
    inx
    cpx #6
    beq wide_skip_52
    jmp !pointers-
wide_skip_52:
    rts
transfer:
    lda #0
    sta $d702
    sta $d704
    sty $d701
    stx $d705
    rts

menu_show:
    lda $d05d
    and #$7f // HOTREG OFF before legacy writes; direct geometry follows.
    sta $d05d
    lda $d011
    and #$0f
    sta $d011 // DEN off; no ECM/BMM. IRQ disabled throughout image display.
    lda #0
    sta $d015 // hardware sprites off, other sprite state untouched
    sta $d020
    sta $d021
    lda $d030
    and #$fe // no CRAM2K mapping over hardware I/O
    sta $d030
    lda $d031
    and #$47 // H320 / V200, no VIC-III attributes or bitplanes
    ora #$40 // FAST together with D054.VFAST; original restored on X
    sta $d031
    lda $d016
    and #$e0
    ora #8 // 40-col legacy CSEL flag; custom count is40
    sta $d016
    lda #$45 // VFAST + CHR16/FCLRHI; no NCM, RRB/GOTOX, alpha or flips
    sta $d054
    lda $d07a
    and #$ef // CHARY16 off
    sta $d07a
    lda #$50 // mapped bank1, primary bank1
    sta $d070
    ldx #15
apply_palette_loop:
    lda menu_red,x
    sta $d100,x
    lda menu_green,x
    sta $d200,x
    lda menu_blue,x
    sta $d300,x
    dex
    bmi wide_skip_53
    jmp apply_palette_loop
wide_skip_53:
    // All RGB4 expanded channels have identical nibbles; VIC nibble swap
    // leaves exact values unchanged ($A -> $AA, etc.).
    lda #$00
    sta $d060
    lda #$90
    sta $d061
    lda #0
    sta $d062
    sta $d063
    sta $d064
    lda #$20
    sta $d065 // own colour pointer offset $2000
    lda #80
    sta $d058
    lda #0
    sta $d059
    lda #40
    sta $d05e
    lda #24 // 25 original320x200 menu rows
    sta $d07b
    lda #120 // H320: one source pixel per two native horizontal pixels
    sta $d05a
    lda #1 // CHRYSCL = physical rasters per pixel minus 1: 2 - 1.
    sta $d05b
    lda #40 // PAL border area; image inside, X=48..751
    sta $d05c
    lda #0
    sta $d05d
    sta $d049
    sta $d04b
    sta $d04d
    sta $d04f
    lda #80
    sta $d04c // 640 native pixels, horizontally centered
    lda #88
    sta $d048
    sta $d04e // 400 native rows, centered in PAL display
    lda #<488
    sta $d04a // bottom is exclusive
    lda #>488
    sta $d04b
    ldx #<colour_fill
    ldy #>colour_fill
    jsr transfer
    lda #$ff
    sta $1120
    lda #$1b
    sta $d011 // DEN on; HOTREG remains off, custom geometry not propagated
    rts


selection: .byte 0
initial_level: .byte 1
placeholder: .byte 0
previous_joy: .byte 0
repeat_timer: .byte 0
fire_armed: .byte 0
joystick: .byte 0
key_previous: .byte 0
key_timer: .byte 0
key_event: .byte 0
start_pending: .byte 0
digits: .fill 3,0
digit_no: .byte 0
digit_row: .byte 0
digit_col: .byte 0
digit_bits: .byte 0
digit_x: .byte 6,12,18
pixel_lo: .byte $00,$40,$80
pixel_hi: .byte $8c,$8c,$8c
digit_screen: .word $480,$481,$482,$483,$484,$485
screen_lo: .byte <M_SCREEN0,<M_SCREEN1,<M_SCREEN2
screen_hi: .byte >M_SCREEN0,>M_SCREEN1,>M_SCREEN2
screen_bank: .byte (M_SCREEN0>>16)&15,(M_SCREEN1>>16)&15,(M_SCREEN2>>16)&15
screen_copy:
    .byte $80,$80,$81,0,$0a,0,0
    .word 2000
    .byte <M_SCREEN0,>M_SCREEN0,(M_SCREEN0>>16)&15
    .word $9000
    .byte 0
    .word 0
digit_copy:
    .byte $0a,0,0
    .word 384
    .word $8c00
    .byte 0
    .word $2000
    .byte 1
    .word 0
colour_fill:
    .byte $80,0,$81,$ff,$0a,0,3
    .word 2000
    .word 0
    .byte 0
    .word $2000
    .byte 8
    .word 0
.import source "menu_palette.inc"
.if (*>$7800) { .error "Menu controller overlaps animation" }

// Private fixed-position menu renderer. Six complete FCM cells per actor.
*=$7800 "32 independent menu animations"
menu_init:
    ldx #31
!loop:
    lda menu_initial_frames,x
    sta menu_frames,x
    lda menu_initial_delays,x
    sta menu_delays,x
    dex
    bmi wide_skip_54
    jmp !loop-
wide_skip_54:
    lda #0
    sta menu_clock
    rts
menu_tick:
    inc menu_clock
    lda menu_clock
    cmp #MENU_FRAME_DIVIDER
    bcc wide_skip_55
    jmp !animate+
wide_skip_55:
    rts
!animate:
    lda #0
    sta menu_clock
menu_animate:
    ldx #31
!actor:
    dec menu_delays,x
    beq wide_skip_56
    jmp !next+
wide_skip_56:
    lda menu_periods,x
    sta menu_delays,x
    lda menu_frames,x
    clc
    adc #1
    cmp menu_counts,x
    bcs wide_skip_57
    jmp !frame+
wide_skip_57:
    lda #0
!frame:
    sta menu_frames,x
    asl
    sta menu_offset
    asl
    clc
    adc menu_offset
    asl // frame *12 bytes, <=132
    clc
    adc menu_base_lo,x
    sta menu_read+1
    lda menu_base_hi,x
    adc #0
    sta menu_read+2
    lda menu_dst_lo,x
    sta menu_write+1
    lda menu_dst_hi,x
    sta menu_write+2
    lda #3
    sta menu_rows
!row:
    ldy #3
!byte:
menu_read:
    lda $ffff,y
menu_write:
    sta $ffff,y
    dey
    bmi wide_skip_58
    jmp !byte-
wide_skip_58:
    clc
    lda menu_read+1
    adc #4
    sta menu_read+1
    bcs wide_skip_59
    jmp !src+
wide_skip_59:
    inc menu_read+2
!src:
    clc
    lda menu_write+1
    adc #80
    sta menu_write+1
    bcs wide_skip_60
    jmp !dst+
wide_skip_60:
    inc menu_write+2
!dst:
    dec menu_rows
    beq wide_skip_61
    jmp !row-
wide_skip_61:
!next:
    dex
    bpl wide_skip_62
    jmp !done+
wide_skip_62:
    jmp !actor-
!done:
    rts
menu_offset: .byte 0
menu_rows: .byte 0
.if (* > $8000) { .error "Menu animator exceeds private code budget" }

.import source "stage6b1_banking.asm"
.import source "menu_assets.inc"
*=$8d80 "Digit tile background keeps adjacent original L"
digit_background:
.import binary "digit_background.bin"
*=$9800 "Original Amiga menu font in C64 screen-code layout"
.import binary "menu_font.bin"
