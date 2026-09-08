// PitClaw Rev B carrier enclosure CONCEPT: two outer halves + internal retainer.
// Units mm. WT32 uses centered PCB coordinates; the carrier is shifted toward
// the power end by carrier_case_offset_y from the generated interface.
// This is a fit prototype, not a mechanically released / weather-rated case.
// WT32 OEM holes are REAR blind bosses: do not screw through the glass / PCB.
// See enclosure/README.md for source drawings and the physical measurement gate.
include <carrier-interface.scad>

// Views: assembled, exploded, section, top, bottom, retainer, print.
// Single-part views are oriented flat on the build plate.
// Diagnostics insertion-check, carrier-installation-check and
// electronics-closure-check must render EMPTY.
part = "assembled";
show_electronics = true;
show_fasteners = true;
$fn = 48;
eps = 0.02;

// Shell and registration. Closure screws sit beyond the free LONG board sides.
case_width = 86;
case_length = 104;
wall = 2.5;
floor_thickness = 2.5;
front_plate = 3;
corner_radius = 5;
case_closure_xy = [[-38,-28],[38,-28],[-38,28],[38,28]];
locating_lip_height = 2;
locating_lip_wall = 1.2;
locating_lip_clearance = 0.3;

// Common short insert: Ruthex RX-M3Sx4.0, OD4.6, L4.0, pilot4.0.
// Print an insertion coupon in the chosen material before committing the case.
insert_od = 4.6;
insert_length = 4;
insert_pilot = 4.0;
insert_bore_depth = 5;
insert_boss_od = 9;
carrier_standoff = 5;
minimum_floor_under_insert = 2.5;
m3_clearance = 3.4;
m3_head_clearance = 6.4;
closure_head_recess = 3.2;
// At the default stack, M3x18 closure screws give 3.9 mm insert engagement
// and 1.1 mm bore-bottom clearance. Verify engagement on the actual print.
// Carrier: M3x6 + 0.5 mm washer. Retainer: M3x6 button heads, without washers.

// Conservative vertical stack. Component and cable envelopes require samples.
carrier_component_height = 16;    // provisional; requires Q1 flat on the carrier
                                  // covers mated JST / socketed ADC envelopes
// K1 is modeled separately from the CAD contract at 16.2 mm seated height.
// Its local reserved gap is 2.8 mm; do not pretend it fits the 16 mm envelope.
board_gap = 3;                    // below the lowest display/retainer screw head
wt32_size = [60,92,10.8];          // footprint and nominal rear mounting-boss datum
// The 10.8 mm datum is not a maximum rear-component or mated-connector height.
// Fit-check those parts and the harness within the reserved rear stack below.
wt32_mount_xy = [[4.305,6.52],[55.695,6.52],
                 [4.305,81.66],[55.695,81.66]];
wt32_active = [49.56,74.04];       // manufacturer drawing, centered on front
window_size = [50.6,75.1];        // provisional touch/display edge allowance
glass_recess = 1.5;
front_pad_compressed = 0.3;       // soft perimeter strip on inactive glass border
module_side_clearance = 0.4;      // never rigidly pinch the glass edge

// The manufacturer's side view places the rear boss face 10.8 mm behind glass.
// Verify the purchased module, screw type/engagement, and cable exits physically.
// Four small screws pass through retainer INTO the OEM's rear blind bosses.
wt32_rear_mount_depth = 10.8;     // glass front -> OEM boss rear face; sample-verify
retainer_thickness = 2.5;        // retain stiffness along the long, narrow webs
small_screw_head_height = 2;
small_screw_clearance = 2.8;      // provisional; OEM pilot is shown as diameter2.3
small_screw_head_od = 4.8;
retainer_outer = [70,96];
retainer_inner = [60.8,92.8];
retainer_tab_od = 6.4;
retainer_anchor_xy = [[-35.5,0],[35.5,0]];
retainer_anchor_od = 9;
retainer_anchor_head_od = 5.7;   // ISO 7380 M3 button head, without washer
retainer_anchor_head_height = 1.65;
retainer_anchor_pilot = insert_pilot; // same M3 heat-set insert as lower shell
retainer_anchor_bore_depth = insert_bore_depth;

