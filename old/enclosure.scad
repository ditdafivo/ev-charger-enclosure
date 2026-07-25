/*
EV charger enclosure + street-light/address-base baseline
=========================================================

OpenSCAD units: inches.  Treat one OpenSCAD unit as one inch.

This model is a parameterized reconstruction of the uploaded Tinkercad OBJ.
The OBJ itself appears to have been exported in centimeters: 13.97 cm in the
OBJ maps to a 5.5" composite-decking board, and 119.38 cm maps to 47" overall
height.

Coordinate convention used here:
  X = left/right, centered on the enclosure
  Y = depth, negative Y is the street/front side
  Z = height above grade

Notes:
  - Body/enclosure depth is about 20".  The address/light projection extends
    forward, so the full visual depth including that element is larger.
  - Most composite-board intersections are intentionally allowed to overlap a
    little, as the Tinkercad model did.  This keeps the baseline easy to edit.
  - The internal lumber, conduit, fasteners, and actual equipment dimensions
    should be refined before using this as a build document.
*/

// -----------------------------------------------------------------------------
// MASTER DISPLAY SWITCHES
// -----------------------------------------------------------------------------
show_posts                  = true;
show_composite_shell        = false;
show_top_cap                = false;
show_equipment_placeholders = false;
show_ev_connector_handle    = false;
show_unifi_ap_placeholder   = false;
show_outlet_placeholder     = false;
show_conduit_placeholders   = false;
show_optional_lumber_rails  = false;
show_address_light_block    = false;
show_address_numbers        = false;
show_reference_envelope     = false;
show_footprint_pad          = true;
show_part_labels            = false;
show_imported_obj_reference = false;   // requires tinker.obj beside this .scad
show_cutlist_echos          = false;    // emits a rough BOM/cut list to console

// -----------------------------------------------------------------------------
// PRIMARY DIMENSIONS
// -----------------------------------------------------------------------------
overall_width  = 24.0;     // intended finished enclosure width
body_depth     = 20.0;     // intended enclosure depth, excluding front projection
overall_height = 47.0;     // intended finished height

// 4x4 nominal wood posts: actual roughly 3.5" x 3.5".
post_size          = 3.5;
post_height        = 46.0;
post_shell_setback = 1.0;  // distance from exterior shell face to outside of posts

// Composite decking.  The OBJ board width corresponds to 5.5".
deck_board_face_width = 5.5;   // visible face width of deck board
 deck_board_thickness = 1.0;   // board thickness / shell thickness
board_gap             = 0.125; // vertical reveal between courses
vertical_board_rows   = 8;

// Bottom ripped strip/kick strip visible in the Tinkercad model.
bottom_clearance   = 1.0;
bottom_strip_height = 1.0;
first_board_z      = bottom_clearance + bottom_strip_height + board_gap;

// Top cap boards lie flat over the enclosure.
top_cap_count         = 3;
top_cap_thickness     = deck_board_thickness;
top_cap_board_width   = deck_board_face_width;
top_cap_side_margin   = 1.0;
top_cap_front_setback = 1.1;
top_cap_rear_setback  = 1.0;
top_cap_length        = overall_width - 2 * top_cap_side_margin;
top_cap_gap           = top_cap_count > 1 ?
                        (body_depth - top_cap_front_setback - top_cap_rear_setback - top_cap_count * top_cap_board_width) / (top_cap_count - 1) : 0;

// Rear service opening approximation from the OBJ.
rear_wing_width  = deck_board_face_width;
rear_return_depth = 4.5;
side_board_length = body_depth - 2 * deck_board_thickness;

// Equipment placeholder sizes and positions, based on the OBJ scale.
equipment_backer_width     = 7.0;
equipment_backer_height    = 24.0;
equipment_backer_thickness = 0.25;
equipment_backer_center_z  = 26.0;
equipment_backer_y         = -6.0;

charger_body_width  = 6.6;
charger_body_depth  = 3.3;
charger_body_height = 6.6;
charger_body_center_z = 27.3;

holster_width  = 3.3;
holster_depth  = 1.34;
holster_height = 5.4;
holster_center_z = 16.9;

// UniFi / AP rough placeholder; set dimensions/position to actual hardware later.
ap_width  = 2.8;
ap_depth  = 1.1;
ap_height = 6.0;
ap_center = [-4.6, equipment_backer_y - 0.05, 35.4];

// 120V outlet rough placeholder; set position to the chosen circuit location.
outlet_width  = 3.0;
outlet_depth  = 1.0;
outlet_height = 4.75;
outlet_center = [4.8, equipment_backer_y - 0.05, 13.0];

