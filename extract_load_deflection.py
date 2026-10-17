#!/usr/bin/env python3
"""Load-deflection curve from a CalculiX .dat file (3-point bending).

Reads the 'total force ... for set LOAD' blocks written by *NODE PRINT,
converts step time to roller displacement, writes CSV (+ PNG if matplotlib).
Usage: python3 extract_load_deflection.py gyroid_bend.dat [D_MAX]
"""
import re, sys

dat = sys.argv[1] if len(sys.argv) > 1 else "gyroid_bend.dat"
d_max = float(sys.argv[2]) if len(sys.argv) > 2 else None
if d_max is None:                       # read D_MAX from the generator if present
    try:
        src = open("gyroid_bending_ccx.py").read()
        d_max = float(re.search(r"^D_MAX\s*=\s*([\d.eE+-]+)", src, re.M).group(1))
    except Exception:
        d_max = 4.0

lines = open(dat).read().splitlines()
rows = [(0.0, 0.0)]
for i, ln in enumerate(lines):
    m = re.search(r"total force \(fx,fy,fz\) for set LOAD and time\s+([\d.eE+-]+)", ln)
    if m:
        t = float(m.group(1))
        vals = [v for v in lines[i + 1:i + 4] if v.strip()][0].split()
        rows.append((t * d_max, -float(vals[2])))

csv = dat.rsplit(".", 1)[0] + "_load_deflection.csv"
with open(csv, "w") as fh:
    fh.write("deflection_mm,load_N\n")
    for d, p in rows:
        fh.write(f"{d:.5f},{p:.3f}\n")
print(f"{len(rows) - 1} increments -> {csv}")
print(f"peak load {max(p for _, p in rows):.1f} N")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d, p = zip(*rows)
    plt.figure(figsize=(5, 3.6))
    plt.plot(d, p, "o-", ms=3)
    plt.xlabel("Roller displacement (mm)")
    plt.ylabel("Load (N)")
    plt.title("Gyroid beam - 3-point bending")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    png = csv.replace(".csv", ".png")
    plt.savefig(png, dpi=150)
    print(f"plot -> {png}")
except ImportError:
    pass
