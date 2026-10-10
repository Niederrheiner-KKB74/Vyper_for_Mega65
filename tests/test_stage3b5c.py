"""Real Stage 3b-5c instructions; narrow CPU/DMA/VIC models, not XEMU."""
import unittest
import os
import sys
import json
from pathlib import Path
import test_stage3b5b as OLD
sys.path.insert(0,str(OLD.ROOT/'tools'))
import build_stage3b5c as BUILD
import build_explosion_assets as EXP
ROOT=OLD.ROOT
ART=ROOT/'releases/stage_3b5c'
N=BUILD.symbols((ART/'STAGE3B5C.sym').read_text())
class Machine(OLD.Machine):
    def __init__(self):
        super().__init__()
        p=(ART/'STAGE3B5C.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.cpu.pc=N['p_startup']
        self.memory.data[0xd613]=255
        self.before=bytes(self.memory.data)
def start():
    m=Machine().execute()
    assert m.error==0
    for _ in range(300000):
        if m.cpu.pc==N['main_loop']:return m
        m.cpu.step()
    raise AssertionError('boot')
def call(m,name):
    m.cpu.pc=N[name];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff)
    for _ in range(2_000_000):
        if m.cpu.pc==0x200:return
        m.cpu.step()
    raise AssertionError(name+' did not return')
def frame(m,key=0,buttons=255):
    m.memory.data[0xdc00]=buttons
    sampled=False
    for _ in range(250000):
        if m.cpu.pc==0x200 or sampled and m.cpu.pc==N['main_loop']:return
        if m.cpu.pc==0xffe4:
            sampled=True;m.cpu.a=key;m.cpu.pc=m.cpu.stPopWord()+1
        else:m.cpu.step()
    raise AssertionError('frame')
def setv(m,name,v,i=0):m.memory.data[N[name]+i]=v&255
def get(m,name,i=0):return m.memory.data[N[name]+i]
def word(m,a,n=4):return int.from_bytes(m.memory.data[a:a+n],'little')
def enemies(m,state=0):
    m.memory.data[N['c_es']:N['c_es']+23]=bytes([state])*23
    m.memory.data[N['p_test_enabled']]=0
    m.memory.data[N['p_active']:N['p_active']+6]=bytes(6)
def player(m,x=90,y=90):m.memory.data[0x1662]=x;m.memory.data[0x1664]=y
def target(m,i=0,state=1,x=90,y=90):
    setv(m,'c_es',state,i)
    if i==22:m.memory.data[0x167a]=x;m.memory.data[0x167c]=y
    else:setv(m,'s2i_x',x,i);setv(m,'s2i_y',y,i)
def shot(m,i,x=98,y=96):
    setv(m,'p_active',1,i);setv(m,'p_xpos',x,i);setv(m,'p_ypos',y,i)
