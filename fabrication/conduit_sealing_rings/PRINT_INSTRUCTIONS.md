# TPU conduit sealing rings — Bambu X2D

**Current UF-B layout:** print only five rings: three E943E (3/4 inch),
one E943F (1 inch), and one E943G (1-1/4 inch). The two E943D rings for
`power_junction_light_adapter` and `power_junction_outlet_adapter` are obsolete;
those branches now use UF cable connectors and their specified hardware.
The seven-ring STEP, 3MF, ZIP, inventory, and dimensions below describe the
archived conduit layout. Use individual size files for the current five-ring set.

Print seven flat rings: two for Carlon E943D (1/2 inch), three for E943E
(3/4 inch), one for E943F (1 inch), and one for E943G (1-1/4 inch).
These correspond to every modeled `*_sealing_washer` in the EV charger enclosure.

## Files and dimensions

All STEP files use **millimeters** and contain exact circular CAD solids.
Each individual ring is centered on X/Y with its lower flat face at Z = 0.

| Adapter | Trade size | Quantity | Ring OD (mm) | Bore (mm) | Thickness (mm) |
|---|---|---:|---:|---:|---:|
| E943D | 1/2 inch | 2 | 28.956 | 22.0 | 2.032 |
| E943E | 3/4 inch | 3 | 34.290 | 27.4 | 2.032 |
| E943F | 1 inch | 1 | 41.021 | 34.3 | 2.032 |
| E943G | 1-1/4 inch | 1 | 49.784 | 43.1 | 2.032 |

- `full_set_7_rings.step`: seven separate solids laid flat with gaps; footprint
  184.29 × 102.037 mm. Import this once for one complete enclosure set.
- `step_by_size/`: one reusable ring per adapter size. Print the quantities above.
- `step_by_location/`: one file for each of the seven installation locations.
  These duplicate the size files; do not print both collections unless you want spares.
- `ring_inventory.csv`: location-to-adapter mapping and dimensions.
- `design_inputs.json` and `generate_rings.py`: editable parameters and regeneration.
- `dimensions_and_validation.json`: provenance, calculated bore basis, and STEP checks.

The combined layout has no connecting sprues or base sheet. It is a geometry file,
not a configured Bambu Studio project or ready-to-run machine code.

## Prepare TPU and the X2D

Use dry **95A TPU** as the starting material. This guide assumes a **0.4 mm main
hotend**. Softer TPU changes compression and feeding behavior and needs its own trial.