// RJ45 and barrel receptacle faces meet the flat exterior wall. USB-C sits
// 2 mm behind it, level with the floor of an access pocket for the cable boot.
// The three independent openings retain solid plastic between the sockets.
carrier_slide_start_y = 0.5;
carrier_slide_lift = 0.3;
power_profile_clearance = 0.3;
carrier_tail_projection = 3;     // maximum clipped lead/solder depth; inspect build
probe_axis_above_pcb = 3.5;       // measure MJ1-2503A sample
probe_plug_opening = 10.5;
rj45_face_size = [15.75,13.21];  // Amphenol RJHSE-5080 housing, W x H above PCB
rj45_body_depth = 14.99;
barrel_face_size = [9,10.8];     // Tensility 54-00133 full housing; parameterized
barrel_body_depth = 14;
barrel_axis_above_pcb = 6.5;     // bore axis, not the housing center
usb_axis_above_pcb = 6.1;         // 3mm spacer + modulePCB + receptacle: measure
usb_face_size = [8.94,3.2];      // shell width from Eagle; height is sample-gated
usb_pocket_size = [20,10];
usb_pocket_depth = 2;
usb_inward_backing = 1;
usb_socket_opening = [9.54,4.1]; // fitted shell plus clearance and 0.3 mm seat lift
power_face_size = [rj45_face_size,barrel_face_size,usb_face_size];
power_face_center_z = [rj45_face_size[1]/2,barrel_face_size[1]/2,
                       usb_axis_above_pcb];
power_face_corner_r = [0.2,0.2,0.4];

pd_pcb_size = [20.32,23.495,1.6];
pd_spacer_height = 3;
pd_face_overhang = 1.143;
pd_pcb_front_y = carrier_power_face_y[2]-pd_face_overhang;
// Consume the actual H5/H6 coordinates exported from the carrier CAD. These
// holes sit 0.127 mm left of the module center; do not assume +/-7.62.
pd_mount_xy = carrier_pd_mount_xy;
pd_hardware_diameter = 5;        // maximum head/washer/nut envelope, verified BOM
pd_hardware_below_pcb = 3.3;     // nut, washer and screw tip; inspect actual stack
pd_hardware_head_height = 2;    // total upper screw head + washer; inspect stack
blind_pocket_clearance = 0.2;

// Derived datums: Z=0 is the bottom exterior, +Z points toward the screen.
carrier_bottom_z = floor_thickness + carrier_standoff;
carrier_top_z = carrier_bottom_z + carrier_board_mm[2];
// Retainer and heads reserve 15.3 mm behind the glass with current parameters.
// Actual WT32 rear components and mated connectors still require measurement.
display_rear_depth = max(wt32_size[2], wt32_rear_mount_depth +
                        retainer_thickness + small_screw_head_height);
glass_front_z = carrier_top_z + carrier_component_height + board_gap +
                display_rear_depth;
case_height = glass_front_z + glass_recess;
power_opening_roof_z = max(
    max([for(i=[0:1]) carrier_top_z+power_face_center_z[i]+
        power_face_size[i][1]/2+power_profile_clearance+carrier_slide_lift]),
    carrier_top_z+usb_axis_above_pcb+usb_pocket_size[1]/2);
// Preserve the existing seam and closure grip after fitting the smaller ports.
// At least 2 mm of plastic must remain above every opening.
seam_z = max(carrier_top_z + carrier_component_height + 2,
             carrier_top_z+18.5,power_opening_roof_z + 2);
retainer_top_z = glass_front_z - wt32_rear_mount_depth;
retainer_bottom_z = retainer_top_z - retainer_thickness;
front_pocket_roof_z = glass_front_z + front_pad_compressed;
inside_width = case_width - 2*wall;
inside_length = case_length - 2*wall;
lip_width = inside_width - 2*locating_lip_clearance;
lip_length = inside_length - 2*locating_lip_clearance;

function local_xy(p) = [p[0]-carrier_board_mm[0]/2,
                        p[1]-carrier_board_mm[1]/2];
function carrier_local_xy(p) = [p[0]-carrier_board_mm[0]/2,
                               p[1]-carrier_board_mm[1]/2+carrier_case_offset_y];
function dist2(a,b) = sqrt(pow(a[0]-b[0],2)+pow(a[1]-b[1],2));
pd_pcb_front_local_y = pd_pcb_front_y-46+carrier_case_offset_y;
pd_pcb_wall_clearance = inside_length/2-pd_pcb_front_local_y;
pd_hardware_wall_clearance = min([for(p=pd_mount_xy) inside_length/2-
    (p[1]-46+carrier_case_offset_y+pd_hardware_diameter/2)]);
usb_face_setback = case_length/2-
    (carrier_power_face_y[2]-46+carrier_case_offset_y);
usb_pocket_floor_y = case_length/2-usb_pocket_depth;
usb_backing_inner_y = inside_length/2-usb_inward_backing;
usb_nominal_floor = usb_pocket_floor_y-usb_backing_inner_y;
usb_pcb_relief_skin = usb_pocket_floor_y-
    (pd_pcb_front_local_y+blind_pocket_clearance);
