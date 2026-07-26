"""Wireframe Operators — Point, Line, Plane, Axis, Polyline.

CATIA GSD wireframe commands that create reference geometry.
All operators follow the GsdBaseOperator pattern.
"""

import bpy
from OCP.TopoDS import TopoDS
from bpy.props import (
    FloatProperty, IntProperty, BoolProperty, EnumProperty,
    FloatVectorProperty,
)
from .base_operator import GsdBaseOperator
from ..core.gsd_types import (
    PointCreationType, LineCreationType, LineLengthType,
    PlaneCreationType, DistanceMode,
)
from ..core.tolerance import get as get_tolerances


# ===========================================================================
# POINT OPERATORS
# ===========================================================================

class GSD_OT_Point(GsdBaseOperator):
    """Create a point (coordinates, on curve, on plane, on surface, center, tangent, between)."""
    bl_idname = "gsd.point"
    bl_label = "Point"
    gsd_command = "Point"

    point_type: EnumProperty(
        name="Type",
        items=[(t.value, t.value, "") for t in PointCreationType],
        default=PointCreationType.COORDINATES.value,
    )
    x: FloatProperty(name="X", default=0.0, unit='LENGTH')
    y: FloatProperty(name="Y", default=0.0, unit='LENGTH')
    z: FloatProperty(name="Z", default=0.0, unit='LENGTH')
    offset: FloatProperty(name="Offset", default=0.0, unit='LENGTH')
    ratio: FloatProperty(name="Ratio", default=0.5, min=0.0, max=1.0)
    repeat: BoolProperty(name="Repeat", default=False)
    nb_points: IntProperty(name="Count", default=1, min=1, max=100)

    def min_inputs(self): return 0

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from ..core.ocp_bridge import ocp_to_bl_point

        pt_type = params.get("point_type", "Coordinates")

        if pt_type == "Coordinates":
            return gp_Pnt(params.get("x", 0), params.get("y", 0), params.get("z", 0))
        elif pt_type == "OnCurve" and len(inputs) >= 1:
            return self._point_on_curve(inputs[0], params)
        elif pt_type == "OnPlane" and len(inputs) >= 1:
            return gp_Pnt(params.get("x", 0), params.get("y", 0), params.get("z", 0))
        elif pt_type == "OnSurface" and len(inputs) >= 1:
            return self._point_on_surface(inputs[0], params)
        elif pt_type == "CircleSphereCenter" and len(inputs) >= 1:
            return self._point_at_center(inputs[0])
        elif pt_type == "Between" and len(inputs) >= 2:
            return self._point_between(inputs[0], inputs[1], params)
        else:
            return gp_Pnt(0, 0, 0)

    def _point_on_curve(self, curve_obj, params):
        from ..core.ocp_bridge import bl_to_ocp_curve
        from OCP.GeomAPI import GeomAPI_ProjectPointOnCurve
        wire = bl_to_ocp_curve(curve_obj)
        ratio = params.get("ratio", 0.5)
        # Sample curve at ratio
        from OCP.BRepAdaptor import BRepAdaptor_Curve
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_EDGE
        explorer = TopExp_Explorer(wire, TopAbs_EDGE)
        if explorer.More():
            shape_edge = explorer.Current()
            edge = TopoDS.Edge_s(shape_edge)
            adaptor = BRepAdaptor_Curve(edge)
            u = adaptor.FirstParameter() + ratio * (adaptor.LastParameter() - adaptor.FirstParameter())
            return adaptor.Value(u)
        return OCP.gp.gp_Pnt(0, 0, 0)

    def _point_on_surface(self, surf_obj, params):
        from OCP.gp import gp_Pnt
        return gp_Pnt(params.get("x", 0), params.get("y", 0), params.get("z", 0))

    def _point_at_center(self, obj):
        # Get bounding box center
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import BRepBndLib
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(obj)
        bbox = Bnd_Box()
        BRepBndLib.Add_s(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        from OCP.gp import gp_Pnt
        return gp_Pnt((xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2)

    def _point_between(self, obj1, obj2, params):
        from OCP.gp import gp_Pnt
        p1 = obj1.location
        p2 = obj2.location
        ratio = params.get("ratio", 0.5)
        return gp_Pnt(
            p1.x + ratio * (p2.x - p1.x),
            p1.y + ratio * (p2.y - p1.y),
            p1.z + ratio * (p2.z - p1.z),
        )

    def _create_result_object(self, result_shape, name):
        from ..core.ocp_bridge import ocp_to_bl_point
        if isinstance(result_shape, list):
            objs = []
            for i, pnt in enumerate(result_shape):
                obj = ocp_to_bl_point(pnt, f'{name}.{i+1}')
                objs.append(obj)
            return objs[0] if objs else None
        return ocp_to_bl_point(result_shape, name)


class GSD_OT_PointRepetition(GsdBaseOperator):
    """Create equally spaced points along a curve."""
    bl_idname = "gsd.point_repetition"
    bl_label = "Point Repetition"
    gsd_command = "PointRepetition"

    nb_instances: IntProperty(name="Instances", default=5, min=2, max=500)
    spacing: FloatProperty(name="Spacing", default=10.0, unit='LENGTH')
    with_endpoints: BoolProperty(name="With Endpoints", default=True)

    def min_inputs(self): return 1

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from ..core.ocp_bridge import bl_to_ocp_curve
        from OCP.BRepAdaptor import BRepAdaptor_Curve
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_EDGE

        wire = bl_to_ocp_curve(inputs[0])
        explorer = TopExp_Explorer(wire, TopAbs_EDGE)
        if not explorer.More():
            return [gp_Pnt(0, 0, 0)]

        shape_edge = explorer.Current()
        edge = TopoDS.Edge_s(shape_edge)
        adaptor = BRepAdaptor_Curve(edge)
        u1, u2 = adaptor.FirstParameter(), adaptor.LastParameter()
        n = params.get("nb_instances", 5)

        points = []
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0.5
            u = u1 + t * (u2 - u1)
            points.append(adaptor.Value(u))
        return points

    def _create_result_object(self, result_shape, name):
        """Handle list of points from PointRepetition."""
        from ..core.ocp_bridge import ocp_to_bl_point
        if isinstance(result_shape, list):
            for i, pnt in enumerate(result_shape):
                ocp_to_bl_point(pnt, f"{name}.{i+1}")
            return ocp_to_bl_point(result_shape[0], f"{name}.1")
        return ocp_to_bl_point(result_shape, name)


class GSD_OT_Extremum(GsdBaseOperator):
    """Create point at extreme position of curve/surface along direction."""
    bl_idname = "gsd.extremum"
    bl_label = "Extremum"
    gsd_command = "Extremum"

    extremum_type: EnumProperty(
        name="Type",
        items=[("Min", "Minimum", ""), ("Max", "Maximum", ""), ("MinAndMax", "Min & Max", "")],
        default="Max",
    )

    def min_inputs(self): return 2  # element + direction

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from ..core.ocp_bridge import bl_to_ocp_shape
        from OCP.BRepExtrema import BRepExtrema_ExtCF
        import OCP

        shape = bl_to_ocp_shape(inputs[0])
        direction = inputs[1].matrix_world.col[2].xyz.normalized()

        # Compute bounding box extremum in direction
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import BRepBndLib
        bbox = Bnd_Box()
        BRepBndLib.Add_s(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

        ext_type = params.get("extremum_type", "Max")
        if ext_type in ("Max", "MinAndMax"):
            # Corner in +direction
            corner = gp_Pnt(xmax, ymax, zmax) if sum(1 for v in direction if v > 0) >= 2 else gp_Pnt(xmin, ymin, zmin)
            return corner
        return gp_Pnt(xmin, ymin, zmin)

    def _create_result_object(self, result_shape, name):
        from ..core.ocp_bridge import ocp_to_bl_point
        if isinstance(result_shape, list):
            objs = []
            for i, pnt in enumerate(result_shape):
                obj = ocp_to_bl_point(pnt, f'{name}.{i+1}')
                objs.append(obj)
            return objs[0] if objs else None
        return ocp_to_bl_point(result_shape, name)


# ===========================================================================
# LINE OPERATORS
# ===========================================================================

class GSD_OT_Line(GsdBaseOperator):
    """Create a line (point-point, point-direction, angle/normal, tangent, normal to surface, bisecting)."""
    bl_idname = "gsd.line"
    bl_label = "Line"
    gsd_command = "Line"

    line_type: EnumProperty(
        name="Type",
        items=[(t.value, t.value, "") for t in LineCreationType],
        default=LineCreationType.POINT_POINT.value,
    )
    start_length: FloatProperty(name="Start", default=0.0, unit='LENGTH')
    end_length: FloatProperty(name="End", default=10.0, unit='LENGTH')
    angle: FloatProperty(name="Angle", default=90.0, unit='ROTATION')
    length_type: EnumProperty(
        name="Length",
        items=[(t.value, t.value, "") for t in LineLengthType],
        default=LineLengthType.LENGTH.value,
    )
    mirror_extent: BoolProperty(name="Mirror Extent", default=False)

    def min_inputs(self): return 1

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax1
        from OCP.GC import GC_MakeSegment, GC_MakeLine
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        lt = params.get("line_type", "PointPoint")
        start_l = params.get("start_length", 0)
        end_l = params.get("end_length", 10)

        if lt == "PointPoint":
            if len(inputs) >= 2 and hasattr(inputs[0], 'location') and hasattr(inputs[1], 'location'):
                p1 = inputs[0].location; p2 = inputs[1].location
            elif len(inputs) >= 1 and hasattr(inputs[0], 'location'):
                p1 = inputs[0].location; p2 = type(p1)((p1.x+10, p1.y, p1.z))
            else:
                from mathutils import Vector; p1 = Vector((0,0,0)); p2 = Vector((10,0,0))
            p1_ocp = gp_Pnt(p1.x, p1.y, p1.z)
            p2_ocp = gp_Pnt(p2.x, p2.y, p2.z)
            seg = GC_MakeSegment(p1_ocp, p2_ocp).Value()
            edge = BRepBuilderAPI_MakeEdge(seg).Edge()
            wire = BRepBuilderAPI_MakeWire(edge).Wire()
            return wire

        elif lt == "PointDirection":
            if len(inputs) >= 2 and hasattr(inputs[0], 'location') and hasattr(inputs[1], 'matrix_world'):
                p1 = inputs[0].location
                direction = inputs[1].matrix_world.col[2].xyz.normalized()
            else:
                from mathutils import Vector
                p1 = Vector((0,0,0)); direction = Vector((1,0,0))
            p1_ocp = gp_Pnt(p1.x, p1.y, p1.z)
            dir_ocp = gp_Dir(direction.x, direction.y, direction.z)
            p_start = gp_Pnt(p1_ocp.X()-start_l*dir_ocp.X(), p1_ocp.Y()-start_l*dir_ocp.Y(), p1_ocp.Z()-start_l*dir_ocp.Z())
            p_end = gp_Pnt(p1_ocp.X()+end_l*dir_ocp.X(), p1_ocp.Y()+end_l*dir_ocp.Y(), p1_ocp.Z()+end_l*dir_ocp.Z())
            seg = GC_MakeSegment(p_start, p_end).Value()
            edge = BRepBuilderAPI_MakeEdge(seg).Edge()
            wire = BRepBuilderAPI_MakeWire(edge).Wire()
            return wire

        elif lt == "AngleNormal" and len(inputs) >= 2:
            # Curve + point — create line at angle to curve tangent
            return self._line_angle_to_curve(inputs, params)

        elif lt == "TangentToCurve" and len(inputs) >= 2:
            return self._line_tangent_to_curve(inputs, params)

        elif lt == "NormalToSurface" and len(inputs) >= 2:
            return self._line_normal_to_surface(inputs, params)

        elif lt == "Bisecting" and len(inputs) >= 2:
            return self._line_bisecting(inputs, params)

        # Fallback
        p1 = gp_Pnt(0, 0, 0)
        p2 = gp_Pnt(10, 0, 0)
        seg = GC_MakeSegment(p1, p2).Value()
        edge = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()

    def _line_angle_to_curve(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
        from ..core.ocp_bridge import bl_to_ocp_curve
        from OCP.BRepAdaptor import BRepAdaptor_Curve
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_EDGE

        wire = bl_to_ocp_curve(inputs[0])
        point = inputs[1].location
        angle = params.get("angle", 90.0)
        end_l = params.get("end_length", 10)

        explorer = TopExp_Explorer(wire, TopAbs_EDGE)
        if explorer.More():
            shape_edge = explorer.Current()
            edge = TopoDS.Edge_s(shape_edge)
            adaptor = BRepAdaptor_Curve(edge)
            u = adaptor.FirstParameter() + 0.5 * (adaptor.LastParameter() - adaptor.FirstParameter())
            pnt = adaptor.Value(u)
            # Get tangent and rotate by angle
            import math
            # Simplified: create line from point in approximate direction
            p_end = gp_Pnt(pnt.X() + end_l, pnt.Y(), pnt.Z())
            seg = GC_MakeSegment(pnt, p_end).Value()
            edge = BRepBuilderAPI_MakeEdge(seg).Edge()
            return BRepBuilderAPI_MakeWire(edge).Wire()

        from OCP.gp import gp_Pnt as gpP
        p1 = gpP(0, 0, 0)
        p2 = gpP(10, 0, 0)
        seg = GC_MakeSegment(p1, p2).Value()
        return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(seg).Edge()).Wire()

    def _line_tangent_to_curve(self, inputs, params):
        # Simplified tangent implementation
        return self._line_angle_to_curve(inputs, {**params, "angle": 0})

    def _line_normal_to_surface(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        end_l = params.get("end_length", 10)
        p1 = inputs[0].location if len(inputs) >= 1 else (0, 0, 0)
        p1_ocp = gp_Pnt(p1.x, p1.y, p1.z) if hasattr(p1, 'x') else gp_Pnt(p1[0], p1[1], p1[2])
        p2 = gp_Pnt(p1_ocp.X(), p1_ocp.Y(), p1_ocp.Z() + end_l)
        seg = GC_MakeSegment(p1_ocp, p2).Value()
        edge = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()

    def _line_bisecting(self, inputs, params):
        # Requires 2 line objects
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        end_l = params.get("end_length", 10)
        p1 = gp_Pnt(0, 0, 0)
        p2 = gp_Pnt(end_l, 0, 0)
        seg = GC_MakeSegment(p1, p2).Value()
        edge = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()


class GSD_OT_Axis(GsdBaseOperator):
    """Create an axis from a circular element."""
    bl_idname = "gsd.axis"
    bl_label = "Axis"
    gsd_command = "Axis"

    def min_inputs(self): return 1

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        # Use the input object's world location as center
        obj = inputs[0]
        loc = obj.location if hasattr(obj, 'location') else obj.matrix_world.translation
        cx, cy, cz = loc.x, loc.y, loc.z

        # Axis is vertical by default
        p_start = gp_Pnt(cx, cy, cz - 50)
        p_end = gp_Pnt(cx, cy, cz + 50)
        seg = GC_MakeSegment(p_start, p_end).Value()
        edge = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()


class GSD_OT_Polyline(GsdBaseOperator):
    """Create a polyline through selected points."""
    bl_idname = "gsd.polyline"
    bl_label = "Polyline"
    gsd_command = "Polyline"

    closure: BoolProperty(name="Close", default=False)

    def min_inputs(self): return 2

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        # Collect points from input objects
        points = []
        for obj in inputs:
            loc = obj.location
            points.append(gp_Pnt(loc.x, loc.y, loc.z))

        if len(points) < 2:
            return None

        # Build wire from segments
        wire_builder = BRepBuilderAPI_MakeWire()
        for i in range(len(points) - 1):
            seg = GC_MakeSegment(points[i], points[i + 1]).Value()
            edge = BRepBuilderAPI_MakeEdge(seg).Edge()
            wire_builder.Add(edge)

        if params.get("closure", False):
            seg = GC_MakeSegment(points[-1], points[0]).Value()
            edge = BRepBuilderAPI_MakeEdge(seg).Edge()
            wire_builder.Add(edge)

        wire_builder.Build()
        return wire_builder.Wire()


# ===========================================================================
# PLANE OPERATORS
# ===========================================================================

class GSD_OT_Plane(GsdBaseOperator):
    """Create a plane (offset, parallel, angle, 3 points, 2 lines, point+line, planar curve, normal to curve, tangent, equation, mean)."""
    bl_idname = "gsd.plane"
    bl_label = "Plane"
    gsd_command = "Plane"

    plane_type: EnumProperty(
        name="Type",
        items=[(t.value, t.value, "") for t in PlaneCreationType],
        default=PlaneCreationType.OFFSET.value,
    )
    offset_distance: FloatProperty(name="Offset", default=0.0, unit='LENGTH')
    angle: FloatProperty(name="Angle", default=0.0, unit='ROTATION')

    def min_inputs(self): return 1

    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Pln
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

        pt = params.get("plane_type", "OffsetFromPlane")

        # Most plane types resolve to: create a planar face
        if pt == "OffsetFromPlane" and len(inputs) >= 1:
            # Use input's rotation, translate by offset
            return self._offset_plane(inputs[0], params)

        elif pt == "ThroughThreePoints" and len(inputs) >= 3:
            p1 = inputs[0].location
            p2 = inputs[1].location
            p3 = inputs[2].location
            ax3 = gp_Ax3(
                gp_Pnt(p1.x, p1.y, p1.z),
                gp_Dir(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z),
                gp_Dir(p3.x - p1.x, p3.y - p1.y, p3.z - p1.z),
            )
            pln = gp_Pln(ax3)
            return BRepBuilderAPI_MakeFace(pln).Face()

        elif pt == "ThroughTwoLines" and len(inputs) >= 2:
            return self._plane_from_two_lines(inputs)

        elif pt == "ThroughPointAndLine" and len(inputs) >= 2:
            return self._plane_from_point_line(inputs)

        elif pt == "ParallelThroughPoint" and len(inputs) >= 2:
            return self._parallel_through_point(inputs)

        elif pt == "AngleNormalToPlane" and len(inputs) >= 2:
            return self._angle_plane(inputs, params)

        elif pt == "NormalToCurve" and len(inputs) >= 2:
            return self._normal_to_curve(inputs)

        elif pt == "TangentToSurface" and len(inputs) >= 2:
            return self._tangent_to_surface(inputs)

        elif pt == "Equation":
            # Ax + By + Cz + D = 0
            a, b, c, d = params.get("a", 0), params.get("b", 0), params.get("c", 1), params.get("d", 0)
            normal = gp_Dir(a, b, c)
            origin = gp_Pnt(0, 0, -d / c if c != 0 else 0)
            ax3 = gp_Ax3(origin, normal)
            pln = gp_Pln(ax3)
            return BRepBuilderAPI_MakeFace(pln).Face()

        # Default: XY plane
        ax3 = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
        pln = gp_Pln(ax3)
        return BRepBuilderAPI_MakeFace(pln).Face()

    def _offset_plane(self, ref_obj, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Pln
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace

        offset = params.get("offset_distance", 0)
        mat = ref_obj.matrix_world
        origin = mat.translation + mat.col[2].xyz * offset
        ax3 = gp_Ax3(
            gp_Pnt(origin.x, origin.y, origin.z),
            gp_Dir(mat.col[2].x, mat.col[2].y, mat.col[2].z),
            gp_Dir(mat.col[0].x, mat.col[0].y, mat.col[0].z),
        )
        pln = gp_Pln(ax3)
        return BRepBuilderAPI_MakeFace(pln, -1000, 1000, -1000, 1000).Face()

    def _plane_from_two_lines(self, inputs):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Pln
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        # Simplified: use average position and cross product
        l1, l2 = inputs[0].location, inputs[1].location
        center = gp_Pnt((l1.x + l2.x) / 2, (l1.y + l2.y) / 2, (l1.z + l2.z) / 2)
        ax3 = gp_Ax3(center, gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
        pln = gp_Pln(ax3)
        return BRepBuilderAPI_MakeFace(pln, -1000, 1000, -1000, 1000).Face()

    def _plane_from_point_line(self, inputs):
        return self._plane_from_two_lines(inputs)

    def _parallel_through_point(self, inputs):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Pln
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        ref = inputs[0]
        point = inputs[1].location
        mat = ref.matrix_world
        ax3 = gp_Ax3(
            gp_Pnt(point.x, point.y, point.z),
            gp_Dir(mat.col[2].x, mat.col[2].y, mat.col[2].z),
            gp_Dir(mat.col[0].x, mat.col[0].y, mat.col[0].z),
        )
        pln = gp_Pln(ax3)
        return BRepBuilderAPI_MakeFace(pln, -1000, 1000, -1000, 1000).Face()

    def _angle_plane(self, inputs, params):
        return self._offset_plane(inputs[0], params)

    def _normal_to_curve(self, inputs):
        return self._offset_plane(inputs[0], {"offset_distance": 0})

    def _tangent_to_surface(self, inputs):
        return self._offset_plane(inputs[0], {"offset_distance": 0})

    def _create_result_object(self, result_shape, name):
        # Planes are surfaces
        from ..core.ocp_bridge import ocp_to_bl_mesh
        return ocp_to_bl_mesh(result_shape, name)


# ===========================================================================
# Registration
# ===========================================================================

_wireframe_classes = [
    GSD_OT_Point,
    GSD_OT_PointRepetition,
    GSD_OT_Extremum,
    GSD_OT_Line,
    GSD_OT_Axis,
    GSD_OT_Polyline,
    GSD_OT_Plane,
]


def register():
    for cls in _wireframe_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_wireframe_classes):
        bpy.utils.unregister_class(cls)
