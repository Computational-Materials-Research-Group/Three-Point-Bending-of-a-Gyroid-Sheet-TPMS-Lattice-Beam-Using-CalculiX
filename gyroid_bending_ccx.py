#!/usr/bin/env python3
"""
Gyroid (sheet-TPMS) beam in 3-point bending  ->  CalculiX input deck
=====================================================================
Units: mm, N, MPa, s

  * Voxel hexahedral mesh (C3D8I, good in bending) of a sheet gyroid |f| < t
  * Disconnected islands removed (only the main beam is kept)
  * Two support rollers + one loading roller meshed as tubes so they show
    up in ParaView. They move rigidly with the prescribed boundary
    conditions (support lines fixed in z, loading line pushed down).
  * Elasto-plastic AlSi10Mg-like material, NLGEOM, fixed increments
    -> one result frame per increment -> animated .pvd in ParaView

Usage:
    python3 gyroid_bending_ccx.py            # writes gyroid_bend.inp
    ccx gyroid_bend                          # solve (-> gyroid_bend.frd/.dat)
    ccx2paraview gyroid_bend.frd vtu         # -> gyroid_bend.pvd + .vtu frames
"""
import numpy as np
from scipy import ndimage

# ---------------------------------------------------------------- parameters
JOB        = "gyroid_bend"
L_CELL     = 10.0      # gyroid unit-cell size (mm)
NCX, NCY, NCZ = 12, 1, 3   # cells along span (x), width (y), depth (z)
T_LEVEL    = 0.6       # sheet half-thickness in level-set units (rho ~ 0.38)
VOX        = 12        # voxels per cell edge (mesh resolution; 16 = finer)

OVERHANG   = 5.0       # beam length beyond each support (mm)
R_ROLL     = 5.0       # roller radius (mm)
D_MAX      = 4.0       # loading-roller travel (mm)
N_INC      = 70        # output frames (exactly, via *TIME POINTS)

E, NU      = 70000.0, 0.33                        # MPa
PLASTIC    = [(220.0, 0.0), (260.0, 0.01),        # true stress (MPa), plastic strain
              (300.0, 0.04), (330.0, 0.10), (340.0, 0.30)]

# ---------------------------------------------------------------- geometry
LX, LY, LZ = NCX * L_CELL, NCY * L_CELL, NCZ * L_CELL
NX, NY, NZ = NCX * VOX, NCY * VOX, NCZ * VOX
h = L_CELL / VOX
k = 2.0 * np.pi / L_CELL

xc = (np.arange(NX) + 0.5) * h
yc = (np.arange(NY) + 0.5) * h
zc = (np.arange(NZ) + 0.5) * h
X, Y, Z = np.meshgrid(xc * k, yc * k, zc * k, indexing="ij")
f = np.sin(X) * np.cos(Y) + np.sin(Y) * np.cos(Z) + np.sin(Z) * np.cos(X)
solid = np.abs(f) < T_LEVEL

# keep only the largest face-connected component (drop floating islands)
lab, nlab = ndimage.label(solid)
if nlab > 1:
    sizes = ndimage.sum(solid, lab, range(1, nlab + 1))
    solid = lab == (1 + int(np.argmax(sizes)))
rho = solid.mean()

# ---------------------------------------------------------------- beam mesh
def gid(i, j, kk):
    return (i * (NY + 1) + j) * (NZ + 1) + kk

ii, jj, kk = np.nonzero(solid)
conn = np.stack([gid(ii, jj, kk),         gid(ii + 1, jj, kk),
                 gid(ii + 1, jj + 1, kk), gid(ii, jj + 1, kk),
                 gid(ii, jj, kk + 1),     gid(ii + 1, jj, kk + 1),
                 gid(ii + 1, jj + 1, kk + 1), gid(ii, jj + 1, kk + 1)], axis=1)

