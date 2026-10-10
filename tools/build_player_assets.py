#!/usr/bin/env python3
"""Build the user-approved 16x16 Vyper player assets from extracted indices.

Requires only Python stdlib. Optional Pillow generates a preview PNG.
"""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "player"
rows = (ASSET / "player_pixels.txt").read_text().splitlines()
assert len(rows) == 16 and all(len(row) == 16 for row in rows)
pixels = [[int(c, 16) for c in row] for row in rows]
assert all(0 <= p <= 8 for row in pixels for p in row)

sprite, ncm = bytearray(), bytearray()
for row in pixels:
    for x in range(0, 16, 2):
        left, right = row[x], row[x + 1]
        sprite.append((left << 4) | right)
        ncm.append((right << 4) | left)
assert len(sprite) == len(ncm) == 128
(ASSET / "player_sprite.bin").write_bytes(sprite)
(ASSET / "player_ncm.bin").write_bytes(ncm)

amiga = [0x000, 0x344, 0xFFF, 0xE00, 0xFF0, 0x899, 0x344, 0x566, 0xABB]
rgb = [tuple(((v >> shift) & 15) * 17 for shift in (8, 4, 0)) for v in amiga]
for ch, name in enumerate("rgb"):
    (ASSET / f"player_palette_{name}.bin").write_bytes(
        bytes(c[ch] for c in rgb) + bytes(16 - len(rgb))
    )

try:
    from PIL import Image
except ImportError:
    pass
else:
    image = Image.new("RGBA", (16, 16))
    for y, row in enumerate(pixels):
        for x, p in enumerate(row):
            image.putpixel((x, y), (*rgb[p], 255) if p else (0, 0, 0, 0))
    image.resize((384, 384), Image.Resampling.NEAREST).save(
        ASSET / "player_preview_original_palette.png"
    )

for name in ("player_sprite.bin", "player_ncm.bin"):
    data = (ASSET / name).read_bytes()
    print(name, len(data), hashlib.sha256(data).hexdigest())
