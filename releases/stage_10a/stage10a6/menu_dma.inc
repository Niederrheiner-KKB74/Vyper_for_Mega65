header_copy:
    .byte $80,$00,$81,$00,$0a,0,0
    .word $0020
    .word $0000
    .byte $04
    .word $6900
    .byte $00
    .word 0
asset_header:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $0020
    .word $0000
    .byte $01
    .word $6900
    .byte $00
    .word 0
asset_save0:
    .byte $80,$00,$81,$80,$0a,0,0
    .word $ff00
    .word $0000
    .byte $04
    .word $0000
    .byte $01
    .word 0
asset_save1:
    .byte $80,$00,$81,$80,$0a,0,0
    .word $53c0
    .word $ff00
    .byte $04
    .word $ff00
    .byte $01
    .word 0
engine_save:
    .byte $80,$00,$81,$80,$0a,0,0
    .word $3000
    .word $7000
    .byte $00
    .word $1000
    .byte $00
    .word 0
engine_restore:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $3000
    .word $1000
    .byte $00
    .word $7000
    .byte $00
    .word 0
colour_save:
    .byte $80,$00,$81,$80,$0a,0,0
    .word $0a50
    .word $f100
    .byte $05
    .word $4000
    .byte $00
    .word 0
colour_restore:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $0a50
    .word $4000
    .byte $00
    .word $f100
    .byte $05
    .word 0
overlay_load:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $3000
    .word $22c0
    .byte $02
    .word $7000
    .byte $00
    .word 0
atlas_low:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $d000
    .word $0050
    .byte $01
    .word $2800
    .byte $01
    .word 0
atlas_high:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $3b00
    .word $d050
    .byte $01
    .word $c500
    .byte $05
    .word 0
font_load:
    .byte $80,$80,$81,$00,$0a,0,0
    .word $0800
    .word $4ac0
    .byte $02
    .word $4000
    .byte $00
    .word 0
