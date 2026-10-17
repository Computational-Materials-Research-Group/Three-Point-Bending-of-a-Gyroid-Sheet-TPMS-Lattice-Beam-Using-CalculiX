# Three-Point Bending of a Gyroid (Sheet-TPMS) Lattice Beam Using CalculiX

<p align="center">
  <img src="https://img.shields.io/badge/CalculiX-2.21-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/TPMS-Gyroid%20Sheet-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/3--Point-Bending-red?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/AlSi10Mg-Aluminium-silver?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Voxel%20Mesh-C3D8I-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Plasticity-NLGEOM-darkgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/ParaView-PVD%20Animation-green?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey?style=for-the-badge"/>
</p>

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.23435335"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.23435335.svg" alt="DOI"/></a>
</p>

<p align="center">
  A <b>fully scripted, open-source lattice-beam model</b>: a beam built
  entirely from a <b>gyroid sheet triply periodic minimal surface (TPMS)</b>
  in <b>AlSi10Mg-like aluminium</b> is loaded in <b>three-point bending</b>
  between two support rollers and a loading roller. The model captures
  the <b>elastic response</b>, <b>yielding of the lattice walls</b>, the
  <b>plastic plateau</b> and the stress distribution through the gyroid
  architecture, reports the <b>load versus deflection</b> curve, and
  exports a <b>70-frame ParaView animation</b> with the rollers visible.
</p>

<img width="1008" height="526" alt="bending_von" src="https://github.com/user-attachments/assets/0c69d92a-25f5-43d7-94c8-5c223a589c7c" />


---

## Concept

Triply periodic minimal surfaces (TPMS) such as the gyroid are the
signature architecture of additively manufactured lattices: smooth,
self-supporting, fully interconnected walls with a very high
stiffness-to-weight ratio. **Sheet-TPMS** lattices are made by
thickening the minimal surface into a wall of finite thickness, which
gives a stretching-dominated response that is stiffer and stronger than
strut lattices at the same density.

In **three-point bending** the top of the beam is compressed, the bottom
is stretched and the material near mid-depth carries shear. In a solid
beam this is a smooth stress field; in a lattice beam the load is
funnelled through the individual walls, so stress concentrates along
wall paths under the loading roller and along the tension face, and the
cell walls yield progressively until the beam reaches a **plastic
plateau**.

This repository is a compact testbed for that problem: one Python
script generates the complete CalculiX model (lattice geometry, mesh,
rollers, material and loading), the solver writes exactly 70 animation
frames, and post-processing scripts extract the load curve and build a
smooth ParaView visualisation of the voxel geometry.

| Aspect | Description |
|---|---|
| Test | Three-point bending, displacement-controlled, 4 mm roller travel |
| Specimen | Gyroid sheet-TPMS beam, 120 x 10 x 30 mm, 12 x 1 x 3 unit cells |
| Material | AlSi10Mg-like aluminium, elastic-plastic (tabulated hardening) |
| Rollers | Two supports + one loader, meshed as tubes for visualisation |
| Kinematics | 3D, large deformation (NLGEOM), quasi-static |
| Geometry generation | Level-set voxelisation, \|f(x,y,z)\| < t |
| Elements | C3D8I (8-node hexahedron with incompatible modes) |
| Solver | CalculiX `ccx` 2.21, implicit static, automatic incrementation |
| Output | `.frd` / `.dat`, converted to `.vtu` / `.pvd`; CSV load curve |

---

## Process Sequence

```
  Stage A  GEOMETRY    gyroid level set evaluated on a voxel grid,
                       sheet |f| < t kept, floating islands removed
  Stage B  MESH        one C3D8I hexahedron per solid voxel;
                       three roller tubes meshed as separate bodies
  Stage C  BENDING     loading line and loading roller displaced 4 mm down,
                       support lines fixed in z (frictionless rollers)
                       automatic increments, max 1/70 of the stroke
  Stage D  OUTPUT      fields at 70 equally spaced time points (*TIME POINTS)
                       (U, S, PEEQ); roller reaction forces at the same points
```

---

## Geometry

