// Stage5a: bounded bank1 record parser; no CPU ROM reads, no original data edits.
*=$3200 "Stage5a record validation and byte reader"
.namespace s3b2 {
.label pointer=level.read_pointer
.label new_pointer=$1da0
.label word_value=$1da2
.label enemy_start=$1da4
.label group_total=$1da6
.label groups_left=$1da8
.label enemies_left=$1da9
.label attacks_left=$1daa
.label selected_type=$1dab
.label frame=$1dac
.label frame_count=$1dad
.label source_base=$1dae
.label frame_source=$1db0
.const DIRECTORY=$6a00
.const GRAPHICS=$9800
prepare:
    jsr level.load_record
    bcc !valid+
    jmp invalid
!valid:
    lda #<$2008
    sta pointer
    lda #>$2008
    sta pointer+1
    lda #0
    sta group_total
    sta group_total+1
    sta frame
    lda $7602
    sta groups_left
!group:
    jsr read_word
    bcc !guard+
    jmp invalid
!guard:
    lda word_value+1
    beq !guard+
    jmp invalid
!guard:
    lda word_value
    bne !guard+
    jmp invalid
!guard:
    clc
    adc group_total
    bcc !guard+
    jmp invalid
!guard:
    sta group_total
    jsr read_word
    bcc !guard+
    jmp invalid
!guard:
    jsr read_word
    bcc !guard+
    jmp invalid
!guard:
    jsr read_word
    bcc !guard+
    jmp invalid
!guard:
    lda word_value
    ora word_value+1
    bne !guard+
    jmp invalid
!guard:
    jsr skip_curve
    bcc !guard+
    jmp invalid
!guard:
    dec groups_left
    bne !group-
    lda group_total
    cmp $7603
    beq !guard+
    jmp invalid
!guard:
    lda pointer
    sta enemy_start
    lda pointer+1
    sta enemy_start+1
    jmp level.validate_enemies
invalid:
    lda #7
    sta s3b.error
    sec
    rts
get_byte:
    lda pointer+1
    cmp level.record_end+1
    bcc !read+
    bne !bad+
    lda pointer
    cmp level.record_end
    bcs !bad+
!read:
    jsr level.read_record
    pha
    inc pointer
    bne !done+
    inc pointer+1
!done:
    pla
    clc
    rts
!bad:
    lda #7
    sta s3b.error
    sec
    rts
read_word:
    jsr get_byte
    bcs !done+
    sta word_value
    jsr get_byte
    bcs !done+
    sta word_value+1
!done:
    rts
skip_curve:
    clc
    lda pointer
    adc word_value
    sta new_pointer
    lda pointer+1
    adc word_value+1
    sta new_pointer+1
    bcs !bad+
    cmp level.record_end+1
    bcc !ok+
    bne !bad+
    lda new_pointer
    cmp level.record_end
    bcc !ok+
    bne !bad+
!ok:
    lda new_pointer
    sta pointer
    lda new_pointer+1
    sta pointer+1
    clc
    rts
!bad:
    jmp invalid
init_objects:
    jsr v014_init_objects
    rts
animate:
    jsr s2ja_animate_pixies
    inc frame
    lda frame
    cmp #12
    bcc !done+
    lda #0
    sta frame
!done:
    ldx #0
!enemy_frame:
    inc level.gframe,x
    lda level.gframe,x
    cmp level.gframes,x
    bcc !next+
    lda #0
    sta level.gframe,x
!next:
    inx
    cpx $7603
    bne !enemy_frame-
    rts
// Compatibility cache for the isolated F test; normal enemies use private banks.
draw_frame:
    jmp level.enemy_frame
code_end:
}
.if (* > $3600) { .error "Stage5a data code overlaps approved player assets" }
