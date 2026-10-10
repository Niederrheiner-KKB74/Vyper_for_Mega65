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
        # Arbitrary font bytes exercise all pairs; no ROM data is distributed.
        self.char_wom=bytes((i*37+i//8)&255 for i in range(8192))
        self.screen_writes=[]
    def __setitem__(self,a,v):
        if 0x5000<=a<0x57d0: self.screen_writes.append(a)
        if a==0xd705 and self.data[0xd701]*256+v==NAMES['font_dma']:
            self.data[a]=v
            p=NAMES['font_dma']; d=self.data[p:p+15]
            assert d[0]==0x80 and d[2:5]==b'\x0a\x00\x00'
            assert d[5:7]==b'\x00\x08' and d[10:15]==b'\x00\x40\x00\x00\x00'
            src=int.from_bytes(d[7:10],'little')+(d[1]<<20)
            if 0xff7e000<=src<=0xff7f800:
                payload=self.char_wom[src-0xff7e000:src-0xff7e000+2048]
            else:
                assert src+2048<=len(self.data)
                payload=self.data[src:src+2048]
            self.data[0x4000:0x4800]=payload
            self.base.transfers.append((src,0x4000,2048))
            return
        super().__setitem__(a,v)

class Machine(PREVIOUS.Machine):
    def __init__(self):
        super().__init__()
        prg=(ARTIFACTS/'STAGE3B4A.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(prg)-2]=prg[2:]
        self.memory=Memory(self.memory.base)
        self.cpu.memory=self.memory
        for a,v in {0xd068:0,0xd069:0x10,0xd06a:0,0xd05a:120,0xd031:0x20,0xd030:0,0xd070:0}.items():
            self.memory.data[a]=v
        self.before=bytes(self.memory.data)


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
    at=0x5000+row*80+2+column*2
    return ''.join(chr(c+64 if 1<=c<=26 else c) for c in m.memory.data[at:at+length*2:2])

def hud_pixels(m):
    """All 40 SEAM entries. Implements XEMU SEAM fetch and transparency.

    Returns palette index per native H640 pixel, with the original 2x glyph width.
    Monochrome UI uses four-column trimming; NCM symbols use all 16 columns.
    """
    result=[[0]*640 for _ in range(200)]
    for y in range(200):
        row=y//8; sub=y%8; x=0; offset=0; transparent=False
        for e in range(40):
            at=row*80+e*2
            word=int.from_bytes(m.memory.data[0x5000+at:0x5002+at],'little')
            attrs=int.from_bytes(m.memory.data[0xd800+at:0xd802+at],'big')
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

    def test_initial_values_font_and_palette_isolation(self):
        m=self.start()
        for row,column,length,expected in [(1,6,7,'0000000'),(4,6,7,'0000000'),(5,11,3,'001'),(23,13,3,'100'),(24,11,3,'115')]:
            self.assertEqual(number(m,row,column,length),expected)
        for row in (0,1,3,4,5,14,15,16,18,19,20,21,23,24):
            text=number(m,row,1,17).strip()
            self.assertEqual(text,BUILD.LABELS[row][0])
        self.assertEqual(m.memory.data[0xd05a],60)
        self.assertTrue(m.memory.data[0xd031]&128)
        for i in range(1024):
            b=m.memory.char_wom[i]
            expected=(0x80 if b&0xc0 else 0)|(0x40 if b&0x30 else 0)|(0x20 if b&12 else 0)|(0x10 if b&3 else 0)
            self.assertEqual(m.memory.data[0x4000+i],expected)
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
            self.assertEqual(number(m,4,6,7),f'{score%10000000:07d}')
            self.assertEqual(int.from_bytes(m.memory.data[NAMES['player1_score']:NAMES['player1_score']+4],'little'),score)
        m.memory.screen_writes.clear()
        for name in ('hud_update_score','hud_update_level','hud_update_lives','hud_update_points'): call(m,name)
        self.assertEqual(m.memory.screen_writes,[])
        m.memory.data[NAMES['player1_level']:NAMES['player1_level']+2]=(999).to_bytes(2,'little')
        call(m,'hud_update_level'); self.assertEqual(number(m,5,11,3),'999')

    def test_motion_rendering_prefix_survives_clearing_and_player2_keys_inactive(self):
        old=PREVIOUS.Machine().execute(); PREVIOUS.begin(old)
        new=self.start()
        prefix=[bytes(new.memory.data[0x5000+r*80:0x5000+r*80+42]) for r in range(25)]
        initial_hud=[row[480:] for row in hud_pixels(new)]
        new_start=new.cpu.processorCycles; old_start=old.cpu.processorCycles
        for i in range(56):
            key=[0,0x20,0x2b,0x2d,0x50,0x53][i%6]; buttons=[255,251,247,254,253][i%5]
            PREVIOUS.frame(old,key,buttons); frame(new,key,buttons)
            self.assertEqual(new.memory.data[0x1600:0x1900],old.memory.data[0x1600:0x1900])
            self.assertEqual(new.memory.data[NAMES['s2i_phase']:NAMES['s2i_phase']+22],old.memory.data[PREVIOUS.NAMES['s2i_phase']:PREVIOUS.NAMES['s2i_phase']+22])
            self.assertLessEqual(max(new.memory.data[NAMES['s2i_x']:NAMES['s2i_x']+22])+16,240)
            for row in range(25): self.assertEqual(bytes(new.memory.data[0x5000+row*80:0x5000+row*80+42]),prefix[row])
            for row in range(2,23):
                count=new.memory.data[NAMES['v014_row_count']+row]
                for slot in range(count):
                    at=0x5000+row*80+42+slot*4
                    self.assertEqual(int.from_bytes(new.memory.data[at:at+2],'little')&1023,old.memory.data[at]*2)
                    self.assertEqual(new.memory.data[at+2:at+4],old.memory.data[at+2:at+4])
            self.assertEqual(new.memory.data[NAMES['player2_active']],0)
        self.assertEqual([row[480:] for row in hud_pixels(new)],initial_hud)
        # Preserve 50Hz wait logic. Report model cycle overhead, no real-time claim.
        print('Stage3b4a model mean extra CPU cycles/frame:',(new.cpu.processorCycles-new_start-old.cpu.processorCycles+old_start)/56)

    def test_exit_registers_color_cursor_rom_palette_and_restart(self):
        m=Machine().execute()
        addresses=(0xd020,0xd021,0xd030,0xd031,0xd054,0xd05a,0xd05d,0xd058,0xd059,0xd05e,0xd060,0xd061,0xd062,0xd063,0xd064,0xd065,0xd068,0xd069,0xd06a,0xd07b,0xd070)
        before={a:m.memory.data[a] for a in addresses}; colour=bytes(m.memory.data[0xd800:0xe000]); cursor=bytes(m.memory.data[0x1000:0x1600]); palette=m.memory.primary_palette()
        for _ in range(2):
            begin(m); frame(m,0x58)
            self.assertEqual(m.cpu.pc,0x0200)
            self.assertEqual({a:m.memory.data[a] for a in addresses},before)
            self.assertEqual(bytes(m.memory.data[0xd800:0xe000]),colour)
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

    def test_font_aliases_and_direct_saved_charset(self):
        for high,bank,expected in ((0x10,0,0xff7e000),(0x18,0,0xff7e800),(0x90,0,0xff7e000),(0x98,0,0xff7e800),(0x10,2,0x21000)):
            m=Machine()
            m.memory.data[NAMES['saved_d068']]=0
            m.memory.data[NAMES['saved_d069']]=high
            m.memory.data[NAMES['saved_d06a']]=bank
            call(m,'hud_copy_font')
            self.assertEqual(m.memory.base.transfers[-1],(expected,0x4000,2048))

if __name__=='__main__': unittest.main()
