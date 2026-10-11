#!/usr/bin/env python3
"""Exact original RGB4/PNG -> VIC-IV FCM tiles. Never quantize or invent pixels."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def palette(path):
    rows=[]
    for line in path.read_text().splitlines():
        m=re.fullmatch(r'COLOR(\d{2}): \$([0-9A-Fa-f]{3})  RGB\((\d+),(\d+),(\d+)\)',line)
        if not m:raise ValueError('Unexpected original palette line: '+line)
        i=int(m[1]);w=int(m[2],16);rgb=tuple(int(m[k]) for k in (3,4,5))
        if i!=len(rows) or rgb!=tuple(((w>>s)&15)*17 for s in (8,4,0)):raise ValueError('Palette index/RGB4 mismatch')
        rows.append({'index':i,'rgb4':w,'rgb':rgb})
    if len(rows)!=33:raise ValueError('Expected exactly33 original entries')
    return rows

def convert(image_path,palette_path,output):
    from PIL import Image
    rows=palette(palette_path);lookup={}
    for row in rows:lookup.setdefault(row['rgb'],[]).append(row['index'])
    with Image.open(image_path) as im:
        if im.format!='PNG' or im.size!=(352,240):raise ValueError('Original PNG must be352x240')
        mode=im.mode;rgba=list(im.convert('RGBA').getdata())
        if any(a!=255 for r,g,b,a in rgba):raise ValueError('Transparency requires explicit source interpretation; no implicit alpha discard')
        rgb=[p[:3] for p in rgba]
        missing=sorted(set(rgb)-set(lookup))
        if missing:raise ValueError('PNG colours absent from original palette: '+repr(missing))
        original=list(im.getdata()) if mode=='P' else None
        pixels=[];remapped=0
        for j,c in enumerate(rgb):
            options=lookup[c];idx=original[j] if original is not None else None
            if idx in options:pixels.append(idx)
            else:pixels.append(options[0]);remapped+=int(original is not None)
        # 44x30 distinct8x8 tiles, linear rows within each tile; no flip/resize.
        tiles=bytes(pixels[(ty*8+y)*352+tx*8+x] for ty in range(30) for tx in range(44) for y in range(8) for x in range(8))
        restored=[None]*(352*240)
        for ty in range(30):
            for tx in range(44):
                for y in range(8):
                    for x in range(8):restored[(ty*8+y)*352+tx*8+x]=rows[tiles[((ty*44+tx)*8+y)*8+x]]['rgb']
        if restored!=rgb:raise ValueError('Exact pixel roundtrip failed')
        pal=bytes(c for row in rows for c in row['rgb'])
        payload=pal+tiles
        # v1: magic,version,width,height,palettecount,tilebytes,payload sum16.
        header=struct.pack('<4sHHHHIH',b'VYTI',1,352,240,33,len(tiles),sum(payload)&65535)
        data=header+payload
        output.mkdir(parents=True,exist_ok=True)
        (output/'VYTI.DAT').write_bytes(data);(output/'title_fcm.bin').write_bytes(tiles)
        for c,name in enumerate('rgb'):(output/f'title_palette_{name}.bin').write_bytes(bytes(row['rgb'][c] for row in rows))
        report={'source_png_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'source_palette_sha256':hashlib.sha256(palette_path.read_bytes()).hexdigest(),
            'size':[352,240],'mode':mode,'source_unique_RGB_colours':len(set(rgb)),'original_palette_entries':33,
            'duplicate_RGB_indices':[v for v in lookup.values() if len(v)>1],'exact_RGB_roundtrip_pixels':len(rgb),
            'PNG_indices_preserved_when_matching_named_original_index':mode=='P','remapped_PNG_indices_pixels':remapped,
            'RGB_input_index_policy':'lowest exactly matching original index; duplicate RGB does not prove original index identity',
            'tile_grid':[44,30],'tile_bytes':len(tiles),'format':'VYTI v1;18-byte little-endian header,99 RGB bytes,84480 tile bytes',
            'VYTI_bytes':len(data),'VYTI_sha256':hashlib.sha256(data).hexdigest(),'xemu':'NOT_RUN'}
        (output/'conversion-report.json').write_text(json.dumps(report,indent=2)+'\n')
        return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--png',type=Path,default=ROOT/'assets/stage5d0/original_sources/vyper_palette_candidate_9a50.png')
    p.add_argument('--palette',type=Path,default=ROOT/'assets/stage5d0/original_sources/vyper_title_palette.txt')
    p.add_argument('--output',type=Path,default=ROOT/'assets/stage5d0')
    p.add_argument('--check-palette-only',action='store_true');a=p.parse_args()
    if a.check_palette_only:
        rows=palette(a.palette);print(json.dumps({'entries':len(rows),'unique_RGB_colours':len(set(r['rgb'] for r in rows)),'duplicate_black_indices':[r['index'] for r in rows if r['rgb']==(0,0,0)]}));return
    if not a.png.is_file():p.error('Original PNG file missing; upload it as a file attachment. No substitute image is generated.')
    print(json.dumps(convert(a.png,a.palette,a.output),indent=2))
if __name__=='__main__':main()
