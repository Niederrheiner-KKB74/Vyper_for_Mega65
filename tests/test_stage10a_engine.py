"""Actual complete Stage10a transition paths; inherited constrained VIC/PCM/DOS models."""
import copy,hashlib,json,os,pickle,unittest
import stage10a_model as M
from stage10a_model import N,MN,HS,H,G,C,ART,ROOT
import highscore_format as F
class EngineIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  snapshot=os.getenv('STAGE10A_BOOT_SNAPSHOT')
  if snapshot:
   with open(snapshot,'rb') as f:cls.menu=pickle.load(f)
   for name in ('VYHS.DAT','VYMN.DAT','VYSO.DAT'):assert cls.menu.files[name]==(ART/name).read_bytes(),'stale fixture'
  else:cls.menu=M.Machine().boot()
  assert cls.menu.cpu.pc==MN['menu_loop'],(hex(cls.menu.cpu.pc),cls.menu.error)
  save_snapshot=os.getenv('STAGE10A_SAVE_BOOT_SNAPSHOT')
  if save_snapshot:
   with open(save_snapshot,'wb') as f:pickle.dump(cls.menu,f)
 def fixture(self):return copy.deepcopy(self.menu)
 def open_f3(self,m,entries=None):
  if entries is not None:m.files['VYHI.DAT']=F.encode(entries)
  m.menu_frame();m.menu_frame(0x86);self.assertEqual(m.cpu.pc,HS['main_loop']);m.hi_frame()
 def test_f3_repeat_pages_exit_menu_settings_and_game_start(self):
  m=self.fixture();m.memory.data[MN['initial_level']]=29
  for _ in range(3):
   self.open_f3(m,[(b'OLD',30)])
   self.assertEqual(m.entries(),[(b'OLD',30)])
   for page in range(1,4):m.hi_frame(29);m.hi_frame();self.assertEqual(m.memory.data[HS['page']],page)
   m.hi_frame(13);self.assertEqual(m.cpu.pc,MN['menu_loop']);self.assertEqual(m.memory.data[MN['initial_level']],29)
   self.assertEqual(m.memory.data[MN['selection']],3)
   self.assertEqual(m.memory.data[0xd015],0)
   for r in (0xd720,0xd740):self.assertNotEqual(m.memory.data[r]&0x88,0x80)
  m.game(29);self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(m.memory.data[N['number']],29)
 def test_held_opening_and_exit_controls_do_not_reopen(self):
  m=self.fixture();self.open_f3(m)
  m.hi_frame(13);self.assertEqual(m.cpu.pc,MN['menu_loop'])
  for _ in range(4):m.menu_frame(0x86,joy=0xef,matrix=0xb5);self.assertEqual(m.cpu.pc,MN['menu_loop'])
  m.menu_frame();m.menu_frame(0x86);self.assertEqual(m.cpu.pc,HS['main_loop'])
 def finish_game(self,m,score,entries):
  m.files['VYHI.DAT']=F.encode(entries);m.game(1)
  d=m.memory.data;d[0x1a04:0x1a08]=score.to_bytes(4,'little');d[N['c_ps']]=4;d[H['over_clock']]=148
  m.game_frame();self.assertEqual(d[H['over_clock']],149);self.assertEqual(m.cpu.pc,N['main_loop'])
  m.game_frame();return m
 def test_gameover_name_save_exactly_once_reload_and_new_f1(self):
  m=self.fixture();entries=[(b'AAA',20),(b'OLD',10),(b'END',10)];self.finish_game(m,10,entries)
  self.assertEqual(m.cpu.pc,HS['main_loop']);self.assertEqual(m.memory.data[HS['hi_mode']],2)
  m.hi_frame()
  for k in b'NEW':m.hi_frame(k)
  m.hi_frame(13,matrix=253);expected=[(b'AAA',20),(b'NEW',10),(b'OLD',10),(b'END',10)]
  self.assertEqual(F.decode(m.files['VYHI.DAT']),expected)
  after=dict(m.files)
  for _ in range(3):m.hi_frame(13,matrix=253)
  self.assertEqual(m.files,after);m.hi_frame();m.hi_frame(13);self.assertEqual(m.cpu.pc,MN['menu_loop'])
  self.open_f3(m);self.assertEqual(m.entries(),expected);m.hi_frame(13)
  m.game(4);self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(int.from_bytes(m.memory.data[0x1a00:0x1a04],'little'),20)
  for _ in range(4):m.game_frame()
  self.assertEqual(m.memory.data[G['error']],0)
 def test_gameover_nonqual_cancel_and_r_restart_no_write(self):
  m=self.fixture();entries=[(b'OLD',100-i) for i in range(80)];self.finish_game(m,20,entries);self.assertEqual(m.cpu.pc,MN['menu_loop']);self.assertEqual(m.written,[])
  m=self.fixture();self.finish_game(m,100,[]);m.hi_frame();m.hi_frame(27);self.assertEqual(m.cpu.pc,MN['menu_loop']);self.assertEqual(m.written,[])
  m=self.fixture();m.game(1);d=m.memory.data;d[N['c_ps']]=4;d[N['c_armed']]=1;d[H['over_clock']]=100
  m.game_frame(ord('R'));self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(d[N['c_ps']],0);self.assertEqual(d[H['over_clock']],0);self.assertEqual(m.written,[])
 def test_level_paths_and_sound_core_unchanged_then_x_and_run(self):
  for level in (1,4,99,100):
   m=self.fixture();m.game(level)
   for _ in range(5):m.game_frame()
   self.assertEqual(m.memory.data[N['error']],0);self.assertEqual(m.memory.data[G['error']],0)
   gate=bytes(m.memory.data[0x1920:0x1920+194]);self.assertEqual(gate[:3],self.menu.memory.data[0x1920:0x1923])
   self.assertEqual(m.memory.attic[0x31a00:0x574c0],self.menu.memory.attic[0x31a00:0x574c0])
  m=self.fixture();self.open_f3(m);m.hi_frame(88);self.assertEqual(m.cpu.pc,0x200)
  # Re-enter the real startup chain after the table's BASIC exit.
  m.cpu.pc=N['p_startup'];m.cpu.stPushWord(0x1ff);m.boot();self.assertEqual(m.cpu.pc,MN['menu_loop'])

