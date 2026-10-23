*=$3600 "Highscore private state and UI constants"
hi_mode: .byte 0 // 0view,1score,2name,3message
hi_device: .byte 8
hi_blocked: .byte 0
hi_present: .byte 0
hi_dirty: .byte 0
hi_error: .byte 0
hi_dos: .byte 0
hi_stage: .byte 0
hi_len: .byte 0
hi_name_len: .byte 0
hi_rank: .byte 0
hi_row: .byte 0
hi_slot: .byte 0
hi_col: .byte 0
hi_count: .byte 0
hi_key_byte: .byte 0
hi_return_lock: .byte 0
hi_score: .fill 4,0
hi_work: .fill 4,0
hi_old: .fill 4,0
hi_previous: .fill 4,$ff
hi_name: .fill 3,0
hi_digits: .fill 10,0
hi_number: .fill 10,32
hi_crc: .word 0
hi_offset: .word 0
hi_ptr: .word 0
hi_left: .word 0
hi_status_lo: .byte <hi_msg_ready
hi_status_hi: .byte >hi_msg_ready
hi_alphabet: .text "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-+/."
.byte 64 // literal ASCII @; KickAssembler PETSCII encoding otherwise emits NUL
.text "!?"
.byte 0
hi_magic: .byte $56,$59,$48,$49,1,32,7
hi_msg_ready: .text "LEFT/RIGHT: PAGE   OTHER KEY: MENU"; .byte 0
hi_msg_missing: .text "NEW EMPTY LIST - SAVED AFTER CONFIRMED ENTRY"; .byte 0
hi_msg_bad: .text "INVALID FILE / BACKUP RECOVERY: DISK KEPT, READ ONLY"; .byte 0
hi_msg_score: .text "SCORE 0..4294967295; RETURN: NEXT; ESC: CANCEL"; .byte 0
hi_msg_name: .text "ENTER EXACTLY 3 CHARS; DEL: CORRECT; RETURN: SAVE; ESC: CANCEL"; .byte 0
hi_msg_reject: .text "NOT QUALIFIED - PRESS ESC OR RETURN"; .byte 0
hi_msg_saved: .text "SAVED AND VERIFIED - RETURN TO MENU"; .byte 0
hi_msg_failed: .text "DISK ERROR - OLD LIST RESTORED; CHECK MEDIA AND RESTART"; .byte 0
hi_msg_readonly: .text "READ ONLY: REPAIR FILES IN BASIC OR USE A CLEAN DISK COPY"; .byte 0
hi_msg_input: .text "INVALID INPUT / OVERFLOW; CORRECT OR PRESS ESC"; .byte 0
hi_page_text: .text "PAGE 1/4 - HIGH SCORES"; .byte 0
hi_powers:
.for (var n=9;n>=0;n--) { .dword pow(10,n) }
hi_rec_lo: .fill 80,<($4800+32+7*i)
hi_rec_hi: .fill 80,>($4800+32+7*i)
hi_screen_lo: .fill 20,<($a000+80*(7+mod(i,10))+(i<10 ? 16 : 49))
hi_screen_hi: .fill 20,>($a000+80*(7+mod(i,10))+(i<10 ? 16 : 49))
hi_filename: .text "0:VYHI.DAT,S,R"; .byte 0
hi_tmp_read: .text "0:VYHI.TMP,S,R"; .byte 0
hi_tmp_write: .text "0:VYHI.TMP,S,W"; .byte 0
hi_bak_read: .text "0:VYHI.BAK,S,R"; .byte 0
hi_scratch_bak: .text "S0:VYHI.BAK"; .byte 0
hi_rename_bak: .text "R0:VYHI.BAK=VYHI.DAT"; .byte 0
hi_rename_dat: .text "R0:VYHI.DAT=VYHI.TMP"; .byte 0
hi_file_ptr: .word 0
hi_file_len: .byte 0
hi_lfn: .byte 2
hi_secondary: .byte 2
hi_io_byte: .byte 0
hi_io_status: .byte 0
hi_cmd_budget: .byte 0
hi_cmd_code: .byte 0
.if (*>$4000) { .error "Highscore UI data overlaps background" }
hi_shift: .fill 7,0
hi_display_slot: .byte 0
hi_display_rank: .byte 0
hi_digit_value: .byte 0
hi_leading: .byte 0
hi_math_left: .byte 0
hi_score_label: .text "SCORE ["; .byte 0
hi_name_label: .text "NAME ["; .byte 0
.if (*>$4000) { .error "Highscore data exceeds budget" }

hi_cache_slot: .byte 0
hi_cache_lo: .fill 80,<($5500+10*i)
hi_cache_hi: .fill 80,>($5500+10*i)
.if (*>$4000) { .error "Score cache pointers overlap background" }

hi_recovered: .byte 0
hi_probe_error: .byte 0
hi_probe_dos: .byte 0
hi_msg_pending: .text "PENDING TEMP / IO ERROR: FILES KEPT; READ ONLY - CHECK DISK"; .byte 0
.if (*>$4000) { .error "Recovery state overlaps background" }

hi_error_label: .text "IO "; .byte 0
hi_dos_label: .text " DOS "; .byte 0
.if (*>$4000) { .error "Diagnostics overlap background" }
