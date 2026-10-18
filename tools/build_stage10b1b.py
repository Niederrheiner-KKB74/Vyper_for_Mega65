#!/usr/bin/env python3
"""Offline Stage10b1b build. Existing diagnostic and engine files are read-only."""
import argparse,hashlib,json,shutil,struct,subprocess,tempfile
from pathlib import Path
import build_stage10b1a as P
import build_stage3b1 as D
from diagnostic_baseline import protect
ROOT=Path(__file__).resolve().parents[1]
BASE='17d329f2ce7f002bd20df3441ec30d564dd64cb3'
REGS=P.REGS
RESTORE=sorted(set(P.RESTORE+list(range(4,8))+[0x29,0x2a]))
def sc(s):return P.sc(s)
def text_cells():
 hud=['HUD X240-319','COMMON PROFILE E','PALEMU0 DBLRR0','NORRDEL0','STRIDE192 COUNT96','MONO FONT4000','PIXIE X224 Y80','H/E MEASURE','S SAVE POST','X EXIT BASIC','FIXED HUD START','CAPTURE PALETTES','NO ENGINE CHANGE','1 TEXT ONLY','2 TEXT + PIXIE','3 TEXT + GOTOX','4 FULL REFERENCE','H LABEL HARDWARE','E LABEL XEMU','PRE BEFORE H/E','PST PHOTO THEN S','END NEXT SCENE','SAVING CHANGES IO','PAL 80X25 START','READ TEST GUIDE']
 lines=[]
 for y in range(25):
  left=('+'+'-'*58+'+') if y in (0,24) else ('I'+' '*58+'I')
  if y in (3,5,7,9,13,15,17,19,21):
   msg={3:'10B1B ORDINARY TEXT / FIXED PROFILE E',5:'PLAYFIELD X0-239 Y0-199',7:'CHARACTER WIDTH 4 LOGICAL PIXELS',9:'NCM TEST RESERVED AT X224 Y80',13:'GOTOX TEST TARGET 0 AND480 NATIVE',15:'SPRITE LABEL AT UPPER LEFT',17:'SAME SCREEN AND FONT ADDRESSES',19:'HARDWARE AND XEMU USE SAME PRG',21:'DO NOT CHANGE OTHER PARAMETERS'}[y]
   left='I '+msg.ljust(56)[:56]+' I'
  if y in (10,11):left=left[:56]+' '*4
  lines.append((left+hud[y].ljust(20)[:20]))
 return [list(sc(x)) for x in lines]
def cells_for(scene,lines):
 rows=[]
 for y,line in enumerate(lines):
  if scene=='A':words=[(c,0,1) for c in line]+[(32,0,1)]*16
  elif scene=='B':
   words=([(c,0,1) for c in line[:56]]+[(0x241+y-10,8,0x10)]+[(c,0,1) for c in line[60:]]+[(32,0,1)]*19) if y in (10,11) else [(c,0,1) for c in line]+[(32,0,1)]*16
  else:words=[(0,0x10,0)]+[(c,0,1) for c in line[:60]]+[(480,0x10,0)]+[(c,0,1) for c in line[60:]]+[(32,0,1)]*14
  assert len(words)==96;rows.append(words)
 return rows
def pack(rows):
 return (b''.join(struct.pack('<H',v) for row in rows for v,f,c in row),bytes(t for row in rows for v,f,c in row for t in (f,c)))