```
      z (depth)
      |                        ( O )  loading roller, R = 5 mm
      |                          |    displaced -4 mm
      |  +-------------------------------------------------+  z = 30 mm
      |  |                                                 |
      |  |        gyroid sheet-TPMS lattice beam           |
      |  |        12 x 1 x 3 cells, L = 10 mm              |
      |  |                                                 |
      |  +-------------------------------------------------+  z = 0
      |      ( O )                                 ( O )
      +-------+---------------------------------------+------ x (span)
      0     x = 5 mm                              x = 115 mm      120 mm
            support 1           span S = 110 mm    support 2

  Beam:     120 mm (x) x 10 mm (y, width) x 30 mm (z, depth)
  Overhang: 5 mm beyond each support
  Rollers:  R = 5 mm tubes along y, tangent to the beam faces
```

The gyroid sheet is defined by the level-set function

```
  f(x, y, z) = sin(kx) cos(ky) + sin(ky) cos(kz) + sin(kz) cos(kx),    k = 2 pi / L

  solid where |f| < t        (t = 0.6  ->  relative density 0.333)
```

All side faces of the beam are free, so the gyroid pore pattern is cut
open and visible on every surface.

---

## Physics

### Equilibrium (quasi-static, large deformation)

```
  div(sigma) = 0                      in the lattice
  updated geometry at every increment (NLGEOM)
```

Inertia is neglected: the roller travel is applied as a quasi-static
ramp.

### Lattice plasticity

```
  von Mises yield:        sigma_eq = sigma_y(eps_p)
  isotropic hardening, tabulated in *PLASTIC up to eps_p = 0.30
```

### Roller contact (kinematic)

```
  Support lines:   u_z = 0 on the bottom-face nodes within one voxel of x = 5 and x = 115 mm
  Loading line:    u_z = -4 mm (ramped) on top-face nodes within one voxel of x = 60 mm
  Tangential:      free  -> frictionless rollers (no horizontal reaction)
  Rigid-body:      one support node fixed in x and y, one in y only
```

The roller tubes are separate meshed bodies with no shared nodes: the
supports are fully fixed and the loader moves rigidly with the loading
line, so they show the roller positions in ParaView without
transmitting load themselves.

### Reference solutions

```
  Solid-beam bending stiffness:       K = 48 E I / S^3,       I = b h^3 / 12
  Nominal flexural stress:            sigma = 3 P S / (2 b h^2)
  Solid-beam plastic collapse load:   P_c = 4 M_p / S,        M_p = sigma_y b h^2 / 4
```

The solid-beam values give the upper bound against which the lattice
stiffness and strength are normalised.

### Boundary conditions

| Node set | Region | Constraint |
|---|---|---|
| `SUPPORT` | Bottom-face nodes at both support lines | u_z = 0 |
| `ANCHOR` | One node on support 1 | u_x = u_y = 0 |
| `ANCHOR2` | One node on support 2 | u_y = 0 |
| `LOAD` | Top-face nodes at mid-span | u_z = -4 mm (ramped over the step) |
| `ROLL_SUP` | Support roller tubes | Fully fixed |
| `ROLL_LOAD` | Loading roller tube | u_x = u_y = 0, u_z = -4 mm |

---

## Material Properties

| Property | Lattice (AlSi10Mg-like) | Rollers (steel, visual only) | Unit |
|---|---|---|---|
| Young's modulus E | 70,000 | 210,000 | MPa |
| Poisson's ratio | 0.33 | 0.30 | n/a |
| Initial yield stress | 220 | elastic | MPa |
| Hardening table (stress, plastic strain) | (220, 0), (260, 0.01), (300, 0.04), (330, 0.10), (340, 0.30) | n/a | MPa, n/a |

The hardening curve is a representative fit for as-built AlSi10Mg.
Replace `E`, `NU` and `PLASTIC` with your own test data for
quantitative work.

---

## Model Parameters

### Lattice and specimen

| Parameter | Symbol | Default | Unit |
|---|---|---|---|
| Unit-cell size | `L_CELL` | 10 | mm |
| Cells along span / width / depth | `NCX`, `NCY`, `NCZ` | 12, 1, 3 | n/a |
| Sheet half-thickness (level set) | `T_LEVEL` | 0.6 | n/a |
| Voxels per cell edge | `VOX` | 12 | n/a |
| Overhang beyond each support | `OVERHANG` | 5 | mm |

### Loading

| Parameter | Symbol | Default | Unit |
|---|---|---|---|
| Roller radius | `R_ROLL` | 5 | mm |
| Loading-roller travel | `D_MAX` | 4 | mm |
| Output frames | `N_INC` | 70 | n/a |

### Material

| Parameter | Symbol | Default | Unit |
|---|---|---|---|
| Young's modulus | `E` | 70,000 | MPa |
| Poisson's ratio | `NU` | 0.33 | n/a |
| Hardening table | `PLASTIC` | see above | MPa, n/a |