// Conduit placeholders, when enabled.
conduit_od = 0.75;
conduit_center_x = 5.9;
conduit_y = equipment_backer_y - 0.2;

// Address / downward-facing light block at the front top.
front_projection_depth = 4.0;
address_block_width  = 11.75;
address_block_depth  = 4.0;
address_block_height = 4.0;
address_block_center_z = 42.35;
address_number_text = "4754";
address_text_height = 4.0;
address_text_depth  = 0.25;
address_text_center_z = 36.0;

// Optional imported Tinkercad OBJ reference.  Keep disabled unless the OBJ file
// is available next to this OpenSCAD file.
obj_reference_file = "tinker.obj";
cm_to_inch = 1 / 2.54;
obj_center_cm_x = 66.080;
obj_center_cm_y = 5.4191;

// -----------------------------------------------------------------------------
// COLORS
// -----------------------------------------------------------------------------
composite_color   = [0.17, 0.18, 0.19, 1.0];
wood_post_color   = [0.50, 0.31, 0.16, 1.0];
white_color       = [0.98, 0.98, 0.98, 1.0];
light_gray_color  = [0.74, 0.78, 0.80, 1.0];
mid_gray_color    = [0.38, 0.40, 0.42, 1.0];
dark_gray_color   = [0.12, 0.13, 0.14, 1.0];
conduit_color     = [0.62, 0.62, 0.60, 1.0];
lens_color        = [1.0, 0.93, 0.60, 0.55];
envelope_color    = [0.1, 0.4, 1.0, 0.08];
label_color       = [1.0, 0.85, 0.15, 1.0];

// -----------------------------------------------------------------------------
// BASIC HELPERS
// -----------------------------------------------------------------------------
module part_box(size=[1,1,1], center=[0,0,0], c=[0.8,0.8,0.8,1]) {
    color(c)
        translate([center[0] - size[0]/2, center[1] - size[1]/2, center[2] - size[2]/2])
            cube(size, center=false);
}

module rounded_box_xz(size=[1,1,1], r=0.125, center=[0,0,0], c=[0.8,0.8,0.8,1]) {
    // Rounded in the visible X-Z face; extruded through Y depth.
    color(c)
        translate([center[0], center[1] + size[1]/2, center[2]])
            rotate([90, 0, 0])
                linear_extrude(height=size[1], convexity=6)
                    offset(r=r)
                        square([max(0.01, size[0] - 2*r), max(0.01, size[2] - 2*r)], center=true);
}

module cyl_x(len=1, d=1, center=[0,0,0], c=[0.8,0.8,0.8,1], facets=48) {
    color(c)
        translate([center[0] - len/2, center[1], center[2]])
            rotate([0, 90, 0])
                cylinder(h=len, d=d, $fn=facets);
}

module cyl_y(len=1, d=1, center=[0,0,0], c=[0.8,0.8,0.8,1], facets=48) {
    color(c)
        translate([center[0], center[1] - len/2, center[2]])
            rotate([-90, 0, 0])
                cylinder(h=len, d=d, $fn=facets);
}

module cyl_z(len=1, d=1, center=[0,0,0], c=[0.8,0.8,0.8,1], facets=48) {
    color(c)
        translate([center[0], center[1], center[2] - len/2])
            cylinder(h=len, d=d, $fn=facets);
}

module front_text(txt="TEXT", txt_size=1, depth=0.1, center=[0,0,0], c=[1,1,1,1]) {
    color(c)
        translate([center[0], center[1], center[2]])
            rotate([90, 0, 0])
                linear_extrude(height=depth, convexity=10)
                    text(txt, size=txt_size, halign="center", valign="center", font="Liberation Sans:style=Bold");
}

module optional_label(txt="", center=[0,0,0], size=0.35) {
    if (show_part_labels)
        front_text(txt=txt, txt_size=size, depth=0.035, center=center, c=label_color);
}

// -----------------------------------------------------------------------------
// STRUCTURAL MODULES
// -----------------------------------------------------------------------------
module four_posts() {
    post_x = overall_width/2 - post_shell_setback - post_size/2;
    post_y = body_depth/2 - post_shell_setback - post_size/2;
    for (sx=[-1,1])
        for (sy=[-1,1]) {
            part_box(size=[post_size, post_size, post_height],
                     center=[sx*post_x, sy*post_y, post_height/2],
                     c=wood_post_color);
        }
}

