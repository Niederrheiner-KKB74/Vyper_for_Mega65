"""Actual Stage8b engine/controller instructions; constrained hardware model, NOT XEMU."""
import os,re,sys,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'releases/stage_8b'
def namespace(text,name):
 start=text.index('.namespace '+name+' {');a=text.index('{',start);depth=1;b=a+1
 while depth:
  if text[b]=='{':depth+=1
  if text[b]=='}':depth-=1
  b+=1
 return start,b,text[a+1:b-1]
def labels(text):return {k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',text)}
SYMBOLS=(ART/'STAGE8B.sym').read_text();G=labels(namespace(SYMBOLS,'audio8')[2]);BOOT=labels(namespace(SYMBOLS,'audioboot')[2]);C=labels((ART/'stage8b_audio_core.sym').read_text())
clean=SYMBOLS
for ns in ('audio8','audioboot'):
 a,b,_=namespace(clean,ns);clean=clean[:a]+clean[b:]
ALIAS=tempfile.TemporaryDirectory(prefix='stage8b-engine-model-');alias=Path(ALIAS.name)
for f in ART.iterdir():
 name=f.name.replace('STAGE8B','STAGE7B5B');(alias/name).symlink_to(f)
(alias/'STAGE7B5B.sym').unlink();(alias/'STAGE7B5B.sym').write_text(clean)
os.environ['STAGE7B5B_ARTIFACTS']=str(alias)
import test_stage7b5b as M
B=M.B;N=M.N
class AudioMemory(B.MenuMemory):
 def __getitem__(self,a):
  if a in (0xd011,0xd012):
   raster=(self.clock_cycles%810000)*312//810000
   return raster&255 if a==0xd012 else (self.data[a]&127)|((raster&256)>>1)
  if not getattr(self,'linear',False) and 0xa000<=a<0xc000 and self.map_mask&32:return self.data[a+self.map_offset]
  if a==0xd6f5:return self.mixer[self.data[0xd6f4]]
  if a==0xd7fa:return self.frame_counter
  if 0x08000000<=a<0x08070000:return self.attic[(a-0x08000000)&self.attic_mask]
  return super().__getitem__(a)
 def __setitem__(self,a,v):
  v&=255
  if a in (0xd720,0xd740) and v&0x88==0x80 and self.data[a]&0x88!=0x80:
   source=(a-0xd720)//32
   self.starts.append((source,self.data[C['choices']+0x14000+source],self.frame_counter,len(self.samples[source])))
  if not getattr(self,'linear',False) and 0xa000<=a<0xc000 and self.map_mask&32:self.data[a+self.map_offset]=v;return
  if a==0xd6f5:self.mixer[self.data[0xd6f4]]=v;return
  if 0x08000000<=a<0x08070000:self.attic[(a-0x08000000)&self.attic_mask]=v;return
  if a!=0xd705:return super().__setitem__(a,v)
  self.data[a]=v;p=self.data[0xd701]*256+v+(self.data[0xd702]&15)*65536
  assert self.data[0xd704]==0
  srcmb=dstmb=0
  while self.data[p]:
   opt=self.data[p];p+=1
   if opt==0x80:srcmb=self.data[p];p+=1
   elif opt==0x81:dstmb=self.data[p];p+=1
   else:assert opt==0xa
  p+=1;d=self.data[p:p+11];assert d[0] in (0,3) and d[9:]==bytes(2)
  n=int.from_bytes(d[1:3],'little');assert n
  src=int.from_bytes(d[3:6],'little')+(srcmb<<20);dst=int.from_bytes(d[6:9],'little')+(dstmb<<20)
  if getattr(self,'title_active',False):
   for lo,hi in B.OLD.TITLE_RANGES+[(0xff82000,0xff82a50)]:assert not(dst<hi and dst+n>lo),('Title overwritten',hex(dst),n)
  prev=self.linear;self.linear=True
  try:
   if d[0]==3:payload=bytes([d[3]])*n
   elif 0xff7e000<=src<0xff80000:payload=self.char_wom[src-0xff7e000:src-0xff7e000+n]
   else:payload=bytes(self[src+i] for i in range(n))
   for i,v in enumerate(payload):self[dst+i]=v
  finally:self.linear=prev
  self.base.transfers.append((src,dst,n))
  self.elapse(n*4)
 def elapse(self,cycles):
  self.clock_cycles+=cycles
  self.frame_counter=(self.clock_cycles//810000)&255
  self.elapsed_cycles+=cycles
  if not self.simulate_audio:return
  for source in (0,1):
   r=0xd720+32*source
   if self.data[r]&0x88!=0x80:self.fractions[source]=0;continue
   rate=int.from_bytes(self.data[r+4:r+7],'little')
   count,self.fractions[source]=divmod(self.fractions[source]+rate*cycles,1<<24)
   self.advance(source,count)
 def advance(self,source,n):
  d=self.data;r=0xd720+32*source;base=(0x16400,0x5c500)[source]
  for i in range(n):
   if d[r]&0x88!=0x80:break
   p=int.from_bytes(d[r+10:r+13],'little');assert base<=p<base+4096,hex(p)
   self.samples[source].append(d[p]);p+=1
   if p&65535==int.from_bytes(d[r+7:r+9],'little'):
    if d[r]&64:p=int.from_bytes(d[r+1:r+4],'little')
    else:d[r]|=8
   d[r+10:r+13]=p.to_bytes(3,'little')
class AudioCPU(B.Machine().cpu.__class__):
 def step(self):
  before=self.processorCycles;result=self.execute_step()
  self.memory.elapse(self.processorCycles-before)
  return result
 def execute_step(self):
  op=self.memory[self.pc]
  if op in (0xda,0x5a,0xdb):
   self.stPush({0xda:self.x,0x5a:self.y,0xdb:self.z}[op]);self.pc+=1;self.processorCycles+=3;return self
  if op in (0xfa,0x7a,0xfb):
   v=self.stPop();setattr(self,{0xfa:'x',0x7a:'y',0xfb:'z'}[op],v);self.FlagsNZ(v);self.pc+=1;self.processorCycles+=4;return self
  if op==0xa3:
   self.z=self.memory[self.pc+1];self.FlagsNZ(self.z);self.pc+=2;self.processorCycles+=2;return self
  if op==0x5c:
   assert self.p&4,'MAP without SEI'
   assert self.a==self.x==0 and (self.y,self.z) in ((0x40,0x20),(0x40,0x21),(0,0x83))
   self.memory.map_mask=self.z&0xf0;self.memory.map_offset=(self.y<<8)|((self.z&15)<<16)
   self.pc+=1;self.processorCycles+=2;return self
  return super().step()
class Machine(B.Machine):
 def __init__(self):
  super().__init__();self.memory.__class__=AudioMemory;self.memory.attic=bytearray(0x70000)
  self.memory.map_mask=0x80;self.memory.map_offset=0x30000;self.memory.mixer=bytearray((7+13*i)&255 for i in range(256));self.memory.frame_counter=0;self.memory.samples=[bytearray(),bytearray()];self.memory.starts=[];self.memory.attic_mask=0x7ffff;self.memory.clock_cycles=0;self.memory.simulate_audio=False;self.memory.elapsed_cycles=0;self.memory.fractions=[0,0]
  for i in range(4):self.memory.data[0xd720+16*i]=2
  self.memory.data[0xd711]=0;self.cpu.__class__=AudioCPU
  self.files['VYSO.DAT']=(ART/'VYSO.DAT').read_bytes();self.before=bytes(self.memory.data);self.mixer_before=bytes(self.memory.mixer)
 def trap(self):
  assert self.memory.map_mask==0x80 and self.memory.map_offset==0x30000,('KERNAL with banked audio map',hex(self.cpu.pc))
  super().trap()
 def run_to(self,targets,limit=50_000_000):return super().run_to(targets,limit)
 def frame(self,key=0,buttons=255):
  return super().frame(key,buttons)
 def sound(self,name,x=0):
  self.cpu.x=x;return self.call_at(G[name])
 def call_at(self,p):
  self.cpu.pc=p;self.cpu.stPushWord(0x1ff);return self.run_to([0x200],3_000_000)
def core(m,n,i=0):return m.memory.data[C[n]+0x14000+i]
class Integration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.boot=Machine().boot();assert cls.boot.cpu.pc==B.MN['menu_loop'],(cls.boot.error,hex(cls.boot.cpu.pc))
 def machine(self,level=1):
  import copy
  return copy.deepcopy(self.boot).game(level)
 def test_full_title_SEVEN_SEQ_loads_menu_and_first_game(self):
  m=self.boot;self.assertEqual(m.error,0);self.assertEqual(m.opened_names,['VYTI.DAT','VYSO.DAT','VYMN.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT','VYSH.DAT'])
  self.assertEqual(m.memory.attic[0x30000:0x30000+len(m.files['VYSO.DAT'])],m.files['VYSO.DAT'])
  m=self.machine();self.assertEqual(m.memory.data[G['error']],0);self.assertEqual(m.memory.data[G['ready']],1)
  self.assertEqual(m.memory.map_mask,0x80);self.assertEqual(core(m,'configured'),1)
 def core_call(self,m,name,source=0,index=None):
  d=m.memory.data;d[C['s']+0x14000]=source
  if index is not None:d[C['choices']+0x14000+source]=index
  oldp=m.cpu.p;m.cpu.p|=4;m.memory.map_mask=32;m.memory.map_offset=0x14000
  m.call_at(C[name]);m.memory.map_mask=128;m.memory.map_offset=0x30000;m.cpu.p=oldp
  return m
 def set_type(self,m,index,actor=0):
  m.memory.data[0x6a80+actor]=core(m,'gfx_lo',index);m.memory.data[0x6a96+actor]=core(m,'gfx_hi',index)
 def test_all_38_four_field_original_event_mappings(self):
  m=self.machine();types=json.loads((ART/'audio-metadata.json').read_text())['types']
  for i,t in enumerate(types):
   self.set_type(m,i)
   for event,col,source in [('entry','entry_sound',0),('attack','attack_sound',0),('enemy_death','destruction_sound',1),('enemy_shot','shot_sound',1)]:
    m.memory.data[C['busy']+0x14000+source]=0
    m.memory.data[N['p_source_enemy']+2]=0
    m.sound(event,2 if event=='enemy_shot' else 0)
    self.assertEqual(core(m,'pending_id',source),int(t[col]),(i,event))
  self.assertEqual({int(t['destruction_sound']) for t in types},{1,3,8,9,18,20})
 def test_two_sources_pending_busy_preemption_and_projectile_pan_pointer(self):
  m=self.machine();self.set_type(m,14)
  m.sound('entry');m.sound('attack');self.assertEqual(core(m,'pending_id'),7)
  m.sound('tick');self.assertEqual(core(m,'busy'),6)
  m.sound('entry');self.assertEqual(core(m,'pending_id'),0)
  m.sound('player_shot',0);self.assertEqual(core(m,'pending_id'),17);self.assertEqual(core(m,'active'),0)
  m.sound('tick');self.assertEqual(core(m,'active'),1)
  m.memory.data[N['p_source_enemy']+2]=0;m.sound('enemy_shot',2);m.sound('tick')
  self.assertEqual([core(m,'active',s) for s in (0,1)],[1,1])
  m.memory.data[N['p_source_enemy']+3]=0;m.memory.data[N['p_xpos']+3]=240
  m.sound('enemy_shot',3);m.memory.elapse(3000);m.sound('service');self.assertEqual(core(m,'pan_owner',1),3);self.assertEqual(core(m,'pending_id',1),0);self.assertEqual(core(m,'positions',1),240)
  m.sound('player_death');self.assertEqual(core(m,'pending_id'),19);m.sound('tick');self.assertEqual(core(m,'busy'),120)
 def test_all_20_samples_chip_banks_exact_end_and_restart(self):
  m=self.machine();meta=json.loads((ART/'audio-metadata.json').read_text());pcm=m.files['VYSO.DAT'][0x1a00:]
  for i,sample in enumerate(meta['samples']):
   source=i&1;m.sound('stop');m.memory.samples[source].clear();self.core_call(m,'start_source',source,i)
   for poll in range(500):
    m.memory.advance(source,97);m.memory.elapse(97*(1<<24)//sample['rate']);m.sound('service')
    if not core(m,'active',source):break
   else:self.fail('Never completed '+str(sample['id']))
   self.assertEqual(bytes(m.memory.samples[source]),pcm[sample['offset']:sample['offset']+sample['length']],sample['id']);self.assertEqual(m.memory.data[G['error']],0)
   self.core_call(m,'start_source',source,i);m.memory.advance(source,31)
   self.assertEqual(m.memory.samples[source][-31:],pcm[sample['offset']:sample['offset']+31])
 def test_transition_24_then22_busy_freezes_but_streaming_continues(self):
  m=self.machine();m.sound('transition_early');m.sound('tick');self.assertEqual(core(m,'busy'),120)
  m.memory.data[B.FX['state']]=2;m.memory.data[N['mode']]=2;m.memory.data[B.FX['ring']]=0
  m.sound('transition_rect');m.sound('tick');self.assertEqual(core(m,'choices'),18)
  before=core(m,'busy');m.memory.data[B.FX['ring']]=1
  for _ in range(10):m.memory.advance(0,97);m.sound('tick')
  self.assertEqual(core(m,'busy'),before);self.assertTrue(core(m,'active'))
  m.sound('reset');self.assertTrue(core(m,'active'));self.assertEqual(core(m,'pan_kind'),0)
  m.sound('restart');self.assertFalse(core(m,'active'))
 def test_exit_restore_and_second_RUN_with_audio(self):
  m=self.machine();m.sound('player_death');m.sound('tick');self.assertTrue(core(m,'active'))
  cached_loader=bytes(m.memory.attic[0x2c000:0x2d000])
  m.call('exit_to_basic');self.assertEqual(bytes(m.memory.mixer),m.mixer_before);self.assertEqual(m.memory.data[0xd711],m.before[0xd711])
  self.assertEqual(m.memory.map_mask,128);self.assertFalse(m.cpu.p&4)
  self.assertEqual(bytes(m.memory.data[0xe000:0xf000]),cached_loader)
  m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot();self.assertEqual(m.cpu.pc,B.MN['menu_loop'])
  m.game(3);self.assertEqual(m.memory.data[G['error']],0)
 def test_panning_per_preserved_and_no_gameplay_RNG_consumed(self):
  m=self.machine();d=m.memory.data
  rng=(bytes(d[N['a_random']:N['a_random']+2]) if 'a_random' in N else b'',bytes(d[B.FE['seed']:B.FE['seed']+2]))
  m.sound('player_shot');m.sound('tick');self.assertEqual(int.from_bytes(d[0xd724:0xd727],'little'),4127)
  for x in (0,120,240):
   d[N['p_xpos']]=x;m.memory.elapse(3000);m.sound('service');right=x//4;left=60-right
   self.assertEqual(m.memory.mixer[0x10],(left*255+32)//64);self.assertEqual(m.memory.mixer[0x30],(right*255+32)//64)
  self.assertEqual(rng[1],bytes(d[B.FE['seed']:B.FE['seed']+2]))
 def test_level_initialization_1_3_29_54_100_preserves_sound_archive(self):
  m=self.machine();archive=bytes(m.memory.attic[0x30000:0x574c0])
  for level in (1,3,29,54,100,1):
   m.call('transition',level);self.assertEqual(m.error,0);self.assertEqual(m.memory.data[G['error']],0)
   self.assertEqual(archive,bytes(m.memory.attic[0x30000:0x574c0]));m.sound('entry',0)
 def test_native_projectile_player_collision_and_event_regressions(self):
  case=M.MotionTests();case.machine=lambda:self.machine()
  for name in ('test_player_step_clamps_50_100_frames_muzzle_respawn','test_hit_explosion_respawn_keeps_X_and_blink_move','test_native_fraction_floor_before_DY_45degree_and_sign','test_spread_full_range_parity_projected_muzzle_and_rng_isolation','test_signed_offscreen_no_wrap_collision_or_early_X_death','test_six_pool_event_consumption_owner_death_and_player_independence','test_event_schedule_unchanged'):
   with self.subTest(rule=name):getattr(case,name)()
 def test_real_game_transition_samples_under_simultaneous_long_voice_load(self):
  m=self.machine();m.sound('stop');self.core_call(m,'start_source',0,15);self.core_call(m,'start_source',1,18)
  # Isolated stress fixture: both longest samples, ongoing engine frames, eight
  # projectiles and three attackers. No game-source test/diagnostic mode is added.
  m.memory.simulate_audio=True;max_cycles=0;max_jobs=0
  for frame in range(130):
   d=m.memory.data
   d[N['c_ps']]=3;d[N['c_blink']]=150
   for slot in range(8):
    d[N['p_active']+slot]=1;d[N['p_xpos']+slot]=20+slot*20;d[N['p_ypos']+slot]=170
   for actor in range(3):
    d[N['c_es']+actor]=3;d[N['e_phase']+actor]=4
   before=m.cpu.processorCycles;before_time=m.memory.elapsed_cycles;jobs=len(m.memory.base.transfers)
   m.frame()
   cost=m.cpu.processorCycles-before;max_cycles=max(max_cycles,cost);max_jobs=max(max_jobs,len(m.memory.base.transfers)-jobs)
   elapsed=m.memory.elapsed_cycles-before_time
   # The cycle-driven raster supplies the real wait; no synthetic extra frame.
   self.assertEqual(m.memory.data[G['error']],0)
  self.assertEqual(core(m,'underruns'),0)
  meta=json.loads((ART/'audio-metadata.json').read_text());pcm=m.files['VYSO.DAT'][0x1a00:]
  for voice,index in ((0,15),(1,18)):
   sample=meta['samples'][index];self.assertGreaterEqual(len(m.memory.samples[voice]),sample['length']);self.assertEqual(bytes(m.memory.samples[voice][:sample['length']]),pcm[sample['offset']:sample['offset']+sample['length']])
  print('Stress130frames max modeled6502 CPU cycles:',max_cycles,'DMAjobs/frame:',max_jobs,'underruns:',core(m,'underruns'))
 def test_missing_short_invalid_VYSO_clean_BASIC_failure(self):
  for kind in ('missing','short','header','attic_alias'):
   m=Machine()
   if kind=='missing':del m.files['VYSO.DAT']
   elif kind=='short':m.files['VYSO.DAT']=m.files['VYSO.DAT'][:255]
   elif kind=='header':m.files['VYSO.DAT']=b'BAD!'+m.files['VYSO.DAT'][4:]
   else:m.memory.attic_mask=0x3ffff
   m.boot();self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.error,10);self.assertFalse(m.opened or m.active);self.assertFalse(m.memory.data[G['ready']])
 def test_full_animated_transition_24_to22_and_next_level_no_underrun(self):
  m=self.machine();m.sound('stop');self.core_call(m,'start_source',1,15)
  m.call_at(B.FX['begin']);m.memory.simulate_audio=True;costs=[]
  for frame in range(170):
   m.memory.data[N['c_ps']]=3;m.memory.data[N['c_blink']]=150
   before=m.memory.elapsed_cycles;cpu=m.cpu.processorCycles;m.frame();costs.append(m.cpu.processorCycles-cpu)
   elapsed=m.memory.elapsed_cycles-before
   # The cycle-driven raster supplies the real wait; no synthetic extra frame.
   self.assertEqual(m.memory.data[G['error']],0)
  starts=[(index,frame,n) for voice,index,frame,n in m.memory.starts if voice==0]
  self.assertEqual([i for i,f,n in starts][:2],[19,18]);self.assertEqual((starts[1][1]-starts[0][1])&255,50)
  meta=json.loads((ART/'audio-metadata.json').read_text());pcm=m.files['VYSO.DAT'][0x1a00:];cut=starts[1][2]
  s24=meta['samples'][19];s22=meta['samples'][18];s19=meta['samples'][15]
  self.assertEqual(bytes(m.memory.samples[0][:cut]),pcm[s24['offset']:s24['offset']+cut])
  self.assertEqual(bytes(m.memory.samples[0][cut:cut+s22['length']]),pcm[s22['offset']:s22['offset']+s22['length']])
  self.assertEqual(bytes(m.memory.samples[1][:s19['length']]),pcm[s19['offset']:s19['offset']+s19['length']])
  self.assertEqual(m.memory.data[N['number']],2);self.assertEqual(core(m,'underruns'),0)
  print('Transition170frames max modeled6502 cycles:',max(costs),'Astarts:',starts[:2],'underruns:',core(m,'underruns'))
 def test_banked_gate_preserves_AXYZ_B_flags_and_native_SYS_mapping(self):
  m=self.machine();m.cpu.a=0x5a;m.cpu.x=18;m.cpu.y=7;m.cpu.z=55;m.cpu.b=0x44;m.cpu.p=0xf9
  before=(m.cpu.a,m.cpu.x,m.cpu.y,m.cpu.z,m.cpu.b,m.cpu.p&0xcf)
  m.call_at(G['service'])
  self.assertEqual((m.cpu.a,m.cpu.x,m.cpu.y,m.cpu.z,m.cpu.b,m.cpu.p&0xcf),before)
  self.assertEqual((m.memory.map_mask,m.memory.map_offset),(0x80,0x30000))
 def test_bad_audio_pointer_stops_owned_voices_without_exiting_game(self):
  m=self.machine();self.core_call(m,'start_source',0,13)
  d=m.memory.data;d[C['left_hi']+0x14000]=8;d[C['left_lo']+0x14000]=0
  d[C['cursor_bank']+0x14000]=2;d[C['cursor_hi']+0x14000]=0;d[C['cursor_lo']+0x14000]=0
  self.core_call(m,'fill_half');m.sound('tick')
  self.assertEqual(m.memory.data[G['error']],5);self.assertFalse(core(m,'active'));self.assertFalse(core(m,'active',1))
  x=d[0x1662];m.frame(buttons=0xf7);self.assertEqual(d[0x1662],min(x+2,224));self.assertEqual(m.cpu.pc,N['main_loop'])
 def test_unowned_audio_failure_still_waits_for50Hz_frame(self):
  m=self.machine();d=m.memory.data;d[C['configured']+0x14000]=0;d[C['error']+0x14000]=2
  m.memory.clock_cycles=(m.memory.clock_cycles//810000+1)*810000
  before=m.memory.clock_cycles;m.frame()
  self.assertGreater(m.memory.clock_cycles-before,500000);self.assertEqual(m.cpu.pc,N['main_loop'])
 def test_F1_level100_navigation_GAMEOVER_and_R_preserve_rules(self):
  m=self.machine(100);d=m.memory.data
  self.assertEqual(d[N['number']],100)
  d[N['high_score']:N['high_score']+4]=(123456).to_bytes(4,'little')
  d[N['player1_score']:N['player1_score']+4]=(54321).to_bytes(4,'little')
  saved=(bytes(d[N['high_score']:N['high_score']+4]),bytes(d[N['player1_score']:N['player1_score']+4]),bytes(d[N['player1_lives']:N['player1_lives']+2]))
  m.frame(key=45);self.assertEqual(d[N['number']],99);m.frame();m.frame(key=43);self.assertEqual(d[N['number']],100)
  self.assertEqual((bytes(d[N['high_score']:N['high_score']+4]),bytes(d[N['player1_score']:N['player1_score']+4]),bytes(d[N['player1_lives']:N['player1_lives']+2])),saved)
  d[N['player1_lives']]=1;d[N['player1_lives']+1]=0;m.call('c_player_hit');m.sound('tick')
  for _ in range(21):m.call('c_timers')
  self.assertEqual(d[N['c_ps']],4);m.memory.simulate_audio=True
  for _ in range(12):m.frame()
  self.assertGreater(len(m.memory.samples[0]),0);m.frame(key=65);self.assertEqual(d[N['c_ps']],4)
  m.frame();m.frame(key=82);self.assertEqual(d[N['number']],1)
  self.assertEqual(bytes(d[N['high_score']:N['high_score']+4]),saved[0]);self.assertEqual(int.from_bytes(d[N['player1_score']:N['player1_score']+4],'little'),0)
  self.assertGreater(d[N['player1_lives']],0);self.assertEqual(m.memory.data[G['error']],0)
 def test_packet_integrity_original_assets_and_complete_D81(self):
  import hashlib,struct,build_stage3b1 as DISK
  packet=(ART/'VYSO.DAT').read_bytes();meta=json.loads((ART/'audio-metadata.json').read_text())
  self.assertEqual(packet[:8],b'VYSO\x01\x00\x00\x02');self.assertEqual(len(packet),160960)
  for sample in meta['samples']:
   blob=packet[0x1a00+sample['offset']:0x1a00+sample['offset']+sample['length']]
   self.assertEqual(hashlib.sha256(blob).hexdigest(),sample['sha256'])
  for n in ('VYLV.DAT','VYGR.DAT','VYCL.DAT','VYTI.DAT','VYMN.DAT','VYSH.DAT'):
   self.assertEqual((ART/n).read_bytes(),(ROOT/'releases/stage_7b5b'/n).read_bytes())
  entries=[('STAGE8B',(ART/'STAGE8B.PRG').read_bytes(),0x82)]+[(n,(ART/n).read_bytes(),0x81) for n in ('VYLV.DAT','VYGR.DAT','VYCL.DAT','VYTI.DAT','VYMN.DAT','VYSH.DAT','VYSO.DAT')]
  DISK.verify_disk((ART/'VYPER_STAGE8B.d81').read_bytes(),entries)
if __name__=='__main__':unittest.main()