def assets(w):
 old=P.assets(w);lines=text_cells();(w/'scene_text.bin').write_bytes(bytes(c for row in lines for c in row))
 full_screen=bytearray((w/'scene_screen.bin').read_bytes());full_colour=(w/'scene_colour.bin').read_bytes()
 hud=['10B1B FULL REFERENCE','PLAYFIELD X0-239','HUD X240-319','H640 X480=HUD','STRIDE192 /96','RRB AT224,80','SPR0 AT112,112','SHOT AT232,64','SPR=CHAR+2X-3','Y=CHARY+2Y','1 TEXT ONLY','2 TEXT + PIXIE','3 TEXT + GOTOX','4 FULL REFERENCE','H/E MEASURE','S SAVE POST','X EXIT BASIC','PAL 80X25 START','PALEMU0 DBLRR0','NORRDEL0','PST PHOTO THEN S','PRE BEFORE H/E','END NEXT SCENE','CHECK BOTH FILES','NO ENGINE CHANGE']
 for y,t in enumerate(hud):
  for x,c in enumerate(sc(t.ljust(20)[:20])):struct.pack_into('<H',full_screen,y*192+44+2*x,c)
 (w/'scene_screen.bin').write_bytes(full_screen)
 rowsD=[]
 for y in range(25):rowsD.append([(struct.unpack_from('<H',full_screen,y*192+x*2)[0],full_colour[y*192+x*2],full_colour[y*192+x*2+1]) for x in range(96)])
 budget={}
 for scene in 'ABCD':
  rows=rowsD if scene=='D' else cells_for(scene,lines);scr,col=pack(rows)
  (w/f'scene_{scene}_screen.bin').write_bytes(scr);(w/f'scene_{scene}_colour.bin').write_bytes(col)
  stats=[]
  for y,row in enumerate(rows):
   cmd=sum(bool(f&16) for v,f,c in row);ncm=sum(not f&16 and bool(f&8) for v,f,c in row);mono=96-cmd-ncm
   stats.append({'row':y,'entries':96,'GOTOX':cmd,'NCM':ncm,'mono':mono,'nominal_native_pixel_work':ncm*32+mono*16,'glyph_row_payload_bytes':ncm*8+mono,'screen_bytes':192,'colour_bytes':192,'note':'H640/scale60: mono16 and NCM32 native pixels before clipping; not measured FPGA cycles. Historical scene labels retain their documented geometry mistakes.'})
  budget[scene]=stats
 (w/'scene_budget.json').write_text(json.dumps(budget,indent=2)+'\n')
 font=(w/'font.bin').read_bytes();letters=bytearray();phases=bytearray()
 for c in 'ABCD':
  sprite=bytearray(64)
  for y,v in enumerate(font[(ord(c)-64)*8:(ord(c)-64)*8+8]):
   bits=sum((7<<(3*(7-x))) for x in range(8) if v&(128>>x))
   for dy in range(2):sprite[(2*y+dy)*3:(2*y+dy+1)*3]=bits.to_bytes(3,'big')
  letters+=sprite
 for text in ['PRE','PST','END','ERR']:
  sprite=bytearray(64)
  for y in range(8):
   for dy in range(2):sprite[(2*y+dy)*3:(2*y+dy+1)*3]=bytes(font[(ord(c)-64)*8+y] for c in text)
  phases+=sprite
 (w/'scene_markers.bin').write_bytes(letters);(w/'phase_markers.bin').write_bytes(phases)
 (w/'sprites.bin').write_bytes((w/'sprites.bin').read_bytes()+bytes(128))
 regions=[('screen',0xe000,4800),('colour',0xff80000,4800),('font',0x4000,2048),('grid',0x18000,24000),('pixie',0x9040,128),('sprites',0x9200,256),('pointers',0x9300,8),('guards',0x8000,64),('guard2',0x90c0,64),('palettes',0x5400,3072),('write_shadows',0x4800,16),('screen_next_row',0xf2c0,192),('colour_next_row',0xff812c0,192)]
 offset=768;descs=[]
 for name,addr,n in regions:descs.append({'name':name,'address':addr,'offset':offset,'length':n});offset+=n
 schema={'magic':'VYDG1B1B','version':1,'base':BASE,'registers':old['registers'],'register_offset':48,'context_offset':32,'directory_offset':48+3*len(REGS),'header_size':768,'dump_size':offset,'buffers':{'PRE':[{'address':0x50000,'offset':0,'length':offset}],'POST':[{'address':0x48000,'offset':0,'length':32768},{'address':0x5a000,'offset':32768,'length':offset-32768}]},'regions':descs,'checksum':'CRC16-CCITT-FALSE initFFFF polynomial1021; bytes28/29 treated as zero','phase_marker':{'region':'sprites','offset':192,'length':64},'shadow_phase':{'region':'write_shadows','offset':7,'length':1},'markers':{'scene':{c:hashlib.sha256(letters[i*64:(i+1)*64]).hexdigest() for i,c in enumerate('ABCD')},'phase':{c:hashlib.sha256(phases[i*64:(i+1)*64]).hexdigest() for i,c in enumerate(['PRE','PST','END','ERR'])}},'palette_source':{'mirror':0x5400,'hardware_windows':[0xd100,0xd200,0xd300],'banks':4,'layout':'bank0..3, each R256/G256/B256; mapped selector only changes during readback'},'platform_label':'manual only; use confirmed provenance','target_core':'aaf4542','target_xemu':'20260129235930'}
 (w/'registers.json').write_text(json.dumps(schema,indent=2)+'\n')
 h=bytearray(768);h[:8]=b'VYDG1B1B';h[8:12]=bytes([1,65,85,1]);struct.pack_into('<HHI',h,12,len(REGS),len(regions),offset);h[24:28]=bytes([31,31,0,0]);h[30:32]=bytes([2,1])
 for i,a in enumerate(REGS):struct.pack_into('<HB',h,48+3*i,a,0)
 for i,r in enumerate(descs):struct.pack_into('<IIIHH',h,schema['directory_offset']+16*i,r['address'],r['offset'],r['length'],0,0)
 (w/'snapshot_header.bin').write_bytes(h)
 (w/'constants.inc').write_text(f'.const REG_COUNT={len(REGS)}\n.const REGION_COUNT={len(regions)}\n.const SNAPSHOT_SIZE={offset}\n.const RESTORE_COUNT={len(RESTORE)}\n')
 tables={'reg_lo':[x&255 for x in REGS],'reg_hi':[x>>8 for x in REGS],'restore_regs':RESTORE}
 for label,fn in [('ms_lo',lambda r:r['address']&255),('ms_hi',lambda r:r['address']>>8&255),('ms_bank',lambda r:r['address']>>16&15),('ms_mb',lambda r:r['address']>>20&255),('md_lo',lambda r:r['offset']&255),('md_hi',lambda r:r['offset']>>8),('ml_lo',lambda r:r['length']&255),('ml_hi',lambda r:r['length']>>8)]:tables[label]=[fn(r) for r in descs]
 (w/'tables.inc').write_text('\n'.join(k+': .byte '+','.join(str(x) for x in v) for k,v in tables.items())+'\n')
 names=[]
 for ext in ['PRE','PST']:
  for scene in 'ABCD':
   for platform in 'HX':names.append(f'V1B{scene}{platform}.{ext}')
 ns=[]
 for key,prefix,suffix in [('name','0:',',S,W'),('scratch','S0:','')]:
  for byte,op in [('lo','<'),('hi','>')]:ns.append(f'{key}_{byte}: .byte '+','.join(op+f'{key}_{i}' for i in range(16)))
  ns.extend(f'{key}_{i}: .text "{prefix}{name}{suffix}"' for i,name in enumerate(names))
 (w/'names.inc').write_text('\n'.join(ns)+'\n')
 # Remove inherited generated interfaces not used by this independent format.
 for name in ['memory.json','memory.inc','memory_constants.inc','memory_header.bin','registers.inc']:(w/name).unlink()
 return schema