usb_head_relief_skin = min([for(p=pd_mount_xy) usb_pocket_floor_y-
    (p[1]-46+carrier_case_offset_y+pd_hardware_diameter/2+blind_pocket_clearance)]);
usb_pocket_channel_gap = carrier_top_z+usb_axis_above_pcb-usb_pocket_size[1]/2-
    (carrier_top_z+power_profile_clearance+carrier_slide_lift);

assert(carrier_board_mm == [60,92,1.6], "Review enclosure after board change");
assert(insert_boss_od >= insert_od+2*1.6, "Insert boss wall too thin");
assert(floor_thickness+carrier_standoff-insert_bore_depth >=
       minimum_floor_under_insert, "Blind insert bore thins the bottom floor");
assert(insert_bore_depth >= insert_length+1, "Insufficient insert melt relief");
assert(front_pad_compressed > 0 && glass_recess-front_pad_compressed >= 1,
       "Need compliant interface plus at least1mm plastic front rim");
assert(window_size[0] > wt32_active[0] && window_size[1] > wt32_active[1],
       "Window masks active display");
assert(retainer_outer[0] < inside_width && retainer_outer[1] < inside_length,
       "Retainer does not fit shell");
assert(retainer_bottom_z-small_screw_head_height -
       (carrier_top_z+carrier_component_height) >= board_gap-eps,
       "Retainer screw head collides with carrier envelope");
assert(!is_undef(carrier_case_offset_y), "Regenerate the carrier interface");
assert(inside_length/2 > 46-carrier_probe_face_y-carrier_slide_start_y,
       "Probe noses cannot lower at the initial installation offset");
assert(max(carrier_power_face_y)-46+carrier_slide_start_y < inside_length/2,
       "Power faces cannot lower at the initial installation offset");
assert(pd_pcb_wall_clearance >= 0.2, "USB module PCB needs clearance from normal wall");
assert(pd_hardware_wall_clearance >= 0.15, "USB mounting hardware touches normal wall");
assert(abs(usb_face_setback-2)<eps, "USB-C face must sit 2 mm behind the exterior");
assert(abs(usb_face_setback-usb_pocket_depth)<eps,
       "USB-C face must be level with the access-pocket floor");
assert(usb_nominal_floor >= 1.5, "USB pocket backing is too thin");
assert(usb_pcb_relief_skin >= 0.94, "Hidden USB PCB relief breaks through the pocket floor");
assert(usb_head_relief_skin >= 0.98, "Hidden USB head relief breaks through the pocket floor");
assert(usb_pocket_channel_gap >= 0.5-eps, "USB pocket overlaps the carrier-edge channel");
for(face_y=[carrier_power_face_y[0],carrier_power_face_y[1]])
    assert(abs(face_y+carrier_case_offset_y-46-case_length/2)<0.02,
           "Power receptacle face is not flush with the exterior panel");
assert(retainer_bottom_z > seam_z, "Retainer must stay with upper half");
assert(seam_z >= power_opening_roof_z+2-eps,
       "Power opening leaves less than 2 mm wall below the seam");
assert(retainer_top_z > seam_z+1,
       "Retainer insertion relief reaches the final anchor hard stops");
assert(case_height-retainer_top_z-retainer_anchor_bore_depth >= 2.5,
       "Retainer insert bore leaves too little front material");
for (p=case_closure_xy)
    assert(abs(p[0])-insert_boss_od/2 > carrier_board_mm[0]/2,
           "Closure hardware overlaps either board");
for (p=retainer_anchor_xy, q=case_closure_xy)
    assert(dist2(p,q) > (retainer_anchor_od+insert_boss_od)/2+1,
           "Display anchor intersects closure boss");

echo("DRAFT case W,L,H", [case_width,case_length,case_height]);
echo("Carrier underside / top / max component", [carrier_bottom_z,
     carrier_top_z,carrier_top_z+carrier_component_height]);
echo("Seam / retainer underside / glass front", [seam_z,retainer_bottom_z,glass_front_z]);
echo("USB face setback / pocket floor thickness / channel separation",
     [usb_face_setback,usb_nominal_floor,usb_pocket_channel_gap]);
echo("USB local floor skin at hidden PCB / screw-head clearances",
     [usb_pcb_relief_skin,usb_head_relief_skin]);
echo("USB PCB / mounting hardware clearance from normal wall",
     [pd_pcb_wall_clearance,pd_hardware_wall_clearance]);
echo("UNMEASURED: OEM rear mounting plane, screw engagement, glass pad preload,");
echo("rear components/antenna/cables, all plug overmolds and most connector Z.");

