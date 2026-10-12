"""Actual assembled menu/game instructions with narrow CPU/DMA/VIC models, not XEMU."""
import json,unittest
from pathlib import Path
import test_stage5d1a as OLD
import build_stage6b1 as BUILD
ROOT=BUILD.ROOT;ART=ROOT/'releases/stage_6b1'
N=OLD.OLD.T.BUILD.symbols((ART/'STAGE6B1.sym').read_text())
MN=OLD.OLD.T.BUILD.symbols((ART/'MENU_OVERLAY.sym').read_text())
OLD.N=N;OLD.OLD.N=N;OLD.OLD.T.N=N;OLD.OLD.T.PREV.N=N
class MenuMemory(OLD.TitleMemory):
    def __getitem__(self,a):
        if 0x08000000<=a<0x08040000:return self.attic[a-0x08000000]
        if a in (0xd610,0xd619):return (1 if self.key else 0) if a==0xd610 else self.key
        return super().__getitem__(a)
    def __setitem__(self,a,v):
        if 0x08000000<=a<0x08040000:self.attic[a-0x08000000]=v;return
        if a in (0xd610,0xd619):self.key=0;return
        super().__setitem__(a,v)
class Machine(OLD.Machine):
    def __init__(self):
        super().__init__();p=(ART/'STAGE6B1.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.memory.__class__=MenuMemory;self.memory.attic=bytearray(0x40000);self.memory.key=0
        self.files['VYMN.DAT']=(ART/'VYMN.DAT').read_bytes();self.cpu.pc=N['p_startup']
        self.memory.data[0xdc00]=255;self.before=bytes(self.memory.data)
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
        m=self.boot;self.assertEqual(m.error,0);self.assertEqual(m.opened_names,['VYTI.DAT','VYMN.DAT','VYLV.DAT','VYGR.DAT','VYCL.DAT'])
        self.assertEqual(m.closed,5);self.assertFalse(m.opened or m.active)
        self.assertEqual(raster(m),(ART/'original_menu_indices.bin').read_bytes())
        self.assertEqual((get(m,'initial_level'),get(m,'selection')),(1,0))
        for n,a in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000),('VYCL.DAT',0x5c300)]:self.assertEqual(m.memory.data[a:a+len(m.files[n])],m.files[n])
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
    def test_selected_levels_handoff_fonts_and_static_palette(self):
        for level in (1,2,3,99,100):
            m=self.machine().game(level);self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(m.error,0)
            self.assertEqual(get(m,'number'),level);self.assertEqual(get(m,'player1_level'),level)
            self.assertEqual(int.from_bytes(m.memory.data[0x1a04:0x1a08],'little'),0);self.assertEqual(get(m,'player1_lives'),3)
            font=(ART/'menu_font.bin').read_bytes();actual=m.memory.data[0x4000:0x4800]
            self.assertEqual(actual[:0x400],font[:0x400]);self.assertEqual(actual[0x410:],font[0x410:])
            self.assertEqual(list(m.memory.data[N['p_active']:N['p_active']+6]),[0]*6)
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
        OLD.CombatRegression.test_entry_fire_visibility_signed_muzzle_pool_and_fixed_target(self)
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
        m.memory.data[0xdc00]=255;m.call('tick');m.memory.data[0xdc00]=239;m.call('tick');self.assertEqual(get(m,'number'),2)
        m.call('transition',100);T.enemies(m,0);T.setv(m,'a_enabled',0);m.memory.data[0xdc00]=255;m.call('tick');m.call('tick');m.memory.data[0xdc00]=239;m.call('tick');self.assertEqual(get(m,'number'),1)
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
if __name__=='__main__':unittest.main()
