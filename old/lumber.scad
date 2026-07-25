/*
  Parametric lumber assembly
  Units: inches

  Supports and rails are represented as data records.
  Rendering is separate from geometry definition.

  Actual lumber dimensions:
    2x4 = 1.5 x 3.5
    4x4 = 3.5 x 3.5

  Lumber record format:
    [
      name,      // string, e.g. "left_post"
      type,      // "2x4", "4x4"
      axis,      // "x", "y", or "z"
      start,     // [x, y, z] minimum corner
      length,    // length along axis
      rotated    // bool; rotates cross-section 90 degrees
    ]

  Default orientation:
    X-running 2x4 -> [length, 3.5, 1.5]
    Y-running 2x4 -> [3.5, length, 1.5]
    Z-running 2x4 -> [3.5, 1.5, length]

  Set rotated = false to use the alternate orientation:
    X-running 2x4 -> [length, 1.5, 3.5]
    Y-running 2x4 -> [1.5, length, 3.5]
    Z-running 2x4 -> [1.5, 3.5, length]

  BOM output:
    Call bom_lumber(piece) or bom_lumber_list(pieces).
    Output appears in the OpenSCAD console as ECHO lines.
*/

$fn = 48;


// ------------------------------------------------------------
// Vector helpers
// ------------------------------------------------------------

