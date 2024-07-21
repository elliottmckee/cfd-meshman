from __future__ import print_function
import os
import sys
import glob
import re
import errno
from itertools import islice
import struct

import vtk

# VTK Cell Types
VTK_LINE = 3  # A VTK constant identifying the line(edge) type
VTK_TRI = 5  # A VTK constant identifying the triangle type
VTK_QUAD = 9  # A VTK constant identifying the quadrangle type
VTK_TETRA = 10  # A VTK constant identifying the tetrahedron type
VTK_HEX = 12  # A VTK constant identifying the hexahedron type
VTK_PYRAMID = 14  # A VTK constant identifying the pyramid type
VTK_PRISM = 13  # A VTK constant identifying the prism (wedge) type
# VTK Data Types
VTK_POLYDATA = 0  # A VTK constant for vtkPolyData
VTK_UNSTRUCTURED_GRID = 4  # A VTK constant for vtkUnstructuredGrid
VTK_MULTI_BLOCK = 13  # A VTK constant for vtkMultiBlockDataSet


def write_dict(outfile, dict):
    for k, v in dict.items():
        outfile.write("'"+str(k)+"'"+':')
        if type(v) is str:
            outfile.write("'"+v+"'"+', \\')
        else:
            outfile.write(str(v)+', \\')
        outfile.write('\n')
    outfile.write('}\n')

    return

# Write inputs


def write_inputs(filename, dict):
    try:
        outputfile = open(filename, 'w')
    except IOError:
        print('cannot open', filename, '\nExiting!')
        sys.exit(errno.EIO)

    print('Writing input values to:', filename)
    outputfile.write('input_values = {')
    write_dict(outputfile, dict)
    outputfile.close()

    return

# Examine vtk data structure and determine face types


def getFaceTypes(grid):
    data_type = grid.GetDataObjectType()
    if data_type == VTK_POLYDATA:
        num_faces = grid.GetNumberOfCells()
        num_trias = 0
        num_quads = 0
        for i in range(num_faces):
            face_type = grid.GetCell(i).GetCellType()
            if face_type == VTK_TRI:
                num_trias += 1
            elif face_type == VTK_QUAD:
                num_quads += 1
    elif data_type == VTK_UNSTRUCTURED_GRID:
        face_types = grid.GetCellTypesArray()
        num_faces = grid.GetNumberOfCells()
        num_trias = 0
        num_quads = 0
        for i in range(num_faces):
            face_type = face_types.GetValue(i)
            if face_type == VTK_TRI:
                num_trias += 1
            elif face_type == VTK_QUAD:
                num_quads += 1
    elif data_type == VTK_MULTI_BLOCK:
        num_trias = 0
        num_quads = 0

    return num_trias, num_quads

# Examine vtk data structure and determine volume cell types


def getCellTypes(grid):
    num_tets = 0
    num_pyramids = 0
    num_prisms = 0
    num_hexs = 0
    data_type = grid.GetDataObjectType()
    if data_type == VTK_UNSTRUCTURED_GRID:
        cell_types = grid.GetCellTypesArray()
        num_cells = grid.GetNumberOfCells()
        for i in range(num_cells):
            cell_type = cell_types.GetValue(i)
            if cell_type == VTK_TETRA:
                num_tets += 1
            elif cell_type == VTK_PYRAMID:
                num_pyramids += 1
            elif cell_type == VTK_PRISM:
                num_prisms += 1
            elif cell_type == VTK_HEX:
                num_hexs += 1
            elif cell_type != VTK_TRI and cell_type != VTK_QUAD:
                print(i, cell_type)

    return num_tets, num_pyramids, num_prisms, num_hexs

# Examine vtk data structure and find surface ids
# Note: Surface ids are NOT a built in property


def get_surf_ids(grid):
    data_type = grid.GetDataObjectType()
    set_surf_ids = set()
    if data_type == VTK_POLYDATA:
        if grid.GetCellData().HasArray('surface id') is False:
            print('vtkPolyData object does not have variable: surface id')
            print('Exiting')
            sys.exit(1)
        num_faces = grid.GetNumberOfCells()
        surf_id_data = grid.GetCellData().GetArray('surface id')
        for i in range(num_faces):
            new_id = surf_id_data.GetValue(i)
            if new_id not in set_surf_ids:
                set_surf_ids.add(new_id)

    elif data_type == VTK_UNSTRUCTURED_GRID:
        surf_id_data = grid.GetCellData().GetArray('surface id')
        num_faces = surf_id_data.GetNumberOfTuples()
        for i in range(num_faces):
            new_id = surf_id_data.GetValue(i)
            if new_id not in set_surf_ids:
                set_surf_ids.add(new_id)

    elif data_type == VTK_MULTI_BLOCK:
        set_surf_ids = set()
        num_blocks = grid.GetNumberOfBlocks()
        for block in range(num_blocks):
            sub_grid = grid.GetBlock(block)
            num_faces = sub_grid.GetNumberOfCells()
            surf_id_data = sub_grid.GetCellData().GetArray('surface id')
            for i in range(num_faces):
                new_id = surf_id_data.GetValue(i)
                if new_id not in set_surf_ids:
                    set_surf_ids.add(new_id)

    surf_ids = sorted(set_surf_ids)
    return surf_ids

