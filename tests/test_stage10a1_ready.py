"""PR88 corrected original turns and Get ready, actual assembled instructions."""
import copy,unittest
import test_stage10a1_two_player as T
from stage10a1_model import N,TP,G,ART,MN,HS
import stage10a1_model as M
import highscore_format as F
R=M.labels(M.namespace(M.SYMBOLS,'getready')[2])
FX=M.labels(M.namespace(M.SYMBOLS,'transitionfx')[2])
class OriginalRules(unittest.TestCase):
 # Reuse helpers and one cold menu without inheriting unrelated test cases.
 setUpClass=classmethod(T.TwoPlayer.setUpClass.__func__)
 fixture=T.TwoPlayer.fixture
 game=T.TwoPlayer.game
 word=T.TwoPlayer.word
 lose=T.TwoPlayer.lose
 eliminated=T.TwoPlayer.eliminated
 assert_lives=T.TwoPlayer.assert_lives
 def test_ready_100_full_frames_freeze_every_game_timer_and_clear_colours(self):
  m=self.game(1,wait_ready=False);d=m.memory.data
  self.assertEqual((d[N['mode']],d[R['gr_timer']]),(3,100))
  self.assert_lives(m,0,3);self.assert_lives(m,1,3)
  before=bytes(d[0x1c00:0x1d00])+bytes(d[0x1e00:0x1f00])+bytes(d[0x1f00:0x1fcc])
  # Ignore audio gate scratch1FD0+, but all combat, ENTRY and shot state is frozen.
  stars=bytes(d[0x4e10:0x4e40]);cycle=d[N['cc_word']:N['cc_word']+2]
  for frame in range(1,101):
   m.game_frame(32 if frame==1 else 0,joy=0xe7)
   self.assertEqual(d[R['gr_timer']],100-frame)
   self.assertEqual(d[N['mode']],3 if frame<100 else 0)
   self.assertEqual(bytes(d[0x1c00:0x1d00])+bytes(d[0x1e00:0x1f00]),before[:512])
   self.assertEqual(bytes(d[N['p_active']:N['p_active']+8]),bytes(8))
  self.assertNotEqual(bytes(d[0x4e10:0x4e40]),stars)
  self.assertNotEqual(d[N['cc_word']:N['cc_word']+2],cycle)
  for row in (17,19):
   # Retired prompt is exactly the ordinary renderer's blank tail+attributes.
   screen=bytes(d[0xe000+row*192+84:0xe000+row*192+184])
   colour=bytes(m.memory[0xff80000+row*192+84+i] for i in range(100))
   m.cpu.x=row;m.call_at(N['s2ia_clear_row'])
   self.assertEqual(screen,bytes(d[0xe000+row*192+84:0xe000+row*192+184]))
   self.assertEqual(colour,bytes(m.memory[0xff80000+row*192+84+i] for i in range(100)))
  self.assertEqual(d[0x1d51],0)
  m.game_frame();self.assertEqual(d[0x1d51],1)
 def test_prompt_positions_exact_highlight_index_and_f1_f2_initial_1_100(self):
  for mode in (1,2):
   for level in (1,100):
    m=self.game(level,wait_ready=False) if mode==2 else self.fixture().game(level,wait_ready=False)
    d=m.memory.data
    for row,x,text in ((17,204,bytes((7,101,116,32,114,101,97,100,121))),(19,208,bytes((16,108,97,121,101,114,32,49)))):
     base=0xe000+row*192+84
     self.assertEqual(int.from_bytes(d[base:base+2],'little'),x)
     self.assertEqual(bytes(d[base+2:base+2+len(text)*2:2]),text)
     self.assertEqual([m.memory[0xff80000+row*192+87+2*i] for i in range(len(text))],[d[N['cc_index']]]*len(text))
    self.assertEqual((d[N['number']],d[R['gr_timer']]),(level,100))
    m.finish_ready();self.assertEqual(d[R['gr_timer']],0)
    m.call_at(N['c_game_over'])
    base=0xe000+9*192+84
    self.assertEqual(bytes(d[base+2:base+20:2]),bytes((7,1,13,5,32,15,22,5,18)))
    self.assertEqual([m.memory[0xff80000+9*192+87+2*i] for i in range(9)],[2]*9)
 def complete(self,m):
  d=m.memory.data
  self.assertEqual(d[N['mode']],0)
  for i in range(23):d[N['c_es']+i]=0
  m.call_at(N['try_complete']);self.assertEqual(d[N['mode']],2)
  # Exact same assembled transition ticks and audio service, no fake finish.
  frames=0
  while d[N['mode']]==2:
   m.call_at(N['tick']);m.call_at(G['tick']);frames+=1
   self.assertLess(frames,140)
  self.assertEqual(frames,129);self.assertEqual(d[N['mode']],3)
  self.assertEqual(d[R['gr_timer']],100)
 def test_level_completion_alternates_own_levels_scores_bonus_and_keeps_audio(self):
  m=self.game(1);d=m.memory.data;sp=m.cpu.sp
  d[0x1a04:0x1a08]=(1234).to_bytes(4,'little');d[0x1fd9]=2
  self.complete(m)
  self.assertEqual((d[TP['active']],d[N['number']]),(1,1))
  self.assertEqual((d[TP['records']+4],d[TP['records']+6],d[0x1fd9]),(2,4,0))
  self.assertEqual(int.from_bytes(d[TP['records']:TP['records']+4],'little'),1234)
  self.assertEqual(int.from_bytes(d[0x1a04:0x1a08],'little'),0)
  self.assertEqual(m.cpu.sp,sp)
  # The original transition PCM source remains live across in-place handoff.
  self.assertTrue(any(d[r]&0x88==0x80 for r in (0xd720,0xd740)))
  self.assertEqual(bytes(d[0xe000+19*192+86:0xe000+19*192+102:2]),bytes((16,108,97,121,101,114,32,50)))
  m.finish_ready();d[0x1a04:0x1a08]=(5678).to_bytes(4,'little');self.complete(m)
  self.assertEqual((d[TP['active']],d[N['number']]),(0,2))
  self.assertEqual(int.from_bytes(d[0x1a04:0x1a08],'little'),1234)
  self.assertEqual(int.from_bytes(d[TP['records']+8:TP['records']+12],'little'),5678)
  self.assertEqual((d[0x1fd9],d[0x1fda]),(0,1))
 def test_one_survivor_and_100_wrap_never_select_dead_player(self):
  for mode in (1,2):
   m=self.game(100) if mode==2 else self.fixture().game(100);d=m.memory.data
   d[TP['records']+14:TP['records']+16]=b'\0\0'
   self.complete(m)
   self.assertEqual((d[TP['active']],d[N['number']],d[TP['records']+4]),(0,1,1))
   self.assertEqual(d[0x1fd9],1);self.assertEqual(d[0x1fda],0)
 def test_gameover_waits_for_name_then_ready_other_no_second_dialog(self):
  m=self.game(100);d=m.memory.data;m.files['VYHI.DAT']=F.encode([(b'OLD',10)])
  d[0x1a04:0x1a08]=(10).to_bytes(4,'little');self.lose(m,0);self.eliminated(m)
  self.assertEqual(m.cpu.pc,HS['main_loop']);self.assertEqual(d[TP['active']],0)
  m.hi_frame()
  for key in b'ONE':m.hi_frame(key);self.assertEqual(d[TP['active']],0)
  m.hi_frame(13,matrix=253);m.hi_frame();m.hi_frame(13)
  self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(d[TP['active']],1)
  self.assertEqual((d[N['number']],d[R['gr_timer']]),(100,100))
  self.assertEqual(F.decode(m.files['VYHI.DAT']),[(b'ONE',10),(b'OLD',10)])
  m.finish_ready();m.files['VYHI.DAT']=F.encode([(b'OLD',100)]*80)
  d[0x1a04:0x1a08]=bytes(4);self.lose(m,0);self.eliminated(m)
  self.assertEqual(m.cpu.pc,MN['menu_loop']);self.assertEqual(bytes(d[TP['handled']:TP['handled']+2]),b'\1\1')
 def test_test_navigation_keeps_actor_bonus_and_100_complete_frames(self):
  m=self.game(100);d=m.memory.data;d[0x1fd9]=2
  for key,target in ((ord('-'),99),(ord('+'),100)):
   m.game_frame(key)
   self.assertEqual((d[N['number']],d[R['gr_timer']],d[TP['active']],d[0x1fd9]),(target,100,0,2))
   self.assertEqual(d[TP['records']+12],100)
   m.game_frame();self.assertEqual(d[R['gr_timer']],99)
   m.finish_ready();m.game_frame() # release navigation latch in ordinary play
  m.game_frame(ord('+'))
  self.assertEqual((d[N['mode']],d[N['number']]),(0,100))
 def test_x_during_ready_restores_bootstraps_and_r_starts_new_100_frames(self):
  for elapsed in (0,50,99):
   m=self.game(wait_ready=False);d=m.memory.data
   for _ in range(elapsed):m.call_at(N['tick'])
   m.game_frame(88);self.assertEqual(m.cpu.pc,0x200)
   self.assertEqual(bytes(d[0x4000:0x4800]),bytes(m.memory.attic[:0x800]))
   self.assertEqual(bytes(d[0x5000:0x5640]),bytes(m.memory.attic[0xa0000:0xa0640]))
  m=self.fixture().game(100);d=m.memory.data;d[N['c_ps']]=4;d[N['c_armed']]=1;d[0x1fe7]=100
  m.game_frame(ord('R'));self.assertEqual((d[N['number']],d[R['gr_timer']]),(1,100))

if __name__=='__main__':unittest.main()
