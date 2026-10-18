#!/usr/bin/env python3
"""Validate and compare raw Stage10b1 SEQ/monitor dumps. No third-party modules."""
import argparse, hashlib, json, struct, re
from pathlib import Path
DEFAULT=Path(__file__).resolve().parents[2]/'releases/stage_10b1a/registers.json'
PHASES=['before video','after video','after simulated mode transition','reference scene']
def parse(data,schema):
 if len(data)!=schema['dump_size']:raise ValueError('Wrong size (SEQ has no two-byte PRG load address)')
 if data[:8]!=b'VYDG1B1A' or data[8]!=1:raise ValueError('Unknown magic/version')
 if data[9] not in b'AB' or data[10] not in b'UHX':raise ValueError('Invalid profile/environment')
 n,block,size=struct.unpack_from('<HHI',data,12)
 if (data[11],n,block,size)!=(4,len(schema['registers']),schema['block_size'],len(data)):raise ValueError('Schema/header mismatch')
 if data[30:32]!=b'\1\1':raise ValueError('Unknown checksum/unlock flags')
 expected=struct.unpack_from('<H',data,28)[0]
 if (sum(data)-data[28]-data[29])&65535!=expected:raise ValueError('Checksum mismatch')
 phases=[];contexts=[]
 for p in range(4):
  start=32+p*block
  if data[start:start+2]!=bytes((p+1,data[9])):raise ValueError('Phase/profile mismatch')
  contexts.append({'phase':p+1,'D012':data[start+2],'D011':data[start+3],'classification':'volatile phase-start context'})
  regs={}
  for i,r in enumerate(schema['registers']):
   addr,value=struct.unpack_from('<HB',data,start+4+3*i)
   if addr!=r['address']:raise ValueError('Register sequence mismatch')
   regs[addr]=value
  phases.append(regs)
 return {'profile':chr(data[9]),'environment':chr(data[10]),'sha256':hashlib.sha256(data).hexdigest(),'phases':phases,'phase_context':contexts}
def geometry(r):
 h640=bool(r[0xd031]&128);scale=r[0xd05a]
 stride=r[0xd058]+256*r[0xd059];count=r[0xd05e]+256*((r[0xd063]>>4)&3)
 x=r[0xd04c]+256*(r[0xd04d]&15);y=r[0xd04e]+256*(r[0xd04f]&15)
 return {'H640':h640,'source_pixels_per_native_pixel':scale/(120 if h640 else 240),
  'native_pixels_per_source_pixel':(120 if h640 else 240)/scale if scale else None,
  'line_step_bytes':stride,'characters_per_row':count,'last_row_index':r[0xd07b],
  'physical_rasters_per_source_y':r[0xd05b]+1,'CHARX':x,'CHARY':y,
  'screen_physical':r[0xd060]+256*r[0xd061]+65536*r[0xd062]+16777216*(r[0xd063]&15),
  'colour_offset':r[0xd064]+256*r[0xd065],
  'scene_HUD_GOTOX_native':480,'scene_playfield_logical':[0,239],
  'sprite_rule':'native X=CHARX+2*X-3, native Y=CHARY+2*Y',
  'note':'scene boundaries are source layout, not evidence of physical rendering; HOTREG can overwrite values'}
