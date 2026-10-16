hs_save:
    .byte $80,$00,$81,$80,$0a,0,0
    .word $b000
    .word $2000
    .byte $00
    .word $0000
    .byte $09
    .word 0
hs_restore:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $b000
    .word $0000
    .byte $09
    .word $2000
    .byte $00
    .word 0
hs_load0:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $4e00
    .word $0000
    .byte $08
    .word $2100
    .byte $00
    .word 0
hs_load2:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $22ff
    .word $4f00
    .byte $08
    .word $7000
    .byte $00
    .word 0
hs_check:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $0010
    .word $0000
    .byte $08
    .word $6900
    .byte $00
    .word 0
