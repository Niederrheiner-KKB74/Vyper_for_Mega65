#!/usr/bin/env python3
"""Offline reproducible standalone VIC-IV diagnostics. Never changes Stage10a1 and Stage10b1."""
import argparse,hashlib,json,shutil,subprocess,tempfile,struct,csv
from pathlib import Path
import build_stage3b1 as D
from diagnostic_baseline import protect
ROOT=Path(__file__).resolve().parents[1]
BASE='6fd56b3000d56c8c0a6d274d3076de72b62be523'
# Read only: omit collision latches D01E/F and write-only KEY. No CIA ICR reads.
REGS=list(range(0xd000,0xd080));REGS=[a for a in REGS if a not in (0xd01e,0xd01f,0xd02f)]
REGS+=[0xd08f]
REGS+=list(range(0xd700,0xd710))+[0xd71c,0xd720,0xd740,0xdd00,0xdd02,0xdc0e,0xdc0f]+list(range(0xd629,0xd636))
NAMES={0xd08f:'HWERRATA opt-in level (read only in this test)',0xd07c:'bitplane bank / sync / debug controls',0xd030:'ROM/RAM/CRAM2K',0xd031:'H640 FAST ATTR BPM V400 H1280 MONO INT',0xd048:'border top low',0xd049:'border top high / bitplanes',0xd04a:'border bottom low',0xd04b:'border bottom high / bitplanes',0xd04c:'CHARX low',0xd04d:'CHARX high / sprite tiles',0xd04e:'CHARY low',0xd04f:'CHARY high / sprite tiles',0xd050:'horizontal raster low',0xd051:'horizontal raster high / DBLRR NORRDEL',0xd052:'physical raster low',0xd053:'physical raster high / output controls',0xd054:'ALPHEN VFAST PALEMU SPRH640 SMTH FCLRHI FCLRLO CHR16',0xd055:'sprite variable height enable',0xd056:'sprite variable height',0xd057:'sprite 64 width enable',0xd058:'LINESTEP low',0xd059:'LINESTEP high',0xd05a:'CHRXSCL source pixels /120',0xd05b:'CHRYSCL physical rasters minus1',0xd05c:'side border low',0xd05d:'HOTREG raster delay side border high',0xd05e:'CHRCOUNT low',0xd05f:'sprite X bit9',0xd063:'screen high / count high / FCM / hyperram',0xd064:'colour offset low',0xd065:'colour offset high',0xd068:'CHARPTR low',0xd069:'CHARPTR middle',0xd06a:'CHARPTR high',0xd06b:'FCM sprites enable',0xd06c:'sprite pointer low',0xd06d:'sprite pointer middle',0xd06e:'sprite pointer high /16bit enable',0xd06f:'PAL/NTSC RASLINE0 output timing',0xd070:'palette banks',0xd076:'sprite V400 enable',0xd077:'sprite Y bit8',0xd078:'sprite Y bit9',0xd079:'raster compare low',0xd07a:'raster compare high / CHARY16 / mode',0xd07b:'display last row index'}
VOL={0xd07c:0x3f,0xd07d:0,0xd07e:0,0xd07f:0,0xd011:0x7f,0xd012:0,0xd013:0,0xd014:0,0xd019:0,0xd050:0,0xd051:0xc0,0xd052:0,0xd053:0xe0,0xd700:0,0xd701:0,0xd702:0,0xd703:0,0xd704:0,0xd705:0,0xd706:0,0xd707:0,0xd708:0,0xd709:0,0xd70a:0,0xd70b:0,0xd70c:0,0xd70d:0,0xd70e:0,0xd70f:0}
# D040..47 and D071..75 are context/extension fields: retain raw, do not
# attribute cross-machine differences to geometry without the cited core map.
for a in list(range(0xd040,0xd048))+list(range(0xd071,0xd076)):VOL[a]=0
RESTORE=[*range(0,4),0x10,0x15,0x17,0x1b,0x1c,0x1d,0x20,0x21,0x27,0x28,0x30,*range(0x48,0x50),*range(0x54,0x60),*range(0x60,0x66),*range(0x68,0x6f),0x70,0x76,0x77,0x78,0x79,0x7a,0x7b]
RESTORE.remove(0x5d)
def sc(t):return bytes(ord(c)-64 if 64<=ord(c)<=95 else ord(c) for c in t)
def assets(w):
 screen=bytearray();colour=bytearray()
 hud=['A 10B1A NORRDEL','PLAYFIELD X0-239','HUD X240-319','H640 X480=HUD','STRIDE192 /96','RRB AT224,80','SPR0 AT112,112','SHOT AT232,64','SPR=CHAR+2X-3','Y=CHARY+2Y','1 A NORRDEL 1','2 B NORRDEL 0','H EXPORT HARDWARE','E EXPORT XEMU','X EXIT BASIC','PAL 80X25 START','0.97 AAF4542','XEMU20260129235930','KEEP SAME ROM','SEE README','GRID16X8','WHITE FRAME','RED RIGHT EDGE','CHECK DUMP FILE','NO ENGINE CHANGE']
 for row in range(25):
  words=[(0,0x10,0)]+[(0x600+row*15+x,8,0x30) for x in range(15)]
  while len(words)<21:words.append((640 if len(words)%2==0 else 0x200,0x10 if len(words)%2==0 else 8,0))
  words.append((480,0x10,0));words += [(c,0,1) for c in sc(hud[row].ljust(20)[:20])]
  assert len(words)==42
  words += [(640 if i%2==0 else 0x200,0x10 if i%2==0 else 8,0) for i in range(54)]
  if row in (10,11):words[42:44]=[(448,0x10,0),(0x241+row-10,8,0x10)]
  for val,lo,hi in words:screen+=struct.pack('<H',val);colour+=bytes((lo,hi))
 (w/'scene_screen.bin').write_bytes(screen);(w/'scene_colour.bin').write_bytes(colour)
 atlas=bytearray()
 for flags in range(16):
  for y in range(8):
   pixels=[]
   for x in range(16):
    v=3 if x==0 or y==0 else 0
    if (flags&1 and x==0) or (flags&4 and y==0) or (flags&8 and y==7):v=1
    if flags&2 and x==15:v=2
    pixels.append(v)
   atlas+=bytes(pixels[x]|pixels[x+1]<<4 for x in range(0,16,2))
 (w/'grid_atlas.bin').write_bytes(atlas)
 sprite=bytearray(128)
 for y in range(16):
  bits=0xffff if y in (0,15) else 0x8181
  sprite[y*3:y*3+2]=bits.to_bytes(2,'big')
 for y in range(8):sprite[64+y*3]=0xc0 #2native x8physical =1x4logical
 (w/'sprites.bin').write_bytes(sprite)
 (w/'font.bin').write_bytes((ROOT/'releases/stage_10a/stage10a1/menu_font.bin').read_bytes())
 for f in ('player_ncm.bin','player_palette_r.bin','player_palette_g.bin','player_palette_b.bin'):shutil.copyfile(ROOT/'assets/player'/f,w/f)
 regs=[{'address':a,'name':NAMES.get(a,f'register ${a:04X}'),'compare_mask':VOL.get(a,255),'phase_order':[1,2,3,4]} for a in REGS]
 block=4+3*len(REGS);size=32+4*block
 schema={'magic':'VYDG1B1A','version':1,'base':BASE,'registers':regs,'block_size':block,'dump_size':size,'buffer':0x4800,'checksum':'sum16 excluding bytes28/29','target_core':'aaf4542d02679271b5fb84ad933cc39bbe091c3f','target_xemu_release':'20260129235930','initial_conditions':'same ROM, PAL80x25; user confirmed','automatic_identity':'raw D629..D635 only; target versions are NOT detected versions'}
 (w/'registers.json').write_text(json.dumps(schema,indent=2)+'\n')
 schema['variant_marker']={'physical_address':0xe02c,'region':'screen','offset':44,'values':{'A':1,'B':2}}
 schema['baseline_profile']='E: PALEMU0 DBLRR0'
 memory_assets(w,schema)
 (w/'registers.json').write_text(json.dumps(schema,indent=2)+'\n')
 lines=[f'.const REG_COUNT={len(REGS)}',f'.const BLOCK_SIZE={block}',f'.const DUMP_SIZE={size}','reg_lo: .byte '+','.join(f'${a&255:02x}' for a in REGS),'reg_hi: .byte '+','.join(f'${a>>8:02x}' for a in REGS),'restore_regs: .byte '+','.join(f'${a:02x}' for a in RESTORE),f'.const RESTORE_COUNT={len(RESTORE)}','block_lo: .byte '+','.join(f'<(DUMP+32+{i}*BLOCK_SIZE)' for i in range(4)),'block_hi: .byte '+','.join(f'>(DUMP+32+{i}*BLOCK_SIZE)' for i in range(4))]
 (w/'constants.inc').write_text('\n'.join(x for x in lines if x.startswith('.const'))+'\n')
 (w/'registers.inc').write_text('\n'.join(x for x in lines if not x.startswith('.const'))+'\n')
 return schema


