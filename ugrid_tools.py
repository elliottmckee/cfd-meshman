import os
import io
import numpy as np
from scipy.spatial import KDTree


class UMesh:
    '''
    DOESNT HANDLE THE OPTIONAL FLAGS N THINGS

    TODO: Can simplify and make less redundant
    - Still kinda think the empty numpy business is funny
    '''

    float_fmt = {'float_kind':lambda x: "%.16f" % x};
    int_fmt = {'int_kind':lambda x: "%i" % x}; # Force ints to not have an extra space

    el_type_node_counts = {'tris':3, 'quads':4, 'tets':4, 'pyrmds':5, 'prisms':6, 'hexes':8}
    
    gmsh_tag_types  = {2:'tris', 3:'quads', 4:'tets', 5:'hexes', 6:'prisms', 7:'pyrmds'}
    gmsh_type_tags = {v: k for k, v in gmsh_tag_types.items()}

    def __init__(self, filename=''):

        self.filename = filename
        _, self.file_extension = os.path.splitext(self.filename)

        # Initialize empty numpy arrays for supported element types
        self.nodes = np.empty((0, 3), dtype=np.double)
        for el_type, nodecount in self.el_type_node_counts.items():
            temp = {'defs': np.empty((0, nodecount),    dtype=np.uint32), 
                    'tags': np.empty((0, 1),            dtype=np.uint32)}
            setattr(self, el_type, temp)
        
        if self.file_extension == '.ugrid':
            self.read_ugrid()
        elif self.file_extension == '.msh':
            self.read_gmsh_v2()
        else:
            raise Exception('Unrecognized mesh file extension!')


    @property
    def num_nodes(self): return self.nodes.shape[0]
    @property
    def num_tris(self): return self.tris['defs'].shape[0]
    @property
    def num_quads(self): return self.quads['defs'].shape[0]
    @property
    def num_tets(self): return self.tets['defs'].shape[0]
    @property
    def num_pyrmds(self): return self.pyrmds['defs'].shape[0]
    @property
    def num_prisms(self): return self.prisms['defs'].shape[0]
    @property
    def num_hexes(self): return self.hexes['defs'].shape[0]

    @property
    def num_bdr_elems(self): return self.num_tris + self.num_quads
    @property
    def num_vol_elems(self): return self.num_tets + self.num_pyrmds + self.num_prisms + self.num_hexes
    @property
    def num_elements(self): return self.num_bdr_elems + self.num_vol_elems
    
    @property
    def iter_elem_data(self): return [self.tris, self.quads, self.tets, self.pyrmds, self.prisms, self.hexes]
    @property
    def iter_elem_type_strs(self): return ['tris', 'quads', 'tets', 'pyrmds', 'prisms', 'hexes']
    @property
    def iter_boundary_data(self): return [self.tris, self.quads]
    @property
    def iter_volume_data(self): return [self.tets, self.pyrmds, self.prisms, self.hexes]


    def read_ugrid(self):
        '''
        https://www.simcenter.msstate.edu/software/documentation/ug_io/3d_grid_file_type_ugrid.html
        
        ASSUMES VOLUME TAGS ARE 0 (not modified)
        '''
        
        with open(self.filename) as ufile:
            # get, parse header
            header = ufile.readline().strip().split(' ')

            self.nodes = np.resize(self.nodes, (int(header[0]), 3))    

            # resize numpy array based on number of each geometry type
            for gdata, gdims, n_geoms in zip(self.iter_elem_data, self.el_type_node_counts.values(), header[1:]):
                gdata['defs'] = np.resize(gdata['defs'], (int(n_geoms), gdims))
                gdata['tags'] = np.resize(gdata['tags'], (int(n_geoms), 1))
                
            # Get nodes
            for i_pts in range(self.num_nodes):
                self.nodes[i_pts, :] = ufile.readline().strip().split(' ')
            
            # Get boundary defs
            for geom_data in self.iter_boundary_data:
                for i_geom in range(geom_data['defs'].shape[0]):
                    geom_data['defs'][i_geom, :] = ufile.readline().strip().split(' ')

            # Get boundary tags
            for geom_data in self.iter_boundary_data:
                for i_geom in range(geom_data['defs'].shape[0]):
                    geom_data['tags'][i_geom, :] = ufile.readline().strip().split(' ')

            # Get volume defs
            for geom_data in self.iter_volume_data:
                for i_geom in range(geom_data['defs'].shape[0]):
                    geom_data['defs'][i_geom, :] = ufile.readline().strip().split(' ')

            if ufile.readline():
                print("It looks like there is more file... additional/optional tags may exist, but aren't being read in!")


    def write(self, outfile):

        _, ext = os.path.splitext(outfile)

        match ext:
            case '.ugrid':
                self.write_ugrid(outfile)
            case '.msh':
                Warning('bdr_exclude_tags is being ignored (ironic)')
                self.write_gmsh_v2(outfile)
            case _:
                raise Exception('Invalid extension specified!')
                



    def write_ugrid(self, outfile):
        '''
        https://www.simcenter.msstate.edu/software/documentation/ug_io/3d_grid_file_type_ugrid.html
        '''
        print(f'Writing to {outfile}...')

        with open(outfile, 'w') as outfile:

            # write header
            header = f"{self.num_nodes} {self.num_tris} {self.num_quads} {self.num_tets} {self.num_pyrmds} {self.num_prisms} {self.num_hexes}"
            outfile.write(header+'\n')

            # write nodes
            for ii in range(self.num_nodes):
                out_str = np.array2string(self.nodes[ii, :], formatter=self.float_fmt, separator=' ').strip('[ ]')
                outfile.write(out_str+'\n')

            # write boundary faces
            for geom_data in self.iter_boundary_data:
                for i_geom in range(geom_data['defs'].shape[0]):
                    out_str = np.array2string(geom_data['defs'][i_geom, :], formatter=self.int_fmt).strip('[ ]')
                    outfile.write(out_str+'\n')

            # write boundary tags
            for geom_data in self.iter_boundary_data:
                for i_geom in range(geom_data['tags'].shape[0]):
                    out_str = np.array2string(geom_data['tags'][i_geom], formatter=self.int_fmt).strip('[ ]')
                    outfile.write(out_str+'\n')

            # write volumes
            for geom_data in self.iter_volume_data:
                for i_geom in range(geom_data['defs'].shape[0]):
                    out_str = np.array2string(geom_data['defs'][i_geom, :], formatter=self.int_fmt).strip('[ ]')
                    outfile.write(out_str+'\n')



    def write_gmsh_v2(self, outfile):
        '''
        Making this able to write volumes, to see if I can just read everything into gmsh and not have to stitch together outside
        https://gmsh.info/doc/texinfo/gmsh.html#MSH-file-format-version-2-_0028Legacy_0029

        ASSUMING THAT, WHEN WRITING, THAT PHYSICAL AND ELEMENTARY TAGS ARE THE SAME
        '''
        print(f'Writing gmsh v2 ASCII to: {outfile}')

        with open(outfile, 'w') as outfile:
            outfile.write('$MeshFormat\n')
            outfile.write('2.2 0 8\n')
            outfile.write('$EndMeshFormat\n')

            outfile.write('$Nodes\n')
            outfile.write(f'{self.num_nodes}\n')
            for i in range(self.num_nodes):
                outfile.write(f'{i+1} {self.nodes[i, 0]} {self.nodes[i, 1]} {self.nodes[i, 2]}\n')
            outfile.write('$EndNodes\n')
            
            outfile.write('$Elements\n')
            outfile.write(f'{self.num_elements}\n')
            elem_count = 1
            for geom_data, geomtype_str in zip(self.iter_elem_data, self.iter_elem_type_strs):
                gmsh_tag = self.gmsh_type_tags[geomtype_str]
                for i_geom in range(geom_data['defs'].shape[0]):
                    curr_elem_str = np.array2string(geom_data['defs'][i_geom,:], formatter=self.int_fmt).strip('[ ]')
                    geom_tag = str(geom_data['tags'][i_geom]).strip('[ ]');
                    outfile.write(f'{elem_count} {gmsh_tag} 2 {geom_tag} {geom_tag} '+ curr_elem_str + '\n')
                    elem_count = elem_count+1

            outfile.write('$EndElements\n')



    def read_gmsh_v2(self):
        '''
        https://gmsh.info/doc/texinfo/gmsh.html#MSH-file-format-version-2-_0028Legacy_0029

        ASSUMES 
            - NODES START AT 1 AND COUNT UP
            - PHYSICAL REGION TAG (first one following geomtype tag) IS WHAT WE CARE ABOUT
        TODO: 
            - Make syntax at end less bad
        '''
        print(f'Reading gmsh v2.2 ASCII file: {self.filename} \n')

        nodes = []
        elements = []

        with open(self.filename) as mshfile:

            # burn first lines 
            line = mshfile.readline() #$MeshFormat
            line = mshfile.readline().strip().split(' ') #2.2 0 8
            if line[0]!='2.2': raise Exception('Needs to be .msh v2.2 you ding dong')
            line = mshfile.readline() #$EndMeshFormat
            line = mshfile.readline() #$Nodes

            # read-in block data
            while line:
                if line.strip() == '$Nodes':
                    num_nodes = int(mshfile.readline().strip()) #num nodes
                    for i_node in range(num_nodes):
                        line = mshfile.readline().strip().split(' ')
                        nodes.append([float(x) for x in line[1:]])
                    line = mshfile.readline() #$EndNodes

                if line.strip() == '$Elements':
                    num_elems = int(mshfile.readline().strip()) #num elems
                    for i_elem in range(num_elems):
                        line = mshfile.readline().strip().split(' ')
                        elements.append([int(x) for x in line])
                    line = mshfile.readline() #$EndElements
                line = mshfile.readline()

        # Parse elements by appending to lists
        for data in self.iter_elem_data:
            data['defs'] = []
            data['tags'] = []

        for el in elements:
            if el[1] in self.gmsh_tag_types.keys():
                if el[2] != 2: raise Exception('Currently assuming only 2x tags exist per element in GMSH file')
                data = getattr(self, self.gmsh_tag_types[el[1]])
                data['defs'].append(el[5:])
                data['tags'].append(el[3])

        # Convert all back to numpy
        self.nodes = np.array(nodes, dtype=np.double)
        for data in self.iter_elem_data:
            data['defs'] = np.array(data['defs'], dtype=np.uint32)
            data['tags'] = np.array(data['tags'], dtype=np.uint32)
        

    def extract_surface(self, bc_target):
        
        print(f'Extracting boundary faces tagged with {bc_target} to new UMesh...')
        OutMesh = UMesh()

        # get index of boundary tris, quads with given target
        tri_idx  = np.argwhere(self.tris['tags']  == bc_target)[:,0]
        quad_idx = np.argwhere(self.quads['tags'] == bc_target)[:,0]

        # assign boundary connectivity data to new object
        OutMesh.tris['defs'] = self.tris['defs'][tri_idx] 
        OutMesh.tris['tags'] = self.tris['tags'][tri_idx] 
        OutMesh.quads['defs'] = self.quads['defs'][quad_idx] 
        OutMesh.quads['tags'] = self.quads['tags'][quad_idx] 

        # get node ID's on targeted boundary
        out_nodes_unique = set()

        for geom_data in OutMesh.iter_boundary_data:
            for i_geom in range(geom_data['defs'].shape[0]):
                out_nodes_unique.update(geom_data['defs'][i_geom, :])

        out_nodelist_1dx = list(out_nodes_unique) 
        out_nodelist_1dx.sort()
        out_nodelist_0dx = [x-1 for x in out_nodelist_1dx]

        # assign relevant nodes to new object
        OutMesh.nodes = self.nodes[out_nodelist_0dx, :]

        # Renumber to contiguous nodes (counting up from one) in boundary element definitions
        mapping = {orig: new+1 for orig, new in zip(out_nodelist_1dx, range(OutMesh.num_nodes))}

        for geom_data in OutMesh.iter_boundary_data:
            for ir, ic in np.ndindex(geom_data['defs'].shape):
                geom_data['defs'][ir,ic] = mapping[geom_data['defs'][ir,ic]]

        return OutMesh





        