def build(jar,out):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=D.KICKASS_SHA256:raise ValueError('Expected pinned KickAssembler5.25')
 out=protect(out)
 with tempfile.TemporaryDirectory(prefix='stage10b1b-') as d:
  w=Path(d);schema=assets(w);shutil.copyfile(ROOT/'src/tests/stage10b1b.asm',w/'stage10b1b.asm');shutil.copyfile(ROOT/'src/tests/stage10b1b_helpers.asm',w/'stage10b1b_helpers.asm')
  run=subprocess.run(['java','-jar',str(jar),'stage10b1b.asm','-o','STAGE10B1B.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (w/'assembly.txt').write_text('\n'.join(x.rstrip() for x in run.stdout.replace(str(w),'.').splitlines())+'\n')
  if run.returncode:raise RuntimeError(run.stdout)
  prg=(w/'STAGE10B1B.PRG').read_bytes();entries=[('STAGE10B1B',prg,0x82)];disk=bytearray(D.build_disk(entries));disk[((40-1)*40)*256+4:((40-1)*40)*256+20]=b'VYPER 10B1B DIAG'.ljust(16,b'\xa0');disk=bytes(disk);D.verify_disk(disk,entries);(w/'VYPER_STAGE10B1B.d81').write_bytes(disk)
  (w/'build.json').write_text(json.dumps({'stage':'10b1b','base':BASE,'stable':False,'schema':schema,'hardware':'NOT_RUN','exact_target_xemu':'NOT_RUN'},indent=2)+'\n')
  out.mkdir(parents=True,exist_ok=True);files={p.name:p.read_bytes() for p in w.iterdir() if p.is_file()}
  for name,data in files.items():(out/name).write_bytes(data)
  (out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(b).hexdigest()}  {name}\n' for name,b in sorted(files.items())))
  print('Built',len(prg),'PRG bytes,',len(disk),'D81 bytes;',schema['dump_size'],'bytes per PRE/POST snapshot')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kickass',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'build/diagnostics/stage10b1b');a=p.parse_args();build(a.kickass.resolve(),a.output)
