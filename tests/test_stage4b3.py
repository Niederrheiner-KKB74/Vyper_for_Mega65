"""Actual assembled Stage 4b-3 entry instructions and fetched RRB pixels; not XEMU."""
import unittest
from pathlib import Path
import test_stage3b5c as PREV
import build_stage4b3 as BUILD
ROOT=PREV.ROOT
ART=ROOT/'releases/stage_4b_3'
N=BUILD.symbols((ART/'STAGE4B3.sym').read_text())
class EntryMemory(PREV.OLD.HUD.Memory):
    def __getitem__(self,a):
        if getattr(self,'sys_map',False) and not getattr(self,'linear',False) and 0xa000<=a<0xd000:
            mask=0x10 if a<0xc000 else 0x20
            if self.data[0xd030]&mask:
                self.rom_overlay_reads.append(a)
                return self.data[0x20000+a] # XEMU BANK_POLICY_ROM: read ROM, write underlying RAM
        if getattr(self,'sys_map',False) and not getattr(self,'linear',False) and 0xe000<=a<=0xffff:
            return self.data[0x30000+a]
        return super().__getitem__(a)
    def __setitem__(self,a,v):
        if getattr(self,'sys_map',False) and not getattr(self,'linear',False) and 0xe000<=a<=0xffff:
            self.map_rom_writes.append((a,v))
            return # SYS MAP to protected bank-3 KERNAL; VIC still fetches bank 0.
        pointer=self.data[0xd701]*256+v if a==0xd705 else -1
        names=['font_dma','colour_backup_dma','colour_restore_dma','clear_dma','e_save_dma','e_restore_dma','e_copy_dma','e_screen_dma']
        if pointer in [N[k] for k in names]:
            self.data[a]=v
            p=pointer;src_mb=dst_mb=0
            while self.data[p]:
                opt=self.data[p];p+=1
                if opt in (0x80,0x81):
                    if opt==0x80:src_mb=self.data[p]
                    else:dst_mb=self.data[p]
                    p+=1
                else:assert opt==0x0a
            p+=1;d=self.data[p:p+11]
            assert d[0]==0 and d[9:11]==bytes(2)
            n=int.from_bytes(d[1:3],'little')
            src=int.from_bytes(d[3:6],'little')+(src_mb<<20)
            dst=int.from_bytes(d[6:9],'little')+(dst_mb<<20)
            previous_linear=getattr(self,'linear',False)
            self.linear=True # DMA uses physical addresses, never CPU MAP.
            try:
                payload=self.char_wom[src-0xff7e000:src-0xff7e000+n] if 0xff7e000<=src<0xff80000 else bytes(self[src+i] for i in range(n))
                for i,b in enumerate(payload):self[dst+i]=b
            finally:self.linear=previous_linear
            self.base.transfers.append((src,dst,n));return
        super().__setitem__(a,v)
class MappedCPU(PREV.OLD.HUD.CPU):
    def step(self):
        linear=self.eom and self.memory[self.pc]==0x92
        self.memory.linear=linear
        try:return super().step()
        finally:self.memory.linear=False
