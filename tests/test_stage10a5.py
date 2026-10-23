"""Stage10a5 host checks on the built programs (py65, flat 64 KB; not XEMU/hardware).

- menu: arming and fire need two consecutive released frames
- highscore table: once-per-frame joystick, two released frames before fire exits
- new game: level transition before Get ready; two-player resume unchanged
"""
import os,re,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU

ROOT=Path(__file__).resolve().parents[1]
ART=Path(os.getenv('STAGE10A5_ARTIFACTS',str(ROOT/'releases/stage_10a/stage10a5'))).resolve()
RETURN=0xfff0

def labels(text):return {k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',text)}
def namespace(text,name):
    start=text.index('.namespace '+name+' {');a=text.index('{',start);depth=1;b=a+1
    while depth:
        depth+={'{':1,'}':-1}.get(text[b],0);b+=1
    return labels(text[a+1:b-1])

class Flat:
    def __init__(self,prg,skip=0,base=None):
        self.mem=bytearray(65536)
        data=prg[2+skip:];base=base if base is not None else (prg[0]|prg[1]<<8)+skip
        self.mem[base:base+len(data)]=data
        self.cpu=MPU(memory=self.mem)
    def call(self,addr,stops=(),limit=200000):
        c=self.cpu;c.sp=0xff;c.pc=addr;c.stPushWord(RETURN-1)
        for _ in range(limit):
            if c.pc==RETURN or c.pc in stops:return c.pc
            c.step()
        raise AssertionError('routine did not return')

class MenuTests(unittest.TestCase):
    S=labels((ART/'MENU_OVERLAY.sym').read_text())
    def setUp(self):
        self.m=Flat((ART/'MENU_OVERLAY.PRG').read_bytes());m=self.m.mem
        for n in ('menu_ready','fire_armed','start_pending','key_timer','key_previous','previous_joy'):m[self.S[n]]=0
        m[0xd610]=0 # empty keyboard queue
    def frame(self,fire,keys_released=True):
        m=self.m.mem;m[0xd613]=0xff if keys_released else 0x00
        m[0xdc00]=0xef if fire else 0xff
        return self.m.call(self.S['menu_input'],stops=(self.S['confirm'],))==self.S['confirm']
    def run_pattern(self,p):return [self.frame(c=='#') for c in p]
    def test_held_fire_from_highscore_never_confirms(self):
        self.assertEqual(sum(self.run_pattern('#'*20)),0)
    def test_single_released_frame_does_not_arm(self):
        self.assertEqual(sum(self.run_pattern('####.###.#.##')),0)
    def test_two_released_frames_arm_and_two_more_rearm_fire(self):
        # 2 frames arm the menu, the fire counter then needs 2 released frames.
        self.assertEqual(self.run_pattern('##....#'),[False]*6+[True])
    def test_bounce_after_arming_is_ignored(self):
        self.run_pattern('....')
        self.assertEqual(sum(self.run_pattern('#.#.#')),1)

class HighscoreTests(unittest.TestCase):
    S=labels((ART/'highscore.sym').read_text())
    def setUp(self):
        prg=(ART/'HIGHSCORE.PRG').read_bytes()
        self.m=Flat(prg,skip=0xff);m=self.m.mem
        for n in ('quit','fire_armed','hi_mode','joy_held'):m[self.S[n]]=0
        m[self.S['hs_open_armed']]=1
        for n in ('page_left','page_right'):m[self.S[n]]=0x60
    def frame(self,fire):
        self.m.mem[0xdc00]=0xef if fire else 0xff
        self.m.call(self.S['joy_frame'])
        return bool(self.m.mem[self.S['quit']])
    def test_loop_no_longer_reads_fire(self):
        code=bytes(self.m.mem[self.S['input_tick']:self.S['joy_frame']])
        self.assertNotIn(bytes([0xad,0x00,0xdc]),code,'free-running loop must not sample $DC00')
    def test_arriving_with_fire_held_and_bounce(self):
        self.assertFalse(any(self.frame(c=='#') for c in '####.###.#'))
    def test_two_released_frames_then_press_exits(self):
        self.assertEqual([self.frame(c=='#') for c in '..#'],[False,False,True])

class FirstLevelTests(unittest.TestCase):
    SYM=(ART/'STAGE10A5.sym').read_text()
    I=namespace(SYM,'integration');T=namespace(SYM,'twop');TF=namespace(SYM,'transitionfx')
    GR=namespace(SYM,'getready');LV=namespace(SYM,'level')
    def setUp(self):
        self.m=Flat((ART/'STAGE10A5.PRG').read_bytes());m=self.m.mem
        self.stubs={self.T['ready']:'ready',self.GR['gr_begin']:'get_ready',self.TF['begin']:'transition',
                    self.LV['transition']:'level_load',self.GR['gr_completed']:'completed'}
        for a in self.stubs:m[a]=0x60
    def trace(self,addr):
        c=self.m.cpu;c.sp=0xff;c.pc=addr;c.stPushWord(RETURN-1);seen=[]
        for _ in range(10000):
            if c.pc==RETURN:return seen
            if c.pc in self.stubs:seen.append(self.stubs[c.pc])
            c.step()
        raise AssertionError('no return')
    def start(self,resuming):
        m=self.m.mem;m[self.T['resuming']]=resuming;m[self.LV['number']]=7
        return self.trace(self.I['first_ready'])+self.trace(self.I['first_start'])
    def test_new_game_plays_transition_for_the_selected_level(self):
        self.assertEqual(self.start(0),['ready','transition'])
        self.assertEqual(self.m.mem[self.TF['next_level']],7)
        self.assertEqual(self.trace(self.I['first_finish']),['level_load'])
        self.assertEqual(self.m.mem[self.I['first_pending']],0)
        self.assertEqual(self.trace(self.I['first_finish']),['completed'],'later levels use the normal gate')
    def test_two_player_resume_keeps_direct_get_ready(self):
        self.assertEqual(self.start(1),['ready','get_ready'])
        self.assertEqual(self.trace(self.I['first_finish']),['completed'])
    def test_finish_jumps_to_first_finish(self):
        code=bytes(self.m.mem[self.TF['finish']:self.TF['finish']+40])
        t=self.I['first_finish'];self.assertIn(bytes([0x4c,t&255,t>>8]),code)

if __name__=='__main__':unittest.main()