def memory_assets(w,schema):
 regions=[('screen',0xe000,4800),('colour',0xff80000,4800),('font',0x4000,2048),('grid',0x18000,24000),('pixie',0x9040,128),('sprites',0x9200,128),('pointers',0x9300,4),('guards',0x8000,64),('guard2',0x90c0,64)]
 offset=256;descs=[]
 for name,addr,n in regions:
  descs.append({'name':name,'address':addr,'offset':offset,'length':n});offset+=n
 mem={'magic':'VYMM1B1A','version':1,'buffer':0x50000,'size':offset,'header_size':256,'regions':descs,'checksum':'sum16 excluding28/29','variant_marker':schema['variant_marker']}
 schema['memory']=mem
 (w/'memory.json').write_text(json.dumps(mem,indent=2)+'\n')
 header=bytearray(256);header[:8]=b'VYMM1B1A';header[8:12]=bytes([1,65,85,len(regions)]);struct.pack_into('<HHI',header,12,16,256,offset);header[30:32]=bytes([1,4])
 for i,r in enumerate(descs):struct.pack_into('<IIIHH',header,32+i*16,r['address'],r['offset'],r['length'],0,0)
 (w/'memory_header.bin').write_bytes(header)
 lines=[f'.const MEM_SIZE={offset}',f'.const REGION_COUNT={len(regions)}']
 for label,fn in [('ms_lo',lambda r:r['address']&255),('ms_hi',lambda r:r['address']>>8&255),('ms_bank',lambda r:r['address']>>16&15),('ms_mb',lambda r:r['address']>>20&255),('md_lo',lambda r:r['offset']&255),('md_hi',lambda r:r['offset']>>8),('ml_lo',lambda r:r['length']&255),('ml_hi',lambda r:r['length']>>8)]:
  lines.append(label+': .byte '+','.join(str(fn(r)) for r in descs))
 (w/'memory.inc').write_text('\n'.join(x for x in lines if not x.startswith('.const'))+'\n')
 (w/'memory_constants.inc').write_text('\n'.join(x for x in lines if x.startswith('.const'))+'\n')

