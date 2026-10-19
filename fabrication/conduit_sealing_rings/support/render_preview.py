import os
os.environ['MPLCONFIGDIR']='/tmp/conduit-matplotlib'
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from build123d import import_step
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'ring_inventory.csv').open()))
fig,ax=plt.subplots(figsize=(12,7),facecolor='#f6f7f9')
ax.set_facecolor('#f6f7f9')
colors={'E943D':'#259aa0','E943E':'#5470c6','E943F':'#a66a35','E943G':'#8455ac'}
for row in rows:
    shape=import_step(root/'step_by_location'/(row['location']+'.step'))
    verts,tris=shape.tessellate(.03,.1)
    x,y=float(row['plate_x_mm']),float(row['plate_y_mm'])
    # Plot actual STEP triangulation's horizontal top faces.
    polygons=[]
    for tri in tris:
        points=[verts[i] for i in tri]
        if all(abs(p.Z-2.032)<1e-5 for p in points):
            polygons.append([(p.X+x,p.Y+y) for p in points])
    ax.add_collection(PolyCollection(polygons,facecolor=colors[row['adapter']],edgecolor='none',antialiaseds=False))
    ax.text(x,y,row['adapter'],ha='center',va='center',weight='bold',fontsize=10,color='#263245')
    ax.text(x,y-float(row['outer_diameter_mm'])/2-3,row['trade_size']+' in',ha='center',va='top',fontsize=10)
ax.set_aspect('equal');ax.set_xlim(5,210);ax.set_ylim(0,130)
ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)')
ax.spines[['top','right']].set_visible(False)
fig.suptitle('Conduit sealing rings — full seven-ring set',fontsize=19,weight='bold',x=.1,ha='left')
fig.text(.1,.88,'Top view of exported STEP solids • all rings 2.032 mm thick • broad face on build plate',fontsize=11,color='#435168')
fig.text(.1,.03,'E943D × 2     E943E × 3     E943F × 1     E943G × 1     |     Physical fit and sealing performance require verification.',fontsize=10,color='#435168')
fig.subplots_adjust(left=.1,right=.96,bottom=.13,top=.83)
fig.savefig(root/'preview.png',dpi=150)