if __name__ == "__main__":


    # file = 'box_vol'
    # file = 'box_surf'
    # file = 'box_surf_BLMESH'
    # file = 'fin_can_BLMESH'
    # file = 'box_trisurfs'
    # file = 'box_trisurfs_BLMESH'


    # Mesh = UMesh('pipe_dev/'+file+'.ugrid')
    # Mesh.write('pipe_dev/'+file+'.msh')

    # Mesh = UMesh('t16.msh')
    # Mesh.write('t16.ugrid')


    # Mesh = UMesh('box_simple_v2/cube.msh')
    # Mesh.write('box_simple_v2/cube.ugrid')

    # Mesh = UMesh('cube_BLMESH_VOLMESHED_FINAL.msh')
    # Mesh.write('cube_BLMESH_VOLMESHED_FINAL.ugrid')

    Mesh = UMesh('Fin_Can_Stubby_trisurf_v1p2_FINAL.msh')
    Mesh.write('Fin_Can_Stubby_trisurf_v1p2_FINAL.ugrid')

    # Scaling
    # Mesh = UMesh('stubby_test_v1/Fin_Can_Stubby_trisurf_v1p1.msh')
    # Mesh.nodes = Mesh.nodes/1000
    # Mesh.write('stubby_test_v1/Fin_Can_Stubby_trisurf_v1p2.msh')



    # Mesh = UMesh('stubby_test_v1/Fin_Can_Stubby_trisurf_v1.msh')
    # Mesh.tris['tags'] = Mesh.tris['tags']+1
    # Mesh.write('Fin_Can_Stubby_trisurf_v1p1.msh')






    # STEP 1: SURFACE .MSH TO UGRID
    # Mesh = UMesh(file+'.msh')
    # Mesh.write(file+'.ugrid')

    # STEP 1.5 OPTIONAL CHECK IF CONVERTING BACK TO GMSH BREAKS THINGS
    # Mesh = UMesh(file+'.ugrid')
    # Mesh.write_gmsh_v2(file+'_TEST.msh')

    # STEP 2: mesh_convert.py -i file.ugrid

    # MISSING THE EXTRUDE STEP HERE LOL

    # STEP 3: 
    # Mesh = UMesh(file+'_BLMESH.ugrid')
    # ExtractedSurfMesh = Mesh.extract_surface(bc_target=2)
    # ExtractedSurfMesh.write_gmsh_v2(file+'_BLMESH_CAP.msh')


    # Mesh = UMesh(file+'.ugrid')
    # Mesh = UMesh(file+'.msh')

    # Mesh.write(file+'_bidirectional_convert_check'+'.ugrid')
    # Mesh.write_gmsh_v2(file+'_bidirectional_convert_check.msh')


    # ExtractedSurfMesh = Mesh.extract_surface(bc_target=2)
    # ExtractedSurfMesh.write(file+'_extracted_surfmesh.ugrid')
    # ExtractedSurfMesh.write_gmsh_v2(file+'_extracted_surf.msh')


    print('Done!')

