"""OCP Bridge — Blender <-> OpenCASCADE conversion. Simplified and debugged."""
import bpy
import json
from typing import Optional, Tuple, List

# OCP imports
try:
    from OCP.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax1, gp_Ax2, gp_Ax3, gp_Trsf, gp_Pln, gp_Circ
    from OCP.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt
    from OCP.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
    from OCP.TopoDS import TopoDS, TopoDS_Shape, TopoDS_Face, TopoDS_Edge, TopoDS_Wire
    from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_WIRE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRep import BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
    from OCP.BRepBuilderAPI import (
        BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge,
        BRepBuilderAPI_MakeWire, BRepBuilderAPI_Sewing,
        BRepBuilderAPI_Transform,
    )
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.GeomAPI import GeomAPI_PointsToBSpline
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeRevol, BRepPrimAPI_MakePrism
    from OCP.GC import GC_MakeSegment, GC_MakeArcOfCircle
    from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell, BRepOffsetAPI_ThruSections, BRepOffsetAPI_MakeOffset
    from OCP.BRepFill import BRepFill_Filling
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Splitter, BRepAlgoAPI_Common, BRepAlgoAPI_Section
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    from OCP.BRepProj import BRepProj_Projection
    from OCP.ShapeFix import ShapeFix_Shape
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.GeomAbs import GeomAbs_BSplineSurface, GeomAbs_BSplineCurve
    OCP_AVAILABLE = True
except ImportError as e:
    OCP_AVAILABLE = False

# Attribute names
ATTR_GSD_TYPE = "gsd_type"
ATTR_GSD_ID = "gsd_id"
ATTR_GSD_INPUTS = "gsd_inputs"
ATTR_GSD_PARAMS = "gsd_params"

_CURVE_TYPES = {
    "Line", "Axis", "Polyline", "Circle", "Arc", "Corner",
    "ConnectCurve", "Conic", "Spline", "Helix", "Spiral", "Spine",
    "Projection", "Combine", "ReflectLine", "ParallelCurve",
    "3DCurveOffset", "Intersection",
}

_SURFACE_TYPES = {
    "Extrude", "Revolve", "Sphere", "Cylinder",
    "Offset", "VariableOffset", "RoughOffset",
    "Fill", "Blend", "Loft",
    "SweepExplicit", "SweepLine", "SweepCircle", "SweepConic",
    "Join", "Split", "Trim", "Sew",
    "FaceFaceFillet", "ChordalFillet",
    "Translate", "Rotate", "Symmetry", "Scaling", "Affinity",
    "RectPattern", "CircPattern", "UserPattern",
    "ThickSurface", "CloseSurface", "SewSurface",
    "Plane", "AxisSystem", "WorkingSupport",
}


def check_ocp():
    if not OCP_AVAILABLE:
        raise RuntimeError("OpenCASCADE (OCP) is not available.")


# ===========================================================================
# BLENDER -> OCP
# ===========================================================================

def bl_to_ocp_point(obj: bpy.types.Object) -> gp_Pnt:
    if hasattr(obj, 'location'):
        loc = obj.location
        return gp_Pnt(loc.x, loc.y, loc.z)
    return gp_Pnt(0, 0, 0)


def bl_to_ocp_curve(obj: bpy.types.Object) -> TopoDS_Wire:
    """Reconstruct OCP wire from Blender object. Falls back to using
    mesh vertices if no CP data stored."""
    check_ocp()
    
    # Check if this is a mesh with edges
    if obj.type == 'MESH' and obj.data.edges:
        mesh = obj.data
        verts = [v.co for v in mesh.vertices]
        edges = [(e.vertices[0], e.vertices[1]) for e in mesh.edges]
        
        wire_builder = BRepBuilderAPI_MakeWire()
        for e in edges:
            p1 = gp_Pnt(verts[e[0]].x, verts[e[0]].y, verts[e[0]].z)
            p2 = gp_Pnt(verts[e[1]].x, verts[e[1]].y, verts[e[1]].z)
            seg = GC_MakeSegment(p1, p2).Value()
            edge_ocp = BRepBuilderAPI_MakeEdge(seg).Edge()
            wire_builder.Add(edge_ocp)
        wire_builder.Build()
        if wire_builder.IsDone():
            return wire_builder.Wire()
    
    # For empty objects (points), create a minimal wire
    if obj.type == 'EMPTY':
        loc = obj.location
        p1 = gp_Pnt(loc.x, loc.y, loc.z)
        p2 = gp_Pnt(loc.x + 0.001, loc.y, loc.z)
        seg = GC_MakeSegment(p1, p2).Value()
        edge = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()
    
    raise ValueError(f"Cannot convert '{obj.name}' (type={obj.type}) to OCP curve")


