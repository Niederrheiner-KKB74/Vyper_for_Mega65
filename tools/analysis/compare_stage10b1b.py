#!/usr/bin/env python3
"""Strict Stage10b1b snapshot/CRC, register, palette and scene-layout comparison."""
import argparse,binascii,hashlib,json,struct,re
from pathlib import Path
from compare_stage10b1_registers import disk_file,geometry
ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'releases/stage_10b1b/registers.json'
def crc16(data):
 b=bytearray(data);b[28:30]=b'\0\0';return binascii.crc_hqx(b,0xffff)
def parse(data,schema):
 if len(data)!=schema['dump_size'] or data[:8]!=b'VYDG1B1B' or data[8]!=1:raise ValueError('Snapshot size/magic/version mismatch')
 if data[9] not in b'ABCD' or data[10] not in b'UHX' or data[11] not in (1,2):raise ValueError('Scene/platform/phase mismatch')
 if struct.unpack_from('<HHI',data,12)!=(len(schema['registers']),len(schema['regions']),len(data)):raise ValueError('Header/schema mismatch')
 if data[30:32]!=b'\2\1':raise ValueError('Unsupported CRC algorithm/unlock flags')
 if crc16(data)!=struct.unpack_from('<H',data,28)[0]:raise ValueError('CRC16 mismatch')
 regs={}
 for i,r in enumerate(schema['registers']):
  addr,value=struct.unpack_from('<HB',data,schema['register_offset']+3*i)
  if addr!=r['address']:raise ValueError('Register address sequence mismatch')
  regs[addr]=value
 regions=[]
 for i,r in enumerate(schema['regions']):
  addr,offset,n,flags,reserved=struct.unpack_from('<IIIHH',data,schema['directory_offset']+16*i)
  if (addr,offset,n,flags,reserved)!=(r['address'],r['offset'],r['length'],0,0):raise ValueError('Region directory mismatch')
  payload=data[offset:offset+n];regions.append({**r,'sha256':hashlib.sha256(payload).hexdigest(),'data':payload})
 context={f'${addr:04X}':data[32+i] for i,addr in enumerate([0xd012,0xd011,0xd052,0xd053,0xd050,0xd051])}
 context['classification']='volatile sequential phase-start readbacks, not atomic'
 return {'scene':chr(data[9]),'platform_label':chr(data[10]),'phase':'PRE' if data[11]==1 else 'POST','sequence':struct.unpack_from('<I',data,20)[0],
  'D051_write_shadow':data[24],'D051_restore_shadow':data[25],'measured_export_error':data[26],'entry_IRQ_mask':data[27],
  'phase_context':context,'registers':regs,'regions':regions,'sha256':hashlib.sha256(data).hexdigest()}
def region(a,name):return next(r['data'] for r in a['regions'] if r['name']==name)
def layout(a):
 scr=region(a,'screen');col=region(a,'colour');rows=[]
 for y in range(25):
  commands=[];ncm=[];mono=0
  for x in range(96):
   i=y*192+2*x;word=struct.unpack_from('<H',scr,i)[0];attr=col[i]
   if attr&16:commands.append({'slot':x,'word':word,'colour_attribute':list(col[i:i+2])})
   elif attr&8:ncm.append({'slot':x,'glyph':word,'colour_attribute':list(col[i:i+2])})
   else:mono+=1
  rows.append({'row':y,'entries':96,'mono':mono,'NCM':len(ncm),'GOTOX':len(commands),'first8_commands':commands[:8],'first8_NCM_slots':ncm[:8],'original_pixie_slots':[v for v in ncm if v['glyph'] in (0x241,0x242)],'nominal_native_pixel_work':mono*8+len(ncm)*32,'glyph_row_payload_bytes':mono+len(ncm)*8})
 return rows
