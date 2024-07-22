'''
Example driver showing simplified end-to-end workflow









PLACEHOLDER CONGROUS GMSH SURFACE+VOLUME MESHING WORKFLOW?
not sure how necessary with mesh adaptation though lol






'''
import os
from src.ugrid_tools import UMesh
from src.gen_blmesh import gen_blmesh
from src.gen_farfield import gen_farfield


# input .msh surface mesh
input_gmsh_surf  = 'temp/rocket_v6.msh' # alternatively, use pygmsh here...?

# convert surface mesh from .msh to ugrid
input_ugrid_surf = os.path.splitext(input_gmsh_surf)[0]+'.ugrid'
SurfMesh = UMesh(input_gmsh_surf)
SurfMesh.write(input_ugrid_surf)

# extrude BL mesh from surface mesh
blmesh_path = gen_blmesh(input_ugrid_surf, num_bl_layers=7, near_wall_spacing=4.0e-6, bl_growth_rate=1.5, write_vtk=False)
# blmesh_path = gen_blmesh('rocket_v6/rocket_v6.msh', workdir='rocket_v6', num_bl_layers=13, near_wall_spacing=4.0e-6, bl_growth_rate=1.5)

# generate farfield mesh around boundary layer mesh
volmesh_path = gen_farfield(blmesh_path, farfield_radius=15, farfield_Lc=25, extend_power=.2)
# gen_farfield(bl_meshfile, farfield_radius=15, farfield_Lc=25, extend_power=.2)

# finally, convert volume mesh from .msh to .ugrid
VolMesh = UMesh(volmesh_path)
VolMesh.write(os.path.splitext(volmesh_path)[0]+'.ugrid')

 


