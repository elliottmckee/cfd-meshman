'''
Example driver showing simplified end-to-end workflow

NOTE
- Mesh build is performed wherever the .msh file is by default (so for this script, in resource/)
- There are a lot of intermediate files that get written in this workflow, that arent cleaned up.
'''
import os
import gmsh
from src.ugrid_tools import UMesh
from src.gen_blmesh import gen_blmesh
from src.gen_farfield import gen_farfield


# Lets pass some additional size-fields in 
# This will get applied congrously to the surface and volume meshes!
# This dictionary mirrors how you specify size fields in the GMSH api
size_fields_dict = {'Cylinder':{'VIn':  0.03,
                                'VOut': 1e22,
                                'XAxis': 0.4,
                                'YAxis': 0.0,
                                'ZAxis': 0.0,
                                'XCenter': -0.1,
                                'YCenter': 0.0,
                                'ZCenter': 0.0,
                                'Radius': 0.3}}


# f_wake = gmsh.model.mesh.field.add("Cylinder")
# gmsh.model.mesh.field.setNumber(f_wake, "VIn",  0.03)
# gmsh.model.mesh.field.setNumber(f_wake, "VOut", 1e22)
# gmsh.model.mesh.field.setNumber(f_wake, "XAxis", 0.4)
# gmsh.model.mesh.field.setNumber(f_wake, "YAxis", 0)
# gmsh.model.mesh.field.setNumber(f_wake, "ZAxis", 0)
# gmsh.model.mesh.field.setNumber(f_wake, "XCenter", -0.1)
# gmsh.model.mesh.field.setNumber(f_wake, "YCenter", 0.0)
# gmsh.model.mesh.field.setNumber(f_wake, "ZCenter", 0.0)
# gmsh.model.mesh.field.setNumber(f_wake, "Radius",  0.3) 

# f_shoulder = gmsh.model.mesh.field.add("Cylinder")
# gmsh.model.mesh.field.setNumber(f_shoulder, "VIn",  0.025)
# gmsh.model.mesh.field.setNumber(f_shoulder, "VOut", 1e22)
# gmsh.model.mesh.field.setNumber(f_shoulder, "XAxis", 0.03)
# gmsh.model.mesh.field.setNumber(f_shoulder, "YAxis", 0)
# gmsh.model.mesh.field.setNumber(f_shoulder, "ZAxis", 0)
# gmsh.model.mesh.field.setNumber(f_shoulder, "XCenter", 1.53)
# gmsh.model.mesh.field.setNumber(f_shoulder, "YCenter", 0.0)
# gmsh.model.mesh.field.setNumber(f_shoulder, "ZCenter", 0.0)
# gmsh.model.mesh.field.setNumber(f_shoulder, "Radius",  0.25) 

# f_tip = gmsh.model.mesh.field.add("Ball")   
# gmsh.model.mesh.field.setNumber(f_tip, "Radius",  0.03)
# gmsh.model.mesh.field.setNumber(f_tip, "Thickness",  0.05)
# gmsh.model.mesh.field.setNumber(f_tip, "VIn",  0.01)
# gmsh.model.mesh.field.setNumber(f_tip, "VOut",  1e22)
# gmsh.model.mesh.field.setNumber(f_tip, "XCenter",  1.9)

# f_tip2 = gmsh.model.mesh.field.add("Ball")   
# gmsh.model.mesh.field.setNumber(f_tip2, "Radius",  0.15)
# gmsh.model.mesh.field.setNumber(f_tip2, "Thickness",  0.1)
# gmsh.model.mesh.field.setNumber(f_tip2, "VIn",  0.03)
# gmsh.model.mesh.field.setNumber(f_tip2, "VOut",  1e22)
# gmsh.model.mesh.field.setNumber(f_tip2, "XCenter",  1.9)


# input .msh surface mesh
# can make in gmsh gui, or alternatively, use gmsh python api (see advanced example)
# must export from GMSH as version 2 ascii!
SurfMesh = UMesh('resource/rocket_stubby.msh')

# convert surface mesh from .msh to ugrid
SurfMesh.write('resource/rocket_stubby.ugrid')

# mesh_tools: extrude BoundaryLayer mesh from surface mesh, convert back to .msh
BoundLayerMesh = gen_blmesh('resource/rocket_stubby.ugrid', num_bl_layers=10, near_wall_spacing=4.2e-5, bl_growth_rate=1.5)
BoundLayerMesh.write('resource/rocket_stubby_BLMESH.msh')

# gmsh: generate BoundaryLayer+Farfield mesh, by building around/outward-from the boundary layer mesh
VolumeMesh = gen_farfield('resource/rocket_stubby_BLMESH.msh', farfield_radius=15, farfield_Lc=25, extend_power=.2, size_fields_dict=size_fields_dict)

# finally, convert volume mesh from .msh to .ugrid
VolumeMesh.write('resource/rocket_stubby_VOLMESH_FINAL.ugrid')

 