module bottom_shell_strips() {
    zc = bottom_clearance + bottom_strip_height/2;
    // Full-width front ripped strip.
    part_box(size=[overall_width, deck_board_thickness, bottom_strip_height],
             center=[0, -body_depth/2 + deck_board_thickness/2, zc],
             c=composite_color);

    // Left/right side ripped strips.
    for (sx=[-1,1])
        part_box(size=[deck_board_thickness, side_board_length, bottom_strip_height],
                 center=[sx*(overall_width/2 - deck_board_thickness/2), 0, zc],
                 c=composite_color);

    // Rear wing ripped strips.
    for (sx=[-1,1])
        part_box(size=[rear_wing_width, deck_board_thickness, bottom_strip_height],
                 center=[sx*(overall_width/2 - rear_wing_width/2), body_depth/2 - deck_board_thickness/2, zc],
                 c=composite_color);

    // Rear return ripped strips near service opening.
    for (sx=[-1,1])
        part_box(size=[deck_board_thickness, rear_return_depth, bottom_strip_height],
                 center=[sx*(overall_width/2 - rear_wing_width + deck_board_thickness/2),
                         body_depth/2 - deck_board_thickness - rear_return_depth/2,
                         zc],
                 c=composite_color);
}

module deck_course(row=0) {
    zc = first_board_z + row * (deck_board_face_width + board_gap) + deck_board_face_width/2;

    // Full-width street/front face.
    part_box(size=[overall_width, deck_board_thickness, deck_board_face_width],
             center=[0, -body_depth/2 + deck_board_thickness/2, zc],
             c=composite_color);

    // Continuous left and right side faces.
    for (sx=[-1,1])
        part_box(size=[deck_board_thickness, side_board_length, deck_board_face_width],
                 center=[sx*(overall_width/2 - deck_board_thickness/2), 0, zc],
                 c=composite_color);

    // Rear left and right wings, leaving a service opening.
    for (sx=[-1,1])
        part_box(size=[rear_wing_width, deck_board_thickness, deck_board_face_width],
                 center=[sx*(overall_width/2 - rear_wing_width/2), body_depth/2 - deck_board_thickness/2, zc],
                 c=composite_color);

    // Rear return pieces along the service-opening jambs.
    for (sx=[-1,1])
        part_box(size=[deck_board_thickness, rear_return_depth, deck_board_face_width],
                 center=[sx*(overall_width/2 - rear_wing_width + deck_board_thickness/2),
                         body_depth/2 - deck_board_thickness - rear_return_depth/2,
                         zc],
                 c=composite_color);
}

module composite_shell() {
    bottom_shell_strips();
    for (row=[0:vertical_board_rows-1])
        deck_course(row=row);
}

module top_cap_boards() {
    zc = overall_height - top_cap_thickness/2;
    for (i=[0:top_cap_count-1]) {
        yc = -body_depth/2 + top_cap_front_setback + top_cap_board_width/2 + i * (top_cap_board_width + top_cap_gap);
        part_box(size=[top_cap_length, top_cap_board_width, top_cap_thickness],
                 center=[0, yc, zc],
                 c=composite_color);
    }
}

module optional_lumber_rails() {
    // Placeholder only: these are not in the Tinkercad model.  Use these as a
    // starting point for internal 2x lumber and revise for real load paths.
    rail_height = 1.5;
    rail_depth  = 3.5;
    rail_length = overall_width - 2*(post_shell_setback + post_size);
    for (z=[12, 26, 40]) {
        part_box(size=[rail_length, rail_depth, rail_height],
                 center=[0, -body_depth/2 + deck_board_thickness + rail_depth/2, z],
                 c=[0.55,0.38,0.22,1]);
        part_box(size=[rail_length, rail_depth, rail_height],
                 center=[0, body_depth/2 - deck_board_thickness - rail_depth/2, z],
                 c=[0.55,0.38,0.22,1]);
    }
}

// -----------------------------------------------------------------------------
// EQUIPMENT PLACEHOLDERS
// -----------------------------------------------------------------------------
module ev_charger_and_holster() {
    // White mounting/backing plate from the Tinkercad model.
    part_box(size=[equipment_backer_width, equipment_backer_thickness, equipment_backer_height],
             center=[0, equipment_backer_y, equipment_backer_center_z],
             c=white_color);
    optional_label("mount board", [0, equipment_backer_y - equipment_backer_thickness/2 - 0.04, equipment_backer_center_z + 10.8], 0.35);

