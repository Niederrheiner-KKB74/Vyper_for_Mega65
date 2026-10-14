"""Actual assembled menu/game instructions with narrow CPU/DMA/VIC models, not XEMU."""
import json,unittest,os
from pathlib import Path
import test_stage5d1a as OLD
import build_stage7b5a as BUILD
ROOT=BUILD.ROOT;ART=Path(os.getenv('STAGE7B5A_ARTIFACTS',str(ROOT/'releases/stage_7b5a')))
def star_symbols(text):
    import re
    block=text.split('.namespace stars {',1)[1].split('\n}',1)[0]
    symbols={n:int(a,16) for n,a in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',block)}
    stripped=text[:text.index('.namespace stars {')]+text[text.index('\n}',text.index('.namespace stars {'))+2:]
    if '.namespace transitionfx {' in stripped:
        start=stripped.index('.namespace transitionfx {');end=stripped.index('\n}',start)+2
        stripped=stripped[:start]+stripped[end:]
    if '.namespace selection {' in stripped:
        start=stripped.index('.namespace selection {');end=stripped.index('\n}',start)+2;stripped=stripped[:start]+stripped[end:]
    for ns in ('fireevents','fireload'):
        while f'.namespace {ns} {{' in stripped:
            start=stripped.index(f'.namespace {ns} {{');end=stripped.index('\n}',start)+2;stripped=stripped[:start]+stripped[end:]
    return OLD.OLD.T.BUILD.symbols(stripped),symbols
N,S=star_symbols((ART/'STAGE7B5A.sym').read_text())
N['original']=0x31f0
FE={n:int(a,16) for n,a in __import__('re').findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE7B5A.sym').read_text().split('.namespace fireevents {',1)[1].split('\n}',1)[0])}
def fcall(m,name):
    m.cpu.pc=FE[name];m.cpu.stPushWord(0x1ff);return m.run_to([0x200],2_000_000)
def fget(m,name,i=0):return m.memory.data[FE[name]+i]
def fset(m,name,v,i=0):m.memory.data[FE[name]+i]=v
def fword(m,name,i=0):return fget(m,name+'_lo',i)+256*fget(m,name+'_hi',i)
def fputword(m,name,v,i=0):fset(m,name+'_lo',v&255,i);fset(m,name+'_hi',v>>8,i)
# FX labels are unique except state/row; parse the actual assembler namespace.
import re
FX={n:int(a,16) for n,a in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE7B5A.sym').read_text().split('.namespace transitionfx {',1)[1].split('\n}',1)[0])}
MN=OLD.OLD.T.BUILD.symbols((ART/'MENU_OVERLAY.sym').read_text())
OLD.N=N;OLD.OLD.N=N;OLD.OLD.T.N=N;OLD.OLD.T.PREV.N=N
class MenuMemory(OLD.TitleMemory):
    def __getitem__(self,a):
        if 0x60000<=a<0x100000:return 0xff # XEMU MEM_SLOT_TYPE_DUMMY
        if 0x08000000<=a<0x08040000:return self.attic[a-0x08000000]
        if a in (0xd610,0xd619):return (1 if self.key else 0) if a==0xd610 else self.key
        return super().__getitem__(a)
    def __setitem__(self,a,v):
        if 0x60000<=a<0x100000:return # XEMU ignores writes; no physical RAM
        if 0x08000000<=a<0x08040000:self.attic[a-0x08000000]=v;return
        if a in (0xd610,0xd619):self.key=0;return
        super().__setitem__(a,v)
class Machine(OLD.Machine):
    def __init__(self):
        super().__init__();p=(ART/'STAGE7B5A.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.memory.__class__=MenuMemory;self.memory.attic=bytearray(0x40000);self.memory.key=0
        self.files['VYSH.DAT']=(ART/'VYSH.DAT').read_bytes();self.files['VYMN.DAT']=(ART/'VYMN.DAT').read_bytes();self.cpu.pc=N['p_startup']
        self.memory.data[0xdc00]=255;self.memory.data[FX['state']]=3;self.memory.data[FX['palette_ready']]=255;self.memory.data[0xd01c]=0x83
        self.before=bytes(self.memory.data)
    def trap(self):
        if self.cpu.pc==0xffbd:
            c=self.cpu;name=bytes(self.memory.data[c.x+c.y*256:c.x+c.y*256+c.a]).decode()
            self.menu_io=name.startswith('VYMN')
        if getattr(self,'menu_io',False) and self.cpu.pc in self.KERNAL:
            assert self.memory.data[0xd030]&32==self.memory.data[N['original']]&32,'KERNAL ROMC mapping changed during menu I/O'
            assert not self.cpu.p&self.cpu.INTERRUPT,'KERNAL menu I/O with IRQ masked'
            self.menu_io_calls=getattr(self,'menu_io_calls',0)+1
        super().trap()
    def scene_bytes(self):
        scene=super().scene_bytes()
        regs=list(scene[-1]);regs[OLD.VIC_REGS.index(0x30)] &= 0xdf
        # D030.ROMC controls CPU mapping only; VIC fetch/palette are unaffected.
        return (*scene[:-1],tuple(regs))
    def run_to(self,targets,limit=30_000_000):
        targets=set(targets)
        for _ in range(limit):
            if self.cpu.pc in targets:return self
            if self.cpu.pc==N['enter_menu']:self.memory.watch_title=False;self.memory.title_active=False
            if self.cpu.pc in self.KERNAL:self.trap()
            else:self.cpu.step()
        raise AssertionError(('PC did not reach target',hex(self.cpu.pc),targets))
    def boot(self):return self.run_to([MN['menu_loop'],0x200])
    def input(self,key=0,joy=255):
        self.memory.key=key;self.memory.data[0xdc00]=joy
        self.cpu.pc=MN['menu_input'];self.cpu.stPushWord(0x1ff)
        return self.run_to([0x200,N['start_game'],N['exit_menu']])
    def game(self,number=1):
        self.memory.data[MN['initial_level']]=number;self.memory.key=0x85
        self.cpu.pc=MN['menu_loop'];return self.run_to([N['main_loop'],0x200])
    def call(self,name,a=None):
        if a is not None:self.cpu.a=a
        self.cpu.pc=N.get(name,MN.get(name));self.cpu.stPushWord(0x1ff)
        return self.run_to([0x200],2_000_000)
    def frame(self,key=0,buttons=255):
        self.memory.data[0xdc00]=buttons;self.cpu.pc=N['main_loop'];sampled=False
        for _ in range(800000):
            if self.cpu.pc==0x200 or sampled and self.cpu.pc==N['main_loop']:return self
            if self.cpu.pc==0xffe4:
                sampled=True;self.cpu.a=key;self.cpu.pc=self.cpu.stPopWord()+1
            else:self.cpu.step()
        raise AssertionError('game frame')
def get(m,n):return m.memory.data[N.get(n,MN.get(n))]
def raster(m):
    screen=m.memory.data[0x9000:0x97d0];raw=bytearray()
    for y in range(200):
        for x in range(320):
            a=2*((y//8)*40+x//8);g=int.from_bytes(screen[a:a+2],'little')
            raw.append(m.memory.data[g*64+(y%8)*8+x%8])
    return bytes(raw)
def drain_fx(m):
    for _ in range(140):
        if m.memory.data[FX['state']]==0:return m
        m.frame()
    raise AssertionError('Transition did not complete within129 frames')

class MenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boot=Machine().boot()
        assert cls.boot.cpu.pc==MN['menu_loop'],cls.boot.error
        cls.snapshot=bytes(cls.boot.memory.data);cls.attic=bytes(cls.boot.memory.attic);cls.colour=bytes(cls.boot.memory.colour)
        cls.banks=[[bytes(c) for c in b] for b in cls.boot.memory.banks]
    def machine(self):
        m=Machine();m.memory.data[:]=self.snapshot;m.memory.attic[:]=self.attic;m.memory.colour[:]=self.colour
        for b in range(4):
            for c in range(3):m.memory.banks[b][c][:]=self.banks[b][c]
        m.cpu.sp=self.boot.cpu.sp;m.memory.watch_title=False;m.memory.title_active=False
        return m
    def test_full_loader_title_and_exact_menu_pixels(self):
        m=self.boot;self.assertEqual(m.error,0);self.assertEqual(m.opened_names,['VYTI.DAT','VYMN.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT','VYSH.DAT'])
        self.assertEqual(m.closed,6);self.assertFalse(m.opened or m.active)
        self.assertEqual(raster(m),(ART/'original_menu_indices.bin').read_bytes())
        self.assertEqual((get(m,'initial_level'),get(m,'selection')),(1,0))
        for n,a in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000),('VYCL.DAT',0x5c300),('VYSH.DAT',0xb000)]:self.assertEqual(m.memory.data[a:a+len(m.files[n])],m.files[n])
        self.assertEqual(m.memory.data[0x10000:0x12000],m.before[0x10000:0x12000])
    def test_menu_wrap_keys_joystick_repeat_and_fire(self):
        m=self.machine();m.input(0x9d);self.assertEqual(get(m,'initial_level'),100)
        m.input(0x1d);self.assertEqual(get(m,'initial_level'),1)
        m.input(0x91);self.assertEqual(get(m,'selection'),3)
        m.input(0x11);self.assertEqual(get(m,'selection'),0)
        for _ in range(3):m.input(joy=0xef)
        self.assertEqual(get(m,'initial_level'),1);self.assertEqual(get(m,'selection'),0)
        m.input(joy=255);m.input(joy=0xf7);self.assertEqual(get(m,'initial_level'),2)
        for _ in range(19):m.input(joy=0xf7)
        self.assertEqual(get(m,'initial_level'),2)
        m.input(joy=0xf7);self.assertEqual(get(m,'initial_level'),3)
        for _ in range(4):m.input(joy=0xf7)
        self.assertEqual(get(m,'initial_level'),3)
        m.input(joy=0xf7);self.assertEqual(get(m,'initial_level'),4)
        for s in range(4):
            m.memory.data[MN['selection']]=s;m.call('menu_colours')
            for j in range(4):self.assertEqual([m.memory.banks[1][c][8+j] for c in range(3)],[255,0,0] if j==s else [255]*3)
    def test_placeholders_preserve_selection_and_level(self):
        m=self.machine();m.input(0x9d)
        for key,selection,placeholder in [(0x89,2,1),(0x86,3,2)]:
            m.input(key);self.assertEqual((get(m,'selection'),get(m,'placeholder'),get(m,'initial_level')),(selection,placeholder,100))
            self.assertNotEqual(raster(m),(ART/'original_menu_indices.bin').read_bytes())
            m.input(13);self.assertEqual((get(m,'selection'),get(m,'placeholder'),get(m,'initial_level')),(selection,0,100))
        m.input(0x1d);self.assertEqual(get(m,'initial_level'),100)
    def test_all_original_animations_and_cycle(self):
        m=self.machine();before=bytes(m.memory.data[0x12800:0x1f800])+bytes(m.memory.data[0x5c500:0x60000]);static=[[bytes(c) for c in b] for b in m.memory.banks]
        seen=[set() for _ in range(32)]
        for _ in range(84):
            m.call('menu_tick');m.call('cc_tick')
            for i in range(32):seen[i].add(m.memory.data[MN['menu_frames']+i])
        for i,a in enumerate(json.loads((ART/'build-report.json').read_text())['menu']['actors']):self.assertEqual(seen[i],set(range(a['frame_count'])))
        self.assertEqual(before,bytes(m.memory.data[0x12800:0x1f800])+bytes(m.memory.data[0x5c500:0x60000]))
        for b in range(4):
            for c in range(3):
                expected=bytearray(static[b][c]);actual=bytearray(m.memory.banks[b][c]);expected[2]=actual[2] if b==1 else expected[2];self.assertEqual(actual,expected)
    def test_full_cpu_clock_in_title_menu_game_and_basic_restore(self):
        for speed in (False,True):
            m=Machine();m.memory.data[0xd031]=(m.memory.data[0xd031]&~64)|(64 if speed else 0);m.memory.data[0xd054]=(m.memory.data[0xd054]&~64)|(64 if speed else 0)
            original=(m.memory.data[0xd031],m.memory.data[0xd054]);m.run_to([N['load_menu']])
            self.assertEqual(m.memory.data[0xd031]&64,64);self.assertEqual(m.memory.data[0xd054]&64,64)
            m.boot();self.assertEqual(m.memory.data[0xd031]&64,64);self.assertEqual(m.memory.data[0xd054]&64,64)
            m.game();self.assertEqual(m.memory.data[0xd031]&64,64);self.assertEqual(m.memory.data[0xd054]&64,64)
            m.frame(0x58);self.assertEqual(m.cpu.pc,0x200);self.assertEqual((m.memory.data[0xd031],m.memory.data[0xd054]),original)
    def test_KERNAL_menu_SEQ_has_original_romc_and_enabled_IRQ(self):
        m=Machine();m.memory.data[0xd030]=0x20
        m.run_to([N['load_menu']]);self.assertTrue(m.cpu.p&m.cpu.INTERRUPT);self.assertEqual(m.memory.data[0xd030]&32,0)
        m.run_to([N['finish_menu_load']]);self.assertTrue(m.cpu.p&m.cpu.INTERRUPT);self.assertEqual(m.memory.data[0xd030]&32,0)
        self.assertGreater(m.menu_io_calls,2*len(m.files['VYMN.DAT']))
        self.assertFalse(m.opened or m.active);m.boot();self.assertEqual(m.error,0)
    def test_selected_levels_handoff_fonts_and_static_palette(self):
        for level in (1,2,3,99,100):
            m=self.machine().game(level);self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(m.error,0)
            self.assertEqual(get(m,'number'),level);self.assertEqual(get(m,'player1_level'),level)
            self.assertEqual(int.from_bytes(m.memory.data[0x1a04:0x1a08],'little'),0);self.assertEqual(get(m,'player1_lives'),3)
            font=(ART/'menu_font.bin').read_bytes();actual=m.memory.data[0x4000:0x4800]
            self.assertEqual(actual[:0x400],font[:0x400]);self.assertEqual(actual[0x410:],font[0x410:])
            self.assertEqual(list(m.memory.data[N['p_active']:N['p_active']+8]),[0]*8)
            static=[[bytes(c) for c in b] for b in m.memory.banks]
            for _ in range(42):m.call('cc_tick')
            for b in range(4):
                for c in range(3):
                    expected=bytearray(static[b][c]);expected[19]=m.memory.banks[b][c][19] if b==1 else expected[19];self.assertEqual(m.memory.banks[b][c],expected)
            m.frame();self.assertEqual(get(m,'number'),level)
    def test_level_nav_palette_cycle_and_exit_run(self):
        m=self.machine().game(100);old_word=m.memory.data[N['cc_word']:N['cc_word']+2];m.frame(0x2b);self.assertEqual(get(m,'number'),100)
        m.frame();m.frame(0x2d);self.assertEqual(get(m,'number'),99)
        self.assertNotEqual(m.memory.data[N['cc_word']:N['cc_word']+2],old_word)
        m.frame(0x58);self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(m.memory.data[0x10000:0x12000],m.before[0x10000:0x12000]);self.assertEqual(m.memory.data[0x1120],0x10)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot()
        self.assertEqual(m.error,0);self.assertEqual(get(m,'initial_level'),1)
    def test_menu_exit_restores_basic_and_engine(self):
        m=self.machine();m.cpu.pc=MN['menu_loop'];m.memory.key=0x58;m.run_to([0x200]);self.assertEqual(m.error,0)
        for r in OLD.VIC_REGS:
            # p_startup saved/disabled hardware sprites before loader, unchanged baseline.
            expected=0 if r==0x15 else m.before[0xd000+r]
            self.assertEqual(m.memory.data[0xd000+r],expected,hex(r))
        self.assertEqual(m.memory.data[0x1120],0x10)
        self.assertEqual(m.memory.data[0x7000:0xa000],m.memory.attic[0x1000:0x4000])
    def test_release_guard_on_fire_confirm(self):
        m=self.machine();m.memory.data[MN['selection']]=1;m.memory.data[MN['fire_armed']]=1;m.cpu.pc=MN['menu_loop'];m.memory.data[0xdc00]=0xef
        m.run_to([MN['confirm']]);
        for _ in range(1000):m.cpu.step()
        self.assertNotEqual(m.cpu.pc,N['main_loop'])
        m.memory.data[0xdc00]=255;m.run_to([N['main_loop']]);self.assertEqual(get(m,'p_active'),0)

class ZCombatRegression(unittest.TestCase):
    def machine(self):return MenuTests().machine().game(1)
    def test_game_over_complete_explosion_R_and_X(self):
        OLD.CombatRegression.test_game_over_after_complete_explosion_R_and_X(self)
    def test_combat_limits_return_respawn_and_invulnerable_control(self):
        OLD.CombatRegression.test_simultaneous_combat_limits_return_and_respawn(self)
    def test_entry_fire_pool_fixed_target_and_wait_visibility(self):
        ProjectileCapacityTests.test_six_enemy_slots_targeting_and_full_pool(self)
    def test_return_follows_drifting_formation(self):
        OLD.CombatRegression.test_return_tracks_current_drifting_slot(self)
    def test_all100_palettes_keep_static_banks_and_cycle_phase(self):
        import convert_stage5c_palettes as PAL
        ids,words=PAL.decode((ART/'VYCL.DAT').read_bytes());m=self.machine()
        static=[[bytes(c) for c in b] for b in m.memory.banks];phase=bytes(m.memory.data[N['cc_word']:N['cc_word']+2])
        for number in range(1,101):
            m.call('transition',number);self.assertEqual(m.error,0);self.assertEqual(get(m,'number'),number)
            for c,shift in enumerate((8,4,0)):
                expected=bytes(((w>>shift)&15)*17 for w in words[ids[number-1]][:8])
                for index in range(17,25):
                    if index!=19:self.assertEqual(m.memory.banks[1][c][index],expected[index-17],(number,c,index))
                self.assertEqual(m.memory.banks[1][c][:16],static[1][c][:16]);self.assertEqual(m.memory.banks[2][c],static[2][c]);self.assertEqual(m.memory.banks[3][c],static[3][c])
            self.assertEqual(bytes(m.memory.data[N['cc_word']:N['cc_word']+2]),phase)
    def test_level_clear_press_release_wrap_score_lives_and_R(self):
        m=self.machine();T=OLD.OLD.T
        T.enemies(m,0);T.setv(m,'a_enabled',0);T.setv(m,'c_es',4,21);m.call('tick');self.assertEqual(get(m,'mode'),0)
        T.enemies(m,0);m.memory.data[0xdc00]=239;m.call('tick');self.assertEqual(get(m,'mode'),1)
        m.call('tick');self.assertEqual(get(m,'number'),1)
        m.memory.data[0xdc00]=255;m.call('tick');m.memory.data[0xdc00]=239;m.call('tick');drain_fx(m);self.assertEqual(get(m,'number'),2)
        m.call('transition',100);T.enemies(m,0);T.setv(m,'a_enabled',0);m.memory.data[0xdc00]=255;m.call('tick');m.call('tick');m.memory.data[0xdc00]=239;m.call('tick');drain_fx(m);self.assertEqual(get(m,'number'),1)
        m.memory.data[N['high_score']:N['high_score']+4]=(76543).to_bytes(4,'little');m.memory.data[N['player1_score']:N['player1_score']+4]=(1234).to_bytes(4,'little')
        m.call('restart');self.assertEqual(get(m,'number'),1);self.assertEqual(get(m,'player1_score'),0);self.assertEqual(int.from_bytes(m.memory.data[N['high_score']:N['high_score']+4],'little'),76543);self.assertEqual(get(m,'player1_lives'),3)
    def test_romc_basic_mapping_and_repeat_menu_start(self):
        m=Machine();m.memory.data[0xd030]=0x21;m.before=bytes(m.memory.data);m.boot();self.assertEqual(m.error,0)
        m.game(3);self.assertEqual(m.memory.data[0xd030]&32,0);self.assertEqual(get(m,'number'),3)
        m.frame(0x58);self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.memory.data[0xd030],0x21)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot();self.assertEqual(m.error,0);self.assertEqual(get(m,'initial_level'),1)
    def test_player_speed_and_keyboard_repeat(self):
        m=MenuTests().machine();m.memory.data[0xd613]=0x7f # cursor down held
        m.input(0x11);self.assertEqual(get(m,'selection'),1)
        for _ in range(19):m.input(0x11)
        self.assertEqual(get(m,'selection'),1)
        m.input(0x11);self.assertEqual(get(m,'selection'),2)
        m.memory.data[0xd613]=255;m.input();m.input(0x11);self.assertEqual(get(m,'selection'),3)
        m=MenuTests().machine().game(1);before=m.memory.data[0x1662]
        for _ in range(10):m.frame(buttons=0xf7)
        self.assertEqual(m.memory.data[0x1662],before+10);self.assertEqual(m.memory.data[0x1664],184)
    def test_new_menu_asset_failure_paths_restore_basic(self):
        for fault in ('missing','extra','header'):
            m=Machine()
            if fault=='missing':del m.files['VYMN.DAT']
            elif fault=='extra':m.files['VYMN.DAT']+=b'\0'
            else:
                b=bytearray(m.files['VYMN.DAT']);b[4]+=1;b[9]-=1 # altered header with unchanged sum16
                self.assertEqual(sum(b)&65535,sum(m.files['VYMN.DAT'])&65535)
                m.files['VYMN.DAT']=bytes(b)
            m.boot();self.assertEqual(m.cpu.pc,0x200);self.assertNotEqual(m.error,0);self.assertFalse(m.active or m.opened)
            self.assertEqual(m.memory.data[0x1120],0x10);self.assertEqual(m.memory.data[0xd070],m.before[0xd070])
    def test_X_during_pending_start_remains_responsive(self):
        m=MenuTests().machine();m.memory.data[MN['selection']]=1;m.memory.data[MN['fire_armed']]=1;m.memory.data[0xdc00]=239;m.cpu.pc=MN['menu_loop']
        m.run_to([MN['pending_wait']]);m.memory.key=0x58;m.run_to([0x200]);self.assertEqual(m.error,0)


# New star tests execute assembled instructions. Raster/GPU/DMA remain host models.
import convert_stage7a2_stars as STAR

def scall(m,name,a=None):
    if a is not None:m.cpu.a=a
    m.cpu.pc=S[name];m.cpu.stPushWord(0x1ff)
    return m.run_to([0x200],500000)

def star_bytes(m):return bytes(m.memory.data[STAR.BUFFER:STAR.BUFFER+24000])
def oracle(m):
    b=bytearray(24000)
    for i in range(STAR.COUNT):
        y=m.memory.data[S['ys']+i]
        xbase=m.memory.data[S['xbase_lo']+i]+256*m.memory.data[S['xbase_hi']+i]
        bits=m.memory.data[S['draw_bits']+i]
        b[(y//8)*960+(y%8)*8+xbase]|=bits
    return bytes(b)

def background_pixels(m):
    pixels={}
    for row in range(25):
        for col in range(15):
            a=0xe002+row*192+col*2
            g=int.from_bytes(m.memory.data[a:a+2],'little')&8191
            for ry in range(8):
                for sx in range(16):
                    v=(m.memory.data[g*64+ry*8+sx//2]>>(4*(sx%2)))&15
                    if v:pixels[col*16+sx,row*8+ry]=48+v
    return pixels

def composite(m):
    # Actual fetched NCM prefix plus transparent/opaque dynamic GOTOX records.
    pixels=background_pixels(m)
    for row in range(25):
        for slot in range(m.memory.data[N['v014_row_count']+row]):
            off=row*192+84+slot*4;a=0xe000+off
            go=int.from_bytes(m.memory.data[a:a+2],'little')
            attr=int.from_bytes(m.memory.colour[off:off+2],'big')
            cw=int.from_bytes(m.memory.colour[off+2:off+4],'big')
            glyph=int.from_bytes(m.memory.data[a+2:a+4],'little')&8191
            x=(go&1023)//2;shift=((go>>13)&7)*(-1 if go&0x1000 else 1)
            for ry in range(8):
                for sx in range(16):
                    if not 0<=x+sx<240:continue
                    v=(m.memory.data[glyph*64+(ry+shift)*8+sx//2]>>(4*(sx%2)))&15
                    xy=(x+sx,row*8+ry)
                    if v:pixels[xy]=(cw&240)+v
                    elif not attr&0x8000:pixels.pop(xy,None)
    return pixels

class StarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(MenuTests,'snapshot'):MenuTests.setUpClass()
    def machine(self):return MenuTests().machine().game(1)
    def test_background_binding_buffer_and_exact_colours(self):
        m=self.machine();self.assertEqual(star_bytes(m),oracle(m))
        self.assertEqual(m.memory.data[S['ready']],1)
        self.assertEqual(len(background_pixels(m)),48)
        for row in range(25):
            for col in range(15):
                a=0xe002+row*192+col*2
                self.assertEqual(int.from_bytes(m.memory.data[a:a+2],'little'),0x600+row*15+col)
                self.assertEqual(m.memory.colour[row*192+2+col*2:row*192+4+col*2],b'\x08\x30')
        for i,rgb in enumerate(((0,0,0),*STAR.RGB)):
            self.assertEqual(tuple(m.memory.banks[1][c][48+i] for c in range(3)),rgb)
        self.assertEqual((m.memory.data[0xd031]&64,m.memory.data[0xd054]&64),(64,64))
    def test_1600_frames_exact_rates_wrap_and_dma_bounds(self):
        m=self.machine();initial=star_bytes(m);start_y=bytes(m.memory.data[S['ys']:S['ys']+48]);maximum=0
        before=bytes(m.memory.data);colours=bytes(m.memory.colour)
        for frame in range(1,1601):
            start=len(m.memory.base.transfers);scall(m,'frame')
            jobs=m.memory.base.transfers[start:];maximum=max(maximum,len(jobs))
            due=sum(16 for d in STAR.DIVIDERS if frame%d==0)
            self.assertEqual(len(jobs),due*4)
            for src,dst,n in jobs:
                self.assertEqual(n,1)
                self.assertTrue(src==0x6800 and 0x18000<=dst<0x1ddc0 or dst==0x6800 and 0x18000<=src<0x1ddc0)
            if frame%8==0 or frame<9:self.assertEqual(star_bytes(m),oracle(m),frame)
            for i,y in enumerate(start_y):self.assertEqual(m.memory.data[S['ys']+i],(y+frame//STAR.DIVIDERS[i//16])%200)
        self.assertEqual(star_bytes(m),initial);self.assertEqual(maximum,192)
        self.assertEqual(m.memory.colour,colours)
        for lo,hi in ((0x10000,0x18000),(0x1ddc0,0x20000),(0x40000,0x5c4dc)):
            self.assertEqual(m.memory.data[lo:hi],before[lo:hi])
    def test_all_edges_adjacent_nibbles(self):
        m=self.machine();scall(m,'clear')
        # Set adjacent stars at both X edges with distinct nibbles, same Y=199.
        for i,x in enumerate((0,1,238,239)):
            xb=(x//16)*64+(x%16)//2
            m.memory.data[S['xbase_lo']+i]=xb&255;m.memory.data[S['xbase_hi']+i]=xb>>8
            m.memory.data[S['draw_bits']+i]=(1+i%3)<<(4*(x%2))
            m.memory.data[S['ys']+i]=199
        scall(m,'paint_all');self.assertEqual(star_bytes(m),oracle(m))
        for _ in range(8):scall(m,'frame')
        self.assertEqual(list(m.memory.data[S['ys']:S['ys']+4]),[0]*4)
        self.assertEqual(star_bytes(m),oracle(m))
    def test_prefix_hud_slots_and_palettes_unmodified_during_updates(self):
        m=self.machine();pal=[[bytes(c) for c in b] for b in m.memory.banks]
        hud=[bytes(m.memory.data[0xe000+r*192+32:0xe000+r*192+84]) for r in range(25)]
        colour=bytes(m.memory.colour);registers=bytes(m.memory.data[0xd000:0xd100])
        sprite_graphics=bytes(m.memory.data[0x8900:0x8a80]);counts=bytes(m.memory.data[N['v014_row_count']:N['v014_row_count']+25])
        for _ in range(40):scall(m,'frame')
        self.assertEqual(m.memory.data[0xd000:0xd100],registers)
        self.assertEqual(m.memory.data[0x8900:0x8a80],sprite_graphics)
        self.assertEqual(m.memory.colour,colour)
        self.assertEqual(m.memory.data[N['v014_row_count']:N['v014_row_count']+25],counts)
        self.assertEqual([[bytes(c) for c in b] for b in m.memory.banks],pal)
        for r in range(25):self.assertEqual(m.memory.data[0xe000+r*192+32:0xe000+r*192+84],hud[r])
    def test_level_changes_keep_background_and_exit_restores_palette(self):
        m=self.machine();saved=bytes(m.memory.data[S['palette_saved']:S['palette_saved']+12]);b=star_bytes(m)
        for number in (2,3,29,37,54,100,1):
            m.call('transition',number);self.assertEqual(star_bytes(m),b)
            self.assertEqual(background_pixels(m),{(x,y):48+1+i//16 for i,(x,y) in enumerate(zip(json.loads((ART/'build-report.json').read_text())['starfield']['x'],m.memory.data[S['ys']:S['ys']+48]))})
        m.frame(0x58);self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(b''.join(bytes(m.memory.banks[1][c][48:52]) for c in range(3)),saved)
        self.assertEqual(m.memory.data[S['ready']],0)
    def test_transparency_clipping_all_four_edges_and_no_trails(self):
        m=self.machine();T=OLD.OLD.T
        T.enemies(m,0);m.memory.data[0x7603]=1;T.setv(m,'c_ps',2)
        T.setv(m,'c_es',1,0);T.setv(m,'e_phase',3,0)
        before=star_bytes(m);seen_hidden=seen_holes=False
        for x,y in ((-15,-15),(-1,0),(0,0),(224,0),(239,0),(240,0),(0,184),(0,199),(0,200),(11,2),(11,20),(11,100)):
            T.setv(m,'e_xlo',x&255,0);T.setv(m,'e_xhi',(x>>8)&255,0)
            T.setv(m,'e_ylo',y&255,0);T.setv(m,'e_yhi',(y>>8)&255,0)
            m.call('e_render');pixels=composite(m);bg=background_pixels(m)
            self.assertEqual(star_bytes(m),before)
            self.assertTrue(all(0<=xx<240 and 0<=yy<200 for xx,yy in pixels))
            self.assertLessEqual(max(m.memory.data[N['v014_row_count']:N['v014_row_count']+25]),24)
            for xy,v in bg.items():
                if x<=xy[0]<x+16 and y<=xy[1]<y+16:
                    if pixels.get(xy)==v:seen_holes=True
                    else:seen_hidden=True
        # Deliberately align one star with each original-frame pixel to exercise both mask cases.
        xs=json.loads((ART/'build-report.json').read_text())['starfield']['x'];i=0
        m.memory.data[S['ys']+i]=100;scall(m,'clear');scall(m,'paint_all')
        for sy in range(16):
            for sx in range(16):
                T.setv(m,'e_xlo',(xs[i]-sx)&255,0);T.setv(m,'e_xhi',255 if xs[i]-sx<0 else 0,0)
                T.setv(m,'e_ylo',100-sy,0);T.setv(m,'e_yhi',0,0)
                m.call('e_render');v=composite(m).get((xs[i],100))
                seen_holes|=v==49;seen_hidden|=v not in (None,49)
                if seen_hidden and seen_holes:break
            if seen_hidden and seen_holes:break
        self.assertTrue(seen_hidden);self.assertTrue(seen_holes)
        T.setv(m,'c_es',0,0);m.call('e_render');self.assertEqual(composite(m),background_pixels(m))
    def test_actual_host_cost_without_runtime_profiler(self):
        m=self.machine();jobs=[];cycles=[]
        for phase in range(8):
            before=m.cpu.processorCycles;start=len(m.memory.base.transfers);scall(m,'frame')
            cycles.append(m.cpu.processorCycles-before);batch=m.memory.base.transfers[start:]
            jobs.append({'dma_jobs':len(batch),'payload_bytes':sum(n for _,_,n in batch),'CPU_model_cycles':cycles[-1]})
        self.assertEqual([j['dma_jobs'] for j in jobs],[0,64,0,128,0,64,0,192])
        self.assertLess(max(cycles),30000) # Bounded shared displacement path, no extra DMA per move.
        m.memory.data[S['clock']]=7;m.memory.data[S['ys']:S['ys']+48]=bytes([199])*48
        scall(m,'clear');scall(m,'paint_all')
        before=m.cpu.processorCycles;start=len(m.memory.base.transfers);scall(m,'frame')
        wrapping={'CPU_model_cycles':m.cpu.processorCycles-before,'dma_jobs':len(m.memory.base.transfers)-start}
        self.assertEqual(wrapping['dma_jobs'],192);self.assertEqual(star_bytes(m),oracle(m))
        self.assertLess(wrapping['CPU_model_cycles'],30000)
        report={'stage':'7b5a','PRG_sha256':BUILD.BASE.sha((ART/'STAGE7B5A.PRG').read_bytes()),'measurement_kind':'actual assembled instructions, narrow 6502/45GS02 host adapter; DMA instantaneous, NOT XEMU timing','phases':jobs,'mean_CPU_model_cycles':sum(cycles)/8,'max_CPU_model_cycles':max(cycles),'mean_DMA_jobs':sum(j['dma_jobs'] for j in jobs)/8,'max_DMA_jobs':192,'simultaneous_all_stars_wrap':wrapping,'runtime_profiler':False,'XEMU':'NOT_RUN; user acceptance required'}
        (ART/'starfield-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
        print('Stage7b5a actual instruction/DMA host model:',json.dumps(report))
    def test_disk_and_original_assets(self):
        BUILD.protect_stable()
        names=[f['name'] for f in json.loads((ART/'build-report.json').read_text())['files']]
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE7B5A.d81').read_bytes(),[(n,(ART/(n+'.PRG' if n=='STAGE7B5A' else n)).read_bytes(),0x82 if n=='STAGE7B5A' else 0x81) for n in names])
        for n in ('VYTI.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT'):
            self.assertEqual((ART/n).read_bytes(),(ROOT/'releases/stage_6b1'/n).read_bytes())


    def test_exact_accepted_star_parameters_and_six_global_API_labels(self):
        old=json.loads((ROOT/'releases/stage_7a1/build-report.json').read_text())['starfield']
        new=json.loads((ART/'build-report.json').read_text())['starfield']
        for k in ('seed','count','colours_RGB','dividers_frames','pixels_per_second','x','initial_y','buffer','palette_indices'):
            self.assertEqual(new[k],old[k],k)
        self.assertEqual((ART/'stars_layout.inc').read_bytes(),(ROOT/'releases/stage_7a1/stars_layout.inc').read_bytes())
        for public,internal in [('init','init'),('tick','frame'),('bind','bind'),('restore','restore'),('reset','reset'),('set_speed_mode','set_speed_mode')]:
            self.assertEqual(N['starfield_'+public],S[internal])
    def test_idempotent_init_reserved_speed_API_reset_and_no_test_keys(self):
        m=self.machine()
        for _ in range(37):scall(m,'frame')
        buf=star_bytes(m);ys=bytes(m.memory.data[S['ys']:S['ys']+48]);phase=m.memory.data[S['clock']]
        saved=bytes(m.memory.data[S['palette_saved']:S['palette_saved']+12])
        scall(m,'init');self.assertEqual(star_bytes(m),buf);self.assertEqual(m.memory.data[S['clock']],phase)
        self.assertEqual(m.memory.data[S['palette_saved']:S['palette_saved']+12],saved)
        for mode in (0,1,255,0):
            scall(m,'set_speed_mode',mode)
            self.assertEqual(bool(m.cpu.p&m.cpu.CARRY),mode>1)
            self.assertEqual(star_bytes(m),buf);self.assertEqual(m.memory.data[S['ys']:S['ys']+48],ys)
            self.assertEqual(m.memory.data[S['clock']],phase);self.assertEqual(m.memory.data[S['speed_mode']],0 if mode==0 else 1)
        border=m.memory.data[0xd020]
        for key in (0x42,0x56,0x62,0x76):
            m.frame(key);self.assertEqual(star_bytes(m),oracle(m));self.assertEqual(m.memory.data[0xd020],border)
        self.assertNotIn('key',S);self.assertNotIn('span',S);self.assertNotIn('marker',S);self.assertNotIn('read_raster',S)
        self.assertEqual(m.memory.data[0xcfec:0xcff6],bytes(10))
        scall(m,'reset');self.assertEqual(m.memory.data[S['clock']],0)
        self.assertEqual(m.memory.data[S['ys']:S['ys']+48],m.memory.data[S['initial_y']:S['initial_y']+48])
        self.assertEqual(star_bytes(m),oracle(m));self.assertEqual(m.memory.data[S['palette_saved']:S['palette_saved']+12],saved)
    def test_continuous_level_clear_press_release_and_100_wrap(self):
        m=self.machine();T=OLD.OLD.T
        for _ in range(19):m.frame()
        ys=bytes(m.memory.data[S['ys']:S['ys']+48]);phase=m.memory.data[S['clock']]
        T.enemies(m,0);T.setv(m,'a_enabled',0);m.call('tick')
        self.assertEqual(get(m,'mode'),1)
        for frame in range(1,161):
            m.frame(buttons=255)
            self.assertEqual(get(m,'mode'),1);self.assertEqual(get(m,'number'),1)
            self.assertEqual(m.memory.data[S['clock']],(phase+frame)&255)
            for i,y in enumerate(ys):
                d=STAR.DIVIDERS[i//16]
                moves=(phase+frame)//d-phase//d
                self.assertEqual(m.memory.data[S['ys']+i],(y+moves)%200)
            self.assertEqual(star_bytes(m),oracle(m))
            for row,text in [(11,[12,5,22,5,12,32,3,12,5,1,18]),(13,[16,18,5,19,19,32,2,21,20,20,15,14,32,20,15,32,3,15,14,20,9,14,21,5])]:
                a=0xe000+row*192+86
                self.assertEqual(list(m.memory.data[a:a+len(text)*2:2]),text)
        before=(bytes(m.memory.data[S['ys']:S['ys']+48]),m.memory.data[S['clock']])
        m.frame(buttons=239);self.assertEqual(get(m,'mode'),2)
        self.assertEqual(m.memory.data[S['clock']],(before[1]+1)&255)
        self.assertEqual(star_bytes(m),oracle(m))
        drain_fx(m);self.assertEqual(get(m,'number'),2)
        m.call('transition',100);T.enemies(m,0);T.setv(m,'a_enabled',0);m.memory.data[0xdc00]=239;m.call('tick')
        self.assertEqual(get(m,'mode'),1)
        m.frame(buttons=239);self.assertEqual(get(m,'number'),100)
        m.frame(buttons=255);m.frame(buttons=239);drain_fx(m);self.assertEqual(get(m,'number'),1)
        self.assertEqual(star_bytes(m),oracle(m))
    def test_all100_transitions_and_R_never_blank_or_reset_background(self):
        m=self.machine()
        class PrefixWatch(MenuMemory):
            def __setitem__(self,a,v):
                if getattr(self,'watch_prefix',False):
                    if 0xe000<=a<0xe000+4800 and (getattr(self,'linear',False) or not getattr(self,'sys_map',False)):
                        if 2<=((a-0xe000)%192)<32 and self.data[a]!=v:self.changed_prefix.append((a,v))
                    if 0xff80000<=a<0xff80000+4800 and 2<=((a-0xff80000)%192)<32:
                        if self.colour[a-0xff80000]!=v:self.changed_prefix.append((a,v))
                super().__setitem__(a,v)
        m.memory.__class__=PrefixWatch;m.memory.watch_prefix=True;m.memory.changed_prefix=[]
        for _ in range(37):scall(m,'frame')
        for level in range(1,101):
            buf=star_bytes(m);ys=bytes(m.memory.data[S['ys']:S['ys']+48]);phase=m.memory.data[S['clock']]
            m.call('transition',level);self.assertEqual(m.error,0)
            self.assertEqual(star_bytes(m),buf);self.assertEqual(m.memory.data[S['ys']:S['ys']+48],ys)
            self.assertEqual(m.memory.data[S['clock']],phase);self.assertEqual(m.memory.changed_prefix,[])
            scall(m,'frame');self.assertEqual(star_bytes(m),oracle(m))
        before=star_bytes(m);ys=bytes(m.memory.data[S['ys']:S['ys']+48]);phase=m.memory.data[S['clock']]
        m.memory.data[N['high_score']:N['high_score']+4]=(54321).to_bytes(4,'little')
        m.call('restart');self.assertEqual(get(m,'number'),1);self.assertEqual(get(m,'player1_lives'),3)
        self.assertEqual(get(m,'player1_score'),0)
        self.assertEqual(int.from_bytes(m.memory.data[N['high_score']:N['high_score']+4],'little'),54321)
        self.assertEqual(star_bytes(m),before);self.assertEqual(m.memory.data[S['ys']:S['ys']+48],ys)
        self.assertEqual(m.memory.data[S['clock']],phase);self.assertEqual(m.memory.changed_prefix,[])
    def test_selected_F1_levels_have_no_stars_until_game_and_repeat_start(self):
        for level in (1,2,3,11,100):
            m=MenuTests().machine();self.assertEqual(m.memory.data[S['ready']],0)
            m.game(level);self.assertEqual(m.memory.data[S['ready']],1);self.assertEqual(get(m,'number'),level)
            self.assertEqual(star_bytes(m),oracle(m))
        m.frame(0x58);self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.memory.data[S['ready']],0)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot()
        self.assertEqual(m.error,0);self.assertEqual(m.memory.data[S['ready']],0)
        self.assertEqual(raster(m),(ART/'original_menu_indices.bin').read_bytes())
        m.game(3);self.assertEqual(m.memory.data[S['ready']],1);self.assertEqual(star_bytes(m),oracle(m))



class TransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(MenuTests,'snapshot'):MenuTests.setUpClass()
    def machine(self,level=1):return MenuTests().machine().game(level)
    def begin(self,m):
        T=OLD.OLD.T;T.enemies(m,0);T.setv(m,'a_enabled',0)
        m.memory.data[0xdc00]=255;m.call('tick')
        self.assertEqual(get(m,'mode'),1)
        m.frame(buttons=255);m.frame(buttons=239)
        self.assertEqual(m.memory.data[FX['state']],1);self.assertEqual(get(m,'mode'),2)
        return m
    def hud(self,m):
        return tuple((bytes(m.memory.data[0xe000+r*192+32:0xe000+r*192+84]),bytes(m.memory.colour[r*192+32:r*192+84])) for r in range(25))
    def columns(self,m):
        # Prefix must ALWAYS retain the original375 star bitmap glyphs.
        for r in range(25):
            for c in range(15):
                a=0xe002+r*192+c*2
                self.assertEqual(int.from_bytes(m.memory.data[a:a+2],'little'),0x600+r*15+c)
        return [None]*15
    def pixels(self,m):
        raw=star_bytes(m)
        return bytes((raw[((y//8)*15+x//16)*64+(y%8)*8+(x%16)//2]>>(4 if x%2==0 else 0))&15 for y in range(200) for x in range(240))
    def test_actual_sprite_pixels_white_and_unchanged_hitboxes(self):
        m=self.machine();T=OLD.OLD.T
        self.assertEqual(m.memory.data[0xd01c],0xff)
        self.assertEqual((m.memory.data[0xd025],m.memory.data[0xd026]),(10,13))
        for slot in range(8):
            g=int.from_bytes(m.memory.data[0x8900+slot*2:0x8902+slot*2],'little')*64
            raw=m.memory.data[g:g+64]
            matrix={(x,y):(raw[y*3+x//4]>>(6-2*(x%4)))&3 for y in range(21) for x in range(12)}
            original=[[0,1,0],[0,1,0],[0,1,0],[3,1,3],[2,1,2],[2,2,2],[0,2,0]]
            rows=list(reversed(original)) if slot<2 else original
            code={0:0,1:1,2:3,3:2}
            expected={(x,y):code[rows[y//2][x]] for y in range(14) for x in range(3) if rows[y//2][x]}
            self.assertEqual({k:v for k,v in matrix.items() if v},expected)
            self.assertEqual(m.memory.data[0xd027+slot],16)
            T.setv(m,'p_xpos',100,slot);T.setv(m,'p_ypos',60,slot)
            m.cpu.x=slot;m.call('c_shot_box')
            self.assertEqual((get(m,'c_ax'),get(m,'c_ar'),get(m,'c_ay'),get(m,'c_ab')),(100 if slot<2 else 99,101 if slot<2 else 102,60,64))
        for level in range(1,101):
            m.call('transition',level)
            self.assertEqual(m.memory.data[0xd01c],0xff)
            self.assertEqual(tuple(m.memory.banks[2][c][10] for c in range(3)),(255,255,255))
            self.assertEqual(tuple(m.memory.banks[2][c][13] for c in range(3)),(238,0,0))
            self.assertEqual(tuple(m.memory.banks[2][c][16] for c in range(3)),(51,68,68))
    def test_fast_mode_modulo_rates_exact_and_same_DMA_peak(self):
        m=self.machine();before=bytes(m.memory.data[S['ys']:S['ys']+48])
        scall(m,'set_speed_mode',1);self.assertFalse(m.cpu.p&m.cpu.CARRY)
        peak=0
        for frame in range(1,201):
            start=len(m.memory.base.transfers);cycles=m.cpu.processorCycles;scall(m,'frame')
            self.assertEqual(len(m.memory.base.transfers)-start,192)
            peak=max(peak,m.cpu.processorCycles-cycles)
            self.assertEqual(star_bytes(m),oracle(m))
            for i,y in enumerate(before):self.assertEqual(m.memory.data[S['ys']+i],(y+frame*(1<<(i//16)))%200)
        self.assertLess(peak,30000)
        self.assertEqual(m.memory.data[S['ys']:S['ys']+48],before)
        phase=m.memory.data[S['clock']];scall(m,'set_speed_mode',0)
        self.assertEqual(m.memory.data[S['clock']],phase);self.assertEqual(m.memory.data[S['ys']:S['ys']+48],before)
    def test_exact_50_39_39_1_concentric_pixels_HUD_palette_score(self):
        m=self.machine();self.begin(m);hud=self.hud(m)
        pal=[[bytes(c) for c in b] for b in m.memory.banks]
        m.memory.data[N['player1_score']:N['player1_score']+4]=(23456).to_bytes(4,'little')
        m.memory.data[N['high_score']:N['high_score']+4]=(65432).to_bytes(4,'little')
        m.memory.data[N['player1_lives']]=2
        ys=bytes(m.memory.data[S['ys']:S['ys']+48]);phase=m.memory.data[S['clock']]
        counts={1:0,2:0,3:0,4:0};cost=[];jobs=[]
        for frame in range(1,130):
            state=m.memory.data[FX['state']];counts[state]+=1
            start=m.cpu.processorCycles;dma=len(m.memory.base.transfers);m.frame()
            cost.append(m.cpu.processorCycles-start);jobs.append(len(m.memory.base.transfers)-dma)
            self.columns(m)
            if frame<129:
                self.assertEqual(get(m,'number'),1);self.assertEqual(get(m,'mode'),2)
                self.assertEqual(self.hud(m),hud);self.assertEqual(m.memory.data[0xd015],0)
                for bank in range(4):
                    for c in range(3):
                        a=bytearray(m.memory.banks[bank][c]);e=bytearray(pal[bank][c])
                        if bank==1:e[19]=a[19]
                        self.assertEqual(a,e)
            # Every newly-painted ring, test all48000 output pixels, including
            # moving unoccluded stars and continuity of centre-black rectangle.
            if 53<=frame<=128 and (frame-50)%3==0:
                pixels=self.pixels(m)
                baseline=oracle(m)
                cd=12-((frame-53)//3) if frame<=89 else 0
                bd=13 if frame<=89 else 12-((frame-92)//3)
                for y in range(200):
                    for x in range(240):
                        depth=min(x//8,29-x//8,y//8,24-y//8)
                        if depth>=bd:expected=0
                        elif depth>=cd:expected=4+depth%4
                        else:
                            a=((y//8)*15+x//16)*64+(y%8)*8+(x%16)//2
                            expected=(baseline[a]>>(4 if x%2==0 else 0))&15
                        if pixels[y*240+x]!=expected:self.fail((frame,x,y,depth,pixels[y*240+x],expected))
            for i,y in enumerate(ys):self.assertEqual(m.memory.data[S['ys']+i],(y+frame*(1<<(i//16)))%200)
            self.assertEqual(m.memory.data[S['clock']],(phase+frame)&255)
        self.assertEqual(counts,{1:50,2:39,3:39,4:1})
        self.assertEqual(get(m,'number'),2);self.assertEqual(get(m,'mode'),0)
        self.assertEqual(m.memory.data[S['speed_mode']],0);self.assertEqual(star_bytes(m),oracle(m))
        self.assertEqual(int.from_bytes(m.memory.data[N['player1_score']:N['player1_score']+4],'little'),23456)
        self.assertEqual(int.from_bytes(m.memory.data[N['high_score']:N['high_score']+4],'little'),65432)
        self.assertEqual(get(m,'player1_lives'),2)
        report={'stage':'7b5a','frames':counts,'max_CPU_model_cycles':max(cost),'max_DMA_jobs':max(jobs),'CPU_cycles_by_frame':cost,'DMA_jobs_by_frame':jobs,'timing':'host model, DMA instantaneous, NOT XEMU','XEMU':'NOT_RUN'}
        (ART/'transition-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
        print('Stage7b5a transition model',max(cost),'cycles',max(jobs),'DMA jobs')
    def test_four_level_edges_and_plus_minus_bypass_animation(self):
        for level,next_level in ((1,2),(2,3),(99,100),(100,1)):
            m=self.machine(level);self.begin(m);drain_fx(m)
            self.assertEqual(get(m,'number'),next_level);self.assertEqual(m.error,0)
            self.assertEqual(self.columns(m),[None]*15);self.assertEqual(m.memory.data[S['speed_mode']],0)
        m=self.machine(2);m.frame(0x2b);self.assertEqual(get(m,'number'),3)
        self.assertEqual(m.memory.data[FX['state']],0);self.assertEqual(m.memory.data[S['speed_mode']],0)
        m.frame();m.frame(0x2d);self.assertEqual(get(m,'number'),2);self.assertEqual(m.memory.data[FX['state']],0)
    def test_X_every_phase_restores_basic_palette_and_second_RUN(self):
        for target,frames in ((1,0),(2,53),(3,92),(4,128)):
            m=self.machine();self.begin(m)
            for _ in range(frames):m.frame()
            self.assertEqual(m.memory.data[FX['state']],target)
            saved=bytes(m.memory.data[S['palette_saved']:S['palette_saved']+12])
            m.frame(0x58);self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.memory.data[S['ready']],0)
            self.assertEqual(b''.join(bytes(m.memory.banks[1][c][48:52]) for c in range(3)),saved)
            self.assertEqual(m.memory.data[0x10000:0x12000],m.before[0x10000:0x12000])
            self.assertEqual(m.memory.data[0x1f800:0x20000],m.before[0x1f800:0x20000])
            self.assertEqual(m.memory.data[0xd01c],0x83)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot();self.assertEqual(m.error,0)
        m.game();self.assertEqual(m.memory.data[FX['state']],0);self.assertEqual(m.memory.data[S['speed_mode']],0)
        self.assertEqual(self.columns(m),[None]*15)
    def test_transition_palette_snapshot_and_two_consecutive_transitions(self):
        m=self.machine()
        self.assertEqual([tuple(m.memory.banks[1][c][i] for c in range(3)) for i in range(52,56)],[(0,102,238),(221,221,0),(170,0,0),(0,0,170)])
        saved=bytes(m.memory.data[FX['saved_palette']:FX['saved_palette']+12])
        shared=bytes(m.memory.data[FX['saved_shared']:FX['saved_shared']+2])
        for level in (2,3):
            self.begin(m);drain_fx(m)
            self.assertEqual(get(m,'number'),level);self.assertEqual(star_bytes(m),oracle(m))
        m.frame(0x58);self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(b''.join(bytes(m.memory.banks[1][c][52:56]) for c in range(3)),saved)
        self.assertEqual(bytes(m.memory.data[0xd025:0xd027]),shared)
        self.assertEqual(m.memory.data[0xd01c],0x83)
        self.assertEqual(bytes(m.memory.data[FX['saved_sprite_palette']:FX['saved_sprite_palette']+3]),bytes(m.memory.banks[2][c][16] for c in range(3)))

class ProjectileCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(MenuTests,'snapshot'):MenuTests.setUpClass()
    def machine(self):return MenuTests().machine().game(1)
    def test_six_enemy_slots_targeting_and_full_pool(self):
        m=self.machine();T=OLD.OLD.T
        T.enemies(m,0);T.setv(m,'c_es',2,0);T.setv(m,'e_phase',1,0);T.setv(m,'e_visible',1,0)
        for f,v in [('e_xlo',90),('e_xhi',0),('e_ylo',70),('e_yhi',0),('a_hidden',0)]:T.setv(m,f,v,0)
        for slot in range(2):T.setv(m,'p_active',1,slot);T.setv(m,'p_xpos',100,slot);T.setv(m,'p_ypos',100,slot)
        for shot in range(6):
            m.memory.data[N['c_es']:N['c_es']+23]=bytes(23);actor=shot//2
            for f,v in [('c_es',2),('e_phase',1),('e_visible',1),('e_xlo',90),('e_xhi',0),('e_ylo',70),('e_yhi',0),('a_hidden',0)]:T.setv(m,f,v,actor)
            fset(m,'pending',1,actor);m.call('a_fire')
        self.assertEqual(list(m.memory.data[N['p_active']:N['p_active']+8]),[1]*8)
        snapshot=bytes(m.memory.data[0x1f00:0x1f78]);T.setv(m,'p_cooldown',0);T.setv(m,'p_random_lo',0);m.call('a_fire')
        self.assertEqual(list(m.memory.data[N['p_active']:N['p_active']+8]),[1]*8)
        for i in range(2,8):
            self.assertEqual(m.memory.data[N['p_target_x']+i],m.memory.data[0x1662]+8)
            self.assertEqual(m.memory.data[N['p_target_y']+i],184)
        m.call('p_publish');self.assertEqual(m.memory.data[0xd015],255);self.assertEqual(m.memory.data[0xd076],255)
        ptrs=[int.from_bytes(m.memory.data[0x8900+i*2:0x8902+i*2],'little') for i in range(8)]
        self.assertEqual(ptrs,[0x228]*2+[0x229]*6)
        for i in range(8):
            native_x=(m.memory.data[0xd04c]|((m.memory.data[0xd04d]&15)<<8))+2*m.memory.data[N['p_xpos']+i]-3
            x=m.memory.data[0xd000+i*2]+((m.memory.data[0xd010]>>i&1)<<8)
            self.assertEqual(x,native_x)
        # Original target remains saved after player movement.
        saved=m.memory.data[N['p_target_x']+2];m.memory.data[0x1662]+=20;m.call('p_update')
        for i in range(2,8):self.assertEqual(m.memory.data[N['p_target_x']+i],saved)
    def test_eight_channel_X_Y_MSB_and_bit9_masks(self):
        m=self.machine()
        m.memory.data[0xd04c]=80;m.memory.data[0xd04d]=0
        m.memory.data[0xd04e]=248;m.memory.data[0xd04f]=1
        for i in range(8):
            m.memory.data[N['p_active']+i]=1;m.memory.data[N['p_xpos']+i]=239;m.memory.data[N['p_ypos']+i]=196
        m.call('p_publish');self.assertEqual(m.memory.data[0xd015],255)
        for i in range(8):
            x=m.memory.data[0xd000+2*i]+((m.memory.data[0xd010]>>i&1)<<8)+((m.memory.data[0xd05f]>>i&1)<<9)
            y=m.memory.data[0xd001+2*i]+((m.memory.data[0xd077]>>i&1)<<8)+((m.memory.data[0xd078]>>i&1)<<9)
            self.assertEqual((x,y),(555,896),i)
    def test_last_two_slots_move_expire_and_collide_independently(self):
        m=self.machine();T=OLD.OLD.T;T.enemies(m,0);T.setv(m,'a_enabled',0)
        for i in (6,7):
            T.setv(m,'p_active',1,i);T.setv(m,'p_xpos',100,i);T.setv(m,'p_ypos',50+i,i);T.setv(m,'p_vy',1,i)
        m.call('p_update');self.assertEqual(m.memory.data[N['p_ypos']+6],57);self.assertEqual(m.memory.data[N['p_ypos']+7],58)
        T.setv(m,'p_ypos',196,6);m.call('p_update');self.assertEqual(m.memory.data[N['p_active']+6],0);self.assertEqual(m.memory.data[N['p_active']+7],1)
        T.setv(m,'p_xpos',m.memory.data[0x1662]+5,7);T.setv(m,'p_ypos',187,7);T.setv(m,'c_ps',0);m.call('c_collisions')
        self.assertEqual(get(m,'c_ps'),1);self.assertEqual(m.memory.data[N['p_active']+7],0)
    def test_due_single_survivor_selection_statuses_and_cap(self):
        m=self.machine();T=OLD.OLD.T;T.enemies(m,0);T.setv(m,'a_ready',1);T.setv(m,'a_start_tick',0)
        T.setv(m,'c_es',1,21);T.setv(m,'e_phase',3,21);m.call('a_postframe')
        self.assertEqual(m.memory.data[N['c_es']+21],3);self.assertEqual(get(m,'a_event_enemy'),21)
        # Empty list returns immediately with the attack still due.
        T.enemies(m,0);T.setv(m,'a_start_tick',0);T.setv(m,'a_event',0);m.call('a_postframe');self.assertEqual(get(m,'a_event'),0);self.assertEqual(get(m,'a_start_tick'),0)
        for i in range(3):T.setv(m,'c_es',3,i)
        T.setv(m,'c_es',1,21);T.setv(m,'e_phase',3,21);m.call('a_postframe');self.assertEqual(m.memory.data[N['c_es']+21],1)
        for mode in (1,2):
            T.enemies(m,0);T.setv(m,'c_es',1,21);T.setv(m,'e_phase',3,21);T.setv(m,'mode',mode);T.setv(m,'a_event',0);m.call('a_postframe');self.assertEqual(get(m,'a_event'),0)

class ExitAndCurveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(MenuTests,'snapshot'):MenuTests.setUpClass()
    def test_eight_sprite_snapshot_restored_and_IRQ_enabled_on_BASIC_exit(self):
        m=MenuTests().machine().game(1)
        snapshot=bytes(m.memory.data[N['p_saved_registers']:N['p_saved_registers']+43])
        offsets=bytes(m.memory.data[N['register_offsets']:N['register_offsets']+43])
        for i in range(8):m.memory.data[N['p_active']+i]=1;m.memory.data[N['p_xpos']+i]=160;m.memory.data[N['p_ypos']+i]=190
        m.call('p_publish');m.frame(0x58);self.assertEqual(m.cpu.pc,0x200)
        for r,v in zip(offsets,snapshot):
            if r in list(range(16))+list(range(0x27,0x2f))+[0x17,0x1b,0x1c,0x1d,0x55,0x5f,0x76,0x77,0x78]:self.assertEqual(m.memory.data[0xd000+r],v,hex(r))
        self.assertEqual(m.memory.data[0xd015],0);self.assertFalse(m.cpu.p&m.cpu.INTERRUPT)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot();self.assertEqual(m.error,0);m.game(3);self.assertEqual(get(m,'number'),3)
    def test_assigned_curves_preserved_for_multiple_levels(self):
        m=MenuTests().machine().game(1);T=OLD.OLD.T
        for level in [1,2,3,29,60,100]:
            m.call('transition',level);self.assertEqual(m.error,0)
            T.enemies(m,0);T.setv(m,'a_ready',1);T.setv(m,'a_start_tick',0)
            if not get(m,'attack_allowed'):continue
            for i in range(m.memory.data[0x7603]):T.setv(m,'c_es',1,i);T.setv(m,'e_phase',3,i)
            assigned=bytes(m.memory.data[N['a_index']:N['a_index']+22])
            for _ in range(64):
                m.call('a_postframe')
                if get(m,'a_event')==1:break
            else:self.fail(('no selection',level))
            chosen=get(m,'a_event_enemy');self.assertEqual(m.memory.data[N['a_index']+chosen],assigned[chosen])
            self.assertEqual(m.memory.data[N['c_es']+chosen],3)


class OriginalEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(MenuTests,'snapshot'):MenuTests.setUpClass()
    def machine(self):return MenuTests().machine().game(1)
    def ready(self,actor=0):
        m=self.machine();T=OLD.OLD.T;T.enemies(m,0)
        for f,v in [('c_es',2),('e_phase',1),('e_visible',1),('e_xlo',90),('e_xhi',0),('e_ylo',70),('e_yhi',0),('a_hidden',0)]:T.setv(m,f,v,actor)
        return m
    def test_all100_plans_nth_across_groups_originalY_and_mode(self):
        m=self.machine();report=json.loads((ART/'fire-parameters.json').read_text())
        for row in report['levels']:
            number=row['level'];m.call('transition',number);self.assertEqual(m.error,0,number)
            self.assertEqual(fget(m,'dy_original'),row['DY_stored_only']);self.assertEqual(fget(m,'mode'),row['mode']);self.assertEqual(fget(m,'nth'),row['every_nth'])
            import struct
            source=(ART/'VYLV.DAT').read_bytes();off,size=struct.unpack_from('<IH',source,8+(number-1)*8);raw=source[off:off+size]
            pos=8;bitmap_offset=12;original_ys=[]
            for group in range(raw[2]):
                count,gx,gy,n=struct.unpack_from('<HhhH',raw,pos);pos+=8;expected=bytearray((n+7)//8);ys=[]
                for t,b in enumerate(raw[pos:pos+n]):
                    gy+=-(b&7) if b&8 else b&7;ys.append(gy)
                    if gy<=148:expected[t//8]|=1<<(t%8)
                self.assertEqual(bytes(m.memory.data[FE['record']+bitmap_offset:FE['record']+bitmap_offset+len(expected)]),bytes(expected),(number,group))
                bitmap_offset+=len(expected);pos+=n;original_ys.append(ys)
            for actor in range(m.memory.data[0x7603]):
                t1=fword(m,'first',actor);t2=fword(m,'second',actor);g=m.memory.data[N['e_group']+actor];n=row['curve_lengths'][g]
                if (actor+1)%row['every_nth']:
                    self.assertEqual((t1,t2),(0,0),(number,actor));continue
                self.assertTrue(row['lower_bounds'][g]<=t1<n,(number,actor,t1))
                self.assertLessEqual(original_ys[g][t1],148,(number,actor,t1))
                # Admission bit comes from original expanded Y, not B2 visible Y.
                bitoff=12+sum((nn+7)//8 for nn in row['curve_lengths'][:g])+t1//8
                self.assertTrue(m.memory.data[FE['record']+bitoff]&(1<<(t1%8)))
                self.assertEqual(t2,(t1+15)%n if row['mode']==2 else 0,(number,actor))
            self.assertEqual(bytes(m.memory.data[FE['pending']:FE['pending']+22]),bytes(22))
    def test_attack_scheduler_and_projectile_math_byte_identical_to_tested_base(self):
        oldn,_=star_symbols((ROOT/'releases/stage_7b4/STAGE7B4.sym').read_text())
        old=(ROOT/'releases/stage_7b4/STAGE7B4.PRG').read_bytes()[2:];new=(ART/'STAGE7B5A.PRG').read_bytes()[2:]
        for start,end in [('a_postframe',0x4fb2),('a_preframe',oldn['a_postframe']),('a_fire_start',oldn['a_fire_count']-5),('p_direction',oldn['p_save_registers']),('p_random_step',oldn['p_enemy_fire'])]:
            a=oldn[start];self.assertEqual(N[start],a,start);self.assertEqual(new[a-0x2001:end-0x2001],old[a-0x2001:end-0x2001],start)
    def test_countdown_word_zero_independent_and_no_retry(self):
        m=self.ready();m.cpu.x=0;fputword(m,'first',257);fputword(m,'second',2)
        for step in range(1,258):
            fcall(m,'entry_tick');self.assertEqual(fword(m,'first'),257-step)
            self.assertEqual(fword(m,'second'),max(0,2-step))
            self.assertEqual(fget(m,'pending'),(2 if step>=2 else 0)|(1 if step==257 else 0))
        fset(m,'pending',0)
        for _ in range(3):fcall(m,'entry_tick')
        self.assertEqual(fget(m,'pending'),0)
    def test_actual_ENTRY_curve_hook_wait_and_B2_offbyone(self):
        m=self.ready();T=OLD.OLD.T;fputword(m,'first',2);fputword(m,'second',0)
        T.setv(m,'c_es',5,0);T.setv(m,'e_phase',0,0);T.setv(m,'e_delay',3,0)
        for _ in range(3):
            m.call('e_objects');self.assertEqual(fword(m,'first'),2);self.assertEqual(fget(m,'pending'),0)
        m.call('e_objects') # spawn is a visible start point, not a packed curve step
        self.assertEqual(m.memory.data[N['e_cursor']],0);self.assertEqual(fword(m,'first'),2)
        m.call('e_objects');self.assertEqual(m.memory.data[N['e_cursor']],1);self.assertEqual(fword(m,'first'),1)
        m.call('e_objects');self.assertEqual(m.memory.data[N['e_cursor']],2);self.assertEqual(fget(m,'pending'),1)
    def test_attack_threshold_formula_and_guard_uses_original_coordinate_basis(self):
        m=self.ready();T=OLD.OLD.T
        for mode in (1,2):
            fset(m,'mode',mode)
            for y in (0,20,100,148,167):
                shifted=y-get(m,'y_shift');T.setv(m,'e_ylo',shifted&255);T.setv(m,'e_yhi',(shifted>>8)&255)
                for _ in range(20):
                    m.cpu.x=0;fcall(m,'attack_plan');t1=fword(m,'first');t2=fword(m,'second')
                    self.assertTrue(y<=t1<168,(y,t1));expected=t1+20
                    if expected>168:expected-=32
                    self.assertEqual(t2,expected if mode==2 else 0)
            for y in (168,178,195,200,300,-1):
                shifted=y-get(m,'y_shift');T.setv(m,'e_ylo',shifted&255);T.setv(m,'e_yhi',(shifted>>8)&255)
                fputword(m,'first',50);fputword(m,'second',60);m.cpu.x=0;fcall(m,'attack_plan')
                self.assertEqual((fword(m,'first'),fword(m,'second')),(0,0))
    def test_attack_thresholds_once_including_second_before_first_and_same_frame(self):
        m=self.ready();T=OLD.OLD.T
        for y,expected in [(137,0),(138,2),(149,2),(150,3),(151,3)]:
            shifted=y-get(m,'y_shift');T.setv(m,'e_ylo',shifted&255);T.setv(m,'e_yhi',(shifted>>8)&255)
            if y==137:fputword(m,'first',150);fputword(m,'second',138)
            m.cpu.x=0;fcall(m,'attack_tick');self.assertEqual(fget(m,'pending'),expected)
        self.assertEqual((fword(m,'first'),fword(m,'second')),(0,0));fset(m,'pending',0);fcall(m,'attack_tick');self.assertEqual(fget(m,'pending'),0)
        fputword(m,'first',1);fputword(m,'second',2);T.setv(m,'e_ylo',(-1-get(m,'y_shift'))&255);T.setv(m,'e_yhi',255);fcall(m,'attack_tick')
        self.assertEqual((fword(m,'first'),fword(m,'second')),(1,2));self.assertEqual(fget(m,'pending'),0)
    def test_six_global_no_owner_cap_and_original_saved_target_speed(self):
        m=self.ready(21)
        for _ in range(3):fset(m,'pending',3,21);m.call('a_fire')
        self.assertEqual(list(m.memory.data[N['p_active']+2:N['p_active']+8]),[1]*6)
        self.assertEqual(list(m.memory.data[N['p_source_enemy']+2:N['p_source_enemy']+8]),[21]*6)
        self.assertEqual(list(m.memory.data[N['p_vy']+2:N['p_vy']+8]),[1]*6)
        self.assertTrue(all(m.memory.data[N['p_target_y']+i]==184 for i in range(2,8)))
    def test_full_pool_consumes_both_events_and_does_not_retry_after_release(self):
        m=self.ready();T=OLD.OLD.T
        for i in range(2,8):T.setv(m,'p_active',1,i)
        fset(m,'pending',3);m.call('a_fire');self.assertEqual(fget(m,'pending'),0)
        m.cpu.x=2;m.call('p_deactivate');m.call('a_fire');self.assertEqual(m.memory.data[N['p_active']+2],0)
        fset(m,'pending',1);m.call('a_fire');self.assertEqual(m.memory.data[N['p_active']+2],1)
    def test_one_slot_two_events_first_spawns_second_expires(self):
        m=self.ready()
        for i in range(2,7):m.memory.data[N['p_active']+i]=1
        fset(m,'pending',3);m.call('a_fire');self.assertEqual(m.memory.data[N['p_active']+7],1);self.assertEqual(fget(m,'pending'),0)
    def test_wait_dead_exploding_hidden_invalid_origins_discard_pending(self):
        T=OLD.OLD.T
        for state,phase,hidden in [(5,0,0),(0,0,0),(4,1,0),(3,4,1)]:
            m=self.ready();T.setv(m,'c_es',state);T.setv(m,'e_phase',phase);T.setv(m,'a_hidden',hidden)
            fset(m,'pending',3);m.call('a_fire');self.assertEqual(fget(m,'pending'),0);self.assertEqual(sum(m.memory.data[N['p_active']+2:N['p_active']+8]),0)
        for y in (-16,168,200):
            m=self.ready();T.setv(m,'e_ylo',y&255);T.setv(m,'e_yhi',(y>>8)&255);fset(m,'pending',3);m.call('a_fire')
            self.assertEqual(sum(m.memory.data[N['p_active']+2:N['p_active']+8]),0)
    def test_event_planning_and_flushing_do_not_consume_attack_RNG(self):
        m=self.ready();before=bytes(m.memory.data[N['p_random_lo']:N['p_random_hi']+1])
        for _ in range(20):m.cpu.x=0;fcall(m,'attack_plan')
        fset(m,'pending',3);m.call('a_fire');self.assertEqual(bytes(m.memory.data[N['p_random_lo']:N['p_random_hi']+1]),before)
    def test_formation_return_do_not_generate_events_and_relaunch_replaces_stale(self):
        m=self.ready();T=OLD.OLD.T
        for state,phase in [(1,3),(2,2)]:
            T.setv(m,'c_es',state);T.setv(m,'e_phase',phase);fputword(m,'first',1);fputword(m,'second',1)
            m.call('e_objects');self.assertEqual((fword(m,'first'),fword(m,'second')),(1,1));self.assertEqual(fget(m,'pending'),0)
        fset(m,'mode',1);T.setv(m,'e_ylo',20);T.setv(m,'e_yhi',0);m.cpu.x=0;m.call('a_start');self.assertEqual(fword(m,'second'),0)
    def test_level_transition_R_and_menu_F1_reinitialize_events(self):
        m=self.ready()
        for number in (54,100,1):
            fset(m,'pending',3,21);m.call('transition',number);self.assertEqual(m.error,0);self.assertEqual(sum(m.memory.data[FE['pending']:FE['pending']+22]),0)
            self.assertEqual(fget(m,'mode'),json.loads((ART/'fire-parameters.json').read_text())['levels'][number-1]['mode'])
        m.memory.data[N['c_ps']]=4;m.frame(0x52);self.assertEqual(get(m,'number'),1);self.assertEqual(fget(m,'mode'),2)

class ChipRAMMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(MenuTests,'snapshot'):MenuTests.setUpClass()
    def test_unmapped_384KB_boundary_drops_writes_reads_FF(self):
        m=MenuTests().machine()
        self.assertEqual(len(m.memory.data),0x60000)
        for a in (0x60000,0x70000,0x7045b,0xfffff):
            m.memory[a]=0x42;self.assertEqual(m.memory[a],0xff)
    def test_live_DMA_never_uses_unmapped_fast_memory_and_file_survives_menu_game(self):
        m=MenuTests.boot
        for src,dst,n in m.memory.base.transfers:
            for address in (src,dst):
                self.assertFalse(address<0x100000 and address+n>0x60000,(hex(src),hex(dst),n))
        raw=(ART/'VYSH.DAT').read_bytes()
        self.assertEqual(bytes(m.memory.data[0xb000:0xb000+len(raw)]),raw)
        game=MenuTests().machine().game(54)
        for level in (100,1,46):
            game.call('transition',level);self.assertEqual(game.error,0)
            self.assertEqual(bytes(game.memory.data[0xb000:0xb000+len(raw)]),raw)

class FireLoaderTests(unittest.TestCase):
    def test_missing_short_extra_bad_sum_header_and_record_CRC_fail_cleanly(self):
        for fault in ('missing','short','extra','sum','header','layout','record'):
            with self.subTest(fault=fault):
                m=Machine();raw=bytearray(m.files['VYSH.DAT'])
                if fault=='missing':del m.files['VYSH.DAT']
                elif fault=='short':m.files['VYSH.DAT']=bytes(raw[:-1])
                elif fault=='extra':m.files['VYSH.DAT']=bytes(raw)+b'\0'
                else:
                    if fault=='sum':raw[-1]^=1
                    elif fault=='header':raw[4]+=1;raw[16]-=1
                    elif fault=='layout':raw[12]+=1;raw[16]-=1
                    else:raw[16]+=1;raw[17]-=1 # same sum16 and same header, invalid record CRC
                    m.files['VYSH.DAT']=bytes(raw)
                m.boot();self.assertEqual(m.cpu.pc,0x200);self.assertNotEqual(m.error,0);self.assertFalse(m.active or m.opened)
                self.assertEqual(m.memory.data[0x1120],0x10);self.assertEqual(m.memory.data[0xd070],m.before[0xd070])

if __name__=='__main__':unittest.main()
