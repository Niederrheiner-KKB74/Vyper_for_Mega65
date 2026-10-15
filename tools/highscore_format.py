"""Stage9c2 VYHI v1 reference codec; uint32 scores, explicit occupied count."""
import binascii,struct
MAGIC=b'VYHI\x01\x20\x07';SIZE=592
ALPHABET=b'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-+/.@!?'
def seal(data):
 b=bytearray(data);assert len(b)==SIZE
 b[8:10]=binascii.crc_hqx(b[:8]+b[10:],65535).to_bytes(2,'little');return bytes(b)
def encode(entries):
 if len(entries)>80:raise ValueError('count')
 b=bytearray(SIZE);b[:7]=MAGIC;b[7]=len(entries)
 previous=0xffffffff
 for i,(name,score) in enumerate(entries):
  if len(name)!=3 or any(c not in ALPHABET for c in name) or not 0<=score<=previous:raise ValueError('record')
  b[32+7*i:39+7*i]=name+struct.pack('<I',score);previous=score
 return seal(b)
def decode(data):
 b=bytes(data)
 if len(b)!=SIZE or b[:7]!=MAGIC or b[7]>80 or any(b[10:32]) or seal(b)!=b:raise ValueError('header/CRC')
 entries=[(b[32+7*i:35+7*i],struct.unpack_from('<I',b,35+7*i)[0]) for i in range(b[7])]
 if encode(entries)!=b:raise ValueError('records/empty slots')
 return entries
def insert(entries,name,score):
 if not 0<=score<=0xffffffff:raise ValueError('score')
 i=next((i for i,e in enumerate(entries) if score>=e[1]),len(entries))
 return (entries[:i]+[(name,score)]+entries[i:])[:80] if i<80 else entries[:]