# GMSH Ascii format writer
# Node ordering is 1-Based
# Takes a vtk data structures and writes out a gmsh compatible file


def gmsh_edge_writer(filename, output_grid):

    num_nodes = output_grid.GetNumberOfPoints()
    num_edges = output_grid.GetNumberOfCells()

    # Header
    output_file = open(filename, 'w')
    output_file.write('$MeshFormat\n')
    output_file.write('2.2 0 8\n')
    output_file.write('$EndMeshFormat\n')

    # Nodes
    output_file.write('$Nodes\n')
    output_file.write(str(num_nodes)+'\n')
    for i in range(num_nodes):
        node = output_grid.GetPoint(i)
        output_file.write(
            str(i)+' '+str(node[0])+' '+str(node[1])+' '+str(node[2])+'\n')
    output_file.write('$EndNodes\n')

    # Faces
    output_file.write('$Elements\n')
    output_file.write(str(num_edges)+'\n')
    edge_num = 1
    for i in range(num_edges):
        face = output_grid.GetCell(i)
        face_nodes = face.GetPointIds()
        node_id0 = face_nodes.GetId(0)
        node_id1 = face_nodes.GetId(1)
        output_file.write(str(i)+' 1 2 99 '+str(edge_num) +
                          ' '+str(node_id0)+' '+str(node_id1)+'\n')
    output_file.write('$EndElements\n')

    output_file.close()
    

# GMSH Edge Ascii format writer
# Node ordering is 1-Based
# Takes a vtk data structure and writes out a gmsh compatible file


def msh_writer_v2(filename, output_grid):
    try:
        output_file = open(filename, 'w')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit(errno.EIO)

    num_nodes = output_grid.GetNumberOfPoints()
    num_cells = output_grid.GetNumberOfCells()

    # Header
    output_file.write('$MeshFormat\n')
    output_file.write('2.2 0 8\n')
    output_file.write('$EndMeshFormat\n')

    # Nodes
    output_file.write('$Nodes\n')
    output_file.write(str(num_nodes)+'\n')
    for i in range(num_nodes):
        node = output_grid.GetPoint(i)
        output_file.write(
            str(i)+' '+str(node[0])+' '+str(node[1])+' '+str(node[2])+'\n')
    output_file.write('$EndNodes\n')

    # Faces
    output_file.write('$Elements\n')
    output_file.write(str(num_cells)+'\n')
    edge_num = 1
    for i in range(num_cells):
        cell = output_grid.GetCell(i)
        cell_nodes = cell.GetPointIds()
        cell_type = cell.GetCellType()
        if cell_type == VTK_LINE:
            node_id0 = cell_nodes.GetId(0)
            node_id1 = cell_nodes.GetId(1)
            output_file.write(str(i)+' 1 2 99 '+str(edge_num) +
                              ' '+str(node_id0)+' '+str(node_id1)+'\n')
        elif cell_type == VTK_TRI:
            node_id0 = cell_nodes.GetId(0)
            node_id1 = cell_nodes.GetId(1)
            node_id2 = cell_nodes.GetId(2)
            output_file.write(str(i)+' 2 2 98 '+str(edge_num)+' ' +
                              str(node_id0)+' '+str(node_id1)+' '+str(node_id2)+'\n')
        elif cell_type == VTK_QUAD:
            node_id0 = cell_nodes.GetId(0)
            node_id1 = cell_nodes.GetId(1)
            node_id2 = cell_nodes.GetId(2)
            node_id3 = cell_nodes.GetId(3)
            output_file.write(str(i)+' 3 2 98 '+str(edge_num)+' '+str(node_id0) +
                              ' '+str(node_id1)+' '+str(node_id2)+' '+str(node_id3)+'\n')
    output_file.write('$EndElements\n')

    output_file.close()
    return

# GMSH POS format writer
# Node ordering is 1-Based
# Takes a vtk data structures and writes out a gmsh compatible file