function v_add(a, b) =
    [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

function v_mid(a, b) =
    [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];

function v_replace(v, i, value) =
    [
        i == 0 ? value : v[0],
        i == 1 ? value : v[1],
        i == 2 ? value : v[2]
    ];


// ------------------------------------------------------------
// Axis helpers
// ------------------------------------------------------------

function axis_index(axis) =
    axis == "x" ? 0 :
    axis == "y" ? 1 :
    axis == "z" ? 2 :
    undef;

function axis_name(i) =
    i == 0 ? "x" :
    i == 1 ? "y" :
    i == 2 ? "z" :
    undef;

function axis_replace(v, axis, value) =
    v_replace(v, axis_index(axis), value);

function axis_coord(v, axis) =
    v[axis_index(axis)];

function other_axis(axis_a, axis_b) =
    let(
        ai = axis_index(axis_a),
        bi = axis_index(axis_b)
    )
    ai != 0 && bi != 0 ? "x" :
    ai != 1 && bi != 1 ? "y" :
    "z";


// ------------------------------------------------------------
// Lumber data model
// ------------------------------------------------------------

function lumber(
    name,
    type,
    axis,
    start,
    length,
    rotated = true
) =
    [
        name,
        type,
        axis,
        start,
        length,
        rotated
    ];

function l_name(l) =
    l[0];

function l_type(l) =
    l[1];

function l_axis(l) =
    l[2];

function l_start(l) =
    l[3];

function l_len(l) =
    l[4];

function l_rotated(l) =
    len(l) > 5 ? l[5] : true;


// ------------------------------------------------------------
// Lumber dimensions
// ------------------------------------------------------------

function l_dims(type) =
    type == "2x4" ? [1.5, 3.5] :
    type == "4x4" ? [3.5, 3.5] :
    [1, 1];

function l_size(l) =
    l_axis(l) == "x" ?
        [
            l_len(l),
            l_rotated(l) ? l_dims(l_type(l))[1] : l_dims(l_type(l))[0],
            l_rotated(l) ? l_dims(l_type(l))[0] : l_dims(l_type(l))[1]
        ] :

    l_axis(l) == "y" ?
        [
            l_rotated(l) ? l_dims(l_type(l))[1] : l_dims(l_type(l))[0],
            l_len(l),
            l_rotated(l) ? l_dims(l_type(l))[0] : l_dims(l_type(l))[1]
        ] :

    l_axis(l) == "z" ?
        [
            l_rotated(l) ? l_dims(l_type(l))[1] : l_dims(l_type(l))[0],
            l_rotated(l) ? l_dims(l_type(l))[0] : l_dims(l_type(l))[1],
            l_len(l)
        ] :

    [1, 1, 1];


// ------------------------------------------------------------
// Bounding box helpers
// ------------------------------------------------------------

function l_min(l) =
    l_start(l);

function l_max(l) =
    v_add(l_start(l), l_size(l));

function l_center(l) =
    v_mid(l_min(l), l_max(l));

function min_on_axis(l, axis) =
    l_min(l)[axis_index(axis)];

function max_on_axis(l, axis) =
    l_max(l)[axis_index(axis)];

function center_on_axis(l, axis) =
    l_center(l)[axis_index(axis)];

function size_on_axis(l, axis) =
    l_size(l)[axis_index(axis)];


// ------------------------------------------------------------
// Derived lumber: generalized rail/member between two references
// ------------------------------------------------------------

/*
  Creates a member between the inside faces of two support/reference pieces.

  Parameters:
    name:
      Name of the generated member for BOM output.

    type:
      Lumber type, e.g. "2x4".

    support_a, support_b:
      Lumber records used as references.

    span_axis:
      Axis along which the new member runs: "x", "y", or "z".

    position_axis:
      Axis on which the single position parameter is applied.

    position:
      Center coordinate of the new member on position_axis.

    cross_offset:
      Offset from the aligned support center on the remaining cross-section axis.
      The remaining axis is automatically determined from:
        span_axis + position_axis.

    inset:
      Offset inward from the reference faces.
      Positive inset shortens the member.

    rotated:
      Cross-section orientation.
      Defaults to true:
        wide dimension on cross_axis,
        narrow dimension on position_axis.

  Example:
    lumber_between(
      "front_rail",
      "2x4",
      left_post,
      right_post,
      span_axis = "x",
      position_axis = "z",
      position = 32,
      cross_offset = 0
    );
*/
function lumber_between(
    name,
    type,
    support_a,
    support_b,
    span_axis,
    position_axis,
    position,
    cross_offset = 0,
    inset = 0,
    rotated = true
) =
    let(
        d = l_dims(type),

        cross_axis = other_axis(span_axis, position_axis),

        cross_dim = rotated ? d[1] : d[0],
        pos_dim   = rotated ? d[0] : d[1],

        a_min = min_on_axis(support_a, span_axis),
        a_max = max_on_axis(support_a, span_axis),
        b_min = min_on_axis(support_b, span_axis),
        b_max = max_on_axis(support_b, span_axis),

        a_before_b = a_min < b_min,

        start_face = a_before_b ? a_max : b_max,
        end_face   = a_before_b ? b_min : a_min,

        start_span = start_face + inset,
        end_span   = end_face - inset,

        member_len = end_span - start_span,

        cross_min = max(
            min_on_axis(support_a, cross_axis),
            min_on_axis(support_b, cross_axis)
        ),
        cross_max = min(
            max_on_axis(support_a, cross_axis),
            max_on_axis(support_b, cross_axis)
        ),
        cross_center = (cross_min + cross_max) / 2,

        start0 = [0, 0, 0],
        start1 = axis_replace(start0, span_axis, start_span),
        start2 = axis_replace(start1, cross_axis, cross_center + cross_offset - cross_dim / 2),
        start3 = axis_replace(start2, position_axis, position - pos_dim / 2)
    )
    lumber(
        name,
        type,
        span_axis,
        start3,
        member_len,
        rotated
    );


// ------------------------------------------------------------
// Derived lumber: generalized auto-position helper
// ------------------------------------------------------------

/*
  Creates a member between two references and automatically centers it
  on position_axis within the overlapping range of both supports.

  This replaces the older lumber_between_x_auto_z style.
*/
function lumber_between_auto_position(
    name,
    type,
    support_a,
    support_b,
    span_axis,
    position_axis,
    cross_offset = 0,
    inset = 0,
    rotated = true
) =
    let(
        p1 = max(
            min_on_axis(support_a, position_axis),
            min_on_axis(support_b, position_axis)
        ),

        p2 = min(
            max_on_axis(support_a, position_axis),
            max_on_axis(support_b, position_axis)
        ),

        p_center = (p1 + p2) / 2
    )
    lumber_between(
        name,
        type,
        support_a,
        support_b,
        span_axis = span_axis,
        position_axis = position_axis,
        position = p_center,
        cross_offset = cross_offset,
        inset = inset,
        rotated = rotated
    );


// ------------------------------------------------------------
// Rendering
// ------------------------------------------------------------

module render_lumber(l) {
    translate(l_start(l))
        cube(l_size(l));
}

module render_lumber_list(pieces) {
    for (piece = pieces)
        render_lumber(piece);
}


// ------------------------------------------------------------
// BOM output
// ------------------------------------------------------------

module bom_lumber(l) {
    echo(
        str(
            "BOM | name: ", l_name(l),
            " | type: ", l_type(l),
            " | length: ", l_len(l), " in",
            " | axis: ", l_axis(l)
        )
    );
}

module bom_lumber_list(pieces) {
    echo("BOM | ---- lumber members ----");

    for (piece = pieces)
        bom_lumber(piece);

    echo("BOM | ------------------------");
}


// ------------------------------------------------------------
// Optional combined render + BOM output
// ------------------------------------------------------------

module render_lumber_with_bom(l) {
    bom_lumber(l);
    render_lumber(l);
}

module render_lumber_list_with_bom(pieces) {
    bom_lumber_list(pieces);
    render_lumber_list(pieces);
}


// ------------------------------------------------------------
// Example assembly
// ------------------------------------------------------------

// Two fixed supports.
left_post = lumber(
    "left_post",
    "4x4",
    "z",
    [-30, -1.75, 0],
    48
);

right_post = lumber(
    "right_post",
    "4x4",
    "z",
    [30, -1.75, 0],
    60
);

// A 2x4 automatically spanning between the inside faces.
//
// span_axis = "x":
//   The rail runs left-to-right.
//
// position_axis = "z":
//   position = 32 means the rail is centered at Z = 32.
//
// cross_offset = 0:
//   The rail is centered on the support overlap along Y.
//
// rotated defaults to true:
//   X-running 2x4 size is [length, 3.5, 1.5].
front_rail = lumber_between(
    "front_rail",
    "2x4",
    left_post,
    right_post,
    span_axis = "x",
    position_axis = "z",
    position = 32,
    cross_offset = 0
);


// Same idea, but auto-positioned on the overlapping Z range
// of the two posts.
rear_rail_auto_z = lumber_between_auto_position(
    "rear_rail_auto_z",
    "2x4",
    left_post,
    right_post,
    span_axis = "x",
    position_axis = "z",
    cross_offset = 6
);


// Example of a Y-axis span using the same generalized function.
near_post = lumber(
    "near_post",
    "4x4",
    "z",
    [-1.75, -30, 0],
    48
);

far_post = lumber(
    "far_post",
    "4x4",
    "z",
    [-1.75, 30, 0],
    48
);

side_rail = lumber_between(
    "side_rail",
    "2x4",
    near_post,
    far_post,
    span_axis = "y",
    position_axis = "z",
    position = 20,
    cross_offset = 0
);


// Collect pieces into a single assembly list.
assembly = [
    left_post,
    right_post,
    front_rail,
    rear_rail_auto_z,

    near_post,
    far_post,
    side_rail
];


// ------------------------------------------------------------
// Render scene and output BOM
// ------------------------------------------------------------

render_lumber_list_with_bom(assembly);
