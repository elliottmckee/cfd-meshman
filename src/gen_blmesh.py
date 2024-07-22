import os
import csv
import subprocess
import warnings
from pathlib import Path

from .ugrid_tools import UMesh
from .extrude_config import EXTRUDE_CONFIG


def gen_blmesh(surfmesh_ugrid_path, num_bl_layers=10, near_wall_spacing=1e-4, bl_growth_rate=1.2, write_vtk=False):
    ''' 
    TODO: 
        - MAKE THIS USE A TEMP DIR?
        - more explicit warnings if failed
        - Allow parameter overwrites, or pointing to new default extrude inputs file 
        - Remove clunky interaction with mesh_tools mesh_convert.py, and just add VTP writer to Umesh
        - Output stream of extrude command to pipe for realtime outputs

    NOTES:
        - All work is performed in directory where surface mesh file lives

    INPUTS:
        surfmesh_ugrid_path: str, path to .ugrid surface mesh file to exrude

    OUTPUTS: 
        blmesh_msh: str, path to output BL mesh file in .msh format
    '''

    # paths
    base_dir = os.getcwd()
    work_dir = os.path.dirname(surfmesh_ugrid_path)
    
    surfmesh_stem   = Path(surfmesh_ugrid_path).stem
    blmesh_ugrid    = f'{surfmesh_stem}_BLMESH.ugrid'
    blmesh_msh      = f'{surfmesh_stem}_BLMESH.msh'
    blmesh_vtk      = f'{surfmesh_stem}_BLMESH.vtk'
    blmesh_ugrid_path   = os.path.join(work_dir, blmesh_ugrid)
    blmesh_msh_path     = os.path.join(work_dir, blmesh_msh)
    blmesh_vtk_path     = os.path.join(work_dir, blmesh_vtk)
    
    # generate layer spacing
    layers = [near_wall_spacing]
    for i in range(0, num_bl_layers):
        layers.append(layers[i]*bl_growth_rate)
    print(f'Layers: {layers}')
     
    # cd into "workdir"
    os.chdir(work_dir)

    # Call mesh_tools mesh_convert.py to convert .ugrid to .vtp
    print('Calling mesh_tools mesh_convert to convert .ugrid to .vtp...\n')
    cmd = f'conda run --verbose -n mesh_tools_p3p7 mesh_convert.py -i {surfmesh_stem}.ugrid'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout); print(result.stderr)

    # Write extrude.inputs
    with open('extrude.inputs', 'w') as fid:
        for line in iter(EXTRUDE_CONFIG.splitlines()):
            fid.write(eval(f"f'{line}'")+"\n")

    # Write layers.csv
    with open('layers.csv', 'w') as fid:
        write = csv.writer(fid)
        write.writerow(layers)  

    # Call mesh_tools extrude to get BL mesh
    print('Calling mesh_tools extrude...\n')
    cmd = 'extrude'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout); print(result.stderr)

    # Change back to base dir
    os.chdir(base_dir)

    # Read in resultant ugrid, convert to .msh               
    BLMesh = UMesh(blmesh_ugrid_path)
    BLMesh.write(blmesh_msh_path)
    
    if write_vtk:
        print(f'Converting BL mesh to VTK using meshio (workaround)...\n')   
        cmd = f'meshio convert {blmesh_ugrid_path} {blmesh_vtk_path}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout); print(result.stderr) 

    return blmesh_msh_path

    