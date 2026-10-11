"""Assembled A/B/C projection, stable trajectory and unchanged combat consumers."""
import json,random,unittest
from pathlib import Path
import test_stage5d1a as TITLE
OLD=TITLE.OLD
import analyze_stage3b2_data as DATA
from analyze_attack_descriptors import decode
class DIAG:
    DATA=DATA
    decode=staticmethod(decode)
    transform=staticmethod(lambda y,v:y-16)
ROOT=OLD.ROOT
ART=ROOT/'releases/stage_5d_1_b2'
STABLE_N=OLD.N
N=STABLE_N

def bind(n):
    global N
    N=n;OLD.N=n;OLD.T.N=n;OLD.T.PREV.N=n

def call(m,name):
    m.cpu.pc=N[name];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff)
    for _ in range(2000000):
        if m.cpu.pc==0x200:return
        m.cpu.step()
    raise AssertionError(name)
def val(m,name,i=0):return m.memory.data[N[name]+i]
def put(m,name,v,i=0):m.memory.data[N[name]+i]=v&255
def word(m,lo,hi,i=0):return int.from_bytes(bytes([val(m,lo,i),val(m,hi,i)]),'little',signed=True)
def pos(m,lo,hi,v,i=0):put(m,lo,v,i);put(m,hi,v>>8,i)

