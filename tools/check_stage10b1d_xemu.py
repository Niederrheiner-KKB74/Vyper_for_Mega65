#!/usr/bin/env python3
"""Supplemental local XEMU Audio-DMA pointer regression. Dummy SDL output is NOT a hearing test."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from check_stage10a1_xemu import Monitor,labels
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from inspect_stage10b1d import parse

def run(a):
 artifact_hash=hashlib.sha256((a.artifacts/'VYPER_STAGE10B1D.d81').read_bytes()).hexdigest()
 m=Monitor(a.socket);n=labels(a.artifacts/'stage10b1d.sym');bp=n['main']+3;a.output.mkdir(parents=True,exist_ok=True)
 def paused():return m.wait(lambda r:r['pc']==bp+3,timeout=60)
 def key(k):
  m.cmd(f'b {bp:x}');m.cmd(f'~key{k:02x}');m.cmd('t0');paused();m.cmd('t0');paused()
 def dump(tag):
  raw=m.read(0x5000,2080);r=parse(raw);(a.output/f'{tag}.LOG').write_bytes(raw);(a.output/f'{tag}.json').write_text(json.dumps(r,indent=2)+'\n');return r
 def mixer():
  old=m.read(0xffd36f4,1)[0];out=bytearray()
  for i in range(256):m.write(0xffd36f4,bytes([i]));out+=m.read(0xffd36f5,1)
  m.write(0xffd36f4,bytes([old]));return bytes(out)
 m.cmd(f'b {bp:x}');m.cmd('~key0d');m.cmd('t0');paused()
 assert m.read(n['init_error'],1)==b'\0'
 pcm=(a.artifacts/'sound17.s8').read_bytes();assert m.read(0x16480,len(pcm))==pcm;assert m.read(0x6000,len(pcm))==pcm
 assert m.read(n['crc'],2)==bytes([0x6f,0x7f])
 routes=mixer();wanted=bytearray(256)
 for i in [0x10,0x11,0x30,0x31,0xd0,0xd1,0xf0,0xf1,0x1e,0x1f,0x3e,0x3f,0xde,0xdf,0xfe,0xff]:wanted[i]=255
 assert routes==bytes(wanted)
 cases=[]
 for attempt,(name,k,variant) in enumerate([('A1',0x31,'A'),('B',0x32,'B'),('A2',0x31,'A'),('A_replay',0x50,'A')],1):
  key(k);r=dump(name+'_started');events=[e for e in r['events'] if e['attempt']==attempt]
  assert len(events)>=3 and events[0]['current']==0x18020 and events[0]['software_1FD3']==0
  assert events[1]['current']==0x16480 and events[1]['software_1FD3']==0 and events[1]['control']==2
  assert events[2]['variant']==variant and events[2]['software_1FD3']==0
  # Native XEMU updates individual bytes, so BOTH A and B must succeed here.
  m.cmd('b 0');m.cmd('t0')
  m.wait(lambda regs:m.read(n['playing'],1)==b'\0' and m.read(0x5009,1)[0]>=attempt*4,timeout=20)
  m.cmd(f'b {bp:x}');m.cmd('t0');paused();r=dump(name+'_done');last=r['events'][-1]
  assert last['phase']==3 and last['software_1FD3']==0,last
  assert last['current']==0x17ec0,last
  cases.append({'case':name,'attempt':attempt,'variant':variant,'seed_current':events[0]['current'],'latched_current':events[1]['current'],'software_error':0,'completion_current':last['current'],'natural_one_shot_completion':True,'sound_heard':'NOT_TESTED dummy SDL'})
 key(0x47);r=dump('D711_observation');assert r['events'][-1]['phase']==5
 key(0x53);assert m.read(n['playing'],1)==b'\0'
 initial_channel=m.read(n['old_channel'],16);initial_global=m.read(n['old_global'],1)[0];initial_swap=m.read(n['old_swap'],1)[0];initial_mixer=m.read(n['old_mixer'],256);initial_mailbox=m.read(n['old_mailbox'],1)
 m.cmd(f'b {n["exit_restored"]:x}');m.cmd('~key58');m.cmd('t0');m.wait(lambda r:r['pc']==n['exit_restored']+1)
 assert mixer()==initial_mixer
 assert m.read(0xffd3720,16)==initial_channel
 assert m.read(0xffd3711,1)[0]&0xb8==initial_global&0xb8
 assert m.read(0xffd3712,1)[0]&2==initial_swap
 assert m.read(0x1fd3,1)==initial_mailbox
 for addr,saved in [(0x30,'old_d030'),(0x31,'old_d031'),(0x54,'old_d054')]:assert m.read(0xffd3000+addr,1)==m.read(n[saved],1)
 m.cmd(f'b {bp:x}');m.cmd('t0');time.sleep(.25);m.basic_key(b'RUN\r');m.cmd('t0');paused();assert m.read(n['init_error'],1)==b'\0';assert parse(m.read(0x5000,2080))['records']==0
 # Exit second time using regular input, then actual BASIC DIRECTORY.
 m.cmd(f'b {n["exit_restored"]:x}');m.cmd('~key58');m.cmd('t0');m.wait(lambda r:r['pc']==n['exit_restored']+1)
 m.cmd('b 0');m.cmd('t0');time.sleep(.25);m.basic_key(b'DIRECTORY\r')
 def directory_ready(regs):
  if regs['pc']<0xe000 or m.read(0xd0,1)!=b'\0':return False
  return b'VYPER 10B1D TEST' in bytes(v+64 if v<32 else v for v in (b&127 for b in m.read(0x800,2000)))
 m.wait(directory_ready)
 assert hashlib.sha256((a.artifacts/'VYPER_STAGE10B1D.d81').read_bytes()).hexdigest()==artifact_hash,'Artifacts changed during run'
 report={'kind':'supplemental local headless XEMU controller/data test','local_xemu_commit':'40dfef0d1d5f56be2469492715c12bdb32c75b67','patch':'tools/diagnostics/stage10a1_xemu_trace.patch (~key)','ROM':'V920413 PAL80x25','D81_sha256':artifact_hash,'original_sample_SHA256':hashlib.sha256(pcm).hexdigest(),'sample_DMA_readback_and_CRC':True,'cases':cases,'D711_read_only_observation':True,'mixer_channel_pointer_global_VIC_mailbox_restore':True,'repeated_RUN':True,'BASIC_DIRECTORY':True,'hardware':'NOT_RUN','exact_target_xemu_release':'NOT_RUN','hearing':'NOT_RUN','timing':'UART pauses and SDL scheduling invalidate hardware duration/latency claims'}
 (a.output/'runtime.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
def manual_stop(a):
 """Focused follow-up from BASIC READY after the complete main regression."""
 artifact_hash=hashlib.sha256((a.artifacts/'VYPER_STAGE10B1D.d81').read_bytes()).hexdigest()
 m=Monitor(a.socket);n=labels(a.artifacts/'stage10b1d.sym');bp=n['main']+3
 def paused():return m.wait(lambda r:r['pc']==bp+3,timeout=60)
 def key(k):
  m.cmd(f'b {bp:x}');m.cmd(f'~key{k:02x}');m.cmd('t0');paused();m.cmd('t0');paused()
 m.cmd(f'b {bp:x}');m.basic_key(b'RUN\r');m.cmd('t0');paused()
 assert m.read(n['init_error'],1)==b'\0'
 key(0x32);assert m.read(n['playing'],1)==b'\1'
 key(0x53);raw=m.read(0x5000,2080);r=parse(raw);last=r['events'][-1]
 assert last['phase']==4 and last['software_1FD3']==0 and 0x16480<=last['current']<0x17ec0,last
 (a.output/'manual_stop.LOG').write_bytes(raw);(a.output/'manual_stop.json').write_text(json.dumps(r,indent=2)+'\n')
 stopped=last['current']
 key(0x50);raw=m.read(0x5000,2080);r=parse(raw)
 start=[e for e in r['events'] if e['attempt']==2]
 assert start[0]['current']==0x18020 and start[1]['current']==0x16480 and start[2]['software_1FD3']==0
 m.cmd('b 0');m.cmd('t0');m.wait(lambda regs:m.read(n['playing'],1)==b'\0' and m.read(0x5009,1)[0]>=8,timeout=20)
 m.cmd(f'b {bp:x}');m.cmd('t0');paused()
 raw=m.read(0x5000,2080);r=parse(raw);assert r['events'][-1]['phase']==3 and r['events'][-1]['current']==0x17ec0
 (a.output/'B_replay_after_stop.LOG').write_bytes(raw);(a.output/'B_replay_after_stop.json').write_text(json.dumps(r,indent=2)+'\n')
 m.cmd(f"b {n['exit_restored']:x}");m.cmd('~key58');m.cmd('t0');m.wait(lambda r:r['pc']==n['exit_restored']+1)
 assert hashlib.sha256((a.artifacts/'VYPER_STAGE10B1D.d81').read_bytes()).hexdigest()==artifact_hash
 report={'kind':'focused supplemental local XEMU manual-stop/replay follow-up','D81_sha256':artifact_hash,'stop_while_active_current':stopped,'stop_error':0,'B_replay_seed':0x18020,'B_replay_start':0x16480,'B_replay_end':0x17ec0,'X_return':True,'hardware':'NOT_RUN','hearing':'NOT_RUN'}
 (a.output/'manual_stop_runtime.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--socket',required=True);p.add_argument('--artifacts',type=Path,default=Path('releases/stage_10b1d'));p.add_argument('--output',type=Path,default=Path('docs/diagnostics/stage10b1d'));p.add_argument('--manual-stop-only',action='store_true');a=p.parse_args()
 if not a.manual_stop_only:run(a)
 manual_stop(a)
