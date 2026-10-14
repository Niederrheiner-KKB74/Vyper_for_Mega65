#!/usr/bin/env python3
"""Issue61: bounded OFS/HUNK/USS evidence. Read-only engine and original assets.
Writes only analysis JSON/text/CSV; never assembles or creates PRG/D81/DAT.
"""
import argparse, csv, hashlib, io, json, struct
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HASHES = {
 'Vyper_Memory_Dump.dat':'d74aea88fb4232e36caab80e51abc51f73d470a5b55a54f5cb010f1d910ddf8c',
 'Vyper_Startscreen.uss':'d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916',
 'VYPER.ADF':'b28cab911431aaf3e48fd3e9979159de7154f98538eeba191f52ac47ef9665e5',
}

# Addresses in the supplied start-screen BRAM mapping, NOT universal addresses.
RANGES = [
 ('sprite_record_initialization',0xc0a0fe,0xc0a16a),
 ('level_record_pointer',0xc0a2ea,0xc0a304),
 ('enemy_count_and_mode',0xc0a730,0xc0a75e),
 ('attack_timer_level_tables',0xc0a75e,0xc0a82c),
 ('entry_expansion',0xc0a876,0xc0a9a2),
 ('entry_selection_counter_init',0xc0ad32,0xc0ad5e),
 ('entry_lower_bound_reset',0xc0adb6,0xc0adc4),
 ('entry_delay_and_length',0xc0ade6,0xc0ae56),
 ('entry_shot_planning',0xc0ae8e,0xc0af84),
 ('level_projectile_speed_reset',0xc0b1e4,0xc0b24a),
 ('packed_xy_decoder',0xc0c3bc,0xc0c40e),
 ('raster_sync',0xc09454,0xc09462),
 ('game_update_calls',0xc09708,0xc0972a),
 ('loop_back',0xc09934,0xc09938),
 ('counter_update',0xc0d08c,0xc0d0aa),
 ('player_spawn_and_update',0xc0d0aa,0xc0d174),
 ('attack_selection_and_shot_planning',0xc0d174,0xc0d27e),
 ('enemy_hit_no_projectile_cleanup',0xc0d340,0xc0d360),
 ('enemy_entry_return_attack_death',0xc0d3e2,0xc0d56e),
 ('publish_eight_hw_sprites',0xc0d56e,0xc0d5c8),
 ('enemy_projectile_update',0xc0d5c8,0xc0d612),
 ('enemy_projectile_spawn',0xc0d612,0xc0d6d6),
 ('beam_rng',0xc0d764,0xc0d77e),
 ('attack_timer_reset',0xc0d846,0xc0d890),
 ('entry_rng',0xc0edf8,0xc0ee24),
]
def sha(data): return hashlib.sha256(data).hexdigest()
def u16(b,o): return struct.unpack_from('>H',b,o)[0]
def u32(b,o): return struct.unpack_from('>I',b,o)[0]

def ofs_selected(adf):
    if len(adf)!=901120 or adf[:4]!=b'DOS\0': raise ValueError('Expected original OFS disk')
    def block(n):
        if not 0<n<1760: raise ValueError('OFS block out of bounds')
        b=adf[n*512:(n+1)*512]
        if sum(struct.unpack('>128I',b))&0xffffffff: raise ValueError('OFS checksum')
        return b
    out={};seen=set()
    def walk(n,path=''):
        if n in seen: raise ValueError('Directory cycle')
        seen.add(n);b=block(n);w=struct.unpack('>128I',b)
        name=b[433:433+b[432]].decode('latin1');path+='/'+name
        if w[127] in (1,2):
            for q in w[6:78]:
                chain=set()
                while q:
                    if q in chain:raise ValueError('Hash-chain cycle')
                    chain.add(q);walk(q,path);q=u32(block(q),496)
        elif w[127]==0xfffffffd and (name in ('Shot','vyper','a','startup-sequence') or '/Wave/' in path):
            data=bytearray();q=w[4];seq=1;chain=set();blocks=[]
            while q:
                if q in chain:raise ValueError('File cycle')
                chain.add(q);blocks.append(q);bb=block(q);v=struct.unpack('>6I',bb[:24])
                if v[0]!=8 or v[1]!=n or v[2]!=seq or v[3]>488:raise ValueError('OFS data sequence')
                data+=bb[24:24+v[3]];q=v[4];seq+=1
            if len(data)!=w[81]:raise ValueError('OFS size')
            out[name]={'path':path,'bytes':bytes(data),'header_block':n,'data_blocks':blocks}
    walk(880)
    return out