class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boots={};cls.symbols={}
        for v in 'B':
            n=OLD.T.BUILD.symbols((ART/f'STAGE5D1A.sym').read_text());bind(n)
            m=OLD.Machine();p=(ART/f'STAGE5D1A.PRG').read_bytes();m.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
            m.cpu.pc=n['p_startup'];m.execute()
            assert m.error==0 and m.closed==4
            for _ in range(2000000):
                if m.cpu.pc==n['main_loop']:break
                m.cpu.step()
            else:raise AssertionError('boot')
            cls.boots[v]=m;cls.symbols[v]=n
    def machine(self,v):
        bind(self.symbols[v]);b=self.boots[v];m=OLD.Machine();m.memory.data[:]=b.memory.data;m.memory.colour[:]=b.memory.colour
        for i,bank in enumerate(b.memory.banks):
            for j,c in enumerate(bank):m.memory.banks[i][j][:]=c
        m.cpu.pc=N['main_loop'];return m
    def test_signed_transform_boundaries_and_negative_rounding(self):
        values=sorted(set([-32768,-32767,-1024,-233,-232,-231,-30,-29,-28,-17,-16,-15,-1,0,1,15,16,28,29,30,199,200,231,232,233,32767]+list(range(-300,350))))
        for v in 'B':
            m=self.machine(v)
            for y in values:
                if v=='B' and y<-32752:continue
                m.cpu.a=y&255;m.cpu.y=(y>>8)&255;m.cpu.x=17;call(m,'transform')
                result=int.from_bytes(bytes([m.cpu.a,m.cpu.y]),'little',signed=True)
                self.assertEqual(result,DIAG.transform(y,v),(v,y));self.assertEqual(m.cpu.x,17)
    def test_projection_restore_states_and_explosion_hit_position(self):
        for v in 'B':
            m=self.machine(v);put(m,'a_enabled',0);call(m,'clear')
            for i,(state,phase) in enumerate([(2,1),(2,2),(1,3),(3,4),(5,0),(4,1)]):
                put(m,'c_es',state,i);put(m,'e_phase',phase,i);pos(m,'e_ylo','e_yhi',199,i)
            call(m,'postframe')
            for i in range(6):self.assertEqual(word(m,'e_ylo','e_yhi',i),DIAG.transform(199,v) if i==0 else 199)
            call(m,'restore');self.assertEqual(word(m,'e_ylo','e_yhi'),199)
            call(m,'postframe');put(m,'c_es',4);call(m,'restore')
            self.assertEqual(word(m,'e_ylo','e_yhi'),DIAG.transform(199,v))
            call(m,'clear');self.assertFalse(any(m.memory.data[N['projected']:N['projected']+22]))
    def test_actual_original_entry_points_levels1_2_3(self):
        records=DIAG.DATA.level_records((ROOT/'assets/VYLV.DAT').read_bytes())
        for v in 'B':
            m=self.machine(v)
            for level in (1,2,3):
                m.cpu.a=level;call(m,'transition');put(m,'a_enabled',0)
                p=DIAG.DATA.parse_level_record(records[level-1][1])
                for gidx,g in enumerate(p['groups']):
                    call(m,'clear')
                    for i in range(22):put(m,'c_es',0,i)
                    put(m,'c_es',5);put(m,'e_group',gidx);put(m,'e_delay',0);put(m,'e_delayhi',0);put(m,'e_cursor',0);put(m,'e_cursorhi',0);put(m,'e_timer',0);put(m,'e_visible',0)
                    m.cpu.x=0;call(m,'e_move_one');call(m,'postframe')
                    x,y=g['start_x'],g['start_y']
                    self.assertEqual(word(m,'e_ylo','e_yhi'),DIAG.transform(y,v))
                    curve=bytes.fromhex(g['curve_hex'])
                    for j,b in enumerate(curve):
                        call(m,'restore');m.cpu.x=0;call(m,'e_move_one');call(m,'postframe')
                        dx,dy=DIAG.decode(b);x+=dx;y+=dy
                        expected=DIAG.transform(y-dy,v) if j==len(curve)-1 else DIAG.transform(y,v)
                        self.assertEqual(word(m,'e_xlo','e_xhi'),x-dx if j==len(curve)-1 else x,(v,level,gidx,j))
                        self.assertEqual(word(m,'e_ylo','e_yhi'),expected,(v,level,gidx,j))
                        self.assertEqual(val(m,'e_cursor')+val(m,'e_cursorhi')*256,j+1)
    def test_visible_collision_boxes_and_hidden_wait(self):
        for v in 'B':
            m=self.machine(v);put(m,'a_enabled',0);call(m,'clear');put(m,'c_es',2);put(m,'e_phase',1);put(m,'e_visible',1);pos(m,'e_xlo','e_xhi',104);pos(m,'e_ylo','e_yhi',190)
            call(m,'postframe');m.cpu.x=0;call(m,'e_collision_box')
            y=DIAG.transform(190,v);self.assertEqual(val(m,'c_by'),min(200,max(0,y+2)))
            self.assertEqual(val(m,'c_bb'),min(200,max(0,y+14)))
            put(m,'c_es',5);m.cpu.x=0;call(m,'e_collision_box');self.assertEqual(val(m,'c_by'),val(m,'c_bb'))
    def test_actual_rrb_pixels_follow_projected_y_and_clipping(self):
        import extract_stage5b_graphics as G
        payload=G.graphics_types((ROOT/'assets/stage5b/VYGR.DAT').read_bytes())[14]['frames'][0]
        for v in 'B':
            m=self.machine(v);put(m,'a_enabled',0);put(m,'c_ps',2)
            for i in range(22):put(m,'c_es',0,i)
            put(m,'c_es',2);put(m,'e_phase',1);put(m,'e_visible',1);put(m,'gframe',0)
            pos(m,'e_xlo','e_xhi',104)
            for y in (-20,-1,0,15,184,190,199,216):
                call(m,'clear');pos(m,'e_ylo','e_yhi',y);call(m,'postframe');call(m,'e_render')
                self.assertEqual(OLD.T.fetched(m),OLD.T.oracle(104,DIAG.transform(y,v),payload),(v,y))
                self.assertEqual(val(m,'v014_overflow_count'),0)

    def test_entry_shot_origin_visible_target_four_limit_and_wait(self):
        for v in 'B':
            m=self.machine(v);put(m,'a_enabled',0);call(m,'clear')
            put(m,'c_es',2);put(m,'e_phase',1);put(m,'e_visible',1);pos(m,'e_xlo','e_xhi',104);pos(m,'e_ylo','e_yhi',100)
            call(m,'postframe');put(m,'p_random_lo',0);put(m,'p_random_hi',0)
            for i in range(6):put(m,'p_active',0,i)
            for _ in range(5):
                put(m,'p_cooldown',0);call(m,'a_fire')
            self.assertEqual(sum(val(m,'p_active',i) for i in range(2,6)),4)
            for i in range(2,6):
                self.assertEqual(val(m,'p_ypos',i),DIAG.transform(100,v)+16)
                self.assertEqual(val(m,'p_xpos',i),112)
                self.assertEqual(val(m,'p_target_y',i),184)
            for i in range(2,6):put(m,'p_active',0,i)
            put(m,'c_es',5);put(m,'p_cooldown',0);call(m,'a_fire')
            self.assertFalse(any(val(m,'p_active',i) for i in range(2,6)))


    def test_exit_and_second_RUN_each_independent_build(self):
        for v in 'B':
            m=self.machine(v);m.cpu.pc=N['main_loop'];OLD.T.frame(m,0x58)
            self.assertEqual(m.cpu.pc,0x200)
            m.execute(N['p_startup']);self.assertEqual(m.error,0)
            for _ in range(2000000):
                if m.cpu.pc==N['main_loop']:break
                m.cpu.step()
            else:self.fail('second RUN '+v)
            self.assertEqual(val(m,'number'),1)
            self.assertFalse(any(m.memory.data[N['projected']:N['projected']+22]))

    def test_transitions_all_enemies_levels_1_2_3(self):
        traces=[]
        for level in (1,2,3):
            m=self.machine('B');m.cpu.a=level;call(m,'transition');put(m,'a_enabled',0)
            seen=set();finished=set()
            for frame in range(1800):
                before=[(val(m,'e_phase',i),word(m,'e_xlo','e_xhi',i),word(m,'e_ylo','e_yhi',i)) for i in range(22)]
                call(m,'a_objects')
                for i,(phase,x,y) in enumerate(before):
                    after=(word(m,'e_xlo','e_xhi',i),word(m,'e_ylo','e_yhi',i));p=val(m,'e_phase',i)
                    if phase==1 and p==2:
                        self.assertEqual(after,(x,y));seen.add(i)
                        traces.append({'level':level,'enemy':i,'frame':frame,'event':'ENTRY_RETURN','logical_before':[x,word(m,'logical_lo','logical_hi',i)],'visible_before':[x,y],'visible_after':after,'target':[val(m,'e_tx',i)+val(m,'a_offset'),val(m,'e_ty',i)]})
                    if phase==2:
                        self.assertLessEqual(abs(after[0]-x),1);self.assertLessEqual(abs(after[1]-y),1)
                        if p==3:
                            self.assertEqual(after[1],val(m,'e_ty',i));finished.add(i)
                            traces.append({'level':level,'enemy':i,'frame':frame,'event':'RETURN_FORMATION','before':[x,y],'after':after})
                if seen and finished==seen and all(val(m,'c_es',i)!=5 for i in range(22)):break
            expected=20 if level==3 else 22
            self.assertEqual(len(seen),expected);self.assertEqual(finished,seen)
        (ART/'transition-traces.json').write_text(json.dumps(traces,indent=2)+'\n')