module rounded_rect(w,h,r=2) {
    offset(r=r) square([w-2*r,h-2*r],center=true);
}
module rounded_solid(w,h,z,r=2) {
    linear_extrude(height=z) rounded_rect(w,h,r);
}
module ring(w,h,iw,ih,z,r=2) {
    difference() {
        rounded_solid(w,h,z,r);
        translate([0,0,-eps]) rounded_solid(iw,ih,z+2*eps,max(r-1,0.4));
    }
}
module blind_insert_bore(top_z) {
    translate([0,0,top_z-insert_bore_depth])
        cylinder(d=insert_pilot,h=insert_bore_depth+eps);
}
module retainer_insertion_relief() {
    // The ring and its two anchor pads must pass through the lip and shoulder
    // before reaching their mounting plane. Provide 0.4/0.5 mm edge clearance.
    // Stop below the final anchor bosses; these remain solid hard stops.
    translate([0,0,seam_z-locating_lip_height-eps]) {
        rounded_solid(retainer_outer[0]+0.8,retainer_outer[1]+1,
                      locating_lip_height+1+2*eps,1);
        for(p=retainer_anchor_xy)
            translate([p[0],p[1],0])
                cylinder(d=retainer_anchor_od+1,
                         h=locating_lip_height+1+2*eps);
    }
}
module connector_openings() {
    for (x=carrier_probe_x)
        translate([x-carrier_board_mm[0]/2,-case_length/2,
                   carrier_top_z+probe_axis_above_pcb])
            rotate([90,0,0]) cylinder(d=probe_plug_opening,h=wall*4,center=true);
    for(i=[0:1])
        translate([carrier_power_x[i]-30,case_length/2,
                   carrier_top_z+power_face_center_z[i]+carrier_slide_lift/2])
            rotate([90,0,0])
                linear_extrude(height=wall*4,center=true)
                    rounded_rect(power_face_size[i][0]+2*power_profile_clearance,
                                 power_face_size[i][1]+2*power_profile_clearance+
                                 carrier_slide_lift,power_face_corner_r[i]);
    translate([carrier_power_x[2]-30,case_length/2,
               carrier_top_z+usb_axis_above_pcb]) {
        // The recess receives the cable's plastic body. Only the fitted metal
        // shell opening passes through its floor, level with the socket face.
        translate([0,0,carrier_slide_lift/2]) rotate([90,0,0])
            linear_extrude(height=wall*4,center=true)
                rounded_rect(usb_socket_opening[0],usb_socket_opening[1],0.4);
        translate([0,eps,0]) rotate([90,0,0])
            linear_extrude(height=usb_pocket_depth+eps)
                rounded_rect(usb_pocket_size[0],usb_pocket_size[1],2);
    }
}
module usb_pocket_backing() {
    // Integral backing gives a 1.5 mm nominal floor. Limit it to the pocket's
    // projection so it remains above the separate carrier-edge channel.
    translate([carrier_power_x[2]-30,inside_length/2+eps,
               carrier_top_z+usb_axis_above_pcb]) rotate([90,0,0])
        linear_extrude(height=usb_inward_backing+eps)
            rounded_rect(usb_pocket_size[0],usb_pocket_size[1],2);
}
module carrier_blind_reliefs() {
    // Internal carrier-edge channel: the PCB stops 1.5 mm behind the exterior;
    // 0.2 mm end clearance leaves 1.3 mm continuous exterior plastic.
    translate([-30-blind_pocket_clearance,inside_length/2-eps,
               carrier_bottom_z-power_profile_clearance])
        cube([60+2*blind_pocket_clearance,
              46+carrier_case_offset_y+blind_pocket_clearance-inside_length/2+eps,
              carrier_board_mm[2]+2*power_profile_clearance+carrier_slide_lift]);
    // These clearances are hidden behind the recessed USB floor. Include the
    // 0.3 mm installation lift. The PCB slot leaves 0.943 mm local skin.
    translate([carrier_power_x[2]-30-pd_pcb_size[0]/2-blind_pocket_clearance,
               usb_backing_inner_y-eps,
               carrier_top_z+pd_spacer_height-blind_pocket_clearance])
        cube([pd_pcb_size[0]+2*blind_pocket_clearance,
              pd_pcb_front_local_y+blind_pocket_clearance-usb_backing_inner_y+eps,
              pd_pcb_size[2]+2*blind_pocket_clearance+carrier_slide_lift]);
    // Round upper-head clearances retain more material than rectangular cuts.
    // Nuts lie below the backing and need no cuts. Minimum head-pocket skin is
    // 0.983 mm; these pockets cannot open onto the visible access-pocket floor.
    for(p=pd_mount_xy)
        translate(concat(carrier_local_xy(p),
                         [carrier_top_z+pd_spacer_height+pd_pcb_size[2]-
                          blind_pocket_clearance]))
            cylinder(d=pd_hardware_diameter+2*blind_pocket_clearance,
                     h=pd_hardware_head_height+carrier_slide_lift+
                       2*blind_pocket_clearance);
}
module carrier_support_posts() {
    // Bare-board contact patches stay at the carrier datum, including where a
    // blind wall pocket passes nearby. The carrier slides 0.3 mm above them.
    for(x=[2,56])
        translate([x-30,90.7-46+carrier_case_offset_y,floor_thickness-eps])
            cube([3,1.3,carrier_standoff+eps]);
}

