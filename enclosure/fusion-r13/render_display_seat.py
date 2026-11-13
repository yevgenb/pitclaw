"""Plot the nominal display fit using a section through the native top mesh."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/pitclaw-display-fit-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
import trimesh

OUT=Path(__file__).resolve().parent
mesh=trimesh.load(OUT/'native-stl/carrier-top.stl',force='mesh')
segments=trimesh.intersections.mesh_plane(mesh,[0,1,0],[0,0,0])[:,:,[0,2]]
fig,axes=plt.subplots(1,2,figsize=(12,5),sharex=True,sharey=True)
for ax,front,title in zip(axes,[41.9,43.7],['Original fit: 1.5-1.8 mm air gap','Revised top: glass seated']):
    ax.add_collection(LineCollection(segments,colors='#293c52',linewidths=2))
    ax.add_patch(Rectangle((22,front-1.45),8,1.45,facecolor='#89c5d8',edgecolor='#256b83'))
    ax.text(23.4,front-.5,'Glass',color='#163e4b',weight='bold')
    ax.text(27.4,44.25,'Top shell',color='#293c52',weight='bold')
    ax.plot([24.5,32],[43.7,43.7],ls=':',lw=1,color='#5b6470')
    ax.annotate('Bezel underside\nZ43.7',xy=(30.65,43.7),xytext=(30.9,42.1),arrowprops={'arrowstyle':'->','color':'#5b6470'},fontsize=9,color='#37404b')
    if front<43.7:
        ax.annotate('1.5-1.8 mm open',xy=(28.8,42.8),xytext=(26.9,40.8),arrowprops={'arrowstyle':'->','color':'#b66d21'},color='#975817',fontsize=10)
    else:
        ax.annotate('Inactive border\ntouches the ledge',xy=(28.8,43.7),xytext=(27,41.1),arrowprops={'arrowstyle':'->','color':'#247451'},color='#247451',fontsize=10)
    ax.set(title=title,xlim=(22.5,33.7),ylim=(40.3,45.45),xlabel='X (mm)')
    ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False)
    ax.grid(alpha=.12);ax.set_axisbelow(True)
axes[0].set_ylabel('Assembly Z (mm)')
fig.suptitle('Display seating beneath the bezel',fontsize=17,weight='bold',y=.93)
fig.text(.5,.085,'Top-mesh section at Y=0; original glass position inferred from the reported gap. Exterior stays at Z44.9.',ha='center',fontsize=10)
fig.text(.5,.04,'Retainer posts are 1.8 mm shorter. Fit 0-0.3 mm shims at the four outer anchors to seat the glass without force.',ha='center',fontsize=10,color='#745733')
fig.subplots_adjust(top=.8,bottom=.23,wspace=.2)
fig.savefig(OUT/'display-seat-section.png',dpi=180)
