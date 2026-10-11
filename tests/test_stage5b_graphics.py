"""Independent original-plane oracle and actual assembled RRB/DMA regressions."""
import unittest,json,struct,tempfile
from pathlib import Path
import test_stage5b as T
import extract_stage5b_graphics as G
ROOT=T.ROOT
class OriginalGraphicsTests(unittest.TestCase):
    def test_all259_pixels_original_pointer_masks_and_columns(self):
        m=(ROOT/'assets/stage5b/original_sources/Vyper_Memory_Dump.dat').read_bytes()
        raw=(ROOT/'assets/stage5b/VYGR.DAT').read_bytes();types=G.graphics_types(raw)
        manifest=json.loads((ROOT/'assets/stage5b/extraction_manifest.json').read_text())
        self.assertEqual(manifest['frames'],259);checked=0
        for i,t in enumerate(types):
            p=int.from_bytes(m[0x2daf2+18*i+8:0x2daf2+18*i+12],'big')
            for j,f in enumerate(t['frames']):
                addresses=[int.from_bytes(m[p+32*j+k:p+32*j+k+4],'big') for k in (0,4,8,24)]
                opaque=[0]*16
                for y in range(16):
                    for x in range(16):
                        visible=bool(m[addresses[3]+y*2+x//8]&(128>>(x%8)))
                        colour=0
                        for plane,a in enumerate(addresses[:3]):
                            colour|=int(bool(m[a+y*2+x//8]&(128>>(x%8))))<<plane
                        actual=(f[y*8+x//2]>>(4*(x%2)))&15
                        self.assertEqual(actual,colour+1 if visible else 0,(i,j,x,y))
                        opaque[x]+=visible;checked+=1
                self.assertEqual(opaque,manifest['frames_manifest'][sum(q['frame_count'] for q in types[:i])+j]['opaque_per_column'])
        self.assertEqual(checked,66304)
    def test_extraction_reproducible_all_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);G.extract(output=out)
            expected=[p for p in (ROOT/'assets/stage5b').iterdir() if p.is_file()]
            self.assertGreater(len(expected),259)
            for p in expected:self.assertEqual(p.read_bytes(),(out/p.name).read_bytes(),p.name)
    def test_mapping_and_all_original_Forme_slots(self):
        r=json.loads((ROOT/'assets/stage5b/extraction_manifest.json').read_text())
        self.assertEqual([m['vygr_type_1based'] for m in r['mapping']],list(range(1,39)))
        self.assertFalse(r['original_indexing_routine_proven'])
        self.assertEqual(sum(x['enemy_count'] for x in r['levels']),2194)
        for index,levels in [(36,[29,54]),(37,[37])]:
            self.assertEqual([l['level'] for l in r['levels'] if index in l['indices']],levels)
    def test_all259_frames_actual_rrb_odd_edges_overlap_and_guards(self):
        m=T.start();T.enemies(m);T.setv(m,'c_ps',2)
        types=G.graphics_types((ROOT/'assets/stage5b/VYGR.DAT').read_bytes())
        positions=[(-1,60),(239,60),(60,-1),(60,199),(-3,-3),(237,195),(60,60)]
        for t in types:
            for slot in (0,1):
                T.setv(m,'gxlo',t['offset']&255,slot);T.setv(m,'gxhi',t['offset']>>8,slot);T.setv(m,'gframes',t['frame_count'],slot)
            for j,payload in enumerate(t['frames']):
                for slot in (0,1):T.setv(m,'gframe',j,slot)
                for x,y in positions:
                    T.target(m,0,1,x&255,y&255)
                    for n,v in [('e_xlo',x&255),('e_xhi',(x>>8)&255),('e_ylo',y&255),('e_yhi',(y>>8)&255)]:T.setv(m,n,v)
                    T.call(m,'e_render');self.assertEqual(T.fetched(m),T.oracle(x,y,payload),(t['type'],j,x,y))
                    self.assertEqual(T.get(m,'v014_overflow_count'),0)
                    self.assertEqual(m.memory.data[0x14000:0x14040],bytes(64))
                    self.assertEqual(m.memory.data[0x140c0:0x14100],bytes(64))
                # Two fragments at exactly the same origin must still reproduce the original.
                T.target(m,1,1,60,60)
                for n,v in [('e_xlo',60),('e_xhi',0),('e_ylo',60),('e_yhi',0)]:T.setv(m,n,v,1)
                T.call(m,'e_render');self.assertEqual(T.fetched(m),T.oracle(60,60,payload))
                T.setv(m,'c_es',0,1)
    def test_loader_extended_size_checksums_and_readback_faults(self):
        m=T.Machine().execute();self.assertEqual(m.error,0)
        raw=(ROOT/'assets/stage5b/VYGR.DAT').read_bytes()
        self.assertEqual(m.memory.data[0x54000:0x54000+len(raw)],raw)
        self.assertEqual(m.memory.data[0x54000+len(raw)],0xa5)
        self.assertEqual(m.memory.data[0x40000:0x53f81],(ROOT/'assets/VYLV.DAT').read_bytes())
        # Stable loader has a bounded-length contract: extra trailing bytes are not read.
        trailing=T.Machine();trailing.files['VYGR.DAT']=raw+b'\0';trailing.execute()
        self.assertEqual(trailing.error,0)
        self.assertEqual(trailing.memory.data[0x54000+len(raw)],0xa5)
        for kind in ('short','checksum','dma'):
            n=T.Machine()
            if kind=='short':n.files['VYGR.DAT']=raw[:-1]
            elif kind=='checksum':n.files['VYGR.DAT']=raw[:-1]+bytes([raw[-1]^1])
            else:n.memory.base.corrupt_dma=True
            n.execute();self.assertNotEqual(n.error,0,kind)
    def test_graphics_type_38_valid_39_invalid_and_end_bounds(self):
        m=T.start()
        for value in (37,38):
            T.setv(m,'selected_type',value);T.setv(m,'index',0);T.call(m,'graphics_descriptor');self.assertEqual(m.error,0)
            self.assertEqual(T.get(m,'gframes'),10)
        for value in (0,39):
            T.setv(m,'selected_type',value);T.call(m,'graphics_descriptor');self.assertEqual(m.error,8);T.setv(m,'error',0)
        # Last directory entry ending one byte after the physical payload is rejected.
        m.memory.data[0x54130:0x54132]=(33464-127).to_bytes(2,'little')
        T.setv(m,'selected_type',38);T.call(m,'graphics_descriptor');self.assertEqual(m.error,8)
if __name__=='__main__':unittest.main()
