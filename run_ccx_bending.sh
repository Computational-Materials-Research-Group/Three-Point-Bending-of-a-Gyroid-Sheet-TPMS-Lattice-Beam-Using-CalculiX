#!/bin/bash
# ============================================================
#  Gyroid beam 3-point bending (CalculiX) -> ParaView .pvd, 70 frames
#
#  One-time install (Ubuntu / WSL):
#     sudo apt install calculix-ccx python3-pip zip
#     pip install numpy scipy matplotlib
#     pipx install ccx2paraview && pipx inject ccx2paraview vtk
#
#  Run:   bash run_ccx_bending.sh
# ============================================================
set -e
JOB=gyroid_bend
NP=14                                     # CPU threads

export OMP_NUM_THREADS=$NP
export CCX_NPROC_STIFFNESS=$NP
export CCX_NPROC_EQUATION_SOLVER=$NP
export CCX_NPROC_RESULTS=$NP

echo ">>> 1/4  Building mesh + input deck"
python3 gyroid_bending_ccx.py

echo ">>> 2/4  Solving with CalculiX ($NP threads) - progress: tail -f ${JOB}.sta"
ccx $JOB > ccx.log 2>&1
tail -n 2 $JOB.sta

echo ">>> 3/4  Converting to ParaView (.vtu frames + .pvd)"
mkdir -p pvd && cd pvd
ln -sf ../$JOB.frd $JOB.frd
ccx2paraview $JOB.frd vtu
rm -f $JOB.frd
cd ..


echo ">>> 4/4  Load-deflection curve"
python3 extract_load_deflection.py $JOB.dat

echo "Done. Open pvd/${JOB}.pvd in ParaView and press Play."
