"""Actual assembled Stage10a paths; constrained CPU/VIC/PCM/DOS model, not XEMU."""
import copy,pickle,os,unittest
import stage10a_model as M
from stage10a_model import N,MN,HS,H,TP,ART
import highscore_format as F
class TwoPlayer(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  snapshot=os.getenv('STAGE10A_BOOT_SNAPSHOT')
  if snapshot:
   with open(snapshot,'rb') as f:cls.menu=pickle.load(f)
  else:
   from test_stage10a_engine import EngineIntegration
   if not hasattr(EngineIntegration,'menu'):EngineIntegration.setUpClass()
   cls.menu=EngineIntegration.menu
  # All later code changes must trigger a fresh fixture (no stale execution).
  prg=(ART/'STAGE10A.PRG').read_bytes();base=int.from_bytes(prg[:2],'little')
  expected=prg[2:];diff=[base+i for i,b in enumerate(expected) if cls.menu.before[base+i]!=b]
  assert not diff,('stale boot fixture',hex(diff[0]),hex(diff[-1]))
 def fixture(self):return copy.deepcopy(self.menu)
 def game(self,level=1):
  m=self.fixture();m.menu_frame();m.memory.data[MN['initial_level']]=level;m.memory.key=0x89 # MEGA65 F2 PETSCII
  # Use actual F2 mapping from the menu source, not a synthetic controller call.
  m.memory.key=0x89;m.cpu.pc=MN['menu_loop'];m.run_to([N['main_loop'],0x200]);self.assertEqual(m.cpu.pc,N['main_loop'])
  self.assertEqual(m.memory.data[TP['mode']],2);return m
 def word(self,m,a):return int.from_bytes(m.memory.data[a:a+2],'little')
 def lose(self,m,remaining):
  d=m.memory.data;d[N['c_ps']]=0;d[0x1a0a:0x1a0c]=(remaining+1).to_bytes(2,'little')
  m.call_at(N['c_player_hit']);self.assertEqual(self.word(m,0x1a0a),remaining)
  for _ in range(21):m.call_at(N['c_timers'])
  self.assertEqual(d[N['c_ps']],2 if remaining else 4)
  d[M.G['command']]=1;m.call_at(M.G['gate']) # service the queued original death sound before inspecting its hardware completion
 def eliminated(self,m):
  m.memory.data[H['over_clock']]=149;m.game_frame();return m
 def close_name(self,m,name=b'NEW'):
  m.hi_frame()
  for c in name:m.hi_frame(c)
  m.hi_frame(13,matrix=253);m.hi_frame();m.hi_frame(13)
 def test_f2_initial_level_independent_state_and_p1_starts(self):
  m=self.game(29);d=m.memory.data
  self.assertEqual(d[TP['active']],0);self.assertEqual(d[TP['records']+4],29);self.assertEqual(d[TP['records']+12],29)
  self.assertEqual((self.word(m,0x1a0a),self.word(m,TP['records']+14)),(3,3));self.assertEqual(bytes(d[0x1fd9:0x1fdb]),b'\0\0')
 def test_switch_after_full_explosion_and_sound_then_restore_own_level(self):
  m=self.game(4);d=m.memory.data;initial_sp=m.cpu.sp;d[0x1a04:0x1a08]=(1234).to_bytes(4,'little');d[0x1a00:0x1a04]=(1234).to_bytes(4,'little');d[0x1fd9]=2
  self.lose(m,2);d[0xd720]=0x80;m.game_frame();self.assertEqual(d[TP['active']],0);self.assertEqual(d[N['c_ps']],2)
  d[0xd720]=2;m.game_frame();self.assertEqual(d[TP['active']],1);self.assertEqual(m.cpu.sp,initial_sp);self.assertEqual(d[N['number']],4);self.assertEqual(d[N['c_ps']],3)
  self.assertEqual(int.from_bytes(d[0x1a04:0x1a08],'little'),0);self.assertEqual(int.from_bytes(d[0x1a00:0x1a04],'little'),1234)
  self.assertEqual((d[N['c_blink']],d[N['c_flash']],d[N['c_visible']]),(150,25,1))
  m.cpu.a=37;m.call_at(N['transition']);d[0x1a04:0x1a08]=(5678).to_bytes(4,'little');d[0x1fda]=1
  self.lose(m,2);d[0xd720]=2;m.game_frame();self.assertEqual(d[TP['active']],0);self.assertEqual(m.cpu.sp,initial_sp);self.assertEqual(d[N['number']],4)
  self.assertEqual(int.from_bytes(d[0x1a04:0x1a08],'little'),1234);self.assertEqual(d[TP['records']+12],37);self.assertEqual(bytes(d[0x1fd9:0x1fdb]),bytes((2,1)))
  self.assertEqual(bytes(d[N['p_active']:N['p_active']+8]),bytes(8));self.assertEqual(d[M.G['error']],0)
 def test_independent_bonus_saturation_and_both_hud_icon_caps(self):
  m=self.game();d=m.memory.data
  for active in (0,1):
   d[TP['active']]=active
   for lives in (0,1,2,8,9,29,30):
    d[0x1a0a:0x1a0c]=lives.to_bytes(2,'little');d[0x1fd9+active]=2;other=d[0x1fda-active]
    m.call_at(N['bonus_completed']);self.assertEqual(self.word(m,0x1a0a),lives if lives in (0,30) else lives+1);self.assertEqual(d[0x1fd9+active],0);self.assertEqual(d[0x1fda-active],other)
   for lives in (0,1,2,8,9,29,30):
    d[0x1a0a:0x1a0c]=lives.to_bytes(2,'little');m.call_at(TP['render'])
    rows=range(7,12) if active==0 else range(15,20)
    count=sum(1 for y in rows for x in range(0,40,2) if int.from_bytes(d[0xe000+192*y+42+x:0xe000+192*y+44+x],'little') in (0x321,0x322,0x323))
    self.assertEqual(count,min(8,lives)*3,(active,lives,count))
 def test_each_elimination_gets_own_score_ties_new_before_old_then_survivor(self):
  m=self.game();d=m.memory.data;m.files['VYHI.DAT']=F.encode([(b'OLD',10),(b'END',10)])
  d[0x1a04:0x1a08]=(10).to_bytes(4,'little');self.lose(m,0);self.eliminated(m);self.assertEqual(m.cpu.pc,HS['main_loop']);self.close_name(m,b'ONE')
  self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(d[TP['active']],1);self.assertEqual(d[TP['handled']],1)
  self.assertEqual(F.decode(m.files['VYHI.DAT']),[(b'ONE',10),(b'OLD',10),(b'END',10)])
  self.lose(m,2);d[0xd720]=2;m.game_frame();self.assertEqual(d[TP['active']],1);self.assertEqual(d[N['c_ps']],2) # existing wait, no swap to dead P1
  d[0x1a04:0x1a08]=(10).to_bytes(4,'little');self.lose(m,0);self.eliminated(m);self.close_name(m,b'TWO')
  self.assertEqual(m.cpu.pc,MN['menu_loop']);self.assertEqual(F.decode(m.files['VYHI.DAT']),[(b'TWO',10),(b'ONE',10),(b'OLD',10),(b'END',10)])
 def test_reverse_elimination_nonqual_and_cancel_leave_survivor(self):
  for qualified in (False,True):
   m=self.game();d=m.memory.data
   self.lose(m,2);d[0xd720]=2;m.game_frame();self.assertEqual(d[TP['active']],1)
   m.files['VYHI.DAT']=F.encode([] if qualified else [(b'OLD',100)]*80)
   d[0x1a04:0x1a08]=(1).to_bytes(4,'little');self.lose(m,0);self.eliminated(m)
   if qualified:m.hi_frame();m.hi_frame(27)
   self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(d[TP['active']],0);self.assertEqual(d[TP['handled']+1],1);self.assertEqual(m.written,[])
 def test_actual_dma_death_sample_completion_and_respawn_controls(self):
  m=self.game();d=m.memory.data;m.memory.simulate_audio=True
  self.lose(m,2)
  self.assertEqual(d[TP['active']],0)
  frames=0
  while d[TP['active']]==0 and frames<150:
   m.game_frame();frames+=1
  self.assertLess(frames,150);self.assertGreater(frames,50)
  self.assertEqual(d[TP['active']],1);self.assertEqual(d[M.G['error']],0)
  self.assertEqual(d[N['c_ps']],3)
  # New identity stays protected, controllable, and can fire during hidden blink.
  d[N['c_visible']]=0;d[0xdc00]=0xfb;x=d[0x1662]
  m.call_at(N['c_move']);self.assertEqual(d[0x1662],x-2)
  d[0xdc00]=0xe7;m.call_at(N['c_move']);self.assertEqual(d[0x1662],x)
  m.call_at(N['p_player_fire']);self.assertEqual(d[N['p_active']],1)
  self.assertEqual(d[N['p_xpos']],x+8);self.assertEqual(d[N['p_ypos']],184)
  lives=self.word(m,0x1a0a);m.call_at(N['c_player_hit']);self.assertEqual(self.word(m,0x1a0a),lives)
 def test_identity_hud_scores_levels_and_active_marker_after_redraw(self):
  m=self.game(4);d=m.memory.data
  d[0x1a04:0x1a08]=(1234).to_bytes(4,'little');m.call_at(TP['render'])
  self.assertEqual(d[0xe000+3*192+46],0x3e);self.assertEqual(d[0xe000+12*192+46],0x20)
  for row,text in ((4,'0001234'),(13,'0000000')):
   self.assertEqual(''.join(chr(d[0xe000+192*row+42+2*(i+3)]) for i in range(7)),text)
  m.cpu.a=4;m.call_at(N['transition'])
  # The existing level redraw invalidates identity shadows before publication:
  for row,text in ((4,'0001234'),(13,'0000000')):
   self.assertEqual(''.join(chr(d[0xe000+192*row+42+2*(i+3)]) for i in range(7)),text)
 def test_x_has_priority_on_the_exact_frame_a_switch_becomes_ready(self):
  for identity in (0,1):
   m=self.game();d=m.memory.data
   if identity:
    self.lose(m,2);d[0xd720]=2;m.game_frame()
   self.lose(m,2);d[0xd720]=2
   m.game_frame(ord('X'));self.assertEqual(m.cpu.pc,0x200)
   self.assertEqual(d[TP['active']],identity)
 def test_skips_wrap_and_restart_do_not_touch_other_bonus_or_score(self):
  m=self.game(100);d=m.memory.data;d[0x1fd9]=2;d[0x1fda]=1
  d[0x1a04:0x1a08]=(55).to_bytes(4,'little')
  m.game_frame(ord('+'));self.assertEqual(d[N['number']],100);m.game_frame();m.game_frame(ord('-'));self.assertEqual(d[N['number']],99)
  self.assertEqual(bytes(d[0x1fd9:0x1fdb]),bytes((2,1)));self.assertEqual(int.from_bytes(d[0x1a04:0x1a08],'little'),55)
  self.assertEqual(d[TP['records']+12],100)
  # Existing transition-complete next_level helper is used unchanged.
  m.cpu.a=100;m.call_at(N['transition'])
  d[N['c_ps']]=0
  for i in range(23):d[N['c_es']+i]=0
  m.call_at(N['try_complete'])
  for _ in range(130):m.call_at(N['tick'])
  self.assertEqual(d[N['number']],1)
if __name__=='__main__':unittest.main()
