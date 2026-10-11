"""Stable4c trajectory oracle: execute archived assembled instructions, no guessed curve model."""
import json
import test_stage4c as t
m=t.start();t.setv(m,'a_enabled',1)
fields=['c_es','e_xlo','e_xhi','e_ylo','e_yhi','e_tx','e_ty','e_delay','e_cursor','e_group','e_phase','e_timer','a_index']
trace=[]
for tick in range(402):
    t.setv(m,'a_start_tick',255)
    t.call(m,'a_objects')
    trace.append([[t.get(m,n,i) for i in range(22)] for n in fields]+[[t.get(m,n) for n in ['a_offset','a_ready','a_form_tick','a_direction']]])
print(json.dumps(trace))
