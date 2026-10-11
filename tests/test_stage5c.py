"""Stage5c assembled loader, palette banks and inherited combat regression; not XEMU."""
import unittest,json,struct,tempfile
from pathlib import Path
import test_stage5b as T
import convert_stage5c_palettes as PAL
import build_stage5c as BUILD
ROOT=T.ROOT
N=T.BUILD.symbols((ROOT/'releases/stage_5c/STAGE5C.sym').read_text())
OriginalMachine=T.Machine
class Machine(OriginalMachine):
    def __init__(self):
        super().__init__()
        p=(ROOT/'releases/stage_5c/STAGE5C.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.files['VYCL.DAT']=(ROOT/'assets/stage5c/VYCL.DAT').read_bytes()
        self.cpu.pc=N['p_startup'];self.before=bytes(self.memory.data)
        self.devices=[]
    def trap(self):
        if self.cpu.pc==0xffba:
            assert self.cpu.a==2 and self.cpu.y==2
            self.devices.append(self.cpu.x)
            self.cpu.p &= ~self.cpu.CARRY;self.bank_set=False
            self.cpu.pc=self.cpu.stPopWord()+1
        else:super().trap()
T.N=N;T.PREV.N=N;T.Machine=Machine;T.PREV.Machine=Machine
# Import after rebinding: these suites exercise the Stage5c PRG, not archived Stage5b.
import test_stage5b_dos as DOS
import test_stage5b_graphics as GRAPHICS
LevelRegression=T.LevelTests
CombatRegression=T.CombatTests
DOSRegression=DOS.DOSProtectionTests
GraphicsRegression=GRAPHICS.OriginalGraphicsTests
class PaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids,cls.words=PAL.read_sources();cls.boot=T.start()
        cls.snapshot=bytes(cls.boot.memory.data);cls.colour=bytes(cls.boot.memory.colour)
        cls.banks=[[bytes(c) for c in bank] for bank in cls.boot.memory.banks]
    def machine(self):
        m=Machine();m.memory.data[:]=self.snapshot;m.memory.colour[:]=self.colour
        for b in range(4):
            for c in range(3):m.memory.banks[b][c][:]=self.banks[b][c]
        m.cpu.pc=N['main_loop'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff)
        return m
    def assert_palette(self,m,number):
        p=self.ids[number-1];self.assertEqual(T.get(m,'palette_id'),p)
        for c,shift in enumerate((8,4,0)):
            expected=bytes(((w>>shift)&15)*17 for w in self.words[p][:8])
            self.assertEqual(m.memory.banks[1][c][17:25],expected,(number,c))
            self.assertEqual(m.memory.banks[1][c][:16],self.banks[1][c][:16])
            self.assertEqual(m.memory.banks[2][c],self.banks[2][c])
            self.assertEqual(m.memory.banks[3][c],self.banks[3][c])
        self.assertEqual(m.memory.data[0xd070],0x9a)
    def test_original_binary_roundtrip_and_reproducible(self):
        raw=(ROOT/'assets/stage5c/VYCL.DAT').read_bytes()
        self.assertEqual(len(raw),476);self.assertEqual(PAL.decode(raw),(self.ids,self.words))
        with tempfile.TemporaryDirectory() as d:
            actual,_=PAL.build(Path(d));self.assertEqual(actual,raw)
        for bad in (raw[:-1],raw+b'\0',b'FAIL'+raw[4:]):
            with self.assertRaises(ValueError):PAL.decode(bad)
        for pos,value in ((16,20),(117,16),(4,2)):
            bad=bytearray(raw);bad[pos]=value
            with self.assertRaises(ValueError):PAL.decode(bad)
        BUILD.protect_stable()
        entries=[('STAGE5C',(ROOT/'releases/stage_5c/STAGE5C.PRG').read_bytes(),0x82)]+[(n,(ROOT/'releases/stage_5c'/n).read_bytes(),0x81) for n in ['VYLV.DAT','VYGR.DAT','VYCL.DAT']]
        BUILD.BASE.verify_disk((ROOT/'releases/stage_5c/VYPER_STAGE5C.d81').read_bytes(),entries)
    def test_actual_loader_three_SEQs_and_dma_bounds(self):
        m=Machine().execute();self.assertEqual(m.error,0)
        self.assertEqual(m.opened_names,['VYLV.DAT','VYGR.DAT','VYCL.DAT'])
        self.assertEqual(m.closed,3);self.assertFalse(m.active or m.opened)
        raw=m.files['VYCL.DAT'];self.assertEqual(m.memory.data[0x5c300:0x5c4dc],raw)
        self.assertEqual(m.memory.data[0x6d00:0x6edc],raw)
        self.assertEqual(m.memory.data[0x5c2b8:0x5c300],m.before[0x5c2b8:0x5c300])
        self.assertEqual(m.memory.data[0x5c4dc],m.before[0x5c4dc])
        self.assertIn((0x5c300,0x6d00,476),m.memory.base.transfers)
    def test_actual_loader_failure_missing_truncated_corrupt_and_trailing(self):
        for fault in ('missing','short','header','index','rgb4','checksum','extra'):
            m=Machine();b=bytearray(m.files['VYCL.DAT'])
            if fault=='missing':del m.files['VYCL.DAT']
            else:
                if fault=='short':b=b[:-1]
                elif fault=='header':b[0]^=1
                elif fault=='index':b[16]=20
                elif fault=='rgb4':b[117]=16
                elif fault=='checksum':b[14]^=1
                elif fault=='extra':b+=b'\0'
                m.files['VYCL.DAT']=bytes(b)
            m.execute();self.assertEqual(m.cpu.pc,0x200,fault)
            self.assertNotEqual(m.error,0,fault);self.assertFalse(m.active or m.opened)
            self.assertEqual(m.memory.data[0xd070],m.before[0xd070])
    def test_runtime_schema_validation_independent_of_pinned_sum(self):
        for pos,value in ((0,0),(4,2),(6,99),(8,19),(10,8),(12,0),(16,20),(117,16),(14,0)):
            m=self.machine();m.memory.data[0x6d00+pos]=value
            T.setv(m,'error',0);T.call(m,'validate');self.assertEqual(m.error,7,(pos,value))
    def test_all100_level_palettes_and_constant_banks(self):
        m=self.machine();self.assert_palette(m,1)
        for n in range(1,101):
            m.cpu.a=n;T.call(m,'transition');self.assertEqual(m.error,0);self.assert_palette(m,n)
            self.assertEqual(m.memory.data[0x6d00:0x6edc],m.files['VYCL.DAT'])
    def test_palette_changes_on_buttons_nav_wrap_and_R(self):
        m=self.machine()
        for n in (1,2,3,4,5,10,11,20,21,71,99,100):
            m.cpu.a=n;T.call(m,'transition');self.assert_palette(m,n)
        T.enemies(m);T.setv(m,'a_enabled',0);T.call(m,'tick')
        m.cpu.pc=N['main_loop'];T.frame(m,buttons=255);T.frame(m,buttons=239)
        self.assertEqual(T.get(m,'number'),1);self.assert_palette(m,1)
        T.frame(m,0x2b);self.assert_palette(m,2);T.frame(m)
        T.frame(m,0x2d);self.assert_palette(m,1)
        m.cpu.a=71;T.call(m,'transition');T.setv(m,'c_ps',4)
        m.cpu.pc=N['main_loop'];T.frame(m);T.frame(m,0x52);self.assert_palette(m,1)
    def test_program_load_device_retained_for_all_SEQs(self):
        m=Machine();m.memory.data[0xba]=9;m.execute()
        self.assertEqual(m.error,0);self.assertEqual(m.devices,[9,9,9])
    def test_full_colour_cursor_ROM_palette_exit_and_repeat_start(self):
        m=Machine()
        original_colour=bytes((i*53+19)&255 for i in range(4800))
        m.memory.colour[:4800]=original_colour
        cursor=bytes(m.memory.data[0x1000:0x1600]);rom_palette=m.memory.primary_palette()
        m.execute()
        for _ in range(800000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('initialization')
        self.assertEqual(m.memory.data[0x15600:0x15a80],original_colour[2048:3200])
        for n in (71,100,1):
            m.cpu.a=n;T.call(m,'transition');self.assert_palette(m,n)
        m.cpu.pc=N['main_loop'];T.frame(m,0x58)
        self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(m.memory.colour[:4800],original_colour)
        self.assertEqual(m.memory.data[0x1000:0x1600],cursor)
        self.assertEqual(m.memory.primary_palette(),rom_palette)
        m.execute(N['p_startup'])
        for _ in range(800000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('second RUN')
        self.assertEqual(m.error,0);self.assert_palette(m,1)
    def test_glyph_palette_attribute_player_enemy_explosion_crop(self):
        m=self.machine()
        for glyph,state,expected in ((0x321,1,0),(0x305,4,0),(0x31f,4,0),(0x261,1,16),(0x329,1,16),(0x501,1,16),(0x501,4,0)):
            T.setv(m,'v014_top_lo',glyph&255);T.setv(m,'v014_top_hi',glyph>>8)
            T.setv(m,'e_slot',0);T.setv(m,'c_es',state)
            m.cpu.x=17;m.cpu.y=91;T.call(m,'glyph_colour')
            self.assertEqual(m.cpu.a,expected);self.assertEqual((m.cpu.x,m.cpu.y),(17,91))
        for state,x,y,expected in ((1,50,50,16),(1,0,0,16),(1,-3,-5,16),(4,50,50,0),(4,-3,-5,0)):
            T.enemies(m);T.setv(m,'c_ps',2);T.target(m,0,state,x&255,y&255)
            for name,value in [('e_xlo',x&255),('e_xhi',(x>>8)&255),('e_ylo',y&255),('e_yhi',(y>>8)&255)]:T.setv(m,name,value)
            T.call(m,'e_render')
            count=0
            for row in range(25):
                for slot in range(T.get(m,'v014_row_count',row)):
                    a=row*192+84+slot*4
                    self.assertEqual(m.memory.colour[a+3]&240,expected,(state,x,y,row));count+=1
            self.assertGreater(count,0)
if __name__=='__main__':unittest.main()
