import os
import math
import csv
import subprocess
import warnings
from pathlib import Path

import numpy as np

import gmsh
from ugrid_tools import UMesh


# HACK WORKAROUND
ENV_ACTIVATE_ALIAS = 'activate_mesh_tools'





def gen_farfield(bl_meshfile, farfield_radius=10, farfield_Lc=2, extend_power=2, numthreads=6):
    '''
    TODO: 
        - I TRIED TO MAKE THIS WITH OPENCASCADE BUT WAS HAVING ISSUES. AM PROBABLY JUST DUMB

    INPUTS:

    OUTPUTS: 
    '''

    # The distribution of the mesh element sizes will be obtained by interpolation
    # of these mesh sizes throughout the geometry. Another method to specify mesh
    # sizes is to use general mesh size Fields (see `t10.py'). A particular case is
    # the use of a background mesh (see `t7.py').
    
    #   gmsh.option.setNumber("Mesh.MshFileVersion", x)
    # for any version number `x'. As an alternative, you can also not specify the
    # format explicitly, and just choose a filename with the `.msh2' or `.msh4'
    # extension.

    # To visualize the model we can run the graphical user interface with
    # `gmsh.fltk.run()'. Here we run it only if "-nopopup" is not provided in the
    # command line arguments:
    # if '-nopopup' not in sys.argv:
    #     gmsh.fltk.run()

    # Note that starting with Gmsh 3.0, models can be built using other geometry
    # kernels than the default "built-in" kernel. To use the OpenCASCADE CAD kernel
    # instead of the built-in kernel, you should use the functions with the
    # `gmsh.model.occ' prefix.
    #
    # Different CAD kernels have different features. With OpenCASCADE, instead of
    # defining the surface by successively defining 4 points, 4 curves and 1 curve
    # loop, one can define the rectangular surface directly with
    #
    # gmsh.model.occ.addRectangle(.2, 0, 0, .1, .3)
    #
    # After synchronization with the Gmsh model with
    #
    # gmsh.model.occ.synchronize()
    #
    # the underlying curves and points could be accessed with
    # gmsh.model.getBoundary().
    #
    # See e.g. `t16.py', `t18.py', `t19.py' or `t20.py' for complete examples based
    # on OpenCASCADE, and `examples/api' for more.

    # Mesh sizes associated to geometrical points can be set by passing a vector of
    # (dim, tag) pairs for the corresponding points:
    # gmsh.model.geo.mesh.setSize([(0, 103), (0, 105), (0, 109), (0, 102), (0, 28),
    #                             (0, 24), (0, 6), (0, 5)], lc * 3)

    # https://gitlab.onelab.info/gmsh/gmsh/-/blob/gmsh_4_12_1/tutorials/python/t3.py

    # In order to compute the mesh sizes from the background mesh only, and
    # disregard any other size constraints, one can set:
    # gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

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

    def gmsh_sphere_surf(x, y, z, r, lc, surf_tag, physical_group):
        # This function will create a spherical shell (surf_tag) 

        p1 = gmsh.model.geo.addPoint(x, y, z, lc)
        p2 = gmsh.model.geo.addPoint(x + r, y, z, lc)
        p3 = gmsh.model.geo.addPoint(x, y + r, z, lc)
        p4 = gmsh.model.geo.addPoint(x, y, z + r, lc)
        p5 = gmsh.model.geo.addPoint(x - r, y, z, lc)
        p6 = gmsh.model.geo.addPoint(x, y - r, z, lc)
        p7 = gmsh.model.geo.addPoint(x, y, z - r, lc)

        c1 = gmsh.model.geo.addCircleArc(p2, p1, p7)
        c2 = gmsh.model.geo.addCircleArc(p7, p1, p5)
        c3 = gmsh.model.geo.addCircleArc(p5, p1, p4)
        c4 = gmsh.model.geo.addCircleArc(p4, p1, p2)
        c5 = gmsh.model.geo.addCircleArc(p2, p1, p3)
        c6 = gmsh.model.geo.addCircleArc(p3, p1, p5)
        c7 = gmsh.model.geo.addCircleArc(p5, p1, p6)
        c8 = gmsh.model.geo.addCircleArc(p6, p1, p2)
        c9 = gmsh.model.geo.addCircleArc(p7, p1, p3)
        c10 = gmsh.model.geo.addCircleArc(p3, p1, p4)
        c11 = gmsh.model.geo.addCircleArc(p4, p1, p6)
        c12 = gmsh.model.geo.addCircleArc(p6, p1, p7)

        l1 = gmsh.model.geo.addCurveLoop([c5, c10, c4])
        l2 = gmsh.model.geo.addCurveLoop([c9, -c5, c1])
        l3 = gmsh.model.geo.addCurveLoop([c12, -c8, -c1])
        l4 = gmsh.model.geo.addCurveLoop([c8, -c4, c11])
        l5 = gmsh.model.geo.addCurveLoop([-c10, c6, c3])
        l6 = gmsh.model.geo.addCurveLoop([-c11, -c3, c7])
        l7 = gmsh.model.geo.addCurveLoop([-c2, -c7, -c12])
        l8 = gmsh.model.geo.addCurveLoop([-c6, -c9, c2])

        s1 = gmsh.model.geo.addSurfaceFilling([l1])
        s2 = gmsh.model.geo.addSurfaceFilling([l2])
        s3 = gmsh.model.geo.addSurfaceFilling([l3])
        s4 = gmsh.model.geo.addSurfaceFilling([l4])
        s5 = gmsh.model.geo.addSurfaceFilling([l5])
        s6 = gmsh.model.geo.addSurfaceFilling([l6])
        s7 = gmsh.model.geo.addSurfaceFilling([l7])
        s8 = gmsh.model.geo.addSurfaceFilling([l8])

        sl = gmsh.model.geo.addSurfaceLoop([s1, s2, s3, s4, s5, s6, s7, s8], surf_tag)
        
        gmsh.model.geo.synchronize()
        gmsh.model.addPhysicalGroup(2, [s1, s2, s3, s4, s5, s6, s7, s8], physical_group)
        return sl
    
    
    gmsh.initialize()
    gmsh.option.setNumber('Geometry.Tolerance', 1e-16)
    gmsh.option.setNumber("General.NumThreads", numthreads)
    gmsh.model.add("model_1")

    # Merge in BLMESH, make surface loops with tagged surfs (i think only works in gmsh kernel. see notes above tho)
    gmsh.merge(bl_meshfile)
    
    ####################################################################################
    # THESE TAGS CHANGES SOMETIMES...??IF YOU ARE HAVING ISSUES TRY CHANGING THIS FIRST, may have to change things below (extend field)
    ####################################################################################
    gmsh.model.geo.addSurfaceLoop([0], 1) 
    gmsh.model.geo.addSurfaceLoop([1], 2) 
    # gmsh.model.geo.addSurfaceLoop([2], 2) 
    
    # Create Farfield
    sphere_sl = gmsh_sphere_surf(x=0, y=0, z=0, r=farfield_radius, lc=farfield_Lc, surf_tag=50, physical_group=3)

    # Create farfield volume (SPHERE-BLMESH_OUTERINTERFACE)
    gmsh.model.geo.addVolume([sphere_sl, 2], 60)
    
    # have to synchronize before physical groups
    gmsh.model.geo.remove_all_duplicates()
    gmsh.model.geo.synchronize()


    # 1 is inner, 2 is outer NOT ALWAYS..?
    gmsh.model.addPhysicalGroup(2, [0], 1)
    # gmsh.model.addPhysicalGroup(2, [2], 2)
    gmsh.model.addPhysicalGroup(3, [0], 1) # BL MESH VOLUME I ARBITRARILY SET THIS SHIT TO 0 IN UGRID READER
    # gmsh.model.addPhysicalGroup(2, [sphere_sl], 4)
    gmsh.model.addPhysicalGroup(3, [60], 61) # FARFIELD MESH VOLUME

    # Extend size field, see extend_field.py example
    #   Can't figure out how to get this field to act on sphere farfield. But we can just be smart about 
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

    # Save
    # gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    outfile_stem = f'{Path(bl_meshfile).stem}_VOLMESHED'
    gmsh.write(outfile_stem+'.msh')

    gmsh.finalize()

    # Convert to ugrid (NEED TO DELETE INTERNAL INTERFACE FIRST)
    #print('Converting to .ugrid...\n')
    #mesh = UMesh(outfile_stem+'.msh')
    #mesh.write(outfile_stem+'.ugrid')

    # Convert to VTK
    print('Converting to .vtk...\n')
    cmd = f'meshio convert {outfile_stem}.msh {outfile_stem}.vtk'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    



