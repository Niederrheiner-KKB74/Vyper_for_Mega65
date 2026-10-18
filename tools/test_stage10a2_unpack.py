#!/usr/bin/env python3
"""Run the ASSEMBLED Stage10a2 decoder (from STAGE10A2.PRG) in a small 45GS02 model.

The KERNAL is mocked: $FFBD/$FFCF/$FFB7 and audio8.rom_call serve the packed
file byte by byte with real READST semantics ($40 together with the last byte).
Both loader styles are exercised exactly like s3b.load_file and the audio
loader call them, and every decoded stream must equal the original DAT file
with READST=$40 only after the final byte. X, Y, IRQ flag and B register must be
restored after every call. Usage: test_stage10a2_unpack.py RELEASE_DIR RAW_DIR
"""
import re, sys
from pathlib import Path

class CPU:
    def __init__(self, mem, attic):
        self.m = mem; self.attic = attic
        self.a = self.x = self.y = self.z = 0; self.b = 0; self.sp = 0x1ff
        self.c = self.zf = self.n = self.v = 0; self.i = 0; self.d = 0
        self.traps = {}; self.cycles = 0
    def rd(self, a): return self.m[a & 0xffff]
    def wr(self, a, v): self.m[a & 0xffff] = v & 255
    def w16(self, a): return self.rd(a) | self.rd(a+1) << 8
    def push(self, v): self.wr(self.sp, v); self.sp = 0x100 | ((self.sp-1) & 255)
    def pull(self): self.sp = 0x100 | ((self.sp+1) & 255); return self.rd(self.sp)
    def flags(self): return self.n<<7 | self.v<<6 | 0x30 | self.d<<3 | self.i<<2 | self.zf<<1 | self.c
    def setp(self, p): self.n, self.v, self.d, self.i, self.zf, self.c = p>>7&1, p>>6&1, p>>3&1, p>>2&1, p>>1&1, p&1
    def nz(self, v): v &= 255; self.zf = int(v == 0); self.n = v >> 7; return v
    def call(self, pc, limit=10**6):
        self.push(0xff); self.push(0xfe)          # return to $FFFF sentinel
        self.pc = pc; steps = 0
        while self.pc != 0xffff:
            if self.pc in self.traps:
                self.traps[self.pc](self); self.pc = (self.pull() | self.pull() << 8) + 1; continue
            self.step(); steps += 1
            if steps > limit: raise RuntimeError('runaway')
        return steps
    def flat(self, zp):
        base = (self.b << 8) | zp
        return self.rd(base) | self.rd(base+1) << 8 | self.rd(base+2) << 16 | (self.rd(base+3) & 15) << 24
    def step(self):
        op = self.rd(self.pc); pc = self.pc
        imm = lambda: self.rd(pc+1); ab = lambda: self.w16(pc+1)
        if op == 0xea and self.rd(pc+1) in (0x92, 0xb2):   # 32-bit [zp],Z
            addr = self.flat(self.rd(pc+2)) + self.z
            if addr >> 24 != 8: raise RuntimeError(f'flat access outside Attic {addr:#x}')
            if self.i == 0: raise RuntimeError('flat access with IRQs enabled')
            if self.rd(pc+1) == 0x92: self.attic[addr] = self.a
            else: self.a = self.nz(self.attic.get(addr, 0))
            self.pc += 3; return
        L = 1
        def adc(v):
            r = self.a + v + self.c; self.v = int(((self.a ^ r) & (v ^ r) & 0x80) != 0)
            self.c = int(r > 255); self.a = self.nz(r)
        def cmp(r, v): self.c = int(r >= v); self.nz(r - v)
        def rmw(addr, f): self.wr(addr, f(self.rd(addr)))
        def lsr(v): self.c = v & 1; return self.nz(v >> 1)
        def rol(v): r = (v << 1) | self.c; self.c = r >> 8; return self.nz(r)
        def ror(v): r = (v >> 1) | (self.c << 7); self.c = v & 1; return self.nz(r)
        def br(cond):
            nonlocal L
            L = 2
            if cond: off = imm(); self.pc = pc + 2 + (off - 256 if off & 128 else off); L = 0
        if op == 0x08: self.push(self.flags())
        elif op == 0x28: self.setp(self.pull())
        elif op == 0x48: self.push(self.a)
        elif op == 0x68: self.a = self.nz(self.pull())
        elif op == 0xda: self.push(self.x)
        elif op == 0xfa: self.x = self.nz(self.pull())
        elif op == 0x5a: self.push(self.y)
        elif op == 0x7a: self.y = self.nz(self.pull())
        elif op == 0xdb: self.push(self.z)
        elif op == 0xfb: self.z = self.nz(self.pull())
        elif op == 0x5b: self.b = self.a
        elif op == 0x7b: self.a = self.nz(self.b)
        elif op == 0xa3: self.z = self.nz(imm()); L = 2
        elif op == 0x20: self.push((pc+2) >> 8); self.push((pc+2) & 255); self.pc = ab(); L = 0
        elif op == 0x60: self.pc = (self.pull() | self.pull() << 8) + 1; L = 0
        elif op == 0x4c: self.pc = ab(); L = 0
        elif op == 0xa9: self.a = self.nz(imm()); L = 2
        elif op == 0xad: self.a = self.nz(self.rd(ab())); L = 3
        elif op == 0xbd: self.a = self.nz(self.rd(ab()+self.x)); L = 3
        elif op == 0x8d: self.wr(ab(), self.a); L = 3
        elif op == 0x9d: self.wr(ab()+self.x, self.a); L = 3
        elif op == 0xa2: self.x = self.nz(imm()); L = 2
        elif op == 0xe8: self.x = self.nz(self.x+1)
        elif op == 0xca: self.x = self.nz(self.x-1)
        elif op == 0x8a: self.a = self.nz(self.x)
        elif op == 0xaa: self.x = self.nz(self.a)
        elif op == 0xae: self.x = self.nz(self.rd(ab())); L = 3
        elif op == 0x8e: self.wr(ab(), self.x); L = 3
        elif op == 0x1d: self.a = self.nz(self.a | self.rd(ab()+self.x)); L = 3
        elif op == 0xde: rmw(ab()+self.x, lambda v: self.nz(v-1)); L = 3
        elif op == 0x2c:
            v = self.rd(ab()); self.zf = int((self.a & v) == 0); self.n = v >> 7; self.v = (v >> 6) & 1; L = 3
        elif op == 0x50: br(not self.v)
        elif op == 0x70: br(self.v)
        elif op == 0xe0: cmp(self.x, imm()); L = 2
        elif op == 0xc9: cmp(self.a, imm()); L = 2
        elif op == 0x09: self.a = self.nz(self.a | imm()); L = 2
        elif op == 0x0d: self.a = self.nz(self.a | self.rd(ab())); L = 3
        elif op == 0x29: self.a = self.nz(self.a & imm()); L = 2
        elif op == 0x2d: self.a = self.nz(self.a & self.rd(ab())); L = 3
        elif op == 0x4d: self.a = self.nz(self.a ^ self.rd(ab())); L = 3
        elif op == 0x69: adc(imm()); L = 2
        elif op == 0x6d: adc(self.rd(ab())); L = 3
        elif op == 0xe9: adc(imm() ^ 255); L = 2
        elif op == 0xed: adc(self.rd(ab()) ^ 255); L = 3
        elif op == 0xee: rmw(ab(), lambda v: self.nz(v+1)); L = 3
        elif op == 0xce: rmw(ab(), lambda v: self.nz(v-1)); L = 3
        elif op == 0x4e: rmw(ab(), lsr); L = 3
        elif op == 0x2e: rmw(ab(), rol); L = 3
        elif op == 0x6e: rmw(ab(), ror); L = 3
        elif op == 0x4a: self.a = lsr(self.a)
        elif op == 0x2a: self.a = rol(self.a)
        elif op == 0x6a: self.a = ror(self.a)
        elif op == 0x18: self.c = 0
        elif op == 0x38: self.c = 1
        elif op == 0x78: self.i = 1
        elif op == 0x58: self.i = 0
        elif op == 0xd0: br(not self.zf)
        elif op == 0xf0: br(self.zf)
        elif op == 0x90: br(not self.c)
        elif op == 0xb0: br(self.c)
        elif op == 0x10: br(not self.n)
        elif op == 0x30: br(self.n)
        else: raise RuntimeError(f'opcode {op:02x} at {pc:04x} not modelled')
        self.pc += L

