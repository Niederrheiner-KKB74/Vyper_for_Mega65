#!/usr/bin/env python3
"""Execute actual assembled enemy motion/events without rendering or player hits.
Host instruction/DMA model; no measured XEMU timing or claim of original cadence.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import test_stage7b5a as T

def flush_trace(m):
    stats={'attempts':0,'spawns':0,'peak':0}
    m.cpu.pc=T.FE['flush'];m.cpu.stPushWord(0x1ff)
    for _ in range(100000):
        pc=m.cpu.pc
        if pc==0x200:return stats
        if pc==T.FE['attempt']:stats['attempts']+=1
        if pc==T.N['a_fire_start']:
            stats['spawns']+=1;stats['peak']=max(stats['peak'],sum(m.memory.data[T.N['p_active']+2:T.N['p_active']+8])+1)
        m.cpu.step()
    raise AssertionError('event flush did not terminate')
def verify_high_y_starts():
    m=T.MenuTests().machine().game(46);cases=[]
    for actor in (9,10,20,21):
        y=m.memory.data[T.N['e_ty']+actor]
        m.memory.data[T.N['e_ylo']+actor]=y;m.memory.data[T.N['e_yhi']+actor]=0
        m.memory.data[T.N['e_phase']+actor]=3;m.memory.data[T.N['c_es']+actor]=1
        m.cpu.x=actor;m.call('a_start')
        assert T.fword(m,'first',actor)==T.fword(m,'second',actor)==0
        assert m.memory.data[T.N['e_phase']+actor]==4 and m.memory.data[T.N['c_es']+actor]==3
        cases.append({'level':46,'actor_zero_based':actor,'original_Y':y+T.get(m,'y_shift'),'ATTACK_starts':True,'shot_events':0})
    return cases

def measure(frames=1200):
    T.MenuTests.setUpClass();rows=[]
    for level in (1,3,29,54):
        m=T.MenuTests().machine().game(level)
        planned=sum(bool(T.fword(m,n,i)) for i in range(m.memory.data[0x7603]) for n in ('first','second'))
        row={'level':level,'frames':frames,'mode':T.fget(m,'mode'),'every_nth':T.fget(m,'nth'),'initial_ENTRY_events_nonzero':planned,'ENTRY_due_events':0,'ATTACK_due_events':0,'spawn_attempts_valid_origin':0,'spawned_projectiles':0,'full_pool_losses':0,'origin_state_losses':0,'peak_enemy_projectiles':0,'attack_starts':0,'max_ATTACK':0}
        for frame in range(frames):
            phases=bytes(m.memory.data[T.N['e_phase']:T.N['e_phase']+22])
            m.call('a_preframe');m.call('e_objects')
            for i in range(m.memory.data[0x7603]):
                phase=m.memory.data[T.N['e_phase']+i];state=m.memory.data[T.N['c_es']+i]
                if phase==4 and phases[i]!=4:row['attack_starts']+=1
                due=T.fget(m,'pending',i).bit_count()
                row['ATTACK_due_events' if state==3 else 'ENTRY_due_events']+=due
            row['max_ATTACK']=max(row['max_ATTACK'],sum(m.memory.data[T.N['c_es']+i]==3 for i in range(22)))
            m.call('p_update');m.call('p_random_step');s=flush_trace(m)
            row['spawn_attempts_valid_origin']+=s['attempts'];row['spawned_projectiles']+=s['spawns'];row['full_pool_losses']+=s['attempts']-s['spawns'];row['peak_enemy_projectiles']=max(row['peak_enemy_projectiles'],s['peak'])
        row['origin_state_losses']=row['ENTRY_due_events']+row['ATTACK_due_events']-row['spawn_attempts_valid_origin']
        assert row['ENTRY_due_events']<=planned and row['peak_enemy_projectiles']<=6 and row['max_ATTACK']<=3
        rows.append(row);print(json.dumps(row),flush=True)
    report={'stage':'7b5a','kind':'assembled CPU/DMA host model, not XEMU/Amiga timing','PRG_sha256':T.BUILD.BASE.sha((T.ART/'STAGE7B5A.PRG').read_bytes()),'scenario':'All original enemies survive; actual ENTRY, attack scheduler, curves, return, motion and six-shot expiry. No renderer, player shots/hits or HUD; one update per model frame. Shooter IDs fixed, target unchanged. Attack RNG keeps the normal per-tick step.','rows':rows,'high_Y_start_guards':verify_high_y_starts()}
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frames',type=int,default=1200);p.add_argument('--output',type=Path,default=T.ART/'event-measurements.json');a=p.parse_args()
    a.output.write_text(json.dumps(measure(a.frames),indent=2)+'\n')
