#!/usr/bin/env python3
"""Lossless RGB4 CSV -> VYCL v1; independently verify archived original ADF bytes."""
import csv,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def read_sources():
    rows=list(csv.DictReader((ROOT/'assets/original_color_level_mapping.csv').read_text().splitlines()))
    palettes=list(csv.DictReader((ROOT/'assets/original_color_palettes_rgb4.csv').read_text().splitlines()))
    if any(set(r)!=set(['level','palette_id','color_offset_hex']) for r in rows):raise ValueError('Unexpected level CSV columns')
    if any(set(r)!=set(['palette_id']+[f'rgb4_{i}' for i in range(9)]) for r in palettes):raise ValueError('Unexpected palette CSV columns')
    if len(rows)!=100 or [int(r['level']) for r in rows]!=list(range(1,101)):raise ValueError('100 ordered levels required')
    if len(palettes)!=20 or [int(r['palette_id']) for r in palettes]!=list(range(20)):raise ValueError('20 ordered palettes required')
    ids=[int(r['palette_id']) for r in rows]
    if any(not 0<=i<20 for i in ids):raise ValueError('Palette index out of range')
    if any(int(r['color_offset_hex'],16)!=2+18*i for r,i in zip(rows,ids)):raise ValueError('Color offset mismatch')
    words=[[int(r[f'rgb4_{i}'],16) for i in range(9)] for r in palettes]
    if any(not 0<=w<=0xfff for row in words for w in row):raise ValueError('RGB4 out of range')
    return ids,words
HEADER=struct.pack('<4sHHHHHH',b'VYCL',1,100,20,9,476,0)
def encode(ids,words):
    if len(ids)!=100 or any(type(i)!=int or not 0<=i<20 for i in ids):raise ValueError('Invalid levels')
    if len(words)!=20 or any(len(row)!=9 for row in words) or any(type(w)!=int or not 0<=w<=4095 for row in words for w in row):raise ValueError('Invalid palettes')
    payload=bytes(ids)+struct.pack('<180H',*(w for row in words for w in row))
    return HEADER[:14]+struct.pack('<H',sum(payload)&65535)+payload


def decode(data):
    if len(data)!=476 or data[:14]!=HEADER[:14]:raise ValueError('Invalid VYCL header/length')
    if sum(data[16:])&65535!=struct.unpack_from('<H',data,14)[0]:raise ValueError('VYCL checksum')
    ids=list(data[16:116]);flat=struct.unpack_from('<180H',data,116)
    words=[list(flat[i:i+9]) for i in range(0,180,9)]
    if encode(ids,words)!=data:raise ValueError('Invalid VYCL values')
    return ids,words
def build(output=ROOT/'assets/stage5c'):
    ids,words=read_sources();data=encode(ids,words);assert decode(data)==(ids,words)
    from extract_stage5b_graphics import ofs_files,SOURCE_HASHES
    adf=(ROOT/'assets/stage5b/original_sources/VYPER.ADF').read_bytes()
    if sha(adf)!=SOURCE_HASHES['VYPER.ADF']:raise ValueError('Original ADF hash mismatch')
    waves=ofs_files(adf);color=waves['Color'];level=waves['Level']
    original=struct.pack('>H',100)+struct.pack('>180H',*(w for row in words for w in row))
    if color!=original or len(level)!=11400:raise ValueError('Original Color differs')
    if ids!=[struct.unpack_from('>H',level,114*i+0x4c)[0] for i in range(100)]:raise ValueError('Original Level mapping differs')
    report={'format':'VYCL v1','bytes':len(data),'sum16':sum(data)&65535,'sha256':sha(data),
        'sources':{n:sha((ROOT/'assets'/n).read_bytes()) for n in ['original_color_level_mapping.csv','original_color_palettes_rgb4.csv']},
        'original_ADF_sha256':sha(adf),'original_Color_sha256':sha(color),'original_Level_sha256':sha(level),
        'original_binary_comparison':'362 Color bytes and all100 Level+$4C fields identical',
        'original_code_usage_proven':False,'enemy_mapping':'visible plane colour c (0..7) -> NCM index c+1 -> RGB4 word c; word8 preserved, not used by 3-plane enemies',
        'levels':[{'level':i+1,'palette_id':p,'rgb4':[f'{w:03X}' for w in words[p]]} for i,p in enumerate(ids)]}
    output.mkdir(parents=True,exist_ok=True);(output/'VYCL.DAT').write_bytes(data)
    (output/'palette-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return data,report
if __name__=='__main__':
    data,report=build();print(json.dumps({k:report[k] for k in ['bytes','sum16','sha256','original_binary_comparison']}))
