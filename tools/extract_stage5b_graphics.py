#!/usr/bin/env python3
"""Reproduce 38 original enemy types from bounded original descriptor pointers.
No Amiga level palette integration. Preserves all Stable input files.
"""
import argparse, hashlib, json, struct
from pathlib import Path
import analyze_stage3b2_data as DATA
ROOT=Path(__file__).resolve().parents[1]
SOURCE_HASHES={'Vyper_Memory_Dump.dat':'d74aea88fb4232e36caab80e51abc51f73d470a5b55a54f5cb010f1d910ddf8c','Vyper_Startscreen.uss':'d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916','VYPER.ADF':'b28cab911431aaf3e48fd3e9979159de7154f98538eeba191f52ac47ef9665e5'}
def sha(d):return hashlib.sha256(d).hexdigest()
def graphics_types(d):
    # Same v1 layout; only the allowed cardinality expands. Legacy parser untouched.
    if d[:4]!=b'VYGR' or struct.unpack_from('<HH',d,4)!=(1,38):raise ValueError('Expected v1/38')
    cursor=312;result=[]
    for i in range(38):
        off,n,res=struct.unpack_from('<IHH',d,8+i*8)
        if off!=cursor or res or not 1<=n<=12 or off+n*128>len(d):raise ValueError('Invalid graphics directory')
        result.append({'type':i+1,'offset':off,'frame_count':n,'frames':[d[off+j*128:off+(j+1)*128] for j in range(n)]})
        cursor+=128*n
    if cursor!=len(d):raise ValueError('Trailing data')
    return result

def ofs_files(adf):
    """Read original OFS directories and selected Wave files, with chain bounds/checksums."""
    def block(n):
        if not 0<n<1760:raise ValueError('ADF block out of bounds')
        b=adf[n*512:(n+1)*512]
        if sum(struct.unpack('>128I',b))&0xffffffff:raise ValueError('ADF checksum')
        return b
    out={};visited=set()
    def walk(n,path=''):
        if n in visited:raise ValueError('Directory cycle')
        visited.add(n);b=block(n);w=struct.unpack('>128I',b);name=b[433:433+b[432]].decode('latin1');path=path+'/'+name
        if w[127] in (1,2):
            for q in w[6:78]:
                chain=set()
                while q:
                    if q in chain:raise ValueError('Hash chain cycle')
                    chain.add(q);walk(q,path);q=struct.unpack_from('>I',block(q),496)[0]
        elif '/Wave/' in path:
            data=bytearray();q=w[4];seen=set();seq=1
            while q:
                if q in seen:raise ValueError('File cycle')
                seen.add(q);r=block(q);v=struct.unpack('>6I',r[:24])
                if v[0]!=8 or v[1]!=n or v[2]!=seq or v[3]>488:raise ValueError('OFS data header')
                data+=r[24:24+v[3]];q=v[4];seq+=1
            if len(data)!=w[81]:raise ValueError('OFS size')
            out[name]=bytes(data)
    if adf[:4]!=b'DOS\0':raise ValueError('Expected original OFS')
    walk(880);return out

def convert(planes,mask,historical=False):
    pixels=[]
    for y in range(16):
        for x in range(16):
            bit=7-x%8;b=2*y+x//8
            colour=sum(((p[b]>>bit)&1)<<k for k,p in enumerate(planes))
            pixels.append(colour+1 if mask[b]&(1<<bit) else 0)
    return bytes(pixels[i]|pixels[i+1]<<4 for i in range(0,256,2))