def gmsh_bgmesh_writer(filename, output_grid):
    try:
        output_file = open(filename, 'w')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit(errno.EIO)

    num_cells = output_grid.GetNumberOfCells()

    spacing = vtk.vtkDoubleArray()
    if output_grid.GetPointData().HasArray('target_spacing'):
        spacing = output_grid.GetPointData().GetArray('target_spacing')
    else:
        print('Variable "target_spacing" was not found!')
        print('Exiting!')
        sys.exit(-1)

    # Header
    output_file.write('View "background mesh" {\n')

    # Write Triangles
    for i in range(num_cells):
        cell = output_grid.GetCell(i)
        cell_type = cell.GetCellType()
        if cell_type == VTK_TRI:
            line = 'ST('
            cell_nodes = cell.GetPointIds()
            for j in range(3):
                node_id = cell_nodes.GetId(j)
                node = output_grid.GetPoint(node_id)
                if j == 2:
                    line += ('{:.14G},{:.14G},{:.14G}'.format(
                        node[0], node[1], node[2]))
                else:
                    line += ('{:.14G},{:.14G},{:.14G},'.format(
                        node[0], node[1], node[2]))
            line += '){'
            for j in range(3):
                node_id = cell_nodes.GetId(j)
                value = spacing.GetValue(node_id)
                if j == 2:
                    line += ('{:.14G}'.format(value))
                else:
                    line += ('{:.14G},'.format(value))
            line += '};\n'
            output_file.write(line)

    output_file.write('};')
    output_file.close()
    return

# GMSH geo writer


def gmsh_geo_writer(filename, spacing):
    try:
        output_file = open(filename, 'w')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit(errno.EIO)

    output_text = '\
Merge "shock_smooth.msh";\n\
// Create a geometry for all the curves and surfaces in the mesh, by computing a\n\
// parametrization for each entity\n\
CreateGeometry;\n\
// Remesh Settings\n\
Mesh.CharacteristicLengthFromPoints = 0;\n\
Mesh.CharacteristicLengthExtendFromBoundary = 0;\n\
Mesh.Algorithm = 6; //1=MeshAdapt, 2=Automatic, 5=Delaunay, 6=Frontal, 7=BAMG, 8=DelQuad\n'
    output_file.write(output_text)
    output_file.close()
    return

# Reads in an STL formatted file and stores it as a vtkPolyData structure
# mesh_tool properties are initialized
# Note: Currently only supports Binary format


def stl_reader(filename, surf_id_offset):
    try:
        inputfile = open(filename, 'r')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit()

    # Readfile
    raw_data = inputfile.read()

    # Initialize Grid and Data Structures
    input_grid = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    is_data = vtk.vtkFloatArray()
    is_data.SetName('initial_spacing')
    blh_data = vtk.vtkFloatArray()
    blh_data.SetName('delta')
    surf_id_data = vtk.vtkIntArray()
    surf_id_data.SetName('surface id')
    bc_flag_data = vtk.vtkIntArray()
    bc_flag_data.SetName('bc flag')
    rc_flag_data = vtk.vtkIntArray()
    rc_flag_data.SetName('rc flag')

    # Check Header
    header = struct.unpack('80c', raw_data[:80])
    if header[:5] == ['s', 'o', 'l', 'i', 'd']:
        print(' Ascii Format Detected')
    else:
        print(' Binary Format Detected')
        num_trias = struct.unpack('I', raw_data[80:84])[0]
        # STL format defines each triangle independently, so total number of points
        # will be 3 times the number of triangles
        num_faces = num_trias
        input_grid.Allocate(num_faces)

        start_index = 84
        size = 50
        node_count = 0
        for i in range(num_trias):
            nodes = vtk.vtkIdList()
            # Vertex 1
            # normal = struct.unpack(
            #    'fff', raw_data[start_index+size*i:start_index+12+size*i])
            vertex = struct.unpack(
                'fff', raw_data[start_index+12+size*i:start_index+24+size*i])
            points.InsertPoint(node_count, float(
                vertex[0]), float(vertex[1]), float(vertex[2]))
            is_data.InsertNextValue(0.0)
            blh_data.InsertNextValue(0.0)
            nodes.InsertNextId(node_count)
            node_count += 1
            # Vertex 2
            vertex = struct.unpack(
                'fff', raw_data[start_index+24+size*i:start_index+36+size*i])
            points.InsertPoint(node_count, float(
                vertex[0]), float(vertex[1]), float(vertex[2]))
            is_data.InsertNextValue(0.0)
            blh_data.InsertNextValue(0.0)
            nodes.InsertNextId(node_count)
            node_count += 1
            # Vertex 3
            vertex = struct.unpack(
                'fff', raw_data[start_index+36+size*i:start_index+48+size*i])
            points.InsertPoint(node_count, float(
                vertex[0]), float(vertex[1]), float(vertex[2]))
            is_data.InsertNextValue(0.0)
            blh_data.InsertNextValue(0.0)
            nodes.InsertNextId(node_count)
            node_count += 1
            # attrib = struct.unpack(
            #    'H', raw_data[start_index+48+size*i:start_index+50+size*i])
            input_grid.InsertNextCell(VTK_TRI, nodes)
            surf_id_data.InsertNextValue(1+surf_id_offset)
            bc_flag_data.InsertNextValue(0)
            rc_flag_data.InsertNextValue(0)
            # faceNormals.append(normal)
    print('Reading Complete')
    inputfile.close()

    input_grid.SetPoints(points)
    input_grid.GetPointData().AddArray(is_data)
    input_grid.GetPointData().AddArray(blh_data)
    input_grid.GetCellData().AddArray(surf_id_data)
    input_grid.GetCellData().AddArray(bc_flag_data)
    input_grid.GetCellData().AddArray(rc_flag_data)

    return input_grid

