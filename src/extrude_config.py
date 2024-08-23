EXTRUDE_CONFIG = '''input_file: {surfmesh_stem}.vtp
layers_file: layers.csv 
output_file: {blmesh_ugrid}
direction: nominal
smooth_normals: true
smooth_normals_iterations: 25
smooth_null_space: true
null_space_iterations: 5
null_space_limit: 2.0
null_space_relaxation: 0.6
eigenvector_threshold: 0.5
smooth_curvature: true
curvature_factor: 4.0     
symmetry: none 
symmetry_threshold: 2.0
unmodified_layers: 3
debug_mode: false
debug_start_layer: 1'''


