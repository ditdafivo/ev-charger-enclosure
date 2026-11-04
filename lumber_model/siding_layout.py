"""Nominal top-datum siding layout; dimensions are never derived from rounded text."""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path


def dimension(value):
    fraction=Fraction(round(abs(value)*64),64)
    whole,remainder=divmod(fraction.numerator,fraction.denominator)
    mixed=(str(whole) if whole else '')+(' ' if whole and remainder else '')+(f'{remainder}/{fraction.denominator}' if remainder else '')
    return f'{value:.4f} in (~{"-" if value<0 else ""}{mixed or "0"} in)'


def layout_data(s):
    lap=s.board_width-s.course_pitch
    trim_bottom=s.roof_finished_top_z+.22-40/25.4
    return dict(
        units="inches", datum="level post tops", datum_z=s.frame_top_z,
        status="NOMINAL: verify level datum, production pitch and stand-off before cutting",
        course_pitch_in=s.course_pitch,
        top_board=dict(physical_width_in=s.board_width,
                      exposed_face_height_in=max(0,trim_bottom-s.courses[0][0]),
                      trim_overlap_in=max(0,s.finished_top_z-trim_bottom),
                      upper_profile_allowance_in=lap,
                      note="Away from front fixture relief; physical width includes upper engagement profile"),
        courses=[dict(course=i,installation_order=len(s.courses)-i+1,
                      bottom_z=b,top_z=t,bottom_below_post_top_in=s.frame_top_z-b,
                      top_below_post_top_in=s.frame_top_z-t,
                      groove_below_post_top_in=s.frame_top_z-b if i<len(s.courses) else None,
                      clip_reference_below_post_top_in=s.frame_top_z-(t-lap/2) if i>1 else None)
                 for i,(b,t) in enumerate(s.courses,1)],
        boards=[dict(board=c.name,wall=c.wall,course=c.course,
                     bottom_scribe=[dict(along_in=a,z=z,below_post_top_in=s.frame_top_z-z) for a,z in c.bottom_edge])
                for c in s.cuts],
        attachments=[dict(board=a.board,kind=a.kind,along_in=a.along,
                          below_post_top_in=s.frame_top_z-a.elevation)
                     for a in s.attachments if a.wall!="roof"])