# SURF Ascii format reader
# Reads in a UG_IO surf ascii file and stores it as a vtkPolyData structure
# mesh_tool properties are initialized
# Node ordering is 1-Based


def surf_reader(filename, surf_id_offset):
    try:
        inputfile = open(filename, 'r')
    except IOError:
        print('Cannot open', filename, '\nExiting!')
        sys.exit(1)

    # Initialize Grid
    input_grid = vtk.vtkPolyData()

    # Get Header
    header = re.split(' ', inputfile.readline().strip())
    num_trias = int(header[0])
    num_quads = int(header[1])
    num_faces = num_trias + num_quads
    num_nodes = int(header[2])

    # Read Nodes
    # Surf Format: x,y,z,initial_spacing,bl_thickness
    raw_data = list(islice(inputfile, num_nodes))

    points = vtk.vtkPoints()
    is_data = vtk.vtkFloatArray()
    is_data.SetName('initial_spacing')
    blh_data = vtk.vtkFloatArray()
    blh_data.SetName('delta')

    for i in range(num_nodes):
        vertex = raw_data[i].strip().split(' ')
        points.InsertPoint(i, float(vertex[0]), float(
            vertex[1]), float(vertex[2]))
        if len(vertex) == 3:
            is_data.InsertNextValue(0.0)
            blh_data.InsertNextValue(0.0)
        elif len(vertex) == 4:
            is_data.InsertNextValue(float(vertex[3]))
            blh_data.InsertNextValue(0.0)
        elif len(vertex) == 5:
            is_data.InsertNextValue(float(vertex[3]))
            blh_data.InsertNextValue(float(vertex[4]))

    input_grid.SetPoints(points)
    input_grid.GetPointData().AddArray(is_data)
    input_grid.GetPointData().AddArray(blh_data)

    input_grid.Allocate(num_faces)

    # Faces
    # SURF format assumes Node values are 1-based.  Adjust to Zero base
    surf_id_data = vtk.vtkIntArray()
    surf_id_data.SetName('surface id')
    bc_flag_data = vtk.vtkIntArray()
    bc_flag_data.SetName('bc flag')
    rc_flag_data = vtk.vtkIntArray()
    rc_flag_data.SetName('rc flag')
    raw_data = list(islice(inputfile, num_faces))
    for i in range(num_faces):
        face = raw_data[i].strip().split(' ')
        face_size = len(face)
        nodes = vtk.vtkIdList()
        if face_size == 6:  # Tria
            face_nodes = 3
            surf_id_data.InsertNextValue(int(face[3])+surf_id_offset)
            rc_flag_data.InsertNextValue(int(face[4]))
            bc_flag_data.InsertNextValue(int(face[5]))
            for node in range(face_nodes):
                nodes.InsertNextId(int(face[node])-1)
            input_grid.InsertNextCell(VTK_TRI, nodes)
        elif face_size == 7:  # Quad
            face_nodes = 4
            surf_id_data.InsertNextValue(int(face[4])+surf_id_offset)
            rc_flag_data.InsertNextValue(int(face[5]))
            bc_flag_data.InsertNextValue(int(face[6]))
            for node in range(face_nodes):
                nodes.InsertNextId(int(face[node])-1)
            input_grid.InsertNextCell(VTK_QUAD, nodes)
        else:
            print('Error: Face size is unsupported.  Exiting Program')
            sys.exit()

    input_grid.GetCellData().AddArray(surf_id_data)
    input_grid.GetCellData().AddArray(bc_flag_data)
    input_grid.GetCellData().AddArray(rc_flag_data)

    return input_grid