BaseMachine=PREV.Machine
class Machine(BaseMachine):
    def __init__(self):
        super().__init__()
        p=(ART/'STAGE4B3.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.memory.__class__=EntryMemory
        self.memory.sys_map=True
        self.memory.map_rom_writes=[]
        self.memory.rom_overlay_reads=[]
        self.cpu.__class__=MappedCPU
        self.cpu.pc=N['p_startup']
        self.before=bytes(self.memory.data)
PREV.Machine=Machine
PREV.N=N
# Keep baseline ART for original explosion source checks (unchanged bytes verified below).
call,setv,get=PREV.call,PREV.setv,PREV.get
def frame(m,key=0,buttons=255):
    m.memory.data[0xdc00]=buttons
    sampled=False
    for _ in range(800000): # R redraws 4800 bytes using mapping-safe stores.
        if m.cpu.pc==0x200 or sampled and m.cpu.pc==N['main_loop']:return
        if m.cpu.pc==0xffe4:
            sampled=True;m.cpu.a=key;m.cpu.pc=m.cpu.stPopWord()+1
        else:m.cpu.step()
    raise AssertionError('frame or R redraw did not return')
PREV.frame=frame
def start():
    m=Machine().execute()
    assert m.error==0
    for _ in range(800000):
        if m.cpu.pc==N['main_loop']:
            setv(m,'a_enabled',0) # baseline regressions isolate unchanged entry/combat
            return m
        m.cpu.step()
    raise AssertionError('boot')
PREV.start=start
enemies,player,shot=PREV.enemies,PREV.player,PREV.shot
EXP_TICKS=PREV.EXP_TICKS
word=PREV.word
OLD=PREV.OLD
os=PREV.os
_original_target=PREV.target
def target(m,i=0,state=1,x=90,y=90):
    _original_target(m,i,state,x,y)
    if i<22:
        for name,value in [('e_xlo',x),('e_xhi',0),('e_ylo',y),('e_yhi',0),('e_phase',3)]:setv(m,name,value,i)
PREV.target=target

target=PREV.target

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
        count=get(m,'v014_row_count',row);assert count<=24
        for slot in range(count):
            a=0xe000+row*192+84+slot*4
            gotox=PREV.word(m,a,2);glyph=PREV.word(m,a+2,2)&8191
            x=(gotox&1023)//2;shift=-((gotox>>13)&7) if gotox&0x1000 else 0
            for ry in range(8):
                for sx in range(16):
                    addr=glyph*64+(ry+shift)*8+sx//2
                    v=(m.memory.data[addr]>>(4*(sx%2)))&15
                    if v:
                        assert 0<=x+sx<240 and 0<=row*8+ry<200
                        pixels[x+sx,row*8+ry]=v
    return pixels

class Regression(PREV.CollisionTests):
    def test_build_baseline_and_disk(self):
        p=(ART/'STAGE4B3.PRG').read_bytes();BUILD.verify_engine(p,N)
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE4B3.d81').read_bytes(),[('STAGE4B3',p,0x82)]+[(n,(ROOT/'assets'/n).read_bytes(),0x81) for n in ('VYLV.DAT','VYGR.DAT')])
    def test_original_conversion_every_pixel_mask_and_guard(self):
        super().test_original_conversion_every_pixel_mask_and_guard()
        old=(PREV.ART/'STAGE3B5C.PRG').read_bytes()[2:]
        p=(ART/'STAGE4B3.PRG').read_bytes()[2:]
        self.assertEqual(p[0xc100-0x2001:0xca00-0x2001],old[0xc100-0x2001:])
        self.assertEqual(p[0xca00-0x2001:0xcb00-0x2001],bytes(256))

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
        m=start()
        self.assertEqual(get(m,'selected_type'),15);self.assertEqual(get(m,'frame_count'),6)
        for name,base in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000)]:
            p=(ROOT/'assets'/name).read_bytes();self.assertEqual(m.memory.data[base:base+len(p)],p)
        self.assertEqual(m.memory.data[N['c_es']:N['c_es']+22],bytes([5])*22)
        self.assertEqual(get(m,'c_es',22),0)
        self.assertEqual(get(m,'p_test_enabled'),0)
        for tick in range(30):
            frame(m,buttons=(0xfb,0xf7,0xfe,0xfd,0xff)[tick%5])
            self.assertEqual(m.memory.data[0x1664],184)
            self.assertEqual(get(m,'v014_overflow_count'),0)

    def test_gameover_wait_restart_highscore_exit_repeated(self):
        m=start();enemies(m);player(m)
        m.memory.data[0x1a00:0x1a04]=(12345678).to_bytes(4,'little')
        for repeat in range(3):
            enemies(m);player(m)
            m.memory.data[0x1a0a:0x1a0c]=bytes([1,0])
            shot(m,2);frame(m)
            self.assertEqual(get(m,'c_ps'),1)
            for _ in range(EXP_TICKS-1):frame(m)
            self.assertEqual(get(m,'c_ps'),1)
            frame(m);self.assertEqual(get(m,'c_ps'),4)
            screen=bytes(m.memory.data[0xe000:0xf2c0]);colour=bytes(m.memory.colour[:4800])
            for row,text in [(9,[7,1,13,5,32,15,22,5,18]),(11,[18,32,45,32,18,5,19,20,1,18,20]),(13,[24,32,45,32,5,24,9,20])]:
                off=row*192+84
                self.assertEqual(list(screen[off+2:off+2+2*len(text):2]),text)
                self.assertEqual(colour[off:off+2],bytes([0x10,0]))
                self.assertEqual(colour[off+2:off+2+2*len(text)],bytes([0,2])*len(text))
                self.assertEqual(screen[off+2+2*len(text):off+6+2*len(text)],bytes([0x80,2,0,2]))
                self.assertEqual(colour[off+2+2*len(text):off+6+2*len(text)],bytes([0x10,0,8,0]))
            self.assertEqual(m.memory.data[0xd015],0)
            for key in [0x52,0x20,0x2b,0x54,0x45]:frame(m,key)
            self.assertEqual(get(m,'c_ps'),4);self.assertEqual(bytes(m.memory.data[0xe000:0xf2c0]),screen)
            self.assertEqual(bytes(m.memory.colour[:4800]),colour)
            m.memory.data[0xd613]=0xfd;frame(m);frame(m,0x52)
            self.assertEqual(get(m,'c_ps'),4)
            m.memory.data[0xd613]=255;frame(m)
            frame(m,0x72)
            self.assertEqual(get(m,'c_ps'),0);self.assertEqual(word(m,0x1a00),12345678)
            self.assertEqual(word(m,0x1a04),0);self.assertEqual(word(m,0x1a08,2),1)
            self.assertEqual(word(m,0x1a0a,2),3)
            self.assertEqual(get(m,'selected_type'),15);self.assertEqual(get(m,'frame_count'),6)
        frame(m,0x78);self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(m.memory.data[0xd05a],m.before[0xd05a])
        self.assertEqual(m.memory.data[0xd015],0)
        self.assertEqual(m.memory.data[0x1000:0x1600],m.before[0x1000:0x1600])
        self.assertEqual(m.memory.colour[:4800],m.before[0xd800:0xe000]+bytes([0xa5])*2752)

    def test_gameover_x_and_second_run_restore_original_registers(self):
        m=start();setv(m,'c_ps',4);setv(m,'anim_paused',1)
        frame(m,0xd8);self.assertEqual(m.cpu.pc,0x200)
        for a in list(range(0xd000,0xd011))+list(range(0xd027,0xd02d))+[0xd04d,0xd04f,0xd054,0xd05a,0xd06c,0xd06d,0xd06e,0xd076,0xd077,0xd078]:
            self.assertEqual(m.memory.data[a],m.before[a],hex(a))
        rom=os.environ.get('MEGA65_ROM')
        if rom:
            data=Path(rom).read_bytes()
            self.assertEqual(OLD.HUD.EXIT.hashlib.sha256(data).hexdigest(),OLD.HUD.EXIT.ROM_SHA)
            for a,v in {0x111f:0,0x1120:0,0x1121:0x20,0x1122:1,0x1123:0}.items():m.memory.data[a]=v
            OLD.HUD.EXIT.blink(m,data)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.execute()
        for _ in range(800000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('second RUN')
        self.assertEqual(get(m,'c_ps'),0);self.assertEqual(word(m,0x1a0a,2),3)
        frame(m,0x58);self.assertEqual(m.cpu.pc,0x200)

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
        screen_before=bytes(m.memory.data[0xe000:0xf2c0])
        colour_before=bytes(m.memory.colour[:4800])
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
                    off=row*192
                    end=84
                    self.assertEqual(m.memory.data[0xe000+off:0xe000+off+end],screen_before[off:off+end])
                    self.assertEqual(m.memory.colour[off:off+end],colour_before[off:off+end])
                if get(m,'r_decision')==1:
                    rows=[r for r in range(25) if get(m,'v014_row_count',r)]
                    self.assertEqual(PREV.word(m,0xe000+rows[0]*192+86,2)&8191,0x261)
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
        before_tick=get(m,'e_ticklo')
        frame(m,0x66);self.assertEqual(get(m,'r_enabled'),0)
        self.assertNotEqual(get(m,'e_ticklo'),before_tick)
        frame(m,0xc6);self.assertEqual(get(m,'r_enabled'),1)
        frame(m,0xd8);self.assertEqual(m.cpu.pc,0x200)
        for a in [0xd054,0xd05a,0xd06c,0xd06d,0xd06e,0xd076,0xd077,0xd078]:self.assertEqual(m.memory.data[a],m.before[a],hex(a))
        self.assertEqual(m.memory.data[0x1000:0x1600],m.before[0x1000:0x1600])
        self.assertEqual(m.memory.colour[:4800],m.before[0xd800:0xe000]+bytes([0xa5])*2752)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.execute()
        for _ in range(800000):
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
class EntryTests(unittest.TestCase):
    def test_sys_map_bank3_screen_long_stores_and_register_preservation(self):
        m=start()
        kernel=bytes(m.memory.data[0x3e000:0x40000])
        self.assertFalse(m.memory.map_rom_writes)
        m.memory[0xe000]=0x77
        self.assertNotEqual(m.memory.data[0xe000],0x77)
        m.memory.map_rom_writes.clear()
        before=bytes(m.memory.data[0xe000:0xf2c0])
        self.assertNotEqual(before,bytes([0xa5])*4800)
        m.cpu.a=0x7a;m.cpu.x=0x39;m.cpu.y=3;m.cpu.b=0;m.cpu.z=0x5d
        flags=m.cpu.p
        m.memory.data[0x1a6c:0x1a70]=(0xe000).to_bytes(4,'little')
        call(m,'long_screen_store')
        self.assertEqual(m.memory.data[0xe003],0x7a)
        self.assertEqual((m.cpu.a,m.cpu.x,m.cpu.y,m.cpu.b,m.cpu.z,m.cpu.p),(0x7a,0x39,3,0,0x5d,flags))
        m.cpu.pc=N['main_loop']
        for _ in range(30):frame(m)
        self.assertTrue(fetched(m))
        self.assertFalse(m.memory.map_rom_writes)
        self.assertEqual(bytes(m.memory.data[0x3e000:0x40000]),kernel)
        self.assertEqual(bytes(m.memory.data[0xd060:0xd063]),bytes([0,0xe0,0]))

    def test_dma_retirement_valid_empty_lists_cpu_budget_and_unchanged_hud(self):
        m=start()
        prefix=[bytes(m.memory.data[0xe000+r*192:0xe000+r*192+84]) for r in range(25)]
        cpu_cost=[]
        for live in (False,True):
            for i in range(22):
                setv(m,'c_es',1 if live else 0,i)
                setv(m,'e_xlo',get(m,'e_tx',i),i);setv(m,'e_ylo',get(m,'e_ty',i),i)
                setv(m,'e_xhi',0,i);setv(m,'e_yhi',0,i)
            m.memory.base.transfers.clear()
            before=m.cpu.processorCycles
            call(m,'e_render')
            cpu_cost.append(m.cpu.processorCycles-before)
            copies=[x for x in m.memory.base.transfers if 0xe000<=x[1]<0xf2c0]
            self.assertEqual(len(copies),25)
            self.assertTrue(all(n==100 for _,_,n in copies))
            self.assertEqual(get(m,'v014_overflow_count'),0)
            for r in range(25):
                self.assertEqual(bytes(m.memory.data[0xe000+r*192:0xe000+r*192+84]),prefix[r])
                off=84+4*get(m,'v014_row_count',r)
                remaining=(184-off)//4
                self.assertEqual(bytes(m.memory.data[0xe000+r*192+off:0xe000+r*192+184]),bytes([0x80,2,0,2])*remaining)
                self.assertEqual(bytes(m.memory.colour[r*192+off:r*192+184]),bytes([0x10,0,8,0])*remaining)
            self.assertFalse(m.memory.map_rom_writes)
        self.assertLess(cpu_cost[1],110000) # Narrow CPU model; old 327427, not hardware timing.
        self.assertLess(cpu_cost[0],40000)

    def test_decoder_all_bytes_and_byte_exact_curves(self):
        import analyze_stage3b2_data as data
        parsed=data.parse_level_record(data.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1])
        m=start()
        for b in range(16):
            m.cpu.a=b;call(m,'e_decode')
            self.assertEqual(m.cpu.a,((- (b&7) if b&8 else b)&255))
        for group,g in enumerate(parsed['groups']):
            ptr=get(m,'e_gptrlo',group)+256*get(m,'e_gptrhi',group)
            self.assertEqual(m.memory.data[ptr:ptr+get(m,'e_glen',group)],bytes.fromhex(g['curve_hex']))
            self.assertEqual((get(m,'e_gxlo',group),get(m,'e_gylo',group)),(g['start_x'],g['start_y']))
    def test_full_two_parallel_groups_exact_steps_targets_and_rrb_capacity(self):
        import analyze_stage3b2_data as data
        p=data.parse_level_record(data.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1])
        m=start();model=[{'state':5,'x':0,'y':0,'cursor':0,'phase':0,'delay':16*(i%11)} for i in range(22)]
        prefix=[bytes(m.memory.data[0xe000+r*192:0xe000+r*192+84]) for r in range(25)]
        maxrows=0
        for tick in range(500):
            call(m,'e_objects')
            for i,a in enumerate(model):
                g=p['groups'][i//11];curve=bytes.fromhex(g['curve_hex']);target=p['enemies'][i]
                if a['state']==5:
                    if a['delay']:a['delay']-=1
                    else:a.update(state=2,x=g['start_x'],y=g['start_y'],phase=1)
                elif a['phase']==1:
                    b=curve[a['cursor']];a['x']+=-((b>>4)&7) if b&128 else (b>>4)&7;a['y']+=-(b&7) if b&8 else b&7
                    a['cursor']+=1
                    if a['cursor']==len(curve):a['phase']=2
                elif a['phase']==2:
                    tx,ty=target['formation_x'],target['formation_y']-25
                    a['x']+=(tx>a['x'])-(tx<a['x']);a['y']+=(ty>a['y'])-(ty<a['y'])
                    if (a['x'],a['y'])==(tx,ty):a.update(state=1,phase=3)
                self.assertEqual((get(m,'c_es',i),get(m,'e_phase',i),get(m,'e_cursor',i)),(a['state'],a['phase'],a['cursor']),(tick,i))
                x=get(m,'e_xlo',i)+256*get(m,'e_xhi',i);y=get(m,'e_ylo',i)+256*get(m,'e_yhi',i)
                x=x-65536 if x>=32768 else x;y=y-65536 if y>=32768 else y
                self.assertEqual((x,y),(a['x'],a['y']),(tick,i))
            if tick%8==0 or tick in (235,236,237):
                call(m,'e_render')
                self.assertEqual(get(m,'v014_overflow_count'),0)
                rows=list(m.memory.data[N['v014_row_count']:N['v014_row_count']+25]);maxrows=max(maxrows,max(rows))
                for r in range(25):
                    self.assertEqual(m.memory.data[0xe000+r*192:0xe000+r*192+84],prefix[r])
                    at=0xe000+r*192+84+4*rows[r]
                    self.assertEqual(m.memory.data[at:at+4],bytes([0x80,2,0,2]))
                    self.assertEqual(m.memory.data[0xe000+r*192+184:0xe000+(r+1)*192],bytes([0x80,2])*4)
        # Moving all targets up changes their character-row alignment.
        self.assertEqual(maxrows,8);self.assertLessEqual(maxrows,24)
        self.assertEqual([a['state'] for a in model],[1]*22)
        self.assertEqual(get(m,'c_es',22),0)
    def test_visibility_starts_only_at_first_movement_all_slots(self):
        m=start()
        for tick in range(1,186):
            call(m,'e_objects')
            for i in range(22):
                first=2+16*(i%11)+(7 if i>=11 else 0)
                self.assertEqual(get(m,'e_visible',i),int(tick>=first),(tick,i))
                m.cpu.x=i;call(m,'e_is_visible')
                self.assertEqual(m.cpu.a,int(tick>=first),(tick,i))
        call(m,'e_init')
        self.assertEqual([get(m,'e_visible',i) for i in range(23)],[0]*23)

    def test_fetched_pixels_no_stationary_start_or_stale_entries(self):
        m=start();setv(m,'c_ps',2)
        source=bytes(m.memory.data[0x9840:0x98c0])
        for tick in range(1,10):
            call(m,'e_objects');call(m,'e_render')
            expected={}
            for i in (0,11):
                if get(m,'e_visible',i):
                    expected.update(oracle(get(m,'e_xlo',i),get(m,'e_ylo',i),source))
            self.assertEqual(fetched(m),expected,tick)
            self.assertEqual(get(m,'v014_overflow_count'),0)
        setv(m,'e_visible',0,11);call(m,'e_render')
        self.assertEqual(fetched(m),oracle(get(m,'e_xlo'),get(m,'e_ylo'),source))

    def test_hidden_wait_and_entry_cannot_hit_player_or_projectile(self):
        for state in (5,2):
            m=start();enemies(m);target(m,0,state=state,x=90,y=90)
            setv(m,'e_phase',1);setv(m,'e_visible',0)
            shot(m,0,98,94);call(m,'c_collisions')
            self.assertEqual(get(m,'c_es'),state)
            self.assertEqual(get(m,'p_active'),1)
            self.assertEqual(word(m,0x1a04),0)
            setv(m,'p_active',0);player(m,90,90)
            before=word(m,0x1a0a,2);call(m,'c_collisions')
            self.assertEqual(get(m,'c_ps'),0)
            self.assertEqual(word(m,0x1a0a,2),before)
        setv(m,'e_visible',1);shot(m,0,98,94);call(m,'c_collisions')
        self.assertEqual(get(m,'c_es'),4)
        self.assertEqual(word(m,0x1a04),175)

    def test_entry_hit_dead_gap_wait_and_restart_no_recreation(self):
        m=start();call(m,'e_objects');call(m,'e_objects')
        x,y=get(m,'e_xlo'),get(m,'e_ylo')
        PREV.shot(m,0,x+8,y+4);call(m,'c_collisions')
        self.assertEqual(get(m,'c_es'),4);self.assertEqual(word(m,0x1a04),175)
        for _ in range(EXP_TICKS):call(m,'c_timers');call(m,'e_objects')
        self.assertEqual(get(m,'c_es'),0)
        for _ in range(450):call(m,'e_objects')
        self.assertEqual(get(m,'c_es'),0)
        self.assertEqual([get(m,'c_es',i) for i in range(1,22)],[1]*21)
        setv(m,'c_ps',2);call(m,'c_wait');self.assertEqual(get(m,'c_ps'),3)
        setv(m,'c_ps',4);setv(m,'c_armed',1);m.cpu.pc=N['main_loop'];frame(m,0x52)
        self.assertEqual(get(m,'c_es'),2);self.assertEqual(get(m,'c_es',1),5)
        self.assertEqual(word(m,0x1a04),0)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(112,184))
    def test_independent_crops_explosions_negative_boxes_and_system_memory(self):
        m=start();PREV.enemies(m);setv(m,'c_ps',2)
        source=bytes(m.memory.data[0x9840:0x98c0]);expected={}
        locations=[(-9,-3),(232,195),(40,190)]
        for i,(x,y) in enumerate(locations):
            PREV.target(m,i,2,x=x&255,y=y&255)
            setv(m,'e_xhi',255 if x<0 else 0,i);setv(m,'e_yhi',255 if y<0 else 0,i)
            expected.update(oracle(x,y,source))
        kernel=bytes(m.memory.data[0x1000:0x1600]);backup=bytes(m.memory.data[0x5000:0x5640])
        call(m,'e_render');self.assertEqual(fetched(m),expected)
        for i in range(3):
            self.assertEqual(m.memory.data[0x10000+i*256:0x10040+i*256],bytes(64))
            self.assertEqual(m.memory.data[0x100c0+i*256:0x10100+i*256],bytes(64))
        self.assertNotEqual(m.memory.data[0x10040:0x100c0],m.memory.data[0x10140:0x101c0])
        self.assertEqual(m.memory.data[0x9840:0x98c0],source)
        self.assertEqual(m.memory.data[0x5000:0x5640],backup);self.assertEqual(m.memory.data[0x1000:0x1600],kernel)
        m.cpu.x=0;call(m,'e_collision_box')
        self.assertEqual((get(m,'c_bx'),get(m,'c_by'),get(m,'c_br'),get(m,'c_bb')),(0,0,5,11))
        setv(m,'c_es',4);setv(m,'c_ef',0);call(m,'e_render')
        exp=(ROOT/'assets/explosions/explosion_00_ncm.bin').read_bytes()
        expected=oracle(-9,-3,exp)
        for x,y in locations[1:]:expected.update(oracle(x,y,source))
        self.assertEqual(fetched(m),expected)
        self.assertEqual(m.memory.data[0x9840:0x98c0],source)
    def test_colour_all_4800_bytes_exit_and_second_run(self):
        m=Machine();original=bytes((i*53+19)&255 for i in range(4800));m.memory.colour[:4800]=original
        m.execute()
        for _ in range(800000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        frame(m,0x58);self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(m.memory.colour[:4800],original)
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.execute()
        for _ in range(800000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('second RUN')
        self.assertEqual(get(m,'c_es'),5)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(112,184))
    def test_default_no_test_enemy_fire_and_diagnostic_toggle(self):
        m=start()
        for _ in range(20):frame(m)
        self.assertEqual(get(m,'p_test_enabled'),0)
        self.assertEqual([get(m,'p_active',i) for i in range(2,6)],[0]*4)
        frame(m,0x44);self.assertEqual(get(m,'e_diag'),1)
        frame(m,0x44);self.assertEqual(get(m,'e_diag'),0)
    def test_isolated_legacy_demo_and_continuous_return(self):
        m=start()
        for _ in range(500):call(m,'e_objects')
        self.assertEqual(get(m,'e_phase',18),3)
        m.cpu.pc=N['main_loop']
        frame(m,0x54);frame(m)
        self.assertEqual(get(m,'p_test_enabled'),1)
        self.assertEqual(get(m,'e_demo'),1)
        self.assertEqual(get(m,'e_phase',18),3)
        frame(m,0x45)
        self.assertIn(get(m,'c_es',18),(2,3))
        frame(m,0x54);frame(m)
        self.assertEqual(get(m,'p_test_enabled'),0)
        self.assertEqual(get(m,'e_phase',18),2)
        for _ in range(500):call(m,'e_objects')
        self.assertEqual(get(m,'c_es',18),1)
        self.assertEqual((get(m,'e_xlo',18),get(m,'e_ylo',18)),(get(m,'e_tx',18),get(m,'e_ty',18)))
        setv(m,'c_es',0,18)
        m.cpu.pc=N['main_loop']
        frame(m,0x54);frame(m,0x45)
        self.assertEqual(get(m,'c_es',18),0)

    def test_invalid_group_count_safe_exit(self):
        m=start();m.memory.data[0x7608]=23
        call(m,'e_init');self.assertEqual(m.memory.data[N['error']],7)
        m.cpu.pc=N['main_loop'];frame(m)
        self.assertEqual(m.cpu.pc,0x200)

class AttackTests(unittest.TestCase):
    def feature_start(self):
        m=start();setv(m,'a_enabled',1);return m
    def formed(self):
        m=self.feature_start()
        for _ in range(336):call(m,'a_objects')
        self.assertEqual(get(m,'a_ready'),1)
        self.assertEqual([get(m,'c_es',i) for i in range(22)],[1]*22)
        return m
    def xy(self,m,i):
        def axis(lo,hi):
            n=get(m,lo,i)+256*get(m,hi,i);return n-65536 if n>=32768 else n
        return axis('e_xlo','e_xhi'),axis('e_ylo','e_yhi')
    def test_ram_explosion_drains_attacks_and_respawns_with_active_scheduler(self):
        m=self.formed()
        # Three live attacks overlap the collision; preserve the actual scheduler.
        for i in (0,1,11):
            m.cpu.x=i;call(m,'a_start')
        target(m,0,state=3,x=112,y=184);setv(m,'e_phase',4)
        player(m,112,184)
        lives=m.memory.data[N['player1_lives']]
        call(m,'c_collisions')
        self.assertEqual(get(m,'c_ps'),1)
        self.assertEqual(m.memory.data[N['player1_lives']],lives-1)
        waiting=False
        for tick in range(500):
            setv(m,'a_start_tick',1) # force a launch opportunity on every update
            setv(m,'a_event',0)
            call(m,'a_objects');call(m,'p_random_step');call(m,'c_timers')
            self.assertNotEqual(get(m,'a_event'),1,'new attack prevents respawn')
            waiting |= get(m,'c_ps')==2
            call(m,'c_wait')
            if get(m,'c_ps')==3:break
        else:self.fail('player never respawned with the attack scheduler enabled')
        self.assertTrue(waiting)
        self.assertEqual(get(m,'c_blink'),150)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(112,184))
        before=m.memory.data[0x1662]
        m.memory.data[0xdc00]=0xfa;call(m,'c_move')
        call(m,'c_timers')
        self.assertNotEqual(m.memory.data[0x1662],before)
        self.assertEqual(m.memory.data[0x1664],184)
        for _ in range(149):call(m,'c_timers')
        self.assertEqual(get(m,'c_ps'),0)

    def test_entry_fire_visibility_signed_muzzle_pool_and_fixed_target(self):
        m=self.feature_start();self.assertEqual(get(m,'a_ready'),0)
        def fire(state,phase,visible,x,y):
            target(m,0,state=state,x=x&255,y=y&255)
            setv(m,'e_phase',phase);setv(m,'e_visible',visible)
            setv(m,'e_xhi',255 if x<0 else 0);setv(m,'e_yhi',255 if y<0 else 0)
            setv(m,'p_cooldown',0);setv(m,'p_random_lo',0);setv(m,'p_random_hi',0)
            for j in range(2,6):setv(m,'p_active',0,j)
            call(m,'a_fire')
            return get(m,'p_active',2)
        for state,phase,visible,x,y in ((5,0,1,90,70),(2,1,0,90,70),(0,1,1,90,70),(4,1,1,90,70),(1,3,1,90,70),(2,2,1,90,70),(2,1,1,-16,70),(2,1,1,240,70),(2,1,1,90,-16),(2,1,1,90,-15),(2,1,1,90,200),(2,1,1,-9,70),(2,1,1,230,70)):
            self.assertEqual(fire(state,phase,visible,x,y),0,(state,phase,x,y))
        for x,y in ((90,70),(-8,70),(229,70)):
            self.assertEqual(fire(2,1,1,x,y),1,(x,y))
            self.assertEqual((get(m,'p_xpos',2),get(m,'p_ypos',2)),(x+8,y+16))
        target(m,0,state=2,x=90,y=70);setv(m,'e_phase',1);setv(m,'e_visible',1)
        for j in range(2,6):setv(m,'p_active',0,j)
        for _ in range(6):
            setv(m,'p_cooldown',0);setv(m,'p_random_lo',0);setv(m,'p_random_hi',0);call(m,'a_fire')
        self.assertEqual(get(m,'a_shots'),4)
        velocities=bytes(m.memory.data[N['p_vxfrac']:N['p_vy']+6])
        player(m,10,184);call(m,'p_update')
        self.assertEqual(bytes(m.memory.data[N['p_vxfrac']:N['p_vy']+6]),velocities)

    def test_real_entry_main_loop_fires_before_barrier_from_started_source(self):
        m=self.feature_start();m.cpu.pc=N['main_loop']
        for tick in range(1,336):
            setv(m,'c_ps',3);setv(m,'c_blink',150);setv(m,'c_visible',1)
            frame(m)
            active=[j for j in range(2,6) if get(m,'p_active',j)]
            self.assertLessEqual(len(active),4)
            if active:
                source=get(m,'p_source_enemy',active[0])
                self.assertEqual(get(m,'a_ready'),0)
                self.assertEqual(get(m,'c_es',source),2)
                self.assertEqual(get(m,'e_phase',source),1)
                self.assertEqual(get(m,'e_visible',source),1)
                self.assertEqual((get(m,'p_target_x',active[0]),get(m,'p_target_y',active[0])),(120,184))
                print('Stage4b3 first actual ENTRY projectile update/source:',tick,source)
                return
        self.fail('no ENTRY projectile before completion barrier')

    def test_formation_original_relative_positions_and_six_frame_visible_top(self):
        import analyze_stage3b2_data as data
        parsed=data.parse_level_record(data.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1])
        m=self.formed();minimum=min(e['formation_y'] for e in parsed['enemies'])
        self.assertEqual(minimum,25)
        for i,e in enumerate(parsed['enemies']):
            self.assertEqual(self.xy(m,i),(e['formation_x'],e['formation_y']-minimum))
        visible=[]
        frames=data.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())[14]['frames']
        for source in frames:
            m.memory.data[0x9840:0x98c0]=source;call(m,'e_render')
            visible.append(min(y for x,y in fetched(m)))
            self.assertEqual(get(m,'v014_overflow_count'),0)
        self.assertEqual(visible,[0,1,2,2,2,1])

    def test_runtime_parser_original_indices_two_separate_curves(self):
        import analyze_stage3b2_data as data
        p=data.parse_level_record(data.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1])
        m=self.feature_start()
        self.assertEqual([get(m,'a_index',i) for i in range(22)],[0]*11+[1]*11)
        for i,enemy in enumerate(p['enemies']):
            self.assertEqual(get(m,'e_ty',i),enemy['formation_y']-25)
        for raw in (0,24,25,26,184,185,255):
            m.cpu.a=raw;call(m,'a_formation_y')
            self.assertEqual(bool(m.cpu.p&1),not 25<=raw<=184)
            if 25<=raw<=184:self.assertEqual(m.cpu.a,raw-25)
        for i,h in enumerate(p['attack_curves_hex']):
            pointer=get(m,'a_ptrlo',i)+256*get(m,'a_ptrhi',i)
            self.assertEqual(get(m,'a_length',i),183)
            self.assertEqual(bytes(m.memory.data[pointer:pointer+183]),bytes.fromhex(h))
        setv(m,'a_index',2);call(m,'a_init');self.assertEqual(get(m,'error'),7)
    def test_enabled_entry_barrier_and_exact_formation_pendulum(self):
        m=self.feature_start()
        for tick in range(1,337):
            call(m,'a_objects')
            self.assertEqual(get(m,'a_offset'),0)
            self.assertEqual(get(m,'a_ready'),int(tick==336))
        setv(m,'a_start_tick',255)
        for tick in range(1,166):
            setv(m,'a_start_tick',255) # isolate pendulum from scheduler
            call(m,'a_objects')
            steps=tick//5;phase=steps%32
            expected=phase if phase<=8 else 16-phase if phase<=24 else phase-32
            self.assertEqual(get(m,'a_offset'),expected&255,tick)
            for i in range(22):
                self.assertEqual(self.xy(m,i),(get(m,'e_tx',i)+expected,get(m,'e_ty',i)))
        self.assertEqual(get(m,'a_direction'),1)
    def test_each_original_curve_points_and_invisible_reentry_to_moving_target(self):
        import analyze_stage3b2_data as data
        p=data.parse_level_record(data.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1])
        for i in (0,11):
            m=start();enemies(m);target(m,i,state=1,x=120,y=43)
            m.cpu.x=i;call(m,'a_start');x,y=120,43;crossed=False
            for cursor,b in enumerate(bytes.fromhex(p['attack_curves_hex'][i//11]),1):
                x+=-(b>>4&7) if b&128 else b>>4&7;y+=-(b&7) if b&8 else b&7
                m.cpu.x=i;call(m,'a_step')
                self.assertEqual(self.xy(m,i),(x,y),cursor)
                self.assertEqual(get(m,'e_cursor',i),cursor)
                crossed=crossed or y>=200
                self.assertEqual(get(m,'a_hidden',i),int(crossed))
            self.assertEqual(get(m,'e_phase',i),5)
            m.cpu.x=i;call(m,'a_step')
            self.assertEqual(self.xy(m,i),(x,-16))
            self.assertEqual((get(m,'c_es',i),get(m,'e_phase',i)),(2,2))
            setv(m,'a_offset',8)
            for tick in range(250):
                m.cpu.x=i;call(m,'e_move_one')
                if get(m,'c_es',i)==1:break
            self.assertEqual(self.xy(m,i),(get(m,'e_tx',i)+8,get(m,'e_ty',i)))
    def test_low_slot_curve_end_tail_is_invisible_before_return(self):
        m=start();enemies(m);target(m,2,state=1,x=61,y=25)
        m.cpu.x=2;call(m,'a_start')
        for _ in range(183):m.cpu.x=2;call(m,'a_step')
        self.assertEqual(self.xy(m,2)[1],193)
        for expected in (195,197,199,201):
            m.cpu.x=2;call(m,'a_step');self.assertEqual(self.xy(m,2)[1],expected)
        m.cpu.x=2;call(m,'e_is_visible');self.assertEqual(m.cpu.a,0)
        m.cpu.x=2;call(m,'a_step');self.assertEqual(self.xy(m,2)[1],-16)
    def test_seed_reproducibility_three_attack_cap_and_no_wait_return_selection(self):
        traces=[]
        for run in range(2):
            m=self.formed();trace=[]
            for tick in range(1200):
                call(m,'a_objects');call(m,'p_random_step')
                count=sum(get(m,'c_es',i)==3 for i in range(22))
                self.assertLessEqual(count,3);self.assertEqual(count,get(m,'a_count'))
                if get(m,'a_event')==1:
                    trace.append((tick,get(m,'a_event_enemy'),get(m,'a_index',get(m,'a_event_enemy'))))
                    setv(m,'a_event',0)
            traces.append(trace)
        self.assertEqual(traces[0],traces[1]);self.assertGreater(len(traces[0]),3)
    def test_shared_four_shot_pool_snapshot_and_dead_hidden_sources(self):
        m=start();enemies(m);setv(m,'a_ready',1);player(m,112,184)
        target(m,0,state=3,x=90,y=70);setv(m,'e_phase',4)
        for slot in range(2,6):
            setv(m,'p_cooldown',0);setv(m,'p_random_lo',0);setv(m,'p_random_hi',0)
            call(m,'a_fire')
            self.assertEqual(get(m,'p_active',slot),1)
            self.assertEqual((get(m,'p_xpos',slot),get(m,'p_ypos',slot)),(98,86))
            self.assertEqual((get(m,'p_target_x',slot),get(m,'p_target_y',slot)),(120,184))
            self.assertEqual(get(m,'p_source_enemy',slot),0)
        self.assertEqual(get(m,'a_shots'),4)
        velocities=bytes(m.memory.data[N['p_vxfrac']:N['p_vy']+6])
        player(m,10,184);call(m,'p_update')
        self.assertEqual(bytes(m.memory.data[N['p_vxfrac']:N['p_vy']+6]),velocities)
        setv(m,'p_cooldown',0);call(m,'a_fire');self.assertEqual(get(m,'a_shots'),4)
        for state,hidden in ((0,0),(4,0),(2,0),(3,1)):
            setv(m,'c_es',state);setv(m,'a_hidden',hidden)
            for j in range(2,6):setv(m,'p_active',0,j)
            setv(m,'p_cooldown',0);call(m,'a_fire')
            self.assertEqual([get(m,'p_active',j) for j in range(2,6)],[0]*4)
    def test_return_chases_offset_changes_during_flight(self):
        m=start();enemies(m);target(m,0,state=2,x=210,y=0)
        setv(m,'e_phase',2);setv(m,'e_ylo',240);setv(m,'e_yhi',255)
        setv(m,'a_enabled',1);setv(m,'a_ready',1);setv(m,'a_form_tick',1)
        for tick in range(200):
            setv(m,'a_start_tick',255)
            call(m,'a_objects')
            if get(m,'c_es')==1:break
        offset=get(m,'a_offset');offset=offset-256 if offset>=128 else offset
        self.assertTrue(-8<=offset<=8);self.assertNotEqual(offset,0)
        self.assertEqual(get(m,'c_es'),1)
        self.assertEqual(self.xy(m,0),(get(m,'e_tx')+offset,get(m,'e_ty')))
        self.assertEqual(get(m,'e_tx'),98)

    def test_bottom_and_top_reentry_fetched_pixels_no_teleport_or_stale(self):
        m=start();enemies(m);setv(m,'c_ps',2)
        target(m,0,state=3,x=90,y=200);setv(m,'e_phase',5);setv(m,'a_hidden',1)
        call(m,'e_render');self.assertEqual(fetched(m),{})
        m.cpu.x=0;call(m,'a_step');call(m,'e_render')
        self.assertEqual(self.xy(m,0),(90,-16));self.assertEqual(fetched(m),{})
        source=bytes(m.memory.data[0x9840:0x98c0])
        for _ in range(16):
            m.cpu.x=0;call(m,'e_move_one');call(m,'e_render')
            x,y=self.xy(m,0)
            self.assertEqual(fetched(m),oracle(x,y,source))
            self.assertEqual(get(m,'v014_overflow_count'),0)

    def test_real_main_loop_three_attackers_sprite_publish_and_cpu_budget(self):
        m=self.formed()
        for i in (0,1,11):m.cpu.x=i;call(m,'a_start')
        setv(m,'p_random_lo',0);setv(m,'p_random_hi',1) # valid $0100 seed: first fire roll selects attacker 0
        setv(m,'p_cooldown',0)
        m.cpu.pc=N['main_loop'];costs=[];maxshots=0
        kernel=bytes(m.memory.data[0x3e000:0x40000])
        for _ in range(160):
            setv(m,'c_ps',3);setv(m,'c_blink',150);setv(m,'c_visible',1)
            before=m.cpu.processorCycles;frame(m)
            costs.append(m.cpu.processorCycles-before)
            active=sum(get(m,'p_active',i) for i in range(2,6));maxshots=max(maxshots,active)
            self.assertLessEqual(active,4)
            self.assertLessEqual(sum(get(m,'c_es',i)==3 for i in range(22)),3)
            self.assertEqual(get(m,'v014_overflow_count'),0)
            self.assertFalse(m.memory.map_rom_writes)
        self.assertGreater(maxshots,0);self.assertLess(max(costs),250000)
        self.assertEqual(bytes(m.memory.data[0x3e000:0x40000]),kernel)
        print('Stage4b3 CPU model cycles/frame mean/peak:',sum(costs)//len(costs),max(costs),'max enemy shots:',maxshots)

    def test_legacy_test_shares_three_attacker_cap(self):
        m=self.formed()
        for i in (0,1,11):m.cpu.x=i;call(m,'a_start')
        setv(m,'p_test_enabled',1);call(m,'e_attack_test')
        self.assertEqual(get(m,'c_es',18),1);self.assertEqual(get(m,'p_attacking'),0)
        self.assertEqual(sum(get(m,'c_es',i)==3 for i in range(22)),3)
        setv(m,'c_es',0,11);call(m,'e_attack_test')
        self.assertEqual(get(m,'c_es',18),3)
        self.assertEqual(sum(get(m,'c_es',i)==3 for i in range(22)),3)

    def test_start_attack_render_restart_exit_with_roma_romc_overlays(self):
        m=Machine();m.memory.data[0xd030]|=0x20;m.before=bytes(m.memory.data)
        m.execute();self.assertEqual(m.error,0)
        for _ in range(800000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('ROM-overlay boot')
        for _ in range(336):call(m,'a_objects')
        m.cpu.x=0;call(m,'a_start')
        for _ in range(10):
            m.memory.data[0xd030]|=0x10 # new helpers also execute with ROMA, unlike legacy B800 renderer
            call(m,'a_objects');call(m,'a_fire')
            m.memory.data[0xd030]&=0xef
            call(m,'e_render')
        self.assertTrue(fetched(m));self.assertFalse(m.memory.rom_overlay_reads)
        setv(m,'c_ps',4);setv(m,'c_armed',1);m.cpu.pc=N['main_loop'];frame(m,0x52)
        self.assertEqual(get(m,'a_ready'),0)
        self.assertFalse(m.memory.rom_overlay_reads)
        frame(m,0x58);self.assertEqual(m.cpu.pc,0x200)
        self.assertEqual(m.memory.data[0xd030],m.before[0xd030])

    def test_attack_return_hits_scores_ram_and_reset_state(self):
        for state,phase in ((3,4),(2,2)):
            m=start();enemies(m);target(m,0,state=state,x=90,y=90);setv(m,'e_phase',phase)
            shot(m,0);call(m,'c_collisions')
            self.assertEqual(get(m,'c_es'),4);self.assertEqual(word(m,0x1a04),175)
            for _ in range(EXP_TICKS):call(m,'c_timers');call(m,'a_objects')
            self.assertEqual(get(m,'c_es'),0)
        m=self.formed();setv(m,'a_offset',8);setv(m,'a_hidden',1)
        call(m,'c_init');self.assertEqual(get(m,'a_ready'),0);self.assertEqual(get(m,'a_offset'),0)
        self.assertEqual([get(m,'a_hidden',i) for i in range(22)],[0]*22)
        self.assertEqual([get(m,'c_es',i) for i in range(22)],[5]*22)

if __name__=='__main__':unittest.main()