    // Charger body, rough wallbox placeholder.
    rounded_box_xz(size=[charger_body_width, charger_body_depth, charger_body_height],
                   r=0.35,
                   center=[0, equipment_backer_y + equipment_backer_thickness/2 + charger_body_depth/2,
                           charger_body_center_z],
                   c=mid_gray_color);
    optional_label("EVSE", [0, equipment_backer_y - 0.2, charger_body_center_z], 0.55);

    // Holster / cable-rest placeholder.
    rounded_box_xz(size=[holster_width, holster_depth, holster_height],
                   r=0.20,
                   center=[0, equipment_backer_y + equipment_backer_thickness/2 + holster_depth/2,
                           holster_center_z],
                   c=light_gray_color);
    optional_label("holster", [0, equipment_backer_y - 0.2, holster_center_z], 0.35);
}

module ev_connector_handle_placeholder() {
    // Approximation of the complex gray Tinkercad connector/handle object.
    base_y = equipment_backer_y + equipment_backer_thickness/2 + charger_body_depth + 0.25;

    // Blocky socket/head.
    rounded_box_xz(size=[4.0, 1.4, 4.6],
                   r=0.18,
                   center=[-1.2, base_y, 34.2],
                   c=mid_gray_color);

    // Short barrel extending away from the mounting plate.
    cyl_y(len=3.6, d=2.4, center=[1.3, base_y + 1.3, 35.0], c=mid_gray_color, facets=48);

    // Angled grip / handle.
    color(mid_gray_color)
        translate([2.3, base_y + 2.9, 31.3])
            rotate([25, 0, 0])
                cylinder(h=5.2, d=1.55, $fn=48);

    // Small upper block, matching the rough geometry in the OBJ.
    rounded_box_xz(size=[2.4, 1.2, 3.1],
                   r=0.10,
                   center=[-0.1, base_y, 37.8],
                   c=mid_gray_color);
}

module unifi_ap_placeholder() {
    // Slim vertical AP placeholder.  Move/resize after measuring the actual AP
    // and desired bracket orientation.
    rounded_box_xz(size=[ap_width, ap_depth, ap_height],
                   r=0.40,
                   center=ap_center,
                   c=white_color);
    optional_label("AP", [ap_center[0], ap_center[1] - ap_depth/2 - 0.04, ap_center[2]], 0.45);
}

module weatherproof_outlet_placeholder() {
    // Weatherproof box + simplified duplex face.
    rounded_box_xz(size=[outlet_width, outlet_depth, outlet_height],
                   r=0.18,
                   center=outlet_center,
                   c=light_gray_color);

    face_y = outlet_center[1] - outlet_depth/2 - 0.04;
    rounded_box_xz(size=[1.35, 0.10, 3.0],
                   r=0.08,
                   center=[outlet_center[0], face_y, outlet_center[2]],
                   c=white_color);

    // Slot marks on the face.
    for (zz=[outlet_center[2]-0.75, outlet_center[2]+0.75]) {
        part_box(size=[0.10, 0.06, 0.36], center=[outlet_center[0]-0.22, face_y-0.07, zz], c=dark_gray_color);
        part_box(size=[0.10, 0.06, 0.36], center=[outlet_center[0]+0.22, face_y-0.07, zz], c=dark_gray_color);
        cyl_y(len=0.07, d=0.16, center=[outlet_center[0], face_y-0.08, zz-0.42], c=dark_gray_color, facets=24);
    }
    optional_label("120V", [outlet_center[0], face_y-0.12, outlet_center[2]+2.7], 0.35);
}

module conduit_placeholders() {
    // Simple draft conduit route.  Replace with actual conduit type, sweep
    // radius, box entries, straps, burial/emergence details, and clearances.
    cyl_z(len=28, d=conduit_od, center=[conduit_center_x, conduit_y, 14], c=conduit_color, facets=32);
    cyl_x(len=2.2, d=conduit_od, center=[conduit_center_x - 1.1, conduit_y, outlet_center[2]], c=conduit_color, facets=32);
    cyl_x(len=2.8, d=conduit_od, center=[conduit_center_x - 1.4, conduit_y, charger_body_center_z], c=conduit_color, facets=32);
}

// -----------------------------------------------------------------------------
// ADDRESS / LIGHT / FRONT PROJECTION
// -----------------------------------------------------------------------------
module address_and_light_block() {
    // Dark rectangular front projection from the OBJ.  Interpreted here as the
    // address/light housing.
    block_center_y = -body_depth/2 - address_block_depth/2;
    part_box(size=[address_block_width, address_block_depth, address_block_height],
             center=[0, block_center_y, address_block_center_z],
             c=dark_gray_color);