# SURF Ascii format writer
# Node ordering is 1-Based
# Takes a vtk data structure and writes out a UG_IO surf format file


def surf_writer(filename, output_grid):

    # Open Output File
    try:
        output_file = open(filename, 'w')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit()

    # Header
    num_nodes = output_grid.GetNumberOfPoints()
    num_faces = output_grid.GetNumberOfCells()
    num_trias, num_quads = getFaceTypes(output_grid)
    output_file.write(str(num_trias)+' '+str(num_quads) +
                      ' '+str(num_nodes)+'\n')

    # Nodes
    is_data = output_grid.GetPointData().GetArray('initial_spacing')
    blh_data = output_grid.GetPointData().GetArray('delta')
    for i in range(num_nodes):
        node = output_grid.GetPoint(i)
        is_value = is_data.GetValue(i)
        blh_value = blh_data.GetValue(i)
        output_file.write('{:.14G} {:.14G} {:.14G} {:.14G} {:.14G}\n'.format(
            node[0], node[1], node[2], is_value, blh_value))

    # Faces
    surf_id_data = output_grid.GetCellData().GetArray('surface id')
    bc_flag_data = output_grid.GetCellData().GetArray('bc flag')
    rc_flag_data = output_grid.GetCellData().GetArray('rc flag')
    # Write All Trias First
    for i in range(num_faces):
        face = output_grid.GetCell(i)
        face_type = face.GetCellType()
        if face_type == VTK_TRI:
            face_nodes = face.GetPointIds()
            num_face_nodes = face_nodes.GetNumberOfIds()
            surf_id_value = surf_id_data.GetValue(i)
            bc_flag_value = bc_flag_data.GetValue(i)
            rc_flag_value = rc_flag_data.GetValue(i)
            # Write Node IDs
            for i in range(num_face_nodes):
                output_file.write(str(face_nodes.GetId(i)+1)+' ')
            # Write Surf ID and Flags
            output_file.write(str(surf_id_value)+' ' +
                              str(rc_flag_value)+' '+str(bc_flag_value)+'\n')
    # Write All Quads
    for i in range(num_faces):
        face = output_grid.GetCell(i)
        face_type = face.GetCellType()
        if face_type == VTK_QUAD:
            face_nodes = face.GetPointIds()
            num_face_nodes = face_nodes.GetNumberOfIds()
            surf_id_value = surf_id_data.GetValue(i)
            bc_flag_value = bc_flag_data.GetValue(i)
            rc_flag_value = rc_flag_data.GetValue(i)
            # Write Node IDs
            for i in range(num_face_nodes):
                output_file.write(str(face_nodes.GetId(i)+1)+' ')
            # Write Surf ID and Flags
            output_file.write(str(surf_id_value)+' ' +
                              str(rc_flag_value)+' '+str(bc_flag_value)+'\n')
    return

# UGRID Ascii format reader
# Reads in a UG_IO surf ascii file and stores it as a vtkPolyData structure
# mesh_tool properties are initialized
# Node ordering is 1-Based
# Note: UGRID files can contain only faces or a mix of faces and volume
# elements. If only faces are present, the data structure is initialized
# as vtkPolyData, otherwise the more generic vtkUnstructuredGrid is used.


