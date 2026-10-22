"""Stage10a4 host checks: respawn window and fire debounce, executed from the built PRG.

Runs the assembled 6502 code of the changed routines with py65 on a flat 64 KB
memory image. This checks the routine logic only; it is not an XEMU or
hardware test.
"""
import os,re,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU

ROOT=Path(__file__).resolve().parents[1]
ART=Path(os.getenv('STAGE10A4_ARTIFACTS',str(ROOT/'releases/stage_10a/stage10a4'))).resolve()

def namespace_labels(text,name):
    start=text.index('.namespace '+name+' {');a=text.index('{',start);depth=1;b=a+1
    while depth:
        depth+={'{':1,'}':-1}.get(text[b],0);b+=1
    return {k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',text[a+1:b-1])}

SYM=(ART/'STAGE10A4.sym').read_text()
G=namespace_labels(SYM,'game');P=namespace_labels(SYM,'shots');H=namespace_labels(SYM,'hud')
TOP={k:int(v,16) for k,v in re.findall(r'^\s*\.label (\w+)=\$([0-9a-f]+)',SYM,re.M)}
PS,BLINK_T,FLASH,VIS,RESPAWN=(G[n] for n in ('c_ps','c_blink','c_flash','c_visible','c_respawn'))
ACTIVE,PLAYER_EXP,WAIT,BLINK=0,1,2,3
RETURN=0xfff0 # sentinel return address (BRK area, never executed)

class Machine:
    def __init__(self):
        prg=(ART/'STAGE10A4.PRG').read_bytes();base=prg[0]|prg[1]<<8
        self.mem=bytearray(65536);self.mem[base:base+len(prg)-2]=prg[2:]
        for a in range(0x1c00,0x1d00):self.mem[a]=0 # c_reset state
        self.mem[P['p_player_slot']]=0x60 # stub shot spawn: RTS, counted by PC
        self.cpu=MPU(memory=self.mem)
    def call(self,addr,a=0,limit=20000):
        c=self.cpu;c.a=a;c.sp=0xff;c.pc=addr
        c.stPushWord(RETURN-1)
        spawned=False
        for _ in range(limit):
            if c.pc==RETURN:return spawned
            if c.pc==P['p_player_slot']:spawned=True
            c.step()
        raise AssertionError('routine did not return')

class RespawnTests(unittest.TestCase):
    def setUp(self):
        self.m=Machine();m=self.m.mem
        m[H['player1_lives']]=2 # lives left after the hit
    def frame(self):
        self.m.call(G['c_timers'])
        self.m.call(G['c_wait_original'])
    def test_window_276_frames_blink_every_20(self):
        m=self.m.mem
        m[PS]=PLAYER_EXP;m[G['c_pf']]=0;m[G['c_pt']]=0
        m[G['c_px']]=97;m[G['c_py']]=184
        states=[];visible=[]
        for f in range(1,300):
            self.frame();states.append(m[PS]);visible.append(m[VIS])
            if m[PS]==ACTIVE:break
        # Explosion 21 frames, then BLINK at once (no wait for the formation).
        self.assertEqual(states[:20],[PLAYER_EXP]*20)
        self.assertEqual(states[20],BLINK)
        self.assertEqual(len(states),276,'protection must end 276 frames after the hit')
        self.assertEqual(m[RESPAWN],0);self.assertEqual(m[VIS],1)
        # Respawn position: the two STA targets after LDA c_px / LDA c_py.
        code=bytes(m[G['c_wait_original']:G['c_wait_original']+40])
        def target(label):
            i=code.index(bytes([0xad,G[label]&255,G[label]>>8]));return code[i+4]|code[i+5]<<8
        self.assertEqual((m[target('c_px')],m[target('c_py')]),(97,184),'respawn at hit position')
        toggles=[i+1 for i in range(21,len(visible)-1) if visible[i]!=visible[i-1]]
        gaps={b-a for a,b in zip(toggles,toggles[1:])}
        self.assertEqual(gaps,{20},'visibility must toggle every 20 frames')
        self.assertEqual(toggles[0],21+15,'first toggle when the timer reaches 240')
    def test_no_fire_and_no_attack_during_respawn(self):
        m=self.m.mem;m[PS]=WAIT;self.m.call(G['c_wait_original'])
        self.assertEqual((m[PS],m[BLINK_T],m[FLASH],m[RESPAWN]),(BLINK,255,15,1))
        self.m.call(G['respawn_fire_state'])
        self.assertFalse(self.m.cpu.p&0x02,'Z=0: fire blocked')
        self.m.call(G['respawn_attack_blocked'])
        self.assertTrue(self.m.cpu.p&0x01,'C=1: attack blocked')
    def test_turn_resume_blink_still_fires_and_attacks(self):
        m=self.m.mem;m[PS]=BLINK;m[RESPAWN]=0
        self.m.call(G['respawn_fire_state']);self.assertTrue(self.m.cpu.p&0x02)
        self.m.call(G['respawn_attack_blocked']);self.assertFalse(self.m.cpu.p&0x01)
    def test_active_and_exploding(self):
        m=self.m.mem
        for ps,fire,attack in ((ACTIVE,True,False),(PLAYER_EXP,False,True),(WAIT,False,True)):
            m[PS]=ps;m[RESPAWN]=0
            self.m.call(G['respawn_fire_state']);self.assertEqual(bool(self.m.cpu.p&0x02),fire,ps)
            self.m.call(G['respawn_attack_blocked']);self.assertEqual(bool(self.m.cpu.p&0x01),attack,ps)

class FireDebounceTests(unittest.TestCase):
    def setUp(self):
        self.m=Machine();self.m.mem[P['p_fire_latch']]=0
    def sample(self,pressed):
        self.m.mem[TOP['v014_joy_sample']]=0xef if pressed else 0xff
        return self.m.call(P['p_player_fire'])
    def run_pattern(self,pattern):
        return [self.sample(c=='#') for c in pattern]
    def test_hold_fires_once(self):
        self.assertEqual(sum(self.run_pattern('#'*30)),1)
    def test_single_released_frame_bounce_is_ignored(self):
        shots=self.run_pattern('###.###.#.##')
        self.assertEqual(sum(shots),1,'one-frame release (contact bounce) must not re-arm')
    def test_two_released_frames_rearm(self):
        shots=self.run_pattern('##..#')
        self.assertEqual(shots,[True,False,False,False,True])
    def test_external_block_needs_release(self):
        self.m.mem[P['p_fire_latch']]=1 # set during respawn/get ready
        self.assertEqual(self.run_pattern('###..#'),[False]*5+[True])

if __name__=='__main__':unittest.main()
