// Stage10a1: phase-shared5000..563F contains the audio loader AND hslink seed.
// entry.e_save_colour overwrites this with BASIC Color RAM. Keep the original
// code once per PRG load, outside the engine/overlay archives, and restore it
// at every BASIC-video exit. Repeated RUN must not execute colour bytes.
*=$8880 "Stage10a1 phase-shared loader cache"
.namespace bootstrapcache {
save:
    lda valid
    bne done
    inc valid
    lda #>save_list
    ldx #<save_list
    jmp hud.transfer
restore:
    lda valid
    beq done
    lda #>restore_list
    ldx #<restore_list
    jmp hud.transfer
done: rts
valid: .byte 0
save_list:
    .byte $80,0,$81,$80,$0a,0,0
    .word $640
    .byte 0,$50,0,0,0,$0a
    .word 0
restore_list:
    .byte $80,$80,$81,0,$0a,0,0
    .word $640
    .byte 0,0,$0a,0,$50,0
    .word 0
.if (*>$8900) { .error "Loader cache overlaps projectile pointers" }
}