For Bambu TPU 95A HF, Bambu specifies 70 °C for 8 hours in a forced-air dryer.
For other TPU, use its manufacturer's drying limits. Feed from a dry container
with a freely turning spool and a short, low-drag path.
[Bambu TPU 95A HF drying guidance](https://eu.store.bambulab.com/en-dk/products/tpu-95a-hf).

On the X2D, print ordinary 95A TPU through the **main hotend**, manually loaded
through the main extruder inlet. Bypass the filament buffer and automatic AMS feed.
AMS HT may act as a dry container using its manual TPU outlet. Assign all rings to
that main hotend. Follow the printer's loading prompts.
[X2D manual, TPU section, printed pages 114–116](https://csm.bblcdn.com/hub/7c58718aaa2e40edab56efb87419a96a.pdf#page=115).

Use a TPU-compatible build plate and its matching filament preset. Clean the plate;
apply a thin release layer of glue if required by that plate's TPU instructions.
Do not use an aggressive adhesion plate without checking TPU compatibility.

## Import and slice in Bambu Studio

1. Configure **Bambu Lab X2D** with the nozzle actually installed. If X2D is absent,
   update Bambu Studio and its printer profiles; do not substitute a different printer.
2. Select the installed plate and the **Generic TPU** preset for the X2D, or the
   exact Bambu TPU preset matching your spool. Select the main hotend/manual spool.
3. For the first fit trial, import one file from `step_by_size/` with **File → Import**
   or drag it onto Prepare. Use the STEP import dialog's fine tessellation option
   if available; target surface deviation no larger than 0.02 mm.
4. Keep scale at **100%**. Check X/Y equals the table's OD and Z equals 2.032 mm.
   Lay the broad annular face on the plate, with the hole vertical. No supports
   are needed. Do not stand the ring on its edge.
5. Use the starting settings below. Slice, then inspect Preview at the first,
   middle, and last layers. Confirm the bore stays open and every ring is fully filled.
6. Print one ring per size and check the cooled parts on the actual adapters.
   After fit checks pass, import `full_set_7_rings.step`. Preserve its separated
   arrangement or split it into objects and arrange with at least 8 mm edge spacing.
   Move the group toward the front-center within the permitted printable area,
   as advised by the X2D TPU guide. Keep all rings on the bed.
7. Check the object/part list: the full set must contain **seven solids**, with
   quantities 2/3/1/1 by ascending size. If imported as one object, its seven parts
   can remain together. Do not enable supports, a raft, or a prime tower for this
   single-material print.
8. Save the configured job as a **3MF project**. Send the plate with bed leveling
   enabled, correct TPU spool mapping, and the main hotend selected. Watch the first
   layer before leaving the print to run.

## Starting process settings

These are conservative design-specific starting values, not a tested X2D preset.
Keep the exact filament preset's temperature, cooling, retraction and flow ratio
unless calibration indicates a change. Use normal printer speed mode.

| Bambu Studio setting | Starting value |
|---|---|
| Layer height | 0.16 mm |
| Initial layer height | 0.16 mm |
| Wall loops | 4 |
| Sparse infill density | 100% |
| Infill pattern | Rectilinear, if available |
| Top / bottom shell layers | 5 / 5 |
| Initial layer speed | 15 mm/s |
| Outer / inner wall speed | 25 / 30 mm/s |
| Solid infill / top surface speed | 30 / 25 mm/s |
| Max volumetric speed | Cap at 2.0 mm³/s for the first trial |
| Print acceleration | 1,000 mm/s² for the first trial |
| Supports / raft / brim | Off |
| Ironing / fuzzy skin / scarf seam | Off |
| Seam | Aligned; inspect and trim any raised blob |
| XY contour / hole compensation | Start at 0 mm |
| Elephant foot compensation | Start at 0.10 mm; inspect the bore and lower edge |

The 2.032 mm modeled thickness is preserved exactly in CAD. With fixed 0.16 mm
layers, slicing will quantize the final height to approximately 2.08 mm (13 layers);
check Preview and measure the actual print. Do not scale the entire ring to change
thickness, since that also changes the bore. Use a finer layer height or regenerate
with a chosen thickness if an exact printed stack height is required.

## Fit and installation checks

Allow the plate to cool, flex it, and gently peel off each ring. Remove strings
and any seam nub without gouging either sealing face. Label storage bags by adapter;
there is no embossed text on the sealing surfaces.

The ring should pass over the threaded end and sit flat against the adapter's
shoulder without folding, tearing, or excessive stretching. Check that the ring
covers the actual box hole continuously and that the shoulder supports it around
its circumference. This matters because the enclosure's fitting and washer outer
diameters were planning envelopes, not measured sealing lands.

Place the ring outside the box between the adapter shoulder and the box wall,
with the locknut inside. Confirm adequate remaining thread engagement. Follow the
hardware manufacturer's tightening instructions; do not rely on crushing TPU to
correct a poor fit. Check again for creep or extrusion after the assembly settles.

Printed TPU rings have **not been validated for weather sealing, compression set,
UV exposure, or an enclosure ingress rating**. They are custom prototype parts,
not replicas of Carlon's neoprene E943DW/EW/FW/GW washers. For a rated weatherproof
connection, use the manufacturer's specified sealing hardware.

If a bore needs correction, measure the actual thread near the shoulder and edit
`bore_override_mm` for that size in `design_inputs.json`, then regenerate. A change
of +0.2 mm in bore diameter adds 0.1 mm radial clearance. Use a test print to separate
CAD fit issues from printer hole undersizing; avoid scaling the whole model.

## Dimension basis and regeneration

Source: EV charger enclosure commit
`f2d7c6e36930bea93ac92b3a3b081d65ab502b61`, `build.py` and
`lumber_model/components.py`, extracted 2026-10-17. Seven actual washer instances
were enumerated. Ring OD and the 0.080-inch thickness come from those models.
The original solid washer envelopes have no bores.

Carlon drawing **WSD-AC03022, revision D** identifies E943D/E/F/G as 1/2, 3/4, 1 and
1-1/4 NPT adapters. A and B are socket diameters, D is the internal passage, and
OD is the body diameter; none is a directly specified thread major diameter.
[Manufacturer drawing, linked by ABB](https://www-public.tnb.com/shared/msds/WSD-AC03022.pdf),
[accessible mirror of the same drawing](https://rexel-cdn.com/products/wsd-ac03022.pdf?i=039871DF-8982-4842-B6A7-3AEC5741A497).

The bore sizing is an engineering derivation, not a published Carlon washer
specification. For a conservative basic thread envelope at the shoulder:

```text
basic major diameter in inches = E0 + S/16 + 0.8/TPI
bore in mm = round UP to 0.1 mm (basic major diameter × 25.4 + 0.4 mm)
```

E0 is the NPT pitch diameter at the small end; S is the adapter's full threaded-end
projection. Extending the basic taper to S includes the region where threads may
vanish into the shoulder. Use S = 0.545 / 0.553 / 0.812 / 0.816 inches respectively;
for E943F, the catalog's 0.812-inch S is slightly longer than the sales drawing's
0.802-inch value and was used conservatively. This calculation does not establish
manufacturing tolerances or the shape of any molded shoulder fillet.

Sources: [ABB Carlon catalog, printed page G9](https://tnb.ca.abb.com/en/pdf-catalogues/fittings-and-conduit-systems/carlon-conduit-and-fitting/G-Carlon-Conduit-and-Fittings-en.pdf#page=9),
[WALWORTH NPT table, printed page 53](https://walworth.com/en/wp-content/uploads/2017/11/BRONZE_VALVES_2016_1.pdf#page=53),
[NPT geometry and basic thread height](https://tectul.com/en/conduccion-de-fluidos/accesorios-de-tuberia/ficha-tecnica-niple-acero-carbon-sch40-1).

Regenerate with Python 3.12+ and `build123d==0.10.0`:

```bash
python generate_rings.py
```

The generator is self-contained with `design_inputs.json`; it does not need the
original enclosure repository. Its checks validate each ring and reimport every
STEP file to confirm solid count and analytic volume. It checks open centers,
outer diameter, thickness, non-overlapping batch geometry and plate bounds.
Physical fit, slicing and leak performance require the print trials above.