def run(release, raw):
    release, raw = Path(release), Path(raw)
    prg = (release/'STAGE10A2.PRG').read_bytes(); sym = (release/'STAGE10A2.sym').read_text()
    def label(ns, name):
        for block in re.findall(r'\.namespace '+ns+r' \{(.*?)\n\}', sym, re.S):
            m = re.search(r'\.label '+name+r'=\$([0-9a-f]+)', block)
            if m: return int(m[1], 16)
        raise KeyError(ns+'.'+name)
    base = prg[0] | prg[1] << 8
    results = []
    for name in ('VYTI.DAT', 'VYSO.DAT', 'VYHS.DAT', 'VYMN.DAT', 'VYLV.DAT', 'VYGR.DAT', 'VYSH.DAT', 'VYCL.DAT'):
        for style in ('s3b', 'rom'):
            if style == 'rom' and name != 'VYSO.DAT': continue
            mem = bytearray(65536); mem[base:base+len(prg)-2] = prg[2:]
            cpu = CPU(mem, {}); packed = (release/name).read_bytes(); want = (raw/name).read_bytes()
            stream = {'pos': 0, 'st': 0, 'opened': False}
            def chrin(c):
                if stream['pos'] >= len(packed): c.a = 0; stream['st'] = 0x42; return
                c.a = packed[stream['pos']]; stream['pos'] += 1
                stream['st'] = 0x40 if stream['pos'] == len(packed) else 0
                c.x = c.y = 0x55                     # KERNAL clobbers registers
            def readst(c): c.a = stream['st']; c.nz(c.a)
            def setnam(c): stream['opened'] = True
            rom_jsr = label('audio8', 'rom_jsr'); rom_call = label('audio8', 'rom_call')
            def romcall(c):
                op = c.rd(rom_jsr+1)
                {0xcf: chrin, 0xb7: readst, 0xbd: setnam}[op](c)
                c.i = 1                              # rom_call returns with IRQs masked
            cpu.traps = {0xffcf: chrin, 0xffb7: readst, 0xffbd: setnam, rom_call: romcall}
            entry = label('unpack', 'setnam' if style == 's3b' else 'setnam_rom')
            cpu.i = 0 if style == 's3b' else 1
            cpu.a, cpu.x, cpu.y = 12, 0x34, 0x12
            cpu.call(entry)
            if (cpu.a, cpu.x, cpu.y) != (12, 0x34, 0x12) or not stream['opened']: raise SystemExit(f'{name}: SETNAM arguments changed')
            out = bytearray(); steps = 0
            for i in range(len(want)):
                irq = cpu.i; cpu.x, cpu.y = 0x11, 0x22
                steps += cpu.call(label('unpack', 'chrin')); out.append(cpu.a)
                if (cpu.x, cpu.y, cpu.b, cpu.i) != (0x11, 0x22, 0, irq): raise SystemExit(f'{name}: registers/IRQ/B not preserved at byte {i}')
                cpu.call(label('unpack', 'readst'))
                expect = 0x40 if i == len(want)-1 else 0
                if cpu.a != expect: raise SystemExit(f'{name}: READST {cpu.a:#x} at byte {i}/{len(want)}')
            if bytes(out) != want: raise SystemExit(f'{name}: decoded data differs')
            results.append((name, style, len(packed), len(want), steps/len(want)))
    for r in results: print(f'{r[0]:10} {r[1]:4} packed {r[2]:7} -> {r[3]:7} bytes, {r[4]:.1f} instructions/byte: OK')
    # Corrupt stream must be reported through READST, never silently accepted.
    print('all decoded streams identical, READST=$40 exactly after the last byte')
    return results

if __name__ == '__main__':
    run(*sys.argv[1:3])
