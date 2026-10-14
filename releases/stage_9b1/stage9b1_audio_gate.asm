// Resident, IRQ-safe bridge; only A000-BFFF is temporarily mapped to physical1E000.
.namespace audio8 {
.label command=$1fd0
.label ready=$1fd1
.label bootmap=$1fd2
.label error=$1fd3
.label arg_a=$1fd4
.label arg_x=$1fd5
.label arg_y=$1fd6
.macro event(n) {
 php
 pha
 lda #n
 sta command
 pla
 plp
 jmp gate
}
*=$33c0 "Stage8b register/IRQ preserving bank gate"
gate:
 php
 sei
 cld
 pha
 .byte $da,$5a,$db // PHX,PHY,PHZ
 sta arg_a
 stx arg_x
 sty arg_y
 lda ready
 beq !restore+
 lda #0
 ldx #0
 ldy #$40
 .byte $a3,$21,$5c,$ea // LDZ#$21; MAP; EOM => upper offset14000, A000 segment
 jsr $a000
 lda #0
 ldx #0
 ldy #0
 .byte $a3,$83,$5c,$ea // restore native SYS E000->3E000 before IRQs
!restore:
 .byte $fb,$7a,$fa // PLZ,PLY,PLX
 pla
 plp
 rts
cached: .byte 0
startup:
 lda #0
 sta ready
 sta error
 jmp s3b.entry
.if (*>$3400) { .error "Audio gate overlaps cache helpers" }
*=$35d4
service:
 jmp poll
 .fill 9,$ea
tick: :event(1)
entry: :event(2)
.if (*>$3600) { .error "Audio thunks overlap player source" }
*=$37d0
attack: :event(3)
enemy_shot: :event(4)
enemy_death: :event(5)
player_shot: :event(6)
.if (*>$3800) { .error "Audio thunks overlap HUD" }
*=$3ed0
player_death: :event(7)
transition_early: :event(8)
transition_rect: :event(9)
reset: :event(10)
.if (*>$3f00) { .error "Audio thunks overlap colour templates" }
*=$4fd8
stop: :event(11)
init: :event(12)
restart: :event(14)
.if (*>$5000) { .error "Audio thunks overlap colour backup" }
*=$5c50
load_and_menu:
 php
 sei
 lda $d030
 sta bootmap
 lda cached
 bne !cached+
 jsr bootstrap_copy
 inc cached
!cached:
 lda #0
 jsr boot_call
 plp
 lda s3b.error
 bne !done+
 jmp menubank.load
!done:
 rts
.if (*>$5c80) { .error "Audio load gate overlaps sprite pointers" }
*=$66b0
// Bootstrap requests a KERNAL entry by patching the JSR operand while IRQ-masked.
rom_call:
 pha
 .byte $da,$5a
 lda #0
 ldx #0
 ldy #0
 .byte $a3,$83,$5c,$ea // native SYS mapping for KERNAL
 .byte $7a,$fa
 pla
 .byte $a3,0 // Z=0 KERNAL calling convention, bootstrap itself does not use Z
 cli
rom_jsr:
 jsr $ffff
 // Capture return flags only AFTER masking IRQs, while native SYS ROM is mapped.
 // PLP below must never expose I=0 with the bootstrap mapped at A000.
 sei
 php
 pha
 .byte $da,$5a
 lda #0
 ldx #0
 ldy #$40
 .byte $a3,$20,$5c,$ea // remap CPU A000 to physical E000 bootstrap
 .byte $7a,$fa
 pla
 plp
 sei
 rts
.if (*>$66e0) { .error "KERNAL trampoline overlaps install gate" }
*=$66e0
install:
 lda #3
 jsr boot_call
 lda #1
 sta ready
 rts
finish: :event(13)
.if (*>$6700) { .error "Audio install overlaps immutable blank template" }
*=$9d1a
begin_hook:
 jsr shots.p_disable
 jmp transition_early
finish_exit:
 jsr titlecache.tc_restore
 jsr finish
 lda #0
 sta ready
 rts
.if (*>$9d30) { .error "Audio exit gate overlaps VYSH name" }
}

.namespace audio8 {
*=$31f1
rect_hook:
 lda #2
 sta transitionfx.state
 jmp transition_rect
stop_then_sprites:
 jsr stop
 jmp selection.restore_sprites
.if (*>$3200) { .error "Transition audio hook overlaps record parser" }
*=$9d61
filename: .text "VYSO.DAT,S,R"
 .byte 0
.if (*>$9d70) { .error "Audio filename overlaps conditional renderer" }
}

.namespace audio8 {
*=$662c
bootstrap_copy:
 lda #0
 sta $d702
 sta $d704
 lda #>bootstrap_dma
 sta $d701
 lda #<bootstrap_dma
 sta $d705
 rts
bootstrap_dma:
 .byte $0a,0,0
 .word $1000,$5000
 .byte 0
 .word $e000
 .byte 0
 .word 0
.if (*>$6650) { .error "Bootstrap copy overlaps transition initialization" }
}

.namespace audio8 {
*=$8e14
boot_call:
 sta boot_jump+1
 php
 sei
 cld
 pha
 .byte $da,$5a,$db
 lda #0
 ldx #0
 ldy #$40
 .byte $a3,$20,$5c,$ea
boot_jump:
 jsr $a000
 lda #0
 ldx #0
 ldy #0
 .byte $a3,$83,$5c,$ea
 .byte $fb,$7a,$fa
 pla
 plp
 rts
.if (*>$8e40) { .error "Bootstrap bank gate overlaps clipping" }
}

.namespace audio8 {
*=$87d0
// At most one bank switch per physical rasterline/frame for tiny engine jobs.
poll:
 php
 pha
 lda ready
 beq !done+
 lda $d012
 cmp $1fd7
 bne !due+
 lda $d7fa
 cmp $1fd8
 beq !done+
!due:
 lda $d012
 sta $1fd7
 lda $d7fa
 sta $1fd8
 lda #0
 sta command
 pla
 plp
 jmp gate
!done:
 pla
 plp
 rts
.if (*>$8800) { .error "Audio poll overlaps shared glyphs" }
}