module bottom_shell() {
    difference() {
        union() {
            difference() {
                rounded_solid(case_width,case_length,seam_z,corner_radius);
                translate([0,0,floor_thickness])
                    rounded_solid(inside_width,inside_length,seam_z,
                                  corner_radius-wall);
            }
            for (p=carrier_mount_xy)
                translate(concat(carrier_local_xy(p),[floor_thickness-eps]))
                    cylinder(d=insert_boss_od,h=carrier_standoff+eps);
            for (p=case_closure_xy)
                translate([p[0],p[1],floor_thickness-eps])
                    cylinder(d=insert_boss_od,h=seam_z-floor_thickness+eps);
            usb_pocket_backing();
        }
        for (p=carrier_mount_xy)
            translate(concat(carrier_local_xy(p),[0])) blind_insert_bore(carrier_bottom_z);
        for (p=case_closure_xy)
            translate([p[0],p[1],0]) blind_insert_bore(seam_z);
        connector_openings();
        carrier_blind_reliefs();
    }
    carrier_support_posts();
}

module top_bezel() {
    difference() {
        union() {
            // Top cup: screen pocket is cut separately, leaving a soft-pad ledge.
            difference() {
                translate([0,0,seam_z])
                    rounded_solid(case_width,case_length,case_height-seam_z,corner_radius);
                translate([0,0,seam_z-eps])
                    rounded_solid(inside_width,inside_length,
                                  case_height-front_plate-seam_z+eps,corner_radius-wall);
            }
            // Loose locating lip. No snap catches. Interrupted at closure posts.
            // This shoulder overlaps BOTH the inset lip and cup wall. Without
            // it the 0.3mm fit clearance would leave the lip as a loose ring.
            translate([0,0,seam_z])
                ring(case_width,case_length,
                     lip_width-2*locating_lip_wall,
                     lip_length-2*locating_lip_wall,1,corner_radius);
            difference() {
                translate([0,0,seam_z-locating_lip_height])
                    ring(lip_width,lip_length,
                         lip_width-2*locating_lip_wall,
                         lip_length-2*locating_lip_wall,
                         locating_lip_height+eps,2);
                for(p=case_closure_xy)
                    translate([p[0],p[1],seam_z-locating_lip_height-eps])
                        cylinder(d=insert_boss_od+1,h=locating_lip_height+2*eps);
            }
            // Solid meeting faces transfer case clamp force around the display.
            for(p=case_closure_xy)
                translate([p[0],p[1],seam_z])
                    cylinder(d=insert_boss_od,h=case_height-seam_z);
            // These hard stops fix the retainer plane; tightening cannot close
            // the glass pocket. Pad compression is set by dimensions, not torque.
            for(p=retainer_anchor_xy)
                translate([p[0],p[1],retainer_top_z])
                    cylinder(d=retainer_anchor_od,h=case_height-retainer_top_z);
        }
        translate([0,0,seam_z-eps])
            rounded_solid(wt32_size[0]+2*module_side_clearance,
                          wt32_size[1]+2*module_side_clearance,
                          front_pocket_roof_z-seam_z+eps,1.5);
        translate([0,0,front_pocket_roof_z-eps])
            rounded_solid(window_size[0],window_size[1],
                          case_height-front_pocket_roof_z+2*eps,1);
        // Small front-edge chamfer keeps the lip out of a finger's approach.
        translate([0,0,case_height-0.5])
            linear_extrude(height=0.5+eps,scale=[1.015,1.01])
                rounded_rect(window_size[0],window_size[1],1);
        for(p=case_closure_xy) {
            translate([p[0],p[1],seam_z-eps])
                cylinder(d=m3_clearance,h=case_height-seam_z+2*eps);
            translate([p[0],p[1],case_height-closure_head_recess])
                cylinder(d=m3_head_clearance,h=closure_head_recess+eps);
        }
        for(p=retainer_anchor_xy)
            translate([p[0],p[1],retainer_top_z-eps])
                cylinder(d=retainer_anchor_pilot,h=retainer_anchor_bore_depth+eps);
        retainer_insertion_relief();
    }
}