class CollisionTests(unittest.TestCase):
    def test_original_conversion_every_pixel_mask_and_guard(self):
        import re
        source=(ROOT/'assets/explosions/explosion_amiga_planes.txt').read_text()
        frames=EXP.convert(source)
        blocks=re.findall(r'```text\s+([\s\S]*?)```',source)
        p=(ART/'STAGE3B5C.PRG').read_bytes()[2:]
        for i,(f,block) in enumerate(zip(frames,blocks)):
            planes=[bytes.fromhex(row) for row in block.strip().splitlines()]
            self.assertEqual(f,(ROOT/f'assets/explosions/explosion_{i:02d}_ncm.bin').read_bytes())
            for y in range(16):
                for x in range(16):
                    b=2*y+x//8;mask=128>>(x%8)
                    c=sum(1<<j for j in range(3) if planes[j][b]&mask)+1 if planes[3][b]&mask else 0
                    self.assertEqual((f[y*8+x//2]>>(4*(x%2)))&15,c)
            a=0xc100+i*256 if i<7 else 0xca00
            self.assertEqual(p[a-0x2001:a-0x2001+256],bytes(64)+f+bytes(64))
        with self.assertRaises(ValueError):EXP.convert(source.replace('Frame 7','Frame 8'))
    def test_full_loader_type15_animation_and_old_motion(self):
        m=start();old=OLD.start()
        self.assertEqual(get(m,'selected_type'),15);self.assertEqual(get(m,'frame_count'),6)
        for name,base in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000)]:
            p=(ROOT/'assets'/name).read_bytes();self.assertEqual(m.memory.data[base:base+len(p)],p)
        for tick in range(30):
            buttons=(0xfb,0xf7,0xfe,0xfd,0xff)[tick%5]
            frame(m,buttons=buttons);OLD.frame(old,buttons=buttons)
            self.assertEqual(m.memory.data[0x1600:0x1920],old.memory.data[0x1600:0x1920])
            self.assertEqual(m.memory.data[0x9840:0x98c0],old.memory.data[0x9840:0x98c0])
            self.assertEqual(m.memory.data[0xc800:0xca00],old.memory.data[0xc800:0xca00])
        self.assertEqual(word(m,0x1a17,2),175)
    def test_formation_entry_attack_orbit_and_once(self):
        m=start()
        for i,state,points in [(0,1,100),(1,2,175),(18,3,175),(22,1,100)]:
            enemies(m);target(m,i,state);shot(m,0);shot(m,1)
            before=word(m,0x1a04)
            call(m,'c_collisions')
            self.assertEqual(get(m,'c_es',i),4)
            self.assertEqual((get(m,'c_ex',i),get(m,'c_ey',i)),(90,90))
            self.assertEqual(get(m,'p_active',0),0);self.assertEqual(get(m,'p_active',1),1)
            self.assertEqual(word(m,0x1a04),before+points)
            self.assertEqual(word(m,0x1a00),before+points)
            call(m,'c_collisions');self.assertEqual(word(m,0x1a04),before+points)
    def test_four_enemy_shots_one_life_player_frozen(self):
        m=start();enemies(m);player(m)
        for i in range(2,6):shot(m,i)
        call(m,'c_collisions');self.assertEqual(get(m,'c_ps'),1)
        self.assertEqual(word(m,0x1a0a,2),2)
        self.assertEqual(get(m,'p_active',2),0)
        self.assertEqual([get(m,'p_active',i) for i in (3,4,5)],[1,1,1])
        call(m,'c_collisions');self.assertEqual(word(m,0x1a0a,2),2)
        for _ in range(24):
            m.memory.data[0xdc00]=0xfb;call(m,'c_move');self.assertEqual(m.memory.data[0x1662],90)
            call(m,'c_timers')
        self.assertEqual(get(m,'c_ps'),2)
    def test_ram_two_explosions_no_points_and_invulnerability(self):
        m=start();enemies(m);player(m)
        target(m,state=1);call(m,'c_collisions');self.assertEqual(get(m,'c_ps'),0)
        target(m,state=2);call(m,'c_collisions');self.assertEqual(get(m,'c_ps'),1)
        self.assertEqual(get(m,'c_es'),4);self.assertEqual(word(m,0x1a04),0)
        self.assertEqual(word(m,0x1a0a,2),2)
        call(m,'c_objects');self.assertEqual(get(m,'s2i_x'),90)
        self.assertEqual(get(m,'s2i_y'),90)
        setv(m,'c_ps',3);target(m,state=3);call(m,'c_collisions')
        self.assertEqual(get(m,'c_es'),3);self.assertEqual(word(m,0x1a0a,2),2)
    def test_independent_frames_complete_and_guards_render(self):
        m=start();enemies(m);player(m)
        target(m,0,3);target(m,1,1,x=130);shot(m,0,138,96)
        call(m,'c_collisions') # enemy1 hit then player ram enemy0
        self.assertEqual([get(m,'c_es',i) for i in (0,1)],[4,4])
        for tick in range(24):
            self.assertEqual(get(m,'c_pf'),tick//3)
            self.assertEqual([get(m,'c_ef',i) for i in (0,1)],[tick//3]*2)
            call(m,'c_render');self.assertEqual(get(m,'v014_overflow_count'),0)
            self.assertEqual([get(m,'c_ex',i) for i in (0,1)],[90,130])
            call(m,'c_timers')
        self.assertEqual([get(m,'c_es',i) for i in (0,1)],[0,0])
        self.assertEqual(get(m,'c_ps'),2)
        target(m,0,1);m.cpu.x=0;call(m,'c_enemy_hit')
        for _ in range(3):call(m,'c_timers')
        target(m,1,1,x=130);m.cpu.x=1;call(m,'c_enemy_hit')
        self.assertEqual([get(m,'c_ef',i) for i in (0,1)],[1,0])
        call(m,'c_render')
        self.assertEqual(get(m,'v014_overflow_count'),0)
    def test_wait_real_states_blink_exact_150_25_and_no_fire(self):
        m=start();enemies(m);player(m,100,120)
        call(m,'c_player_hit');setv(m,'c_ps',2);target(m,0,3)
        call(m,'c_wait');self.assertEqual(get(m,'c_ps'),2)
        target(m,0,0);call(m,'c_wait');self.assertEqual(get(m,'c_ps'),3)
        self.assertEqual((get(m,'c_px'),get(m,'c_py')),(100,120))
        for tick in range(150):
            self.assertEqual(get(m,'c_visible'),1 if (tick//25)%2==0 else 0)
            shot(m,2,108,126);target(m,0,3,x=100,y=120)
            call(m,'c_collisions');self.assertEqual(word(m,0x1a0a,2),2)
            self.assertEqual(get(m,'c_es'),3)
            call(m,'c_timers')
        self.assertEqual(get(m,'c_ps'),0);self.assertEqual(get(m,'c_visible'),1)
        call(m,'c_collisions');self.assertEqual(word(m,0x1a0a,2),1)
    def test_points_formula_carry_saturation_and_display(self):
        m=start()
        for level in [1,10,11,20,21,100,65535]:
            m.memory.data[0x1a08:0x1a0a]=level.to_bytes(2,'little');call(m,'c_formula')
            a=100+50*((level-1)//10);b=a+75
            self.assertEqual(word(m,N['c_points']),a);self.assertEqual(word(m,N['c_points']+4),b)
            self.assertEqual(word(m,0x1a15,2),a%1000);self.assertEqual(word(m,0x1a17,2),b%1000)
        m.memory.data[0x1a04:0x1a08]=(0xfffffffe).to_bytes(4,'little')
        setv(m,'c_oldstate',1);call(m,'c_award')
        self.assertEqual(word(m,0x1a04),0xffffffff);self.assertEqual(word(m,0x1a00),0xffffffff)
    def test_hitbox_touching_and_playfield_edges(self):
        m=start();enemies(m)
        for x,y,sx,sy,hit in [(32,16,34,18,True),(224,167,237,180,True),(32,16,46,18,False),(32,16,34,30,False),(32,16,33,18,False),(32,16,34,14,False)]:
            target(m,0,1,x,y);shot(m,0,sx,sy);call(m,'c_collisions')
            self.assertEqual(get(m,'c_es')==4,hit)
    def test_gameover_wait_restart_highscore_exit_repeated(self):
        m=start();enemies(m);player(m)
        m.memory.data[0x1a00:0x1a04]=(12345678).to_bytes(4,'little')
        for repeat in range(3):
            enemies(m);player(m)
            m.memory.data[0x1a0a:0x1a0c]=bytes([1,0])
            shot(m,2);frame(m)
            self.assertEqual(get(m,'c_ps'),1)
            for _ in range(23):frame(m)
            self.assertEqual(get(m,'c_ps'),1)
            frame(m);self.assertEqual(get(m,'c_ps'),4)
            screen=bytes(m.memory.data[0x5000:0x5c80]);colour=bytes(m.memory.colour[:3200])
            for row,text in [(9,[7,1,13,5,32,15,22,5,18]),(11,[18,32,45,32,18,5,19,20,1,18,20]),(13,[24,32,45,32,5,24,9,20])]:
                off=row*128+84
                self.assertEqual(list(screen[off+2:off+2+2*len(text):2]),text)
                self.assertEqual(colour[off:off+2],bytes([0x10,0]))
                self.assertEqual(colour[off+2:off+2+2*len(text)],bytes([0,2])*len(text))
                self.assertEqual(screen[off+2+2*len(text):off+6+2*len(text)],bytes([0x80,2,0,2]))
                self.assertEqual(colour[off+2+2*len(text):off+6+2*len(text)],bytes([0x10,0,8,0]))
            self.assertEqual(m.memory.data[0xd015],0)
            for key in [0x52,0x20,0x2b,0x54,0x45]:frame(m,key)
            self.assertEqual(get(m,'c_ps'),4);self.assertEqual(bytes(m.memory.data[0x5000:0x5c80]),screen)
            self.assertEqual(bytes(m.memory.colour[:3200]),colour)
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
        self.assertEqual(m.memory.colour[:3200],m.before[0xd800:0xe000]+bytes([0xa5])*1152)
    def test_blink_blocks_real_frame_joystick_and_fire_and_pause_does_not_stop_explosion(self):
        m=start();enemies(m);player(m,100,120)
        shot(m,2,108,126);frame(m)
        death=(m.memory.data[0x1662],m.memory.data[0x1664])
        frame(m,0x20)
        for _ in range(23):frame(m)
        self.assertEqual(get(m,'c_ps'),3)
        setv(m,'c_es',0,18)
        for tick in range(149):
            frame(m,buttons=0xeb) # held LEFT + FIRE
            self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),death)
            self.assertEqual([get(m,'p_active',i) for i in (0,1)],[0,0])
        frame(m,buttons=0xeb)
        self.assertEqual(get(m,'c_ps'),0)
        self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),death)
        frame(m,buttons=0xfb);frame(m,buttons=0xef)
        self.assertEqual(get(m,'p_active',0),1)
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
        for _ in range(300000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('second RUN')
        self.assertEqual(get(m,'c_ps'),0);self.assertEqual(word(m,0x1a0a,2),3)
        frame(m,0x58);self.assertEqual(m.cpu.pc,0x200)
    def test_restart_invalid_original_record_exits_without_stack_corruption(self):
        m=start();setv(m,'c_ps',4);setv(m,'c_armed',1);setv(m,'anim_paused',1)
        m.memory.data[0x40328]=0
        frame(m,0x52)
        self.assertEqual(m.cpu.pc,0x200);self.assertNotEqual(m.error,0)
        self.assertEqual(m.memory.data[0xd015],0)
    def test_build_baseline_and_disk(self):
        p=(ART/'STAGE3B5C.PRG').read_bytes();BUILD.verify_engine(p,N)
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE3B5C.d81').read_bytes(),[('STAGE3B5C',p,0x82)]+[(n,(ROOT/'assets'/n).read_bytes(),0x81) for n in ('VYLV.DAT','VYGR.DAT')])
if __name__=='__main__':unittest.main()
