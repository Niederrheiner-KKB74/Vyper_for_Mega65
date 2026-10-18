#!/usr/bin/env python3
"""Validate and compare raw Stage10b1 SEQ/monitor dumps. No third-party modules."""
import argparse, hashlib, json, struct, re
from pathlib import Path
DEFAULT=Path(__file__).resolve().parents[2]/'releases/stage_10b1/registers.json'
PHASES=['before video','after video','after simulated mode transition','reference scene']
def parse(data,schema):
 if len(data)!=schema['dump_size']:raise ValueError('Wrong size (SEQ has no two-byte PRG load address)')
 if data[:8]!=b'VYDG10B1' or data[8]!=1:raise ValueError('Unknown magic/version')
 if data[9] not in b'SE' or data[10] not in b'UHX':raise ValueError('Invalid profile/environment')
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
 if data.startswith(b'VYDG10B1'):return data
 # UART monitor M output: :00004800:5659... (16bytes per line).
 rows=re.findall(rb':([0-9A-Fa-f]{8}):([0-9A-Fa-f]{32})',data)
 if rows:
  chunks={int(a,16):bytes.fromhex(b.decode()) for a,b in rows}
  if min(chunks)!=0x4800:raise ValueError('Monitor dump must begin at4800')
  return b''.join(chunks[a] for a in sorted(chunks))[:struct.unpack_from('<I',chunks[0x4810],0)[0]]
 return data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('left',type=Path);p.add_argument('right',type=Path,nargs='?');p.add_argument('--schema',type=Path,default=DEFAULT);p.add_argument('--json',type=Path);p.add_argument('--left-file',help='SEQ filename when left input is a D81');p.add_argument('--right-file',help='SEQ filename when right input is a D81');a=p.parse_args()
 try:
  schema=json.loads(a.schema.read_text());left=parse(load(a.left,a.left_file),schema)
  report=compare(left,parse(load(a.right,a.right_file),schema),schema) if a.right else {'input':{k:v for k,v in left.items() if k!='phases'},'geometry':[geometry(r) for r in left['phases']]}
 except (ValueError,OSError,KeyError) as e:p.error(str(e))
 rendered=json.dumps(report,indent=2)+'\n'
 if a.json:a.json.write_text(rendered)
 else:print(rendered,end='')
if __name__=='__main__':main()
