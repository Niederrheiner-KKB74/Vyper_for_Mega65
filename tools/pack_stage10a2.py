#!/usr/bin/env python3
"""Stage10a2 packed SEQ format: "Z0", total(24), plain(24), ZX0 v2 stream.

Bytes after `plain` are delta coded before compression (out[i] = out[i-1] + d[i]),
which helps 8-bit PCM. Compression uses the reference ZX0 v2 compressor by Einar
Saukas (https://github.com/einar-saukas/ZX0), executable given by --zx0 / $ZX0.
Every packed file is verified with `decode`, a model of the 45GS02 streaming
decoder in src/engine/stage10a2_unpack.asm (same 32 KB ring and state machine).
"""
import os, subprocess, tempfile
from pathlib import Path

MAGIC = b'Z0'
RING = 32768

def delta(data, plain):
    out = bytearray(data[:plain]); prev = data[plain-1] if plain else 0
    for b in data[plain:]:
        out.append((b-prev) & 255); prev = b
    return bytes(out)

def decode(packed):
    if packed[:2] != MAGIC: raise ValueError('Packed header')
    total = int.from_bytes(packed[2:5], 'little'); plain = int.from_bytes(packed[5:8], 'little')
    pos = 8; mask = 0; val = 0; back = False; last = 0
    def raw():
        nonlocal pos, last
        if pos >= len(packed): raise ValueError('Packed stream ends early')
        last = packed[pos]; pos += 1; return last
    def bit():
        nonlocal mask, val, back
        if back: back = False; return last & 1
        mask >>= 1
        if not mask: mask = 128; val = raw()
        return 1 if val & mask else 0
    def gamma(inv):
        v = 1
        while not bit():
            v = (v << 1) | (bit() ^ inv)
            if v > 0xffff: raise ValueError('Gamma exceeds 16 bits')
        return v
    ring = bytearray(RING); w = 0; r = 0; out = bytearray(); offset = 1; acc = 0
    mode = 'LIT'; cnt = gamma(0)
    while len(out) < total:
        if cnt:
            if mode == 'LIT': b = raw()
            else: b = ring[r]; r = (r+1) & (RING-1)
            ring[w] = b; w = (w+1) & (RING-1); cnt -= 1
            acc = b if len(out) < plain else (acc+b) & 255
            out.append(acc); continue
        if mode == 'LIT' and not bit():
            mode = 'MATCH'; cnt = gamma(0); r = (w-offset) & (RING-1); continue
        if mode != 'LIT' and not bit():
            mode = 'LIT'; cnt = gamma(0); continue
        v = gamma(1)
        if v > 255: raise ValueError('End marker before total')
        offset = v*128 - (raw() >> 1); back = True
        if not 1 <= offset <= RING: raise ValueError('Offset exceeds ring')
        cnt = gamma(0) + 1
        if cnt > 0xffff: raise ValueError('Match length exceeds 16 bits')
        mode = 'MATCH'; r = (w-offset) & (RING-1)
    return bytes(out)

def pack(data, plain=None, zx0=None):
    zx0 = zx0 or os.environ.get('ZX0')
    if not zx0: raise ValueError('ZX0 compressor required (--zx0 or $ZX0)')
    plain = len(data) if plain is None else plain
    if not 0 <= plain <= len(data) or len(data) >= 1 << 24: raise ValueError('Packed range')
    with tempfile.TemporaryDirectory() as t:
        src = Path(t)/'in.bin'; dst = Path(t)/'in.zx0'
        src.write_bytes(delta(data, plain))
        subprocess.run([zx0, '-f', str(src), str(dst)], check=True, stdout=subprocess.DEVNULL)
        stream = dst.read_bytes()
    packed = MAGIC + len(data).to_bytes(3, 'little') + plain.to_bytes(3, 'little') + stream
    if decode(packed) != data: raise ValueError('Packed stream does not reproduce original')
    return packed