module retainer() {
    difference() {
        union() {
            ring(retainer_outer[0],retainer_outer[1],
                 retainer_inner[0],retainer_inner[1],retainer_thickness,1);
            for(p=wt32_mount_xy) {
                q=local_xy(p);
                hull() {
                    translate([q[0],q[1],0])
                        cylinder(d=retainer_tab_od,h=retainer_thickness);
                    translate([q[0]<0 ? -32 : 32,q[1],0])
                        cylinder(d=1.6,h=retainer_thickness);
                }
            }
            for(p=retainer_anchor_xy)
                translate([p[0],p[1],0])
                    cylinder(d=retainer_anchor_od,h=retainer_thickness);
        }
        // Scallop the ring around independent enclosure closure columns.
        for(p=case_closure_xy)
            translate([p[0],p[1],-eps])
                cylinder(d=insert_boss_od+1,h=retainer_thickness+2*eps);
        for(p=wt32_mount_xy)
            translate(concat(local_xy(p),[-eps]))
                cylinder(d=small_screw_clearance,h=retainer_thickness+2*eps);
        for(p=retainer_anchor_xy)
            translate([p[0],p[1],-eps])
                cylinder(d=m3_clearance,h=retainer_thickness+2*eps);
    }
}

// A convex primitive swept between two positions models each part separately.
// Taking a hull of the complete populated board would incorrectly fill the air
// between its leads and report spurious collisions with the mounting posts.
module swept_carrier_box(pos,size,offset0,offset1,lift0,lift1) {
    hull() {
        translate([pos[0],pos[1]+offset0,pos[2]+lift0]) cube(size);
        translate([pos[0],pos[1]+offset1,pos[2]+lift1]) cube(size);
    }
}
module swept_carrier_cylinder(pos,d,h,offset0,offset1,lift0,lift1) {
    hull() {
        translate([pos[0],pos[1]+offset0,pos[2]+lift0]) cylinder(d=d,h=h,$fn=24);
        translate([pos[0],pos[1]+offset1,pos[2]+lift1]) cylinder(d=d,h=h,$fn=24);
    }
}
module carrier_sweep(offset0,offset1,lift0,lift1) {
    // Ignore only the intentional zero-clearance seating contact with posts.
    swept_carrier_box([-30,-46,carrier_bottom_z+eps],
        [60,92,carrier_board_mm[2]-eps],offset0,offset1,lift0,lift1);
    swept_carrier_box([-18,-23,carrier_top_z],
        [36,46,carrier_component_height],offset0,offset1,lift0,lift1);
    if(!is_undef(carrier_relay_box))
        swept_carrier_box([carrier_relay_box[0]-30,carrier_relay_box[1]-46,
                          carrier_top_z],
                         [carrier_relay_box[2],carrier_relay_box[3],carrier_relay_box[4]],
                         offset0,offset1,lift0,lift1);
    for(i=[0:2]) {
        depth = i==0 ? rj45_body_depth : i==1 ? barrel_body_depth : 7.5;
        swept_carrier_box([carrier_power_x[i]-30-power_face_size[i][0]/2,
            carrier_power_face_y[i]-46-depth,
            carrier_top_z+power_face_center_z[i]-power_face_size[i][1]/2],
            [power_face_size[i][0],depth,power_face_size[i][1]],
            offset0,offset1,lift0,lift1);
    }
    for(x=carrier_probe_x)
        swept_carrier_box([x-33,carrier_probe_face_y-46,
                          carrier_top_z+probe_axis_above_pcb-3],
                         [6,12,6],offset0,offset1,lift0,lift1);
    swept_carrier_box([carrier_power_x[2]-30-pd_pcb_size[0]/2,
        pd_pcb_front_y-46-pd_pcb_size[1],carrier_top_z+pd_spacer_height],
        pd_pcb_size,offset0,offset1,lift0,lift1);
    for(p=pd_mount_xy) {
        swept_carrier_cylinder([p[0]-30,p[1]-46,
            carrier_bottom_z-pd_hardware_below_pcb],pd_hardware_diameter,
            pd_hardware_below_pcb-eps,offset0,offset1,lift0,lift1);
        swept_carrier_cylinder([p[0]-30,p[1]-46,
            carrier_top_z+pd_spacer_height+pd_pcb_size[2]],pd_hardware_diameter,
            pd_hardware_head_height,offset0,offset1,lift0,lift1);
    }
    // Generated pad diameters include solder fillet allowance. Actual lead tails
    // must be clipped and inspected to stay within the declared 3 mm projection.
    for(p=carrier_underside_pads)
        swept_carrier_cylinder([p[0]-30,p[1]-46,
            carrier_bottom_z-carrier_tail_projection],p[2],
            carrier_tail_projection-eps,offset0,offset1,lift0,lift1);
}

