// Stage 3a-1 standalone MEGA65/C64 KERNAL sequential file/header test.
// No DMA and no renderer in this stage.
// MEGA65 BASIC 65: 10 SYS 8448, start code at $2100.
*=$2001
BasicUpstart:
    .word BasicEnd
    .word 10
    .byte $9e
    .text "8448"
    .byte 0
BasicEnd:
    .word 0
*=$2100
start:
    lda #$93
    jsr $ffd2
    ldx #<msg_title
    ldy #>msg_title
    jsr print_string
    // Filename is uppercase PETSCII bytes; lowercase .text maps to control bytes.
    // KERNAL current device ($BA) usually retains the LOAD device.
    lda $ba
    cmp #8
    bcs device_ok
    lda #8
 device_ok:
    sta device
    ldx #<msg_device
    ldy #>msg_device
    jsr print_string
    lda device
    jsr print_hex
    lda #13
    jsr $ffd2
    lda #2
    ldx device
    ldy #2
    jsr $ffba       // SETLFS logical file 1, secondary 2
    lda #0          // LOAD/SAVE data bank 0
    ldx #0          // Filename bank 0
    jsr $ff6b       // MEGA65 SETBNK
    lda #12
    ldx #<filename
    ldy #>filename
    jsr $ffbd       // SETNAM
    jsr $ffc0       // OPEN
    bcc open_ok
    jmp open_error
 open_ok:
    lda #0
    sta status_open
    ldx #2
    jsr $ffc6       // CHKIN
    bcc channel_ok
    jmp channel_error
 channel_ok:
    lda #0
    sta status_chkin
    lda #0
    sta read_index
    sta last_status
 read_loop:
    jsr $ffcf
    sta first_byte
    ldx read_index       // CHRIN
    sta header,x
    jsr $ffb7       // READST; no screen output while input channel active
    sta last_status
    bne read_error  // For an 8-byte header, any premature EOF is an error
    inc read_index
    lda read_index
    cmp #8
    bne read_loop
    jsr close_file
    ldx #0
 check_magic:
    lda header,x
    cmp signature,x
    bne invalid
    inx
    cpx #8
    bne check_magic
    jsr print_statuses
    ldx #<msg_success
    ldy #>msg_success
    jsr print_string
    jmp finished
 invalid:
    jsr print_statuses
    ldx #<msg_invalid
    ldy #>msg_invalid
    jsr print_string
    jmp finished
 read_error:
    jsr close_file
    jsr print_statuses
    ldx #<msg_read
    ldy #>msg_read
    jsr print_string
    jmp finished
print_statuses:
    ldx #<msg_openst
    ldy #>msg_openst
    jsr print_string
    lda status_open
    jsr print_hex
    lda #13
    jsr $ffd2
    ldx #<msg_chkinst
    ldy #>msg_chkinst
    jsr print_string
    lda status_chkin
    jsr print_hex
    lda #13
    jsr $ffd2
    ldx #<msg_first
    ldy #>msg_first
    jsr print_string
    lda first_byte
    jsr print_hex
    lda #13
    jsr $ffd2
    ldx #<msg_status
    ldy #>msg_status
    jsr print_string
    lda last_status
    jsr print_hex
    lda #13
    jsr $ffd2
    ldx #<msg_count
    ldy #>msg_count
    jsr print_string
    lda read_index
    jsr print_hex
    lda #13
    jsr $ffd2
    rts
 channel_error:
    jsr close_file
 open_error:
    ldx #<msg_open
    ldy #>msg_open
    jsr print_string
 finished:
    ldx #<msg_done
    ldy #>msg_done
    jsr print_string
    rts
close_file:
    jsr $ffcc       // CLRCHN, before ANY result output
    lda #2
    jsr $ffc3       // CLOSE
    rts
print_string:
    stx str_ptr+1
    sty str_ptr+2
    ldx #0
 print_next:
 str_ptr:
    lda $ffff,x
    beq print_end
    jsr $ffd2
    inx
    bne print_next
 print_end:
    rts
print_hex:
    pha
    lsr
    lsr
    lsr
    lsr
    jsr nibble
    pla
    and #$0f
nibble:
    and #$0f
    cmp #10
    bcc digit
    adc #6
 digit:
    adc #$30
    jmp $ffd2
filename:
    .text "VYLV.DAT,S,R"
signature:
    .byte $56,$59,$4c,$56,$01,$00,$64,$00
msg_title:
    .text "VYPER STAGE 3A-1"
    .byte 13
    .text "HEADER TEST - SETBNK 0"
    .byte 13
    .byte 13
    .byte 0
msg_device:
    .text "DEVICE $"
    .byte 0
msg_success:
    .text "VYLV.DAT HEADER OK"
    .byte 13
    .text "VERSION 1 / 100 LEVELS"
    .byte 13
    .byte 0
msg_invalid:
    .text "ERROR: INVALID HEADER"
    .byte 13
    .byte 0
msg_openst: .text "AFTER OPEN $"
    .byte 0
msg_chkinst: .text "AFTER CHKIN $"
    .byte 0
msg_first: .text "CHRIN BYTE $"
    .byte 0
msg_status:
    .text "READST $"
    .byte 0
msg_count:
    .text "BYTE INDEX $"
    .byte 0
msg_read:
    .text "ERROR: SHORT FILE OR READ"
    .byte 13
    .byte 0
msg_open:
    .text "ERROR: CANNOT OPEN VYLV.DAT"
    .byte 13
    .byte 0
msg_done:
    .byte 13
    .text "TEST COMPLETE"
    .byte 13
    .byte 0
device:
    .byte 8
header: .fill 8,0
read_index: .byte 0

last_status: .byte 0

status_open: .byte 0
status_chkin: .byte 0
first_byte: .byte 0