def compare(a,b,schema):
 rows=[]
 for p in range(4):
  for r in schema['registers']:
   addr=r['address'];v=a['phases'][p][addr];w=b['phases'][p][addr];mask=r['compare_mask']
   if v!=w:rows.append({'phase':p+1,'phase_name':PHASES[p],'address':f'${addr:04X}','name':r['name'],
     'left':f'${v:02X}','right':f'${w:02X}','mask':f'${mask:02X}',
     'stable_bits_differ':bool((v^w)&mask),'classification':'compare stable bits' if (v^w)&mask else 'volatile/context bits; raw difference retained'})
 first=next((r['phase'] for r in rows if r['stable_bits_differ']),None)
 report={'left':{k:v for k,v in a.items() if k!='phases'},'right':{k:v for k,v in b.items() if k!='phases'},
  'same_profile':a['profile']==b['profile'],'first_stable_divergence_phase':first,'differences':rows,
  'geometry_left':[geometry(r) for r in a['phases']],'geometry_right':[geometry(r) for r in b['phases']],
  'interpretation':'Value comparison only. Equal registers do not prove equal rendering. Use photographs and pinned core semantics. Environment labels are user declarations.'}
 report['phase_context_differences']=[{'phase':i+1,'left':a['phase_context'][i],'right':b['phase_context'][i],'classification':'volatile timing context'} for i in range(4) if a['phase_context'][i]!=b['phase_context'][i]]
 report['configuration_left']=configuration(a);report['configuration_right']=configuration(b)
 report['unexpected_stable_differences']=[r for r in rows if r['stable_bits_differ'] and not (a['profile']!=b['profile'] and r['phase']>1 and r['address']=='$D051' and (int(r['left'][1:],16)^int(r['right'][1:],16))&0xc0==0x80)]
 return report
def disk_file(data,name):
 if len(data)!=819200:raise ValueError('Expected D81 size819200')
 def sector(t,s):
  if not 1<=t<=80 or not 0<=s<40:raise ValueError('Invalid sector')
  i=((t-1)*40+s)*256;return data[i:i+256]
 t,s=40,3;seen=set()
 while t:
  if (t,s) in seen:raise ValueError('Directory cycle')
  seen.add((t,s));b=sector(t,s)
  for i in range(8):
   e=b[2+32*i:32+32*i]
   if e[0] and e[3:19].rstrip(b'\xa0').decode('ascii')==name.upper():
    ft,fs=e[1:3];out=bytearray();chain=set()
    while ft:
     if (ft,fs) in chain:raise ValueError('File cycle')
     chain.add((ft,fs));q=sector(ft,fs);ft,fs=q[:2]
     if not ft and not 1<=fs<=255:raise ValueError('Invalid terminal length')
     out.extend(q[2:256 if ft else fs+1])
    return bytes(out)
  t,s=b[:2]
 raise ValueError('File not found: '+name)
def load(path,name=None):
 data=path.read_bytes()
 if name:return disk_file(data,name)
 if data.startswith((b'VYDG1B1A',b'VYMM1B1A')):return data
 # UART monitor M output: :00004800:5659... (16bytes per line).
 rows=re.findall(rb':([0-9A-Fa-f]{8}):([0-9A-Fa-f]{32})',data)
 if rows:
  chunks={int(a,16):bytes.fromhex(b.decode()) for a,b in rows}
  if min(chunks)!=0x4800:raise ValueError('Monitor dump must begin at4800')
  return b''.join(chunks[a] for a in sorted(chunks))[:struct.unpack_from('<I',chunks[0x4810],0)[0]]
 return data


def configuration(a):
 expected=0x80 if a['profile']=='A' else 0
 failures=[]
 for i,r in enumerate(a['phases'][1:],2):
  tests={0xd051:(0xc0,expected),0xd054:(0xff,0x55),0xd031:(0xff,0xc0),0xd05a:(255,60),0xd058:(255,192),0xd059:(255,0),0xd05e:(255,96),0xd01a:(16,0),0xd05b:(255,1),0xd07b:(255,25),0xd063:(255,0),0xd060:(255,0),0xd061:(255,0xe0),0xd062:(255,0),0xd064:(255,0),0xd065:(255,0),0xd068:(255,0),0xd069:(255,0x40),0xd06a:(255,0)}
  for addr,(mask,want) in tests.items():
   if r[addr]&mask!=want:failures.append({'phase':i,'address':f'${addr:04X}','mask':mask,'expected':want,'actual':r[addr]})
 return {'fixed_E_NORRDEL_DBLRR_checks_pass':not failures,'failures':failures}
