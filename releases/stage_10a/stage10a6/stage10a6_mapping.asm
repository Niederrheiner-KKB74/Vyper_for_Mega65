*=$8900 "Projectile pointers and mapping"
.namespace shots {
pointer_data: .fill 16,0
p_mapping: .byte 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38
p_mapping_confirmed: .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
}
*=$8a00 "Original3x7 projectile graphics; player red tip above"
.namespace shots {
.import binary "projectile_sprites.bin"
}
