#!/usr/bin/env python3
"""Stage8b original Amiga PCM integration; preserve main/Stage7b5b and historical assets."""
import argparse,json,os,shutil,struct,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import build_stage5d1a as ENGINE
import convert_stage5d1_title as TITLE
import convert_stage6b1_menu as MENU
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[f'stage8b{s}.asm' for s in ENGINE.COMPONENTS+['_title','_entry_projection','_cycling','_integration','_banking','_stars','_transition','_selection','_fire','_fire_loader','_motion','_audio_gate','_audio_loader']]
STABLES={'2954dc57418f3898b8f958a9d15d79a57b2dd6bb':'2954dc57418f3898b8f958a9d15d79a57b2dd6bb','bd63682fa37df2853338b499f1210ec9dd2f56dc':'bd63682fa37df2853338b499f1210ec9dd2f56dc','a41e92ab8e4994a0a3288d60d63984d8593c8332':'a41e92ab8e4994a0a3288d60d63984d8593c8332','ec7a512bf913e522e5aaadfd57c9c4e7bb019bef':'ec7a512bf913e522e5aaadfd57c9c4e7bb019bef','stage7b1-stable':'5d9c4f563f9fd3de7f5786b623791b7fc26e79e7','stage7a2-stable':'b4cc1f7f4f2250bb69664ba15613350942e29d9c','stage7a1-stable':'9ebbcabd2a792661b0da354f2716abb7772d74a6','stage6b1-stable':'31ae0bd4bcdd79f3217126f902cf9978907cb48d','stage5d1a-stable':'39890c0095fab55b2ea71f95cccf59a3419848c6','stage6a2-stable':'24559e46c4f237492bc4e03439c86ea6c402a0b0'}
def protect_stable():
    for ref,commit in STABLES.items():
        if subprocess.check_output(['git','rev-parse',ref+'^{}'],cwd=ROOT,text=True).strip()!=commit:raise ValueError('Stable ref changed '+ref)
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines()
        # Other baseline branch files need not be imported. Existing ones must match.
        for p in paths:
            local=ROOT/p
            if local.exists() and local.read_bytes()!=subprocess.check_output(['git','show',commit+':'+p],cwd=ROOT):raise ValueError('Stable file modified '+p)
    ENGINE.protect_stable()
    for name in subprocess.check_output(['git','ls-tree','-r','--name-only','f7350d6','--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines():
        if (ROOT/name).read_bytes()!=subprocess.check_output(['git','show','f7350d6:'+name],cwd=ROOT):raise ValueError('Main baseline modified '+name)
def descriptor(name,src,dst,n,command=0):
    return f'{name}:\n    .byte $80,${src>>20:02x},$81,${dst>>20:02x},$0a,0,{command}\n    .word ${n:04x}\n    .word ${src&65535:04x}\n    .byte ${(src>>16)&15:02x}\n    .word ${dst&65535:04x}\n    .byte ${(dst>>16)&15:02x}\n    .word 0\n'
def assemble(w,jar,src,out):
    run=subprocess.run(['java','-jar',str(jar),src,'-o',out,'-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(run.stdout,end='');run.check_returncode();return run.stdout
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_8b'):raise ValueError('Protected release target')
    protect_stable();PLAYER.verify_player_assets()
    with tempfile.TemporaryDirectory(prefix='vyper-8b-') as t:
        w=Path(t);ti,title=TITLE.build(w);menu=MENU.convert(w)
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
        for name in SOURCES+['stage8b_menu.asm']:shutil.copyfile(ROOT/'src/engine'/name,w/name)
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
        assemble(w,jar,'stage8b_menu.asm','MENU_OVERLAY.PRG')
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
            if b!=(ROOT/'releases/stage_7b5a'/name).read_bytes():raise ValueError('Existing DAT changed '+name)
            (w/name).write_bytes(b)
        import convert_stage8b_audio as AUDIO
        audio_meta,pcm,audio_types=AUDIO.prepare(w)
        base_symbols=(ROOT/'releases/stage_7b5b/STAGE7B5B.sym').read_text()
        def addr(name):return int(re.search(r'\.label '+name+r'=\$([0-9a-f]+)',base_symbols)[1],16)
        (w/'audio_engine.inc').write_text(''.join(f'.label {a}=${addr(b):x}\n' for a,b in [('anim_pause_address','anim_paused'),('shots_x_address','p_xpos'),('motion_xhi_address','xhi'),('shooter_address','p_source_enemy')]))
        shutil.copyfile(ROOT/'src/engine/stage8b_audio_core.asm',w/'stage8b_audio_core.asm')
        assemble(w,jar,'stage8b_audio_core.asm','AUDIO_CORE.PRG')
        audio=AUDIO.package(w,audio_meta,pcm,audio_types)
        data['VYSO.DAT']=(w/'VYSO.DAT').read_bytes()
        asm=assemble(w,jar,'stage8b.asm' ,'STAGE8B.PRG');prg=(w/'STAGE8B.PRG').read_bytes()
        actual_restore=int(re.search(r'\.label t_restore_video=\$([0-9a-f]+)',(w/'stage8b.sym').read_text())[1],16)
        actual_seq=int(re.search(r'\.label load_file=\$([0-9a-f]+)',(w/'stage8b.sym').read_text())[1],16)
        actual_symbols=(w/'stage8b.sym').read_text()
        for n in ('anim_paused','p_xpos','xhi','p_source_enemy'):
            if int(re.search(r'\.label '+n+r'=\$([0-9a-f]+)',actual_symbols)[1],16)!=addr(n):raise ValueError('Audio engine ABI moved '+n)
        if actual_seq!=seq:raise ValueError('Menu SEQ gate does not match assembled loader')
        if actual_restore!=restore:raise ValueError('Menu BASIC-restore gate does not match assembled title routine')
        entries=[('STAGE8B',prg,0x82)]+[(n,b,0x81) for n,b in data.items()]
        disk=bytearray(BASE.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER STAGE8B'.ljust(16,b'\xa0');disk=bytes(disk)
        files=BASE.verify_disk(disk,entries)
        report={'stage':'8b','fire_events':fire,'issue':73,'stable':False,'starfield':star,'protected_bases':STABLES,'starfield_source_commit':'ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a','runtime_star_debug':False,'speed_API':'mode0 normal8/4/2; mode1 eightfold1/2/4 pixels per frame','transition':{'accelerated_frames':50,'ring_frames':3,'rings':13,'fill_frames':39,'black_frames':39,'initialization_frames':1,'bitmap':[0x18000,0x1ddbf],'approximation':'concentric8px bands, spatial outer-to-inner blue/yellow/red/darkblue; screenshot-derived geometry/RGB and3frames/ring approximation'},'projectiles':{'colour':'white/red/grey bank2/indices10,13,16','visual_logical_pixels':[3,7],'hitboxes_preserved':{'player':[1,4],'enemy':[3,4]},'original_conversion':shot['implementation'],'enemy':'Original3x7 white/red/grey; player reflected vertically'},'menu':menu,'title':title,'menu_DAT':{'bytes':len(mn),'sum16':sum(mn)&65535,'header':header.hex(),'offsets':constants},'files':files,'xemu':'NOT_RUN; user acceptance required','DMA':jobs}
        report['audio']=audio
        report['motion']={'player_step_test_default':2,'native_player_update_Hz':'unproven','enemy':'original16.16, level DY, parity spread0..19,45degree cap','signed_coordinates':True,'extra_state':[0x1f9a,0x1fcc],'legacy_T':'isolated unchanged8.8 helper'}
        report['attack_selection']={'interval_frames':30,'max_ATTACK':3,'eligible':'live FORMATION plus phase3','sampling':'power-of-two rejection; due timer retained on rejection/no actor'}
        report['projectiles'].update({'enemy_limit':6,'player_limit':2,'cooldown_frames':None,'normal_shot_decision':'original ENTRY countdown / ATTACK thresholds','state_range':[0x1f00,0x1f77],'eligible_list':[0x1f80,0x1f99],'per_enemy_limit':None,'ownership':'original shooter ID retained diagnostically; global slots2..7 only','snapshot':[0x1b60,0x1b8a],'base_graphics_byte_identical':True})
        out={'STAGE8B.PRG':prg,'STAGE8B.sym':(w/'stage8b.sym').read_bytes(),'MENU_OVERLAY.PRG':overlay,'MENU_OVERLAY.sym':(w/'stage8b_menu.sym').read_bytes(),'VYPER_STAGE8B.d81':disk,**data,'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(asm[asm.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in SOURCES+['stage8b_audio_core.asm','AUDIO_CORE.PRG','stage8b_audio_core.sym','audio_constants.inc','audio_engine.inc','audio_events.inc','audio_samples.inc','audio_file.inc','audio_header.bin','audio-metadata.json','stage8b_menu.asm','menu_layout.inc','menu_dma.inc','menu_header.bin','menu_palette.inc','menu_assets.inc','menu_fcm.bin','menu_screens.bin','menu_font.bin','digit_background.bin','original_menu_indices.bin','title_layout.inc','title_screen.bin','title_fcm_unique.bin','color_cycle.inc','stars_layout.inc','projectile_sprites.bin','fire_layout.inc','fire_constants.inc','fire-parameters.json']:out[name]=(w/name).read_bytes()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for name,b in out.items():(output/name).write_bytes(b)
    print('Stable baselines unchanged. Seven SEQ assets, PRG and full D81 chains verified.')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.getenv('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_8b');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
