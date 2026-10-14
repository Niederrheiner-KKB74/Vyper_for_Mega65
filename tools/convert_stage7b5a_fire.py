#!/usr/bin/env python3
"""Original Level shot fields and ENTRY lower bounds (no curve edits)."""
import argparse,binascii,csv,hashlib,json,struct
from pathlib import Path
from analysis.analyze_amiga_enemy_fire import ofs_selected,HASHES
ROOT=Path(__file__).resolve().parents[1]
def convert(out):
    adf=(ROOT/'assets/stage5b/original_sources/VYPER.ADF').read_bytes()
    assert hashlib.sha256(adf).hexdigest()==HASHES['VYPER.ADF']
    files=ofs_selected(adf);level=files['Level']['bytes'];debut=files['Debut']['bytes']
    rows=list(csv.DictReader((ROOT/'assets/amiga_enemy_fire_level_parameters.csv').open()))
    vylv=(ROOT/'assets/VYLV.DAT').read_bytes();records=[];offsets=[];audit=[]
    be=lambda r,o:struct.unpack_from('>H',r,o)[0]
    for i,row in enumerate(rows):
        r=level[i*114:(i+1)*114];groups=be(r,0x30);dy,mode,every=[be(r,o) for o in (0x6c,0x6e,0x70)]
        assert [dy,mode,every]==[int(row[k]) for k in ('projectile_dy_6C','shot_event_mode_6E','entry_every_nth_enemy_70')]
        assert dy in (1,2,3) and mode in (1,2) and 1<=every<=4
        off,length=struct.unpack_from('<IH',vylv,8+i*8);vl=vylv[off:off+length];p=8
        assert vl[2]==groups
        lows=[be(r,0x18+2*g) for g in range(groups)]
        record=bytearray([dy,mode,every,groups])+bytearray(struct.pack('<4H',*(lows+[0]*(4-groups))))
        masks=[];lengths=[]
        for g in range(groups):
            n=be(r,0x10+2*g);curveoff=struct.unpack_from('>I',r,4*g)[0];curve=debut[curveoff:curveoff+n]
            count,x,y,nn=struct.unpack_from('<HhhH',vl,p);p+=8
            assert (count,x,y,nn)==(be(r,0x32+2*g),struct.unpack_from('>h',r,0x20+2*g)[0],struct.unpack_from('>h',r,0x28+2*g)[0],n)
            assert vl[p:p+n]==curve;p+=n
            mask=bytearray((n+7)//8)
            for t,b in enumerate(curve):
                y+=-(b&7) if b&8 else b&7
                if y<=148:mask[t//8]|=1<<(t%8)
            assert any(mask[t//8]&(1<<(t%8)) for t in range(lows[g],n))
            masks.append(mask);lengths.append(n)
        assert lows==list(map(int,row['entry_lower_bounds_18'].split('|')))
        assert lengths==list(map(int,row['group_curve_lengths'].split('|')))
        # Verify bitmap capacity; only the11 original parameter bytes enter VYSH.
        record+=b''.join(masks);assert 12<len(record)<256
        offsets.append(16+11*i);records.append(bytes([dy,mode,every])+struct.pack('<4H',*(lows+[0]*(4-groups))))
        audit.append({'level':i+1,'DY_stored_only':dy,'mode':mode,'every_nth':every,'lower_bounds':lows,'curve_lengths':lengths,'record_bytes':11,'bitmap_work_bytes':len(record)})
    assert len(records)==100
    payload=b''.join(records)
    header=struct.pack('<4sBBBBHHHH',b'VYSH',1,100,4,11,16+len(payload),sum(payload)&65535,16,0)
    data=header+payload;out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'VYSH.DAT').write_bytes(data)
    (out/'fire_constants.inc').write_text(f'.const F_BYTES={len(data)}\n.const F_SUM={sum(data)&65535}\n')
    inc=''
    inc+='f_record_lo: .byte '+','.join(str(x&255) for x in offsets)+'\n'
    inc+='f_record_hi: .byte '+','.join(str(x>>8) for x in offsets)+'\n'
    inc+='f_record_size: .byte '+','.join(str(len(x)&255) for x in records)+'\n'
    crcs=[binascii.crc_hqx(r,65535) for r in records]
    inc+='f_crc_lo: .byte '+','.join(str(c&255) for c in crcs)+'\n'
    inc+='f_crc_hi: .byte '+','.join(str(c>>8) for c in crcs)+'\n'
    (out/'fire_layout.inc').write_text(inc)
    report={'format':'VYSH v1','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'header':header.hex(),'DY_applied':False,'runtime_integrity':'pinned full sum16, exact header/fixed layout, CRC-16/CCITT-FALSE for each of100 records','runtime_bitmap':'Not stored in DAT. Reconstructed from loaded VYLV: bit t = original expanded Debut Y[t] <=148, before B2 projection; negative Y is eligible','levels':audit}
    (out/'fire-parameters.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();convert(a.output)
