# IPEX Scepter STB40S (077454)

Reference CAD model of the 1-1/4 inch PVC Type TB access fitting, based on
the supplied `ipex_077454.pdf` (IPEX drawing 077454_CPD, March 1, 2023).

Generate the STEP assembly with the existing project environment:

```sh
.venv/bin/python tools/generate_ipex_stb40s.py
```

Output: `output/ipex_stb40s/ipex_stb40s_077454.step`. Units are millimeters.
Four solids represent the hollow body, removable cover and two screws.
X is width, Z is the long axis, and Y runs from the cover toward the rear hub.
The origin is the intersection of the three conduit axes. The cover faces -Y.

## Drawing dimensions

| Feature | Inches | Millimeters |
| --- | ---: | ---: |
| Overall axial length | 7.91 | 200.914 |
| Body width | 2.30 | 58.420 |
| Overall depth, screw heads to rear socket mouth | 3.92 | 99.568 |
| Three socket inside diameters | 1.68 | 42.672 |
| End socket insertion depth | 1.11 | 28.194 |
| End conduit axis to rear body surface | 1.00 | 25.400 |
| Rear body surface to rear socket mouth | 1.00 | 25.400 |

The drawing's vertical chain is 1.11 + 2.85 + 2.85 + 1.11 = 7.92 inches,
whereas its overall dimension is 7.91 inches. The model follows 7.91 overall
and 1.11 insertion depths, placing the two shoulders at Z = +/-2.845 inches.

## Estimated geometry

The drawing is a reference drawing marked NTS, with incomplete manufacturing
dimensions. Undimensioned features were estimated from its orthographic views:
2.02 inch hub outside diameters, 7.41 inch capsule body and cover length,
0.14 inch cover thickness, 0.18 inch rear wall, 0.18 inch nominal side walls,
1.54 inch passage diameters, internal access recesses, screw bosses and screws.
The rear socket insertion depth is estimated as 1.00 inch. The model includes
socket shoulders and communicating passages into the access chamber.

Mold draft, small blend radii, socket taper, gasket detail, screw threads,
embossed markings and labels are omitted. This model supports enclosure layout
and clearance planning; it is not a fully specified manufacturing model or a
manufacturer supplied CAD file. Confirm mating and internal clearances against
the physical fitting when those details matter.
