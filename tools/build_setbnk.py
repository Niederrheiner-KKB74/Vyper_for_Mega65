from pathlib import Path
import subprocess,math
p=Path('/mnt/data')
s=(p/'stage3a1_loader_petscii_fixed.asm').read_text()
s=s.replace('    lda #12\n    ldx #<filename', '    lda #0          // LOAD/SAVE data bank 0\n    ldx #0          // Filename bank 0\n    jsr $ff6b       // MEGA65 SETBNK\n    lda #12\n    ldx #<filename')
s=s.replace('HEADER TEST - PETSCII FIX','HEADER TEST - SETBNK 0')
(p/'stage3a1_loader_setbnk.asm').write_text(s)
r=subprocess.run(['java','-jar',str(p/'KickAss65CE02-5.25.jar'),str(p/'stage3a1_loader_setbnk.asm'),'-o',str(p/'STAGE3A1_SETBNK.PRG')],capture_output=True,text=True)
print(r.stdout[-250:],r.stderr);assert r.returncode==0
D=bytearray((p/'VYPER_STAGE3A1_PETSCII_FIX.d81').read_bytes()); prg=(p/'STAGE3A1_SETBNK.PRG').read_bytes()
def off(t,s):return ((t-1)*40+s)*256
entry=off(40,3)+2;t,ss=D[entry+1],D[entry+2];chain=[]
while t:
 o=off(t,ss);chain.append((t,ss,o));t,ss=D[o],D[o+1]
n=math.ceil(len(prg)/254);assert n<=len(chain)
for i,(_,_,o) in enumerate(chain[:n]):
 chunk=prg[i*254:(i+1)*254];D[o+2:o+256]=chunk.ljust(254,b'\0')
 if i==n-1:D[o]=0;D[o+1]=len(chunk)+1
 else:D[o],D[o+1]=chain[i+1][:2]
D[entry+28:entry+30]=n.to_bytes(2,'little')
out=p/'VYPER_STAGE3A1_SETBNK.d81';out.write_bytes(D)
t,ss=D[entry+1],D[entry+2];got=bytearray()
while t:
 o=off(t,ss);nt,ns=D[o],D[o+1];got.extend(D[o+2:o+(ns+1 if nt==0 else 256)]);t,ss=nt,ns
assert got==prg
print('verified',out,len(D),len(prg))