def configuration(a,schema):
 r=a['registers'];mask=15 if a['scene']=='D' else 12
 expected={0xd031:(255,0xc0),0xd054:(255,0x55),0xd051:(0xc0,0),0xd058:(255,192),0xd059:(255,0),0xd05e:(255,96),0xd05a:(255,60),0xd05b:(255,1),0xd063:(255,0),0xd060:(255,0),0xd061:(255,0xe0),0xd062:(255,0),0xd064:(255,0),0xd065:(255,0),0xd068:(255,0),0xd069:(255,0x40),0xd06a:(255,0),0xd015:(255,mask),0xd01a:(16,0),0xd07b:(255,25),0xd06c:(255,0),0xd06d:(255,0x93),0xd06e:(255,0x80),0xd07a:(16,0),0xd05d:(128,0),0xd076:(255,255),0xd070:(255,0x9a),0xd01c:(255,0),0xd055:(255,0),0xd057:(255,0),0xd06b:(255,0)}
 failures=[{'address':f'${addr:04X}','mask':m,'expected':v,'actual':r[addr]} for addr,(m,v) in expected.items() if r[addr]&m!=v]
 for row in layout(a):
  y=row['row'];want={'A':(96,0,0),'B':(95,1,0) if y in (10,11) else (96,0,0),'C':(94,0,2),'D':(20,44,32)}[a['scene']]
  if (row['mono'],row['NCM'],row['GOTOX'])!=want:failures.append({'row':y,'expected_mono_NCM_GOTOX':want,'actual':(row['mono'],row['NCM'],row['GOTOX'])})
 spr=region(a,'sprites');scene_marker=hashlib.sha256(spr[128:192]).hexdigest()==schema['markers']['scene'][a['scene']]
 phase='PRE' if a['phase']=='PRE' else ('ERR' if a['measured_export_error'] else 'PST')
 phase_marker=hashlib.sha256(spr[192:256]).hexdigest()==schema['markers']['phase'][phase]
 if not scene_marker:failures.append({'marker':'scene sprite pattern mismatch'})
 if not phase_marker:failures.append({'marker':'phase sprite pattern mismatch'})
 shadows=region(a,'write_shadows')
 expected_shadows={0:31,1:a['D051_restore_shadow'],2:a['entry_IRQ_mask'],3:a['entry_IRQ_mask']&15,4:0x55,5:0xc0,6:mask,7:1 if a['phase']=='PRE' else 2,8:a['measured_export_error'],9:ord(a['scene']),10:a['sequence']&255,11:a['sequence']>>8&255,13:shadows[12]&0xef,14:0,15:0}
 if a['D051_write_shadow']!=31:failures.append({'write_shadow':'header D051 mismatch'})
 for i,want in expected_shadows.items():
  if shadows[i]!=want:failures.append({'write_shadow_byte':i,'expected':want,'actual':shadows[i]})
 return {'profile_E_constant_checks_pass':not failures,'failures':failures,'scene_marker_valid':scene_marker,'phase_marker_valid':phase_marker}
def summary(a,schema):
 out={k:v for k,v in a.items() if k not in ('regions','registers')}
 out['regions']=[{k:v for k,v in r.items() if k!='data'} for r in a['regions']]
 out['geometry']=geometry(a['registers']);out['geometry']['reference_HUD_native_X']=out['geometry'].pop('scene_HUD_GOTOX_native');out['geometry']['uses_GOTOX']=a['scene'] in 'CD';out['configuration']=configuration(a,schema);out['layout']=layout(a)
 sw=region(a,'write_shadows');out['write_shadow_values']={name:f'${sw[i]:02X}' for i,name in enumerate(['D051_write','D051_restore','entry_IRQ','own_IRQ','D054_write','D031_write','D015_write','phase','measured_error','scene','sequence_low','sequence_high','entry_D07A_read','D07A_write','reserved14','reserved15'])}
 out['palettes']=[{'bank':i,'sha256':hashlib.sha256(region(a,'palettes')[i*768:(i+1)*768]).hexdigest()} for i in range(4)]
 return out
