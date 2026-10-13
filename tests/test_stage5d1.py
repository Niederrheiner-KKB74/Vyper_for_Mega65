"""Assembled Stage5d1 loader + protected FCM scene + inherited Stage5c gameplay."""
import hashlib,json,os,struct,tempfile,unittest
from pathlib import Path
from PIL import Image
import test_stage5c as OLD
import build_stage5d1 as BUILD
import convert_stage5d1_title as CONVERT
ROOT=OLD.ROOT
ART=ROOT/'releases/stage_5d_1'
N=OLD.T.BUILD.symbols((ART/'STAGE5D1.sym').read_text())
BaseMachine=OLD.Machine
BaseMemory=OLD.T.EntryMemory
TITLE_RANGES=[(a,a+n*64) for a,n in CONVERT.RANGES]+[(0xf300,0xfd50)]
VIC_REGS=[0x11,0x15,0x16,0x20,0x21,0x30,0x31,*range(0x48,0x50),0x54,*range(0x58,0x5f),*range(0x60,0x66),0x70,0x7a,0x7b,0x68,0x69,0x6a,0x6c,0x6d,0x6e]
class TitleMemory(BaseMemory):
    def __setitem__(self,a,v):
        if getattr(self,'watch_title',False) and a==N['t_shown']:
            self.title_active=bool(v)
        if a!=0xd705:return super().__setitem__(a,v)
        self.data[a]=v
        assert self.data[0xd702]==self.data[0xd704]==0
        p=self.data[0xd701]*256+v;srcmb=dstmb=0
        while self.data[p]:
            opt=self.data[p];p+=1
            if opt==0x80:srcmb=self.data[p];p+=1
            elif opt==0x81:dstmb=self.data[p];p+=1
            else:assert opt==0x0a
        p+=1;d=self.data[p:p+11];assert d[0] in (0,3) and d[9:]==bytes(2)
        n=int.from_bytes(d[1:3],'little');assert n
        src=int.from_bytes(d[3:6],'little')+(srcmb<<20);dst=int.from_bytes(d[6:9],'little')+(dstmb<<20)
        if getattr(self,'title_active',False):
            for lo,hi in TITLE_RANGES+[(0xff82000,0xff82a50)]:
                assert not (dst<hi and dst+n>lo),('Title overwritten during loading',hex(dst),n)
            self.protected_dma+=1
        prev=self.linear;self.linear=True
        try:
            if d[0]==3:payload=bytes([d[3]])*n
            elif 0xff7e000<=src<0xff80000:payload=self.char_wom[src-0xff7e000:src-0xff7e000+n]
            else:payload=bytes(self[src+i] for i in range(n))
            for i,b in enumerate(payload):self[dst+i]=b
            if self.base.corrupt_dma and dst==0x6900:self.data[dst]^=1;self.base.corrupt_dma=False
        finally:self.linear=prev
        self.base.transfers.append((src,dst,n))