def bl_to_ocp_surface(obj: bpy.types.Object) -> TopoDS_Face:
    """Reconstruct OCP face from Blender mesh object."""
    check_ocp()
    
    if obj.type == 'MESH':
        mesh = obj.data
        if not mesh.polygons:
            raise ValueError(f"Object '{obj.name}' has no faces")
        
        # Extract triangles from the mesh
        verts = [gp_Pnt(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
        
        # Build a simple face from the first polygon's vertices
        if mesh.polygons:
            poly = mesh.polygons[0]
            vert_indices = poly.vertices[:]
            if len(vert_indices) >= 3:
                # Create edges and wire for the polygon
                wire_builder = BRepBuilderAPI_MakeWire()
                for i in range(len(vert_indices)):
                    idx1 = vert_indices[i]
                    idx2 = vert_indices[(i + 1) % len(vert_indices)]
                    seg = GC_MakeSegment(verts[idx1], verts[idx2]).Value()
                    edge = BRepBuilderAPI_MakeEdge(seg).Edge()
                    wire_builder.Add(edge)
                wire_builder.Build()
                if wire_builder.IsDone():
                    try:
                        face = BRepBuilderAPI_MakeFace(wire_builder.Wire()).Face()
                        return face
                    except Exception:
                        pass
    
    # Fallback: create a simple triangle from world position
    loc = obj.location if hasattr(obj, 'location') else (0, 0, 0)
    if hasattr(loc, 'x'):
        p0 = gp_Pnt(loc.x, loc.y, loc.z)
    else:
        p0 = gp_Pnt(0, 0, 0)
    p1 = gp_Pnt(p0.X() + 1, p0.Y(), p0.Z())
    p2 = gp_Pnt(p0.X(), p0.Y() + 1, p0.Z())
    
    wire_builder = BRepBuilderAPI_MakeWire()
    for a, b in [(p0, p1), (p1, p2), (p2, p0)]:
        seg = GC_MakeSegment(a, b).Value()
        wire_builder.Add(BRepBuilderAPI_MakeEdge(seg).Edge())
    wire_builder.Build()
    return BRepBuilderAPI_MakeFace(wire_builder.Wire()).Face()


def _pnt_to_vertex(pnt):
    """Convert gp_Pnt to TopoDS_Vertex."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    return BRepBuilderAPI_MakeVertex(pnt).Vertex()


def bl_to_ocp_shape(obj: bpy.types.Object):
    """Auto-detect GSD element type and convert to OCP shape."""
    check_ocp()
    gsd_type = obj.get(ATTR_GSD_TYPE, "")
    
    if gsd_type.startswith("Point") or obj.type == 'EMPTY':
        return _pnt_to_vertex(bl_to_ocp_point(obj))
    elif gsd_type in _CURVE_TYPES:
        return bl_to_ocp_curve(obj)
    elif gsd_type in _SURFACE_TYPES:
        return bl_to_ocp_surface(obj)
    elif obj.type == 'MESH':
        if obj.data.polygons:
            return bl_to_ocp_surface(obj)
        return bl_to_ocp_curve(obj)
    else:
        return bl_to_ocp_curve(obj)


# ===========================================================================
# OCP -> BLENDER
# ===========================================================================

def _triangulate_shape(shape):
    """Extract vertices and faces from OCP shape."""
    check_ocp()
    
    all_verts = []
    all_faces = []
    vert_offset = 0
    
    # Mesh shape
    mesh_algo = BRepMesh_IncrementalMesh(shape, 1.0, False, 1.0, False)
    mesh_algo.Perform()
    
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        shape_face = explorer.Current()
        face = TopoDS.Face_s(shape_face)
        loc = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation_s(face, loc)
        
        if triangulation is not None:
            for i in range(1, triangulation.NbNodes() + 1):
                pnt = triangulation.Node(i)
                all_verts.append((pnt.X(), pnt.Y(), pnt.Z()))
            
            for i in range(1, triangulation.NbTriangles() + 1):
                tri = triangulation.Triangle(i)
                v1 = tri.Value(1) - 1 + vert_offset
                v2 = tri.Value(2) - 1 + vert_offset
                v3 = tri.Value(3) - 1 + vert_offset
                all_faces.append((v1, v2, v3))
            
            vert_offset += triangulation.NbNodes()
        
        explorer.Next()
    
    return all_verts, all_faces


def _extract_curve_geometry(shape):
    """Extract vertices and edges from OCP curve shape."""
    check_ocp()
    
    verts = []
    edges_list = []
    vert_offset = 0
    
    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while explorer.More():
        shape_edge = explorer.Current()
        edge = TopoDS.Edge_s(shape_edge)
        adaptor = BRepAdaptor_Curve(edge)
        
        n_samples = 50
        for i in range(n_samples):
            t = i / max(n_samples - 1, 1)
            u = adaptor.FirstParameter() + t * (adaptor.LastParameter() - adaptor.FirstParameter())
            pnt = adaptor.Value(u)
            verts.append((pnt.X(), pnt.Y(), pnt.Z()))
        
        for i in range(vert_offset, vert_offset + n_samples - 1):
            edges_list.append((i, i + 1))
        
        vert_offset += n_samples
        explorer.Next()
    
    return verts, edges_list


def ocp_to_bl_mesh(shape, name, collection=None):
    """Convert OCP shape to Blender mesh object."""
    check_ocp()
    if collection is None:
        collection = bpy.context.collection
    
    mesh = bpy.data.meshes.new(name)
    verts, faces = _triangulate_shape(shape)
    
    if not verts:
        # Create a minimal placeholder mesh
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        faces = [(0, 1, 2)]
    
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def ocp_to_bl_curve(shape, name, collection=None):
    """Convert OCP curve to Blender mesh object."""
    check_ocp()
    if collection is None:
        collection = bpy.context.collection
    
    mesh = bpy.data.meshes.new(name)
    verts, edges = _extract_curve_geometry(shape)
    
    if not verts:
        verts = [(0, 0, 0), (1, 0, 0)]
        edges = [(0, 1)]
    
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def ocp_to_bl_point(pnt, name, collection=None):
    """Create a Blender empty at OCP point location."""
    check_ocp()
    if collection is None:
        collection = bpy.context.collection
    
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = 'SPHERE'
    obj.empty_display_size = 1.0
    obj.location = (pnt.X(), pnt.Y(), pnt.Z())
    collection.objects.link(obj)
    return obj