def gen_sphere():
    gmsh.initialize()
    gmsh.option.setNumber("General.NumThreads", 4)
    gmsh.model.add("model_1")

    # Create Farfield
    sphere_sl = gmsh_sphere_surf(x=0, y=0, z=0, r=10, lc=3, surf_tag=50, physical_group=3)
    # Add sphere to physical group
    # gmsh.model.addPhysicalGroup(2, [sphere_sl], 4)
    
    # Create combined volume (SPHERE-BLMESH_OUTERINTERFACE)
    gmsh.model.geo.addVolume([sphere_sl], 60)
    gmsh.model.addPhysicalGroup(3, [60], 61)

    # Configure Size Field Behavior
    # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    # Need to force extend from boundary to only occur on 2D surfaces (farfield)
    # gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", -2)
    
    # set 3D algo. 10=HXT(parallel delaunay)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)

    # go to work
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(3)

    

    # gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write("sphere.msh")

    # Convert to VTK
    # cmd = f'{ENV_ACTIVATE_ALIAS}; meshio convert t16.msh t16.vtk'
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    gmsh.finalize()






if __name__ == "__main__":

    
    # bl_meshfile = 'pipe_dev/box_trisurfs_BLMESH.msh'
    #bl_meshfile = os.path.join('stubby_test_v1', 'Fin_Can_Stubby_trisurf_v1p2_BLMESH.msh')
    #gen_farfield(bl_meshfile, farfield_radius=5, farfield_Lc=1, extend_power=.5)   


    #bl_meshfile = os.path.join('rockettest_v1', 'rocket_v1_BLMESH.msh')
    #gen_farfield(bl_meshfile, farfield_radius=10, farfield_Lc=6, extend_power=.75)

    # bl_meshfile = os.path.join('rocket_v2', 'rocket_v2_BLMESH.msh')
    # gen_farfield(bl_meshfile, farfield_radius=10, farfield_Lc=6, extend_power=.75)
    #mesh = UMesh('rocket_v2_BLMESH_VOLMESHED_no_int.msh')
    #mesh.write('rocket_v2_BLMESH_VOLMESHED_no_int.ugrid')

    
                
    # bl_meshfile = os.path.join('rocket_v3', 'rocket_v3_BLMESH.msh')
    # gen_farfield(bl_meshfile, farfield_radius=15, farfield_Lc=20, extend_power=.3)
    # mesh = UMesh('rocket_v3_BLMESH_VOLMESHED_no_int.msh')
    # mesh.write('rocket_v3_BLMESH_VOLMESHED_no_int.ugrid')


    # bl_meshfile = os.path.join('rocket_v4', 'rocket_v4_BLMESH.msh')
    # gen_farfield(bl_meshfile, farfield_radius=15, farfield_Lc=30, extend_power=.2)
    # mesh = UMesh('rocket_v4_BLMESH_VOLMESHED_no_int.msh')
    # mesh.write('rocket_v4_BLMESH_VOLMESHED_no_int.ugrid')

    # bl_meshfile = os.path.join('rocket_v5', 'rocket_v4  _BLMESH.msh')
    # gen_farfield(bl_meshfile, farfield_radius=15, farfield_Lc=30, extend_power=.2)
    # mesh = UMesh('rocket_v5_BLMESH_VOLMESHED_no_int.msh')
    # mesh.write('rocket_v5_BLMESH_VOLMESHED_no_int.ugrid')

    # bl_meshfile = os.path.join('rocket_v6', 'rocket_v6_BLMESH.msh')
    # gen_farfield(bl_meshfile, farfield_radius=15, farfield_Lc=25, extend_power=.2)
    mesh = UMesh('rocket_v6_BLMESH_VOLMESHED_no_int.msh')
    mesh.write('rocket_v6_BLMESH_VOLMESHED_no_int.ugrid')

    #print('Converting to .ugrid...\n')
    #mesh = UMesh('rocket_v1_BLMESH_VOLMESHED_no_int.msh')
    #mesh.write('rocket_v1_BLMESH_VOLMESHED_no_int.ugrid')

    






    # bl_meshfile = 'pipe_dev/box_trisurfs_BLMESH.msh'
    # bl_meshfile = os.path.join('box_simple_v2', 'cube_BLMESH.msh')
    # gen_farfield(bl_meshfile, farfield_radius=100, farfield_Lc=20, extend_power=.5)



    # gen_sphere()
    # Mesh = UMesh('sphere.msh')
    # Mesh.write('sphere.ugrid', bdr_exclude_tags=[])


    # Convert to ugrid, removing internal face
    # Mesh = UMesh('t16.msh')
    # Mesh.write('t16.ugrid', bdr_exclude_tags=[])

    # for i in Mesh.tris['tags']:
    #     print(i)

    # Convert to gmsh cuz im dumb
    # Mesh = UMesh('t16.ugrid')
    # Mesh.write('t16_cycled.msh')

    