class Machine(BaseMachine):
    def __init__(self):
        super().__init__()
        p=(ART/'STAGE5D1.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.files['VYTI.DAT']=(ART/'VYTI.DAT').read_bytes()
        self.memory.__class__=TitleMemory;self.memory.watch_title=True;self.memory.title_active=False;self.memory.protected_dma=0
        self.memory.data[0x1120]=0x10
        self.cpu.pc=N['p_startup'];self.before=bytes(self.memory.data)
        self.open_scenes=[];self.scene_snapshots=[];self.large_reads=0
        self.palette_before=[[bytes(c) for c in b] for b in self.memory.banks]
        self.title_colour_before=bytes(self.memory.colour[0x2000:0x2a50])
    def trap(self):
        c=self.cpu
        if c.pc==0xffbd:
            name=bytes(self.memory.data[c.x+c.y*256:c.x+c.y*256+c.a]).decode()
            if name.startswith('VYTI'):
                self.memory.watch_title=True;self.memory.title_active=False
                self.scene_snapshots=[] # Compare within this loading phase, not with an earlier game's palette banks.
            else:
                assert self.memory.title_active,'Original DAT started without title'
                assert not c.p&c.INTERRUPT,'KERNAL must run with IRQs enabled'
                assert self.memory.data[0x1120]==255,'cursor not paused'
                scene=self.scene_bytes();self.scene_snapshots.append(scene)
                if len(self.scene_snapshots)>1:assert scene==self.scene_snapshots[-2],'title changed between DATs'
                self.open_scenes.append(name[:-4])
        if c.pc==0xffcf and self.memory.title_active:self.large_reads+=1
        if c.pc==0xffd2 and self.memory.title_active:raise AssertionError('CHROUT on title scene')
        super().trap()
    def execute(self,address=None,limit=25000000):
        r=super().execute(address,limit)
        if address is None or address==N['p_startup']:self.memory.watch_title=False
        return r
    def scene_bytes(self):
        m=self.memory
        return (tuple(bytes(m.data[a:b]) for a,b in TITLE_RANGES),bytes(m.colour[0x2000:0x2a50]),tuple(tuple(bytes(c[:33]) for c in b) for b in m.banks),tuple(m.data[0xd000+r] for r in VIC_REGS))
# Rebind original suites to the new actual PRG and symbols, not old binaries.
OLD.N=N;OLD.T.N=N;OLD.T.PREV.N=N;OLD.T.Machine=Machine;OLD.T.PREV.Machine=Machine
OLD.Machine=Machine
LevelRegression=OLD.LevelRegression
CombatRegression=OLD.CombatRegression
# Original DOS suite replaces the memory class: keep the new enhanced-DMA model.
import test_stage5b_dos as DOS
class TrackedTitleMemory(TitleMemory):
    def __setitem__(self,a,v):
        if 0x10000<=a<0x12000:self.dos_writes.append(a)
        super().__setitem__(a,v)
DOS.TrackedMemory=TrackedTitleMemory
DOSRegression=OLD.DOSRegression
class GraphicsRegression(OLD.GraphicsRegression):
    def test_loader_extended_size_checksums_and_readback_faults(self):
        m=Machine().execute();self.assertEqual(m.error,0)
        raw=(ROOT/'assets/stage5b/VYGR.DAT').read_bytes()
        self.assertEqual(m.memory.data[0x54000:0x54000+len(raw)],raw)
        self.assertEqual(m.memory.data[0x54000+len(raw)],0xa5)
        self.assertEqual(m.memory.data[0x40000:0x53f81],(ROOT/'assets/VYLV.DAT').read_bytes())
        # Issue35 requires exact complete files; trailing data is now rejected.
        trailing=Machine();trailing.files['VYGR.DAT']=raw+b'\0';trailing.execute()
        self.assertEqual(trailing.error,3)
        self.assertEqual(trailing.memory.data[0x54000+len(raw)],0xa5)
        for kind in ('short','checksum','dma'):
            n=Machine()
            if kind=='short':n.files['VYGR.DAT']=raw[:-1]
            elif kind=='checksum':n.files['VYGR.DAT']=raw[:-1]+bytes([raw[-1]^1])
            else:n.memory.base.corrupt_dma=True
            n.execute();self.assertNotEqual(n.error,0,kind)

class PaletteRegression(OLD.PaletteTests):
    def test_original_binary_roundtrip_and_reproducible(self):
        BUILD.protect_stable()
        entries=[('STAGE5D1',(ART/'STAGE5D1.PRG').read_bytes(),0x82)]+[(n,(ART/n).read_bytes(),0x81) for n in ['VYTI.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT']]
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE5D1.d81').read_bytes(),entries)
        with tempfile.TemporaryDirectory() as d:
            data,_=CONVERT.build(Path(d));self.assertEqual(data,(ART/'VYTI.DAT').read_bytes())
    def test_program_load_device_retained_for_all_SEQs(self):
        m=Machine();m.memory.data[0xba]=9;m.execute()
        self.assertEqual(m.error,0);self.assertEqual(m.devices,[9,9,9,9])
    def test_actual_loader_three_SEQs_and_dma_bounds(self):
        m=Machine().execute();self.assertEqual(m.error,0)
        self.assertEqual(m.opened_names,['VYTI.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT'])
        self.assertEqual(m.open_scenes,['VYLV.DAT','VYGR.DAT','VYCL.DAT'])
        self.assertEqual(m.closed,4);self.assertFalse(m.active or m.opened)
        self.assertEqual(m.large_reads,81793+33464+476)
        self.assertGreater(m.memory.protected_dma,900)
        self.assertEqual(m.memory.colour[0x2000:0x2a50],m.title_colour_before)
        self.assertEqual(m.memory.data[0x1120],0x10)
        for n,a in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000),('VYCL.DAT',0x5c300)]:self.assertEqual(m.memory.data[a:a+len(m.files[n])],m.files[n])