def extract(source=ROOT/'assets/stage5b/original_sources',output=ROOT/'assets/stage5b'):
    inputs={n:(source/n).read_bytes() for n in SOURCE_HASHES}
    for n,d in inputs.items():
        if sha(d)!=SOURCE_HASHES[n]:raise ValueError('Original source checksum: '+n)
    m=inputs['Vyper_Memory_Dump.dat'];assert len(m)==524288
    # Independently supplied start-screen savestate, with relocated ChipRAM addresses.
    uss=inputs['Vyper_Startscreen.uss'];pos=0;chip=None
    while pos+12<=len(uss):
        name=uss[pos:pos+4];size,flags=struct.unpack_from('>II',uss,pos+4)
        if name==b'END ':break
        if size<12 or pos+size>len(uss) or flags:raise ValueError('Unexpected USS chunk')
        if name==b'CRAM':chip=uss[pos+12:pos+size]
        pos+=size+4-size%4
    if chip is None or len(chip)!=524288:raise ValueError('USS ChipRAM missing')
    uss_table=0x1ace2
    for i in range(38):
        if chip[uss_table+18*i:uss_table+18*i+8]!=m[0x2daf2+18*i:0x2daf2+18*i+8]:raise ValueError('USS descriptor metadata mismatch')
        if chip[uss_table+18*i+12:uss_table+18*i+14]!=m[0x2daf2+18*i+12:0x2daf2+18*i+14]:raise ValueError('USS frame count mismatch')
    old=DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())
    waves=ofs_files(inputs['VYPER.ADF']);forme=waves['Forme']
    output.mkdir(parents=True,exist_ok=True)
    for n,d in waves.items():(output/('amiga_'+n+'.bin')).write_bytes(d)
    records=DATA.level_records((ROOT/'assets/VYLV.DAT').read_bytes())
    level_evidence=[]
    for _,r in records:
        l=DATA.parse_level_record(r);en=l['enemies']
        original=bytes(v for e in en for v in (e['formation_x'],e['formation_y']-16))+bytes(e['graphic_type'] for e in en)+bytes(e['attack_index'] for e in en)
        # Original coordinates are byte pairs; VYLV Y carries the established +16 conversion.
        off=forme.find(original)
        if off<0:raise ValueError('Original Forme record not found: '+str(l['level']))
        level_evidence.append({'level':l['level'],'forme_offset':off,'enemy_count':len(en),'indices':[e['graphic_type'] for e in en]})
    frames=[];types=[];rows=[];manifest=[];byte_diffs=0;pixel_diffs=0;mask_diffs=0;colour_diffs=0
    def bounded(a):
        if a%2 or not 0<a<=len(m)-32:raise ValueError('Plane/mask pointer bounds')
        return m[a:a+32]
    for i in range(38):
        a=0x2daf2+18*i;p=struct.unpack_from('>I',m,a+8)[0];n=struct.unpack_from('>H',m,a+12)[0]
        if not 0<p<=len(m)-32*n or not 1<=n<=12:raise ValueError('Descriptor bounds')
        if i<36 and old[i]['frame_count']!=n:raise ValueError('Original frame count mismatch')
        if i in (36,37) and (p,n)!=((0x3a07a,10) if i==36 else (0x3a1ba,10)):raise ValueError('Missing type pointer mismatch')
        types.append((len(frames),n))
        rows.append({'vylv_index':i,'vygr_type_1based':i+1,'original_descriptor_address':f'${p:05X}','frame_count':n,'confirmed':i==14,'evidence':'descriptor_and_frame_comparison_strongly_supported'+(';user_visually_confirmed' if i==14 else ''),'original_indexing_routine_proven':False,'source':'ChipRAM $2DAF2+18*i; ADF Forme unchanged type bytes'})
        for j in range(n):
            desc=p+32*j;ptr=struct.unpack_from('>8I',m,desc);planes=[bounded(q) for q in ptr[:3]];mask=bounded(ptr[6]);f=convert(planes,mask)
            up=struct.unpack_from('>I',chip,uss_table+18*i+8)[0];udesc=up+32*j
            if not 0<udesc<=len(chip)-32:raise ValueError('USS frame descriptor bounds')
            ups=struct.unpack_from('>8I',chip,udesc)
            for original,a in zip(planes+[mask],list(ups[:3])+[ups[6]]):
                if a%2 or not 0<a<=len(chip)-32 or original!=chip[a:a+32]:raise ValueError('Independent USS planes/mask mismatch')
            name=f'type_{i+1:02d}_frame_{j:02d}';(output/(name+'_amiga.bin')).write_bytes(b''.join(planes)+mask)
            delta=None
            if i<36:
                o=old[i]['frames'][j];legacyplanes=[bytes(m[q-6+2*((y+3)%16)+k] for y in range(16) for k in range(2)) for q in ptr[:3]]
                recipe=convert(legacyplanes,mask);recipe=bytes((v>>4)|((v&15)<<4) for v in recipe)
                if recipe!=o:raise ValueError('Historical extraction diagnosis does not reproduce original')
                oldpx=[(v>>s)&15 for v in o for s in (0,4)];newpx=[(v>>s)&15 for v in f for s in (0,4)]
                delta={'bytes':sum(a!=b for a,b in zip(o,f)),'pixels':sum(a!=b for a,b in zip(oldpx,newpx)),'rendered_mask_pixels':sum(bool(a)!=bool(b) for a,b in zip(oldpx,newpx))}
                byte_diffs+=delta['bytes'];pixel_diffs+=delta['pixels'];mask_diffs+=delta['rendered_mask_pixels']
                corrected_order=[(v>>s)&15 for v in o for s in (4,0)];colour_diffs+=sum(a!=b for a,b in zip(corrected_order,newpx))
            manifest.append({'original_index':i,'vygr_type':i+1,'frame':j,'uss_descriptor':f'${udesc:05X}','uss_plane_pointers':[f'${q:05X}' for q in ups[:3]],'uss_mask_pointer':f'${ups[6]:05X}','descriptor':f'${desc:05X}','plane_pointers':[f'${q:05X}' for q in ptr[:3]],'mask_pointer':f'${ptr[6]:05X}','amiga_sha256':sha(b''.join(planes)+mask),'ncm_sha256':sha(f),'ncm_target_offset':312+128*len(frames),'legacy_diff':delta,'opaque_per_column':[sum(bool((mask[2*y+x//8]>>(7-x%8))&1) for y in range(16)) for x in range(16)]});frames.append(f)
    directory=b''.join(struct.pack('<IHH',312+128*start,n,0) for start,n in types)
    raw=b'VYGR'+struct.pack('<HH',1,38)+directory+b''.join(frames);graphics_types(raw)
    (output/'VYGR.DAT').write_bytes(raw);(output/'vylv_vygr_mapping.json').write_text(json.dumps(rows,indent=2)+'\n')
    report={'stage':'5b','source_sha256':SOURCE_HASHES,'uss_cross_check':{'table':'$1ACE2','identical_frames':259,'all_plane_and_mask_bytes_match':True},'types':38,'frames':len(frames),'bytes':len(raw),'sha256':sha(raw),'sum16':sum(raw)&65535,'format':'VYGR v1; u16 version/count, 38 x <IHH offset/frame_count/reserved; NCM128 bytes; no palette blocks','ncm':'left low nibble; visible original colour+1, mask-zero transparent; linear pointer-relative rows','legacy_diagnosis':'All239 historical frames reproduced EXACTLY by plane pointer-6, (y+3)%16 row addressing, left high nibble; mask pointer unchanged. Correct recipe uses pointer-relative linear rows and left low nibble.','existing_frame_changes':{'bytes':byte_diffs,'rendered_pixels':pixel_diffs,'rendered_mask_pixels':mask_diffs,'colour_pixels_after_nibble_fix':colour_diffs},'original_indexing_routine_proven':False,'mapping_evidence':'Strong descriptor/frame/ADF comparison; only14->15 separately visually confirmed. No original routine proof claimed.','levels':level_evidence,'mapping':rows,'frames_manifest':manifest}
    (output/'extraction_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    # Indexed contact sheets: diagnostic palette only, not original level colours.
    from PIL import Image,ImageDraw
    image=Image.new('RGB',(16*12,38*20),(40,40,40));draw=ImageDraw.Draw(image)
    for i,(start,n) in enumerate(types):
        for j in range(n):
            f=frames[start+j];px=[(v>>s)&15 for v in f for s in (0,4)]
            for y in range(16):
                for x in range(16):
                    v=px[y*16+x];image.putpixel((j*16+x,i*20+y),(v*28,v*28,v*28) if v else (40,40,40))
    image.resize((768,3040),Image.Resampling.NEAREST).save(output/'all_types_preview.png')
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,default=ROOT/'assets/stage5b/original_sources');ap.add_argument('--output',type=Path,default=ROOT/'assets/stage5b');a=ap.parse_args();r=extract(a.source,a.output);print(json.dumps({k:r[k] for k in ('types','frames','bytes','sha256','sum16','existing_frame_changes')},indent=2))
