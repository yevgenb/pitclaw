"""Add dimensioned visual models for parts missing from the KiCad STEP export.

Run inside the r9 Fusion document, after the native PCB STEP has been rotated
180 degrees about Z and translated [0,4.5,7.5]mm. This uses actual footprint XY,
reviewed body dimensions and explicitly simplified cosmetic geometry.
These visual models do not establish supplier-complete mechanical tolerances.
"""
import adsk.core as C
import adsk.fusion as F
import json,runpy,math
from pathlib import Path

OUT=Path(__file__).resolve().parent
HELPERS=runpy.run_path(str(OUT/'support/build_fusion_r8.py'))
DATA={p['ref']:p for p in json.loads((OUT/'populated/placed-components.json').read_text())}
COLORS={'black':(39,43,48),'gray':(137,147,154),'silver':(184,190,192),
        'gold':(198,151,54),'yellow':(220,158,51),'blue':(34,101,158),
        'green':(35,105,71),'white':(215,218,214),'navy':(34,55,75)}
NEW,CUT=HELPERS['NEW'],HELPERS['CUT']


def xy(u,v): return 30-u,v-41.5


def run(_context):
    app=C.Application.get(); d=F.Design.cast(app.activeProduct)
    assert app.activeDocument.name=='PitClaw enclosure r9 - populated carrier'
    group=d.rootComponent.occurrences.addNewComponent(C.Matrix3D.create())
    group.component.name='REFERENCE - custom populated carrier parts'
    evidence=[]

    def part(ref,basis):
        o=group.component.occurrences.addNewComponent(C.Matrix3D.create());c=o.component
        c.name=ref+' - '+(DATA[ref]['value'] if ref in DATA else 'Adafruit 5807 USB PD module')
        c.attributes.add('PitClaw','model_basis',basis)
        evidence.append({'ref':ref,'basis':basis})
        return c

    def paint(feat,color,label):
        for b in feat.bodies:
            b.name=label
            HELPERS['color_body'](d,b,'PCB visual '+color,COLORS[color])
        return feat

    def box(c,label,center,w,h,z,t,color,r=.1,axis='XY',op=NEW):
        feat=HELPERS['rr'](c,label,center,w,h,r,z,t,op,axis)
        if op==NEW:paint(feat,color,label)
        return feat

    def cyl(c,label,centers,diam,z,t,color,axis='XY',op=NEW):
        feat=HELPERS['circles'](c,label,centers,diam,z,t,op,axis)
        if op==NEW:paint(feat,color,label)
        return feat

    def pins(c,ref,diam=.6,z=6.5,height=3.5):
        points=[xy(*p['xy_mm']) for p in DATA[ref]['pads'] if p['num']]
        cyl(c,ref+' leads',points,diam,z,height,'silver')

    # The library capacitor models have generic 8/10mm body heights. They are
    # hidden in the imported STEP and replaced with the selected BOM dimensions.
    for ref,diam,height in [('C1',10,12.5),('C3',8,11.5)]:
        c=part(ref,'Selected Rubycon nominal diameter/body height; simplified vent and sleeve.')
        pts=[p['xy_mm'] for p in DATA[ref]['pads']]
        center=xy(sum(p[0] for p in pts)/2,sum(p[1] for p in pts)/2)
        cyl(c,ref+' electrolytic sleeve',[center],diam,9.4,height,'navy')
        cyl(c,ref+' aluminum top',[center],diam-.4,9.4+height-.15,.16,'silver')
        pins(c,ref)

    for ref in ['C2','C4','C10','C11','C12']:
        c=part(ref,'TDK FG28 footprint body4x2.5mm, seated-height allowance5.5mm; cosmetic rounded rectangle.')
        pts=[p['xy_mm'] for p in DATA[ref]['pads']]
        center=xy(sum(p[0] for p in pts)/2,sum(p[1] for p in pts)/2)
        vertical=abs(pts[1][1]-pts[0][1])>1
        box(c,ref+' ceramic body',center,2.5 if vertical else 4,4 if vertical else 2.5,10.6,4,'yellow',.35)
        pins(c,ref,.55,6.5,4.2)

    c=part('K1','Omron G5Q-1 reviewed20.3x10.3mm outline and16.2mm maximum seated height; simple housing.')
    box(c,'K1 relay case',(-4.15,13.65),10.3,20.3,9.5,15.8,'black',.25)
    pins(c,'K1',.7)
    c=part('U2','Traco TSR2N nominal14x7.6x10.2mm body at actual F.Fab offset; housing simplified.')
    box(c,'U2 converter case',(10.46,31.61),14,7.6,9.1,10.2,'black',.2)
    pins(c,'U2',.64)

    c=part('Q1','IRF5305 flat tab-down, reviewed10.67x16.51 body envelope,1mm insulating gap; formed leads simplified.')
    box(c,'Q1 insulating support',(-15.84,-14.755),10.4,16.2,9.1,1,'white',.2)
    box(c,'Q1 metal tab',(-15.84,-14.755),10.67,16.51,10.1,.9,'silver',.2)
    cyl(c,'Q1 tab screw hole',[(-15.84,-20.03)],4.08,10.08,1,'silver',op=CUT)
    box(c,'Q1 molded body',(-15.84,-11.325),10.67,9.65,11,3.93,'black',.2)
    for p in DATA['Q1']['pads']:
        x,y=xy(*p['xy_mm'])
        box(c,'Q1 bent lead '+p['num'],(x,-3.5),.65,6,11.6,.5,'silver',0)
        cyl(c,'Q1 lead tail '+p['num'],[(x,y)],.65,6.3,5.8,'silver')

    c=part('BZ1','TDK PS1240P02BT footprint center/diameter12.2mm,7.8mm seated allowance; sound port cosmetic.')
    center=xy(6.8,43)
    cyl(c,'BZ1 piezo housing',[center],12.2,9.1,7.8,'black')
    cyl(c,'BZ1 sound opening',[center],3,15.7,1.22,'black',op=CUT)
    pins(c,'BZ1',.6)

    c=part('J2','Amphenol RJHSE5080 reviewed15.75x14.99x13.21 housing and flush face; cavity/contacts simplified.')
    box(c,'J2 RJ45 housing',(20.5,44.505),15.75,14.99,9.1,13.21,'black',.2)
    box(c,'J2 plug cavity',(20.5,15.705),11.8,8,49,3.03,'black',.2,'XZ',CUT)
    box(c,'J2 latch recess',(20.5,10.95),5,1.5,50,2.03,'black',.1,'XZ',CUT)
    for i in range(8):
        box(c,'J2 contact '+str(i+1),(16.9+i*1.02,50.3),.35,2.5,11.78,.12,'gold',.04)
    pins(c,'J2',.55)

    c=part('J9','Tensility5400133 reviewed14.4x9x10.8 housing,axis6.5mm above PCB; bore and center pin simplified.')
    box(c,'J9 barrel housing',(3.5,44.8),9,14.4,9.1,10.8,'black',.15)
    cyl(c,'J9 barrel opening',[(3.5,15.6)],6.3,48.5,3.55,'black','XZ',CUT)
    cyl(c,'J9 center pin',[(3.5,15.6)],2.1,49,2.6,'silver','XZ')
    pins(c,'J9',.65)

    for ref,x in [('J4',17),('J5',0),('J6',-17)]:
        c=part(ref,'SameSkyMJ12503A5.1mm housing,front nose at reviewed Y-44.5,axis2.55mm; contacts omitted.')
        box(c,ref+' jack housing',(x,-37.5),5.1,8,9.1,5.1,'black',.15)
        cyl(c,ref+' front collar',[(x,11.65)],4,-44.5,3.1,'silver','XZ')
        cyl(c,ref+' 2.5mm plug bore',[(x,11.65)],2.5,-44.52,3.3,'black','XZ',CUT)
        pins(c,ref,.55)

    c=part('J8','Reviewed28x17mm blue ADS1115 module at actual1x10 socket row; socket8.5mm and IC details illustrative.')
    points=[xy(*p['xy_mm']) for p in DATA['J8']['pads']]
    box(c,'J8 female socket',(5.57,-8.5),25.4,2.54,9.1,8.5,'black',.15)
    cyl(c,'J8 socket receptacles',points,1.15,16.8,.82,'black',op=CUT)
    box(c,'ADS1115 blue module PCB',(5.54,-15.5),28,17,17.6,1.6,'blue',.3)
    box(c,'ADS1115 IC visual body',(5.54,-17.5),5,4,19.2,1.2,'black',.12)
    for x,y in points:
        cyl(c,'ADC header pin',[(x,y)],.64,7,12.5,'gold')

    c=part('MOD1','Adafruit5807 publishedPCBoutline/mounts and reviewed USBface. Socket/hardware simplified; small SMD parts omitted.')
    box(c,'Adafruit5807 PCB',(-14.5,37.1095),20.32,23.495,12.1,1.6,'black',.2)
    mounts=[(-6.753,46.317),(-21.993,46.317)]
    cyl(c,'5807 M2 mounting holes',mounts,2.5,12.08,1.64,'black',op=CUT)
    for center in mounts:
        cyl(c,'3mm nylon spacer',[center],5,9.1,3,'white')
        cyl(c,'M2 head washer',[center],5,13.7,.3,'silver')
        cyl(c,'M2 screw head',[center],4,14,1.5,'silver')
    box(c,'USB-C metal shell',(-14.5,15.2),8.94,3.2,42.5,7.5,'silver',1.2,'XZ')
    box(c,'USB-C mouth',(-14.5,15.2),7.5,2,48,2.02,'black',.9,'XZ',CUT)
    box(c,'USB-C inner tongue',(-14.5,49),6.2,1.8,14.95,.5,'black',.12)
    for o in group.component.occurrences:
        for s in o.component.sketches:s.isLightBulbOn=False
    (OUT/'populated/custom-model-provenance.json').write_text(json.dumps(evidence,indent=2)+'\n')
    app.activeViewport.fit()
    print(json.dumps({'custom_components':len(evidence),'refs':[p['ref'] for p in evidence]}))