### Numerical

| Parameter | Location | Default |
|---|---|---|
| Initial / max increment | `*STATIC` | 1/70 of the step |
| Minimum increment | `*STATIC` | 1/70 x 10⁻³ of the step |
| Output time points | `*TIME POINTS` | 70, equally spaced |
| Time-incrementation controls | `*CONTROLS` | 8, 10, 9, 16, 10, 4, , 10 |

All parameters except the numerical controls are set at the top of
`gyroid_bending_ccx.py`.

---

## Derived Design Values (computed from the default inputs)

These follow directly from the parameters above. They are **not**
simulation results.

| Quantity | Value |
|---|---|
| Span S | 110 mm |
| Span-to-depth ratio S/h | 3.67 |
| Second moment of area of the solid section, I | 22,500 mm⁴ |
| Solid-beam bending stiffness 48EI/S³ | ≈ 56.8 kN/mm |
| Solid-beam plastic collapse load (σ_y = 220 MPa) | ≈ 18.0 kN |
| Voxel size | 0.833 mm |
| Roller travel per output frame | 0.057 mm |

---

## Mesh

| Quantity | Value |
|---|---|
| Lattice elements | 20,736 C3D8I |
| Roller elements | 432 C3D8 (3 tubes x 144) |
| Total nodes | 47,947 |
| Element size | 0.833 mm cubes |
| Relative density after island removal | 0.333 |
| Support / load nodes | 52 / 26 |

Treat the console line printed by `gyroid_bending_ccx.py` as
authoritative; it changes with any geometry or mesh parameter.

---

## Results

Values from the default model (CalculiX 2.21, 71 increments).

### Load-deflection response

| Quantity | Value |
|---|---|
| Initial bending stiffness | ≈ 4.1 kN/mm |
| Stiffness relative to the solid beam | ≈ 7 % |
| Onset of yielding | ≈ 0.6 mm, ≈ 2.1 kN |
| Peak (plateau) load | 2630.7 N |
| Peak load relative to the solid-beam collapse load | ≈ 15 % |
| Nominal flexural stress at peak load | ≈ 48 MPa |
| Horizontal reaction at the rollers | ≈ 0 (frictionless) |

The low stiffness ratio reflects both the lattice (relative density
0.33) and the short span: at S/h = 3.7, shear deformation of the
lattice core and local deformation under the loading line add
significantly to the bending deflection.

<!-- Replace with your own plot -->
<img width="600" alt="load-deflection" src="gyroid_bend_load_deflection.png" />

### What to look for

| Field | Expected behaviour |
|---|---|
| `U` | Mid-span moves down 4 mm; beam ends rotate over the supports |
| `S_Mises` | Stress carried along gyroid wall paths fanning out from the loader to the supports; highest under the loader and along the tension face |
| `PEEQ` | Plasticity starts under the loading line, then spreads through the walls near mid-span and along the bottom face |
| `S` (xx) | Compression in the top walls, tension in the bottom walls |
| Load curve | Linear rise, yielding knee at ≈ 2.1 kN, plastic plateau at ≈ 2.6 kN |

### Known limitation: loading-line hotspot

The load is applied as a prescribed displacement on one band of voxel
nodes rather than through roller contact. This produces a local stress
and plastic-strain concentration directly under the loading line that
is a boundary-condition artefact. Use a colour range of about 0 to
350 MPa for `S_Mises` so the hotspot does not hide the stress field in
the rest of the lattice.

---

## Output Files

| File | Description |
|---|---|
| `gyroid_bend.inp` | CalculiX input deck written by `gyroid_bending_ccx.py` |
| `gyroid_bend.frd` | Field results at the 70 time points (+ final increment) |
| `gyroid_bend.dat` | Total reaction forces on the loading line and supports |
| `gyroid_bend.sta`, `.cvg` | Solver status and convergence history |
| `ccx.log` | Solver console output |
| `gyroid_bend_load_deflection.csv` | Load-deflection curve |
| `gyroid_bend_load_deflection.png` | Plot of the load-deflection curve |
| `pvd/gyroid_bend.01.vtu` ... `.71.vtu` | ParaView frames |
| `pvd/gyroid_bend.pvd` | ParaView collection with the correct time values |

### VTU data fields