def parse_memory(data,schema):
 m=schema['memory']
 if len(data)!=m['size'] or data[:8]!=b'VYMM1B1A' or data[8]!=1:raise ValueError('Memory size/magic/version mismatch')
 if data[9] not in b'AB' or data[10] not in b'UHX' or data[11]!=len(m['regions']):raise ValueError('Memory variant/label/count mismatch')
 if struct.unpack_from('<HHI',data,12)!=(16,256,len(data)) or data[30:32]!=b'\1\4':raise ValueError('Memory header mismatch')
 if (sum(data)-data[28]-data[29])&65535!=struct.unpack_from('<H',data,28)[0]:raise ValueError('Memory checksum mismatch')
 regions=[]
 for i,r in enumerate(m['regions']):
  addr,offset,n,flags,reserved=struct.unpack_from('<IIIHH',data,32+16*i)
  if (addr,offset,n,flags,reserved)!=(r['address'],r['offset'],r['length'],0,0):raise ValueError('Memory directory mismatch')
  payload=data[offset:offset+n]
  regions.append({**r,'sha256':hashlib.sha256(payload).hexdigest(),'data':payload})
 return {'variant':chr(data[9]),'environment':chr(data[10]),'sha256':hashlib.sha256(data).hexdigest(),'regions':regions}
def compare_memory(a,b):
 result=[]
 for l,r in zip(a['regions'],b['regions']):
  diffs=[{'offset':i,'address':f"${l['address']+i:07X}",'left':v,'right':w,'declared_variant_marker':l['name']=='screen' and i==44 and a['variant']!=b['variant'] and (v,w)==(ord(a['variant'])-64,ord(b['variant'])-64)} for i,(v,w) in enumerate(zip(l['data'],r['data'])) if v!=w]
  result.append({'name':l['name'],'address':l['address'],'bytes':len(l['data']),'left_sha256':l['sha256'],'right_sha256':r['sha256'],'different_bytes':len(diffs),'unexpected_different_bytes':sum(not d['declared_variant_marker'] for d in diffs),'first64_differences':diffs[:64]})
 return {'regions':result,'unexpected_different_bytes':sum(r['unexpected_different_bytes'] for r in result),'note':'Only screen byte44 is an expected A/B annotation; none is ignored for the same variant across platforms.'}
def memory_summary(a):return {**{k:v for k,v in a.items() if k!='regions'},'regions':[{k:v for k,v in r.items() if k!='data'} for r in a['regions']]}
def raw_input(path,filename=None):
 if filename:return disk_file(path.read_bytes(),filename)
 return load(path)
def main():
 p=argparse.ArgumentParser(description='Stage10b1a versioned register/memory validation and comparison')
 p.add_argument('left',type=Path);p.add_argument('right',type=Path,nargs='?');p.add_argument('--schema',type=Path,default=DEFAULT);p.add_argument('--json',type=Path)
 for side in ['left','right']:
  p.add_argument('--'+side+'-reg-file');p.add_argument('--'+side+'-memory',type=Path);p.add_argument('--'+side+'-mem-file')
 a=p.parse_args()
 try:
  schema=json.loads(a.schema.read_text());l=parse(raw_input(a.left,a.left_reg_file),schema)
  report=compare(l,parse(raw_input(a.right,a.right_reg_file),schema),schema) if a.right else {'input':{k:v for k,v in l.items() if k!='phases'},'configuration':configuration(l),'geometry':[geometry(r) for r in l['phases']]}
  memories=[]
  for side,regpath in [('left',a.left),('right',a.right)]:
   path=getattr(a,side+'_memory');name=getattr(a,side+'_mem_file')
   if path or name:
    mem=parse_memory(raw_input(path or regpath,name),schema);reg=parse(raw_input(regpath,getattr(a,side+'_reg_file')),schema)
    if (mem['variant'],mem['environment'])!=(reg['profile'],reg['environment']):raise ValueError('Register/memory run label mismatch')
    memories.append(mem);report[side+'_memory']=memory_summary(mem)
  if len(memories)==2:report['memory_comparison']=compare_memory(*memories)
 except (ValueError,OSError,KeyError,TypeError) as e:p.error(str(e))
 text=json.dumps(report,indent=2)+'\n'
 if a.json:a.json.write_text(text)
 else:print(text,end='')
if __name__=='__main__':main()
