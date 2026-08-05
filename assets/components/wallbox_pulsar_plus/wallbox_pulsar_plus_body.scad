// Dimensionally scaled Wallbox Pulsar Plus North America enclosure.
//
// Coordinate system matches ComponentType's local axes:
//   x = along / vertical, y = across / horizontal, z = out from the wall.
// Units are inches.  Overall body dimensions and profile proportions are
// derived from Wallbox's 2021 North American technical datasheet.  The
// 1.25-inch power aperture and 1-inch fitting recommendation come from the
// North American installation guide.

$fn = 72;

body_height = 7.9;
body_width = 7.8;
body_depth = 3.9;

power_port_from_left = 2.30;
charge_port_from_right = 2.26;
port_from_wall = 1.60;

function signed_power(value, exponent) =
    (value < 0 ? -1 : 1) * pow(abs(value), exponent);

function superellipse_points(
    height,
    width,
    exponent = 3.4,
    center = [0, 0],
    segments = 144
) = [
    for (angle = [0 : 360 / segments : 360 - 360 / segments])
        [
            center[0]
                + height / 2 * signed_power(cos(angle), 2 / exponent),
            center[1]
                + width / 2 * signed_power(sin(angle), 2 / exponent)
        ]
];

module front_profile(height, width, exponent = 3.4, center = [0, 0]) {
    polygon(points = superellipse_points(height, width, exponent, center));
}

// The side outline is normalized to the published 3.9-inch maximum depth.
// Intermediate stations follow the vector side profile in the datasheet.
side_profile = [
    [0.00, 0.00],
    [body_height, 0.00],
    [7.90, 2.89],
    [7.80, 3.39],
    [7.65, 3.65],
    [7.40, 3.80],
    [6.90, 3.88],
    [6.00, 3.90],
    [2.00, 3.90],
    [1.00, 3.88],
    [0.50, 3.80],
    [0.25, 3.65],
    [0.10, 3.25],
    [0.00, 2.89]
];

module side_profile_volume() {
    // Rotate an x/z polygon extrusion so it spans the local y axis.
    translate([0, body_width, 0])
        rotate([90, 0, 0])
            linear_extrude(height = body_width, convexity = 10)
                polygon(points = side_profile);
}

module enclosure_shell() {
    intersection() {
        linear_extrude(height = body_depth, convexity = 10)
            front_profile(
                body_height,
                body_width,
                center = [body_height / 2, body_width / 2]
            );
        side_profile_volume();
    }
}

module halo_groove() {
    // Scale-derived front bezel: about 5.56 x 5.62 inches, with an inner
    // halo/panel envelope of about 5.18 x 5.21 inches.
    translate([0, 0, body_depth - 0.055])
        linear_extrude(height = 0.075, convexity = 10)
            difference() {
                front_profile(5.62, 5.56, 4.0, [3.98, body_width / 2]);
                front_profile(5.21, 5.18, 4.0, [3.98, body_width / 2]);
            }
}

module vertical_gland(center_y, projection, outside_diameter) {
    // A three-stage envelope captures the lower boss/gland shown in the
    // dimensioned profiles while keeping the conduit centerline unobstructed.
    translate([-0.14, center_y, port_from_wall])
        rotate([0, 90, 0])
            cylinder(h = 0.75, d = 1.05);
    translate([-projection + 0.12, center_y, port_from_wall])
        rotate([0, 90, 0])
            cylinder(h = projection - 0.24, d = outside_diameter);
    translate([-projection, center_y, port_from_wall])
        rotate([0, 90, 0])
            cylinder(h = 0.14, d1 = outside_diameter * 0.82, d2 = outside_diameter);
}

union() {
    difference() {
        enclosure_shell();
        halo_groove();
    }

    // Physical left is local across-max when the unit is mounted on the
    // enclosure's front face.
    vertical_gland(body_width - power_port_from_left, 0.59, 1.33);
    vertical_gland(charge_port_from_right, 0.63, 1.34);
}