def hunks(b):
    p=0
    def word():
        nonlocal p
        if p+4>len(b):raise ValueError('Truncated HUNK')
        n=u32(b,p);p+=4;return n
    if word()!=0x3f3 or word()!=0:raise ValueError('Expected unnamed HUNK_HEADER')
    count,first,last=word(),word(),word()
    if (count,first,last)!=(3,0,2):raise ValueError('Expected three original hunks')
    sizes=[word() for _ in range(count)];result=[]
    for index in range(count):
        kind=word();length=word()*4;offset=p
        if kind not in (0x3e9,0x3ea,0x3eb) or length>(sizes[index]&0x3fffffff)*4:raise ValueError('Invalid HUNK kind/size')
        data=bytes(length) if kind==0x3eb else b[p:p+length]
        if len(data)!=length:raise ValueError('Truncated HUNK payload')
        if kind!=0x3eb:p+=length
        rel=[]
        while True:
            op=word()
            if op==0x3f2:break
            if op!=0x3ec:raise ValueError('Unhandled HUNK '+hex(op))
            while True:
                n=word()
                if not n:break
                target=word()
                if target>=count:raise ValueError('Relocation target outside hunks')
                for _ in range(n):
                    o=word()
                    if o+4>len(data) or o&1:raise ValueError('Relocation outside hunk')
                    rel.append((target,o))
        result.append({'kind':kind,'data':data,'file_offset':offset,'relocations':rel,'allocated_bytes':(sizes[index]&0x3fffffff)*4})
    if p!=len(b):raise ValueError('Trailing HUNK bytes')
    return result

def uss_chunks(b):
    out={};p=0
    while p+12<=len(b):
        name=b[p:p+4];size=u32(b,p+4)
        if name==b'END ':return out
        if size<12 or p+size>len(b) or u32(b,p+8)!=0:raise ValueError('Unsupported USS chunk')
        out[name]={'data':b[p+12:p+size],'payload_offset':p+12};p+=size+4-size%4
    raise ValueError('Missing USS end')

def relocated(code,rel,bases):
    out=bytearray(code)
    for target,o in rel:out[o:o+4]=((u32(code,o)+bases[target])&0xffffffff).to_bytes(4,'big')
    return bytes(out)