used = np.unique(conn)
new_id = -np.ones((NX + 1) * (NY + 1) * (NZ + 1), dtype=np.int64)
new_id[used] = np.arange(1, used.size + 1)
gi = used // ((NY + 1) * (NZ + 1))
gj = (used // (NZ + 1)) % (NY + 1)
gk = used % (NZ + 1)
beam_xyz = np.stack([gi * h, gj * h, gk * h], axis=1)
beam_conn = new_id[conn]
n_beam_nodes = used.size

# ---------------------------------------------------------------- roller meshes (tubes, axis = y)
x_s1, x_s2, x_mid = OVERHANG, LX - OVERHANG, LX / 2.0
nodes = [beam_xyz]
elems = [beam_conn]
next_node = n_beam_nodes + 1
roller_sets = {}

def tube(xc0, zc0, r_out, r_in, ylo, yhi, nth=36, ny=4):
    """hex tube along y; returns (xyz, conn) with local 0-based node ids"""
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    ys = np.linspace(ylo, yhi, ny + 1)
    rs = [r_in, r_out]
    xyz, idx = [], {}
    for a, yy in enumerate(ys):
        for b, rr in enumerate(rs):
            for c, tt in enumerate(th):
                idx[(a, b, c)] = len(xyz)
                xyz.append((xc0 + rr * np.cos(tt), yy, zc0 + rr * np.sin(tt)))
    cn = []
    for a in range(ny):
        for c in range(nth):
            c1 = (c + 1) % nth
            q = [idx[(a, 0, c)], idx[(a, 0, c1)], idx[(a, 1, c1)], idx[(a, 1, c)],
                 idx[(a + 1, 0, c)], idx[(a + 1, 0, c1)], idx[(a + 1, 1, c1)], idx[(a + 1, 1, c)]]
            cn.append(q)
    return np.array(xyz), np.array(cn)

for name, x0, z0 in [("SUP1", x_s1, -R_ROLL), ("SUP2", x_s2, -R_ROLL), ("LOADER", x_mid, LZ + R_ROLL)]:
    xyz, cn = tube(x0, z0, R_ROLL, 0.6 * R_ROLL, -1.0, LY + 1.0)
    ids = np.arange(next_node, next_node + len(xyz))
    nodes.append(xyz)
    elems.append(cn + next_node)
    roller_sets[name] = ids
    next_node += len(xyz)

all_xyz = np.vstack(nodes)
all_conn = np.vstack(elems)

# make every hex right-handed (positive Jacobian)
def fix_orientation(conn, xyz):
    p = xyz[conn - 1]
    e1, e2, e3 = p[:, 1] - p[:, 0], p[:, 3] - p[:, 0], p[:, 4] - p[:, 0]
    neg = np.einsum("ij,ij->i", np.cross(e1, e2), e3) < 0
    conn[neg] = conn[neg][:, [0, 3, 2, 1, 4, 7, 6, 5]]
    return conn

all_conn = fix_orientation(all_conn, all_xyz)
n_beam_el = beam_conn.shape[0]

# ---------------------------------------------------------------- boundary node sets
bx, bz = beam_xyz[:, 0], beam_xyz[:, 2]
beam_ids = np.arange(1, n_beam_nodes + 1)
tol = 1.01 * h
sup_nodes  = beam_ids[(bz < 1e-9) & ((np.abs(bx - x_s1) <= tol) | (np.abs(bx - x_s2) <= tol))]
load_nodes = beam_ids[(np.abs(bz - LZ) < 1e-9) & (np.abs(bx - x_mid) <= tol)]
if len(sup_nodes) == 0 or len(load_nodes) == 0:
    raise SystemExit("No support/load nodes found - adjust OVERHANG or mesh")
# rigid-body motion only: one node on support 1 fixed in x and y, one node on
# support 2 fixed in y -> supports and loader act as frictionless rollers
s1 = sup_nodes[np.abs(bx[sup_nodes - 1] - x_s1) <= tol]
s2 = sup_nodes[np.abs(bx[sup_nodes - 1] - x_s2) <= tol]
anchor  = s1[np.argmin(np.abs(bx[s1 - 1] - x_s1))]
anchor2 = s2[np.argmin(np.abs(bx[s2 - 1] - x_s2))]

# ---------------------------------------------------------------- write .inp
def write_set(fh, kw, name, ids):
    fh.write(f"*{kw}SET, {kw}SET={name}\n")
    ids = list(ids)
    for a in range(0, len(ids), 12):
        fh.write(", ".join(str(int(v)) for v in ids[a:a + 12]) + "\n")

with open(JOB + ".inp", "w") as fh:
    fh.write("** Gyroid sheet-TPMS beam, 3-point bending (units mm, N, MPa)\n")
    fh.write(f"** cell {L_CELL} mm, cells {NCX}x{NCY}x{NCZ}, t={T_LEVEL}, "
             f"rel. density {rho:.3f}, voxel {h:.4f} mm\n")
    fh.write("*NODE, NSET=NALL\n")
    for n, (x, y, z) in enumerate(all_xyz, start=1):
        fh.write(f"{n}, {x:.6f}, {y:.6f}, {z:.6f}\n")

    fh.write("*ELEMENT, TYPE=C3D8I, ELSET=BEAM\n")
    for e in range(n_beam_el):
        fh.write(f"{e + 1}, " + ", ".join(map(str, all_conn[e])) + "\n")
    fh.write("*ELEMENT, TYPE=C3D8, ELSET=ROLLERS\n")
    for e in range(n_beam_el, all_conn.shape[0]):
        fh.write(f"{e + 1}, " + ", ".join(map(str, all_conn[e])) + "\n")

    write_set(fh, "N", "SUPPORT", sup_nodes)
    write_set(fh, "N", "LOAD", load_nodes)
    write_set(fh, "N", "ANCHOR", [anchor])
    write_set(fh, "N", "ANCHOR2", [anchor2])
    write_set(fh, "N", "ROLL_SUP", np.concatenate([roller_sets["SUP1"], roller_sets["SUP2"]]))
    write_set(fh, "N", "ROLL_LOAD", roller_sets["LOADER"])

    fh.write("*MATERIAL, NAME=ALSI10MG\n*ELASTIC\n")
    fh.write(f"{E}, {NU}\n*PLASTIC\n")
    for s, ep in PLASTIC:
        fh.write(f"{s}, {ep}\n")
    fh.write("*SOLID SECTION, ELSET=BEAM, MATERIAL=ALSI10MG\n\n")
    fh.write("*MATERIAL, NAME=ROLLER\n*ELASTIC\n210000.0, 0.3\n")
    fh.write("*SOLID SECTION, ELSET=ROLLERS, MATERIAL=ROLLER\n\n")

    # fixed boundary conditions
    fh.write("*BOUNDARY\nSUPPORT, 3, 3, 0.0\nANCHOR, 1, 2, 0.0\nANCHOR2, 2, 2, 0.0\nROLL_SUP, 1, 3, 0.0\n")

    dt = 1.0 / N_INC
    fh.write(f"*TIME POINTS, NAME=FRAMES, GENERATE\n{dt:.6g}, 1.0, {dt:.6g}\n")
    fh.write("*STEP, NLGEOM, INC=1000\n")
    fh.write(f"*STATIC\n{dt:.6g}, 1.0, {dt * 1e-3:.6g}, {dt:.6g}\n")
    fh.write("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n8, 10, 9, 16, 10, 4, , 10\n")
    fh.write(f"*BOUNDARY\nLOAD, 3, 3, {-D_MAX}\n")
    fh.write(f"ROLL_LOAD, 1, 2, 0.0\nROLL_LOAD, 3, 3, {-D_MAX}\n")
    fh.write("*NODE FILE, TIME POINTS=FRAMES\nU\n")
    fh.write("*EL FILE, TIME POINTS=FRAMES\nS, PEEQ\n")
    fh.write("*NODE PRINT, NSET=LOAD, TOTALS=ONLY, TIME POINTS=FRAMES\nRF\n")
    fh.write("*NODE PRINT, NSET=SUPPORT, TOTALS=ONLY, TIME POINTS=FRAMES\nRF\n")
    fh.write("*END STEP\n")

print(f"Wrote {JOB}.inp")
print(f"  beam {LX:.1f} x {LY:.1f} x {LZ:.1f} mm, span {x_s2 - x_s1:.1f} mm")
print(f"  relative density {rho:.3f}")
print(f"  beam elements {n_beam_el}, roller elements {all_conn.shape[0] - n_beam_el}, nodes {all_xyz.shape[0]}")
print(f"  support nodes {len(sup_nodes)}, load nodes {len(load_nodes)}")
