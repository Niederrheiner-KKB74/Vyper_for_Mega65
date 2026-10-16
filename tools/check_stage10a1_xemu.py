#!/usr/bin/env python3
"""Controlled UART-monitor regression against a running XEMU, not a visual test.

Start XEMU with ROM V920413, a COPY of the D81, -uartmon /tmp/vyper.sock.
Complete onboarding and wait for the menu. This writes diagnostic state only in
that emulator: F2 menu activation, ordinary respawn and completed-level states, and ROM keyboard queue.
No modified XEMU is needed. Collision/audio-completion timing is tested elsewhere.
"""
import argparse,hashlib,json,re,socket,time
from pathlib import Path

def labels(path):
 return {k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',path.read_text())}
class Monitor:
 def __init__(self,path):
  self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.connect(path);self.sock.settimeout(5)
 def cmd(self,text):
  self.sock.sendall(text.encode()+b'\r');data=b''
  while not re.search(rb'\r?\n\.\r?\n',data):
   part=self.sock.recv(65536)
   if not part:raise RuntimeError('XEMU closed monitor')
   data+=part
  return data.decode('ascii',errors='replace')
 def read(self,address,n=16):
  out=bytearray()
  for offset in range(0,n,256):
   answer=self.cmd(f'M {address+offset:x}')
   blocks=re.findall(r':[0-9A-Fa-f]{8}:([0-9A-Fa-f]{32})',answer)
   if len(blocks)!=16:raise RuntimeError(answer)
   out.extend(b''.join(bytes.fromhex(b) for b in blocks))
  return bytes(out[:n])
 def write(self,address,data):self.cmd(f's {address:x} '+data.hex(' '))
 def regs(self):
  answer=self.cmd('r');matches=re.findall(r'\n([0-9A-F]{4}) ((?:[0-9A-F]{2} ){5})([0-9A-F]{4}) ',answer)
  if not matches:raise RuntimeError(answer)
  pc,regs,sp=matches[-1];return {'pc':int(pc,16),'sp':int(sp,16),'registers':regs.strip()}
 def wait(self,predicate,timeout=90):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   r=self.regs()
   if r['pc']==0:raise AssertionError(('PC0',r))
   if predicate(r):return r
   time.sleep(.04)
  raise AssertionError(('timeout',r))
 def basic_key(self,text):
  assert len(text)<=10
  self.write(0x2b0,text);self.write(0xd0,bytes([len(text)]))

def run(args):
 art=args.artifacts;n=labels(art/'STAGE10A1.sym');menu=labels(art/'MENU_OVERLAY.sym')
 # Duplicate names in namespaces are deliberately avoided below; these labels
 # are unique ABI addresses in the complete symbol file.
 main=n['main_loop'];overlay=(art/'MENU_OVERLAY.PRG').read_bytes()[2:18]
 m=Monitor(args.socket);report={'kind':'headless XEMU controlled-state regression','rom':'V920413',
  'D81_sha256':hashlib.sha256((art/'VYPER_STAGE10A1.d81').read_bytes()).hexdigest(),
  'real_inputs':'ROM GETIN queue for X, RUN, DIRECTORY; menu/start, WAIT and all-enemies-DEAD diagnostic writes',
  'limits':'No physical joystick, visual/panning judgment, natural collision or death-sound timing claim; UART pauses distort hardware/wall timing, ready count is100 main-loop/FSM steps, not a2s wall-clock measurement', 'cases':[]}
 def menu_ready():return m.wait(lambda r:menu['menu_loop']<=r['pc']<=menu['menu_input'] and m.read(0x7000,16)==overlay)
 def game_paused(expected_mode=2):
  def is_game(r):
   if main<=r['pc']<=main+2:
    if m.read(0x2100,1)==b'\x78':return True
    m.cmd('t0') # same logical breakpoint may occur inside the HS overlay
   return False
  r=m.wait(is_game)
  assert m.read(0x1b10,1)==bytes([expected_mode]),r
  return r
 def check_initial_hud(mode):
  counts=[]
  for player in range(mode):
   rows=range(7,12) if player==0 else range(16,21)
   words=[int.from_bytes(m.read(0xe000+192*row+42,40)[i:i+2],'little') for row in rows for i in range(0,40,2)]
   count=sum(w in (0x321,0x322,0x323) for w in words)
   assert count==9,('initial HUD lives',mode,player,count)
   counts.append(count)
  if mode==2:
   for row in (12,21):
    assert m.read(0xe000+row*192+46,20)[::2]==bytes([0x81])*9+b'\x80',('separator',row)
  report.setdefault('initial_HUD',[]).append({'mode':mode,'life_glyph_counts':counts,'before_first_game_frame':True,'separator_rows':[12,21] if mode==2 else []})
 def ready_frames():
  assert m.read(n['gr_timer'],1)==b'\x64'
  assert m.read(0x1d89,1)==b'\x03'
  frozen=m.read(0x1e00,0x100)
  first=m.read(0xffd37fa,1)[0];observed=[]
  for frame in range(1,101):
   m.cmd('t0');game_paused()
   remaining=m.read(n['gr_timer'],1)[0]
   assert remaining==100-frame,(frame,remaining)
   assert m.read(0x1e00,0x100)==frozen,('ENTRY changed during ready',frame)
   observed.append(m.read(0xffd37fa,1)[0])
  assert m.read(0x1d89,1)==b'\0'
  report.setdefault('ready_phases',[]).append({'frames':100,'initial_hardware_frame':first,'last_hardware_frame':observed[-1],'ENTRY_frozen':True,'active':m.read(0x1b11,1)[0]})
 menu_ready()
 for switches in (0,1,2):
  m.cmd(f'b {main:x}')
  m.write(menu['selection'],b'\x02');m.write(menu['start_pending'],b'\x01')
  start=game_paused();check_initial_hud(2);ready_frames();steps=[]
  # A normal life loss must respawn the same actor, not trigger a handoff.
  m.write(0x1a0a,b'\x02\x00');m.write(n['c_ps'],b'\x02')
  m.write(n['c_es'],b'\x01'+bytes(22));m.write(0x1ec6,b'\x03')
  m.cmd('t0');game_paused()
  assert m.read(0x1b11,1)==b'\0' and m.read(n['c_ps'],1)==b'\x03'
  for i in range(switches):
   m.write(n['c_es'],bytes(23));m.write(n['c_ps'],b'\0')
   m.cmd('t0');game_paused()
   assert m.read(0x1d89,1)==b'\x02'
   frames=0
   while m.read(0x1d89,1)==b'\x02':
    m.cmd('t0');r=game_paused();frames+=1
    assert frames<140
   assert frames==129,frames
   active=m.read(0x1b11,1)[0];assert active==(i+1)%2,active
   assert r['sp']==start['sp'],(start,r)
   expected_levels=bytes((2,0,2 if i else 1,0))
   actual_levels=m.read(0x1b04,2)+m.read(0x1b0c,2)
   assert actual_levels==expected_levels,(actual_levels,expected_levels)
   ready_frames()
   steps.append({'active':active,'transition_frames':frames,'saved_levels':list(actual_levels),**r})
  # Confirm both transient code regions, not merely the PC after engine RTS.
  title=m.read(0x08000000,0x800);loader=m.read(0x080a0000,0x640)
  m.cmd('b 0');m.basic_key(b'X');m.cmd('t0')
  basic=m.wait(lambda r:r['pc']>=0xe000 and m.read(0xffd3060,4)==b'\x00\x08\x00\x00')
  assert m.read(0x4000,0x800)==title,'title bootstrap missing after X'
  assert m.read(0x5000,0x640)==loader,'audio/highscore bootstrap missing after X'
  assert all(m.read(a,1)[0]&0x88!=0x80 for a in (0xffd3720,0xffd3740)),'audio still running'
  m.basic_key(b'RUN\r');after=menu_ready()
  report['cases'].append({'switches':switches,'game_start':start,'handoffs':steps,'BASIC':basic,'RUN_menu':after,'code_restored':True})
  print(f'PASS: ordinary death stays P1; {switches} level handoffs +100-frame ready, X, code restore, RUN -> menu',flush=True)
 # Exercise menu -> new game after both highscore overlays too. The overlay
 # quit flag simulates cancellation only; persistence/input are separate tests.
 m.cmd(f'b {main:x}');m.write(menu['selection'],b'\x02');m.write(menu['start_pending'],b'\x01');game_paused();ready_frames()
 hs=labels(art/'highscore.sym');over=[]
 for player in (0,1):
  m.cmd(f"b {hs['main_loop']:x}")
  m.write(0x1a0a,b'\0\0');m.write(n['c_ps'],b'\x04');m.write(0x1fe7,b'\x95');m.cmd('t0')
  r=m.wait(lambda r:r['pc'] in (hs['main_loop']+3,hs['input_tick']) and m.read(0x2100,1)==b'\x08')
  over.append({'player':player,**r});m.write(hs['quit'],b'\x01')
  m.cmd(f'b {main:x}' if player==0 else 'b 0');m.cmd('t0')
  if player==0:game_paused();ready_frames()
  else:menu_ready()
 m.cmd(f'b {main:x}');m.write(menu['selection'],b'\x01');m.write(menu['start_pending'],b'\x01');game_paused(1);check_initial_hud(1)
 title=m.read(0x08000000,0x800);loader=m.read(0x080a0000,0x640)
 m.cmd('b 0');m.basic_key(b'X');m.cmd('t0')
 m.wait(lambda r:r['pc']>=0xe000 and m.read(0xffd3060,4)==b'\x00\x08\x00\x00')
 assert m.read(0x4000,0x800)==title and m.read(0x5000,0x640)==loader
 report['game_over_menu_restart']={'overlays':over,'new_F1_then_X_code_restored':True,'overlay_input':'quit flag, not physical name cancellation'}
 print('PASS: both Game Overs/highscore overlays -> menu -> new F1 -> X, code restored',flush=True)
 m.basic_key(b'DIRECTORY\r');time.sleep(.3)
 m.wait(lambda r:r['pc']>=0xe000 and m.read(0xd0,1)==b'\0')
 raw=m.read(0x800,2000);text=''.join(chr((v&127)+64 if (v&127)<32 else v&127) for v in raw)
 assert 'DEVICE NOT PRESENT' not in text and 'VYPER STAGE10A1' in text,text
 report['DIRECTORY']=text;print('PASS: actual BASIC DIRECTORY lists Stage10a1 disk',flush=True)
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
def audio_exit(args):
 """Optional diagnostic stub in unused private1B40..1B48, not in the PRG."""
 art=args.artifacts;n=labels(art/'STAGE10A1.sym');mn=labels(art/'MENU_OVERLAY.sym');m=Monitor(args.socket)
 m.basic_key(b'RUN\r')
 m.wait(lambda r:mn['menu_loop']<=r['pc']<=mn['menu_input'])
 main=n['main_loop'];m.cmd(f'b {main:x}');m.write(mn['selection'],b'\x02');m.write(mn['start_pending'],b'\x01')
 m.wait(lambda r:main<=r['pc']<=main+2 and m.read(0x2100,1)==b'\x78')
 assert n['tick']==0x35e0
 stub=b'\x20'+n['player_death'].to_bytes(2,'little')+b'\x20'+n['tick'].to_bytes(2,'little')+b'\x4c'+main.to_bytes(2,'little')
 m.write(0x1b40,stub);m.cmd('g 1b40');m.cmd('t0')
 m.wait(lambda r:main<=r['pc']<=main+2)
 before=m.read(0xffd3720,1)[0];assert before&0x88==0x80,hex(before)
 m.cmd('b 0');m.basic_key(b'X');m.cmd('t0')
 r=m.wait(lambda r:r['pc']>=0xe000 and m.read(0xffd3060,4)==b'\x00\x08\x00\x00')
 after=m.read(0xffd3720,1)[0];assert after&0x88!=0x80,hex(after)
 result={'D81_sha256':hashlib.sha256((art/'VYPER_STAGE10A1.d81').read_bytes()).hexdigest(),'diagnostic_stub':{'address':0x1b40,'bytes':stub.hex(),'calls':'original audio8.player_death and tick'},'before_CTRL':before,'after_CTRL':after,'BASIC':r,'limits':'DMA CTRL and safe exit; no hearing/panning claim'}
 args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS: X stops an actually running original Player-death PCM source and returns to BASIC',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--socket',required=True);p.add_argument('--audio-only',action='store_true');p.add_argument('--artifacts',type=Path,default=Path(__file__).resolve().parents[1]/'releases/stage_10a/stage10a1');p.add_argument('--output',type=Path,default=Path('/tmp/stage10a1-xemu.json'));a=p.parse_args();(audio_exit if a.audio_only else run)(a)
