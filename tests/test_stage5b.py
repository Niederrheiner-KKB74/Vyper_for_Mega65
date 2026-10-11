"""Actual assembled Stage 5b entry instructions and fetched RRB pixels; not XEMU."""
import unittest
from pathlib import Path
import test_stage3b5c as PREV
import build_stage5b as BUILD
ROOT=PREV.ROOT
ART=ROOT/'releases/stage_5b'
N=BUILD.symbols((ART/'STAGE5B.sym').read_text())
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
    @property
    def error(self):return self.memory.data[N["error"]]
    def __init__(self):
        super().__init__()
        self.files["VYGR.DAT"]=(ROOT/"assets/stage5b/VYGR.DAT").read_bytes()
        p=(ART/'STAGE5B.PRG').read_bytes()
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


import json
import struct
import analyze_stage5b_capacity as CAP
import extract_stage5b_graphics as GRAPHICS

class LevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boot=start()
        cls.snapshot=bytes(cls.boot.memory.data)
        cls.colour=bytes(cls.boot.memory.colour)
        cls.records=CAP.DATA.level_records((ROOT/'assets/VYLV.DAT').read_bytes())
        cls.mapping=json.loads((ROOT/'assets/stage5b/vylv_vygr_mapping.json').read_text())
        cls.types=GRAPHICS.graphics_types((ROOT/'assets/stage5b/VYGR.DAT').read_bytes())
    def machine(self):
        m=Machine()
        m.memory.data[:]=self.snapshot;m.memory.colour[:]=self.colour
        m.cpu.pc=N['main_loop'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff)
        return m
    def transition(self,m,n):
        m.cpu.a=n;call(m,'transition');self.assertEqual(m.error,0)
        self.assertEqual(get(m,'number'),n)
    def test_capacity_and_original_assets(self):
        report=CAP.audit()
        self.assertEqual(report['summary']['max_entry_curve_bytes'],469)
        self.assertEqual(report['summary']['max_spawn_delay'],2100)
        self.assertEqual(report['summary']['max_graphic_indices'],22)
        self.assertEqual(report['summary']['max_rrb_slots'],23)
        BUILD.BASE.verify_disk((ART/'VYPER_STAGE5B.d81').read_bytes(),[('STAGE5B',(ART/'STAGE5B.PRG').read_bytes(),0x82)]+[(n,(ROOT/'assets'/('stage5b/'+n if n=='VYGR.DAT' else n)).read_bytes(),0x81) for n in ['VYLV.DAT','VYGR.DAT']])
    def test_every_original_record_runtime_initialization(self):
        m=self.machine()
        for number,(offset,record) in enumerate(self.records,1):
            with self.subTest(level=number):
                self.transition(m,number)
                p=CAP.DATA.parse_level_record(record)
                self.assertEqual(m.memory.data[0x12000:0x12000+len(record)],record)
                self.assertEqual(m.memory.data[0x7600:0x7608],record[:8])
                self.assertEqual(word(m,N['record_end'],2),0x2000+len(record))
                self.assertEqual(get(m,'y_shift'),min(e['formation_y'] for e in p['enemies']))
                self.assertEqual(get(m,'a_curve_count'),len(p['attack_curves_hex']))
                self.assertEqual(get(m,'attack_allowed'),int(number not in [25,50,99,100]))
                cursor=8;slot=0
                for i,g in enumerate(p['groups']):
                    cursor+=8
                    self.assertEqual(get(m,'e_glen',i)+256*get(m,'e_glenhi',i),g['curve_length'])
                    self.assertEqual(get(m,'e_gptrlo',i)+256*get(m,'e_gptrhi',i),0x2000+cursor)
                    for j in range(g['enemy_count']):
                        self.assertEqual(get(m,'e_group',slot),i)
                        self.assertEqual(get(m,'e_delay',slot)+256*get(m,'e_delayhi',slot),j*p['entry_interval'])
                        slot+=1
                    cursor+=g['curve_length']
                for i,e in enumerate(p['enemies']):
                    self.assertEqual(get(m,'c_es',i),5)
                    self.assertEqual(get(m,'a_index',i),e['attack_index'])
                    self.assertEqual(get(m,'e_tx',i),e['formation_x'])
                    self.assertEqual(get(m,'e_ty',i),e['formation_y']-get(m,'y_shift'))
                    typ=self.types[self.mapping[e['graphic_type']]['vygr_type_1based']-1]
                    self.assertEqual(get(m,'gframes',i),typ['frame_count'])
                    self.assertEqual(get(m,'gxlo',i)+256*get(m,'gxhi',i),typ['offset'])
                for i in range(len(p['enemies']),23):self.assertEqual(get(m,'c_es',i),0)
                k=(number-1)//10
                self.assertEqual(word(m,N['formation_points'],2),100+50*k)
                self.assertEqual(word(m,N['attack_points'],2),175+50*k)
                cursor+=len(p['enemies'])*6
                for i,h in enumerate(p['attack_curves_hex']):
                    payload=bytes.fromhex(h);cursor+=2
                    self.assertEqual(get(m,'a_ptrlo',i)+256*get(m,'a_ptrhi',i),0x2000+cursor)
                    self.assertEqual(get(m,'a_length',i),len(payload));cursor+=len(payload)
    def test_preserves_values_and_resets_all_transients(self):
        m=self.machine()
        for n,v in [('player1_score',987654),('high_score',1234567),('player1_lives',2)]:
            length=2 if n.endswith('lives') else 4;m.memory.data[N[n]:N[n]+length]=v.to_bytes(length,'little')
        setv(m,'anim_speed',9);setv(m,'anim_paused',1)
        for number in [2,3,5,25,50,71,99,100,1]:
            enemies(m,4);setv(m,'c_ps',1);setv(m,'a_offset',8)
            m.memory.data[N['p_active']:N['p_active']+6]=bytes([1])*6
            self.transition(m,number)
            self.assertEqual(word(m,N['player1_score']),987654)
            self.assertEqual(word(m,N['high_score']),1234567)
            self.assertEqual(word(m,N['player1_lives'],2),2)
            self.assertEqual((get(m,'anim_speed'),get(m,'anim_paused')),(9,1))
            self.assertEqual(get(m,'c_ps'),0);self.assertEqual(get(m,'a_offset'),0)
            self.assertEqual(m.memory.data[N['p_active']:N['p_active']+6],bytes(6))
            self.assertEqual((m.memory.data[0x1662],m.memory.data[0x1664]),(112,184))
    def test_long_original_entry_curve_and_word_delays(self):
        m=self.machine();self.transition(m,60)
        p=CAP.DATA.parse_level_record(self.records[59][1]);slot=sum(g['enemy_count'] for g in p['groups'][:3])
        g=p['groups'][3];setv(m,'e_slot',slot);setv(m,'e_delay',0,slot);setv(m,'e_delayhi',0,slot)
        m.cpu.x=slot;call(m,'e_move_one')
        x,y=g['start_x'],g['start_y']
        for i,b in enumerate(bytes.fromhex(g['curve_hex']),1):
            dx,dy=CAP.decode(b);x+=dx;y+=dy;m.cpu.x=slot;call(m,'e_move_one')
            self.assertEqual(get(m,'e_xlo',slot)+256*get(m,'e_xhi',slot),x&65535)
            self.assertEqual(get(m,'e_ylo',slot)+256*get(m,'e_yhi',slot),y&65535)
            self.assertEqual(get(m,'e_cursor',slot)+256*get(m,'e_cursorhi',slot),i)
        self.assertEqual(get(m,'e_phase',slot),2)
        slot=5;delay=get(m,'e_delay',slot)+256*get(m,'e_delayhi',slot)
        self.assertEqual(delay,1260)
        for _ in range(260):m.cpu.x=slot;call(m,'e_move_one')
        self.assertEqual(get(m,'c_es',slot),5)
        self.assertEqual(get(m,'e_delay',slot)+256*get(m,'e_delayhi',slot),1000)
    def test_all_22_graphic_indices_and_frames_preserved_in_private_buffers(self):
        m=self.machine();self.transition(m,100)
        p=CAP.DATA.parse_level_record(self.records[99][1])
        # Same visible position stresses all private slots without changing original assets.
        for i,e in enumerate(p['enemies']):
            typ=self.types[self.mapping[e['graphic_type']]['vygr_type_1based']-1]
            for f,payload in enumerate(typ['frames']):
                setv(m,'gframe',f,i)
                setv(m,'e_slot',i);setv(m,'c_es',1,i)
                setv(m,'e_xlo',60,i);setv(m,'e_xhi',0,i);setv(m,'e_ylo',60,i);setv(m,'e_yhi',0,i)
                m.cpu.x=i;call(m,'e_draw_one')
                self.assertEqual(m.memory.data[0x10000+i*256+64:0x10000+i*256+192],payload)
                self.assertEqual(m.memory.data[0x10000+i*256:0x10000+i*256+64],bytes(64))
                self.assertEqual(m.memory.data[0x10000+i*256+192:0x10100+i*256],bytes(64))
    def test_level_clear_requires_all_dead_and_button_release_then_press(self):
        m=self.machine();enemies(m,0);setv(m,'a_enabled',0)
        setv(m,'c_es',5,21);call(m,'tick');self.assertEqual(get(m,'mode'),0)
        setv(m,'c_es',4,21);setv(m,'c_ef',0,21);call(m,'tick');self.assertEqual(get(m,'mode'),0)
        enemies(m,0);m.memory.data[0xdc00]=0xef
        call(m,'tick');self.assertEqual(get(m,'mode'),1)
        for _ in range(3):call(m,'tick');self.assertEqual(get(m,'number'),1)
        m.memory.data[0xdc00]=255;call(m,'tick');self.assertEqual(get(m,'button_armed'),1)
        m.memory.data[0xdc00]=0xef;call(m,'tick');self.assertEqual(get(m,'number'),2)
        self.assertEqual(get(m,'mode'),0)
        self.transition(m,100);enemies(m,0);setv(m,'a_enabled',0)
        m.memory.data[0xdc00]=255;call(m,'tick');call(m,'tick')
        m.memory.data[0xdc00]=0xef;call(m,'tick');self.assertEqual(get(m,'number'),1)
    def test_nav_limits_latch_and_gameover_restart(self):
        m=self.machine()
        def key(k,release=True):
            if release:setv(m,'nav_latch',0)
            setv(m,'r_keybyte',k);call(m,'key_filter')
        key(45);self.assertEqual(get(m,'number'),1)
        key(43);self.assertEqual(get(m,'number'),2)
        key(43,False);self.assertEqual(get(m,'number'),2)
        key(0,False);self.assertEqual(get(m,'nav_latch'),0)
        key(43,False);self.assertEqual(get(m,'number'),3)
        self.transition(m,100);key(43);self.assertEqual(get(m,'number'),100)
        key(45);self.assertEqual(get(m,'number'),99)
        setv(m,'mode',1);key(43);self.assertEqual(get(m,'number'),99)
        setv(m,'mode',0);setv(m,'c_ps',4);key(45);self.assertEqual(get(m,'number'),99)
        m.memory.data[N['high_score']:N['high_score']+4]=(76543).to_bytes(4,'little')
        m.memory.data[N['player1_score']:N['player1_score']+4]=(1234).to_bytes(4,'little')
        call(m,'restart');self.assertEqual(get(m,'number'),1)
        self.assertEqual(word(m,N['player1_score']),0);self.assertEqual(word(m,N['high_score']),76543)
        self.assertEqual(word(m,N['player1_lives'],2),3)
    def test_runtime_invalid_directory_and_index_fail_safely(self):
        m=self.machine();m.memory.data[0x40000+12:0x40000+16]=(65535).to_bytes(4,'little')
        m.cpu.a=1;call(m,'transition');self.assertEqual(m.error,7)
        m.cpu.pc=N['main_loop'];frame(m);self.assertEqual(m.cpu.pc,0x200)

    def test_independent_animation_counts_and_rom_mapping(self):
        m=self.machine();self.transition(m,100)
        initial_code=bytes(m.memory.data[0x7608:0x7800])
        for tick in range(36):
            for i in range(22):self.assertEqual(get(m,'gframe',i),tick%get(m,'gframes',i))
            call(m,'animate')
        for bits in [0x10,0x20,0x30]:
            m.memory.data[0xd030]=(m.memory.data[0xd030]&0xcf)|bits
            setv(m,'number',71);call(m,'prepare');call(m,'e_init')
            self.assertEqual(m.error,0)
            self.assertEqual(bytes(m.memory.data[0x7608:0x7800]),initial_code)
            # Existing B800 renderer requires ROMA off; new data/parser code does not.
            m.memory.data[0xd030]&=0xef
            self.transition(m,71)
            setv(m,'e_slot',0);setv(m,'c_es',1);setv(m,'e_xlo',60);setv(m,'e_xhi',0);setv(m,'e_ylo',60);setv(m,'e_yhi',0)
            m.cpu.x=0;call(m,'e_draw_one');self.assertEqual(m.error,0)
    def test_level_clear_text_position_and_frozen_gameplay(self):
        m=self.machine();enemies(m,0);setv(m,'a_enabled',0)
        call(m,'tick');self.assertEqual(get(m,'mode'),1)
        for row,x,text in [(11,152,'LEVEL CLEAR'),(13,48,'PRESS BUTTON TO CONTINUE')]:
            at=0xe000+192*row+84
            self.assertEqual(word(m,at,2),x)
            codes=m.memory.data[at+2:at+2+len(text)*2:2]
            expected=bytes(ord(c)-64 if 'A'<=c<='Z' else ord(c) for c in text)
            self.assertEqual(codes,expected)
        before=bytes(m.memory.data[0x1e00:0x1f00]);player_before=bytes(m.memory.data[0x1660:0x1678])
        m.memory.data[0xdc00]=0xfb
        for _ in range(10):call(m,'move');call(m,'objects');call(m,'tick')
        self.assertEqual(m.memory.data[0x1e00:0x1f00],before)
        self.assertEqual(m.memory.data[0x1660:0x1678],player_before)
        self.assertEqual(m.memory.data[N['p_active']:N['p_active']+6],bytes(6))
    def test_fixed_curves_for_other_levels_and_special_scheduler(self):
        m=self.machine()
        for lev in [1,2,47,71]:
            self.transition(m,lev)
            p=CAP.DATA.parse_level_record(self.records[lev-1][1])
            for i,e in enumerate(p['enemies']):
                setv(m,'e_xlo',90,i);setv(m,'e_xhi',0,i);setv(m,'e_ylo',50,i);setv(m,'e_yhi',0,i)
                m.cpu.x=i;call(m,'a_start');x,y=90,50
                curve=bytes.fromhex(p['attack_curves_hex'][e['attack_index']])
                for b in curve[:3]:
                    dx,dy=CAP.decode(b);x+=dx;y+=dy;m.cpu.x=i;call(m,'a_step')
                    self.assertEqual(get(m,'e_xlo',i),x&255);self.assertEqual(get(m,'e_ylo',i),y&255)
        for lev in [25,50,99,100]:
            self.transition(m,lev)
            for i in range(22):setv(m,'c_es',1,i);setv(m,'e_phase',3,i)
            setv(m,'a_ready',1);setv(m,'a_start_tick',0)
            for _ in range(20):call(m,'a_postframe')
            self.assertEqual(m.memory.data[N['c_es']:N['c_es']+22],bytes([1])*22)
            for key in [0x54,0x45]:
                setv(m,'r_keybyte',key);call(m,'key_filter');self.assertTrue(m.cpu.p&m.cpu.CARRY)
    def test_player_one_pixel_per_frame_and_nav_from_real_main_loop(self):
        m=self.machine()
        for _ in range(5):frame(m,buttons=0xf7)
        self.assertEqual(m.memory.data[0x1662],117);self.assertEqual(m.memory.data[0x1664],184)
        frame(m,43);self.assertEqual(get(m,'number'),2)
        frame(m,43);self.assertEqual(get(m,'number'),2)
        frame(m,0);frame(m,43);self.assertEqual(get(m,'number'),3)
        frame(m,0);frame(m,45);self.assertEqual(get(m,'number'),2)
    def test_exit_from_clear_and_second_start_restores_basic(self):
        m=self.machine();self.transition(m,71)
        enemies(m,0);setv(m,'a_enabled',0);call(m,'tick')
        self.assertEqual(get(m,'mode'),1)
        m.cpu.pc=N['main_loop'];frame(m,0x58)
        self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.memory.data[0xd05a],120)
        self.assertEqual(bytes(m.memory.colour[:2048]),bytes(m.memory.data[0x9000:0x9800]))
        m.execute(N["p_startup"])
        for _ in range(800000):
            if m.cpu.pc==N["main_loop"]:break
            m.cpu.step()
        else:self.fail("second RUN did not return")
        self.assertEqual(get(m,"number"),1)


class CombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m=start();cls.snapshot=bytes(m.memory.data);cls.colour=bytes(m.memory.colour)
    def machine(self):
        m=Machine();m.memory.data[:]=self.snapshot;m.memory.colour[:]=self.colour
        m.cpu.pc=N['main_loop'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff)
        return m
    def test_all_edges_original_graphics_and_private_crop(self):
        m=self.machine();enemies(m,0);setv(m,'c_ps',2)
        payload=GRAPHICS.graphics_types((ROOT/'assets/stage5b/VYGR.DAT').read_bytes())[14]['frames'][0]
        for x,y in [(x,y) for x in [-16,-15,-14,-3,-2,-1,0,224,225,226,237,238,239,240] for y in [-16,-15,-14,-1,0,184,185,198,199,200]]:
            target(m,0,1,x&255,y&255)
            for n,v in [('e_xlo',x&255),('e_xhi',(x>>8)&255),('e_ylo',y&255),('e_yhi',(y>>8)&255)]:setv(m,n,v)
            call(m,'e_render');self.assertEqual(fetched(m),oracle(x,y,payload),(x,y))
            self.assertEqual(get(m,'v014_overflow_count'),0)
    def test_game_over_after_complete_explosion_R_and_X(self):
        m=self.machine();enemies(m,0);setv(m,'a_enabled',0);player(m,112,184)
        m.memory.data[N['high_score']:N['high_score']+4]=(123456).to_bytes(4,'little')
        m.memory.data[N['player1_lives']:N['player1_lives']+2]=bytes([1,0])
        shot(m,2,120,190);frame(m)
        self.assertEqual(get(m,'c_ps'),1)
        for _ in range(20):frame(m);self.assertEqual(get(m,'c_ps'),1)
        frame(m);self.assertEqual(get(m,'c_ps'),4)
        for key in [43,45,32,0x54,0x45]:frame(m,key);self.assertEqual(get(m,'c_ps'),4)
        at=0xe000+9*192+84
        self.assertEqual(m.memory.data[at+2:at+20:2],bytes([7,1,13,5,32,15,22,5,18]))
        frame(m,0);frame(m,0x52)
        self.assertEqual(get(m,'number'),1);self.assertEqual(get(m,'c_ps'),0)
        self.assertEqual(word(m,N['player1_score']),0);self.assertEqual(word(m,N['high_score']),123456)
        frame(m,0x58);self.assertEqual(m.cpu.pc,0x200)
    def test_simultaneous_combat_limits_return_and_respawn(self):
        m=self.machine()
        for i in range(22):
            setv(m,'c_es',1,i);setv(m,'e_phase',3,i);setv(m,'e_xlo',get(m,'e_tx',i),i);setv(m,'e_ylo',get(m,'e_ty',i),i)
            setv(m,'e_xhi',0,i);setv(m,'e_yhi',0,i)
        setv(m,'a_ready',1);setv(m,'c_ps',3);setv(m,'c_blink',150)
        for i in range(3):m.cpu.x=i;call(m,'a_start')
        for _ in range(20):
            setv(m,'a_start_tick',1);setv(m,'p_cooldown',0)
            frame(m)
            self.assertLessEqual(sum(get(m,'c_es',i)==3 for i in range(22)),3)
            self.assertLessEqual(sum(get(m,'p_active',i) for i in range(2,6)),4)
            self.assertEqual(get(m,'v014_overflow_count'),0)
        # Ram the player, then force attack opportunities: no new launch during WAIT.
        setv(m,'c_ps',0);target(m,0,3,x=112,y=184);setv(m,'e_phase',4)
        call(m,'c_collisions');self.assertEqual(get(m,'c_ps'),1)
        for _ in range(600):
            setv(m,'a_start_tick',1);setv(m,'a_event',0)
            call(m,'a_objects');call(m,'c_timers');call(m,'c_wait')
            self.assertNotEqual(get(m,'a_event'),1)
            if get(m,'c_ps')==3:break
        else:self.fail('respawn stalled')
        before=m.memory.data[0x1662];m.memory.data[0xdc00]=0xf7;call(m,'c_move')
        self.assertEqual(m.memory.data[0x1662],before+1);self.assertEqual(m.memory.data[0x1664],184)
        self.assertEqual(get(m,'c_blink'),150)
    def test_renderer_frame_budget_and_maximum_row_load(self):
        m=self.machine();setv(m,'c_ps',2)
        cycles=[]
        for x,y in [(60,0),(60,60),(60,184),(60,185),(60,195),(-1,60),(239,60)]:
            for i in range(22):
                target(m,i,1,x=x&255,y=y)
                setv(m,"e_xhi",(x>>8)&255,i)
            before=m.cpu.processorCycles;call(m,'e_render');cycles.append(m.cpu.processorCycles-before)
            self.assertEqual(get(m,'v014_overflow_count'),0)
            self.assertLessEqual(max(m.memory.data[N['v014_row_count']:N['v014_row_count']+25]),24)
        self.assertLess(max(cycles),800000)
        print('Stage5a worst22-pixie renderer model cycles:',max(cycles),'full/clipped:',cycles)

    def test_entry_fire_visibility_signed_muzzle_pool_and_fixed_target(self):
        m=self.machine();self.assertEqual(get(m,'a_ready'),0)
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

    def test_stable4c_entry_formation_402_updates_identical(self):
        import subprocess,sys
        stable=json.loads(subprocess.check_output([sys.executable,str(ROOT/'tests/stage4c_entry_reference.py')],cwd=ROOT,text=True))
        m=self.machine()
        fields=['c_es','e_xlo','e_xhi','e_ylo','e_yhi','e_tx','e_ty','e_delay','e_cursor','e_group','e_phase','e_timer','a_index']
        for tick,expected in enumerate(stable):
            setv(m,'a_start_tick',255);call(m,'a_objects')
            actual=[[get(m,n,i) for i in range(22)] for n in fields]+[[get(m,n) for n in ['a_offset','a_ready','a_form_tick','a_direction']]]
            self.assertEqual(actual,expected,tick+1)
        self.assertEqual(get(m,'a_ready'),1)
    def test_return_tracks_current_drifting_slot(self):
        m=self.machine();enemies(m);target(m,0,2,x=210,y=0)
        setv(m,'e_phase',2);setv(m,'e_ylo',240);setv(m,'e_yhi',255)
        setv(m,'a_ready',1);setv(m,'a_form_tick',1);offsets=set()
        for _ in range(220):
            setv(m,'a_start_tick',255);call(m,'a_objects')
            offset=get(m,'a_offset');offset=offset-256 if offset>=128 else offset;offsets.add(offset)
            if get(m,'c_es')==1:break
        self.assertIn(-8,offsets);self.assertIn(8,offsets)
        self.assertEqual(get(m,'c_es'),1)
        self.assertEqual(get(m,'e_xlo'),get(m,'e_tx')+offset)
        self.assertEqual(get(m,'e_ylo'),get(m,'e_ty'))

# Retain the assembled collision/explosion/score regressions; no mirrored algorithms.
for name in ['test_four_enemy_shots_one_life_player_frozen','test_ram_two_explosions_no_points_and_invulnerability',
             'test_independent_frames_complete_and_guards_render','test_wait_real_states_blink_exact_150_25_and_no_fire',
             'test_points_formula_carry_saturation_and_display','test_hitbox_touching_and_playfield_edges']:
    setattr(CombatTests,name,getattr(PREV.CollisionTests,name))

if __name__=='__main__':unittest.main()
