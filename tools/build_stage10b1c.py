#!/usr/bin/env python3
"""Offline isolated Stage10b1c H640/H320 test. Old sources/assets/releases are protected."""
import argparse,hashlib,json,shutil,struct,subprocess,tempfile
from pathlib import Path
import build_stage10b1 as P
import build_stage10b1b as B
import build_stage3b1 as D
ROOT=Path(__file__).resolve().parents[1]
BASE='fd6214c1c6be1adcedea095b0ebd474288a83403'
COUNT,STRIDE=48,96
PROBES={2:0,3:40,4:80,5:120,6:160,7:200,8:240,20:304,21:319,22:320}
PIXIES=[(32,80),(112,104),(224,128)]
RESTORE=B.RESTORE

def gotox(x,mode):
 if not 0<=x<=320 or mode not in 'AB':raise ValueError('Invalid logical X or mode')
 return x*2 if mode=='A' else x

def predict(x,mode,renderer):
 raw=gotox(x,mode)
 if renderer=='XEMU':return raw if mode=='A' else raw*2
 if renderer=='FPGA_SOURCE_MODEL':return raw*2
 raise ValueError('Unknown renderer')

def assets(w):
 old=P.assets(w)
 # Discard unrelated generated predecessor interfaces; retain only actual assets.
 for n in ['registers.json','registers.inc','constants.inc']:(w/n).unlink()
 font=(w/'font.bin').read_bytes()
 markers=bytearray()
 for ch in 'AB':
  b=bytearray(64)
  for y,v in enumerate(font[(ord(ch)-64)*8:(ord(ch)-64)*8+8]):
   bits=sum(7<<(3*(7-x)) for x in range(8) if v&(128>>x))
   for dy in (0,1):b[(2*y+dy)*3:(2*y+dy+1)*3]=bits.to_bytes(3,'big')
  markers+=b
 (w/'variant_markers.bin').write_bytes(markers)
 noio=bytearray(64)
 # 3 letters NO I/O represented by "NIO", spelled out in guide. No scene text dependency.
 for y in range(8):
  for dy in (0,1):noio[(y*2+dy)*3:(y*2+dy+1)*3]=bytes(font[(ord(c)-64)*8+y] for c in 'NIO')
 (w/'sprites.bin').write_bytes((w/'sprites.bin').read_bytes()+bytes(64)+noio)
 # White single logical pixel at left, 15 transparent pixels.
 (w/'probe.bin').write_bytes(bytes([1,0,0,0,0,0,0,0])*8)
 hud=['10B1C','HUD X240','WIDTH 10','G0 X000','G1 X040','G2 X080','G3 X120','G4 X160','G5 X200','G6 X240','RRB X032','Y080','RRB X112','Y104','RRB X224','Y128','SPR X112','Y160','SHOT X224','Y176','G7 X304','G8 X319','G9 X320','1=A 2=B','R D X']
 for y,x in PROBES.items():hud[y]=f'GOTO X{x:03d}'
 rows=[];patches=[];raw_model=[]
 for y in range(25):
  words=[]
  def go(x,transparent=False):
   slot=len(words);patches.append((y*STRIDE+slot*2,x));words.append((gotox(x,'A'),0x90 if transparent else 0x10,0));raw_model.append({'row':y,'slot':slot,'logical_x':x,'A_word':gotox(x,'A'),'B_word':gotox(x,'B'),'transparent_overlay':transparent})
  go(0)
  words.extend((0x600+y*15+x,8,0x30) for x in range(15))
  go(240)
  words.extend((c,0,1) for c in P.sc(hud[y].ljust(10)[:10]))
  for x,py in PIXIES:
   if y in (py//8,py//8+1):
    go(x,True);words.append((0x241+y-py//8,8,0x10))
  if y in PROBES:
   go(PROBES[y],True);words.append((0x8100//64,8,0x30))
  go(320,True)
  # Padding GOTOX commands only: do not repeatedly paint glyphs or return to screen.
  while len(words)<COUNT:go(320,True)
  if len(words)!=COUNT:raise ValueError('Scene exceeds fixed row capacity')
  rows.append(words)
 for mode in 'AB':
  scr=bytearray();col=bytearray()
  for row in rows:
   for v,f,c in row:scr+=struct.pack('<H',v);col+=bytes((f,c))
  for off,x in patches:struct.pack_into('<H',scr,off,gotox(x,mode))
  (w/f'scene_{mode}_screen.bin').write_bytes(scr)
 (w/'scene_screen.bin').write_bytes((w/'scene_A_screen.bin').read_bytes())
 (w/'scene_colour.bin').write_bytes(col)
 tables={'reg_lo':[r&255 for r in P.REGS],'reg_hi':[r>>8 for r in P.REGS],'restore_regs':RESTORE,
  'patch_lo':[(0xa000+o)&255 for o,x in patches],'patch_hi':[(0xa000+o)>>8 for o,x in patches]}
 # More than255 commands are processed in multiple groups below, not an8bit count.
 for mode in 'AB':
  for name,fn in [('lo',lambda v:v&255),('hi',lambda v:v>>8)]:tables[f'goto_{mode.lower()}_{name}']=[fn(gotox(x,mode)) for off,x in patches]
 # Tables are grouped into chunks <=255 by generated unrolled routines.
 lines=[]
 for name,values in tables.items():lines.append(name+': .byte '+','.join(map(str,values)))
 (w/'tables.inc').write_text('\n'.join(lines)+'\n')
 (w/'constants.inc').write_text(f'.const REG_COUNT={len(P.REGS)}\n.const RESTORE_COUNT={len(RESTORE)}\n.const SNAPSHOT_SIZE={32+3*len(P.REGS)}\n.const PATCH_COUNT={len(patches)}\n')
 schema={'stage':'10b1c','base':BASE,'count':COUNT,'stride':STRIDE,'rows':25,'screen':0xe000,'colour':0xff80000,'source':0xa000,
  'snapshot_address':0x4800,'snapshot_size':32+3*len(P.REGS),'snapshot_magic':'VYDG1B1C','registers':old['registers'],
  'A':{'D031':0xc0,'D05A':60,'GOTOX':'logical X times2'},'B':{'D031':0x40,'D05A':120,'GOTOX':'logical X unchanged; no ASL'},
  'common':{'D054':0x55,'D051_write':31,'D07A_write':0,'D079_write':0,'D053_output_bits':0,'D01A_write':0,'D05B':1,'CHARX':80,'CHARY':104,'D070':0x9a,'glyph_native_width':{'mono':16,'NCM':32},'sprite_H640':True},
  'HUD':{'logical_x':240,'characters':10,'logical_width':80},'RRB_pixies':PIXIES,'hardware_sprite':{'logical_x':112,'logical_y':160,'raw_X':301,'raw_Y':424},'hardware_projectile':{'logical_x':224,'logical_y':176,'raw_X':525,'raw_Y':456},
  'probes':[{'row':y,'logical_x':x,'A_word':gotox(x,'A'),'B_word':gotox(x,'B'),'XEMU_A_native':predict(x,'A','XEMU'),'FPGA_A_native_hypothesis':predict(x,'A','FPGA_SOURCE_MODEL'),'B_both_native_hypothesis':predict(x,'B','FPGA_SOURCE_MODEL')} for y,x in PROBES.items()],
  'commands':raw_model,'patch_count':len(patches),'scene_marker':'sprite2 A/B','io_marker':'sprite3 NIO; no active-scene KERNAL calls','hardware':'NOT_RUN','exact_target_xemu':'NOT_RUN'}
 (w/'scene.json').write_text(json.dumps(schema,indent=2)+'\n')
 return schema

def build(jar,out):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=D.KICKASS_SHA256:raise ValueError('Expected pinned KickAssembler5.25')
 for p in subprocess.check_output(['git','diff',BASE,'--name-only','--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines():
  if subprocess.run(['git','cat-file','-e',BASE+':'+p],cwd=ROOT,stderr=subprocess.DEVNULL).returncode==0:raise ValueError('Protected baseline changed: '+p)
 with tempfile.TemporaryDirectory(prefix='stage10b1c-') as d:
  w=Path(d);s=assets(w);shutil.copyfile(ROOT/'src/tests/stage10b1c.asm',w/'stage10b1c.asm')
  run=subprocess.run(['java','-jar',str(jar),'stage10b1c.asm','-o','STAGE10B1C.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (w/'assembly.txt').write_text('\n'.join(v.rstrip() for v in run.stdout.replace(str(w),'.').splitlines())+'\n')
  if run.returncode:raise RuntimeError(run.stdout)
  prg=(w/'STAGE10B1C.PRG').read_bytes();entries=[('STAGE10B1C',prg,0x82)];disk=bytearray(D.build_disk(entries));disk[((40-1)*40)*256+4:((40-1)*40)*256+20]=b'VYPER 10B1C TEST'.ljust(16,b'\xa0');D.verify_disk(bytes(disk),entries);(w/'VYPER_STAGE10B1C.d81').write_bytes(disk)
  (w/'build.json').write_text(json.dumps({'stage':'10b1c','base':BASE,'stable':False,'PRG_bytes':len(prg),'D81_bytes':len(disk),'hardware':'NOT_RUN','exact_target_xemu':'NOT_RUN'},indent=2)+'\n')
  out.mkdir(parents=True,exist_ok=True);files={p.name:p.read_bytes() for p in w.iterdir() if p.is_file()}
  for name,data in files.items():(out/name).write_bytes(data)
  (out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())))
  print('Built',len(prg),'PRG bytes;',len(disk),'D81 bytes;',len(s['commands']),'GOTOX patches')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kickass',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'releases/stage_10b1c');a=p.parse_args();build(a.kickass.resolve(),a.output)
