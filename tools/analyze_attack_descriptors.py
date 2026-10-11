#!/usr/bin/env python3
"""Audit all VYLV.DAT attack-curve indices. Standard library only."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import struct

def u16(data, p):
    return struct.unpack_from("<H", data, p)[0]

def u32(data, p):
    return struct.unpack_from("<I", data, p)[0]

def parse(data):
    if data[:4] != b"VYLV":
        raise ValueError("Not a VYLV file")
    count = u16(data, 6)
    for i in range(count):
        base = 8 + 8 * i
        start, size = u32(data, base), u32(data, base + 4)
        end = start + size
        if end > len(data):
            raise ValueError(f"Level {i+1}: record exceeds file")
        level = u16(data, start)
        ng, ne = data[start+2], data[start+3]
        interval, na = u16(data, start+4), u16(data, start+6)
        p = start + 8
        groups = []
        for _ in range(ng):
            n, x, y, length = [u16(data, p + j) for j in (0, 2, 4, 6)]
            p += 8
            if p + length > end:
                raise ValueError(f"Level {level}: group overflow")
            groups.append((n, x, y, length))
            p += length
        if sum(g[0] for g in groups) != ne:
            raise ValueError(f"Level {level}: enemy/group count mismatch")
        enemies = []
        for _ in range(ne):
            if p + 6 > end:
                raise ValueError(f"Level {level}: enemy overflow")
            enemies.append((u16(data,p),u16(data,p+2),data[p+4],data[p+5]))
            p += 6
        attacks = []
        for _ in range(na):
            if p + 2 > end:
                raise ValueError(f"Level {level}: attack length overflow")
            n = u16(data,p)
            p += 2
            if p + n > end:
                raise ValueError(f"Level {level}: attack data overflow")
            attacks.append(data[p:p+n])
            p += n
        if p != end:
            raise ValueError(f"Level {level}: {end-p} bytes unparsed")
        for e in enemies:
            if e[3] >= na:
                raise ValueError(f"Level {level}: attack index {e[3]} >= {na}")
        yield (level, interval, groups, enemies, attacks)

def decode(b):
    dx, dy = (b >> 4) & 7, b & 7
    return (-dx if b & 0x80 else dx, -dy if b & 8 else dy)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default="assets/VYLV.DAT")
    args = parser.parse_args()
    data = Path(args.file).read_bytes()
    print("VYLV bytes:", len(data), "SHA256:", hashlib.sha256(data).hexdigest())
    levels = list(parse(data))
    print("levels:", len(levels), "enemies:", sum(len(l[3]) for l in levels))
    print("curve count distribution:", dict(sorted(Counter(len(l[4]) for l in levels).items())))
    print("enemy attack index distribution:", dict(sorted(Counter(e[3] for l in levels for e in l[3]).items())))
    for level, interval, groups, enemies, attacks in levels:
        counts = Counter(e[3] for e in enemies)
        missing = set(range(len(attacks))) - set(counts)
        if missing:
            print(f"Level {level}: unused curve(s) {sorted(missing)}")
    for number in (1, 2, 5, 47, 52, 56, 97, 99, 100):
        level, interval, groups, enemies, attacks = levels[number-1]
        counts = Counter(e[3] for e in enemies)
        print(f"Level {level}: {len(enemies)} enemies, {len(attacks)} curves, "
              f"lengths={[len(a) for a in attacks]}, "
              f"usage={[counts[i] for i in range(len(attacks))]}")
    a,b=levels[0][4]
    mirror = len(a)==len(b) and all(
        decode(x)[0] == -decode(y)[0] and decode(x)[1] == decode(y)[1]
        for x,y in zip(a,b)
    )
    print("Level 1: curves horizontally mirrored:", mirror)

if __name__ == "__main__":
    main()