class RespawnIntegration(EngineIntegration):
 # Share the full cold-boot fixture; inherit only fixture helpers, not test copies.
 @classmethod
 def setUpClass(cls):
  if not hasattr(EngineIntegration,'menu'):EngineIntegration.setUpClass()
  cls.menu=EngineIntegration.menu
 def test_25_frame_visual_blink_movement_two_hidden_shots_and_protection(self):
  m=self.fixture();m.game(1);d=m.memory.data
  for i in range(23):d[N['c_es']+i]=0
  d[N['c_ps']]=2;d[N['c_px']]=112;d[N['c_py']]=184
  d[N['c_visible']]=0;d[N['c_flash']]=7
  m.call_at(N['c_wait'])
  self.assertEqual((d[N['c_ps']],d[N['c_blink']],d[N['c_flash']],d[N['c_visible']]),(3,150,25,1))
  lives=bytes(d[0x1a0a:0x1a0c]);samples=len(m.memory.starts)
  for frame in range(1,151):
   m.call_at(N['c_timers'])
   expected=1 if frame==150 else 1-(frame//25)%2
   self.assertEqual(d[N['c_visible']],expected,frame)
   self.assertEqual(d[N['c_ps']],0 if frame==150 else 3,frame)
   if frame<150:
    m.call_at(N['c_player_hit']);self.assertEqual(bytes(d[0x1a0a:0x1a0c]),lives)
   if frame in (1,24,25,49,50,74,75,99,100,124,125,149,150):
    m.call_at(N['e_render'])
    count=sum(d[N['v014_row_count']:N['v014_row_count']+25]);self.assertEqual(count,2 if expected else 0,frame)
   if frame==25:
    self.assertEqual(d[N['c_visible']],0)
    d[0xdc00]=255;m.call_at(N['c_move']);m.call_at(N['c_tick_update']) # release
    for slot,joy in ((0,0xe7),(1,0xeb)):
     old=d[0x1662];d[0xdc00]=joy;m.call_at(N['c_move']);self.assertEqual(d[0x1662],old+(2 if slot==0 else -2));self.assertEqual(d[0x1664],184)
     m.call_at(N['c_tick_update']);self.assertEqual(d[N['p_active']+slot],1)
     self.assertEqual(d[N['p_xpos']+slot],d[0x1662]+8);self.assertEqual(d[N['p_ypos']+slot],184)
     m.call_at(N['c_tick_update']);self.assertEqual(sum(d[N['p_active']:N['p_active']+2]),slot+1)
     d[0xdc00]=255;m.call_at(N['c_move']);m.call_at(N['c_tick_update'])
    starts=len(m.memory.starts);d[0xdc00]=0xef;m.call_at(N['c_move']);m.call_at(N['c_tick_update'])
    self.assertEqual(sum(d[N['p_active']:N['p_active']+2]),2);self.assertEqual(len(m.memory.starts),starts)
    self.assertEqual(d[N['c_visible']],0)
  self.assertEqual(d[N['c_blink']],0);self.assertEqual(d[N['c_visible']],1)
  m.call_at(N['c_player_hit']);self.assertEqual(d[N['c_ps']],1);self.assertEqual(int.from_bytes(d[0x1a0a:0x1a0c],'little'),int.from_bytes(lives,'little')-1)
 def test_gameover_overlay_has_only_original_gameover_caption(self):
  m=self.fixture();m.game(1);d=m.memory.data
  for i in range(23):d[N['c_es']+i]=0
  d[N['c_ps']]=4;m.call_at(N['e_render'])
  before=bytes(d[0xe000:0xe000+25*192]);m.call_at(N['c_game_over']);after=bytes(d[0xe000:0xe000+25*192])
  changed=[row for row in range(25) if before[row*192:(row+1)*192]!=after[row*192:(row+1)*192]]
  self.assertEqual(changed,[9])
# Prevent inherited engine tests running a second time in the respawn subclass.
for _name in list(vars(EngineIntegration)):
 if _name.startswith('test_'):setattr(RespawnIntegration,_name,None)

if __name__=='__main__':unittest.main()
