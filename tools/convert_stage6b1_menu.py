#!/usr/bin/env python3
"""Reproduce Stage6a2 raster/animations and original descriptor font for integration."""
import json,struct,tempfile
from pathlib import Path
import convert_stage6a1_menu as MENU
import analyze_stage5d0_copper as COP
ROOT=Path(__file__).resolve().parents[1]
def glyph_address(i):
    return (0x12800//64+i) if i<832 else (0x5c500//64+i-832)
def convert(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        old=Path(t)
        import shutil
        for p in (ROOT/'assets/stage6a1').iterdir():shutil.copyfile(p,old/p.name)
        report=json.loads((old/'conversion-report.json').read_text())
        if report['source_uss_sha256']!=MENU.sha(MENU.SOURCE.read_bytes()) or report['VYGR_sha256']!=MENU.sha(MENU.VYGR.read_bytes()):raise ValueError('Stable original menu sources changed')
        ram=dict(COP.chunks(MENU.SOURCE.read_bytes()))[b'CRAM']
        rows={}
        for c in range(40):
            p=COP.be(ram,0x227fc+32*c,4)
            if p!=0x185d2+28*c:raise ValueError('Original menu font descriptor changed')
            rows[c]=bytes(ram[p+2*y] for y in range(8))
        font=bytearray(2048)
        for c in range(10):font[(48+c)*8:(49+c)*8]=rows[c]
        for c in range(26):
            for code in [1+c,65+c,97+c]:font[code*8:(code+1)*8]=rows[10+c]
        font[45*8:46*8]=rows[36]
        # Menu charset has no period. Keep the previously confirmed HUD punctuation.
        font[46*8:47*8]=bytes([0,0,0,0,0,0,0x10,0])
        tiles=[(old/'menu_fcm.bin').read_bytes()[i:i+64] for i in range(0,report['tile_bytes'],64)]
        lookup={b:i for i,b in enumerate(tiles)}
        def intern(b):
            if b not in lookup:lookup[b]=len(tiles);tiles.append(b)
            return glyph_address(lookup[b])
        raw=(old/'original_menu_indices.bin').read_bytes()
        bg=bytearray(raw[(144+y)*320+88+x] for y in range(16) for x in range(24))
        for y in range(2,9):bg[y*24+6:y*24+24]=bytes(18)
        digit_bg=bytes(bg[(r*8+y)*24+c*8+x] for r in range(2) for c in range(3) for y in range(8) for x in range(8))
        (out/'digit_background.bin').write_bytes(digit_bg)
        screens=[struct.pack('<1000H',*[glyph_address(v-0x1000) for v in struct.unpack('<1000H',(old/'menu_screen.bin').read_bytes())])]
        for message in ['2 PLAYER UNAVAILABLE','HIGH SCORES UNAVAILABLE']:
            im=bytearray(raw)
            im[128*320:196*320]=bytes(68*320)
            for text,y in [(message,146),('PRESS FIRE OR RETURN',172)]:
                widths=[8 if c in 'GK' else 4 if c in 'CR' else 6 for c in text]
                x=(320-sum(widths))//2
                for char,width in zip(text,widths):
                    f=font[ord(char)*8:ord(char)*8+8]
                    for yy in range(7):
                        for xx in range(width):
                            if f[yy]&(128>>xx):im[(y+yy)*320+x+xx]=1
                    x+=width
            screens.append(struct.pack('<1000H',*[intern(bytes(im[(ty*8+y)*320+tx*8+x] for y in range(8) for x in range(8))) for ty in range(25) for tx in range(40)]))
        if len(tiles)>1068:raise ValueError(f'Menu FCM atlas exceeds released chip RAM: {len(tiles)} tiles')
        table=(old/'menu_assets.inc').read_text().split('*=$8000',1)[1]
        table='*=$8000'+table
        import re
        table=re.sub(r'\$[1-4][0-9a-f]{3}',lambda m:f'${glyph_address(int(m[0][1:],16)-0x1000):04x}' if 0x1000<=int(m[0][1:],16)<0x1000+984 else m[0],table)
        # Original actors destination is now the phase-private CPU-visible screen $9000.
        for a in report['actors']:a['screen_address']+=0x2000
        table=re.sub(r'menu_dst_hi:.*', 'menu_dst_hi: .byte '+','.join(str(a['screen_address']>>8) for a in report['actors']),table)
        (out/'menu_assets.inc').write_text(table)
        for name,data in [('menu_fcm.bin',b''.join(tiles)),('menu_font.bin',bytes(font)),('menu_screens.bin',b''.join(screens)),('original_menu_indices.bin',raw)]: (out/name).write_bytes(data)
        report.update({'issue':47,'font_descriptor_base':'$227FC','font_bitplanes_base':'$185D2','font_glyph_count':40,'font_period':'retained Stage5d1a punctuation; no period in menu alphabet','unique_FCM_tiles':len(tiles),'tile_bytes':len(tiles)*64,'atlas_low':['$12800','$1F7FF'],'atlas_high_start':'$5C500','CPU_overlay':['$7000','$9FFF'],'engine_base':'stage5d1a-stable','menu_base':'stage6a2-stable'})
        (out/'conversion-report.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