// Visual-only witnesses. Do not export these as purchased-part models.
module carrier_witness() {
    translate([0,carrier_case_offset_y,0]) {
        color([0.10,0.42,0.24]) difference() {
            translate([-30,-46,carrier_bottom_z]) cube(carrier_board_mm);
            for(p=carrier_mount_xy)
                translate(concat(local_xy(p),[carrier_bottom_z-eps]))
                    cylinder(d=3.2,h=carrier_board_mm[2]+2*eps);
        }
        color([0.2,0.22,0.25,0.28])
            translate([-18,-23,carrier_top_z]) cube([36,46,carrier_component_height]);
        if(!is_undef(carrier_relay_box))
            color([0.19,0.20,0.21])
                translate([carrier_relay_box[0]-30,carrier_relay_box[1]-46,carrier_top_z])
                    cube([carrier_relay_box[2],carrier_relay_box[3],carrier_relay_box[4]]);
        for(x=carrier_probe_x)
            color([0.18,0.18,0.19])
                translate([x-30,carrier_probe_face_y-46+3,
                           carrier_top_z+probe_axis_above_pcb])
                    rotate([90,0,0]) cylinder(d=6,h=6,center=true);
        for(i=[0:1]) {
            depth = i==0 ? rj45_body_depth : barrel_body_depth;
            color(i==0 ? [0.32,0.35,0.36] : [0.18,0.18,0.19]) difference() {
                translate([carrier_power_x[i]-30-power_face_size[i][0]/2,
                           carrier_power_face_y[i]-46-depth,carrier_top_z])
                    cube([power_face_size[i][0],depth,power_face_size[i][1]]);
                if(i==1)
                    translate([carrier_power_x[i]-30,carrier_power_face_y[i]-46,
                               carrier_top_z+barrel_axis_above_pcb])
                        rotate([90,0,0]) cylinder(d=6.3,h=3,center=true);
                else
                    translate([carrier_power_x[i]-30,carrier_power_face_y[i]-46,
                               carrier_top_z+power_face_size[i][1]/2])
                        cube([11.8,3,8],center=true);
            }
        }
        color([0.1,0.34,0.45])
            translate([carrier_power_x[2]-30-pd_pcb_size[0]/2,
                       pd_pcb_front_y-46-pd_pcb_size[1],carrier_top_z+pd_spacer_height])
                cube(pd_pcb_size);
        // Visual-only shell and dark mouth make the USB setback clear in the
        // access pocket. Collision checks retain the full conservative box.
        translate([carrier_power_x[2]-30,carrier_power_face_y[2]-46,
                   carrier_top_z+usb_axis_above_pcb]) rotate([90,0,0]) {
            color([0.6,0.62,0.64]) difference() {
                linear_extrude(height=7.5)
                    rounded_rect(usb_face_size[0],usb_face_size[1],1.2);
                translate([0,0,-eps]) linear_extrude(height=2+eps)
                    rounded_rect(7.5,2,0.9);
            }
            color([0.06,0.07,0.08]) translate([0,0,1.9])
                linear_extrude(height=0.05) rounded_rect(7.5,2,0.9);
        }
        color([0.65,0.66,0.67])
            for(p=pd_mount_xy)
                translate([p[0]-30,p[1]-46,carrier_bottom_z-pd_hardware_below_pcb])
                    cylinder(d=pd_hardware_diameter,h=pd_hardware_below_pcb,$fn=24);
    }
}

