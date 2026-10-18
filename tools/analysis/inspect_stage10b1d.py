#!/usr/bin/env python3
"""Decode the bounded Stage10b1d RAM log, never infer audibility from pointer equality."""
import argparse,hashlib,json,struct,re
from pathlib import Path

def parse(raw):
 if len(raw)!=2080 or raw[:9]!=b'VYAL1B1D\1':raise ValueError('Log size/magic/version mismatch')
 count,index=raw[9:11]
 if count>64 or index>=64 or struct.unpack_from('<H',raw,16)[0]!=32:raise ValueError('Invalid ring directory')
 if count<64 and index!=count:raise ValueError('Incomplete ring directory')
 events=[]
 for pos in range(count):
  i=(index+pos)%64 if count==64 else pos;b=raw[32+32*i:64+32*i]
  if b[2] not in b'AB' or b[3]>6 or b[6] not in (0,1) or b[7] not in (0,1):raise ValueError('Invalid event tag')
  events.append({'attempt':struct.unpack_from('<H',b)[0],'variant':chr(b[2]),'phase':b[3],'software_1FD3':b[4],'D711_raw':b[5],'D711_strict_eq80':bool(b[6]),'D711_masked_eq80':bool(b[7]),'control':b[8],'D712':b[9],'D713':b[10],'frame':b[11],'current':int.from_bytes(b[12:15],'little'),'volume':b[15],'base':int.from_bytes(b[16:19],'little'),'rate':int.from_bytes(b[19:22],'little'),'end16':int.from_bytes(b[22:24],'little'),'volume_copy':b[24],'seed_error':b[26],'playing':bool(b[27]),'error_before':b[28],'error_after':b[29],'start_frame':b[30],'pointer_read_retry_exhausted':bool(b[31])})
 return {'sha256':hashlib.sha256(raw).hexdigest(),'records':count,'total_records_mod65536':struct.unpack_from('<H',raw,12)[0],'last_attempt':struct.unpack_from('<H',raw,14)[0],'entry_1FD3':raw[18],'init_error':raw[19],'sound_id':raw[20],'Paula_PER':struct.unpack_from('<H',raw,21)[0],'entry_CPU_P':raw[23],'D711_init_raw':raw[30],'target':int.from_bytes(raw[24:27],'little'),'sentinel':int.from_bytes(raw[27:30],'little'),'events':events,'limits':'Sequential unchecksummed RAM sample. Labels identify test variants, not platform. Pointer match does not prove sound heard. Ring overwrites oldest records after64 events.'}
def load(data):
 if len(data)==2080:return data
 if len(data)==2082 and data[:2]==b'\x00\x50':return data[2:]
 rows=re.findall(rb':([0-9A-Fa-f]{8}):([0-9A-Fa-f]{32})',data)
 if rows:
  memory={}
  for addr,hexbytes in rows:
   for i,v in enumerate(bytes.fromhex(hexbytes.decode())):
    a=int(addr,16)+i
    if a in memory and memory[a]!=v:raise ValueError('Conflicting monitor reads')
    memory[a]=v
  if any(a not in memory for a in range(0x5000,0x5820)):raise ValueError('Incomplete monitor log')
  return bytes(memory[a] for a in range(0x5000,0x5820))
 raise ValueError('Expected raw2080 bytes, PRG header5000 or complete UART M transcript')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path);p.add_argument('--json',type=Path);a=p.parse_args();source=a.file.read_bytes();r=parse(load(source));r['input_sha256']=hashlib.sha256(source).hexdigest();text=json.dumps(r,indent=2)+'\n'
 if a.json:a.json.write_text(text)
 else:print(text,end='')
if __name__=='__main__':main()