def build(jar,out):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=D.KICKASS_SHA256:raise ValueError("Expected pinned official KickAssembler5.25")
 out=protect(out)
 with tempfile.TemporaryDirectory(prefix='stage10b1a-') as d:
  w=Path(d);schema=assets(w)
  shutil.copyfile(ROOT/'src/tests/stage10b1a.asm',w/'stage10b1a.asm')
  run=subprocess.run(['java','-jar',str(jar),'stage10b1a.asm','-o','STAGE10B1A.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (w/'assembly.txt').write_text('\n'.join(line.rstrip() for line in run.stdout.replace(str(w),'.').splitlines())+'\n')
  if run.returncode:raise RuntimeError(run.stdout)
  prg=(w/'STAGE10B1A.PRG').read_bytes();entries=[('STAGE10B1A',prg,0x82)];disk=bytearray(D.build_disk(entries))
  disk[((40-1)*40)*256+4:((40-1)*40)*256+20]=b'VYPER 10B1A DIAG'.ljust(16,b'\xa0')
  disk=bytes(disk);D.verify_disk(disk,entries)
  (w/'VYPER_STAGE10B1A.d81').write_bytes(disk)
  (w/'build.json').write_text(json.dumps({'stage':'10b1a','base':BASE,'stable':False,'schema':schema,'XEMU':'not run by builder','hardware':'NOT_RUN'},indent=2)+'\n')
  out.mkdir(parents=True,exist_ok=True)
  files={p.name:p.read_bytes() for p in w.iterdir() if p.is_file()}
  for name,data in files.items():(out/name).write_bytes(data)
  (out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(files.items())))
  print('Built',len(prg),'PRG bytes;',len(disk),'D81 bytes;',schema['dump_size'],'dump bytes')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kickass',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'build/diagnostics/stage10b1a');a=p.parse_args();build(a.kickass.resolve(),a.output)