module wt32_witness() {
    color([0.14,0.16,0.20])
        translate([0,0,glass_front_z-1.45]) rounded_solid(60,92,1.45,1.5);
    color([0.12,0.34,0.46])
        translate([0,0,glass_front_z]) rounded_solid(wt32_active[0],wt32_active[1],0.03,1);
    color([0.20,0.21,0.23])
        translate([0,0,glass_front_z-4.8]) ring(60,92,53,82,3.35,1.5);
    color([0.11,0.13,0.14])
        translate([-24,-35,glass_front_z-wt32_size[2]]) cube([48,70,1.6]);
    for(p=wt32_mount_xy)
        color([0.2,0.21,0.23])
            translate(concat(local_xy(p),[retainer_top_z]))
                difference() {
                    cylinder(d=5.8,h=wt32_rear_mount_depth-4.8);
                    translate([0,0,-eps]) cylinder(d=2.3,h=2.5);
                }
    // Compliant strip is shown as a witness only; fit compression experimentally.
    color([0.82,0.83,0.80])
        translate([0,0,glass_front_z])
            ring(58.8,90.8,55.2,85.2,front_pad_compressed,1.2);
}
module retainer_screw_witness() {
    // M3x6 button heads at outer anchors must remain <=2 mm high.
    for(p=[for(q=wt32_mount_xy) local_xy(q)])
        color([0.66,0.68,0.7])
            translate([p[0],p[1],retainer_bottom_z-small_screw_head_height])
                cylinder(d=small_screw_head_od,h=small_screw_head_height);
    for(p=retainer_anchor_xy)
        color([0.66,0.68,0.7])
            translate([p[0],p[1],retainer_bottom_z-retainer_anchor_head_height])
                cylinder(d=retainer_anchor_head_od,h=retainer_anchor_head_height);
}
module assembly(explode=0) {
    color([0.22,0.25,0.28]) bottom_shell();
    if(show_electronics) carrier_witness();
    translate([0,0,explode]) {
        color([0.77,0.78,0.74]) translate([0,0,retainer_bottom_z]) retainer();
        if(show_fasteners) retainer_screw_witness();
    }
    if(show_electronics) translate([0,0,explode*2]) wt32_witness();
    color([0.95,0.51,0.14]) translate([0,0,explode*3]) top_bezel();
}
module top_print() {
    translate([0,0,case_height]) rotate([180,0,0]) top_bezel();
}
module insertion_collision() {
    // Sweep the preassembled OEM housing and retainer glass-first into the top.
    // The ring stops at its anchor plane; the glass continues into its pocket.
    // This checks modeled solids only, not unmeasured cables or driver access.
    sweep_start = seam_z-locating_lip_height-retainer_thickness-1;
    intersection() {
        top_bezel();
        union() {
            translate([0,0,sweep_start])
                linear_extrude(height=retainer_top_z-sweep_start-0.01)
                    projection(cut=false) retainer();
            translate([0,0,sweep_start])
                rounded_solid(wt32_size[0],wt32_size[1],
                              glass_front_z-sweep_start,1.5);
        }
    }
}

module carrier_installation_collision() {
    assert(!is_undef(carrier_underside_pads) && len(carrier_underside_pads)>0,
           "Regenerate actual underside pad envelopes before checking installation");
    // 1. Lower at +0.5 mm offset, all power noses clear the inner wall.
    // 2. Slide forward 4 mm at 0.3 mm above the posts and ledges.
    // 3. Lower 0.3 mm onto the posts; install the four carrier screws afterward.
    intersection() {
        bottom_shell();
        union() {
            carrier_sweep(carrier_slide_start_y,carrier_slide_start_y,
                          seam_z+5,carrier_slide_lift);
            carrier_sweep(carrier_slide_start_y,carrier_case_offset_y,
                          carrier_slide_lift,carrier_slide_lift);
            carrier_sweep(carrier_case_offset_y,carrier_case_offset_y,
                          carrier_slide_lift,0);
        }
    }
}
module electronics_closure_collision() {
    assert(!is_undef(carrier_relay_box), "Export the placed relay's body envelope");
    assert(glass_front_z-display_rear_depth-carrier_top_z-carrier_relay_box[4]
           >= 2.8-eps, "K1 violates its 2.8 mm reserved local rear clearance");
    echo("K1 minimum reserved rear clearance",
         glass_front_z-display_rear_depth-carrier_top_z-carrier_relay_box[4]);
    intersection() {
        union() {
            top_bezel();
            translate([0,0,retainer_bottom_z]) retainer();
            retainer_screw_witness();
        }
        carrier_sweep(carrier_case_offset_y,carrier_case_offset_y,0,0);
    }
}

if(part=="top") top_print();
else if(part=="bottom") bottom_shell();
else if(part=="retainer") retainer();
else if(part=="print") {
    translate([-case_width-8,0,0]) top_print();
    bottom_shell();
    translate([case_width+8,0,0]) retainer();
}
else if(part=="exploded") rotate([0,0,90]) assembly(15);
else if(part=="section") difference() {
    assembly();
    translate([0,-case_length, -eps]) cube([case_width,case_length*2,case_height+1]);
}
else if(part=="assembled") rotate([0,0,90]) assembly();
else if(part=="insertion-check") insertion_collision();
else if(part=="carrier-installation-check") carrier_installation_collision();
else if(part=="electronics-closure-check") electronics_closure_collision();
else assert(false,"Unknown part view");