def ugrid_reader(filename, surf_id_offset):

    try:
        inputfile = open(filename, 'r')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit()

    # Get Header
    header = re.split(' ', inputfile.readline().strip())
    num_nodes = int(header[0])
    num_trias = int(header[1])
    num_quads = int(header[2])
    num_faces = num_trias + num_quads
    num_tets = int(header[3])
    num_pyramids = int(header[4])
    num_prisms = int(header[5])
    num_hexes = int(header[6])
    num_elems = num_tets + num_pyramids + num_prisms + num_hexes

    # Initialize Grid and Data Structures
    if num_elems == 0:
        input_grid = vtk.vtkPolyData()
    else:
        input_grid = vtk.vtkUnstructuredGrid()
    # Initialize Grid and Data Structures
    points = vtk.vtkPoints()
    is_data = vtk.vtkFloatArray()
    is_data.SetName('initial_spacing')
    blh_data = vtk.vtkFloatArray()
    blh_data.SetName('delta')
    surf_id_data = vtk.vtkIntArray()
    surf_id_data.SetName('surface id')
    bc_flag_data = vtk.vtkIntArray()
    bc_flag_data.SetName('bc flag')
    rc_flag_data = vtk.vtkIntArray()
    rc_flag_data.SetName('rc flag')

    # Nodes
    # UGRID format only has x,y,z
    raw_data = list(islice(inputfile, num_nodes))
    points = vtk.vtkPoints()
    for i in range(num_nodes):
        vertex = raw_data[i].strip().split(' ')
        points.InsertPoint(i, float(vertex[0]), float(
            vertex[1]), float(vertex[2]))
    # If the UGRID file is a surface only, generate blank is and blh data
    if num_elems == 0:
        for i in range(num_nodes):
            is_data.InsertValue(i, 0.0)
            blh_data.InsertValue(i, 0.0)

    input_grid.SetPoints(points)
    if num_elems == 0:
        input_grid.GetPointData().AddArray(is_data)
        input_grid.GetPointData().AddArray(blh_data)

    # Faces
    # UGRID format assumes Node values are 1-based.  Adjust to Zero base
    # UGRID format faces section only has nodes ids
    input_grid.Allocate(num_faces)
    raw_data = list(islice(inputfile, num_faces))
    for i in range(num_faces):
        face = raw_data[i].strip().split(' ')
        face_size = len(face)
        nodes = vtk.vtkIdList()
        if face_size == 3:  # Tria
            face_nodes = 3
            for node in range(face_nodes):
                nodes.InsertNextId(int(face[node])-1)
            input_grid.InsertNextCell(VTK_TRI, nodes)
        elif face_size == 4:  # Quad
            face_nodes = 4
            for node in range(face_nodes):
                nodes.InsertNextId(int(face[node])-1)
            input_grid.InsertNextCell(VTK_QUAD, nodes)
        else:
            print('Error: Face size is unsupported.  Exiting Program')
            print(i)
            print(num_faces)
            print(face)
            sys.exit()

    # SurfIDs
    # UGRID list surface ID of faces separate from node IDs
    surf_id_data = vtk.vtkIntArray()
    surf_id_data.SetName('surface id')
    raw_data = list(islice(inputfile, num_faces))
    for i in range(num_faces):
        face_id = raw_data[i].strip()
        surf_id_data.InsertNextValue(int(face_id)+surf_id_offset)

    if num_elems == 0:
        for i in range(num_faces):
            bc_flag_data.InsertValue(i, -1)
            rc_flag_data.InsertValue(i, 0)

    # Volume Elements
    if num_elems > 0:
        raw_data = list(islice(inputfile, num_elems))
        for i in range(num_elems):
            elem = raw_data[i].strip().split(' ')
            elem_size = len(elem)
            nodes = vtk.vtkIdList()
            for node in range(elem_size):
                nodes.InsertNextId(int(elem[node])-1)
            if elem_size == 4:  # Tet
                elem_type = VTK_TETRA
            elif elem_size == 5:  # Pyramid
                elem_type = VTK_PYRAMID
                # Reorder Ids
                nodes_temp = vtk.vtkIdList()
                nodes_temp.InsertNextId(nodes.GetId(0))  # VTK 0 -> UGIO 0
                nodes_temp.InsertNextId(nodes.GetId(3))  # VTK 3 -> UGIO 1
                nodes_temp.InsertNextId(nodes.GetId(4))  # VTK 4 -> UGIO 2
                nodes_temp.InsertNextId(nodes.GetId(1))  # VTK 1 -> UGIO 3
                nodes_temp.InsertNextId(nodes.GetId(2))  # VTK 2 -> UGIO 4
                nodes = nodes_temp
            elif elem_size == 6:  # Prism
                elem_type = VTK_PRISM
            elif elem_size == 8:  # Hex
                elem_type = VTK_HEX
            input_grid.InsertNextCell(elem_type, nodes)
            surf_id_data.InsertNextValue(0)

    input_grid.GetCellData().AddArray(surf_id_data)
    if num_elems == 0:
        input_grid.GetCellData().AddArray(bc_flag_data)
        input_grid.GetCellData().AddArray(rc_flag_data)

    return input_grid

# UGRID Ascii format writer
# Node ordering is 1-Based


