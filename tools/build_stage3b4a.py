#!/usr/bin/env python3
"""Reproduce Stage 3b-4a from stage3b3-stable; never modify stable releases."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
from build_stage3b2 import symbols
ROOT = Path(__file__).resolve().parents[1]
STABLE_SHA = '4cdb98d30cda81fc2f812fef28e1b7786387050de6c56899ebd5222508cec81d'
LABELS = {
0: ('HIGH SCORE', 0x0a), 1: ('0000000', 0x0a),
3: ('PLAYER 1', 0x0c), 4: ('0000000', 0x0d), 5: ('LEVEL 001', 0x0e),
14: ('PLAYER 2', 0x0f), 15: ('-------', 0x0f), 16: ('LEVEL ---', 0x0f),
18: ('P - PAUSE', 0x0d), 19: ('S - SOUND', 0x0d), 20: ('X - EXIT', 0x0d),
21: ('P/S NOT ACTIVE', 0x0f), 23: ('FORMATION 100', 0x0a), 24: ('ATTACK 115', 0x0a)}

def templates():
    screen, colours = bytearray(), bytearray()
    for row in range(25):
        text = [' ']*19
        text[0] = chr(128)
        text[18] = chr(130)
        tint = [0x0b]+[0x0a]*17+[0x0b]
        if row in (2, 6, 12, 17, 22):
            text = [chr(129)]*18+[chr(131)]
            tint = [0x0b]*19
        if row in LABELS:
            label, colour = LABELS[row]
            column = (19-len(label))//2
            text[column:column+len(label)] = label
            tint[column:column+len(label)] = [colour]*len(label)
        # GOTOX 480, alternative player palette, opaque mono text.
        words = [480]+[(ord(c)-64 if 'A' <= c <= 'Z' else ord(c)) | (0 if ord(c) in (130,131) else 0x8000) for c in text]+[0]
        attributes = [0x6010]+[(t << 8) for t in tint]+[0x0010]
        screen += b''.join(w.to_bytes(2,'little') for w in words)
        colours += b''.join(w.to_bytes(2,'little') for w in attributes)
    return bytes(screen),bytes(colours)

def template_source():
    screen, colours=templates()
    def data(b):
        return '\n'.join('    .byte '+','.join(f'${x:02x}' for x in b[i:i+21]) for i in range(0,len(b),21))
    return '''// Generated reproducibly by tools/build_stage3b4a.py. Do not hand-edit.
*=$5810 "HUD attributes and defaults"
.namespace hud {
attributes:
'''+data(colours)+'''
defaults:
    .dword 0,0
    .word 1,3
    .dword 0
    .word 0,0
    .byte 0
    .word 100,115
colours_r: .byte $ff,$88,$ff,$ee,$00,$55
colours_g: .byte $ff,$88,$ff,$00,$44,$55
colours_b: .byte $ff,$88,$00,$00,$ff,$55
life_top_rows: .byte 7,9
life_yoffsets: .byte $50,$70
life_positions_lo: .byte <490,<524,<558,<592
life_positions_hi: .byte >490,>524,>558,>592
attributes_end:
.if (attributes_end > $6000) { .error "HUD attributes overlap engine template" }
}
*=$7a00 "HUD static screen and font lookup"
.namespace hud {
template:
'''+data(screen)+'''
font_pairs:
'''+data(bytes(((0x80 if i & 0xc0 else 0)|(0x40 if i & 0x30 else 0)|(0x20 if i & 0x0c else 0)|(0x10 if i & 3 else 0)) for i in range(256)))+'''
prefix_lo: .fill 25, <(SCREEN_RAM+i*80)
prefix_hi: .fill 25, >(SCREEN_RAM+i*80)
colour_lo: .fill 25, <(COLOR_RAM+i*80)
colour_hi: .fill 25, >(COLOR_RAM+i*80)
template_lo: .fill 25, <(template+i*42)
template_hi: .fill 25, >(template+i*42)
attributes_lo: .fill 25, <(attributes+i*42)
attributes_hi: .fill 25, >(attributes+i*42)
data_end:
.if (data_end > $8000) { .error "HUD tables overlap NCM glyphs" }
}
'''

def verify_engine(prg,names):
    old=(ROOT/'releases/stage_3b3/STAGE3B3.PRG').read_bytes()
    if BASE.sha(old)!=STABLE_SHA or len(old)!=len(prg):
        raise ValueError('Stable baseline mismatch')
    expected=bytearray(old)
    def at(a): return a-0x2001+2
    old_names=symbols((ROOT/'releases/stage_3b3/STAGE3B3.sym').read_text())
    patches=[]
    # Precisely permit only the init/frame call targets, GOTOX transformation,
    # terminator operands, and scale restoration prologue. All other bytes fixed.
    for name,new in [('player_init','hud_init'),('v014_render_all','hud_render')]:
        target=old_names[name]
        call=b'\x20'+target.to_bytes(2,'little')
        low=at(0x2100); high=at(0x2330)
        sites=[i for i in range(low,high-2) if old[i:i+3]==call]
        if len(sites)!=1: raise ValueError(f'Expected unique {name} hook')
        i=sites[0]
        expected[i:i+3]=b'\x20'+names[new].to_bytes(2,'little')
        patches.append(hex(i-2+0x2001))
    i=at(old_names['v014_write_slot'])
    original=b'\xad'+old_names['v014_x'].to_bytes(2,'little')+b'\x20'+old_names['v012a_store'].to_bytes(2,'little')+b'\xc8\xad'+old_names['v014_ybits'].to_bytes(2,'little')+b'\x20'+old_names['v012a_store'].to_bytes(2,'little')
    sites=[n for n in range(i,i+40) if old[n:n+13]==original]
    if len(sites)!=1: raise ValueError('Unexpected writer sequence')
    i=sites[0]
    expected[i:i+13]=b'\x20'+names['hud_write_x'].to_bytes(2,'little')+b'\xea'*10
    patches.append(hex(i-2+0x2001))
    i=at(old_names['exit_to_basic'])
    if old[i:i+6]!=b'\x78\xa9\x00\x8d\x15\xd0': raise ValueError('Unexpected exit prologue')
    expected[i:i+6]=b'\x20'+names['hud_restore_scale'].to_bytes(2,'little')+b'\x78\xa9\x00'
    patches.append(hex(i-2+0x2001))
    i=at(old_names['v014_write_terminator'])
    for delta,value,original in [(13,0x80,0x40),(19,2,1)]:
        if old[i+delta]!=original: raise ValueError('Unexpected terminator operand')
        expected[i+delta]=value
    for lo,hi in ((0x3800,0x4000),(0x5810,0x6000),(0x7a00,0x8000)):
        if any(old[at(lo):at(hi)]): raise ValueError(f'HUD region not empty: {lo:x}')
        expected[at(lo):at(hi)]=prg[at(lo):at(hi)]
    if expected!=prg:
        differences=[hex(n-2+0x2001) for n,(a,b) in enumerate(zip(expected,prg)) if a!=b]
        raise ValueError('Unexpected baseline changes: '+','.join(differences[:30]))
    for name,address in old_names.items():
        if name in names and names[name]!=address:
            raise ValueError(f'Baseline label moved: {name}')
    table=at(old_names['v014_orbit_x'])
    if max(prg[table:table+256])+16>240:
        raise ValueError('An automatic pixie would cross the HUD/playfield boundary')
    return {'baseline_prg_sha256':STABLE_SHA,'hooks':patches,'changed_prg_bytes':sum(a!=b for a,b in zip(old,prg)),'unchanged':'loader, parser, motion, joystick, animation, glyph assets; exit except D05A restoration hook'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'))
    parser.add_argument('--output',type=Path,default=ROOT/'releases/stage_3b4a')
    args=parser.parse_args()
    if not args.kickass: parser.error('--kickass required')
    jar=Path(args.kickass).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256: raise ValueError('Expected official pinned KickAssembler 5.25')
    PLAYER.verify_player_assets()
    generated=template_source()
    (ROOT/'src/engine/stage3b4a_templates.asm').write_text(generated)
    sources=['stage3b4a.asm','stage3b4a_hud.asm','stage3b4a_templates.asm']
    with tempfile.TemporaryDirectory(prefix='vyper-3b4a-') as directory:
        work=Path(directory)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target=work/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(payload)
        (work/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES: shutil.copyfile(ROOT/'assets/player'/name,work/'player_assets'/name)
        for name in sources: shutil.copyfile(ROOT/'src/engine'/name,work/name)
        result=subprocess.run(['java','-jar',str(jar),'stage3b4a.asm','-o','STAGE3B4A.PRG','-symbolfile','-showmem'],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(result.stdout,end=''); result.check_returncode()
        prg=(work/'STAGE3B4A.PRG').read_bytes()
        sym=(work/'stage3b4a.sym').read_text()
        comparison=verify_engine(prg,symbols(sym))
        entries=[('STAGE3B4A',prg,0x82)]
        for name in ('VYLV.DAT','VYGR.DAT'):
            payload=(ROOT/'assets'/name).read_bytes()
            if BASE.sha(payload)!=BASE.DATA_SHA256[name]: raise ValueError('Original DAT mismatch')
            entries.append((name,payload,0x81))
        disk=bytearray(BASE.build_disk(entries)); header=39*40*256
        disk[header+4:header+20]=b'VYPER STAGE 3B4A'.ljust(16,b'\xa0'); disk=bytes(disk)
        report={'assembler':'KickAssembler 5.25','baseline':'stage3b3-stable','comparison':comparison,'files':BASE.verify_disk(disk,entries),'hud':{'mode':'H640, CHARXSCALE=60; logical X doubled','logical_playfield_right_exclusive':240,'physical_hud_x':480,'physical_hud_width':160,'life_columns':4,'life_rows':2,'life_logical_x':[245,262,279,296],'life_y':[58,75],'initial_lives':3,'player2_active':False},'runtime_xemu':'NOT RUN; user confirmation required'}
        outputs={'STAGE3B4A.PRG':prg,'VYPER_STAGE3B4A.d81':disk,'STAGE3B4A.sym':sym.encode(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in sources: outputs[name]=(ROOT/'src/engine'/name).read_bytes()
        outputs['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {name}\n' for name,b in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True,exist_ok=True)
        for name,b in outputs.items(): (args.output/name).write_bytes(b)
    print('Verified bounded engine patches, original data, HUD layout and D81.')
if __name__=='__main__': main()