def analyze(source,out):
    import capstone
    if capstone.__version__!='5.0.7':raise ValueError('Use capstone==5.0.7')
    raw={n:(source/n).read_bytes() for n in HASHES}
    for n,d in raw.items():
        if sha(d)!=HASHES[n]:raise ValueError('Original source changed: '+n)
    files=ofs_selected(raw['VYPER.ADF']) # Startup invokes Shot; vyper/a are distinct disk files.
    hs=hunks(files['Shot']['bytes']);code=hs[0]['data'];rel=hs[0]['relocations'];ch=uss_chunks(raw['Vyper_Startscreen.uss'])
    assert len(ch[b'CRAM']['data'])==len(ch[b'BRAM']['data'])==524288
    signature=bytes.fromhex('2f0a0c6c00062c1c670000b6');spawn=code.index(signature)
    assert code.count(signature)==1
    sources={}
    for name,data,map_base in [('USS_BRAM',ch[b'BRAM']['data'],0xc00000),('ChipRAM_dump',raw['Vyper_Memory_Dump.dat'],0)]:
        pos=data.index(signature);assert data.count(signature)==1
        start=pos-spawn;saved=data[start:start+len(code)];base=map_base+start;bases={}
        for t in range(3):
            values=Counter((u32(saved,o)-u32(code,o))&0xffffffff for target,o in rel if target==t)
            if values:
                if len(values)!=1:raise ValueError('Ambiguous HUNK relocation base')
                bases[t]=next(iter(values))
        expected=relocated(code,rel,bases);diffs=[i for i,(a,b) in enumerate(zip(expected,saved)) if a!=b]
        sources[name]={'base':base,'offset':start,'hunk_bases':bases,'full_CODE_nonrelocation_differences':len(diffs),'expected':expected,'saved':saved,'payload_file_offset':ch[b'BRAM']['payload_offset'] if name=='USS_BRAM' else 0}
    base=sources['USS_BRAM']['base'];assert base==0xc08760 and sources['ChipRAM_dump']['base']==0x21b20
    tables={'base':[u16(hs[1]['data'],0x18c+2*i) for i in range(10)],'range':[u16(hs[1]['data'],0x1a0+2*i) for i in range(10)],'batch_thresholds':[list(hs[1]['data'][0x1b4+3*i:0x1b7+3*i]) for i in range(10)]}
    for name,src in sources.items():
        ram=ch[b'CRAM']['data'] if name=='USS_BRAM' else raw['Vyper_Memory_Dump.dat']
        data_base=src['hunk_bases'][1]
        assert ram[data_base+0x18c:data_base+0x1d2]==hs[1]['data'][0x18c:0x1d2]
    cpu=ch[b'CPU ']['data'];assert u32(cpu,0)==68000
    pc=u32(cpu,68);a4=u32(cpu,56);assert a4==sources['USS_BRAM']['hunk_bases'][1]+0x7ffe
    md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
    text=[];spans=[]
    for name,lo,hi in RANGES:
        s,e=lo-base,hi-base
        if not 0<=s<e<=len(code):raise ValueError('Range outside CODE')
        for src in sources.values():
            if src['expected'][s:e]!=src['saved'][s:e]:raise ValueError('Relevant code differs: '+name)
        text.append(f'\n; {name}, CODE+${s:04X}, Shot file+${hs[0]["file_offset"]+s:04X}; both runtime sources match after HUNK_RELOC32\n')
        ins=list(md.disasm(sources['USS_BRAM']['saved'][s:e],lo))
        if sum(i.size for i in ins)!=e-s or any(i.mnemonic in ('.byte','dc.w') for i in ins):raise ValueError('Not completely decoded '+name)
        rows=[]
        for i in ins:
            o=i.address-base;dump_addr=sources['ChipRAM_dump']['base']+o
            line=f'{i.address:08X} / {dump_addr:06X} / CODE+{o:04X} / FILE+{hs[0]["file_offset"]+o:04X}  {i.bytes.hex():<22} {i.mnemonic:<9} {i.op_str}'
            text.append(line.rstrip()+'\n');rows.append({'USS_address':i.address,'dump_address_and_offset':dump_addr,'CODE_offset':o,'Shot_file_offset':hs[0]['file_offset']+o,'USS_file_offset':ch[b'BRAM']['payload_offset']+i.address-0xc00000,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str})
        spans.append({'name':name,'start':lo,'end_exclusive':hi,'both_runtime_copies_match_relocated_ADF':True,'instructions':rows})
    # All aligned direct PC-relative/absolute JSR encodings targeting the spawn.
    calls=[];target=0xc0d612
    runtime=sources['USS_BRAM']['expected']
    for o in range(0,len(runtime)-6,2):
        op=u16(runtime,o)
        dst=base+o+2+struct.unpack_from('>h',runtime,o+2)[0] if op==0x4eba else u32(runtime,o+2) if op==0x4eb9 else None
        if dst==target:calls.append(base+o)
    assert calls==[0xc0d452,0xc0d466,0xc0d4fc,0xc0d510],calls
    level=files['Level']['bytes'];assert len(level)==11400
    csvbuf=io.StringIO();writer=csv.writer(csvbuf,lineterminator='\n')
    writer.writerow(['level','original_file_record_offset_hex','groups','enemy_count','group_curve_lengths','entry_lower_bounds_18','projectile_dy_6C','shot_event_mode_6E','entry_every_nth_enemy_70','entry_start_interval_42','entry_newly_planned_events_upper_bound','attack_events_upper_bound_per_launch'])
    levels=[]
    for i in range(100):
        r=level[i*114:(i+1)*114];ng=u16(r,0x30);counts=[u16(r,0x32+2*g) for g in range(ng)];lengths=[u16(r,0x10+2*g) for g in range(ng)];dy,mode,every=[u16(r,o) for o in (0x6c,0x6e,0x70)]
        assert 1<=ng<=4 and dy in (1,2,3) and mode in (1,2) and 1<=every<=4
        lower=[u16(r,0x18+2*g) for g in range(ng)];audit=[]
        for g,(n,low) in enumerate(zip(lengths,lower)):
            assert 0<=low<n # No actual zero-divisor/error-clamp record in supplied100 levels.
            curve_offset=u32(r,4*g);packed=files['Debut']['bytes'][curve_offset:curve_offset+n]
            assert len(packed)==n
            x=struct.unpack_from('>h',r,0x20+2*g)[0];y=struct.unpack_from('>h',r,0x28+2*g)[0];ys=[]
            for b in packed:
                dx=(b>>4)&7;dy_step=b&7
                x+=-dx if b&0x80 else dx;y+=-dy_step if b&8 else dy_step;ys.append(y)
            eligible=[t for t in range(low,n) if ys[t]<=148]
            assert eligible # Original rejection loop has at least one admissible point.
            audit.append({'Debut_offset':curve_offset,'length':n,'lower_bound':low,'eligible_count':len(eligible),'first_eligible_index':eligible[0],'last_eligible_index':eligible[-1]})
        writer.writerow([i+1,f'{i*114:04X}',ng,sum(counts),'|'.join(map(str,lengths)),'|'.join(map(str,lower)),dy,mode,every,u16(r,0x42),sum(counts)//every*mode,mode])
        levels.append({'level':i+1,'group_lengths':lengths,'group_counts':counts,'raw_lower_bounds_18':lower,'entry_point_audit':audit,'6C':dy,'6E':mode,'70':every})
    report={'issue':61,'analysis_only':True,'disassembler':'Capstone5.0.7 M68K_000','source_sha256':HASHES,'input_sizes':{n:len(b) for n,b in raw.items()},'ADF_files':{n:{k:v for k,v in info.items() if k!='bytes'}|{'bytes':len(info['bytes']),'sha256':sha(info['bytes'])} for n,info in files.items()},'HUNK_sections':[{'kind':h['kind'],'file_offset':h['file_offset'],'bytes':len(h['data']),'allocated_bytes':h['allocated_bytes'],'relocations':len(h['relocations'])} for h in hs],'code_sources':{name:{k:v for k,v in src.items() if k not in ('expected','saved')} for name,src in sources.items()},'USS_chunks':{k.decode():{'bytes':len(v['data']),'payload_offset':v['payload_offset'],'sha256':sha(v['data'])} for k,v in ch.items() if k in (b'CPU ',b'CRAM',b'BRAM')},'saved_CPU':{'model':68000,'PC':pc,'A4':a4,'format':'WinUAE save_cpu:15 D0-D7/A0-A6 registers, then PC; CPU payload offsets56/68'},'attack_timer_original_tables':tables,'spawn_call_sites':calls,'verified_spans':spans,'level_fields':levels,'field_distributions':{f'{o:X}':dict(Counter(u16(level,i*114+o) for i in range(100))) for o in (0x6c,0x6e,0x70)},'limitations':['Static original code/data proof, not executed WinUAE trace.','Only one supplied menu savestate plus separate ChipRAM dump; no new (1) gameplay snapshots present.','Whole CODE hunk differs outside verified excerpts: no whole-image-identity claim.','Opcode scan finds4 aligned direct spawn callers; no claim about arbitrary external/self-modifying indirect code.','No game engine, DAT, PRG, D81 or gameplay parameters changed.','50Hz engine cadence has not been measured: 8bit raster sync also matches PAL line256.','ENTRY mode1 sets first countdown but does not explicitly clear second in the selected-actor branch; stale reuse needs trace.']}
    out.mkdir(parents=True,exist_ok=True)
    (out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n');(out/'68000-excerpts.txt').write_text('Addresses: USS virtual / dump address=offset / CODE offset / extracted Shot file offset.\n'+''.join(text));(out/'level_parameters.csv').write_text(csvbuf.getvalue())
    print(json.dumps({'CODE_base_USS':hex(base),'CODE_base_dump':hex(sources['ChipRAM_dump']['base']),'verified_spans':len(spans),'instructions':sum(len(s['instructions']) for s in spans),'level_records':100,'saved_PC':hex(pc),'spawn_call_sites':list(map(hex,calls))},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'assets/stage5b/original_sources');p.add_argument('--output',type=Path,default=ROOT/'docs/amiga_enemy_fire_evidence');a=p.parse_args();analyze(a.source,a.output)