def compare(a,b,schema,require_pair=False):
 pair=(a['scene'],a['platform_label'],a['sequence'])==(b['scene'],b['platform_label'],b['sequence']) and a['phase']!=b['phase']
 if require_pair and not pair:raise ValueError('PRE/POST pair scene/label/sequence mismatch')
 differences=[]
 for spec in schema['registers']:
  addr=spec['address'];l=a['registers'][addr];r=b['registers'][addr];mask=spec['compare_mask']
  if l==r:continue
  expected_sprite=(a['scene']!=b['scene'] and addr==0xd015 and (l^r)==3 and l==(15 if a['scene']=='D' else 12) and r==(15 if b['scene']=='D' else 12))
  differences.append({'address':f'${addr:04X}','name':spec['name'],'left':f'${l:02X}','right':f'${r:02X}','mask':f'${mask:02X}','stable_bits_differ':bool((l^r)&mask),'expected_scene_sprite_enable':expected_sprite})
 mem=[];marker_ok=configuration(a,schema)['phase_marker_valid'] and configuration(b,schema)['phase_marker_valid']
 for l,r in zip(a['regions'],b['regions']):
  diffs=[]
  for i,(v,w) in enumerate(zip(l['data'],r['data'])):
   if v==w:continue
   phase_expected=a['scene']==b['scene'] and a['phase']!=b['phase'] and ((l['name']=='sprites' and 192<=i<256 and marker_ok) or (l['name']=='write_shadows' and i==7 and (v,w)==((1 if a['phase']=='PRE' else 2),(1 if b['phase']=='PRE' else 2))))
   diffs.append({'offset':i,'source_address':f"${l['address']+i:07X}",'left':v,'right':w,'declared_phase_annotation':phase_expected})
  mem.append({'name':l['name'],'source_address':l['address'],'bytes':l['length'],'left_sha256':l['sha256'],'right_sha256':r['sha256'],'different_bytes':len(diffs),'non_annotation_different_bytes':sum(not d['declared_phase_annotation'] for d in diffs),'first64_differences':diffs[:64]})
 return {'left':summary(a,schema),'right':summary(b,schema),'is_matching_PRE_POST_pair':pair,'register_differences':differences,
  'unexpected_stable_register_differences':[d for d in differences if d['stable_bits_differ'] and not d['expected_scene_sprite_enable']],
  'volatile_phase_context':{'left':a['phase_context'],'right':b['phase_context'],'different':a['phase_context']!=b['phase_context']},
  'memory_comparison':mem,'non_annotation_different_bytes':sum(x['non_annotation_different_bytes'] for x in mem),
  'interpretation':'Labels are manual, verify provenance. Across scenes screen/layout/scene-marker changes are intentional but raw differences stay visible. Equal snapshots do not prove equal internal FIFO/render timing.'}
def load(path,name=None,phase=None,schema=None):
 data=path.read_bytes()
 if name:return disk_file(data,name)
 if data.startswith(b'VYDG1B1B'):return data
 if len(data)==0x60000:
  if phase not in ('PRE','POST'):raise ValueError('Full384KiB RAM input requires --left-phase/--right-phase')
  return b''.join(data[r['address']:r['address']+r['length']] for r in schema['buffers'][phase])
 rows=re.findall(rb':([0-9A-Fa-f]{8}):([0-9A-Fa-f]{32})',data)
 if rows:
  if phase not in ('PRE','POST'):raise ValueError('UART text input requires --left-phase/--right-phase')
  memory={int(addr,16)+i:v for addr,hexbytes in rows for i,v in enumerate(bytes.fromhex(hexbytes.decode()))}
  try:return bytes(memory[addr] for r in schema['buffers'][phase] for addr in range(r['address'],r['address']+r['length']))
  except KeyError as e:raise ValueError(f'Missing UART RAM byte {e}')
 return data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('left',type=Path);p.add_argument('right',type=Path,nargs='?');p.add_argument('--left-file');p.add_argument('--right-file');p.add_argument('--left-phase',choices=['PRE','POST']);p.add_argument('--right-phase',choices=['PRE','POST']);p.add_argument('--schema',type=Path,default=DEFAULT);p.add_argument('--pair',action='store_true');p.add_argument('--json',type=Path);a=p.parse_args()
 try:
  schema=json.loads(a.schema.read_text());l=parse(load(a.left,a.left_file,a.left_phase,schema),schema)
  r=compare(l,parse(load(a.right,a.right_file,a.right_phase,schema),schema),schema,a.pair) if a.right else summary(l,schema)
 except (ValueError,OSError,KeyError,StopIteration) as e:p.error(str(e))
 text=json.dumps(r,indent=2)+'\n'
 if a.json:a.json.write_text(text)
 else:print(text,end='')
if __name__=='__main__':main()
