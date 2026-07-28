# Top-plane bracing evaluation

## Decision

Use one stress-rated nominal 1x4 diagonal extended across the back-left and
front-right post tops in 3/4-inch-deep routed seats. The member is 33.977
inches overall in the default model, retains the 25.328-inch clear span, and
occupies `z = 46.25` to `47.00`.

Connect each end with one Simpson Strong-Tie HTP37Z plate aligned to the
diagonal and twenty SD9212 #9-by-2 1/2-inch Strong-Drive SD Connector screws.
The two side perimeter members are top-flush 4x4s occupying `z = 43.50` to
`47.00`; they replace the former upper and tambour side rails.

The brace is still required because none of the other modeled construction is
a defined structural diaphragm.  The four perimeter rails have unspecified
end connections, and the gapped composite roof and wall boards are neither
structurally rated sheathing nor installed with a structural fastening
schedule.  Eliminating the diagonals would therefore leave top-frame racking
resistance to unquantified joint stiffness and cladding friction.

One wood diagonal is sufficient in principle: it changes between tension and
compression when the shear direction reverses.  The former second diagonal
did not create a useful independent load path because its crossing joint and
both members' end connections were undefined.

## Site and screening load

The Boulder County GIS wind and snow layers return the following values at the
project parcel:

- ultimate design wind speed: 155 mph;
- ground snow load: 40 psf.

For a conservative screening calculation, use Exposure B at the 15-foot
minimum velocity-pressure height, `Kd = 0.85`, `Kzt = 1.0`, and an elevation
factor of 0.82.  This gives:

```text
qh = 0.00256 Kz Kzt Kd Ke V^2
   = 0.00256(0.57)(1.0)(0.85)(0.82)(155^2)
   = 24.5 psf ultimate
```

Using a deliberately high net force coefficient of 1.8 gives 44.1 psf.  On
the larger 27.5-inch by 48-inch projected face, the resulting top-level shear
screen is 404 pounds ultimate, or 242 pounds ASD after the 0.6 wind factor.
Doubling that ASD result for model and load-path uncertainty gives a 485-pound
design shear.  The default clear opening is 20.5 by 14.875 inches and its
diagonal is 25.32 inches at 35.96 degrees, producing a maximum screened axial
brace demand of:

```text
P = 485 / sin(35.96 degrees) = 826 pounds ASD
```

The 40 psf snow load governs the gravity support check of the composite roof
and perimeter members, not the in-plane axial force in this diagonal.  The
brace also does not improve whole-enclosure overturning or the lateral
capacity of the gravel footings.

### 1x4 member screen

The American Wood Council permits a stress-rated nominal 1-inch board to use
the corresponding dimension-lumber design values. For Douglas fir-larch No. 2,
use `Fc = 1,400 psi`, `Ft = 500 psi`, and `Emin = 580,000 psi`. Conservatively
apply wet-service factors of 0.80 to compression and 0.90 to `Emin`, the 1.60
wind-duration factor, no size increase, a pinned 25.328-inch effective length,
and the NDS sawn-lumber column constant of 0.8.

```text
area       = 0.75(3.5) = 2.625 square inches
Le / d     = 25.328 / 0.75 = 33.77
Fc*        = 1,400(0.80)(1.60) = 1,792 psi
FcE        = 0.822(580,000)(0.90) / 33.77^2 = 376 psi
Cp         = 0.200
Pcompression = Fc* Cp area = 941 pounds ASD
Ptension     = 500(1.60)(2.625) = 2,100 pounds ASD
```

The screened 1x4 therefore passes member compression by 14 percent and member
tension by a larger margin after the wind demand has already been doubled for
uncertainty. Because the compression margin is not large, substituting a lower
species/grade, an incised member, a longer unsupported brace, or a connection
that reduces the net section requires a new calculation.

## Member and connection requirements

Use a stress-rated, exterior-suitable nominal 1x4 with actual dimensions of
3/4 by 3 1/2 inches.  Specify Douglas fir-larch No. 2 or a species/grade with
equal or greater published compression, tension, and minimum-modulus values.
Reject a board with slope-of-grain defects, checks, splits, or wane in either
end-connection region.

The accepted detail and its installation must provide all of the following for
both load directions:

- at least 826 pounds ASD axial capacity in the member and at each end;
- compression stability about the 3/4-inch weak axis over the modeled length;
- tension capacity at the minimum net section;
- full seating of both plates and all forty SD9212 screws in solid wood;
- positive transfer from the diagonal through the perimeter-frame/post joints;
- corrosion compatibility with treated lumber and the outdoor environment.

The model includes the routed cuts, plates, screw envelopes, and roof shims.
Do not enlarge connector holes or substitute ordinary deck screws, SDS screws,
nails, or an incomplete fastener schedule. Inspect the routed residual sections,
plate seating, screw installation, and complete post load path before removing
temporary bracing.

## Superseded thin-metal option

A tension-only metal solution requires an X.  A pair of coil straps would
recover almost the full 1.5 inches, but the current frame does not provide the
manufacturer-required side-grain anchorage length at all four endpoints.
Nailing a horizontal strap into the tops of the vertical posts would use end
grain, while wrapping, field-bending, or adding custom corner blocks would no
longer be the simple catalog installation being evaluated.

Metal straps are not part of the accepted design. The HTP37Z/SD9212 assemblies
are the modeled connection.

## Roof interface

The modeled HTP37Z plate and SD9212 head projection is 0.18 inch above the
47-inch frame plane. Continuous 1/4-inch ripped PT-lumber shims raise the
composite roof support plane to `z = 47.25` and the finished roof to
`z = 48.25`. Preserve drainage around both plates and increase roof-fastener
length by the shim thickness so the original substrate penetration is retained.

## Sources

- [Boulder County wind and snow load map](https://www.arcgis.com/home/item.html?id=2adc1d7dbdd244e698e265a950a0fde3)
- [Current Boulder County building-code amendments](https://bouldercounty.gov/property-and-land/land-use/building/building-code-amendments/)
- [American Wood Council guidance for stress-rated nominal boards](https://awc.org/faq/where-can-i-find-information-for-nominal-1-1-1-4-and-1-1-2-stress-rated-boards/)
- [American Wood Council 2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/)
- [Simpson Strong-Tie coil-strap installation requirements](https://www.strongtie.com/resources/product-installers-guide/cs-csmst14-installation)
