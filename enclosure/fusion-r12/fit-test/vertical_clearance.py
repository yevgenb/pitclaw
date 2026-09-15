"""Fit-test guide clearances and two support lands."""

SCAD = r'''
module guide_roomier_cavity() {
    // One cavity solid exactly combines the constant roof with the frozen
    // piecewise floor; no coincident core/relief side faces remain.
    stations=[[-52.1,3.5],[-50.6,3.5],[-50,3.8],[-49.2,3.8],
              [-48.6,3.5],[-44.6,3.5],[-44,3.8],[-43,3.8]];
    roof=41.8+sqrt(2)*.4;
    points=[for(p=stations) each [[32.7,p[0],p[1]],[36.3,p[0],p[1]],
                                   [36.3,p[0],roof-36.3],[32.7,p[0],roof-32.7]]];
    faces=concat([[3,2,1,0],[28,29,30,31]],
        [for(i=[0:6],j=[0:3]) [4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j]]);
    polyhedron(points=points,faces=faces);
}
module guide_support_collision(y,drop) {
    intersection() {
        bottom_shell();
        translate([0,0,-drop]) intersection() {
            probe_fascia();
            for(s=[-1,1]) scale([s,1,1])
                box_bounds(33.3,36.1,y-.2,y+.2,3.7,10);
        }
    }
}
module fascia_segment(dy0,dy1,dz0,dz1) {
    //0.0002mm lift clears intentional bearing contact; kernel half-size5nm.
    minkowski() {
        probe_fascia();
        hull() for(q=[[dy0,dz0],[dy1,dz1]])
            translate([-.000005,q[0]-.000005,q[1]+.000195])
                cube([.00001,.00001,.00001]);
    }
}
module lowered_entry_collision() {
    intersection() {
        union() {
            fascia_segment(-12,-7.6,-.3,-.3);
            fascia_segment(-7.6,-7,-.3,0);
            fascia_segment(-7,0,0,0);
        }
        union() {
            intersection() {
                bottom_shell();
                union() {
                    box_bounds(-100,100,-100,-43.0001,-1,60);
                    box_bounds(-100,100,-42.9999,100,-1,60);
                }
            }
            carrier_sweep(carrier_case_offset_y,carrier_case_offset_y,0,0);
        }
    }
}
'''

def candidate(source):
    old='sqrt(2)*.25'
    if source.count(old)!=2:raise ValueError('Unexpected roof-gap expression count')
    source=source.replace(old,'sqrt(2)*.4')
    old='for(s=[-1,1]) scale([s,1,1]) guide_cavity();'
    if source.count(old)!=1:raise ValueError('Unexpected guide cavity call count')
    source=source.replace(old,'for(s=[-1,1]) scale([s,1,1]) guide_roomier_cavity();')
    point='else if(part=="shell-closure-with-fascia-check")'
    extra='''else if(part=="guide-support-front-005-check") guide_support_collision(-49.6,.05);
else if(part=="guide-support-front-010-check") guide_support_collision(-49.6,.1);
else if(part=="guide-support-rear-005-check") guide_support_collision(-43.5,.05);
else if(part=="guide-support-rear-010-check") guide_support_collision(-43.5,.1);
else if(part=="lowered-entry-check") lowered_entry_collision();
'''
    if source.count(point)!=1:raise ValueError('Unexpected fit-test dispatch count')
    return source.replace(point,extra+point)+SCAD

POSITIVE_CHECK = '''        if check.part.startswith(("guide-capture-","guide-support-")):
            if not target.is_file() or process.returncode != 0:
                raise ValueError("Guide did not block the required motion")
            import math
            import numpy as np
            import trimesh
            contact=trimesh.load(target,force="mesh",process=True)
            if not (contact.is_watertight and contact.is_winding_consistent):
                raise ValueError("Guide contact witness is not closed and consistently wound")
            support=check.part.startswith("guide-support-")
            if support:
                y=-49.6 if "front" in check.part else -43.5
                depth=.4
                movement=-.05 if "005" in check.part else -.1
                expected=2.7*depth*abs(movement)
            else:
                stations={"guide-capture-front-check":-51.8,
                          "guide-capture-early-check":-50.8,
                          "guide-capture-midfront-check":-49,
                          "guide-capture-middle-check":-47,
                          "guide-capture-rear-check":-44}
                y=stations[check.part];depth=.2;movement=.7
                expected=2.7*depth*(movement-math.sqrt(2)*.4)
            if not (abs(contact.bounds[0][1]-(y-depth/2))<.001 and
                    abs(contact.bounds[1][1]-(y+depth/2))<.001):
                raise ValueError("Guide contact is outside its intended depth station")
            volumes=[]
            for sign in [-1,1]:
                mask=np.all(sign*contact.vertices[contact.faces,0]>0,axis=1)
                side=contact.submesh([mask],append=True,repair=False)
                volume=float(side.volume)
                if not (len(side.faces)>0 and side.is_watertight and volume>0
                        and abs(volume-expected)<.003):
                    raise ValueError("Guide contact does not match the geometry-derived positive volume")
                volumes.append(volume)
            record["contact"]={"station_y_mm":y,"translation_z_mm":movement,
                "slice_depth_mm":depth,"left_right_intersection_mm3":volumes,
                "expected_volume_each_mm3":expected,"volume_tolerance_mm3":.003,
                "witness_sha256":sha256(target),"lid_present":False}
            record["result"]="PASS: both lands support downward motion" if support else "PASS: both guides block upward motion"
'''

def verifier(source):
    point='    # Use the full edge allowance with each stack/X corner.'
    extra='''    for part in ("guide-support-front-005-check","guide-support-front-010-check",
                 "guide-support-rear-005-check","guide-support-rear-010-check",
                 "lowered-entry-check"):
        checks.append(Check(part,part,(1.6,1.6,3,0,0)))
'''
    if source.count(point)!=1:raise ValueError('Unexpected scenario insertion marker')
    source=source.replace(point,extra+point)
    start=source.index('        if check.part.startswith("guide-capture-"):')
    end=source.index('        elif EMPTY_MESSAGE in log',start)
    return source[:start]+POSITIVE_CHECK+source[end:]
