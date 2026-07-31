# Lightweight ASA Tambour Track and Wooden Curtain

## Summary

Design a modular ASA track and lightweight wooden tambour using 1/2-inch-thick,
3/4-inch-high pressure-treated slats. The slats settle against one another when
closed; mechanical webbing links them, limits separation, and pulls them during
closing but does not hold them apart under gravity.

Retain the existing 1 1/2-inch swept clearance envelope and 2 5/8-inch bend
radius. Prototype 3/8-inch slats as an optional later weight reduction, but use
1/2 inch as the production baseline unless the thinner version passes the same
wind, screw-holding, and durability tests.

## CAD and model changes

- Add build123d as a pinned dependency and generate exact STEP and STL
  fabrication files beneath `output/tambour/`.
- Generate mirrored track sets with straight sections no longer than 300 mm,
  exact tangent bends, side-opening U-channels, integral mounting flanges,
  expansion slots, drainage, removable loading sections and stops, and paired
  external keyed collars that align both channel walls while permitting
  individual segment removal.
- Size printable features for a 0.6 mm nozzle, including nominal 2.4 mm minimum
  walls and reinforced channel/flange transitions.
- Give every track end exterior dovetail pads and retain each paired collar
  with a recessed M3 stainless screw and heat-set insert. Preserve a nominal
  0.6 mm end gap and keep all joint features outside the running channel.
- Provide 0.3, 0.5, and 0.7 mm-per-surface running-clearance coupons. Generate
  production tracks using the tightest clearance that passes the conditioned
  coupon and bend tests.
- Model the actual 1/2-inch slat depth, 3/4-inch travel height, initial
  1/32-inch straight-run gap, 25/32-inch attachment pitch, 44-inch curtain,
  retained 3/8-inch guide-datum offset, and an independent 1 1/2-inch swept
  assembly envelope.
- Generate a replaceable, centered, approximately 300 mm-wide ASA lift ledge
  on each of two pull slats. Limit projection to 5/8 inch and keep every handle
  entirely on one slat and inside the swept envelope.

## Curtain fabrication

- Obtain pressure-treated stock that can be safely surfaced to 1/2 inch using
  a planer, purchased surfaced stock, or outsourced milling. Do not resaw a
  wide board on edge using only the table saw.
- Dry and acclimate stock before final surfacing. Reject warped, checked,
  twisted, or severely incised pieces and record moisture condition.
- Rip the surfaced stock into 3/4-inch-high slats using a repeatable table-saw
  jig. Crosscut from one stop, ease moving edges, and field-treat and seal every
  cut or surfaced face.
- Lay slats face-down against 1/32-inch setup spacers and attach at least three
  exterior-rated polyester webbing strips without stretching them. Fasten the
  webbing mechanically to every slat, outside the track and handle regions.
- Let the lower stop carry the closed curtain vertically. Slat contact carries
  compression; the webbing is not a tensioned spacing belt in this state.

## Structural and wind validation

- Use the existing 44.1 psf ultimate wind-pressure screen. Check each
  20 1/2-by-3/4-inch slat for approximately 4.7 pounds of distributed load and
  the complete door and supports for approximately 260 pounds distributed over
  the door area.
- Test conditioned full-span 1/2- and 3/8-inch coupons with at least 5 pounds
  distributed across one slat. Inspect bending, permanent set, splitting,
  track-edge crushing, and fastener movement.
- Retain 1/2 inch as the production thickness. Adopt 3/8 inch only after it
  passes all structural and operating tests with acceptable margin.
- Treat calculations as screening and prototype requirements rather than a
  stamped structural rating.

## Prototype sequence

1. Print clearance, keyed-collar joint, screw-slot, and handle coupons.
2. Mill short 1/2- and 3/8-inch samples and test finish, swelling, screw holding,
   and edge treatments.
3. Build one complete bend with short straight sections.
4. Assemble a short curtain at 25/32-inch pitch with 1/32-inch setup gaps and
   the actual webbing.
5. Verify settling, bend articulation, edge clearance, and visual closure.
6. Adjust only edge treatment, setup gap, and accepted channel clearance from
   these tests; retain 3/4-inch slat height and 1/2-inch production thickness.
7. Build a rigid full-width test frame using installation gauges.
8. Assemble and test the complete curtain and both pull slats.

## Acceptance criteria

- Complete at least 100 full cycles without binding, derailment, webbing
  separation, joint catching, handle damage, or significant track wear.
- Require no more than 5 pounds peak operating force for centered and
  deliberately off-center pulls.
- Apply a 15-pound handle load for one minute without cracking, screw
  withdrawal, splitting, or permanent deformation.
- Confirm gravity-assisted closure without manually stacking individual slats,
  visually minimal gaps, and no binding after moisture conditioning.
- Pass the distributed slat and complete-door wind tests.
- Keep all actual components inside the 1 1/2-inch swept envelope.
- Permit track-segment, loading-section, stop, handle, and curtain replacement
  without removing siding or permanent electrical equipment.
- Require the keyed joint coupon to cross without catching, withstand a
  10-pound transverse load, and survive 25 removal/reinstallation cycles.
- Repeat operating and clearance tests after final track installation, siding,
  trim, electrical routing, and ceiling installation.

## Assumptions

- The tambour is a visual barrier, not an airtight weather seal or security
  door.
- Shorter 3/4-inch-high slats improve articulation; additional slats restore
  the required curtain length.
- Gravity may reduce straight-run gaps because webbing can bow locally, but
  operation cannot depend on uncontrolled slack.
- Captured slat ends and tracks carry transverse wind load; webbing primarily
  maintains continuity and alignment.
- ASA is a replaceable direct-running guide material without an initial UHMW
  liner.
- Drilling, countersinking, sanding, planing, and jig-making tools may supplement
  the table saw. No router is required.
