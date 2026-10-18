"""Generate TPU rings in millimeters; requires build123d==0.10.0.
Run: python generate_rings.py [--inputs design_inputs.json] [--output DIRECTORY]
Bores may be overridden per size using bore_override_mm in the input JSON.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from build123d import Align, Compound, Cylinder, export_step, import_step


def check(shape, count, volume):
    assert shape.is_valid, 'Invalid CAD topology'
    assert len(shape.solids()) == count, 'Wrong solid count'
    assert math.isclose(shape.volume, volume, rel_tol=1e-7), 'Unexpected volume'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,default=Path(__file__).with_name('design_inputs.json'))
    parser.add_argument('--output',type=Path,default=Path(__file__).parent)
    args=parser.parse_args()
    data=json.loads(args.inputs.read_text())
    out=args.output
    for sub in ['step_by_size','step_by_location']:
        (out/sub).mkdir(parents=True,exist_ok=True)
    report=[]
    placed=[]
    rows=[]
    total_volume=0
    # Seven independent annuli with an 8+ mm edge gap, no sacrificial connections.
    centers=[(30,35),(75,35),(125,35),(180,35),(30,95),(85,95),(145,95)]
    i=0
    for spec in data['rings']:
        # Basic NPT pitch diameter grows at 1:16 on diameter. 0.8/TPI
        # is basic thread height; adding it to pitch diameter gives major diameter.
        major=(spec['npt_e0_in']+spec['thread_projection_in']/16+.8/spec['tpi'])*25.4
        increment=data['round_bore_up_mm']
        bore=spec.get('bore_override_mm',round(math.ceil((major+data['clearance_diametral_mm'])/increment-1e-9)*increment,6))
        od=spec['outer_diameter_mm']
        h=spec['thickness_mm']
        if not (math.isfinite(bore) and 0 < bore < od and h > 0):
            raise ValueError(f'Invalid dimensions: {spec}')
        ring=Cylinder(od/2,h,align=(Align.CENTER,Align.CENTER,Align.MIN))-Cylinder(bore/2,h+2,align=(Align.CENTER,Align.CENTER,Align.CENTER)).translate((0,0,h/2))
        ring.label=f"{spec['carlon_adapter']}_TPU_ring"
        volume=math.pi/4*(od*od-bore*bore)*h
        check(ring,1,volume)
        # Verify an open center at mid-height, and measured OD / axial thickness.
        assert not ring.is_inside((0,0,h/2))
        assert ring.is_inside(((od+bore)/4,0,h/2))
        bb=ring.bounding_box()
        assert math.isclose(bb.size.X,od,abs_tol=1e-6)
        assert math.isclose(bb.size.Z,h,abs_tol=1e-6) and abs(bb.min.Z)<1e-6
        name=f"{spec['carlon_adapter']}_TPU_sealing_ring.step"
        paths=[out/'step_by_size'/name]+[out/'step_by_location'/f'{loc}.step' for loc in spec['locations']]
        for path in paths:
            assert export_step(ring,path)
            imported=import_step(path)
            check(imported,1,volume)
            report.append(dict(file=str(path.relative_to(out)),solids=1,valid=True,volume_mm3=round(imported.volume,6)))
        for loc in spec['locations']:
            x,y=centers[i]
            part=ring.translate((x,y,0))
            part.label=loc
            placed.append(part)
            rows.append(dict(location=loc,adapter=spec['carlon_adapter'],trade_size=spec['trade_size'],outer_diameter_mm=od,bore_mm=bore,thickness_mm=h,plate_x_mm=x,plate_y_mm=y))
            total_volume+=volume
            i+=1
        spec.update(basic_thread_major_at_shoulder_mm=round(major,6),bore_mm=bore,quantity=len(spec['locations']),radial_ring_width_mm=round((od-bore)/2,6))
    assert i==7, 'Unexpected washer inventory; review plate layout'
    for a in range(len(placed)):
        for b in range(a):
            assert (placed[a] & placed[b]).volume < 1e-8, 'Overlapping rings'
    batch=Compound(label='All seven TPU conduit rings',children=placed)
    check(batch,7,total_volume)
    bb=batch.bounding_box()
    assert bb.min.X>=0 and bb.min.Y>=0 and bb.max.X<230 and bb.max.Y<140
    plate_path=out/'full_set_7_rings.step'
    assert export_step(batch,plate_path)
    check(import_step(plate_path),7,total_volume)
    report.append(dict(file=plate_path.name,solids=7,valid=True,volume_mm3=round(total_volume,6)))
    data['plate_bounds_mm']={'min':list(bb.min),'max':list(bb.max)}
    data['validation']=report
    (out/'dimensions_and_validation.json').write_text(json.dumps(data,indent=2)+'\n')
    with (out/'ring_inventory.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({'step_files':len(report),'rings_in_full_set':i,'plate_size_mm':list(bb.size),'sizes':[{k:s[k] for k in ['carlon_adapter','bore_mm','outer_diameter_mm','thickness_mm','quantity']} for s in data['rings']]},indent=2))

if __name__=='__main__':
    main()