| Field | Description |
|---|---|
| `U` | Displacement (mm) |
| `S` | Stress tensor, 6 components (MPa) |
| `S_Mises` | Von Mises stress (MPa) |
| `S_Principal` | Principal stresses (MPa) |
| `PEEQ` | Equivalent plastic strain |
| `ERROR` | CalculiX error estimator |

### CSV columns

```
gyroid_bend_load_deflection.csv : deflection_mm, load_N

deflection_mm : loading-roller displacement
load_N        : total vertical reaction on the loading line
```

---

## Repository Structure

```
.
├── gyroid_bending_ccx.py        # Generates the lattice mesh, rollers and CalculiX deck
├── run_ccx_bending.sh           # Runs the full pipeline: mesh, solve, convert, load curve
├── extract_load_deflection.py   # Load-deflection CSV and plot from the .dat file
├── smooth_view.py               # ParaView script: smoothed, stress-coloured beam
├── gyroid_bend_load_deflection.png
└── README.md                    # This file
```

---

## How to Run

### Requirements
* CalculiX `ccx` 2.21 or later: http://www.calculix.de
* Python 3 with numpy and scipy (mesh generation)
* matplotlib (optional, for the load-deflection plot)
* ccx2paraview with vtk (conversion to `.vtu` / `.pvd`)
* ParaView 5.10 or later: https://www.paraview.org

On Ubuntu or WSL:

```bash
sudo apt install calculix-ccx python3-pip
pip install numpy scipy matplotlib
pipx install ccx2paraview
pipx inject ccx2paraview vtk
```

### Step 1: Run the full pipeline

```bash
bash run_ccx_bending.sh
```

Follow solver progress from a second terminal with
`tail -f gyroid_bend.sta`; the step is complete when the step time
reaches 1.0.

### Step 2: Or run the stages separately

```bash
python3 gyroid_bending_ccx.py                  # writes gyroid_bend.inp
ccx gyroid_bend                                # solve
mkdir -p pvd && cd pvd
ln -sf ../gyroid_bend.frd gyroid_bend.frd
ccx2paraview gyroid_bend.frd vtu               # .vtu frames + .pvd
rm -f gyroid_bend.frd && cd ..
python3 extract_load_deflection.py gyroid_bend.dat
```

The job name is given to `ccx` without the `.inp` extension. For
multi-threaded solving set `OMP_NUM_THREADS`,
`CCX_NPROC_EQUATION_SOLVER`, `CCX_NPROC_STIFFNESS` and
`CCX_NPROC_RESULTS` (done in `run_ccx_bending.sh`).

---

## Visualisation in ParaView

### Option A: Raw voxel result

```
Open pvd/gyroid_bend.pvd, click Apply
Filters > Warp By Vector, Vectors = U, Scale Factor = 1, Apply
Colour by S_Mises (range 0 to 350) or PEEQ
Press Play
```

Node coordinates are the undeformed positions; without Warp By Vector
the undeformed shape is shown at every frame.

### Option B: Smoothed beam (recommended for figures)

```
Edit > Reset Session
View > Python Shell > Run Script > smooth_view.py
Press Play
```

The script chains Warp By Vector, Extract Surface, Smooth (150
iterations) and Generate Surface Normals, colours by `S_Mises` and sets
a front view. Adjust `PVD_FILE`, `SMOOTH_ITER` and the colour range at
the top of the script.

### Option C: Exaggerated deflection without roller overlap

```
Threshold on cell ID 1 to 20736 (lattice only)
Warp By Vector (U) on the Threshold output with a large scale factor
Show the original, unwarped dataset for the rollers
```

---

## Key Numerical Insights

### Voxel mesh of a level-set geometry
Evaluating the gyroid function at voxel centres and keeping |f| < t
gives a conforming hexahedral mesh with no CAD step. The price is a
staircase surface, which is smoothed for display only (Option B).

### Island removal
Cutting a periodic TPMS with free faces leaves small disconnected
pieces of sheet at the edges. A connected-component labelling keeps
only the largest body; otherwise the solver sees unconstrained rigid
bodies.

### Incompatible-mode elements
C3D8I removes the shear locking of fully integrated linear hexahedra
in bending, so walls only one or two elements thick still bend
correctly.

### Frictionless rollers
Pinning the loading line in x makes the beam act partly like an arch
and produces a large horizontal reaction. The default model only
removes rigid-body motion, so the horizontal reaction stays at zero, as
for real rollers.

### Exactly 70 animation frames
`*TIME POINTS` writes results at 70 equally spaced loads, independent
of how many increments the solver needs; the solver can still cut back
the increment size where plasticity requires it.

