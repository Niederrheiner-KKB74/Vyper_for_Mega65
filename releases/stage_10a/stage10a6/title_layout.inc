.const T_FILE_BYTES=$ebcd
.const T_FILE_SUM=$d5a
.const T_PREFIX_BYTES=$7d
.const T_TILE_OFFSET=$acd
.var t_data=LoadBinary("VYTI.DAT")
t_tile_copy_0:
    .byte $80,0,$81,0,$0a,0,0
    .word $1800
    .byte $cd,$0a,$04,$00,$28,$01
    .word 0
t_tile_copy_1:
    .byte $80,0,$81,0,$0a,0,0
    .word $9d00
    .byte $cd,$22,$04,$00,$5b,$01
    .word 0
t_tile_copy_2:
    .byte $80,0,$81,0,$0a,0,0
    .word $2c00
    .byte $cd,$bf,$04,$00,$c5,$05
    .word 0
