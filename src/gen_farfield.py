import os
import math
import csv
import subprocess
import warnings
import gmsh
import numpy as np

from pathlib import Path

from .gmsh_helpers import sphere_surf
from .ugrid_tools import UMesh


def gen_farfield(bl_msh_path, farfield_radius=10, farfield_Lc=2, extend_power=0.5, numthreads=4):
    '''
    TODO: 
        - I TRIED TO MAKE THIS WORK WITH OPENCASCADE BUT WAS HAVING ISSUES. AM PROBABLY JUST DUMB. TRY AGAIN LATER
            See e.g. 't1.py', `t16.py', `t18.py', `t19.py' or `t20.py' for complete examples based on OpenCASCADE, and `examples/api' for more.
        - MAKE THIS AUTOMATICALLY DELETE THE INTERFACE SURFACE
        - Make additional size field a passed-in thing

    INPUTS:
        bl_msh_path: str, path to .msh formatted boundary layer mesh (from gen_blmesh.py)

    OUTPUTS:

    NOTES: 
        - If things break below- it is likely due to assumptions about surface tagging, mainly for the BLMESH outer-most interface surface. Double check these if issues

    GMSH tidbits
    # t10.py, Mesh size fields
    # Finally, while the default "Frontal-Delaunay" 2D meshing algorithm
    # (Mesh.Algorithm = 6) usually leads to the highest quality meshes, the
    #  "Delaunay" algorithm (Mesh.Algorithm = 5) will handle complex mesh size fields
    # better - in particular size fields with large element size gradients:

    # t12.py
    # // "Compound" meshing constraints allow to generate meshes across surface
    # // boundaries, which can be useful e.g. for imported CAD models (e.g. STEP) with
    # // undesired small features.

    # t16.py
    # If we had wanted five empty holes we would have used `cut()' again. Here we
    # want five spherical inclusions, whose mesh should be conformal with the mesh
    # of the cube: we thus use `fragment()', which intersects all volumes in a
    # conformal manner (without creating duplicate interfaces):
    # ov, ovv = gmsh.model.occ.fragment([(3, 3)], holes)

    # x1.py
    # Create a geometry for the discrete curves and surfaces, so that we can remesh
    # them later on:
    # gmsh.model.mesh.createGeometry()
    # Note that for more complicated meshes, e.g. for on input unstructured STL
    # mesh, we could use `classifySurfaces()' to automatically create the discrete
    # entities and the topology; but we would then have to extract the boundaries
    # afterwards.

    '''

    # paths
    volmesh_msh = os.path.splitext(bl_msh_path)[0]+'_VOLMESHED.msh'

    # init gmsh    
    gmsh.initialize()
    gmsh.option.setNumber('Geometry.Tolerance', 1e-16)
    gmsh.option.setNumber("General.NumThreads", numthreads)
    gmsh.model.add("model_1")

    # merge in BL mesh file, 
    gmsh.merge(bl_msh_path)
    
    # make surface loop based on the tagged surfaces of the blmesh, 
    # (expected: 0 is the geometric/wall surface, 1 is the "top cap" of the Bl mesh, but I don't think that is guaranteed)
    # syntax: surfaceTags (vector of integers), tag = -1 (integer) 
    eltag_surf_wall      = gmsh.model.geo.addSurfaceLoop([0], 1) 
    eltag_surf_bl_topcap = gmsh.model.geo.addSurfaceLoop([1], 2) 
    
    # Create Farfield
    eltag_surf_sphere = sphere_surf(x=0, y=0, z=0, r=farfield_radius, lc=farfield_Lc, surf_tag=50, physical_group=3)

    # Create farfield volume (SPHERE-BLMESH_OUTERINTERFACE)
    eltag_vol_farfield = gmsh.model.geo.addVolume([eltag_surf_sphere, eltag_surf_bl_topcap], 60)
    
    # have to synchronize before physical groups
    gmsh.model.geo.remove_all_duplicates() #not sure if necessary
    gmsh.model.geo.synchronize()

    # assign physical groups
    # reminder: all meshes in gmsh must have physical group or will not be written (unless you use the write_all_elements flag in gmsh)
    # syntax: dim (integer), tags (vector of integers for model entities), tag = -1 (integer for physical surface tag), name = "" (string) 
    phystag_surf_wall    = gmsh.model.addPhysicalGroup(2, [0], 1)
    phystag_vol_bl       = gmsh.model.addPhysicalGroup(3, [0], 1) # FOR THIS BL MESH VOLUME- I ARBITRARILY SET THIS TO 0 IN UGRID READER
    phystag_vol_farfield = gmsh.model.addPhysicalGroup(3, [60], 61) # FARFIELD MESH VOLUME

    # Extend size field, see extend_field.py example
    #   Can't figure out how to get this field to act on sphere farfield. But we can just be kinda smart about 
    #   how we set DistMax and SizeMax, relative to the sphere size to get basically the same result
    f_extend = gmsh.model.mesh.field.add("Extend")
    gmsh.model.mesh.field.setNumbers(f_extend, "SurfacesList", [1])
    # # gmsh.model.mesh.field.setNumbers(f, "CurvesList", [e[1] for e in gmsh.model.getEntities(1)])    
    gmsh.model.mesh.field.setNumber(f_extend, "DistMax", farfield_radius)
    gmsh.model.mesh.field.setNumber(f_extend, "SizeMax", farfield_Lc)
    gmsh.model.mesh.field.setNumber(f_extend, "Power", extend_power)

    f_wake = gmsh.model.mesh.field.add("Cylinder")
    gmsh.model.mesh.field.setNumber(f_wake, "VIn",  0.03)
    gmsh.model.mesh.field.setNumber(f_wake, "VOut", 1e22)
    gmsh.model.mesh.field.setNumber(f_wake, "XAxis", 0.4)
    gmsh.model.mesh.field.setNumber(f_wake, "YAxis", 0)
    gmsh.model.mesh.field.setNumber(f_wake, "ZAxis", 0)
    gmsh.model.mesh.field.setNumber(f_wake, "XCenter", -0.1)
    gmsh.model.mesh.field.setNumber(f_wake, "YCenter", 0.0)
    gmsh.model.mesh.field.setNumber(f_wake, "ZCenter", 0.0)
    gmsh.model.mesh.field.setNumber(f_wake, "Radius",  0.3) 

    f_shoulder = gmsh.model.mesh.field.add("Cylinder")
    gmsh.model.mesh.field.setNumber(f_shoulder, "VIn",  0.025)
    gmsh.model.mesh.field.setNumber(f_shoulder, "VOut", 1e22)
    gmsh.model.mesh.field.setNumber(f_shoulder, "XAxis", 0.03)
    gmsh.model.mesh.field.setNumber(f_shoulder, "YAxis", 0)
    gmsh.model.mesh.field.setNumber(f_shoulder, "ZAxis", 0)
    gmsh.model.mesh.field.setNumber(f_shoulder, "XCenter", 1.53)
    gmsh.model.mesh.field.setNumber(f_shoulder, "YCenter", 0.0)
    gmsh.model.mesh.field.setNumber(f_shoulder, "ZCenter", 0.0)
    gmsh.model.mesh.field.setNumber(f_shoulder, "Radius",  0.25) 

    f_tip = gmsh.model.mesh.field.add("Ball")   
    gmsh.model.mesh.field.setNumber(f_tip, "Radius",  0.03)
    gmsh.model.mesh.field.setNumber(f_tip, "Thickness",  0.05)
    gmsh.model.mesh.field.setNumber(f_tip, "VIn",  0.01)
    gmsh.model.mesh.field.setNumber(f_tip, "VOut",  1e22)
    gmsh.model.mesh.field.setNumber(f_tip, "XCenter",  1.9)

    f_tip2 = gmsh.model.mesh.field.add("Ball")   
    gmsh.model.mesh.field.setNumber(f_tip2, "Radius",  0.15)
    gmsh.model.mesh.field.setNumber(f_tip2, "Thickness",  0.1)
    gmsh.model.mesh.field.setNumber(f_tip2, "VIn",  0.03)
    gmsh.model.mesh.field.setNumber(f_tip2, "VOut",  1e22)
    gmsh.model.mesh.field.setNumber(f_tip2, "XCenter",  1.9)

    f_min_all = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(f_min_all, "FieldsList", [f_extend, f_wake, f_shoulder, f_tip, f_tip2])

    # gmsh.model.mesh.field.setAsBackgroundMesh(f_extend)
    gmsh.model.mesh.field.setAsBackgroundMesh(f_min_all)

    # Options
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", -2) # Need to force extend from boundary to only occur on 2D surfaces (farfield)

    # Generate
    gmsh.model.mesh.generate(3)
                
    # Postprocess
    gmsh.model.mesh.remove_duplicate_nodes()
    gmsh.model.mesh.remove_duplicate_elements()

    # Remove interface
    gmsh.model.mesh.removeElements(eltag_surf_bl_topcap, 1)

    # Save
    # gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(volmesh_msh)
    gmsh.finalize()

    return volmesh_msh

    
