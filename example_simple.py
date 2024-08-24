'''
Example driver showing simplified end-to-end workflow

NOTE
- Mesh build is performed wherever the .msh file is by default (so for this script, in resource/)
- There are a lot of intermediate files that get written in this workflow, that arent cleaned up.
'''
import os
from src.ugrid_tools import UMesh
from src.gen_blmesh import gen_blmesh
from src.gen_farfield import gen_farfield

# input .msh surface mesh
# can make in gmsh gui, or alternatively, use gmsh python api (see advanced example)
# must export from GMSH as version 2 ascii!
SurfMesh = UMesh('resource/rocket_stubby_surf.msh')

# convert surface mesh from .msh to ugrid
SurfMesh.write('resource/rocket_stubby_surf.ugrid')

# mesh_tools: extrude BoundaryLayer mesh from surface mesh, convert back to .msh
BoundLayerMesh = gen_blmesh('resource/rocket_stubby_surf.ugrid', num_bl_layers=10, near_wall_spacing=4.2e-5, bl_growth_rate=1.5)
BoundLayerMesh.write('resource/rocket_stubby_BLMESH.msh')

# gmsh: generate BoundaryLayer+Farfield mesh, by building around/outward-from the boundary layer mesh
VolumeMesh = gen_farfield('resource/rocket_stubby_BLMESH.msh', farfield_radius=15, farfield_Lc=25, extend_power=.2)

# finally, convert volume mesh from .msh to .ugrid
VolumeMesh.write('resource/rocket_stubby_VOLMESH_FINAL.ugrid')

 