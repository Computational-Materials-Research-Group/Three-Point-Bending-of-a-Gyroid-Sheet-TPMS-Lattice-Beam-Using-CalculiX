# ParaView: smoothed, stress-coloured view of the voxel gyroid beam
# Use: Edit > Reset Session, then View > Python Shell > Run Script > smooth_view.py
from paraview.simple import *

PVD_FILE    = "/mnt/d/extras/gyroid_ccx_70/pvd/gyroid_bend.pvd"  # used only if no .pvd is open
WARP_SCALE  = 1.0       # deformation scale (1 = true deformation)
SMOOTH_ITER = 150       # 100-200; more = smoother, thin walls shrink slightly
VM_MIN, VM_MAX = 0.0, 350.0   # von Mises colour range (MPa)

reader = next((s for (n, _), s in GetSources().items() if n.lower().endswith(".pvd")), None) \
         or PVDReader(registrationName="gyroid_bend.pvd", FileName=PVD_FILE)
view = GetActiveViewOrCreate("RenderView")

warp    = WarpByVector(registrationName="Warp", Input=reader, Vectors=["POINTS", "U"], ScaleFactor=WARP_SCALE)
surf    = ExtractSurface(registrationName="Surface", Input=warp)
smooth  = Smooth(registrationName="Smooth", Input=surf, NumberofIterations=SMOOTH_ITER, Convergence=0.0)
normals = GenerateSurfaceNormals(registrationName="SmoothBeam", Input=smooth, Splitting=0)

for s in (reader, warp, surf, smooth):
    Hide(s, view)

disp = Show(normals, view)
disp.Representation = "Surface"
ColorBy(disp, ("POINTS", "S_Mises"))

lut = GetColorTransferFunction("S_Mises")
lut.ApplyPreset("Rainbow Uniform", True)
lut.AutomaticRescaleRangeMode = "Never"
lut.RescaleTransferFunction(VM_MIN, VM_MAX)
disp.SetScalarBarVisibility(view, True)
GetScalarBar(lut, view).Title = "Von Mises (MPa)"

view.CameraPosition, view.CameraFocalPoint, view.CameraViewUp = [60, -250, 15], [60, 5, 15], [0, 0, 1]
view.ResetCamera()
Render(view)
print("Done - press Play to animate.")
