import sys, json, hashlib, subprocess
from pathlib import Path
import argparse
parser = argparse.ArgumentParser(description='Refresh washer inventory from the enclosure model.')
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[3])
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'design_inputs.json')
args = parser.parse_args()
sys.path.insert(0, str(args.source))
from build import build_enclosure
from lumber_model.components import SEALING_WASHERS
root=args.source
e=build_enclosure()
rows=[]
for trade,part,e0,tpi,s,body in [('1/2','E943D',.75843,14,.545,1.042),('3/4','E943E',.96768,14,.553,1.290),('1','E943F',1.21363,11.5,.812,1.580),('1-1/4','E943G',1.55713,11.5,.816,1.973)]:
    c=SEALING_WASHERS[trade]
    primitive=c.cylinder_primitives[0]
    rows.append(dict(trade_size=trade,carlon_adapter=part,npt_e0_in=e0,tpi=tpi,thread_projection_in=s,catalog_body_od_in=body,outer_diameter_mm=round(primitive[3]*25.4,6),thickness_mm=round(primitive[2]*25.4,6),locations=[n for n,x in e.components.items() if x.component_type==c and n.endswith('_sealing_washer')]))
data=dict(source_repository=str(root),source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['build.py','lumber_model/components.py']},clearance_diametral_mm=.4,round_bore_up_mm=.1,rings=rows)
args.output.write_text(json.dumps(data,indent=2)+'\n')
