import gmsh


def sphere_surf(x, y, z, r, lc, surf_tag, physical_group):
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


def collect_size_fields(size_fields_dict):
        # GMSH didn't like me trying to pass size fields directly through/into functions that build meshes
        # so just using a dictionary outside the function + this helper to mirror this functionality
        # in a pythonic fashion
        
        gmsh_size_fields = [];
        
        # for each size field
        for size_field, params in size_fields_dict.items():
                sf_curr = gmsh.model.mesh.field.add(size_field)
                gmsh_size_fields.append(sf_curr)

                # for each parameter in size field
                for param, val in params.items():
                        gmsh.model.mesh.field.setNumber(sf_curr, param, val)

        return gmsh_size_fields







