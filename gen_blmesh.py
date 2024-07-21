import os
import csv
import subprocess
import warnings
from pathlib import Path

from ugrid_tools import UMesh


TEMPLATE_EXTRUDE_INPUTS = '''input_file: {fname_base}.vtp
layers_file: layers.csv 
output_file: {fname_base}_BLMESH.ugrid
direction: nominal
smooth_normals: true
smooth_normals_iterations: 15
smooth_null_space: true
null_space_iterations: 30
null_space_limit: 2.0
null_space_relaxation: 0.6
eigenvector_threshold: 0.5
smooth_curvature: true
curvature_factor: 4.0     
symmetry: none 
symmetry_threshold: 2.0
unmodified_layers: 5
debug_mode: false
debug_start_layer: 1'''
            

# HACK WORKAROUND - Need to have VSCODE instantiate shell as login shell i think, see: https://stackoverflow.com/questions/51820921/vscode-integrated-terminal-doesnt-load-bashrc-or-bash-profile
# This still doesn't work for some reason- just calling the functions, un-aliased
#ENV_ACTIVATE_ALIAS = 'activate_mesh_tools'
ENV_ACTIVATE_ALIAS = 'conda activate mesh_tools_p3p7' # THIS SHIT IS BROKEN, BUT YOU CAN DO MANUALLY


def gen_blmesh(meshfile, output_filepath=None, num_bl_layers=10, near_wall_spacing=1e-3, bl_growth_rate=1.2, workdir='.'):
    ''' 
    TODO: 
        - MAKE THIS USE A TEMP DIR?
            - AT LEAST IN THE FOLDER THAT THE .UGRID FILE IS FROM 
        - ADD CHECK IF FILES EXIST IN FOLDERS?
        - MAKE THE GMSH WRITE BATCHED, OR BINARY
    INPUTS:

    OUTPUTS: 
        outmesh_path: str, path to output BL mesh file in .msh format
    '''
    
    # Generate Layer spacing
    layers = [near_wall_spacing]
    for i in range(0, num_bl_layers):
        layers.append(round(layers[i]*bl_growth_rate, 16))
    print(f'Layers: {layers}')
    
    
    # Load in
    fname_base = Path(meshfile).stem
    Mesh = UMesh(meshfile)  

    # Checks
    if Mesh.num_vol_elems != 0:
        warnings.warn('gen_blmesh called on a mesh with volume elements\n')

    if not os.path.exists(workdir):
        os.makedirs(workdir)  

    # Change into workdir
    base_dir = os.getcwd()
    os.chdir(workdir)

    # Write mesh as ugrid
    ugrid_surf_out = f'{fname_base}.ugrid'
    print(f'Writing mesh file to {os.path.abspath(ugrid_surf_out)}\n')
    Mesh.write(ugrid_surf_out)
    print(f'Complete!\n')

    # Call mesh_tools "mesh_convert.py -i file.ugrid" to convert to .vtp
    cmd = f'{ENV_ACTIVATE_ALIAS}; mesh_convert.py -i {fname_base}.ugrid'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)

    # Write extrude.inputs
    with open('extrude.inputs', 'w') as fid:
        for line in iter(TEMPLATE_EXTRUDE_INPUTS.splitlines()):
            fid.write(eval(f"f'{line}'")+"\n")

    
    # Write layers.csv
    with open('layers.csv', 'w') as fid:
        write = csv.writer(fid)
        write.writerow(layers)  

    # Call mesh_tools extrude to get BL mesh
    print('Calling extrude...\n')
    cmd = f'{ENV_ACTIVATE_ALIAS}; extrude'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    # with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
    # for line in process.stdout:
    #   print(line.decode('utf8'))

    # Read in resultant ugrid               
    BLMesh = UMesh(f'{fname_base}_BLMESH.ugrid')
    

    # Output as .msh
    if not output_filepath: # Assign default path
        output_filepath = os.path.abspath(f'{fname_base}_BLMESH.msh')

   
    BLMesh.write_gmsh_v2(output_filepath)
    
    print(f'Converting to vtk...\n')   
    cmd = f'meshio convert {output_filepath} {output_filepath}.vtk'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f'Complete!...\n')   

    # Change back to base dir
    os.chdir(base_dir)
    return output_filepath

    


if __name__ == "__main__":


    # I THINK THIS MESH IS ACCIDENTALLY IN mm
    # blmesh_path = gen_blmesh('stubby_test_v1/Fin_Can_Stubby_trisurf_v1p2.msh', workdir='stubby_test_v1', num_bl_layers=12, near_wall_spacing=0.00000329*2, bl_growth_rate=1.5)
    
    
    # blmesh_path = gen_blmesh('rockettest_v1/rocket_v1.msh', workdir='rockettest_v1', num_bl_layers=1, near_wall_spacing=0.0001, bl_growth_rate=1.5)
    # blmesh_path = gen_blmesh('rocket_v2/rocket_v2.msh', workdir='rocket_v2', num_bl_layers=5, near_wall_spacing=0.0001, bl_growth_rate=1.5)

    # blmesh_path = gen_blmesh('rocket_v3/rocket_v3.msh', workdir='rocket_v3', num_bl_layers=7, near_wall_spacing=2.0e-5, bl_growth_rate=1.5)
    
    
    # blmesh_path = gen_blmesh('rocket_v4/rocket_v4.msh', workdir='rocket_v4', num_bl_layers=15, near_wall_spacing=2.0e-6, bl_growth_rate=1.5)
    # blmesh_path = gen_blmesh('rocket_v5/rocket_v4.msh', workdir='rocket_v5', num_bl_layers=15, near_wall_spacing=2.1e-6, bl_growth_rate=1.5)

    blmesh_path = gen_blmesh('rocket_v6/rocket_v6.msh', workdir='rocket_v6', num_bl_layers=13, near_wall_spacing=4.0e-6, bl_growth_rate=1.5)



