class HotregMemory(TitleMemory):
    """Narrow pending-HOTREG model from XEMU vic4.c / VIC-IV core.

    Model the relevant overwritten precise fields, not a raster renderer.
    Both models remember legacy writes while disabled; XEMU additionally
    cancels a pending update on an explicit HOTREG-disable write.
    """
    def __setitem__(self,a,v):
        super().__setitem__(a,v)
        if not getattr(self,'hotreg_model',False):return
        if a in (0xd011,0xd016,0xd031):self.pending_hotreg=True
        if a==0xd05d and not v&128 and self.cancel_on_disable:self.pending_hotreg=False
        if self.pending_hotreg and self.data[0xd05d]&128:
            self.hotreg_updates+=1;self.pending_hotreg=False
            # Legacy interpretation overwrites precise geometry and pointers.
            width=80 if self.data[0xd031]&128 else 40
            self.data[0xd058:0xd05a]=bytes([width,0])
            self.data[0xd05e]=width
            self.data[0xd064:0xd066]=bytes(2)
            self.data[0xd068:0xd06b]=bytes([0,0x20,0])
            self.data[0xd06c:0xd06f]=bytes([0xf8,7,0])
            self.data[0xd060:0xd064]=bytes([0,4,0,0])
            self.data[0xd048:0xd050]=bytes([104,0,247,1,80,0,104,0])

class HotregHandoffTests(unittest.TestCase):
    def test_missing_game_file_restores_all_saved_video_fields(self):
        m=Machine();del m.files['VYLV.DAT'];m.execute()
        self.assertEqual(m.error,1);self.assertEqual(m.cpu.pc,0x200)
        self.assertFalse(m.active or m.opened)
        for r in VIC_REGS:
            expected=0 if r==0x15 else m.before[0xd000+r] # Error returns through hud.startup, restoring BASIC background.
            self.assertEqual(m.memory.data[0xd000+r],expected,hex(r))
        self.assertEqual(m.memory.data[0x1120],0x10)

    def test_precise_geometry_survives_pending_legacy_updates(self):
        for cancel in (True,False):
            for enabled in (False,True):
                with self.subTest(xemu_cancel=cancel,original_hotreg=enabled):
                    m=Machine();mem=m.memory;mem.__class__=HotregMemory
                    mem.hotreg_model=True;mem.pending_hotreg=False
                    mem.hotreg_updates=0;mem.cancel_on_disable=cancel
                    # Valid precise geometry intentionally differs from legacy
                    # defaults: restoring only legacy mode must not lose it.
                    mem.data[0xd011]=0x1b;mem.data[0xd016]=8
                    mem.data[0xd031]=0xc0;mem.data[0xd05d]=0xc0 if enabled else 0x40
                    mem.data[0xd07a]=0x80
                    mem.data[0xd048:0xd050]=bytes([98,0,241,1,82,0,98,0])
                    mem.data[0xd058:0xd05a]=bytes([160,0]);mem.data[0xd05e]=80
                    mem.data[0xd060:0xd066]=bytes([0,0x80,0,0,0,4])
                    before={r:mem.data[0xd000+r] for r in VIC_REGS}
                    OLD.T.call(m,'t_save_video');OLD.T.call(m,'t_show')
                    mem.data[N['t_shown']]=1
                    OLD.T.call(m,'t_restore_video')
                    self.assertEqual({r:mem.data[0xd000+r] for r in VIC_REGS},before)
                    if enabled:self.assertFalse(mem.pending_hotreg)
                    self.assertEqual(mem.data[0x1120],0x10)

class TitleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.boot=Machine().execute()
    def test_FCM_scene_all_original_pixels_and_geometry(self):
        m=self.boot;self.assertEqual(m.error,0)
        scene=m.scene_snapshots[0];segments,colours,palettes,regs=scene
        cache={a+i:b for (a,end),block in zip(TITLE_RANGES,segments) for i,b in enumerate(block)}
        original=list(Image.open(ROOT/'assets/stage5d0/original_sources/vyper_palette_candidate_9a50.png').get_flattened_data())
        pixels=[]
        for y in range(240):
            for x in range(352):
                p=0xf300+(y//8)*88+(x//8)*2;g=cache[p]|cache[p+1]<<8
                index=cache[g*64+(y%8)*8+x%8];pixels.append(tuple(palettes[1][c][index] for c in range(3)))
        self.assertEqual(pixels,original)
        self.assertEqual(colours,bytes(2640))
        r=dict(zip(VIC_REGS,regs));self.assertEqual((r[0x5a],r[0x5b],r[0x54]),(120,1,5))
        self.assertEqual((r[0x60],r[0x61],r[0x62],r[0x63]),(0,0xf3,0,0))
        self.assertEqual((r[0x58],r[0x59],r[0x5e],r[0x7b]),(88,0,44,29))
    def test_restored_Basic_before_engine_and_phase_code_backup(self):
        m=self.boot
        for r in VIC_REGS:
            expected=0 if r in (0x15,0x21) else m.before[0xd000+r] # Stable startup disables sprites and clears BASIC before title.
            self.assertEqual(m.memory.data[0xd000+r],expected,hex(r))
        self.assertEqual([[bytes(c) for c in b] for b in m.memory.banks],m.palette_before)
        self.assertEqual(m.memory.data[0x15b00:0x16300],m.memory.data[0x4000:0x4800])
        self.assertEqual(m.memory.data[N['tc_saved']],1)
        for a,b in [(0x1000,0x1600),(0x10000,0x12000),(0x1f800,0x20000),(0x20000,0x40000)]:self.assertEqual(m.memory.data[a:b],m.before[a:b],hex(a))
    def test_each_DAT_missing_truncated_checksum_and_header(self):
        for name in ['VYTI.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT']:
            for fault in ['missing','truncated','checksum','header_same_sum']:
                with self.subTest(file=name,fault=fault):
                    m=Machine();b=bytearray(m.files[name])
                    if fault=='missing':del m.files[name]
                    else:
                        if fault=='truncated':b=b[:min(511,len(b)-1)]
                        elif fault=='checksum':b[-2]^=1
                        else:b[0],b[1]=b[1],b[0] # bad magic, unchanged additive sum
                        m.files[name]=bytes(b)
                    m.execute();self.assertEqual(m.cpu.pc,0x200);self.assertNotEqual(m.error,0)
                    self.assertFalse(m.active or m.opened);self.assertIn(name.encode(),m.messages)
                    self.assertEqual(m.memory.data[0x1120],0x10)
                    self.assertEqual(m.memory.colour[0x2000:0x2a50],m.title_colour_before)
                    self.assertEqual([[bytes(c) for c in bank] for bank in m.memory.banks],m.palette_before)
                    self.assertEqual(m.memory.data[N['tc_saved']],0)
    def test_versions_and_levelrecord_error_report_correct_file(self):
        for name in ['VYTI.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT']:
            with self.subTest(version=name):
                m=Machine();b=bytearray(m.files[name]);b[4],b[5]=b[5],b[4]
                m.files[name]=bytes(b);m.execute()
                self.assertEqual(m.cpu.pc,0x200);self.assertNotEqual(m.error,0)
                self.assertIn(name.encode(),m.messages);self.assertFalse(m.active or m.opened)
        m=Machine();b=bytearray(m.files['VYLV.DAT'])
        b[0x328+2],b[0x328+3]=b[0x328+3],b[0x328+2] # Wrong Level1 signature, unchanged sum.
        m.files['VYLV.DAT']=bytes(b);m.execute()
        self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.error,5)
        self.assertIn(b'VYLV.DAT',m.messages);self.assertFalse(m.active or m.opened)

    def test_title_dma_verification_failure(self):
        m=Machine();m.memory.base.corrupt_dma=True;m.execute()
        self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.error,4)
        self.assertFalse(m.active or m.opened);self.assertEqual(m.opened_names,['VYTI.DAT'])
    def test_live_original_ROM_cursor_cannot_touch_title(self):
        import test_stage3b2_exit as ROM
        paths=list(Path('/workspace/attachments').glob('*/MEGA65.ROM'))
        path=Path(os.environ['MEGA65_ROM']) if os.environ.get('MEGA65_ROM') else next((p for p in paths if hashlib.sha256(p.read_bytes()).hexdigest()==ROM.ROM_SHA),None)
        if path is None:self.skipTest('Original ROM V920395 unavailable')
        m=Machine();m.execute(N['t_boot']) # isolated actual title bootstrap, before game DATs
        self.assertEqual(m.error,0);self.assertTrue(m.memory.title_active)
        before=m.scene_bytes();cursor=bytes(m.memory.data[0x111f:0x1124]);ROM.blink(m,path.read_bytes())
        self.assertEqual(m.scene_bytes(),before);self.assertEqual(m.memory.data[0x111f:0x1124],cursor)
        OLD.T.call(m,'t_restore_video');self.assertEqual(m.memory.data[0x1120],0x10)
if __name__=='__main__':unittest.main()