    // Downward-facing diffuser/lens underneath the projection.
    part_box(size=[address_block_width - 1.5, address_block_depth - 0.9, 0.35],
             center=[0, block_center_y, address_block_center_z - address_block_height/2 - 0.20],
             c=lens_color);

    optional_label("light", [0, block_center_y - address_block_depth/2 - 0.08, address_block_center_z], 0.45);
}

module address_numbers() {
    // Raised address numbers on the front face.  Change address_number_text above.
    front_y = -body_depth/2 - 0.05;
    front_text(txt=address_number_text,
               txt_size=address_text_height,
               depth=address_text_depth,
               center=[0, front_y, address_text_center_z],
               c=light_gray_color);
}

// -----------------------------------------------------------------------------
// REFERENCES / UTILITIES
// -----------------------------------------------------------------------------
module reference_envelope() {
    part_box(size=[overall_width, body_depth, overall_height],
             center=[0, 0, overall_height/2],
             c=envelope_color);
}

module footprint_pad() {
    pad_margin = 2.0;
    part_box(size=[overall_width + 2*pad_margin, body_depth + front_projection_depth + 2*pad_margin, 0.08],
             center=[0, -front_projection_depth/2, -0.04],
             c=[0.55,0.55,0.55,0.22]);
}

module imported_tinkercad_obj_reference() {
    // The original OBJ imports in centimeters.  This scales to inches and
    // recenters it to this model's origin.  Keep disabled unless needed.
    color([1.0, 0.0, 0.0, 0.22])
        scale([cm_to_inch, cm_to_inch, cm_to_inch])
            translate([-obj_center_cm_x, -obj_center_cm_y, 0])
                import(obj_reference_file, convexity=10);
}

module cutlist_summary() {
    if (show_cutlist_echos) {
        echo("ROUGH CUT LIST / BOM - all dimensions in inches");
        echo("4x4 actual wood posts", "qty", 4, "size", post_size, "x", post_size, "x", post_height);
        echo("Composite decking, full front courses", "qty", vertical_board_rows, "cut length", overall_width, "face width", deck_board_face_width);
        echo("Composite decking, front bottom ripped strip", "qty", 1, "cut length", overall_width, "ripped height", bottom_strip_height);
        echo("Composite decking, side courses", "qty", 2 * vertical_board_rows, "cut length", side_board_length, "face width", deck_board_face_width);
        echo("Composite decking, side bottom ripped strips", "qty", 2, "cut length", side_board_length, "ripped height", bottom_strip_height);
        echo("Composite decking, rear wing courses", "qty", 2 * vertical_board_rows, "cut length", rear_wing_width, "face width", deck_board_face_width);
        echo("Composite decking, rear wing bottom ripped strips", "qty", 2, "cut length", rear_wing_width, "ripped height", bottom_strip_height);
        echo("Composite decking, rear return courses", "qty", 2 * vertical_board_rows, "cut length", rear_return_depth, "face width", deck_board_face_width);
        echo("Composite decking, rear return bottom ripped strips", "qty", 2, "cut length", rear_return_depth, "ripped height", bottom_strip_height);
        echo("Composite decking, top cap boards", "qty", top_cap_count, "cut length", top_cap_length, "board width", top_cap_board_width, "computed gap", top_cap_gap);
        echo("Equipment placeholders", "EV backer", equipment_backer_width, "x", equipment_backer_height, "charger body", charger_body_width, "x", charger_body_height, "outlet box", outlet_width, "x", outlet_height);
        echo("Overall shell", "width", overall_width, "body depth", body_depth, "height", overall_height, "front projection adds", front_projection_depth);
    }
}

// -----------------------------------------------------------------------------
// MAIN ASSEMBLY
// -----------------------------------------------------------------------------
module ev_charger_enclosure() {
    if (show_footprint_pad) footprint_pad();
    if (show_reference_envelope) reference_envelope();
    if (show_imported_obj_reference) imported_tinkercad_obj_reference();

    if (show_posts) four_posts();
    if (show_composite_shell) composite_shell();
    if (show_top_cap) top_cap_boards();
    if (show_optional_lumber_rails) optional_lumber_rails();

    if (show_equipment_placeholders) ev_charger_and_holster();
    if (show_ev_connector_handle) ev_connector_handle_placeholder();
    if (show_unifi_ap_placeholder) unifi_ap_placeholder();
    if (show_outlet_placeholder) weatherproof_outlet_placeholder();
    if (show_conduit_placeholders) conduit_placeholders();

    if (show_address_light_block) address_and_light_block();
    if (show_address_numbers) address_numbers();

    cutlist_summary();
}

ev_charger_enclosure();
