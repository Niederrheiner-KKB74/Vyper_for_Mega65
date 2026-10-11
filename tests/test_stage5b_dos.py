"""Protect real DOS physical RAM across actual Stage5b CPU/DMA instructions.
KERNAL I/O is modeled; actual DIRECTORY needs user XEMU acceptance.
"""
import unittest,hashlib
import test_stage5b as T
class TrackedMemory(T.EntryMemory):
    def __setitem__(self,a,v):
        if 0x10000<=a<0x12000:self.dos_writes.append(a)
        super().__setitem__(a,v)
class DOSProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=T.Machine();m=cls.m
        m.memory.__class__=TrackedMemory;m.memory.dos_writes=[]
        cls.pattern=bytes((i*73+19)&255 for i in range(8192))
        m.memory.data[0x10000:0x12000]=cls.pattern
        m.execute();assert m.error==0
        for _ in range(800000):
            if m.cpu.pc==T.N['main_loop']:break
            m.cpu.step()
        else:raise AssertionError('startup')
    def assert_dos(self,m):
        self.assertEqual(m.memory.data[0x10000:0x12000],self.pattern)
        self.assertEqual(m.memory.dos_writes,[])
        self.assertFalse(any(0x10000<=dst<0x12000 or dst<0x10000<dst+n for src,dst,n in m.memory.base.transfers))
    def boot_again(self,m):
        m.execute(T.N['p_startup']);self.assertEqual(m.error,0)
        for _ in range(800000):
            if m.cpu.pc==T.N['main_loop']:return
            m.cpu.step()
        self.fail('second RUN')
    def test_all100_transitions_and_full_clipped_explosion_frames_preserve_dos(self):
        m=self.m;self.assert_dos(m)
        for level in range(1,101):
            m.cpu.a=level;T.call(m,'transition');self.assertEqual(m.error,0);self.assert_dos(m)
        for state in (1,4):
            for x,y in ((60,60),(-1,60),(239,60),(60,-1),(60,199)):
                T.enemies(m);T.setv(m,'c_ps',2);T.target(m,0,state,x&255,y&255)
                for name,value in [('e_xlo',x&255),('e_xhi',(x>>8)&255),('e_ylo',y&255),('e_yhi',(y>>8)&255)]:T.setv(m,name,value)
                T.call(m,'e_render');self.assert_dos(m)
    def test_normal_levelclear_gameover_exits_and_repeated_RUN_preserve_dos(self):
        m=self.m
        for mode in ('normal','level_clear','game_over'):
            m.cpu.a=37;T.call(m,'transition');self.assertEqual(m.error,0)
            if mode=='level_clear':
                T.enemies(m);T.setv(m,'a_enabled',0);T.call(m,'tick');self.assertEqual(T.get(m,'mode'),1)
            elif mode=='game_over':T.setv(m,'c_ps',4)
            m.cpu.pc=T.N['main_loop'];T.frame(m,0x58)
            self.assertEqual(m.cpu.pc,0x200);self.assert_dos(m)
            self.boot_again(m);self.assert_dos(m)
if __name__=='__main__':unittest.main()
