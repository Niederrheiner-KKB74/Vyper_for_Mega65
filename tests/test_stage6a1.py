"""Actual standalone menu CPU/DMA and original Amiga bitplane oracle; not XEMU."""
import json,re,struct,tempfile,unittest
from pathlib import Path
import test_stage5d0 as OLD
import build_stage6a1 as BUILD
import convert_stage6a1_menu as CONVERT
ROOT=BUILD.ROOT;ART=ROOT/'releases/stage_6a1'
N={n:int(v,16) for n,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE6A1.sym').read_text())}
OLD.N=N
DATA=(ART/'VYMN.DAT').read_bytes()
REPORT=json.loads((ART/'conversion-report.json').read_text())
CHUNKS=dict(CONVERT.COP.chunks(CONVERT.SOURCE.read_bytes()));RAM=CHUNKS[b'CRAM']
class Machine(OLD.Machine):
    def __init__(self,data=DATA,fault=None,irq_disabled=False):
        self.memory=OLD.Memory(fault);p=(ART/'STAGE6A1.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.cpu=OLD.MPU(memory=self.memory);self.payload=data;self.fault=fault;self.closed=0;self.opened=False;self.active=False;self.bank_set=False;self.messages=bytearray();self.irq_disabled=irq_disabled
        self.before=bytes(self.memory.data);self.before_colour=bytes(self.memory.colour);self.before_banks=[[bytes(c) for c in b] for b in self.memory.banks];self.restart()
    def trap(self):
        c=self.cpu
        if c.pc==0xffbd:
            self.assert_name=bytes(self.memory.data[c.x+c.y*256:c.x+c.y*256+c.a]);assert self.bank_set and self.assert_name==b'VYMN.DAT,S,R'
            c.p&=~c.CARRY;c.pc=c.stPopWord()+1
        else:super().trap()
def call(m,name):
    c=m.cpu;saved=(c.pc,c.sp,c.a,c.x,c.y,c.p);c.pc=N[name];c.sp=0x80;c.stPushWord(0x1ff)
    for _ in range(200000):
        if c.pc==0x200:break
        c.step()
    else:raise AssertionError(name)
    c.pc,c.sp,c.a,c.x,c.y,c.p=saved

def fetch(m):
    mem=m.memory.data;out=bytearray(64000)
    for ty in range(25):
        for tx in range(40):
            p=0x7000+ty*80+tx*2;glyph=int.from_bytes(mem[p:p+2],'little');base=glyph*64
            for y in range(8):out[(ty*8+y)*320+tx*8:(ty*8+y)*320+tx*8+8]=mem[base+y*8:base+y*8+8]
    return bytes(out)

def original_frame(typ,frame):
    p=CONVERT.COP.be(RAM,0x1ace2+(typ-1)*18+8,4)+32*frame
    addresses=[CONVERT.COP.be(RAM,p+k,4) for k in (0,4,8,24)]
    return bytes(sum(((RAM[a+2*y+x//8]>>(7-x%8))&1)<<k for k,a in enumerate(addresses[:3])) if RAM[addresses[3]+2*y+x//8]&(128>>(x%8)) else 0 for y in range(16) for x in range(16))
class HotregMemory(OLD.Memory):
    def __setitem__(self,a,v):
        super().__setitem__(a,v)
        if not getattr(self,'model_hotreg',False):return
        if a in (0xd011,0xd016,0xd031):self.pending=True
        if a==0xd05d and not v&128 and self.cancel:self.pending=False
        if self.pending and self.data[0xd05d]&128:
            self.pending=False
            width=80 if self.data[0xd031]&128 else 40
            self.data[0xd058:0xd05a]=bytes([width,0]);self.data[0xd05e]=width
            self.data[0xd064:0xd066]=bytes(2)
            self.data[0xd060:0xd064]=bytes([0,4,0,0])
            self.data[0xd048:0xd050]=bytes([104,0,247,1,80,0,104,0])

class MenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.boot=Machine().run_to(N['wait_x'])
    def machine(self):
        m=Machine();b=self.boot;m.memory.data[:]=b.memory.data;m.memory.colour[:]=b.memory.colour
        for i,bank in enumerate(b.memory.banks):
            for j,c in enumerate(bank):m.memory.banks[i][j][:]=c
        m.cpu.pc=b.cpu.pc;m.cpu.sp=b.cpu.sp;m.cpu.a=b.cpu.a;m.cpu.x=b.cpu.x;m.cpu.y=b.cpu.y;m.cpu.p=b.cpu.p
        m.memory.data[0x100:0x200]=b.memory.data[0x100:0x200]
        m.before=b.before;m.before_colour=b.before_colour;m.before_banks=b.before_banks;m.closed=b.closed
        return m
    def test_original_32_types_positions_palette_texts_and_conversion(self):
        BUILD.protect_stable()
        actors=REPORT['actors'];self.assertEqual(len(actors),32);self.assertEqual(len({a['type'] for a in actors}),32)
        self.assertEqual([a['type'] for a in actors],[1,2,3,4,5,23,9,10,11,13,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31,32,33,34,35,36])
        self.assertEqual(REPORT['max_actors_per_scanline'],9)
        texts=[x['display'] for x in REPORT['texts']];self.assertIn('- BONUS SHIP EVERY 3 WAVES -',texts);self.assertIn('- SELECT OPTION WITH JOYSTICK OR KEYBOARD -',texts)
        for s in ['INITIAL LEVEL 001','F1 START 1 PLAYER GAME','F2 START 2 PLAYER GAME','F3 VIEW HIGH SCORES']:self.assertIn(s,texts)
        with tempfile.TemporaryDirectory() as d:
            CONVERT.convert(Path(d))
            for p in (ROOT/'assets/stage6a1').iterdir():self.assertEqual(p.read_bytes(),(Path(d)/p.name).read_bytes(),p.name)
    def test_loader_initial_exact_64000_pixels_and_geometry(self):
        m=self.machine();self.assertEqual(m.error,0);self.assertEqual(m.closed,1);self.assertFalse(m.active or m.opened)
        raw=(ART/'original_menu_indices.bin').read_bytes();self.assertEqual(fetch(m),raw)
        self.assertEqual(m.memory.data[0x40000:0x40000+REPORT['tile_bytes']],DATA[117:])
        self.assertEqual(m.memory.colour[0x2000:0x27d0],bytes(2000))
        mem=m.memory.data;self.assertEqual(mem[0xd054],5);self.assertEqual(mem[0xd05e],40);self.assertEqual(mem[0xd07b],24);self.assertEqual(mem[0xd058:0xd05a],bytes([80,0]))
        self.assertEqual(mem[0xd048:0xd050],bytes([88,0,232,1,80,0,88,0]));self.assertEqual(mem[0xd060:0xd064],bytes([0,0x70,0,0]))
        for i in range(16):
            w=CONVERT.COP.be(CHUNKS[b'CHIP'],0xe4+2*i)
            self.assertEqual(tuple(m.memory.banks[1][c][i] for c in range(3)),tuple(((w>>s)&15)*17 for s in (8,4,0)))
    def test_32_animations_every_original_frame_and_no_ghosts(self):
        m=self.machine();original=(ART/'original_menu_indices.bin').read_bytes();seen={a['slot']:set() for a in REPORT['actors']}
        phases={a['slot']:a['initial_frame'] for a in REPORT['actors']};delays={a['slot']:a['initial_delay'] for a in REPORT['actors']}
        for tick in range(1,81):
            call(m,'menu_tick');expected=bytearray(original)
            for a in REPORT['actors']:
                slot=a['slot'];delays[slot]-=1
                if delays[slot]==0:delays[slot]=a['period_frames'];phases[slot]=(phases[slot]+1)%a['frame_count']
                frame=phases[slot];seen[slot].add(frame)
                self.assertEqual(m.memory.data[N['menu_frames']+slot],frame)
                self.assertEqual(m.memory.data[N['menu_delays']+slot],delays[slot])
                px=original_frame(a['type'],frame)
                for y in range(16):expected[(a['y']+y)*320+a['x']:(a['y']+y)*320+a['x']+16]=px[y*16:y*16+16]
            self.assertEqual(fetch(m),expected,tick)
        for a in REPORT['actors']:self.assertEqual(seen[a['slot']],set(range(a['frame_count'])))
        m.memory.data[N['menu_delays']:N['menu_delays']+32]=bytes([1]*32)
        before=m.cpu.processorCycles;call(m,'menu_animate');cost=m.cpu.processorCycles-before
        self.assertLess(cost,18000);(ART/'runtime-budget.json').write_text(json.dumps({'all32_update_6502_model_cycles':cost,'milliseconds_at_3_5MHz':cost/3500,'caveat':'CPU-only; no raster contention/IRQ model','global_frame_divider':1,'original_actor_periods':[a['period_frames'] for a in REPORT['actors']]},indent=2)+'\n')
    def test_only_X_exit_all_state_restored_and_repeated_RUN(self):
        m=Machine()
        for key in (0x78,0x58):
            m.run_to(N['wait_x']);call(m,'menu_animate');self.assertNotEqual(bytes(m.memory.data[0x7000:0x77d0]),(ART/'menu_screen.bin').read_bytes())
            for event in [0x85,0x89,0x86,ord('R'),ord('+'),ord('-')]:
                m.memory.events.append(event)
                for _ in range(80):m.cpu.step()
                self.assertFalse(m.memory.events);self.assertNotEqual(m.cpu.pc,0x200)
            m.exit(key);m.assert_restore(self);m.restart();m.run_to(N['wait_x']);self.assertEqual(fetch(m),(ART/'original_menu_indices.bin').read_bytes());m.exit(key);m.assert_restore(self);m.restart()
    def test_loader_errors_visible_closed_and_video_untouched(self):
        for fault,payload in [('open',DATA),('chkin',DATA),('read',DATA),('dma',DATA),(None,DATA[:-1]),(None,DATA+b'\0'),(None,bytes([DATA[0]^1])+DATA[1:])]:
            m=Machine(payload,fault)
            for _ in range(12000000):
                if m.cpu.pc==0x200:break
                if m.cpu.pc in m.KERNAL:m.trap()
                else:m.cpu.step()
            else:self.fail('error exit')
            self.assertNotEqual(m.error,0);self.assertFalse(m.active or m.opened);self.assertIn(b'STAGE 6A1 LOAD ERROR $',m.messages)
            for r in m.before[N['title_regs']:N['title_saved_compare_bit']]:self.assertEqual(m.memory.data[0xd000+r],m.before[0xd000+r],hex(r))
            self.assertEqual(bytes(m.memory.colour),m.before_colour)
    def test_frame_gate_once_per_PAL_raster_and_outside_display(self):
        m=self.machine();m.memory.live_raster_high=0
        m.memory.data[0xd012]=250;m.run_to(N['wait_raster_leave'])
        screen=bytes(m.memory.data[0x7000:0x77d0]);delays=bytes(m.memory.data[N['menu_delays']:N['menu_delays']+32])
        for _ in range(200):m.cpu.step()
        self.assertEqual(bytes(m.memory.data[0x7000:0x77d0]),screen)
        self.assertEqual(bytes(m.memory.data[N['menu_delays']:N['menu_delays']+32]),delays)
        m.memory.data[0xd012]=251;m.run_to(N['wait_x'])
        m.memory.data[0xd012]=250;m.run_to(N['wait_raster_leave'])
        self.assertNotEqual(bytes(m.memory.data[N['menu_delays']:N['menu_delays']+32]),delays)
        self.assertGreater(250*2,int.from_bytes(m.memory.data[0xd04a:0xd04c],'little'))
    def test_exit_pending_HOTREG_and_original_IRQ_state(self):
        for cancel in (False,True):
            m=Machine(irq_disabled=True);m.memory.__class__=HotregMemory
            m.memory.model_hotreg=True;m.memory.pending=False;m.memory.cancel=cancel
            m.run_to(N['wait_x']);m.exit();m.assert_restore(self)
            self.assertFalse(m.memory.pending)

    def test_disk_complete_and_stable_unchanged(self):
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE6A1.d81').read_bytes(),[('STAGE6A1',(ART/'STAGE6A1.PRG').read_bytes(),0x82),('VYMN.DAT',DATA,0x81)])
        self.assertGreater(BUILD.protect_stable(),30)
if __name__=='__main__':unittest.main()