def ugrid_writer(filename, output_grid):
    try:
        output_file = open(filename, 'w')
    except IOError:
        print('cannot open', filename, '\nexiting')
        sys.exit()

    # Check Data Type and Convert if Necassary
    data_type = output_grid.GetDataObjectType()
    if data_type == VTK_UNSTRUCTURED_GRID:
        pass
    elif data_type == VTK_POLYDATA:
        # Append PolyData
        append_filter = vtk.vtkAppendFilter()
        append_filter.AddInputData(output_grid)
        append_filter.Update()
        output_grid = append_filter.GetOutputDataObject(0)
    else:
        print('Unsupported Data Type for ugrid writer!')
        print('Exiting!')
        sys.exit(-1)

    write_block_size = 10000

    # UGRID format requires all faces and elements sorted by type:
    # 1) Trias, Quads.
    # 2) Tets,Pyramids(Pent5),Prisms(Pent6),Hexs
    # Perform a sort to guarantee this is the case

    # Header
    num_nodes = output_grid.GetNumberOfPoints()
    num_trias, num_quads = getFaceTypes(output_grid)
    num_tets, num_pyramids, num_prisms, num_hexes = getCellTypes(output_grid)

    # Cell Data
    # Note: contains surface ids very every cell including volume cells (0)
    surf_id_data = output_grid.GetCellData().GetArray('surface id')

    output_file = open(filename, 'w')
    output_file.write(str(num_nodes)+' ')
    output_file.write(str(num_trias)+' ')
    output_file.write(str(num_quads)+' ')
    output_file.write(str(num_tets)+' ')
    output_file.write(str(num_pyramids)+' ')
    output_file.write(str(num_prisms)+' ')
    output_file.write(str(num_hexes))
    output_file.write('\n')

    # Write Nodes
    block = ''
    block_size = 0
    for i in range(num_nodes):
        node = output_grid.GetPoint(i)
        # block += (str(node[0])+' '+str(node[1])+' '+str(node[2])+'\n')
        block += ('{:.14G} {:.14G} {:.14G}\n'.format(
            node[0], node[1], node[2]))
        block_size += 1
        if block_size == write_block_size:
            output_file.write(block)
            block = ''
            block_size = 0
    # Write remaining data
    output_file.write(block)

    # Write Surface Element Connectivity
    block = ''
    block_size = 0
    # Write All Trias First
    if num_trias > 0:
        tria_cells = vtk.vtkIdTypeArray()
        output_grid.GetIdsOfCellsOfType(VTK_TRI, tria_cells)
        for i in range(num_trias):
            cell_id = tria_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            cell_nodes = cell.GetPointIds()
            num_cell_nodes = cell_nodes.GetNumberOfIds()
            # Write Node IDs
            for i in range(num_cell_nodes):
                output_file.write(str(cell_nodes.GetId(i)+1)+' ')
            output_file.write('\n')
            # last_id_type = cell_type
    # Write Quads Next
    if num_quads > 0:
        quad_cells = vtk.vtkIdTypeArray()
        output_grid.GetIdsOfCellsOfType(VTK_QUAD, quad_cells)
        for i in range(num_quads):
            cell_id = quad_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            cell_nodes = cell.GetPointIds()
            num_cell_nodes = cell_nodes.GetNumberOfIds()
            # Write Node IDs
            for i in range(num_cell_nodes):
                output_file.write(str(cell_nodes.GetId(i)+1)+' ')
            output_file.write('\n')

    # Write Surface Ids
    # Write All Tria Ids First
    if num_trias > 0:
        for i in range(num_trias):
            cell_id = tria_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            surf_id_value = surf_id_data.GetValue(cell_id)
            output_file.write(str(surf_id_value)+'\n')
    if num_quads > 0:
        for i in range(num_quads):
            cell_id = quad_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            surf_id_value = surf_id_data.GetValue(cell_id)
            output_file.write(str(surf_id_value)+'\n')

    # Write Elements
    # Write All Tets First
    if num_tets > 0:
        tet_cells = vtk.vtkIdTypeArray()
        output_grid.GetIdsOfCellsOfType(VTK_TETRA, tet_cells)
        for i in range(num_tets):
            cell_id = tet_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            cell_nodes = cell.GetPointIds()
            num_cell_nodes = cell_nodes.GetNumberOfIds()
            # Write Node IDs
            for i in range(num_cell_nodes):
                output_file.write(str(cell_nodes.GetId(i)+1)+' ')
            output_file.write('\n')
    # Write All Pyramids Next
    if num_pyramids > 0:
        pyramid_cells = vtk.vtkIdTypeArray()
        output_grid.GetIdsOfCellsOfType(VTK_PYRAMID, pyramid_cells)
        for i in range(num_pyramids):
            cell_id = pyramid_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            cell_nodes = cell.GetPointIds()
            num_cell_nodes = cell_nodes.GetNumberOfIds()
            # Reorder Ids
            nodes_temp = vtk.vtkIdList()
            nodes_temp.InsertNextId(cell_nodes.GetId(0))
            nodes_temp.InsertNextId(cell_nodes.GetId(3))
            nodes_temp.InsertNextId(cell_nodes.GetId(4))
            nodes_temp.InsertNextId(cell_nodes.GetId(1))
            nodes_temp.InsertNextId(cell_nodes.GetId(2))
            cell_nodes = nodes_temp
            # Write Node IDs
            for i in range(num_cell_nodes):
                output_file.write(str(cell_nodes.GetId(i)+1)+' ')
            output_file.write('\n')
    # Write All Prisms Next
    if num_prisms > 0:
        prism_cells = vtk.vtkIdTypeArray()
        output_grid.GetIdsOfCellsOfType(VTK_PRISM, prism_cells)
        for i in range(num_prisms):
            cell_id = prism_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            cell_nodes = cell.GetPointIds()
            num_cell_nodes = cell_nodes.GetNumberOfIds()
            # Write Node IDs
            for i in range(num_cell_nodes):
                output_file.write(str(cell_nodes.GetId(i)+1)+' ')
            output_file.write('\n')
    # Write All Hexes
    if num_hexes > 0:
        hex_cells = vtk.vtkIdTypeArray()
        output_grid.GetIdsOfCellsOfType(VTK_HEX, hex_cells)
        for i in range(num_hexes):
            cell_id = hex_cells.GetValue(i)
            cell = output_grid.GetCell(cell_id)
            cell_nodes = cell.GetPointIds()
            num_cell_nodes = cell_nodes.GetNumberOfIds()
            # Write Node IDs
            for i in range(num_cell_nodes):
                output_file.write(str(cell_nodes.GetId(i)+1)+' ')
            output_file.write('\n')

    output_file.close()

    return