### Visual rollers
The roller tubes share no nodes with the lattice and are fully
prescribed, so they appear in every frame at the correct position
without affecting the solution.

---

## Common Errors and Fixes

| Error / symptom | Cause | Fix |
|---|---|---|
| `ccx: command not found` | CalculiX not installed or not on PATH | `sudo apt install calculix-ccx` |
| `run_ccx_bending.sh: No such file or directory` | Zip extracted into a folder of the same name | `cd` into the inner `gyroid_ccx_70` folder, or `find . -name run_ccx_bending.sh` |
| `$'\r': command not found` | Windows line endings | `sed -i 's/\r$//' run_ccx_bending.sh` |
| `*ERROR reading *STATIC` | Numbers on the card too long | Keep the `:.6g` formatting in the generator |
| `No support/load nodes found` | Roller line falls on a hole in the lattice | Change `OVERHANG` or widen the node band |
| `ccx2paraview`: no module named `vtk` | pipx environment lacks vtk | `pipx inject ccx2paraview vtk` |
| `ccx2paraview` TypeError on complex eigenvalues | numpy returns complex eigenvalues for the stress tensor | Replace `np.linalg.eigvals(tensor)` with `np.linalg.eigvalsh(tensor)` in `ccx2paraview/common.py` |
| ParaView: `Error parsing XML ... not well-formed` | Frames rewritten by an external compression step | Regenerate the frames with `ccx2paraview` and do not post-compress them |
| ParaView shows a flat, undeformed beam | Coordinates are undeformed | Apply Warp By Vector with `U` |
| Loading roller appears to penetrate the beam | Warp scale factor > 1 also exaggerates the roller motion | Use Scale Factor = 1, or Option C |
| Beam looks pixelated | Voxel staircase surface | Option B (smoothing) or increase `VOX` |
| Large red zone under the loader | Loading-line stress concentration | Set `S_Mises` range to 0 to 350 MPa |
| SyntaxError when pasting a script into the Python Shell | Shell cannot take pasted indented blocks | Use **Run Script**, not paste |
| Overlapping duplicate objects in ParaView | Script run several times | Edit > Reset Session, then run once |
| Path not found in ParaView on WSL | Windows path used in a Linux ParaView | Use `/mnt/d/...` instead of `D:\...` |

---

## Extending the Model

| Extension | What to change |
|---|---|
| Other TPMS (Primitive, Diamond, Neovius, I-WP) | Add their level-set functions and select by name; calibrate `t` to a common relative density for a fair comparison |
| Relative-density study | Sweep `T_LEVEL` (or a target density) and fit stiffness and strength versus density (Gibson-Ashby scaling) |
| Finer geometry | Increase `VOX` to 16-20 (more elements, smoother walls, more accurate wall stresses) |
| Smooth geometry | Marching-cubes surface + Gmsh tetrahedral mesh (C3D10) instead of voxels |
| Real roller contact | `*CONTACT PAIR` between roller and lattice surfaces to capture local indentation and crushing |
| Four-point bending | Two loading lines at S/3 for a pure-bending zone |
| Sandwich panel | Add solid face sheets above and below the lattice core |
| Graded lattice | Make `T_LEVEL` or `L_CELL` a function of position |
| Other alloys | Replace `E`, `NU` and `PLASTIC` |
| Parametric study / ML dataset | Loop the generator over TPMS type, density, cell size and span |

---

## Citation

Mishra, A. (2026). *Three-Point Bending of a Gyroid (Sheet-TPMS)
Lattice Beam Using CalculiX* [Computer software]. Zenodo.
https://doi.org/10.5281/zenodo.23435335

```bibtex
@software{mishra2026gyroidbending,
  author       = {Mishra, Akshansh},
  title        = {Three-Point Bending of a Gyroid (Sheet-TPMS) Lattice
                   Beam Using CalculiX},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.23435335},
  url          = {https://doi.org/10.5281/zenodo.23435335}
}
```

---

## License

<p>
<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
<img alt="Creative Commons Licence" style="border-width:0"
  src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png"/>
</a>
<br/>
This work is licensed under a
<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
Creative Commons Attribution NonCommercial 4.0 International License</a>.
</p>

You are free to:
* **Share**: copy and redistribute in any medium or format
* **Adapt**: remix, transform, and build upon the material

Under the following terms:
* **Attribution**: give appropriate credit and link to this repository
* **NonCommercial**: not for commercial use without permission

Copyright 2026 Akshansh Mishra.
