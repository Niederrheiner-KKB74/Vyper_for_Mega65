"""Real assembled instructions with CPU/DMA/VIC models; not a full XEMU run."""
import json
import os
from pathlib import Path
import sys
import unittest
import test_stage3b4a as HUD
sys.path.insert(0,str(HUD.BUILD.ROOT/'tools'))
import build_stage3b5b as BUILD
ROOT=BUILD.ROOT
ARTIFACTS=ROOT/'releases/stage_3b5b'
N=BUILD.symbols((ARTIFACTS/'STAGE3B5B.sym').read_text())

class Machine(HUD.Machine):
    def __init__(self):
        super().__init__()
        p=(ARTIFACTS/'STAGE3B5B.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
        self.cpu.pc=N['p_startup']
        # Actual VIC-IV native text origin for coordinate tests, including high bits.
        self.memory.data[0xd04c:0xd050]=bytes([80,0,104,0])
        self.before=bytes(self.memory.data)

def call(m,name):
    m.cpu.pc=N[name];m.cpu.sp=0xfd;m.cpu.stPushWord(0x01ff)
    for _ in range(200_000):
        if m.cpu.pc==0x0200:return
        m.cpu.step()
    raise AssertionError('Routine did not return: '+name)

def start():
    m=Machine().execute()
    assert m.error==0
    for _ in range(300_000):
        if m.cpu.pc==N['main_loop']:return m
        m.cpu.step()
    raise AssertionError('Initialization did not complete')

def frame(m,key=0,buttons=255):
    m.memory.data[0xdc00]=buttons
    sampled=False
    for _ in range(200_000):
        if m.cpu.pc==0x0200 or sampled and m.cpu.pc==N['main_loop']:return
        if m.cpu.pc==0xffe4:
            sampled=True;m.cpu.a=key;m.cpu.pc=m.cpu.stPopWord()+1
        else:m.cpu.step()
    raise AssertionError('Frame did not complete')

def put(m,name,value,slot=0):m.memory.data[N['p_'+name]+slot]=value&255

def get(m,name,slot=0):return m.memory.data[N['p_'+name]+slot]

def fixed(m,lo,hi,slot=0):
    v=get(m,lo,slot)+256*get(m,hi,slot)
    return v-65536 if v>=32768 else v

def enemy(m,px=120,py=160,ex=100,ey=40):
    m.memory.data[0x1660+2]=px
    m.memory.data[0x1660+4]=py
    m.memory.data[N['s2i_x']+18]=ex
    m.memory.data[N['s2i_y']+18]=ey
    for name,value in [('attacking',1),('cooldown',0),('random_lo',0)]:put(m,name,value)
    call(m,'p_enemy_fire')

class ProjectileTests(unittest.TestCase):
    def test_mapping_table_full_load_and_six_original_frames(self):
        m=start();rows=json.loads((ROOT/'assets/vylv_vygr_mapping.json').read_text())
        self.assertEqual([r['vylv_index'] for r in rows if r['confirmed']],[14])
        for r in rows:
            m.cpu.a=r['vylv_index'];call(m,'p_map_type')
            self.assertEqual(m.cpu.a,r['vygr_type_1based'])
        self.assertEqual(m.memory.data[N['selected_type']],15)
        self.assertEqual(m.memory.data[N['frame_count']],6)
        types=HUD.PREVIOUS.R.DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())
        seen=set()
        for _ in range(12):
            frame=m.memory.data[N['frame']];seen.add(frame)
            self.assertEqual(m.memory.data[0x9840:0x98c0],types[14]['frames'][frame])
            call(m,'animate')
        self.assertEqual(seen,set(range(6)))
        for name,base in [('VYLV.DAT',0x40000),('VYGR.DAT',0x54000)]:
            data=(ROOT/'assets'/name).read_bytes();self.assertEqual(m.memory.data[base:base+len(data)],data)

    def test_player_two_slots_edge_fire_and_independent_vertical_motion(self):
        m=start();m.memory.data[0x1660+2]=90;m.memory.data[0x1660+4]=80
        for sample in (0xef,0xef,0xff,0xef,0xff,0xef):
            m.memory.data[N['v014_joy_sample']]=sample;call(m,'p_player_fire')
        self.assertEqual([get(m,'active',i) for i in range(6)],[1,1,0,0,0,0])
        self.assertEqual([get(m,'xpos',i) for i in (0,1)],[98,98])
        self.assertEqual([get(m,'ypos',i) for i in (0,1)],[80,80])
        put(m,'vy',252,0);call(m,'p_update')
        self.assertEqual((get(m,'ypos',0),get(m,'ypos',1)),(76,77))
        m.memory.data[0x1660+2]=180
        put(m,'ypos',2,0);call(m,'p_update')
        self.assertEqual(get(m,'active',0),0);self.assertEqual(get(m,'active',1),1)
        self.assertEqual(get(m,'ypos',1),74);self.assertEqual(get(m,'xpos',1),98)
        m.memory.data[N['v014_joy_sample']]=255;call(m,'p_player_fire')
        m.memory.data[N['v014_joy_sample']]=239;call(m,'p_player_fire')
        self.assertEqual(get(m,'xpos',0),188)

    def test_aim_vectors_saved_once_and_edge_cases(self):
        m=start()
        for px,py,ex,ey in [(20,160,100,40),(200,160,100,40),(100,160,100,40),(224,57,70,40),(32,57,170,40),(100,56,100,40),(100,20,100,40)]:
            for i in range(2,6):put(m,'active',0,i)
            enemy(m,px,py,ex,ey)
            if py<=ey+16:self.assertEqual(get(m,'active',2),0);continue
            self.assertEqual(get(m,'active',2),1)
            dx=(px+8)-(ex+8);dy=py-(ey+16)
            expected=min(abs(dx)*256//dy,512)*(1 if dx>=0 else -1)
            self.assertEqual(fixed(m,'vxfrac','vx',2),expected)
            self.assertEqual((get(m,'target_x',2),get(m,'target_y',2)),(px+8,py))
            self.assertEqual((get(m,'xpos',2),get(m,'ypos',2)),(ex+8,ey+16))
            saved=bytes(m.memory.data[N['p_target_x']:N['p_source_enemy']+6])
            m.memory.data[0x1660+2]=220
            call(m,'p_update')
            self.assertEqual(fixed(m,'vxfrac','vx',2),expected)
            self.assertEqual(saved,m.memory.data[N['p_target_x']:N['p_source_enemy']+6])

    def test_division_extremes_without_update_division(self):
        m=Machine()
        for dx in (0,1,17,127,231,255):
            for dy in (1,2,3,17,128,199):
                for neg in (0,1):
                    put(m,'dx',dx);put(m,'denominator',dy);put(m,'negative',neg)
                    call(m,'p_direction')
                    result=m.memory.data[N['p_numerator']]+256*m.memory.data[N['p_numerator']+1]
                    if result>=32768:result-=65536
                    self.assertEqual(result,min(dx*256//dy,512)*(-1 if neg else 1))

    def test_global_four_slots_formation_and_cooldown(self):
        m=start()
        for _ in range(7):enemy(m)
        self.assertEqual([get(m,'active',i) for i in range(6)],[0,0,1,1,1,1])
        self.assertEqual(get(m,'source_enemy',2),18)
        for i in range(2,6):put(m,'active',0,i)
        enemy(m);put(m,'random_lo',0);call(m,'p_enemy_fire')
        self.assertEqual([get(m,'active',i) for i in range(2,6)],[1,0,0,0])
        put(m,'cooldown',0);put(m,'attacking',0);call(m,'p_enemy_fire')
        self.assertEqual([get(m,'active',i) for i in range(2,6)],[1,0,0,0])

    def test_random_cadence_test_window_and_no_homing(self):
        m=start();put(m,'random_lo',0xe1);put(m,'random_hi',0xac)
        m.memory.data[0x1660+4]=167
        m.memory.data[N['s2i_y']+18]=30;m.memory.data[N['s2i_x']+18]=100
        fired=[];last=[0]*6
        for tick in range(400):
            call(m,'p_test_attack');call(m,'p_random_step');call(m,'p_update');call(m,'p_enemy_fire')
            now=[get(m,'active',i) for i in range(6)]
            if sum(now)>sum(last):fired.append(tick)
            self.assertLessEqual(sum(now[2:]),4)
            last=now
        self.assertGreater(len(fired),4)
        gaps=[b-a for a,b in zip(fired,fired[1:])]
        self.assertTrue(all(g>=13 for g in gaps));self.assertGreater(len(set(gaps)),1)
        put(m,'test_enabled',0);call(m,'p_test_attack');self.assertEqual(get(m,'attacking'),0)

    def test_bounds_six_visible_sprites_and_native_coordinate_conversion(self):
        m=start()
        for i in range(6):
            put(m,'active',1,i);put(m,'xpos',220-i*10,i);put(m,'ypos',140-i*10,i)
        call(m,'p_publish');self.assertEqual(m.memory.data[0xd015],0x3f)
        for i in range(6):
            x=m.memory.data[0xd000+i*2]+(256 if m.memory.data[0xd010]&(1<<i) else 0)+(512 if m.memory.data[0xd05f]&(1<<i) else 0)
            y=m.memory.data[0xd001+i*2]+(256 if m.memory.data[0xd077]&(1<<i) else 0)+(512 if m.memory.data[0xd078]&(1<<i) else 0)
            self.assertEqual(x,80+2*(220-i*10)-(1 if i<2 else 3))
            self.assertEqual(y,104+2*(140-i*10))
            self.assertLess(x+(2 if i<2 else 6),80+480)
        for x,y,vx in [(1,100,-2),(238,100,2),(120,196,0)]:
            put(m,'active',1,2);put(m,'xpos',x,2);put(m,'ypos',y,2);put(m,'vx',vx,2);put(m,'vxfrac',0,2);put(m,'vy',1,2)
            call(m,'p_update');self.assertEqual(get(m,'active',2),0)
        self.assertEqual(m.memory.data[0xd06b],0);self.assertEqual(m.memory.data[0xd057],0)
        # Fetch the actual 16-bit sprite pointers and mono data as XEMU does.
        # SPR640 adds one native pixel to the register X. V400 adds no Y offset.
        visible=[]
        for i in range(6):
            ptr=int.from_bytes(m.memory.data[0x8900+i*2:0x8902+i*2],'little')*64
            bits=m.memory.data[ptr:ptr+63]
            width=2 if i<2 else 6
            self.assertEqual(sum(v.bit_count() for v in bits),width*8)
            x=m.memory.data[0xd000+i*2]+(256 if m.memory.data[0xd010]&(1<<i) else 0)+(512 if m.memory.data[0xd05f]&(1<<i) else 0)+1
            y=m.memory.data[0xd001+i*2]+(256 if m.memory.data[0xd077]&(1<<i) else 0)
            pixels={(x+bit,y+row,m.memory.data[0xd027+i]) for row in range(21) for bit in range(24) if bits[row*3+bit//8] & (128>>(bit%8))}
            self.assertEqual(len(pixels),width*8)
            self.assertTrue(all(px<560 and py<504 for px,py,_ in pixels))
            visible.append(pixels)
        self.assertTrue(all(visible))
        self.assertEqual(m.memory.data[0xd076],0x3f)
        self.assertEqual(m.memory.data[0xd04d]&0xf0,0)
        self.assertEqual(m.memory.data[0xd04f]&0xf0,0)

    def test_loader_failure_restores_sprite_modes_without_engine_start(self):
        m=Machine();m.files.pop('VYGR.DAT')
        for a,v in {0xd04d:0xa0,0xd04f:0xc0,0xd054:0x12,0xd076:0xff,0xd027:9}.items():m.memory.data[a]=v
        before=bytes(m.memory.data)
        m.execute()
        self.assertNotEqual(m.error,0)
        self.assertEqual(m.cpu.pc,0x0200)
        for a in (0xd04d,0xd04f,0xd054,0xd076,0xd027,0xd021):self.assertEqual(m.memory.data[a],before[a])
        self.assertEqual(m.memory.data[0xd015],0)

    def test_movement_hud_and_exit_restart_preserve_stable(self):
        old=HUD.Machine().execute();HUD.begin(old)
        m=start();before=bytes(m.before)
        for i in range(30):
            buttons=(0xfb,0xf7,0xfe,0xfd,0xef,0xff)[i%6]
            frame(old,buttons=buttons);frame(m,buttons=buttons)
            for lo,hi in [(0x1600,0x1920),(0x5000,0x5c80),(0xc800,0xc900)]:
                self.assertEqual(m.memory.data[lo:hi],old.memory.data[lo:hi])
        frame(m,key=0x58)
        self.assertEqual(m.cpu.pc,0x0200)
        self.assertEqual(m.memory.data[0xd015],0)
        regs=list(range(0xd000,0xd011))+list(range(0xd027,0xd02d))+[0xd04d,0xd04f,0xd017,0xd01b,0xd01c,0xd01d,0xd054,0xd055,0xd057,0xd05f,0xd06b,0xd06c,0xd06d,0xd06e,0xd076,0xd077,0xd078]
        for r in regs:self.assertEqual(m.memory.data[r],before[r],hex(r))
        self.assertEqual(m.memory.colour[:3200],bytes(before[0xd800:0xe000])+bytes([0xa5])*1152)
        self.assertEqual(m.memory.data[0x1000:0x1600],before[0x1000:0x1600])
        rom=os.environ.get('MEGA65_ROM')
        if rom:
            data=Path(rom).read_bytes()
            self.assertEqual(HUD.EXIT.hashlib.sha256(data).hexdigest(),HUD.EXIT.ROM_SHA)
            for a,v in {0x111f:0,0x1120:0,0x1121:0x20,0x1122:1,0x1123:0}.items():m.memory.data[a]=v
            HUD.EXIT.blink(m,data)
        # Second RUN without reloading PRG, loader and sprite state fully reset.
        m.cpu.pc=N['p_startup'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x01ff);m.execute()
        for _ in range(300_000):
            if m.cpu.pc==N['main_loop']:break
            m.cpu.step()
        else:self.fail('Second initialization failed')
        self.assertEqual(m.memory.data[0xd015],0)

if __name__=='__main__':unittest.main()
