"""Actual assembled CPU + KERNAL/DMA/FCM models; no XEMU claim."""
import hashlib,re,sys,tempfile,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_stage3b1 as DISK
import build_stage5d0 as BUILD
import convert_stage5d0_title as CONVERT
import analyze_stage5d0_copper as COPPER
ART=ROOT/'releases/stage_5d0'
N={n:int(v,16) for n,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE5D0.sym').read_text())}
DATA=(ART/'VYTI.DAT').read_bytes()
class Memory:
    def __init__(self,fault=None):
        self.data=bytearray((i*13+7)&255 for i in range(0x60000))
        self.colour=bytearray((i*7+9)&255 for i in range(0x8000))
        self.banks=[[bytearray([(b*51+c)*3&255]*256) for c in range(3)] for b in range(4)]
        self.events=[];self.transfers=[];self.fault=fault;self.writes=[]
        # Normal BASIC 80x25, not the title. D011 read bit7 deliberately live=1;
        # saved comparator bit8 is 0, from D07A.
        self.data[0xd011]=0x1b;self.data[0xd031]=0xc0;self.data[0xd030]=0
        self.data[0xd05d]=0x80;self.data[0xd070]=0;self.data[0xd07a]=0x10
        self.data[0xd060:0xd064]=bytes((0,8,0,0));self.data[0xba]=9
        self.live_raster_high=128
    def __getitem__(self,a):
        if 0xff80000<=a<0xff88000:return self.colour[a-0xff80000]
        if 0xd100<=a<0xd400:return self.banks[self.data[0xd070]>>6][(a-0xd100)//256][a&255]
        if a==0xd610:return self.events[0] if self.events else 0
        if a==0xd011:return (self.data[a]&127)|self.live_raster_high
        return self.data[a]
    def __setitem__(self,a,v):
        if 0xff80000<=a<0xff88000:self.colour[a-0xff80000]=v;return
        if 0xd100<=a<0xd400:self.banks[self.data[0xd070]>>6][(a-0xd100)//256][a&255]=v;return
        if a==0xd610:
            if self.events:self.events.pop(0)
            return
        self.data[a]=v
        if a==0xd011:self.data[0xd07a]=(self.data[0xd07a]&0xf8)|(v>>7)
        if 0xd000<=a<0xd080:self.writes.append((a,v))
        if a!=0xd705:return
        assert self.data[0xd702]==self.data[0xd704]==0
        p=self.data[0xd701]*256+v;srcmb=dstmb=0
        while self.data[p]:
            opt=self.data[p];p+=1
            if opt==0x80:srcmb=self.data[p];p+=1
            elif opt==0x81:dstmb=self.data[p];p+=1
            else:assert opt==0x0a
        p+=1;d=self.data[p:p+11]
        assert d[0]==0 and d[9:]==bytes(2)
        count=int.from_bytes(d[1:3],'little');assert count
        src=(srcmb<<20)+int.from_bytes(d[3:6],'little');dst=(dstmb<<20)+int.from_bytes(d[6:9],'little')
        self.transfers.append((src,dst,count))
        # F018A forward COPY, intentionally not memmove: checks overlap direction.
        for i in range(count):self[dst+i]=self[src+i]
        if self.fault=='dma' and dst==0x6900:self.data[dst]^=1;self.fault=None
class Machine:
    KERNAL={0xffba,0xff6b,0xffbd,0xffc0,0xffc6,0xffcf,0xffb7,0xffcc,0xffc3,0xffd2}
    def __init__(self,data=DATA,fault=None,irq_disabled=False):
        self.memory=Memory(fault);p=(ART/'STAGE5D0.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.cpu=MPU(memory=self.memory);self.payload=data;self.fault=fault;self.closed=0;self.opened=False;self.active=False;self.bank_set=False;self.messages=bytearray();self.irq_disabled=irq_disabled
        self.before=bytes(self.memory.data);self.before_colour=bytes(self.memory.colour);self.before_banks=[[bytes(c) for c in b] for b in self.memory.banks]
        self.restart()
    def restart(self):
        self.cpu.pc=N['title_entry'];self.cpu.sp=0xfd;self.cpu.p=0x24 if self.irq_disabled else 0x20;self.cpu.stPushWord(0x01ff)
    def trap(self):
        c=self.cpu;a=c.pc;c.p&=~c.CARRY
        if a==0xffba:assert(c.a,c.x,c.y)==(2,9,2);self.bank_set=False
        elif a==0xff6b:assert c.a==c.x==0;self.bank_set=True
        elif a==0xffbd:
            assert self.bank_set
            at=c.x+c.y*256;assert bytes(self.memory.data[at:at+c.a])==b'VYTI.DAT,S,R'
        elif a==0xffc0:
            if self.fault=='open':c.p|=c.CARRY
            else:self.opened=True;self.position=0
        elif a==0xffc6:
            assert self.opened and c.x==2
            if self.fault=='chkin':c.p|=c.CARRY
            else:self.active=True
        elif a==0xffcf:
            assert self.active
            c.a=self.payload[self.position] if self.position<len(self.payload) else 0;self.position+=1
            self.status=0x40 if self.position>=len(self.payload) else 0
            if self.fault=='read':self.status=2
        elif a==0xffb7:c.a=self.status
        elif a==0xffcc:self.active=False
        elif a==0xffc3:assert not self.active and c.a==2;self.opened=False;self.closed+=1
        elif a==0xffd2:assert not self.active;self.messages.append(c.a)
        c.pc=c.stPopWord()+1
    def run_to(self,target):
        for _ in range(12000000):
            if self.cpu.pc==target:return self
            if self.cpu.pc==0x200:raise AssertionError('Returned early, error='+str(self.error))
            if self.cpu.pc in self.KERNAL:self.trap()
            else:self.cpu.step()
        raise AssertionError('CPU did not reach target')
    @property
    def error(self):return self.memory.data[N['error']]
    def exit(self,key=0x78):
        self.memory.events.append(key);self.run_to(0x200)
        assert not self.opened and not self.active
        assert bool(self.cpu.p&self.cpu.INTERRUPT)==self.irq_disabled
    def assert_restore(self,test):
        # Use actual table extent (ends immediately before saved compare bit).
        regs=self.before[N['title_regs']:N['title_saved_compare_bit']]
        for r in regs:test.assertEqual(self.memory.data[0xd000+r],self.before[0xd000+r],f'VIC ${r:02X}')
        test.assertEqual(bytes(self.memory.colour),self.before_colour)
        test.assertEqual([[bytes(c) for c in b] for b in self.memory.banks],self.before_banks)
        for lo,hi in [(0,0x100),(0x200,0x1000),(0x1000,0x1600),(0x10000,0x12000),(0x1f800,0x20000),(0x20000,0x40000)]:
            # KERNAL traps do not simulate their workspace updates; checks detect
            # program memory writes, not equivalence of a real disk operation.
            test.assertEqual(bytes(self.memory.data[lo:hi]),self.before[lo:hi],hex(lo))
class TitleTests(unittest.TestCase):
    def test_01_original_roundtrip_and_disk(self):
        BUILD.protect_stable()
        with tempfile.TemporaryDirectory() as t:
            CONVERT.convert(BUILD.SOURCE/'vyper_palette_candidate_9a50.png',BUILD.SOURCE/'vyper_title_palette.txt',Path(t))
            for name in ['VYTI.DAT','title_fcm.bin','title_palette_r.bin','title_palette_g.bin','title_palette_b.bin']:
                self.assertEqual((Path(t)/name).read_bytes(),(ART/name).read_bytes())
        DISK.verify_disk((ART/'VYPER_STAGE5D0.d81').read_bytes(),[('STAGE5D0',(ART/'STAGE5D0.PRG').read_bytes(),0x82),('VYTI.DAT',DATA,0x81)])
        self.assertEqual(len(DATA),84597);self.assertEqual(len((ART/'VYPER_STAGE5D0.d81').read_bytes()),819200)
    def test_02_actual_loader_FCM_all_pixels_and_twice_exit(self):
        m=Machine()
        original=list(Image.open(BUILD.SOURCE/'vyper_palette_candidate_9a50.png').get_flattened_data())
        for key in (0x78,0x58):
            m.run_to(N['wait_x']);mem=m.memory
            self.assertEqual(m.error,0);self.assertTrue(m.cpu.p&m.cpu.INTERRUPT)
            self.assertEqual(mem.data[0x40000:0x54a00],DATA[117:])
            self.assertEqual(mem.data[0x54a75:0x60000],m.before[0x54a75:0x60000])
            self.assertEqual(mem.colour[0x2000:0x2a50],bytes(2640))
            self.assertEqual(mem.data[0xd054],5);self.assertEqual(mem.data[0xd031]&0xb8,0)
            self.assertEqual(mem.data[0xd05a:0xd05c],bytes((120,1)))
            self.assertEqual(mem.data[0xd058:0xd05a],bytes((88,0)))
            self.assertEqual(mem.data[0xd05e],44);self.assertEqual(mem.data[0xd07b],29)
            self.assertEqual(mem.data[0xd060:0xd064],bytes((0,0x70,0,0)))
            self.assertEqual(mem.data[0xd064:0xd066],bytes((0,0x20)))
            self.assertEqual(mem.data[0xd04c:0xd050],bytes((48,0,48,0)))
            self.assertEqual(mem.data[0xd048:0xd04c],bytes((48,0,16,2)))
            pixels=[]
            for y in range(240):
                for x in range(352):
                    at=0x7000+(y//8)*88+(x//8)*2;glyph=int.from_bytes(mem.data[at:at+2],'little')
                    index=mem.data[glyph*64+(y%8)*8+x%8]
                    self.assertLess(index,33)
                    pixels.append(tuple(mem.banks[1][c][index] for c in range(3)))
            self.assertEqual(pixels,original)
            # Non-X must consume the event and preserve the picture.
            mem.events.append(ord('R'));m.cpu.step()
            for _ in range(20):m.cpu.step()
            self.assertEqual(m.cpu.pc,N['wait_x'])
            m.exit(key);m.assert_restore(self)
            self.assertEqual(mem.writes[-1][0],0xd05d)
            m.restart()
    def test_03_IRQ_disabled_entry_preserved(self):
        m=Machine(irq_disabled=True).run_to(N['wait_x']);m.exit();m.assert_restore(self)
    def check_failure(self,payload=DATA,fault=None,error=3):
        m=Machine(payload,fault);m.run_to(0x200)
        self.assertEqual(m.error,error);self.assertFalse(m.active);self.assertFalse(m.opened)
        self.assertIn(b'LOAD ERROR $',m.messages)
        self.assertEqual(m.memory.colour,bytearray(m.before_colour))
        self.assertEqual(m.memory.data[0xd070],m.before[0xd070])
        self.assertEqual(bool(m.cpu.p&m.cpu.INTERRUPT),m.irq_disabled)
        return m
    def test_04_io_failures(self):
        for fault,error in [('open',1),('chkin',2),('read',3),('dma',4)]:
            with self.subTest(fault=fault):self.check_failure(fault=fault,error=error)
    def test_05_truncated_and_oversized(self):
        for payload in (DATA[:511],DATA+b'\0'):
            with self.subTest(size=len(payload)):self.check_failure(payload)
    def test_06_checksum(self):
        b=bytearray(DATA);b[-2]^=1;self.check_failure(b,error=6)
    def test_07_schema_even_with_same_sum(self):
        # Swap width/height bytes -> exact same whole-file sum, wrong header.
        b=bytearray(DATA);b[6],b[8]=b[8],b[6];self.check_failure(b,error=5)
    def test_08_converter_rejects_unapproved_RGB(self):
        with tempfile.TemporaryDirectory() as t:
            im=Image.open(BUILD.SOURCE/'vyper_palette_candidate_9a50.png');im.putpixel((0,0),(1,2,3));p=Path(t)/'wrong.png';im.save(p)
            with self.assertRaisesRegex(ValueError,'absent'):CONVERT.convert(p,BUILD.SOURCE/'vyper_title_palette.txt',Path(t)/'out')
    def test_09_saved_Copper_source_and_geometry_limits(self):
        r=COPPER.analyze()
        self.assertEqual(r['saved_registers']['COP2LC'],'0x184ae')
        self.assertEqual(r['saved_registers']['BPLCON0'],'0x200')
        self.assertEqual(r['lists'][1]['source'],'savestate CRAM')
        phase=[m for m in r['lists'][1]['display_moves'] if m['name']=='BPLCON0']
        self.assertEqual([(m['after_wait']['line8'],m['value']) for m in phase],[(43,'0x200'),(44,'0x4200'),(244,'0x200')])
        self.assertEqual(r['conditional_classic_OCS_ECS_interpretation']['referenced_COP2_DDF_lowres_pixels'],320)
if __name__=='__main__':unittest.main()
