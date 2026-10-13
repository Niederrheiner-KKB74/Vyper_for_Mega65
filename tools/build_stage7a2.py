#!/usr/bin/env python3
"""Stage7a2 full-game starfield integration; protect all stable baselines."""
import argparse,json,os,shutil,struct,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import build_stage5d1a as ENGINE
import convert_stage5d1_title as TITLE
import convert_stage6b1_menu as MENU
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[f'stage7a2{s}.asm' for s in ENGINE.COMPONENTS+['_title','_entry_projection','_cycling','_integration','_banking','_stars']]
STABLES={'stage7a1-stable':'9ebbcabd2a792661b0da354f2716abb7772d74a6','stage6b1-stable':'31ae0bd4bcdd79f3217126f902cf9978907cb48d','stage5d1a-stable':'39890c0095fab55b2ea71f95cccf59a3419848c6','stage6a2-stable':'24559e46c4f237492bc4e03439c86ea6c402a0b0'}
def protect_stable():
    for ref,commit in STABLES.items():
        if subprocess.check_output(['git','rev-parse',ref+'^{}'],cwd=ROOT,text=True).strip()!=commit:raise ValueError('Stable ref changed '+ref)
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines()
        # Other baseline branch files need not be imported. Existing ones must match.
        for p in paths:
            local=ROOT/p
            if local.exists() and local.read_bytes()!=subprocess.check_output(['git','show',commit+':'+p],cwd=ROOT):raise ValueError('Stable file modified '+p)
    ENGINE.protect_stable()
def descriptor(name,src,dst,n,command=0):
    return f'{name}:\n    .byte $80,${src>>20:02x},$81,${dst>>20:02x},$0a,0,{command}\n    .word ${n:04x}\n    .word ${src&65535:04x}\n    .byte ${(src>>16)&15:02x}\n    .word ${dst&65535:04x}\n    .byte ${(dst>>16)&15:02x}\n    .word 0\n'
def assemble(w,jar,src,out):
    run=subprocess.run(['java','-jar',str(jar),src,'-o',out,'-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(run.stdout,end='');run.check_returncode();return run.stdout
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_7a2'):raise ValueError('Protected release target')
    protect_stable();PLAYER.verify_player_assets()
    with tempfile.TemporaryDirectory(prefix='vyper-7a2-') as t:
        w=Path(t);ti,title=TITLE.build(w);menu=MENU.convert(w)
        import convert_stage7a2_stars as STAR
        star=STAR.convert(w)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                p=w/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',w/'explosion_assets');shutil.copytree(ROOT/'assets/player',w/'player_assets')
        for name in SOURCES+['stage7a2_menu.asm']:shutil.copyfile(ROOT/'src/engine'/name,w/name)
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
        assemble(w,jar,'stage7a2_menu.asm','MENU_OVERLAY.PRG')
        overlay=(w/'MENU_OVERLAY.PRG').read_bytes();assert overlay[:2]==b'\x00\x70' and len(overlay)==12290
        body=rgb+tiles+screens+overlay[2:]
        header=struct.pack('<4sHHIIIIHHI',b'VYMN',2,32,len(tiles),screen_offset,overlay_offset,file_len,sum(body)&65535,0,0)
        assert len(header)==32
        mn=header+body;assert len(mn)==file_len;constants['M_FILE_SUM']=sum(mn)&65535;layout();(w/'menu_header.bin').write_bytes(header)
        jobs=[('header_copy',0x40000,0x6900,32),('asset_header',0x08010000,0x6900,32),('asset_save0',0x40000,0x08010000,0xff00),('asset_save1',0x4ff00,0x0801ff00,file_len-0xff00),('engine_save',0x7000,0x08001000,0x3000),('engine_restore',0x08001000,0x7000,0x3000),('colour_save',0x5f100,0x08004000,2640),('colour_restore',0x08004000,0x5f100,2640),('overlay_load',constants['M_OVERLAY'],0x7000,0x3000),('atlas_low',0x08010050,0x12800,832*64),('atlas_high',0x08010050+832*64,0x5c500,len(tiles)-832*64),('font_load',constants['M_FONT'],0x4000,2048)]
        (w/'menu_dma.inc').write_text(''.join(descriptor(*j) for j in jobs))
        data={n:(ROOT/path).read_bytes() for n,path in [('VYLV.DAT','assets/VYLV.DAT'),('VYGR.DAT','assets/stage5b/VYGR.DAT'),('VYCL.DAT','assets/stage5c/VYCL.DAT')]}
        data.update({'VYTI.DAT':ti,'VYMN.DAT':mn})
        for name,b in data.items():(w/name).write_bytes(b)
        asm=assemble(w,jar,'stage7a2.asm','STAGE7A2.PRG');prg=(w/'STAGE7A2.PRG').read_bytes()
        actual_restore=int(re.search(r'\.label t_restore_video=\$([0-9a-f]+)',(w/'stage7a2.sym').read_text())[1],16)
        actual_seq=int(re.search(r'\.label load_file=\$([0-9a-f]+)',(w/'stage7a2.sym').read_text())[1],16)
        if actual_seq!=seq:raise ValueError('Menu SEQ gate does not match assembled loader')
        if actual_restore!=restore:raise ValueError('Menu BASIC-restore gate does not match assembled title routine')
        entries=[('STAGE7A2',prg,0x82)]+[(n,b,0x81) for n,b in data.items()]
        disk=bytearray(BASE.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER STAGE7A2'.ljust(16,b'\xa0');disk=bytes(disk)
        files=BASE.verify_disk(disk,entries)
        report={'stage':'7a2','issue':51,'stable':False,'starfield':star,'stable_bases':STABLES,'starfield_source_commit':'ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a','runtime_star_debug':False,'speed_API':'mode0 normal; all nonzero modes rejected until later transition implementation','menu':menu,'title':title,'menu_DAT':{'bytes':len(mn),'sum16':sum(mn)&65535,'header':header.hex(),'offsets':constants},'files':files,'xemu':'NOT_RUN; user acceptance required','DMA':jobs}
        out={'STAGE7A2.PRG':prg,'STAGE7A2.sym':(w/'stage7a2.sym').read_bytes(),'MENU_OVERLAY.PRG':overlay,'MENU_OVERLAY.sym':(w/'stage7a2_menu.sym').read_bytes(),'VYPER_STAGE7A2.d81':disk,**data,'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(asm[asm.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in SOURCES+['stage7a2_menu.asm','menu_layout.inc','menu_dma.inc','menu_header.bin','menu_palette.inc','menu_assets.inc','menu_fcm.bin','menu_screens.bin','menu_font.bin','digit_background.bin','original_menu_indices.bin','title_layout.inc','title_screen.bin','title_fcm_unique.bin','color_cycle.inc','stars_layout.inc']:out[name]=(w/name).read_bytes()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for name,b in out.items():(output/name).write_bytes(b)
    print('Both stable bases unchanged. Five SEQ assets, PRG and full D81 chains verified.')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.getenv('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_7a2');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
