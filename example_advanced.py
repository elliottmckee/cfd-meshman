'''
Example driver showing advanced end-to-end workflow highlighting
- using gmsh api for "semi-automated" surface meshing
- gmsh size fields common between surface and volume

NOTE
- Mesh build is performed wherever the .msh file is by default (so for this script, in resource/)
- There are a lot of intermediate files that get written in this workflow, that arent cleaned up.
'''

import os
import gmsh
from src.ugrid_tools import UMesh
from src.gen_blmesh import gen_blmesh
from src.gen_farfield import gen_farfield
from src.gmsh_helpers import collect_size_fields


############################
# SURFACE MESH WITH GMSH API
###
gmsh.initialize()
gmsh.option.setNumber("General.NumThreads", 4)

# merge in BL mesh file
gmsh.merge('resource/rocket_stubby.step')
gmsh.model.geo.synchronize()

# lets selectively refine *a few* of the point sizings around the fin edge radii 
points_refine = [68,69,102,103,106,107,72,73,88,89,114,115,84,85,111,110,56,57,94,95,90,91,52,53,33,34,75,76,79,80,37,38,25,26,64,41,42,64,6,7,51,18,19,27,25,26,64]
points_dimTags = [(0, point) for point in points_refine]
gmsh.model.mesh.setSize(points_dimTags, 0.008)

# Lets pass some additional size-fields in 
# This will get applied congrously to the surface and volume meshes!
# This dictionary mirrors how you specify size fields in the GMSH api
size_fields_dict = {'Cylinder':{'VIn':      0.02,
                                'VOut':     1e22,
                                'XAxis':    0.45,
                                'YAxis':    0.0,
                                'ZAxis':    0.0,
                                'XCenter':  -0.1,
                                'YCenter':  0.0,
                                'ZCenter':  0.0,
                                'Radius':   0.3},
                    'Ball':{'Radius':   0.05,
                            'Thickness':0.05,
                            'VIn':      0.015,
                            'VOut':     1e22,           
                            'XCenter':  0.718}}

# have to massage a bit into gmsh format
size_field_tags = collect_size_fields(size_fields_dict)

# take min of all size fields
min_all_sizefields = gmsh.model.mesh.field.add("Min")
gmsh.model.mesh.field.setNumbers(min_all_sizefields, "FieldsList", size_field_tags)
gmsh.model.mesh.field.setAsBackgroundMesh(min_all_sizefields)

# gmsh options
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)     
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 1)
gmsh.option.setNumber("Mesh.MeshSizeMax", 0.03)

# generate mesh
gmsh.model.mesh.generate(2)    

# save out
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.write('resource/rocket_stubby_advanced.msh')
gmsh.finalize()
############################


# convert surface mesh from .msh to ugrid
SurfMesh = UMesh('resource/rocket_stubby_advanced.msh')
SurfMesh.write('resource/rocket_stubby_advanced.ugrid')

# mesh_tools: extrude BoundaryLayer mesh from surface mesh, convert back to .msh
BoundLayerMesh = gen_blmesh('resource/rocket_stubby_advanced.ugrid', num_bl_layers=9, near_wall_spacing=4.2e-5, bl_growth_rate=1.5)
BoundLayerMesh.write('resource/rocket_stubby_advanced_BLMESH.msh')

# gmsh: generate BoundaryLayer+Farfield mesh, by building around/outward-from the boundary layer mesh
VolumeMesh = gen_farfield('resource/rocket_stubby_advanced_BLMESH.msh', farfield_radius=15, farfield_Lc=25, extend_power=.2, size_fields_dict=size_fields_dict)

# finally, convert volume mesh from .msh to .ugrid
VolumeMesh.write('resource/rocket_stubby_advanced_VOLMESH_FINAL.ugrid')

 