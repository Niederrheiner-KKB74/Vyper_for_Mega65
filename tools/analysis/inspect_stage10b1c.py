#!/usr/bin/env python3
"""Decode optional Stage10b1c monitor RAM samples; predictions are not measured positions."""
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=ROOT/'releases/stage_10b1c/scene.json'
def parse(raw,s):
 if len(raw)!=s['snapshot_size'] or raw[:8]!=b'VYDG1B1C' or raw[8]!=1 or raw[9] not in b'AB':raise ValueError('Snapshot magic/version/mode/size mismatch')
 if struct.unpack_from('<HH',raw,16)!=(len(s['registers']),s['snapshot_size']):raise ValueError('Register schema mismatch')
 if raw[12]!=31 or raw[14:16]!=b'\0\0':raise ValueError('Write-shadow mismatch')
 regs={}
 for i,r in enumerate(s['registers']):
  a,v=struct.unpack_from('<HB',raw,32+i*3)
  if a!=r['address']:raise ValueError('Register sequence mismatch')
  regs[a]=v
 mode=chr(raw[9]);expected={0xd031:s[mode]['D031'],0xd05a:s[mode]['D05A'],0xd054:0x55,0xd07a:0,0xd079:0,0xd058:96,0xd059:0,0xd05e:48,0xd04c:80,0xd04d:0,0xd04e:104,0xd04f:0,0xd05c:80,0xd05d:0,0xd015:15,0xd05b:1,0xd061:0xe0,0xd063:0,0xd069:0x40,0xd070:0x9a,0xd06d:0x93,0xd06e:0x80,0xd076:255}
 errors=[{'address':f'${a:04X}','expected':v,'actual':regs[a]} for a,v in expected.items() if regs[a]!=v]
 for a,mask,want in [(0xd051,0xc0,0),(0xd053,0x60,0),(0xd01a,0x1f,0)]:
  if regs[a]&mask!=want:errors.append({'address':f'${a:04X}','mask':mask,'expected':want,'actual':regs[a]})
 def sprite(i):return {'X':regs[0xd000+2*i]+256*bool(regs[0xd010]&(1<<i))+512*bool(regs[0xd05f]&(1<<i)),'Y':regs[0xd001+2*i]+256*bool(regs[0xd077]&(1<<i))+512*bool(regs[0xd078]&(1<<i))}
 if sprite(0)!={'X':301,'Y':424} or sprite(1)!={'X':525,'Y':456}:errors.append({'sprite_coordinates':[sprite(0),sprite(1)]})
 return {'mode':mode,'rebuild_sequence':struct.unpack_from('<H',raw,10)[0],'sha256':hashlib.sha256(raw).hexdigest(),'configuration_valid':not errors,'errors':errors,'write_shadows':{'D051':raw[12],'D051_restore':raw[13],'D07A':raw[14],'D01A':raw[15]},'sprites':[sprite(i) for i in range(4)],'registers':{f'${a:04X}':v for a,v in regs.items()},'limits':'Sequential read-only sample, not atomic or CRC-protected; external capture must be complete. Does not measure internal rendering or physical GOTOX output.'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('sample',type=Path);p.add_argument('--json',type=Path);a=p.parse_args();r=parse(a.sample.read_bytes(),json.loads(SCHEMA.read_text()));out=json.dumps(r,indent=2)+'\n'
 if a.json:a.json.write_text(out)
 else:print(out,end='')
 if not r['configuration_valid']:raise SystemExit(1)
if __name__=='__main__':main()
