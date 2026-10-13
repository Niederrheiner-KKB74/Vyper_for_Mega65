#!/usr/bin/env python3
"""Execute actual assembled scheduler/curves/projectiles; isolated host ticks, not XEMU."""
import argparse,importlib,json,statistics,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['7b2','7b3'],required=True);p.add_argument('--frames',type=int,default=3000);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
T=importlib.import_module('test_stage'+a.stage);N=T.N
T.MenuTests.setUpClass()
def get(m,n,i=0):return m.memory.data[N[n]+i]
def put(m,n,v,i=0):m.memory.data[N[n]+i]=v
slots=6 if a.stage=='7b2' else 8
seed=0xc3a5

def scenario(count):
 m=T.MenuTests().machine().game(1)
 for i in range(23):
  put(m,'c_es',1 if i<count else 0,i);put(m,'e_phase',3,i)
  for target,source in [('e_xlo','e_tx'),('e_ylo','e_ty')]:put(m,target,get(m,source,i),i)
  put(m,'e_xhi',0,i);put(m,'e_yhi',0,i)
 put(m,'a_ready',1);put(m,'a_start_tick',0);put(m,'p_random_lo',seed&255);put(m,'p_random_hi',seed>>8)
 return m

def measure(count,physical):
 m=scenario(count);starts=shots=max_attack=max_shots=0;waits=[];last_ready=[0]*count;hits=[0]*count
 counters={'due':0,'eligible':0,'returns':0};context={'frame':0,'before':[]}
 original_step=m.cpu.step
 def step():
  if m.cpu.pc==N['a_postframe']:
   candidates=[i for i in range(count) if get(m,'c_es',i)==1 and get(m,'e_phase',i)==3]
   if physical:
    for i in candidates:
     if context['before'][i]!=1:last_ready[i]=context['frame'];counters['returns']+=1
   if get(m,'a_start_tick')<=1:
    counters['due']+=1
    if candidates and sum(get(m,'c_es',i)==3 for i in range(count))<3:counters['eligible']+=1
  return original_step()
 m.cpu.step=step
 for frame in range(a.frames):
  context['frame']=frame;put(m,'a_event',0)
  if not physical:
   for i in range(count):put(m,'c_es',1,i);put(m,'e_phase',3,i)
   m.call('a_postframe')
  else:
   context['before']=[get(m,'c_es',i) for i in range(count)]
   m.call('a_objects') # e_objects/ygeometry invokes a_postframe exactly once.
  if get(m,'a_event')==1:
   starts+=1;idx=get(m,'a_event_enemy');hits[idx]+=1;waits.append(frame-last_ready[idx]);last_ready[idx]=frame
  attacks=sum(get(m,'c_es',i)==3 for i in range(count));max_attack=max(max_attack,attacks)
  m.call('p_random_step')
  if physical:
   assert attacks<=3
   m.call('p_update');before=[get(m,'p_active',i) for i in range(2,slots)]
   m.call('a_fire')
   shots+=sum(not old and get(m,'p_active',i) for i,old in zip(range(2,slots),before))
   max_shots=max(max_shots,sum(get(m,'p_active',i) for i in range(2,slots)))
 return {'remaining':count,'frames':a.frames,'due_checks':counters['due'],'available_opportunities':counters['eligible'],'attacks_started':starts,'starts_per_minute':starts*3000/a.frames,'returns_completed':counters['returns'],'enemy_shots_born':shots,'peak_ATTACK':max_attack,'peak_enemy_projectiles':max_shots,'mean_ready_wait_frames':statistics.mean(waits) if waits else None,'max_ready_wait_frames':max(waits,default=None),'starts_by_enemy':hits}

def shoot_only():
 m=scenario(22)
 for i in range(22):
  put(m,'c_es',2,i);put(m,'e_phase',1,i);put(m,'e_visible',1,i);put(m,'e_xlo',90,i);put(m,'e_ylo',10,i);put(m,'a_hidden',0,i)
 births=due=full=peak=0
 for frame in range(a.frames):
  m.call('p_update');before=[get(m,'p_active',i) for i in range(2,slots)]
  if get(m,'p_cooldown')==0:due+=1
  if all(before):full+=1
  m.call('p_random_step');m.call('a_fire')
  births+=sum(not old and get(m,'p_active',i) for i,old in zip(range(2,slots),before));peak=max(peak,sum(get(m,'p_active',i) for i in range(2,slots)))
 return {'frames':a.frames,'cooldown_due_checks':due,'shots_born':births,'capacity_full_frames':full,'peak_projectiles':peak}
result={'stage':a.stage,'PRG_sha256':hashlib.sha256((T.ART/('STAGE'+a.stage.upper()+'.PRG')).read_bytes()).hexdigest(),'seed':seed,'frames':a.frames,'kind':'actual assembled instructions in isolated50Hz host ticks; no rendering/collisions, NOT XEMU','always_available':[measure(n,False) for n in [22,10,5,2,1]],'original_curves_and_return':[measure(n,True) for n in [22,10,5,2,1]],'shooting_only':shoot_only()}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
print(a.stage,json.dumps({'available_starts':[j['attacks_started'] for j in result['always_available']],'physical_starts':[j['attacks_started'] for j in result['original_curves_and_return']],'physical_shots':[j['enemy_shots_born'] for j in result['original_curves_and_return']],'shooting_only':result['shooting_only']}))
