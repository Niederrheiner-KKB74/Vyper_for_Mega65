#!/usr/bin/env python3
"""Verified VYSO1 resource and typed events from original Amiga descriptors."""
import binascii,csv,json,struct,subprocess
from pathlib import Path
import extract_stage8a2_samples as EX
ROOT=EX.ROOT
HEADER=512;CODE=6144;PCM=HEADER+CODE;ATTIC=0x08030000

def prepare(w):
 meta=EX.extract(w);archive=(w/'VYAU.DAT').read_bytes();meta['PCM_offset']=PCM
 with (ROOT/'docs/amiga_sound_evidence/enemy_types.csv').open() as f:types=list(csv.DictReader(f))
 # Re-read actual descriptors; CSV does not get to invent a mapping.
 S=EX.BASE.SOUND;_,read=S.ofs_inventory((ROOT/'assets/stage5b/original_sources/VYPER.ADF').read_bytes());h=S.BASE.hunks(read('/Vyper/Shot'))
 chunks=S.BASE.uss_chunks((ROOT/'assets/stage5b/original_sources/Vyper_Startscreen.uss').read_bytes())
 runtime=[(chunks[b'CRAM']['data'],0x18140),((ROOT/'assets/stage5b/original_sources/Vyper_Memory_Dump.dat').read_bytes(),0x2af50)]
 for i,t in enumerate(types):
  actual=struct.unpack_from('>4H',h[1]['data'],0x2baa+18*i+10)
  if actual!=tuple(int(t[k]) for k in ('destruction_sound','shot_sound','entry_sound','attack_sound')):raise ValueError('Type/event mismatch')
  for ram,base in runtime:
   if struct.unpack_from('>4H',ram,base+0x2baa+18*i+10)!=actual:raise ValueError('Type sound fields differ from runtime evidence')
 frames=(ROOT/'assets/stage5b/VYGR.DAT').read_bytes()
 inc=''
 for label,col in [('death_ids','destruction_sound'),('shot_ids','shot_sound'),('entry_ids','entry_sound'),('attack_ids','attack_sound')]:inc+=label+': .byte '+','.join(t[col] for t in types)+'\n'
 offsets=[struct.unpack_from('<H',frames,8+8*i)[0] for i in range(38)]
 for n,fn in [('gfx_lo',lambda x:x&255),('gfx_hi',lambda x:x>>8)]:inc+=n+': .byte '+','.join(str(fn(o)) for o in offsets)+'\n'
 (w/'audio_events.inc').write_text(inc)
 samples=(w/'samples.inc').read_text()
 for name,shift in [('src_lo',0),('src_hi',8),('src_bank',16)]:
  import re
  vals=[((0x30000+PCM+s['offset'])>>shift)&255 for s in meta['samples']]
  samples=re.sub(r'^'+name+r':.*$',name+': .byte '+','.join(map(str,vals)),samples,flags=re.M)
 (w/'audio_samples.inc').write_text(samples)
 (w/'audio_constants.inc').write_text(f'.const ARCHIVE_BYTES=${0x30000+PCM+len(archive):x}\n')
 return meta,archive,types

def package(w,meta,archive,types):
 code=(w/'AUDIO_CORE.PRG').read_bytes()
 if code[:2]!=b'\x00\xa0' or len(code)!=CODE+2:raise ValueError('Audio core image layout')
 table=b''.join(struct.pack('<BBIHHBBHH',s['id'],1,s['offset'],s['length'],s['per'],s['divisor'],s['busy'],s['rate'],s['crc']) for s in meta['samples'])
 header=struct.pack('<4sHHIIIIHHI',b'VYSO',1,HEADER,HEADER,CODE,PCM,len(archive),20,16,binascii.crc_hqx(archive,65535))
 header=(header+table).ljust(HEADER,b'\0');blob=header+code[2:]+archive
 (w/'VYSO.DAT').write_bytes(blob)
 crc=binascii.crc_hqx(blob,65535)
 (w/'audio_file.inc').write_text(f'.const AUDIO_FILE_BYTES={len(blob)}\n.const AUDIO_FILE_CRC=${crc:04x}\n')
 (w/'audio_header.bin').write_bytes(header[:32])
 meta.update(file_bytes=len(blob),file_crc=crc,file_sha256=EX.BASE.SOUND.BASE.sha(blob),types=types,core_physical=0x1e000,core_attic=ATTIC+HEADER,buffers=[0x16400,0x5c500])
 import re
 symbols={k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(w/'stage8b_audio_core.sym').read_text())}
 meta['diagnostics_physical']={n:symbols[n]+0x14000 for n in ('error','underruns','max_gap','max_lines','refills','completed')}
 meta['gate_mailbox']={'command':0x1fd0,'ready':0x1fd1,'error':0x1fd3}
 meta['source_references']={'game':'f7350d6','audio':'ee66f6d44fe4b6488dd3db25c7b91deaa77878d5','analysis':'d135b754beec10d608ac4bf6b91a2357247b62f3'}
 (w/'audio-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 return meta
