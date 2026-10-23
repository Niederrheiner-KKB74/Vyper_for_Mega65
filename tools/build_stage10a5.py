#!/usr/bin/env python3
"""Stage10a5: Stage10a4 plus debounced menu/highscore fire and transition before the first level."""
import argparse,json,os,shutil,struct,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import d81_highscore as DISK
import build_stage3b3 as PLAYER
import build_stage5d1a as ENGINE
import convert_stage5d1_title as TITLE
import convert_stage6b1_menu as MENU
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[f'stage10a5{s}.asm' for s in ENGINE.COMPONENTS+['_title','_entry_projection','_cycling','_integration','_banking','_stars','_transition','_selection','_fire','_fire_loader','_motion','_audio_gate','_audio_loader','_highscore','_two_player','_bootstrap_cache','_get_ready','_unpack']]
STABLES={'2954dc57418f3898b8f958a9d15d79a57b2dd6bb':'2954dc57418f3898b8f958a9d15d79a57b2dd6bb','bd63682fa37df2853338b499f1210ec9dd2f56dc':'bd63682fa37df2853338b499f1210ec9dd2f56dc','a41e92ab8e4994a0a3288d60d63984d8593c8332':'a41e92ab8e4994a0a3288d60d63984d8593c8332','ec7a512bf913e522e5aaadfd57c9c4e7bb019bef':'ec7a512bf913e522e5aaadfd57c9c4e7bb019bef','stage7b1-stable':'5d9c4f563f9fd3de7f5786b623791b7fc26e79e7','stage7a2-stable':'b4cc1f7f4f2250bb69664ba15613350942e29d9c','stage7a1-stable':'9ebbcabd2a792661b0da354f2716abb7772d74a6','stage6b1-stable':'31ae0bd4bcdd79f3217126f902cf9978907cb48d','stage5d1a-stable':'39890c0095fab55b2ea71f95cccf59a3419848c6','stage6a2-stable':'24559e46c4f237492bc4e03439c86ea6c402a0b0'}
def protect_stable():
    import io,tarfile
    for ref,commit in STABLES.items():
        if subprocess.check_output(['git','rev-parse',ref+'^{}'],cwd=ROOT,text=True).strip()!=commit:raise ValueError('Stable ref changed '+ref)
    for ref in ('dd11d2a50fd777162946479098796c55c61fcd53','6052f677a8b84a841549561e874cd2f3290b2129','bbf996531f31920f2baa1111f74722d075fceba0','daf45af4a95f34e45c84103c55d6fc25d79a0a1d','36d5a4b546fb514e435d4567b36c68e8cd18b6e2','475355caae166e7e42aa8322addf9c04554e18ec','cce69ee2f905cd88a662834190ef4ea25dfc953e','bf5a309c1294ea69a4e79ec38dd853ee48b8e28d'):
        archive=subprocess.check_output(['git','archive',ref,'src','assets','tools','releases'],cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            for item in files:
                local=ROOT/item.name
                if item.isfile() and local.exists() and local.read_bytes()!=files.extractfile(item).read():raise ValueError('Stable changed '+item.name)
def descriptor(name,src,dst,n,command=0):
    return f'{name}:\n    .byte $80,${src>>20:02x},$81,${dst>>20:02x},$0a,0,{command}\n    .word ${n:04x}\n    .word ${src&65535:04x}\n    .byte ${(src>>16)&15:02x}\n    .word ${dst&65535:04x}\n    .byte ${(dst>>16)&15:02x}\n    .word 0\n'
def assemble(w,jar,src,out):
    run=subprocess.run(['java','-jar',str(jar),src,'-o',out,'-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(run.stdout,end='');run.check_returncode();return run.stdout
def build(jar,output,zx0=None):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_10a/stage10a5'):raise ValueError('Protected release target')
    protect_stable();PLAYER.verify_player_assets()
    with tempfile.TemporaryDirectory(prefix='vyper-10a-') as t:
        w=Path(t);ti,title=TITLE.build(w);menu=MENU.convert(w)
        # Confirmed format/graphics stay unchanged; only the phase controller differs.
        for name in ('pages.bin','colours.bin','frame.bin','VYHI.DAT'):
            shutil.copyfile(ROOT/'releases/stage_9c2'/name,w/name)
        # Normal presentation has one navigation hint, no status/debug rows.
        page=bytearray((w/'pages.bin').read_bytes());colours=bytearray((w/'colours.bin').read_bytes())
        hint='CURSOR / JOYSTICK LEFT-RIGHT: CHANGE PAGE';hx=(80-len(hint))//2
        import build_stage9c2 as HSBASE
        page[18*80+hx:18*80+hx+len(hint)]=bytes(HSBASE.screen_code(c) for c in hint)
        title_text=HSBASE.TITLE;footer_text=HSBASE.FOOTER
        for text,y,x in ((title_text,3,(80-len(title_text))//2),(hint,18,hx),(footer_text,21,(80-len(footer_text))//2)):
            colours[y*80+x:y*80+x+len(text)]=bytes([4])*len(text)
        (w/'pages.bin').write_bytes(page);(w/'colours.bin').write_bytes(colours)
        for src in (ROOT/'src/tests').glob('stage10a5*.asm'):shutil.copyfile(src,w/src.name)
        shutil.copyfile(ROOT/'assets/stage6a2/color_cycle.inc',w/'color_cycle.inc')
        hs_asm=assemble(w,jar,'stage10a5.asm','HIGHSCORE.PRG')
        shutil.copyfile(w/'stage10a5.sym',w/'highscore.sym')
        hs=(w/'HIGHSCORE.PRG').read_bytes();assert hs[:2]==b'\x01\x20'
        hs=hs[2+0xff:] # SYS test stub is not part of the runtime overlay; starts2100.
        assert len(hs)<0x8000
        (w/'VYHS.DAT').write_bytes(hs)
        (w/'highscore_prefix.bin').write_bytes(hs[:16])
        (w/'highscore_layout.inc').write_text(f'.const HS_BYTES=${len(hs):x}\n.const HS_SUM=${sum(hs)&65535:x}\n')
        hs_jobs=[('hs_save',0x2000,0x08090000,0xb000),('hs_restore',0x08090000,0x2000,0xb000),('hs_load0',0x08080000,0x2100,0x4e00),('hs_load2',0x08084f00,0x7000,len(hs)-0x4f00),('hs_archive',0x40000,0x08080000,len(hs))]
        (w/'highscore_dma.inc').write_text(''.join(descriptor(*j) for j in hs_jobs[:4]+[('hs_check',0x08080000,0x6900,16)]))
        (w/'highscore_archive.inc').write_text(descriptor(*hs_jobs[4]))
        import convert_stage7b5a_fire as FIRE
        fire=FIRE.convert(w)
        import convert_stage7a2_stars as STAR
        star=STAR.convert(w)
        import analyze_stage7b2_projectiles as SHOT
        shot=SHOT.analyze(w)
        if (w/'projectile_sprites.bin').read_bytes()!=(ROOT/'assets/stage7b2/projectile_sprites.bin').read_bytes():raise ValueError('Projectile conversion differs')
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                p=w/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',w/'explosion_assets');shutil.copytree(ROOT/'assets/player',w/'player_assets')
        for name in SOURCES+['stage10a5_menu.asm']:shutil.copyfile(ROOT/'src/engine'/name,w/name)
        shutil.copyfile(ROOT/'assets/stage6a2/color_cycle.inc',w/'color_cycle.inc')
        tiles=(w/'menu_fcm.bin').read_bytes();screens=(w/'menu_screens.bin').read_bytes();font=(w/'menu_font.bin').read_bytes()
        ch=dict(MENU.COP.chunks(MENU.MENU.SOURCE.read_bytes()));pal=[MENU.COP.be(ch[b'CHIP'],0xe4+2*i) for i in range(16)]
        rgb=bytes(((p>>s)&15)*17 for p in pal for s in (8,4,0))
        screen_offset=80+len(tiles);overlay_offset=screen_offset+len(screens);file_len=overlay_offset+12288
        if file_len>0x1c500:raise ValueError('Menu staging would corrupt title high cache')
        import re
        restore=int(re.search(r'\.label t_restore_video=\$([0-9a-f]+)',(ROOT/'releases/stage_5d_1_b2/STAGE5D1A.sym').read_text())[1],16)
        # Title FAST ORA adds two bytes before its restore routine.
        restore+=2
        seq=int(re.search(r'\.label load_file=\$([0-9a-f]+)',(ROOT/'releases/stage_5d_1_b2/STAGE5D1A.sym').read_text())[1],16)+12 # menu-load hook11 bytes + caller CLI1
        constants={'M_SEQ_LOAD':seq,'M_RESTORE_VIDEO':restore,'M_FILE_BYTES':file_len,'M_FILE_SUM':0,'M_ATLAS_BYTES':len(tiles),'M_OVERLAY':0x08010000+overlay_offset,'M_FONT':0x08010000+overlay_offset+0x2800}
        constants.update({f'M_SCREEN{i}':0x08010000+screen_offset+2000*i for i in range(3)})
        def layout(): (w/'menu_layout.inc').write_text(''.join(f'.const {k}=${v:x}\n' for k,v in constants.items()))
        layout()
        (w/'menu_palette.inc').write_text(''.join(f'{name}: .byte '+','.join(str(rgb[3*i+j]) for i in range(16))+'\n' for j,name in enumerate(['menu_red','menu_green','menu_blue'])))
        assemble(w,jar,'stage10a5_menu.asm','MENU_OVERLAY.PRG')
        overlay=(w/'MENU_OVERLAY.PRG').read_bytes();assert overlay[:2]==b'\x00\x70' and len(overlay)==12290
        body=rgb+tiles+screens+overlay[2:]
        header=struct.pack('<4sHHIIIIHHI',b'VYMN',2,32,len(tiles),screen_offset,overlay_offset,file_len,sum(body)&65535,0,0)
        assert len(header)==32
        mn=header+body;assert len(mn)==file_len;constants['M_FILE_SUM']=sum(mn)&65535;layout();(w/'menu_header.bin').write_bytes(header)
        jobs=[('header_copy',0x40000,0x6900,32),('asset_header',0x08010000,0x6900,32),('asset_save0',0x40000,0x08010000,0xff00),('asset_save1',0x4ff00,0x0801ff00,file_len-0xff00),('engine_save',0x7000,0x08001000,0x3000),('engine_restore',0x08001000,0x7000,0x3000),('colour_save',0x5f100,0x08004000,2640),('colour_restore',0x08004000,0x5f100,2640),('overlay_load',constants['M_OVERLAY'],0x7000,0x3000),('atlas_low',0x08010050,0x12800,832*64),('atlas_high',0x08010050+832*64,0x5c500,len(tiles)-832*64),('font_load',constants['M_FONT'],0x4000,2048)]
        (w/'menu_dma.inc').write_text(''.join(descriptor(*j) for j in jobs))
        data={n:(ROOT/path).read_bytes() for n,path in [('VYLV.DAT','assets/VYLV.DAT'),('VYGR.DAT','assets/stage5b/VYGR.DAT'),('VYCL.DAT','assets/stage5c/VYCL.DAT')]}
        data.update({'VYTI.DAT':ti,'VYMN.DAT':mn,'VYSH.DAT':(w/'VYSH.DAT').read_bytes()})
        for name,b in data.items():
            if name!='VYMN.DAT' and b!=(ROOT/'releases/stage_7b5a'/name).read_bytes():raise ValueError('Existing DAT changed '+name)
            (w/name).write_bytes(b)
        import convert_stage8b_audio as AUDIO
        audio_meta,pcm,audio_types=AUDIO.prepare(w)
        base_symbols=(ROOT/'releases/stage_7b5b/STAGE7B5B.sym').read_text()
        def addr(name):return int(re.search(r'\.label '+name+r'=\$([0-9a-f]+)',base_symbols)[1],16)
        (w/'audio_engine.inc').write_text(''.join(f'.label {a}=${addr(b):x}\n' for a,b in [('anim_pause_address','anim_paused'),('shots_x_address','p_xpos'),('motion_xhi_address','xhi'),('shooter_address','p_source_enemy')]))
        shutil.copyfile(ROOT/'src/engine/stage10a5_audio_core.asm',w/'stage10a5_audio_core.asm')
        assemble(w,jar,'stage10a5_audio_core.asm','AUDIO_CORE.PRG')
        shutil.copyfile(w/'stage10a5_audio_core.sym',w/'stage8b_audio_core.sym') # unchanged shared packer ABI
        audio=AUDIO.package(w,audio_meta,pcm,audio_types)
        data['VYSO.DAT']=(w/'VYSO.DAT').read_bytes()
        data['VYHS.DAT']=hs;data['VYHI.DAT']=(w/'VYHI.DAT').read_bytes()
        asm=assemble(w,jar,'stage10a5.asm' ,'STAGE10A5.PRG');prg=(w/'STAGE10A5.PRG').read_bytes()
        actual_restore=int(re.search(r'\.label t_restore_video=\$([0-9a-f]+)',(w/'stage10a5.sym').read_text())[1],16)
        actual_seq=int(re.search(r'\.label load_file=\$([0-9a-f]+)',(w/'stage10a5.sym').read_text())[1],16)
        # Live compatibility/orbit animation must retain all seven type2 frames.
        stable_prg=(ROOT/'releases/stage_9c3/stage9c3a/STAGE9C3A.PRG').read_bytes()
        program_base=int.from_bytes(prg[:2],'little')
        stable_base=int.from_bytes(stable_prg[:2],'little')
        assert prg[2+0xa200-program_base:2+0xa580-program_base]==stable_prg[2+0xa200-stable_base:2+0xa580-stable_base]
        actual_symbols=(w/'stage10a5.sym').read_text()
        for n in ('anim_paused','p_xpos','xhi','p_source_enemy'):
            if int(re.search(r'\.label '+n+r'=\$([0-9a-f]+)',actual_symbols)[1],16)!=addr(n):raise ValueError('Audio engine ABI moved '+n)
        if actual_seq!=seq:raise ValueError('Menu SEQ gate does not match assembled loader')
        if actual_restore!=restore:raise ValueError('Menu BASIC-restore gate does not match assembled title routine')
        # Stage10a2: every SEQ file read through s3b.load_file or the audio loader is
        # stored packed; VYHI stays raw (written by the highscore overlay's own disk code).
        import pack_stage10a2 as PACK
        pcm_start=int(audio['PCM_offset'])
        packed={n:(PACK.pack(b,pcm_start if n=='VYSO.DAT' else None,zx0) if n!='VYHI.DAT' else b) for n,b in data.items()}
        packing={n:{'raw':len(data[n]),'disk':len(packed[n])} for n in data}
        entries=[('STAGE10A5',prg,0x82)]+[(n,b,0x81) for n,b in packed.items()]
        disk=bytearray(DISK.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER STAGE10A5'.ljust(16,b'\xa0');disk=bytes(disk)
        files=DISK.verify_disk(disk,entries)
        report={'stage':'10a1','fire_events':fire,'issue':87,'stable':False,'starfield':star,'protected_bases':STABLES,'starfield_source_commit':'ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a','runtime_star_debug':False,'speed_API':'mode0 normal8/4/2; mode1 eightfold1/2/4 pixels per frame','transition':{'accelerated_frames':50,'ring_frames':3,'rings':13,'fill_frames':39,'black_frames':39,'initialization_frames':1,'bitmap':[0x18000,0x1ddbf],'approximation':'concentric8px bands, spatial outer-to-inner blue/yellow/red/darkblue; screenshot-derived geometry/RGB and3frames/ring approximation'},'projectiles':{'colour':'white/red/grey bank2/indices10,13,16','visual_logical_pixels':[3,7],'hitboxes_preserved':{'player':[1,4],'enemy':[3,4]},'original_conversion':shot['implementation'],'enemy':'Original3x7 white/red/grey; player reflected vertically'},'menu':menu,'title':title,'menu_DAT':{'bytes':len(mn),'sum16':sum(mn)&65535,'header':header.hex(),'offsets':constants},'files':files,'xemu':'NOT_RUN_BY_BUILDER; separate controlled XEMU protocol in docs/stage10a5_evidence; visual user acceptance pending','DMA':jobs}
        report['attack_motion']={'packed_cursor':'cyclic; only cursor resets at length','coordinates':'accumulated signed16','bottom_exit_y':200,'native_bottom_y':216,'shot_and_sound_plan':'once at attack start; never on wrap','one_byte_level_ban_preserved':[25,50,99,100],'base':'9bbe02ed9d284575c14c23954659a781d6889ee9'}
        report['audio']=audio
        report['stage10a5']={'menu':'unchanged; user confirmed configuration issue',
          'turn_handoff':'ordinary death stays active; successful level switches in-place after full transition; final death switches only after highscore return',
          'resume_IRQ':'masked before bootstrap rearm and level reconstruction',
          'bootstrap_cache':{'code':[0x8880,0x88bf],'source':[0x5000,0x5640],'attic':[0x080a0000,0x080a0640]},
          'title_cache':'re-armed on every resumed turn before font overwrites4000..47ff',
          'hud':{'p2_rows':[13,14,15],'p2_life_rows':[16,20],'separator_rows':[12,21], 'initial_shadow_invalidation':True,'point_rows':[22,23],'bottom_margin_row':24,
                 'active_inks':[12,13,14],'inactive_ink':11,'controls_hidden_2P_only':True}}

        report['stage10a5']['get_ready']={'frames':100,'Hz':50,'mode':3,'state':[0x1b1c,0x1b20],'native_code':[0x9a2a,0x9a4a],'mapped_code_start':0xaf08,'palette':'same bank1 cc_index as enemy COLOR02','rows':[17,19],'native_X':[204,208],'input_start_frame_not_counted':True,'timers_frozen':True}
        report['auto_levels']={'automatic':True,'bonus_every':3,'max_lives':30,'bonus_state':[0x1fd9,0x1fda],'base':'e932974e554f0cd9c84d1f95e63de6bf2e1853a2'}
        report['motion']={'player_step_test_default':2,'native_player_update_Hz':'unproven','enemy':'original16.16, level DY, parity spread0..19,45degree cap','signed_coordinates':True,'extra_state':[0x1f9a,0x1fcc],'legacy_T':'isolated unchanged8.8 helper'}
        report['attack_selection']={'interval_frames':30,'max_ATTACK':3,'eligible':'live FORMATION plus phase3','sampling':'power-of-two rejection; due timer retained on rejection/no actor'}
        report['projectiles'].update({'enemy_limit':6,'player_limit':2,'cooldown_frames':None,'normal_shot_decision':'original ENTRY countdown / ATTACK thresholds','state_range':[0x1f00,0x1f77],'eligible_list':[0x1f80,0x1f99],'per_enemy_limit':None,'ownership':'original shooter ID retained diagnostically; global slots2..7 only','snapshot':[0x1b60,0x1b8a],'base_graphics_byte_identical':True})
        out={'STAGE10A5.PRG':prg,'STAGE10A5.sym':(w/'stage10a5.sym').read_bytes(),'MENU_OVERLAY.PRG':overlay,'MENU_OVERLAY.sym':(w/'stage10a5_menu.sym').read_bytes(),'VYPER_STAGE10A5.d81':disk,**packed,'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(asm[asm.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in SOURCES+['stage10a5_audio_core.asm','AUDIO_CORE.PRG','stage10a5_audio_core.sym','audio_constants.inc','audio_engine.inc','audio_events.inc','audio_samples.inc','audio_file.inc','audio_header.bin','audio-metadata.json','stage10a5_menu.asm','menu_layout.inc','menu_dma.inc','menu_header.bin','menu_palette.inc','menu_assets.inc','menu_fcm.bin','menu_screens.bin','menu_font.bin','digit_background.bin','original_menu_indices.bin','title_layout.inc','title_screen.bin','title_fcm_unique.bin','color_cycle.inc','stars_layout.inc','projectile_sprites.bin','fire_layout.inc','fire_constants.inc','fire-parameters.json','highscore_layout.inc','highscore_dma.inc','highscore_archive.inc','highscore_prefix.bin','HIGHSCORE.PRG','highscore.sym']:out[name]=(w/name).read_bytes()
        for src in (ROOT/'src/tests').glob('stage10a5*.asm'):out['highscore/'+src.name]=src.read_bytes()
        for name in ('pages.bin','colours.bin','frame.bin','VYHI.DAT','color_cycle.inc'):out['highscore/'+name]=(w/name).read_bytes()
        out['highscore-memory-map.txt']=(hs_asm[hs_asm.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()
        for n in ('pages.bin','colours.bin','frame.bin'):out[n]=(w/n).read_bytes()
        report.update({'revision':'10a1','parent_build':'dd11d2a50fd777162946479098796c55c61fcd53','respawn':{'protection_frames':150,'blink_frames':25,'fire_during_blink':True},'highscore_UI':{'static_yellow':['title','navigation','footer'],'normal_debug_rows':False},'base':'36d5a4b546fb514e435d4567b36c68e8cd18b6e2','highscore_base':'bbf996531f31920f2baa1111f74722d075fceba0','highscore_dma':hs_jobs,'VYHI_format':'unchanged v1/CRC16/count80/u32','game_over_delay_frames':150,'two_player':{'record_bytes':8,'identities':2,'lives_max':30,'hud_icons_max':8,'hud_semantics':'all lives including current ship','unfinished_level':'documented per-player restart','state':[0x1b00,0x1b23],'baseline':'36d5a4b546fb514e435d4567b36c68e8cd18b6e2'}})
        report.update({'revision':'10a2','base':'stage10a1-hw (Stage10a1-HW2, hardware confirmed 2026-10-17)','packing':{'format':'Z0 total24 plain24 + ZX0 v2, VYSO PCM delta coded','ring':'Attic $080B0000-$080B7FFF','decoder':'src/engine/stage10a5_unpack.asm at $45CC-$47FF','files':packing,'raw_total':sum(v['raw'] for v in packing.values()),'disk_total':sum(v['disk'] for v in packing.values())}})
        report.update({'revision':'10a3','base':'Stage10a2 main 475355caae166e7e42aa8322addf9c04554e18ec','stage10a5':{'formation_ready':'first live FORMATION/phase3 enemy starts drift and attack countdown (was: whole entry complete)','attacks_during_entry':True,'attack_limits_unchanged':{'max_ATTACK':3,'interval_frames':30,'initial_frames':100},'enemy_explosion_colour':'private-buffer explosions use Colour-RAM $10 (level palette 17..24); player explosion direct glyphs $00 unchanged'}})
        report.update({'revision':'10a4','base':'Stage10a3 (user-confirmed gameplay 2026-10-22)','stage10a5':{'respawn':'no WAIT for formation; BLINK immediately at hit position, 276 frames from hit (21 explosion + 255), toggle when timer%20==0, no player fire, no new attacks (original $2C4E window)','resume_blink':'two-player turn resume keeps 150 frames with fire allowed; period now 20','fire_debounce':'release must be sampled on two consecutive frames before the next shot'}})
        report.update({'revision':'10a5','base':'Stage10a4 (user-confirmed respawn and fire 2026-10-23)','stage10a5':{'menu_fire':'menu arms after two consecutive all-released frames; fire re-arms after two released frames','highscore_fire':'joystick sampled once per frame; two released frames before fire leaves the table','first_level':'new game plays the level transition (animation and both transition sounds) before Get ready; two-player turn resume unchanged'}})
        out['build-report.json']=(json.dumps(report,indent=2)+'\n').encode()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for name,b in out.items():
            (output/name).parent.mkdir(parents=True,exist_ok=True);(output/name).write_bytes(b)
    print('Stable baselines unchanged. Nine SEQ assets, PRG and full D81 chains verified.')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.getenv('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_10a/stage10a5');p.add_argument('--zx0',default=os.getenv('ZX0'));a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    if not a.zx0:p.error('--zx0 required (ZX0 v2 compressor)')
    build(a.kickass,a.output,a.zx0)
