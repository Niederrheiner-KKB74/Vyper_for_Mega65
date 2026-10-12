#!/usr/bin/env python3
"""Exact USS menu raster plus 32 independently animated original VYGR types."""
import argparse,hashlib,json,struct
from pathlib import Path
from PIL import Image
import analyze_stage5d0_copper as COP
import extract_stage5b_graphics as GRAPHICS
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/stage5b/original_sources/Vyper_Startscreen.uss'
VYGR=ROOT/'assets/stage5b/VYGR.DAT'
W,H=320,200
BASES=[0x27770,0x29bb0,0x2bff0,0x2e430]
def sha(b):return hashlib.sha256(b).hexdigest()
def convert(out):
    uss=SOURCE.read_bytes();gr=VYGR.read_bytes()
    if sha(uss)!=GRAPHICS.SOURCE_HASHES[SOURCE.name]:raise ValueError('Original USS changed')
    ch=dict(COP.chunks(uss));ram=ch[b'CRAM'];chip=ch[b'CHIP'];slow=ch[b'BRAM']
    # Compact WinUAE CHIP save: colour registers begin at $E4.
    pal=[COP.be(chip,0xe4+2*i) for i in range(32)]
    if any(w>0xfff for w in pal):raise ValueError('Expected OCS RGB4 palette')
    events=COP.copper(ram,COP.be(chip,0x88,4))['instructions']
    final={int(e['register'],16):int(e['value'],16) for e in events if 'register' in e}
    for r,v in final.items():
        if 0x180<=r<=0x1be and pal[(r-0x180)//2]!=v:raise ValueError('Saved palette differs from last COP2 write')
    for i,p in enumerate(BASES):
        if (final[0xe0+4*i]<<16|final[0xe2+4*i])!=p:raise ValueError('Unexpected original bitplane origin')
    if final[0x100]!=0x200 or not any(e.get('value')=='0x4200' for e in events):raise ValueError('Original 4-plane display phase missing')
    raw=bytes(sum(((ram[p+y*40+x//8]>>(7-x%8))&1)<<i for i,p in enumerate(BASES)) for y in range(H) for x in range(W))
    types=GRAPHICS.graphics_types(gr);matches={}
    for t in types:
        for j,f in enumerate(t['frames']):
            pixels=bytes(v-1 if v else 0 for b in f for v in (b&15,b>>4))
            anchors=[(i%16,i//16,v) for i,v in enumerate(pixels) if v][:12]
            if not anchors:continue
            for y in range(112):
                for x in range(W-15):
                    if not all(raw[(y+dy)*W+x+dx]==v for dx,dy,v in anchors):continue
                    if all(raw[(y+dy)*W+x:(y+dy)*W+x+16]==pixels[dy*16:dy*16+16] for dy in range(16)):
                        matches.setdefault((x,y),{}).setdefault(t['type'],[]).append(j)
    if len(matches)!=32 or any(len(t)!=1 for t in matches.values()):raise ValueError('32 uniquely identified original positions required')
    actors=[]
    for (x,y),ts in sorted(matches.items(),key=lambda item:(item[0][1],item[0][0])):
        typ,phases=next(iter(ts.items()));t=types[typ-1]
        if x%8 or y%8!=4:raise ValueError('Review menu tile alignment')
        slot=len(actors);obj=0x2404a+146*slot
        static_base=COP.be(ram,0x1ace2+(typ-1)*18+8,4)
        current=(COP.be(ram,obj+0x14,4)-static_base)//32
        period=COP.be(ram,obj+0x5a);delay=COP.be(ram,obj+0x58)
        if (COP.be(ram,obj+0x10),COP.be(ram,obj+0x12))!=(x,y+16):raise ValueError('Original actor geometry mismatch')
        if COP.be(ram,obj+0x54,4)!=static_base or COP.be(ram,obj+0x5e)!=t['frame_count']:raise ValueError('Original actor descriptor mismatch')
        if not 0<=current<t['frame_count'] or not 1<=delay<=period<=6:raise ValueError('Original animation state invalid')
        # The front raster can lag the prepared descriptor: keep a matching
        # visible phase, preferably current or previous, never invent a frame.
        initial=current if current in phases else ((current-1)%t['frame_count'] if (current-1)%t['frame_count'] in phases else phases[0])
        actors.append({'slot':slot,'type':typ,'x':x,'y':y,'frame_count':t['frame_count'],'initial_frame':initial,'identical_snapshot_frame_candidates':phases,'original_current_frame':current,'period_frames':period,'initial_delay':delay,'original_object':hex(obj)})
    # Extract original strings from SlowRAM; displayed raster proves wording/shape.
    needles=[b'- VYPER -',b'- bonus ship every %d waves -',b'- select option with joystick or keyboard -',b'initial level %03d',b'f1 start 1 player game',b'f2 start 2 player game',b'f3 View high Scores']
    texts=[]
    for b in needles:
        p=slow.find(b+b'\0')
        if p<0:raise ValueError('Original menu text not present')
        texts.append({'SlowRAM_offset':hex(p),'format':b.decode(),'display':(b.decode().replace('%d','3').replace('%03d','001')).upper()})
    glyphs=[];lookup={}
    def intern(b):
        if b not in lookup:lookup[b]=len(glyphs);glyphs.append(b)
        return 0x1000+lookup[b]
    initial=[intern(bytes(raw[(ty*8+y)*W+tx*8+x] for y in range(8) for x in range(8))) for ty in range(25) for tx in range(40)]
    occupied=set();table=[]
    for a in actors:
        tx=a['x']//8;ty=a['y']//8
        cells=[(ty+r)*40+tx+c for r in range(3) for c in range(2)]
        if occupied.intersection(cells):raise ValueError('Overlapping actor tile footprints')
        occupied.update(cells);a['screen_address']=0x7000+2*cells[0]
        block=bytearray(raw[(ty*8+y)*W+tx*8+x] for y in range(24) for x in range(16))
        for yy in range(4,20):block[yy*16:yy*16+16]=bytes(16)
        a['table_offset']=len(table)*2
        for f in types[a['type']-1]['frames']:
            current=bytearray(block)
            for yy in range(16):
                for xx in range(16):
                    v=(f[yy*8+xx//2]>>(4*(xx%2)))&15
                    if v:current[(yy+4)*16+xx]=v-1
            ids=[intern(bytes(current[(r*8+y)*16+c*8+x] for y in range(8) for x in range(8))) for r in range(3) for c in range(2)]
            table.extend(ids)
        start=a['table_offset']//2+12*a['initial_frame']//2
        if table[start:start+6]!=[initial[c] for c in cells]:raise ValueError('Initial original frame differs')
    tiles=b''.join(glyphs);rgb=bytes(((p>>s)&15)*17 for p in pal[:16]+[0]*17 for s in (8,4,0))
    payload=rgb+tiles;data=struct.pack('<4sHHHHIH',b'VYMN',1,W,H,33,len(tiles),sum(payload)&65535)+payload
    if len(data)>0x20000:raise ValueError('Menu asset exceeds $40000-$5FFFF')
    out.mkdir(parents=True,exist_ok=True)
    for n,b in [('VYMN.DAT',data),('menu_fcm.bin',tiles),('menu_screen.bin',struct.pack('<1000H',*initial)),('original_menu_indices.bin',raw)]: (out/n).write_bytes(b)
    inc=f'.const TITLE_SUM={sum(data)&65535}\n.const TITLE_BYTES={len(tiles)}\n.var titleData=LoadBinary("VYMN.DAT")\n.var menuScreen=LoadBinary("menu_screen.bin")\n'
    inc+='*=$8000 "32 actor FCM frame pointer tables"\nmenu_table:\n'
    inc+=''.join('    .word '+','.join(f'${v:04x}' for v in table[i:i+6])+'\n' for i in range(0,len(table),6))
    for name,values in [('menu_base_lo',[f'<(menu_table+{a["table_offset"]})' for a in actors]),('menu_base_hi',[f'>(menu_table+{a["table_offset"]})' for a in actors]),('menu_dst_lo',[str(a['screen_address']&255) for a in actors]),('menu_dst_hi',[str(a['screen_address']>>8) for a in actors]),('menu_counts',[str(a['frame_count']) for a in actors]),('menu_initial_frames',[str(a['initial_frame']) for a in actors]),('menu_periods',[str(a['period_frames']) for a in actors]),('menu_initial_delays',[str(a['initial_delay']) for a in actors])]:inc+=name+': .byte '+','.join(values)+'\n'
    inc+='menu_frames: .fill 32,0\nmenu_delays: .fill 32,0\nmenu_clock: .byte 0\n.if (* > $a000) { .error "Menu tables exceed private budget" }\n'
    (out/'menu_assets.inc').write_text(inc)
    im=Image.new('RGB',(W,H));im.putdata([tuple(((pal[v]>>s)&15)*17 for s in (8,4,0)) for v in raw]);im.save(out/'original_menu_reference.png')
    report={'issue':43,'source_uss_sha256':sha(uss),'VYGR_sha256':sha(gr),'size':[W,H],'Copper2':hex(COP.be(chip,0x88,4)),'planes':[hex(p) for p in BASES],'CHIP_palette_offset':'$E4','palette_RGB4':[f'${p:03X}' for p in pal[:16]],'actors':actors,'texts':texts,'palette_policy':'original menu COLOR0..15, not level palettes; unused loader-compatible entries16..32 zero','unique_FCM_tiles':len(glyphs),'tile_bytes':len(tiles),'VYMN_bytes':len(data),'VYMN_sha256':sha(data),'max_actors_per_scanline':max(sum(a['y']<=y<a['y']+16 for a in actors) for y in range(H)),'animation_frame_divider':1,'animation_period_note':'Original per-actor countdown and period, BRAM routine $D890-$D8C8; visible frame phase selected against raster where front/back states differ; no WinUAE runtime trace' ,'initial_64000_indices_exact':True,'renderer':'isolated CHR16/FCLRHI FCM 40x25; six pointers per actor; no RRB or gameplay imports','xemu':'NOT_RUN'}
    (out/'conversion-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'assets/stage6a1');a=p.parse_args();r=convert(a.output);print(json.dumps({k:r[k] for k in ['unique_FCM_tiles','tile_bytes','VYMN_bytes','max_actors_per_scanline']}))