# Master file reader for mesh_tools
# This function is called generically in the mesh_tools scripts. The function
# automatically identifies the correct file reader by the file extenstion
# provided.


def file_reader(filename, surf_id_offset):
    file_ext = os.path.splitext(filename)[-1]
    # if(file_ext == '.msh'):
    #     nodeData, faceData = gmsh_surf_reader(filename, nodeData, faceData)
    if(file_ext == '.ply'):
        # Use VTK Reader option
        ply_reader = vtk.vtkPLYReader()
        ply_reader.SetFileName(filename)
        ply_reader.Update()

        input_grid = ply_reader.GetOutput(0)
    elif(file_ext == '.stl'):
        input_grid = stl_reader(filename, surf_id_offset)
    elif(file_ext == '.surf'):
        input_grid = surf_reader(filename, surf_id_offset)
    elif(file_ext == '.ugrid'):
        input_grid = ugrid_reader(filename, surf_id_offset)
    else:
        print(file_ext, ' is an unrecognized file extension!\n Exiting')
        sys.exit(1)
    return input_grid


def finalize_ensight_files(dir_name):

    # Make sure dir exists
    if os.path.isdir(dir_name) is False:
        os.mkdir(dir_name)

    # Change dir
    cwdir = os.getcwd()  # Get Current Dir
    os.chdir(dir_name)

    # Find geo file
    # Use this an an anchor to the process as VTK always writes this
    geo_file = None
    geo_files = glob.glob('*.geo')
    if len(geo_files) != 1:
        print('Bad number of .geo files found!')
        sys.exit(1)
    else:
        geo_file = geo_files[0]

    # Parse filename
    base_name = geo_file.split('.')[0]

    # Rename ensight files
    ensight_files = glob.glob(base_name+'.*')
    node_var_names = list()
    for item in ensight_files:
        item_name = item.split('.')
        ext = item_name[-1]
        var_type = item_name[-2].split('_')[-1]
        new_name = base_name + '.' + ext
        if ext != 'geo' and ext != 'case':
            # check if node or cell based
            if var_type == 'n':
                node_var_names.append(new_name)
        os.rename(item, new_name)

    # Write case file
    case_file_name = base_name + '.case'
    try:
        case_file = open(case_file_name, 'w')
    except IOError:
        print('cannot open', case_file_name, '\nExiting!')
        sys.exit(1)
    # Header
    case_file.write('FORMAT\n')
    case_file.write('type:  ensight gold\n')
    case_file.write('GEOMETRY\n')
    case_file.write('model:  ' + base_name + '.geo\n')
    case_file.write('VARIABLE\n')
    # Node based data
    for item in node_var_names:
        var = item.split('.')[-1]
        case_file.write('scalar per node:	 ' + var + '	' + item + '\n')
    case_file.close()
    os.chdir(cwdir)
