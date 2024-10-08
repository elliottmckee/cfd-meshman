[<img src="resource/images/banner_1_full.png">](https://github.com/elliottmckee/cfd-meshman/blob/main/resource/images/banner_1_full.png?raw=true)

# cfd-meshman
3D unstructured mesh manufacturing/manipulation for a (currently) GMSH+NASA Mesh_Tools viscous CFD meshing stack:
- [GMSH](https://gmsh.info/) for surface meshing
- [NASA Mesh_Tools](https://software.nasa.gov/software/MSC-26648-1) for extruded boundary layer meshes
- [GMSH](https://gmsh.info/) for farfield volume meshing

cfd-meshman consists of the python tools required to get these components to talk to each other, to build combined extruded-boundary-layer + farfield volume meshes with only a handful of lines of code (see [example_simple.py](https://github.com/elliottmckee/cfd-meshman/blob/main/example_simple.py)).

**The goal here is to try and create an acceptable viscous-CFD meshing workflow that is 100% free** (assuming you can access Mesh_Tools through the [NASA Software Catalog/Technology Transfer Program](https://software.nasa.gov/)). 

The main components/functionalities of cfd-meshman are:
- **Umesh**: a "pythonic" representation of unstructured meshes, that primarily facilitates the conversion of mesh formats (GMSH v2.2 .msh <-> .ugrid)
- **gen_blmesh.py**: given a surface mesh, uses NASA Mesh_Tools to extrude a boundary layer mesh
- **gen_farfield.py**: given a boundary layer mesh (from above), uses GMSH to generate the farfield mesh between the boundary-layer and domain extents- and stitches everything together into a single domain.

This workflow is by no means perfect. It is a WIP and thus has limitations and can be brittle; but is decent enough for my personal usage. I have tried to make it somewhat modular, so if you have a better solution for any of these steps, you can ideally just use what you need.

_I welcome any help and/or feedback :)_

> [!NOTE]
> LINK TO LONGER-FORM BLOG POST TO BE ADDED HERE 



# Limitations
- cfd-meshman only supports triangular surfaces meshes right now. Going to fix shortly. All the other tools (Mesh_Tools, GMSH) should be able to handle quads just fine.
- this spits out meshes in GMSH .msh and/or (FUN3D) .ugrid formats. If you need another format for your solver, would recommend trying [meshio](https://github.com/nschloe/meshio).
- no support for symmetry planes yet, although Mesh_Tools, GMSH should be able to support them.
- this is currently focused on external-aero workflows, and there are a good few assumptions baked-in currently for domain tagging. See Usage below.



# Examples

## [example_simple.py](https://github.com/elliottmckee/cfd-meshman/blob/main/example_simple.py)
Just showing the simplest implementation of extruded boundary-layer + tet farfield:
| **Near** | **Detail** | **Far** |
| ----------- | ----------- | ----------- |
| [<img src="resource/images/example_simple_1.png" width=300>](https://github.com/elliottmckee/cfd-meshman/blob/main/resource/images/example_simple_1.png?raw=true) | [<img src="resource/images/example_simple_2.png" width=300>](https://github.com/elliottmckee/cfd-meshman/blob/main/resource/images/example_simple_2.png?raw=true) | [<img src="resource/images/example_simple_3.png" width=300>](https://github.com/elliottmckee/cfd-meshman/blob/main/resource/images/example_simple_3.png?raw=true) |

## [example_advanced.py](https://github.com/elliottmckee/cfd-meshman/blob/main/example_advanced.py)
Showing the use of GMSH size fields to do things like refine the fins/wake or increase resolution at nose tip (note that size fields get applied congrously between the surface and volume meshes):
| **Near** |
| ----------- |
| [<img src="resource/images/example_advanced_1.png" width=300>](https://github.com/elliottmckee/cfd-meshman/blob/main/resource/images/example_advanced_1.png?raw=true) | 








# Installation
I have only used this on Linux. If you're on Windows i'd recommend using WSL2.

The main dependency here that requires instruction is NASA Mesh_Tools. I recommend getting this installed and verifying it is working before playing around with this repo (as I have somewhat outlined below).

> [!NOTE]
> If you are having any issues with installation things, please feel free to reach out to me ([elliottmckee](https://github.com/elliottmckee)).


## [NASA Mesh_Tools](https://software.nasa.gov/software/MSC-26648-1)

> [!CAUTION]
> DO **NOT** USE VERSION 1.2. USE VERSION 1.1 (all versions should be included in the ZIP from the NASA request). The "extrude" functionality of v1.2 did not work for me out of the box, and requires code modifications to make it not segfault. Just use 1.1.

You have to request this from the NASA Software Catalog. See links above.

See [this paper](https://ntrs.nasa.gov/api/citations/20190000067/downloads/20190000067.pdf) for more detail on Mesh_Tools itself.

Unfortunately, this one is a bit complicated to install, but if you follow the README included with it, it should get you up and running. It does requires you to build an older version of [VTK](https://docs.vtk.org/en/latest/build_instructions/index.html) with certain flags enabled, which is inconvenient at best, and can be really horrifying at its worst. 

I recomend just using the default Anaconda install for simplicity (**This is actually required for cfd-meshman to work currently**. I used miniconda personally, but shouldn't really matter though). 

Make sure to add the path to the Mesh_Tools 'extrude' binary (mesh_tools-v1.1.0/bin/extrude) to the system PATH.

To confirm you've installed this correctly, try running the included extrude_for_char and extrude_shock examples and see if it breaks.


## cfd-meshman
1. Clone this repo
2. (recommended) create a virtual environment
3. cd into repo, `pip install -r requirements.txt`
4. Once installed, see if the simple cfd-meshman example above works. If any of the examples don't work, you're more than welcome to bug me.

> [!NOTE]
> The [current implementation](https://github.com/elliottmckee/cfd-meshman/blob/main/src/gen_blmesh.py) relies on the mesh_convert.py functionality included in Mesh_Tools. This is currently invoked using ['conda run'](https://docs.conda.io/projects/conda/en/latest/commands/run.html) functionality. If you have installed Mesh_Tools using conda above, you _shouldn't_ have any issue, **assuming** that the mesh-tools conda environement is named 'mesh_tools_p3p7'.


# Usage
- See examples. 
- If you need to modify the Mesh_Tools extrusion parameters (this is likely, it can be a bit finicky about these), modify [extrude_config.py](https://github.com/elliottmckee/cfd-meshman/blob/main/src/extrude_config.py).


# Tips
Mesh_Tools 'extrude':
- The default extrude_config.py inputs seem to work fine-ish in my experience, but often need fiddling. I don't claim to know what all of them mean, though.
- This will try and extrude as far as you tell it, and maintains a fixed extrude sizing across all elements. If you have a surface mesh with both large and small faces, and you want to extrude the big ones to near-isotropy, you're going to have some very high aspect-ratio cells grown from the smaller faces. 
- If extrusion is failing, try:
  - reducing size/number of layers, and/or increasing these incrementally
  - decreasing null space relaxation
  - increasing/decreasing null space iterations (or try disabling it?)
  - increasing/decreasing curvature_factor

> [!NOTE]
> If you're using FUN3D, the wall is tagged with 1, the farfield is tagged with 3
> In MAPBC file format: 
```
2
1	3000	wall
3	5050	farfield
```


# Other useful things
- [meshio](https://github.com/nschloe/meshio) _can_ be useful for translating meshes into other formats. This is probably better than my own custom .msh<->.ugrid conversion functions, but I just couldn't get it to do what I needed it to at the time.
- [Paraview](https://www.paraview.org/) is what I use for viewing meshes once completed (after using meshio to convert from .msh to .vtk, for example)









