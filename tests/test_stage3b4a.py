"""Assembled HUD tests. CPU/DMA/SEAM raster models, not a full XEMU run."""
import os
from pathlib import Path
import sys
import unittest
import test_stage3b3 as PREVIOUS
import test_stage3b2_exit as EXIT
sys.path.insert(0,str(PREVIOUS.R.ROOT/'tools'))
import build_stage3b4a as BUILD
ARTIFACTS=PREVIOUS.R.ROOT/'releases/stage_3b4a'
NAMES=BUILD.symbols((ARTIFACTS/'STAGE3B4A.sym').read_text())

class Memory(PREVIOUS.PaletteMemory):
    def __init__(self,base):
        super().__init__(base)
        self.char_wom=bytes((i*37+i//8)&255 for i in range(8192))
        self.screen_writes=[]
        self.colour=bytearray(self.data[0xd800:0xe000])+bytearray([0xa5])*0x7800
    def __getitem__(self,a):
        if 0xff80000<=a<0xff88000: return self.colour[a-0xff80000]
        if 0xd800<=a<0xdc00 or 0xdc00<=a<0xe000 and self.data[0xd030]&1:
            return self.colour[a-0xd800]
        return super().__getitem__(a)
    def __setitem__(self,a,v):
        if 0xff80000<=a<0xff88000:
            self.colour[a-0xff80000]=v
            return
        if 0xd800<=a<0xdc00 or 0xdc00<=a<0xe000 and self.data[0xd030]&1:
            self.colour[a-0xd800]=v
            return
        if 0x5000<=a<0x5c80: self.screen_writes.append(a)
        pointer=self.data[0xd701]*256+v if a==0xd705 else -1
        if pointer in (NAMES['font_dma'],NAMES['colour_backup_dma'],NAMES['colour_restore_dma'],NAMES['clear_dma']):
            self.data[a]=v
            p=pointer; source_mb=target_mb=0
            while self.data[p]:
                opt=self.data[p]; p+=1
                if opt in (0x80,0x81):
                    if opt==0x80: source_mb=self.data[p]
                    else: target_mb=self.data[p]
                    p+=1
                else: assert opt==0x0a
            p+=1; d=self.data[p:p+11]
            assert d[0]==0 and d[9:11]==b'\x00\x00'
            count=int.from_bytes(d[1:3],'little')
            source=int.from_bytes(d[3:6],'little')+(source_mb<<20)
            target=int.from_bytes(d[6:9],'little')+(target_mb<<20)
            if 0xff7e000<=source<0xff80000:
                payload=self.char_wom[source-0xff7e000:source-0xff7e000+count]
            else: payload=bytes(self[source+i] for i in range(count))
            for i,value in enumerate(payload): self[target+i]=value
            self.base.transfers.append((source,target,count))
            return
        super().__setitem__(a,v)

class CPU(PREVIOUS.R.LEGACY.MPU):
    """Narrow 45GS02 adapter for the real long Color-RAM stores, not pixel output."""
    def __init__(self,**kw):
        super().__init__(**kw)
        self.b=self.z=0; self.eom=False
    def step(self):
        opcode=self.memory[self.pc]
        if opcode in (0x4b,0x5b,0x6b,0x7b):
            if opcode==0x4b: self.z=self.a
            elif opcode==0x5b: self.b=self.a
            elif opcode==0x6b: self.a=self.z
            elif opcode==0x7b: self.a=self.b
            # TAB sets B without changing status; other transfers set N/Z.
            if opcode!=0x5b: self.FlagsNZ(self.a if opcode in (0x6b,0x7b) else self.z)
            self.pc+=1; self.processorCycles+=2; self.eom=False
            return self
        if opcode==0xea and self.memory[(self.pc+1)&65535]==0x92:
            self.eom=True; self.pc+=1; self.processorCycles+=2; return self
        if opcode==0x92:
            assert self.eom
            assert self.p&self.INTERRUPT, 'IRQ must be masked with temporary base page'
            pointer=self.b*256+self.memory[self.pc+1]
            address=sum(self.memory[pointer+i]<<(i*8) for i in range(4))+self.z
            self.memory[address]=self.a
            self.eom=False; self.pc+=2; self.processorCycles+=8; return self
        self.eom=False
        return super().step()

class Machine(PREVIOUS.Machine):
    def __init__(self):
        super().__init__()
        prg=(ARTIFACTS/'STAGE3B4A.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(prg)-2]=prg[2:]
        self.memory=Memory(self.memory.base)
        previous=self.cpu
        self.cpu=CPU(memory=self.memory,pc=NAMES['startup'])
        self.cpu.p=previous.p; self.cpu.sp=previous.sp
        for a,v in {0xd068:0,0xd069:0x10,0xd06a:0,0xd05a:120,0xd031:0x80,0xd030:0,0xd070:0,0xd060:0,0xd061:8,0xd062:0,0xd063:0}.items():
            self.memory.data[a]=v
        self.before=bytes(self.memory.data)
        self.cleared=False

    def trap(self):
        if self.cpu.pc==0xffd2 and self.cpu.a==0x93:
            # Clear-screen KERNAL command before loader. It runs with BASIC VIC state.
            self.assert_basic_video=(self.memory.data[0xd060:0xd063]==b'\x00\x08\x00')
            self.memory.data[0x800:0xfd0]=b' '*2000
            assert self.assert_basic_video
            assert self.memory.data[0xd021]==0
            self.cleared=True
        super().trap()


def begin(m):
    m.cpu.pc=0x2100; m.cpu.sp=0xfd; m.cpu.stPushWord(0x01ff)
    for _ in range(200_000):
        if m.cpu.pc==NAMES['main_loop']: return
        m.cpu.step()
    raise AssertionError('Initialization failed')

def frame(m,key=0,buttons=255):
    m.memory.data[0xdc00]=buttons
    for i in range(100_000):
        if i and m.cpu.pc in (NAMES['main_loop'],0x0200): return
        if m.cpu.pc==0xffe4:
            m.cpu.a=key; m.cpu.pc=m.cpu.stPopWord()+1
        else: m.cpu.step()
    raise AssertionError('Frame failed')

def call(m,name):
    m.cpu.pc=NAMES[name]; m.cpu.sp=0xfd; m.cpu.stPushWord(0x01ff)
    for _ in range(100_000):
        if m.cpu.pc==0x0200: return
        m.cpu.step()
    raise AssertionError('HUD call failed: '+name)

def number(m,row,column,length):
    at=0x5000+row*128+42+2+column*2
    return ''.join(chr(c+64 if 1<=c<=26 else c) for c in m.memory.data[at:at+length*2:2])

def hud_pixels(m,previous=None):
    """All 64 SEAM entries. Implements XEMU SEAM fetch and transparency.

    Returns palette index per native H640 pixel, with the original 2x glyph width.
    Monochrome text uses all eight columns; only frame cells are trimmed.
    NCM symbols use all 16 columns.
    """
    result=[list(row) for row in previous] if previous is not None else [[0]*640 for _ in range(200)]
    for y in range(200):
        row=y//8; sub=y%8; x=0; offset=0; transparent=False
        for e in range(64):
            at=row*128+e*2
            word=int.from_bytes(m.memory.data[0x5000+at:0x5002+at],'little')
            attrs=int.from_bytes(m.memory.colour[at:at+2],'big')
            if attrs&0x1000:
                x=word&0x3ff; offset=(word>>13)&7
                if word&0x1000: offset=-offset
                transparent=bool(attrs&0x8000)
                continue
            glyph=word&0x1fff
            if attrs&0x800:
                width=16-(word>>13)
                for cx in range(width):
                    b=m.memory.data[glyph*64+(sub+offset)*8+cx//2]
                    colour=(b>>(4*(cx%2)))&15
                    for _ in range(2):
                        if x<640 and (colour or not transparent): result[y][x]=colour
                        x+=1
            else:
                byte=m.memory.data[0x4000+glyph*8+sub]
                for cx in range(8-(word>>13)):
                    colour=attrs&15 if byte&(0x80>>cx) else 0
                    for _ in range(2):
                        if x<640: result[y][x]=colour
                        x+=1
    return result

class HUDTests(unittest.TestCase):
    def start(self):
        m=Machine().execute(); self.assertEqual(m.error,0); begin(m); return m

    def test_build_original_data_and_bounded_patches(self):
        prg=(ARTIFACTS/'STAGE3B4A.PRG').read_bytes()
        BUILD.verify_engine(prg,NAMES)
        entries=[('STAGE3B4A',prg,0x82)]+[(n,(BUILD.ROOT/'assets'/n).read_bytes(),0x81) for n in ('VYLV.DAT','VYGR.DAT')]
        BUILD.BASE.verify_disk((ARTIFACTS/'VYPER_STAGE3B4A.d81').read_bytes(),entries)
        m=self.start()
        self.assertEqual(m.memory.data[0x40000:0x53f81],(BUILD.ROOT/'assets/VYLV.DAT').read_bytes())
        self.assertEqual(m.memory.data[0x54000:0x5b8a8],(BUILD.ROOT/'assets/VYGR.DAT').read_bytes())
        self.assertEqual(m.memory.data[0xc840:0xc8c0],(BUILD.ROOT/'assets/player/player_ncm.bin').read_bytes())
        self.assertEqual(m.memory.data[NAMES['player2_active']],0)
        self.assertTrue(m.cleared)

    def test_initial_values_font_and_palette_isolation(self):
        m=self.start()
        for row,column,length,expected in [(1,2,7,'0000000'),(4,2,7,'0000000'),(5,7,3,'001'),(22,7,3,'100'),(24,7,3,'115')]:
            self.assertEqual(number(m,row,column,length),expected)
        for row in (0,1,3,4,5,14,15,16,18,19,20,21,22,24):
            column,length=1,9
            text=number(m,row,column,length).strip()
            self.assertEqual(text,BUILD.LABELS[row][0])
            prefix=0x5000+row*128+44
            for column in (0,10):
                self.assertEqual(int.from_bytes(m.memory.data[prefix+column*2:prefix+column*2+2],'little'),0x8080)
        self.assertEqual(m.memory.data[0xd05a],60)
        self.assertTrue(m.memory.data[0xd031]&128)
        for code,bitmap in BUILD.thin_font().items():
            self.assertEqual(m.memory.data[0x4000+code*8:0x4008+code*8],bitmap)
        # Thin H has separated one-pixel stems and a single-row crossbar.
        self.assertEqual(m.memory.data[0x4040:0x4048],bytes([0x44,0x44,0x44,0x7c,0x44,0x44,0x44,0]))
        self.assertEqual(m.memory.primary_palette(),tuple(tuple(m.memory.banks[1][c][i] for c in range(3)) for i in range(256)))
        for c in range(3): self.assertEqual(m.memory.banks[3][c],bytearray([3*41+c]*256))
        palette=[(BUILD.ROOT/'assets/player'/f'player_palette_{c}.bin').read_bytes() for c in 'rgb']
        for c in range(3): self.assertEqual(m.memory.banks[2][c][1:9],palette[c][1:9])
        self.assertTrue(all(m.memory.banks[2][c][0]==0 for c in range(3)))

    def test_eight_lives_exact_original_pixels_spacing_clamp_and_no_sprites(self):
        m=self.start()
        pixels=[[int(c,16) for c in line] for line in (BUILD.ROOT/'assets/player/player_pixels.txt').read_text().splitlines()]
        for lives in (0,3,4,5,8,9,256,65535):
            m.memory.data[NAMES['player1_lives']:NAMES['player1_lives']+2]=lives.to_bytes(2,'little')
            call(m,'hud_update_lives')
            raster=hud_pixels(m)
            for slot in range(8):
                x=490+(slot%4)*34; y=58+(slot//4)*17
                for yy in range(16):
                    expected=[v for v in pixels[yy] for _ in range(2)] if slot<min(lives,8) else [0]*32
                    self.assertEqual(raster[y+yy][x:x+32],expected,(lives,slot,yy))
            # The full gap row between ships and full one-pixel column gaps stay black.
            self.assertEqual(raster[74][490:624],[0]*134)
            self.assertTrue(all(raster[y][x]==0 for y in range(58,91) for x in (522,523,556,557,590,591)))
            self.assertEqual(m.memory.data[0xd015],0)
            self.assertEqual(int.from_bytes(m.memory.data[NAMES['player1_lives']:NAMES['player1_lives']+2],'little'),lives)

    def test_32bit_scores_dynamic_values_and_no_unchanged_screen_writes(self):
        m=self.start()
        for score in (0,1,1234567,10000000,4294967295):
            m.memory.data[NAMES['player1_score']:NAMES['player1_score']+4]=score.to_bytes(4,'little')
            call(m,'hud_update_score')
            self.assertEqual(number(m,4,2,7),f'{score%10000000:07d}')
            self.assertEqual(int.from_bytes(m.memory.data[NAMES['player1_score']:NAMES['player1_score']+4],'little'),score)
        m.memory.screen_writes.clear()
        for name in ('hud_update_score','hud_update_level','hud_update_lives','hud_update_points'): call(m,name)
        self.assertEqual(m.memory.screen_writes,[])
        m.memory.data[NAMES['player1_level']:NAMES['player1_level']+2]=(999).to_bytes(2,'little')
        call(m,'hud_update_level'); self.assertEqual(number(m,5,7,3),'999')

    def test_motion_rendering_prefix_survives_clearing_and_player2_keys_inactive(self):
        old=PREVIOUS.Machine().execute(); PREVIOUS.begin(old)
        new=self.start()
        prefix=[bytes(new.memory.data[0x5000+r*128:0x5000+r*128+84]) for r in range(25)]
        initial_hud=[row[480:] for row in hud_pixels(new)]
        new_start=new.cpu.processorCycles; old_start=old.cpu.processorCycles
        for i in range(56):
            key=[0,0x20,0x2b,0x2d,0x50,0x53][i%6]; buttons=[255,251,247,254,253][i%5]
            PREVIOUS.frame(old,key,buttons); frame(new,key,buttons)
            self.assertEqual(new.memory.data[0x1600:0x1900],old.memory.data[0x1600:0x1900])
            self.assertEqual(new.memory.data[NAMES['s2i_phase']:NAMES['s2i_phase']+22],old.memory.data[PREVIOUS.NAMES['s2i_phase']:PREVIOUS.NAMES['s2i_phase']+22])
            self.assertLessEqual(max(new.memory.data[NAMES['s2i_x']:NAMES['s2i_x']+22])+16,240)
            for row in range(25): self.assertEqual(bytes(new.memory.data[0x5000+row*128:0x5000+row*128+84]),prefix[row])
            for row in range(2,23):
                count=new.memory.data[NAMES['v014_row_count']+row]
                for slot in range(count):
                    at=0x5000+row*128+84+slot*4
                    old_at=0x5000+row*80+42+slot*4
                    self.assertEqual(int.from_bytes(new.memory.data[at:at+2],'little')&1023,old.memory.data[old_at]*2)
                    self.assertEqual(new.memory.data[at+2:at+4],old.memory.data[old_at+2:old_at+4])
            self.assertEqual(new.memory.data[NAMES['player2_active']],0)
            for name in ('s2ja_frame','anim_tick','anim_speed','anim_paused',*[f'v010_frame_{n}' for n in range(1,7)]):
                self.assertEqual(new.memory.data[NAMES[name]],old.memory.data[PREVIOUS.NAMES[name]])
            for lo,hi in ((0xc840,0xc8c0),(0xc900,0xca00),(0x9800,0x9900)):
                self.assertEqual(new.memory.data[lo:hi],old.memory.data[lo:hi])
        self.assertEqual([row[480:] for row in hud_pixels(new)],initial_hud)
        # Preserve 50Hz wait logic. Report model cycle overhead, no real-time claim.
        print('Stage3b4a model mean extra CPU cycles/frame:',(new.cpu.processorCycles-new_start-old.cpu.processorCycles+old_start)/56)

    def test_exit_registers_color_cursor_rom_palette_and_restart(self):
        m=Machine()
        m.memory.colour[0x800:0xc80]=bytes((i*53)&255 for i in range(1152))
        m.execute()
        addresses=(0xd020,0xd021,0xd030,0xd031,0xd054,0xd05a,0xd05d,0xd058,0xd059,0xd05e,0xd060,0xd061,0xd062,0xd063,0xd064,0xd065,0xd068,0xd069,0xd06a,0xd07b,0xd070)
        before={a:m.memory.data[a] for a in addresses}; before[0xd021]=m.before[0xd021]; colour=bytes(m.memory.colour[:3200]); cursor=bytes(m.memory.data[0x1000:0x1600]); palette=m.memory.primary_palette()
        for _ in range(2):
            begin(m); frame(m,0x58)
            self.assertEqual(m.cpu.pc,0x0200)
            self.assertEqual({a:m.memory.data[a] for a in addresses},before)
            self.assertEqual(bytes(m.memory.colour[:3200]),colour)
            self.assertEqual(bytes(m.memory.data[0x1000:0x1600]),cursor)
            self.assertEqual(m.memory.primary_palette(),palette)
        rom=os.environ.get('MEGA65_ROM')
        if rom:
            data=Path(rom).read_bytes()
            self.assertEqual(EXIT.hashlib.sha256(data).hexdigest(),EXIT.ROM_SHA)
            # Real ROM routine still runs against the protected cursor state.
            for a,v in {0x111f:0,0x1120:0,0x1121:0x20,0x1122:1,0x1123:0}.items(): m.memory.data[a]=v
            EXIT.blink(m,data)

    def test_runtime_dma_error_restores_scale_and_existing_exit(self):
        m=self.start()
        original_scale=m.memory.data[0x1a49]
        m.memory.base.corrupt_dma=True
        m.cpu.pc=NAMES['animate']; m.cpu.sp=0xfd
        m.cpu.stPushWord(0x01ff); m.cpu.stPushWord(0x22a7)
        m.execute()
        self.assertEqual(m.error,4)
        self.assertEqual(m.cpu.pc,0x0200)
        self.assertEqual(m.memory.data[0xd05a],original_scale)
        self.assertEqual(bytes(m.memory.data[0x1000:0x1600]),m.before[0x1000:0x1600])

    def test_persistent_framebuffer_rejects_missing_background_and_erases_tracks(self):
        m=self.start()
        self.assertTrue(m.cleared)
        # XEMU retains pixels skipped by GOTOX or transparent zero nibbles.
        stale=[[6]*640 for _ in range(200)]
        raster=hud_pixels(m,stale)
        self.assertEqual(raster,hud_pixels(m))
        for i in range(12):
            frame(m,buttons=(251,247,254,253)[i%4])
            raster=hud_pixels(m,raster)
            self.assertEqual(raster,hud_pixels(m),i)
        # Reproduce the omitted-background defect. Blue history survives.
        for entry in range(21):
            at=entry*2
            m.memory.data[0x5000+at:0x5002+at]=(640).to_bytes(2,'little')
            m.memory.colour[at:at+2]=b'\x10\x00'
        broken=hud_pixels(m,stale)
        self.assertNotEqual(broken,raster)
        self.assertEqual(broken[0][:480],[6]*480)

    def test_long_store_preserves_base_z_flags_and_zero_page(self):
        m=self.start()
        m.memory.data[0x1a60:0x1a64]=(0xff80800).to_bytes(4,'little')
        m.cpu.a=13; m.cpu.x=17; m.cpu.y=22; m.cpu.b=0x35; m.cpu.z=0x99; m.cpu.p=0x35
        zero_page=bytes(m.memory.data[:256])
        call(m,'long_colour_store')
        self.assertEqual(m.memory[0xff80816],13)
        self.assertEqual((m.cpu.a,m.cpu.x,m.cpu.y,m.cpu.b,m.cpu.z,m.cpu.p),(13,17,22,0x35,0x99,0x35))
        self.assertEqual(bytes(m.memory.data[:256]),zero_page)

    def test_startup_load_failure_restores_basic_background(self):
        m=Machine(); before=m.memory.data[0xd021]
        m.fault='open'
        m.execute()
        self.assertTrue(m.cleared)
        self.assertNotEqual(m.error,0)
        self.assertEqual(m.cpu.pc,0x0200)
        self.assertEqual(m.memory.data[0xd021],before)
        self.assertEqual(m.memory.data[0xd05a],120)
        self.assertFalse(m.active)

    def test_font_aliases_and_direct_saved_charset(self):
        for high,bank,expected in ((0x10,0,0xff7e000),(0x18,0,0xff7e800),(0x90,0,0xff7e000),(0x98,0,0xff7e800),(0x10,2,0x21000)):
            m=Machine()
            m.memory.data[NAMES['saved_d068']]=0
            m.memory.data[NAMES['saved_d069']]=high
            m.memory.data[NAMES['saved_d06a']]=bank
            call(m,'hud_copy_font')
            self.assertEqual(m.memory.base.transfers[-1],(expected,0x4000,2048))

if __name__=='__main__': unittest.main()
