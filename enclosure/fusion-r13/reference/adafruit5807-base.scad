// Adafruit5807 carrier base. Units mm; one printable solid.
// Local print axes: X=10.16-Eagle_u, Y=Eagle_v, Z=height above carrier top.
// The PCB bears at Z3.0 TOTAL, not3.0 plus the0.8mm floor.
// Two M2 clamps resist extraction. Rear stops resist insertion. The curved
// front features are side/corner guides, not positive forward load stops.
// Source: Adafruit-USB-Type-C-Power-Delivery-Dummy-Breakout-PCB Eagle board.
// use <adafruit5807-base.scad> imports ada5807_base() without rendering it.

module ada5807_rounded_2d(x0,x1,y0,y1,r) {
    translate([(x0+x1)/2,(y0+y1)/2])
        offset(r=r) square([x1-x0-2*r,y1-y0-2*r],center=true);
}
module ada5807_board_2d(extra=0) {
    ada5807_rounded_2d(-extra,20.32+extra,-extra,23.495+extra,2.54+extra);
}
module ada5807_band_2d(inner_offset,v0,v1) {
    intersection() {
        difference() {
            ada5807_board_2d(1.5);
            ada5807_board_2d(inner_offset);
        }
        translate([-5,v0]) square([30,v1-v0]);
    }
}
module ada5807_lower_2d() {
    union() {
        ada5807_band_2d(-1.5,.9,22.8);
        intersection() { ada5807_board_2d(); square([20.32,1.1]); }
        for(u=[6.2,12.9]) translate([u,-1.5]) square([1.6,2.6]);
        for(u=[2.413,17.653]) translate([u,20.955]) circle(d=5);
    }
}
module ada5807_upper_2d() {
    union() {
        ada5807_band_2d(.3,6.2,22.8);
        for(u=[6.2,12.9]) translate([u,-1.5]) square([1.6,1.2]);
    }
}
module ada5807_clearances_2d() {
    ada5807_rounded_2d(.8,19.52,1.3,6.3,.3);
    for(ur=[[4.84,7.995],[12.325,15.48]])
        ada5807_rounded_2d(ur[0],ur[1],16.3,24,.3);
    for(u=[2.413,17.653]) translate([u,20.955]) circle(d=2.4);
}
module ada5807_base() {
    $fn=96;
    // Merge each horizontal section in2D before extrusion. Hidden0.02mm
    // overlaps join adjacent levels while preserving all exposed surfaces.
    mirror([1,0,0]) translate([-10.16,0,0]) union() {
        linear_extrude(height=.8) difference() {
            union() { ada5807_board_2d(); ada5807_lower_2d(); }
            ada5807_clearances_2d();
        }
        translate([0,0,.78]) linear_extrude(height=2.22) difference() {
            ada5807_lower_2d(); ada5807_clearances_2d();
        }
        translate([0,0,2.98]) linear_extrude(height=1.22) difference() {
            ada5807_upper_2d(); ada5807_clearances_2d();
        }
    }
}

ada5807_base();
