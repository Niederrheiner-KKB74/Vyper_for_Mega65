"""1581 image builder with chained directory sectors; extends the protected baseline."""
import struct,hashlib
def sha(b):return hashlib.sha256(b).hexdigest()

def build_disk(entries):
    """1581 D81: track 40 header/BAM/directory, 254 payload bytes per sector."""
    image = bytearray(80 * 40 * 256)
    directory_count=(len(entries)+7)//8
    if not 1<=directory_count<=37:raise ValueError("Directory capacity")
    used = {(40, s) for s in range(3+directory_count)}
    free_sectors = [(t, s) for t in range(1, 81) if t != 40 for s in range(40)]

    def put(t, s, data):
        offset = ((t-1)*40+s)*256
        image[offset:offset+256] = data

    def pet(text, size):
        return text.upper().encode('ascii').ljust(size, b'\xa0')

    directories=[bytearray(256) for _ in range(directory_count)]
    for i,d in enumerate(directories):d[:2]=bytes((40,4+i)) if i+1<directory_count else bytes((0,255))
    for i, (name, payload, kind) in enumerate(entries):
        count = (len(payload)+253)//254
        chain, free_sectors = free_sectors[:count], free_sectors[count:]
        if len(chain) != count or not chain:
            raise ValueError('Disk full or empty file')
        used.update(chain)
        for j, (t, s) in enumerate(chain):
            part = payload[j*254:(j+1)*254]
            block = bytearray(256)
            block[:2] = bytes(chain[j+1]) if j+1 < count else bytes((0, len(part)+1))
            block[2:2+len(part)] = part
            put(t, s, block)
        directory=directories[i//8]
        offset = 2+(i%8)*32
        directory[offset] = kind
        directory[offset+1:offset+3] = bytes(chain[0])
        directory[offset+3:offset+19] = pet(name, 16)
        directory[offset+28:offset+30] = struct.pack('<H', count)
    for i,directory in enumerate(directories):put(40,3+i,directory)
    header = bytearray(256)
    header[:4] = bytes((40, 3, 0x44, 0))
    header[4:20] = pet('VYPER STAGE 3B1', 16)
    header[20:29] = b'\xa0\xa03B\xa03D\xa0\xa0'
    put(40, 0, header)
    for index in range(2):
        bam = bytearray(256)
        bam[:8] = bytes((40, 2, 0x44, 0xbb, 0x33, 0x42, 0xc0, 0)) if index == 0 else bytes((0, 255, 0x44, 0xbb, 0x33, 0x42, 0xc0, 0))
        for j in range(40):
            t = index*40+j+1
            free = [s for s in range(40) if (t, s) not in used]
            offset = 16+j*6
            bam[offset] = len(free)
            for s in free:
                bam[offset+1+s//8] |= 1 << (s%8)
        put(40, index+1, bam)
    return bytes(image)


def verify_disk(image, entries):
    if len(image) != 819200:
        raise ValueError('D81 size mismatch')
    def get(t, s):
        if not 1 <= t <= 80 or not 0 <= s < 40:
            raise ValueError('Invalid sector pointer')
        offset = ((t-1)*40+s)*256
        return image[offset:offset+256]
    if get(40, 0)[:4] != bytes((40, 3, 0x44, 0)):
        raise ValueError('D81 header mismatch')
    directories=[];occupied={(40,s) for s in range(3)};t,s=40,3
    while t:
        if (t,s) in occupied:raise ValueError('Directory cycle')
        occupied.add((t,s));directory=get(t,s);directories.append(directory);t,s=directory[:2]
    if s!=255 or len(directories)!=(len(entries)+7)//8:raise ValueError('Directory termination')
    report = []
    for i, (name, data, kind) in enumerate(entries):
        directory=directories[i//8]
        offset = 2+(i%8)*32
        if directory[offset] != kind or directory[offset+3:offset+19] != name.encode().ljust(16, b'\xa0'):
            raise ValueError('Directory name/type mismatch')
        t, s = directory[offset+1:offset+3]
        collected = bytearray()
        blocks = 0
        while t:
            if (t, s) in occupied:
                raise ValueError('Cross-linked/cyclic file chain')
            occupied.add((t, s))
            blocks += 1
            block = get(t, s)
            nt, ns = block[:2]
            if not nt and not 1 <= ns <= 255:
                raise ValueError('Invalid last-sector length')
            collected += block[2:256 if nt else ns+1]
            t, s = nt, ns
        if bytes(collected) != data or blocks != int.from_bytes(directory[offset+28:offset+30], 'little'):
            raise ValueError(f'Disk file verification failed: {name}')
        report.append({'name': name, 'bytes': len(data), 'blocks': blocks, 'sha256': sha(data)})
    for t in range(1, 81):
        bam = get(40, 1 if t <= 40 else 2)
        if bam[2:6] != b'\x44\xbb3B':
            raise ValueError('BAM version/ID mismatch')
        offset = 16+((t-1)%40)*6
        free = 0
        for s in range(40):
            is_free = bool(bam[offset+1+s//8] & (1 << (s%8)))
            if is_free == ((t, s) in occupied):
                raise ValueError('BAM allocation mismatch')
            free += is_free
        if bam[offset] != free:
            raise ValueError('BAM free-sector count mismatch')
    return report
