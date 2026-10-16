"""Actual complete Stage9c3 transition paths; inherited constrained VIC/PCM/DOS models."""
import copy,hashlib,json,os,pickle,unittest
import stage9c3_model as M
from stage9c3_model import N,MN,HS,H,G,C,ART,ROOT
import highscore_format as F
class EngineIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  snapshot=os.getenv('STAGE9C3_BOOT_SNAPSHOT')
  if snapshot:
   with open(snapshot,'rb') as f:cls.menu=pickle.load(f)
   for name in ('VYHS.DAT','VYMN.DAT','VYSO.DAT'):assert cls.menu.files[name]==(ART/name).read_bytes(),'stale fixture'
  else:cls.menu=M.Machine().boot()
  assert cls.menu.cpu.pc==MN['menu_loop'],(hex(cls.menu.cpu.pc),cls.menu.error)
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
if __name__=='__main__':unittest.main()