def write_field_layout(s, directory):
    from reportlab.pdfgen import canvas
    directory=Path(directory)
    data=layout_data(s)
    (directory/'siding_field_layout.json').write_text(json.dumps(data,indent=2)+'\n')
    with (directory/'siding_field_layout.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(data['courses'][0]))
        writer.writeheader(); writer.writerows(data['courses'])
    pdf=canvas.Canvas(str(directory/'siding_field_layout.pdf'),pagesize=(612,792))
    def line(y,text,size=10):
        pdf.setFont('Helvetica',size); pdf.drawString(32,y,text)
    line(756,'US135 nominal field layout - distances below LEVEL POST TOPS',13)
    for y,text in zip(range(732,630,-16),[
        'Verify all post tops against one level reference; do not follow individual uneven tops.',
        'Dry-fit production boards and clips. Measure pitch; update course_pitch and rebuild if needed.',
        'Transfer the starter upper edge and seam marks around all four walls with a level.',
        'Scribe only the starter bottom to grade + 3/4 in; retain its upper engagement profile.',
        'Fit T-7-backed starter face screws into wood. Engage full courses upward on AW08.',
        'Check seams against marks as you go; do not accumulate rounded tape increments.',
        'Field correction / measured pitch: __________________________________________']): line(y,text)
    top=data['top_board']
    line(604,'Top board physical width: '+dimension(top['physical_width_in']))
    line(588,'Face visible below US20: '+dimension(top['exposed_face_height_in']))
    line(572,'US20 overlap on physical profile: '+dimension(top['trim_overlap_in']))
    line(548,'Course   Fit order    Bottom / seam below tops       Upper edge       Clip reference',10)
    y=526
    for row in data['courses']:
        line(y,f"{row['course']:>3}          {row['installation_order']:>3}          {dimension(row['bottom_below_post_top_in'])}",9)
        line(y-13,f"Upper edge: {dimension(row['top_below_post_top_in'])}; clip reference: "+('T-7 termination' if row['clip_reference_below_post_top_in'] is None else dimension(row['clip_reference_below_post_top_in'])),9)
        y-=32
    line(120,'Negative offsets are ABOVE the post tops. Clip references are provisional, not drill templates.',9)
    line(104,'Lowest nominal profile edge is removed by the scribe. See each wall elevation for cut heights.',9)
    line(88,'Narrow starter ends: verify screw edge distances; schematic centers are not drilling dimensions.',9)
    pdf.showPage()
    for wall in ('front','left','rear','right'):
        line(756,wall.upper()+' - common course grid / nominal field-fit elevation',13)
        a,b=s.span(wall); scale=min(14,480/(b-a),600/(s.finished_top_z-s.bottom_z))
        x0=58; y0=100
        def point(along,z): return x0+(along-a)*scale,y0+(z-s.bottom_z)*scale
        for part in (p for p in s.board_parts if p.name.startswith(s.name+'_'+wall+'_')):
            along=part.start[0 if wall in ('front','rear') else 1]
            points=[(along+u,part.start[2]+v) for u,v in part.polygon]
            path=pdf.beginPath(); path.moveTo(*point(*points[0]))
            for pt in points[1:]: path.lineTo(*point(*pt))
            path.close(); pdf.setStrokeColorRGB(.55,.55,.55); pdf.drawPath(path)
        for cut in (c for c in s.cuts if c.wall==wall):
            x,y=point(cut.start,cut.top)
            line(y-10,f"C{cut.course}",8)
            for along,z in (cut.bottom_edge[0],cut.bottom_edge[-1]):
                x,y=point(along,z); pdf.setFont('Helvetica',7)
                pdf.drawString(x,y-9,f"{s.frame_top_z-z:.4f} below")
        for bottom,_ in s.courses[:-1]:
            x,y=point(a,bottom); xx,_=point(b,bottom)
            pdf.setStrokeColorRGB(.1,.1,.1); pdf.line(x,y,xx,y)
            pdf.setFont('Helvetica',8); pdf.drawString(xx+5,y,f"{s.frame_top_z-bottom:.4f}")
        line(70,'Endpoint labels are scribe distances below post tops; maintain grade clearance between endpoints.',9)
        line(54,'Field correction: __________________________________________________________',10)
        pdf.showPage()
    pdf.save()
    # Actual generated parts, with bores and trim relief preserved in every review.
    front=s.min_y-s.exterior_offset
    for name,z,height,section in (
        ('joint',s.courses[1][0]-1,3,False),
        ('starter',min(z for c in s.cuts for _,z in c.bottom_edge),8,False),
        ('top',s.finished_top_z-7,9,False),
        ('top_section',s.finished_top_z-7,9,True)):
        lo=s.min_x+1 if section else s.min_x-2
        width=1 if section else s.max_x-s.min_x+4
        parts='\n'.join(f'  render_siding_part({p.scad_record()});' for p in s.parts
                         if all(p.start[i]<hi and p.start[i]+p.size[i]>low for i,low,hi in
                                ((0,lo,lo+width),(1,front-2,front+3),(2,z,z+height))))
        text=('// Inches; provisional groove and clip envelopes.\nuse <model.scad>\n'
              '$vpr=[90,0,0]; $vpd=55;\n'
              f'$vpt=[{(s.min_x+s.max_x)/2},{front},{z+height/2}];\n'
              'intersection() { union() {\n'+parts+'\n}\n'
              f'translate([{lo},{front-2},{z}]) cube([{width},5,{height}]);\n}}\n')
        (directory/f'siding_review_{name}.scad').write_text(text)
