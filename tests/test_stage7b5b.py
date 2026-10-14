"""Execute assembled45GS02 instructions in inherited constrained CPU/DMA model, not XEMU."""
import json,re,unittest,os
from pathlib import Path
import test_stage7b5a as B
ROOT=B.ROOT;ART=Path(os.getenv('STAGE7B5B_ARTIFACTS',str(ROOT/'releases/stage_7b5b')))
class ArtifactNames:
 def __truediv__(self,name):return ART/name.replace('STAGE7B5A','STAGE7B5B')
B.ART=ArtifactNames()
sym=(ART/'STAGE7B5B.sym').read_text()
block=sym.split('.namespace motion {',1)[1].split('\n}',1)[0]
M={n:int(a,16) for n,a in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',block)}
a=sym.index('.namespace motion {');b=sym.index('\n}',a)+2;flat=sym[:a]+sym[b:]
B.N,B.S=B.star_symbols(flat);B.N['original']=0x31f0
N=B.N
B.FE={n:int(a,16) for n,a in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',sym.split('.namespace fireevents {',1)[1].split('\n}',1)[0])}
for mod in (B.OLD,B.OLD.OLD,B.OLD.OLD.T,B.OLD.OLD.T.PREV):mod.N=N
T=B.OLD.OLD.T

def put(m,n,v,i=0):m.memory.data[N.get(n,M.get(n))+i]=v&255
def get(m,n,i=0):return m.memory.data[N.get(n,M.get(n))+i]
def word(m,lo,hi,i=0):
 v=get(m,lo,i)+256*get(m,hi,i);return v-65536 if v&32768 else v
def call(m,n):
 m.cpu.pc=M[n];m.cpu.stPushWord(0x1ff);return m.run_to([0x200],2_000_000)
def velocity(m,i):return (get(m,'p_vx',i)<<16)+(get(m,'p_vxfrac',i)<<8)+get(m,'p_vyfrac',i)
def original_step(dx,dy,v):return v<<16 if dy<=0 or abs(dx)>=dy else ((abs(dx)<<16)//dy)*v

class MotionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  B.MenuTests.setUpClass();cls.boot=B.MenuTests.boot
 def machine(self):return B.MenuTests().machine().game(1)
 def ready(self,ex=90,ey=70,px=112,parity=0,dy=1):
  m=self.machine();T.enemies(m,0)
  for n,v in [('c_es',2),('e_phase',1),('e_visible',1),('e_xlo',ex),('e_xhi',0),('e_ylo',ey),('e_yhi',0),('a_hidden',0)]:put(m,n,v)
  m.memory.data[0x1662]=px;put(m,'e_ticklo',parity);B.fset(m,'dy_original',dy)
  return m
 def fire(self,m,slot=2):
  put(m,'a_source',0);m.cpu.x=slot;call(m,'spawn');return slot
 def test_loader_menu_six_DATs_and_base_assets(self):
  B.MenuTests.test_full_loader_title_and_exact_menu_pixels(self)
  for n in ('VYLV.DAT','VYGR.DAT','VYCL.DAT','VYTI.DAT','VYMN.DAT','VYSH.DAT','projectile_sprites.bin'):
   self.assertEqual((ART/n).read_bytes(),(ROOT/'releases/stage_7b5a'/n).read_bytes(),n)
 def test_player_step_clamps_50_100_frames_muzzle_respawn(self):
  m=self.machine()
  for joy,step in [(0xfb,-2),(0xf7,2)]:
   m.memory.data[0x1662]=112;m.memory.data[0xdc00]=joy
   for count in range(1,101):
    m.call('v014_move_record');self.assertEqual(m.memory.data[0x1662],max(0,min(224,112+step*count)),count)
    self.assertEqual(m.memory.data[0x1664],184)
  for start,joy,end in [(1,0xfb,0),(223,0xf7,224)]:
   m.memory.data[0x1662]=start;m.memory.data[0xdc00]=joy;m.call('v014_move_record');self.assertEqual(m.memory.data[0x1662],end)
  put(m,'v014_joy_sample',0xef);put(m,'p_fire_latch',0);m.call('p_player_fire')
  self.assertEqual((get(m,'p_xpos'),get(m,'p_ypos')),(232,184))
  put(m,'c_ps',3);m.memory.data[0xdc00]=0xfb;before=m.memory.data[0x1662];m.call('c_move');self.assertEqual(m.memory.data[0x1662],before-2)
 def test_actual_mainloop_one_move_per_frame_and_instruction_budget(self):
  m=self.ready();put(m,'a_ready',0);put(m,'c_ps',3)
  m.memory.data[0x1662]=0
  counts={'moves':0,'instructions':0};original=m.cpu.step
  def step():
   counts['instructions']+=1
   if m.cpu.pc==N['v014_move_record']:counts['moves']+=1
   return original()
  m.cpu.step=step
  positions={}
  for frame in range(1,101):
   m.frame(buttons=0xf7)
   if frame in (50,100):positions[frame]=m.memory.data[0x1662]
  self.assertEqual(counts['moves'],100);self.assertEqual(positions,{50:100,100:200})
  # Per routine, report actual model instructions, not asserted native bus cycles.
  put(m,'e_xlo',90);put(m,'e_ylo',70);put(m,'e_xhi',0);put(m,'e_yhi',0);m.memory.data[0x1662]=112;B.fset(m,'dy_original',3)
  counts['instructions']=0;self.fire(m);spawn_count=counts['instructions']
  for i in range(2,8):
   put(m,'format',1,i);put(m,'p_active',1,i);put(m,'p_ypos',20,i);put(m,'yhi',0,i);put(m,'p_vy',3,i)
   put(m,'p_vx',2,i);put(m,'p_vxfrac',127,i);put(m,'p_vyfrac',255,i)
  counts['instructions']=0;m.call('p_update');update_count=counts['instructions']
  (ART/'motion-test-measurements.json').write_text(json.dumps({'scope':'actual assembled instructions in host CPU model; NOT hardware cycle/raster timing','player_frames':100,'movement_calls':counts['moves'],'player_x_at_frame50':positions[50],'player_x_at_frame100':positions[100],'one_fractional_spawn_instructions':spawn_count,'six_projectile_update_instructions':update_count},indent=2)+'\n')
 def test_hit_explosion_respawn_keeps_X_and_blink_move(self):
  m=self.machine();T.enemies(m,0);put(m,'c_ps',0);m.memory.data[0x1662]=73
  m.call('c_player_hit');self.assertEqual(get(m,'c_px'),73)
  for _ in range(21):m.call('c_timers')
  self.assertEqual(get(m,'c_ps'),2);m.call('c_wait')
  self.assertEqual((get(m,'c_ps'),m.memory.data[0x1662],m.memory.data[0x1664]),(3,73,184))
  m.memory.data[0xdc00]=0xf7;m.call('c_move');self.assertEqual(m.memory.data[0x1662],75)
 def test_isolated_legacy_T_keeps_old_8_8_update(self):
  m=self.machine();put(m,'p_test_enabled',1);i=2;put(m,'format',0,i)
  for n,v in [('p_active',1),('p_xpos',100),('p_ypos',100),('p_vx',255),('p_vxfrac',128),('p_vy',1),('p_vyfrac',0),('p_xfrac',0),('p_yfrac',0)]:put(m,n,v,i)
  m.call('p_update');self.assertEqual((get(m,'p_xpos',i),get(m,'p_ypos',i)),(99,101))
  put(m,'p_test_enabled',0) # already flying legacy shot must keep its own format
  m.call('p_update');self.assertEqual((get(m,'p_xpos',i),get(m,'p_ypos',i)),(99,102))
 def test_levelclear_100_wrap_R_and_event_reset_F1(self):
  next(c for c in vars(B).values() if isinstance(c,type) and 'test_level_clear_press_release_wrap_score_lives_and_R' in vars(c)).test_level_clear_press_release_wrap_score_lives_and_R(self)
  original_ready=self.ready;self.ready=lambda actor=0:B.OriginalEventTests.ready(self,actor)
  try:B.OriginalEventTests.test_level_transition_R_and_menu_F1_reinitialize_events(self)
  finally:self.ready=original_ready
 def test_native_fraction_floor_before_DY_45degree_and_sign(self):
  m=self.machine()
  for dy in (1,2,3):
   for dx,delta in [(0,121),(1,121),(33,121),(120,121),(121,121),(200,121),(-1,121),(-33,121),(-120,121),(-121,121),(-200,121),(3,0),(3,-1)]:
    # Invoke actual aim using signed centred origins; legal and edge cases.
    i=2;put(m,'p_xpos',100,i);put(m,'xhi',0,i);target=100+dx
    put(m,'p_target_x',target,i);put(m,'targethi',target>>8,i)
    y=184-delta;put(m,'p_ypos',y,i);put(m,'yhi',y>>8,i);put(m,'p_target_y',184,i);put(m,'p_vy',dy,i)
    put(m,'p_vyfrac',0,i);put(m,'p_vxfrac',0,i);put(m,'p_yfrac',0,i);put(m,'p_xfrac',0,i)
    m.cpu.x=i;call(m,'aim');self.assertEqual(velocity(m,i),original_step(dx,delta,dy),(dx,delta,dy))
    self.assertEqual(get(m,'sign',i),255 if dx<0 else 0)
    self.assertLessEqual(velocity(m,i),dy<<16)
    # native accumulators, signed X, Y-first expiry; compare every step.
    xpos=100;frac=0;ypos=y;vel=velocity(m,i)
    for frame in range(1,8):
     m.call('p_update');ypos+=dy
     self.assertEqual(word(m,'p_ypos','yhi',i),ypos)
     if ypos>=200:
      self.assertEqual(get(m,'p_active',i),0);break
     total=frac+vel;frac=total&65535;xpos+=(total>>16)*(-1 if dx<0 else 1)
     self.assertEqual(word(m,'p_xpos','xhi',i),xpos,(dx,delta,dy,frame))
     self.assertEqual((get(m,'p_xfrac',i)<<8)+get(m,'p_yfrac',i),frac)
 def test_spread_full_range_parity_projected_muzzle_and_rng_isolation(self):
  m=self.ready();seen={0:set(),1:set()}
  attack_before=bytes(m.memory.data[N['p_random_lo']:N['p_random_hi']+1]);planning_before=B.fget(m,'seed')+256*B.fget(m,'seed',1)
  for parity in (0,1):
   put(m,'e_ticklo',parity)
   for _ in range(128):
    self.fire(m);spread=get(m,'spread');seen[parity].add(spread)
    self.assertEqual(get(m,'p_target_x',2),113+(spread if parity else -spread))
    self.assertEqual((word(m,'p_xpos','xhi',2),word(m,'p_ypos','yhi',2)),(98,63))
  self.assertEqual(seen,{0:set(range(20)),1:set(range(20))})
  self.assertEqual(bytes(m.memory.data[N['p_random_lo']:N['p_random_hi']+1]),attack_before)
  self.assertEqual(B.fget(m,'seed')+256*B.fget(m,'seed',1),planning_before)
  m.memory.data[0x1662]=0;put(m,'e_ticklo',0);put(m,'seed',20);put(m,'seed',0,1);self.fire(m)
  self.assertEqual(word(m,'p_target_x','targethi',2),-9)
 def test_signed_offscreen_no_wrap_collision_or_early_X_death(self):
  m=self.ready(ex=0,ey=0,px=0);self.fire(m);i=2
  self.assertEqual(word(m,'p_ypos','yhi',i),-7)
  m.cpu.x=i;call(m,'visible');self.assertFalse(m.cpu.p&m.cpu.CARRY)
  put(m,'p_xpos',0,i);put(m,'xhi',0,i);put(m,'p_ypos',100,i);put(m,'yhi',0,i)
  put(m,'p_vx',3,i);put(m,'sign',255,i);put(m,'p_vy',1,i);put(m,'p_vxfrac',0,i);put(m,'p_vyfrac',0,i)
  m.call('p_update');self.assertEqual(word(m,'p_xpos','xhi',i),-3);self.assertEqual(get(m,'p_active',i),1)
  m.call('p_publish');self.assertEqual(m.memory.data[0xd015]&4,0)
  put(m,'p_ypos',199,i);m.call('p_update');self.assertEqual(get(m,'p_active',i),0)
 def test_six_pool_event_consumption_owner_death_and_player_independence(self):
  m=self.ready()
  for i in range(6):B.fset(m,'pending',1);m.call('a_fire')
  self.assertEqual([get(m,'p_active',i) for i in range(2,8)],[1]*6)
  seed=get(m,'seed')+256*get(m,'seed',1);B.fset(m,'pending',3);m.call('a_fire')
  self.assertEqual(B.fget(m,'pending'),0);self.assertEqual(get(m,'seed')+256*get(m,'seed',1),seed)
  put(m,'c_es',0);put(m,'p_active',1);put(m,'p_xpos',50);put(m,'p_ypos',100);put(m,'p_vy',253)
  m.call('p_update');self.assertEqual(get(m,'p_ypos'),97)
  self.assertEqual([get(m,'p_active',i) for i in range(2,8)],[1]*6)
 def test_all100_level_DY_reset_and_representative_frames(self):
  m=self.machine();levels=json.loads((ART/'fire-parameters.json').read_text())['levels']
  for row in levels:
   put(m,'xhi',255,7);put(m,'yhi',255,7);put(m,'seed',0)
   m.call('transition',row['level']);self.assertEqual(m.error,0,row['level'])
   self.assertEqual(B.fget(m,'dy_original'),row['DY_stored_only'])
   self.assertEqual(bytes(m.memory.data[M['xhi']:M['xhi']+32]),bytes(32))
   self.assertEqual(get(m,'seed')+256*get(m,'seed',1),0x7b5b)
   self.assertEqual(bytes(m.memory.data[M['format']:M['format']+8]),bytes(8))
  for lv in (1,3,29,54,100):
   m.call('transition',lv)
   for _ in range(50):m.frame()
   self.assertEqual(m.error,0,lv)
 def test_byte_identity_events_attack_selection_loader_and_art(self):
  old=(ROOT/'releases/stage_7b5a/STAGE7B5A.PRG').read_bytes()[2:];new=(ART/'STAGE7B5B.PRG').read_bytes()[2:]
  for lo,hi in [(0xa600,0xaf08),(0x9c00,0x9cee),(0x4f00,0x4fb2),(0x4800,0x4b57),(0x8a00,0x8a80),(0xc100,0xc800),(0xb480,0xb800)]:
   self.assertEqual(new[lo-0x2001:hi-0x2001],old[lo-0x2001:hi-0x2001],hex(lo))
 # Carry forward event regressions whose expected motion is independent of Stage7b5a.
 machine_event=B.OriginalEventTests.machine
 ready_event=B.OriginalEventTests.ready
 def test_event_schedule_unchanged(self):
  original_ready=self.ready
  self.ready=lambda actor=0:B.OriginalEventTests.ready(self,actor)
  try:
   for method in ('test_countdown_word_zero_independent_and_no_retry','test_actual_ENTRY_curve_hook_wait_and_B2_offbyone','test_attack_threshold_formula_and_guard_uses_original_coordinate_basis','test_attack_thresholds_once_including_second_before_first_and_same_frame','test_full_pool_consumes_both_events_and_does_not_retry_after_release','test_wait_dead_exploding_hidden_invalid_origins_discard_pending','test_event_planning_and_flushing_do_not_consume_attack_RNG'):
    getattr(B.OriginalEventTests,method)(self)
  finally:self.ready=original_ready
 def test_BASIC_exit_second_RUN(self):
  B.ExitAndCurveTests.test_eight_sprite_snapshot_restored_and_IRQ_enabled_on_BASIC_exit(self)
if __name__=='__main__':unittest.main()
