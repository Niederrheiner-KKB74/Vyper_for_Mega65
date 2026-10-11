"""Actual assembled Stage 4b preparation instructions and fetched RRB pixels; not XEMU."""
import unittest
import test_stage3b5c as PREV
import build_stage4b as BUILD
ROOT=PREV.ROOT
ART=ROOT/'releases/stage_4b'
N=BUILD.symbols((ART/'STAGE4B.sym').read_text())
BaseMachine=PREV.Machine
class Machine(BaseMachine):
    def __init__(self):
        super().__init__()
        p=(ART/'STAGE4B.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.cpu.pc=N['p_startup']
        self.before=bytes(self.memory.data)
PREV.Machine=Machine
PREV.N=N
# Keep baseline ART for original explosion source checks (unchanged bytes verified below).
start,call,frame,setv,get=PREV.start,PREV.call,PREV.frame,PREV.setv,PREV.get
enemies,player,shot=PREV.enemies,PREV.player,PREV.shot
EXP_TICKS=PREV.EXP_TICKS

def position(m,x,y):
    for name,value in [('r_x',x),('r_y',y)]:
        m.memory.data[N[name]:N[name]+2]=(value&65535).to_bytes(2,'little')
def signed(m,name):
    v=PREV.word(m,N[name],2)
    return v-65536 if v>=32768 else v

def oracle(x,y,source):
    return {(x+sx,y+sy): (source[sy*8+sx//2]>>(4*(sx%2)))&15
            for sy in range(16) for sx in range(16)
            if 0<=x+sx<240 and 0<=y+sy<200 and (source[sy*8+sx//2]>>(4*(sx%2)))&15}

def fetched(m):
    pixels={}
    for row in range(25):
        count=get(m,'v014_row_count',row)
        assert count<=1,('capacity',row,count)
        if not count:continue
        a=0x5000+row*128+84
        gotox=PREV.word(m,a,2)
        glyph=PREV.word(m,a+2,2)&0x1fff
        native_x=gotox&1023
        assert native_x%2==0
        x=native_x//2
        shift=-((gotox>>13)&7) if gotox&0x1000 else 0
        for ry in range(8):
            for sx in range(16):
                addr=glyph*64+(ry+shift)*8+sx//2
                value=(m.memory.data[addr]>>(4*(sx%2)))&15
                if value:
                    assert 0<=x+sx<240 and 0<=row*8+ry<200,('escaped',x+sx,row*8+ry)
                    pixels[x+sx,row*8+ry]=value
    return pixels

class Regression(PREV.CollisionTests):
    def test_build_baseline_and_disk(self):
        p=(ART/'STAGE4B.PRG').read_bytes();BUILD.verify_engine(p,N)
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE4B.d81').read_bytes(),[('STAGE4B',p,0x82)]+[(n,(ROOT/'assets'/n).read_bytes(),0x81) for n in ('VYLV.DAT','VYGR.DAT')])
    def test_original_conversion_every_pixel_mask_and_guard(self):
        super().test_original_conversion_every_pixel_mask_and_guard()
        old=(PREV.ART/'STAGE3B5C.PRG').read_bytes()[2:]
        p=(ART/'STAGE4B.PRG').read_bytes()[2:]
        self.assertEqual(p[0xc100-0x2001:0xca00-0x2001],old[0xc100-0x2001:])
        self.assertEqual(p[0xca00-0x2001:],bytes(256))

    def test_blink_allows_joystick_blocks_fire_and_pause_does_not_stop_explosion(self):
        m=start();enemies(m);player(m,100,120)
        shot(m,2,108,126);frame(m)
        death=(m.memory.data[0x1662],m.memory.data[0x1664])
        frame(m,0x20)
        for _ in range(EXP_TICKS-1):frame(m)
        self.assertEqual(get(m,'c_ps'),3)
        setv(m,'c_es',0,18)
        for tick in range(149):
            frame(m,buttons=0xeb) # held LEFT + FIRE
            self.assertEqual(m.memory.data[0x1662],max(0,death[0]-tick-1))
            self.assertEqual(m.memory.data[0x1664],death[1])
            self.assertEqual([get(m,'p_active',i) for i in (0,1)],[0,0])
        frame(m,buttons=0xeb)
        self.assertEqual(get(m,'c_ps'),0)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(0,death[1]))
        frame(m,buttons=0xfb);frame(m,buttons=0xef)
        self.assertEqual(get(m,'p_active',0),1)

    def test_full_loader_type15_animation_and_old_motion(self):
        m=start();old=PREV.OLD.start()
        self.assertEqual(get(m,'selected_type'),15);self.assertEqual(get(m,'frame_count'),6)
        for name,base in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000)]:
            p=(ROOT/'assets'/name).read_bytes();self.assertEqual(m.memory.data[base:base+len(p)],p)
        for tick in range(30):
            buttons=(0xfb,0xf7,0xfe,0xfd,0xff)[tick%5]
            frame(m,buttons=buttons);PREV.OLD.frame(old,buttons=buttons)
            for a,b in ((0x1600,0x1660),(0x1678,0x1900),(0x9840,0x98c0),(0xc800,0xca00)):
                self.assertEqual(m.memory.data[a:b],old.memory.data[a:b])
            self.assertEqual(m.memory.data[0x1664],184)

class OffscreenTests(unittest.TestCase):
    def test_signed_rectangle_all_edges_and_extremes(self):
        m=Machine()
        xs=[-32768,-257,-256,-17,-16,*range(-15,1),1,112,224,*range(225,241),255,256,32767]
        ys=[-32768,-257,-16,-1,0,*range(1,17),17,92,184,*range(185,201),255,256,32767]
        for x in xs:
            for y in ys:
                position(m,x,y);call(m,'r_clip')
                width=max(0,min(x+16,240)-max(x,0))
                height=max(0,min(y+16,200)-max(y,0))
                decision=0 if not width or not height else 1 if width==height==16 else 2
                self.assertEqual(get(m,'r_decision'),decision,(x,y))
                self.assertEqual(get(m,'r_width'),width,(x,y))
                self.assertEqual(get(m,'r_height'),height,(x,y))
                if decision:
                    self.assertEqual((get(m,'r_draw_x'),get(m,'r_draw_y')),(max(x,0),max(y,0)))
                    self.assertEqual((get(m,'r_src_x'),get(m,'r_src_y')),(max(-x,0),max(-y,0)))
    def test_actual_rrb_pixels_six_frames_edges_corners_guards_and_hud(self):
        m=start();setv(m,'r_enabled',1)
        types=PREV.OLD.HUD.PREVIOUS.R.DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())
        locations=[(-16,92),(240,92),(112,0),(112,200),(112,0),(224,184),(-257,92),(256,92),(112,-1),(112,256)]
        for n in range(1,16):
            locations += [(-n,92),(240-n,92),(112,0-n),(112,200-n),(-n,0-n),(240-n,200-n),(-n,200-n),(240-n,0-n)]
        protected=[(0x1000,0x1600),(0x9000,0x9840),(0x98c0,0xb800),(0xbf07,0xca40),(0xcac0,0xcb00)]
        screen_before=bytes(m.memory.data[0x5000:0x5c80])
        colour_before=bytes(m.memory.colour[:3200])
        sentinel={a:bytes(m.memory.data[a:b]) for a,b in protected}
        for index,source in enumerate(types[14]['frames']):
            m.memory.data[0x9840:0x98c0]=source
            for x,y in locations:
                position(m,x,y);call(m,'r_render')
                self.assertEqual(fetched(m),oracle(x,y,source),(index,x,y))
                self.assertEqual(get(m,'v014_overflow_count'),0)
                self.assertEqual(m.memory.data[0x9840:0x98c0],source)
                for a,b in protected:self.assertEqual(bytes(m.memory.data[a:b]),sentinel[a],hex(a))
                for row in range(25):
                    off=row*128
                    end=84
                    self.assertEqual(m.memory.data[0x5000+off:0x5000+off+end],screen_before[off:off+end])
                    self.assertEqual(m.memory.colour[off:off+end],colour_before[off:off+end])
                if get(m,'r_decision')==1:
                    rows=[r for r in range(25) if get(m,'v014_row_count',r)]
                    self.assertEqual(PREV.word(m,0x5000+rows[0]*128+86,2)&8191,0x261)
    def test_normal_renderer_uses_new_top_and_bottom_rows(self):
        m=start();PREV.enemies(m);setv(m,'c_ps',2)
        source=bytes(m.memory.data[0x9840:0x98c0])
        for y in (0,15,184,199):
            PREV.target(m,0,1,x=112,y=y)
            call(m,'c_render')
            self.assertEqual(fetched(m),oracle(112,y,source),y)
            self.assertEqual(get(m,'v014_overflow_count'),0)
            self.assertEqual(get(m,'r_enabled'),0)
    def test_private_crop_pixels_transparency_and_odd_nibbles(self):
        m=Machine();source=bytes(((i*13+7)&255) for i in range(128))
        m.memory.data[0x9840:0x98c0]=source
        for x,y in [(-n,0-n) for n in range(1,16)]+[(240-n,200-n) for n in range(1,16)]:
            position(m,x,y);call(m,'r_clip');call(m,'r_crop')
            w,h=get(m,'r_width'),get(m,'r_height')
            sx,sy=get(m,'r_src_x'),get(m,'r_src_y')
            for row in range(16):
                for col in range(16):
                    expected=((source[(row+sy)*8+(col+sx)//2]>>(4*((col+sx)%2)))&15) if row<h and col<w else 0
                    actual=(m.memory.data[0xca40+row*8+col//2]>>(4*(col%2)))&15
                    self.assertEqual(actual,expected,(x,y,row,col))
            self.assertEqual(m.memory.data[0xca00:0xca40],bytes(64));self.assertEqual(m.memory.data[0xcac0:0xcb00],bytes(64))
    def test_path_all_five_directions_signed_continuity_and_loop(self):
        m=Machine();m.memory.data[0x1d00:0x1d40]=bytes(64);setv(m,'r_enabled',1);call(m,'r_begin')
        seen={i:set() for i in range(5)}
        last=None;cycles=0
        for _ in range(2600):
            case=get(m,'r_case');x,y=signed(m,'r_x'),signed(m,'r_y')
            seen[case].add((x,y))
            if last and case==last[0]:
                self.assertLessEqual(abs(x-last[1]),1);self.assertLessEqual(abs(y-last[2]),1)
            if last and last[0]==4 and case==0:cycles+=1
            call(m,'r_clip')
            if (x+16<=0 or x>=240 or y+16<=0 or y>=200):self.assertEqual(get(m,'r_decision'),0)
            last=case,x,y;call(m,'r_objects')
        self.assertGreaterEqual(cycles,2)
        for case,ends in enumerate([[(112,-16),(112,200)],[(112,200),(112,-16)],[(-16,92),(240,92)],[(240,92),(-16,92)],[(-16,-16),(240,240)]]):
            for point in ends:self.assertIn(point,seen[case])
    def test_toggle_pause_next_animation_freeze_resume_and_basic_exit(self):
        m=start();PREV.shot(m,0,120,50)
        frame(m,0x46)
        self.assertEqual(get(m,'r_enabled'),1);self.assertEqual(m.memory.data[0xd015],0)
        game=bytes(m.memory.data[0x1b00:0x1d00]);objects=bytes(m.memory.data[0x1600:0x1900]);score=bytes(m.memory.data[0x1a00:0x1a19])
        for key in (0x54,0x45):
            frame(m,key)
            self.assertEqual(m.memory.data[0x1b00:0x1d00],game)
        frames=set()
        for _ in range(50):
            frame(m,buttons=0xeb);frames.add(get(m,'frame'))
            self.assertEqual(m.memory.data[0x1b00:0x1d00],game)
            self.assertEqual(m.memory.data[0x1600:0x1900],objects)
            self.assertEqual(m.memory.data[0x1a00:0x1a19],score)
        self.assertEqual(frames,set(range(6)))
        frame(m,0x50);xy=signed(m,'r_x'),signed(m,'r_y')
        for _ in range(3):frame(m)
        self.assertEqual((signed(m,'r_x'),signed(m,'r_y')),xy)
        frame(m,0x4e);self.assertEqual(get(m,'r_case'),1)
        frame(m,0x70);self.assertEqual(get(m,'r_paused'),0)
        frame(m,0x66);self.assertEqual(get(m,'r_enabled'),0)
        self.assertNotEqual(m.memory.data[0x1600:0x1900],objects)
        frame(m,0xc6);self.assertEqual(get(m,'r_enabled'),1)
        frame(m,0xd8);self.assertEqual(m.cpu.pc,0x200)
        for a in [0xd054,0xd05a,0xd06c,0xd06d,0xd06e,0xd076,0xd077,0xd078]:self.assertEqual(m.memory.data[a],m.before[a],hex(a))
        self.assertEqual(m.memory.data[0x1000:0x1600],m.before[0x1000:0x1600])
        self.assertEqual(m.memory.colour[:3200],m.before[0xd800:0xe000]+bytes([0xa5])*1152)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.execute()
        for _ in range(300000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('second RUN')
        self.assertEqual(get(m,'r_enabled'),0)
        frame(m,0x58);self.assertEqual(m.cpu.pc,0x200)
    def test_gameover_cannot_enter_test_restart_and_error_stack_unchanged(self):
        m=start();setv(m,'c_ps',4);setv(m,'c_armed',1)
        frame(m,0x46);self.assertEqual(get(m,'r_enabled'),0)
        frame(m,0x52);self.assertEqual(get(m,'c_ps'),0)
        setv(m,'c_ps',4);setv(m,'c_armed',1);setv(m,'anim_paused',1)
        m.memory.data[0x40328]=0
        frame(m,0x52);self.assertEqual(m.cpu.pc,0x200);self.assertNotEqual(m.error,0)
class PlayerTests(unittest.TestCase):
    def test_start_joystick_all_32_combinations_and_horizontal_limits(self):
        m=start()
        self.assertEqual(m.memory.data[0x1662:0x1666],bytes([112,0,184,0]))
        for state in (0,3):
            setv(m,'c_ps',state)
            for mask in range(32):
                for x in (0,1,112,223,224):
                    m.memory.data[0x1662]=x
                    m.memory.data[0xdc00]=0xe0|mask
                    call(m,'c_move')
                    expected=x
                    if not mask&4:expected=max(0,expected-1)
                    if not mask&8:expected=min(224,expected+1)
                    self.assertEqual(m.memory.data[0x1662],expected,(state,mask,x))
                    self.assertEqual(m.memory.data[0x1664],184)
                    self.assertEqual(get(m,'v014_joy_sample'),0xe0|mask)
        for state in (1,2,4):
            setv(m,'c_ps',state);m.memory.data[0x1662]=112
            m.memory.data[0xdc00]=0xe0;call(m,'c_move')
            self.assertEqual(m.memory.data[0x1662:0x1666],bytes([112,0,184,0]))
    def test_shot_origin_hitboxes_death_respawn_and_restart(self):
        m=start();PREV.enemies(m)
        for x in (0,112,224):
            m.memory.data[0x1662]=x
            for i in range(2):setv(m,'p_active',0,i)
            setv(m,'p_fire_latch',0);setv(m,'v014_joy_sample',0xef)
            call(m,'p_player_fire')
            self.assertEqual((get(m,'p_xpos'),get(m,'p_ypos')),(x+8,184))
            call(m,'c_player_box')
            self.assertEqual((get(m,'c_bx'),get(m,'c_by'),get(m,'c_br'),get(m,'c_bb')),(x+2,186,x+14,198))
        m.memory.data[0x1662]=51;PREV.shot(m,2,59,190)
        call(m,'c_collisions')
        self.assertEqual((get(m,'c_px'),get(m,'c_py')),(51,184))
        self.assertEqual(get(m,'c_ps'),1)
        for _ in range(PREV.EXP_TICKS):call(m,'c_timers')
        call(m,'c_wait');self.assertEqual(get(m,'c_ps'),3)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(51,184))
        m.memory.data[0xdc00]=0xfe;call(m,'c_move')
        self.assertEqual(m.memory.data[0x1664],184)
        m.memory.data[0xdc00]=0xfa;call(m,'c_move')
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(50,184))
        setv(m,'c_ps',4);setv(m,'c_armed',1)
        m.cpu.pc=N['main_loop']
        frame(m,0x52)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(112,184))
        self.assertEqual(get(m,'c_ps'),0)
if __name__=='__main__':unittest.main()
