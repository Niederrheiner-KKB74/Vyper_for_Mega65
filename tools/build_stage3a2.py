from pathlib import Path
import math,struct,hashlib
r=Path('/mnt/data')
entries=[('STAGE3A2',(r/'STAGE3A2.PRG').read_bytes(),0x82),('VYLV.DAT',(r/'VYLV.DAT').read_bytes(),0x81),('VYGR.DAT',(r/'VYGR.DAT').read_bytes(),0x81)]
img=bytearray(80*40*256);used={(40,0),(40,1),(40,2),(40,3)}
def at(t,s):return ((t-1)*40+s)*256
def write(t,s,b):img[at(t,s):at(t,s)+256]=b
def pet(s,n):return s.upper().encode()[:n].ljust(n,b'\xa0')
avail=[(t,s) for t in list(range(1,40))+list(range(41,81)) for s in range(40)]
def add(data):
 n=math.ceil(len(data)/254);chain=avail[:n];del avail[:n];used.update(chain)
 for i,(t,s) in enumerate(chain):
  part=data[i*254:(i+1)*254];sec=bytearray(256)
  sec[0:2]=bytes(chain[i+1]) if i+1<n else bytes([0,len(part)+1]);sec[2:2+len(part)]=part;write(t,s,sec)
 return chain[0],n
d=bytearray(256);d[0:2]=bytes([0,255])
for i,(name,data,typ) in enumerate(entries):
 (t,s),n=add(data);o=2+i*32;d[o]=typ;d[o+1:o+3]=bytes([t,s]);d[o+3:o+19]=pet(name,16);d[o+28:o+30]=struct.pack('<H',n)
write(40,3,d)
h=bytearray(256);h[:4]=bytes([40,3,0x44,0]);h[4:20]=pet('VYPER STAGE 3A2',16);h[0x16:0x1b]=b'3A\xa02A';write(40,0,h)
for idx,tracks in enumerate((range(1,41),range(41,81))):
 b=bytearray(256);b[:2]=bytes([40,2 if idx==0 else 1]);b[2]=0x44;b[4:6]=b'3A'
 for j,t in enumerate(tracks):
  free=[s for s in range(40) if (t,s) not in used];o=0x10+j*6;b[o]=len(free)
  for s in free:b[o+1+s//8]|=1<<(s%8)
 write(40,idx+1,b)
for i,(name,data,_) in enumerate(entries):
 o=2+i*32;t,s=d[o+1:o+3];got=bytearray();seen=set()
 while t:
  assert (t,s) not in seen;seen.add((t,s));b=img[at(t,s):at(t,s)+256];nt,ns=b[:2];got+=b[2:256 if nt else ns+1];t,s=nt,ns
 assert got==data,(name,len(got),len(data))
 print(name,len(data),len(seen),'blocks verified')
out=r/'VYPER_STAGE3A2_FULL_LOAD_DMA.d81';out.write_bytes(img)
print(out,len(img),hashlib.sha256(img).hexdigest())
