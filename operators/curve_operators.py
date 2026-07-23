"""Curve Operators — Circle, Corner, Connect, Conic, Spline, Helix, Spiral, Spine."""
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator
from ..core.gsd_types import (
    CircleCreationType, SplineType, SpiralType, SpiralOrientation,
    HelixOrientation,
)

class GSD_OT_Circle(GsdBaseOperator):
    bl_idname = "gsd.circle"; bl_label = "Circle"; gsd_command = "Circle"
    circle_type: EnumProperty(name="Type", items=[(t.value, t.value, "") for t in CircleCreationType], default=CircleCreationType.CENTER_RADIUS.value)
    radius: FloatProperty(name="Radius", default=5.0, unit='LENGTH')
    start_angle: FloatProperty(name="Start Angle", default=0.0, unit='ROTATION')
    end_angle: FloatProperty(name="End Angle", default=360.0, unit='ROTATION')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Circ
        from OCP.GC import GC_MakeArcOfCircle
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
        ct = params.get("circle_type", "CenterRadius")
        r = params.get("radius", 5)
        if ct in ("CenterRadius", "CenterPoint", "ThreePoints", "CenterAxis"):
            center = inputs[0].location if len(inputs) >= 1 else (0, 0, 0)
            ax2 = gp_Ax2(gp_Pnt(center.x, center.y, center.z), gp_Dir(0, 0, 1))
            circ = gp_Circ(ax2, r)
            sa = params.get("start_angle", 0) * 3.14159 / 180
            ea = params.get("end_angle", 360) * 3.14159 / 180
            arc = GC_MakeArcOfCircle(circ, sa, ea, True).Value()
            edge = BRepBuilderAPI_MakeEdge(arc).Edge()
            return BRepBuilderAPI_MakeWire(edge).Wire()
        # Fallback
        ax2 = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
        circ = gp_Circ(ax2, r)
        arc = GC_MakeArcOfCircle(circ, 0, 6.283, True).Value()
        edge = BRepBuilderAPI_MakeEdge(arc).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()

class GSD_OT_Corner(GsdBaseOperator):
    bl_idname = "gsd.corner"; bl_label = "Corner"; gsd_command = "Corner"
    radius: FloatProperty(name="Radius", default=5.0, unit='LENGTH')
    trim_curve1: BoolProperty(name="Trim First", default=True)
    trim_curve2: BoolProperty(name="Trim Second", default=True)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
        p1 = inputs[0].location; p2 = inputs[1].location
        mid = gp_Pnt((p1.x + p2.x)/2, (p1.y + p2.y)/2, (p1.z + p2.z)/2)
        seg = GC_MakeSegment(gp_Pnt(p1.x, p1.y, p1.z), mid).Value()
        e = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(e).Wire()

class GSD_OT_ConnectCurve(GsdBaseOperator):
    bl_idname = "gsd.connect_curve"; bl_label = "Connect Curve"; gsd_command = "ConnectCurve"
    continuity1: EnumProperty(name="Continuity 1", items=[("Point","Point",""),("Tangent","Tangent",""),("Curvature","Curvature","")], default="Tangent")
    continuity2: EnumProperty(name="Continuity 2", items=[("Point","Point",""),("Tangent","Tangent",""),("Curvature","Curvature","")], default="Tangent")
    tension1: FloatProperty(name="Tension 1", default=1.0, min=0.01)
    tension2: FloatProperty(name="Tension 2", default=1.0, min=0.01)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
        p1 = inputs[0].location; p2 = inputs[1].location
        seg = GC_MakeSegment(gp_Pnt(p1.x, p1.y, p1.z), gp_Pnt(p2.x, p2.y, p2.z)).Value()
        e = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(e).Wire()

class GSD_OT_Conic(GsdBaseOperator):
    bl_idname = "gsd.conic"; bl_label = "Conic"; gsd_command = "Conic"
    conic_param: FloatProperty(name="Parameter", default=0.5, min=0.01, max=0.99, description="0.5=Parabola, <0.5=Ellipse, >0.5=Hyperbola")
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
        p1 = inputs[0].location; p2 = inputs[1].location
        # Simplified conic as straight segment (full conic needs Geom2d)
        seg = GC_MakeSegment(gp_Pnt(p1.x, p1.y, p1.z), gp_Pnt(p2.x, p2.y, p2.z)).Value()
        e = BRepBuilderAPI_MakeEdge(seg).Edge()
        return BRepBuilderAPI_MakeWire(e).Wire()

class GSD_OT_Spline(GsdBaseOperator):
    bl_idname = "gsd.spline"; bl_label = "Spline"; gsd_command = "Spline"
    spline_type: EnumProperty(name="Type", items=[(t.value, t.value, "") for t in SplineType], default=SplineType.THROUGH_POINTS.value)
    closure: BoolProperty(name="Close", default=False)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.TColgp import TColgp_Array1OfPnt
        from OCP.GeomAPI import GeomAPI_PointsToBSpline
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        n = len(inputs); poles = TColgp_Array1OfPnt(1, n)
        for i, obj in enumerate(inputs):
            loc = obj.location; poles.SetValue(i + 1, gp_Pnt(loc.x, loc.y, loc.z))

        spline = GeomAPI_PointsToBSpline(poles, 3, 1e-10, True).Curve()
        edge = BRepBuilderAPI_MakeEdge(spline).Edge()
        return BRepBuilderAPI_MakeWire(edge).Wire()

class GSD_OT_Helix(GsdBaseOperator):
    bl_idname = "gsd.helix"; bl_label = "Helix"; gsd_command = "Helix"
    pitch: FloatProperty(name="Pitch", default=10.0, unit='LENGTH')
    height: FloatProperty(name="Height", default=50.0, unit='LENGTH')
    orientation: EnumProperty(name="Orientation", items=[(t.value, t.value, "") for t in HelixOrientation], default=HelixOrientation.COUNTER_CLOCKWISE.value)
    taper_angle: FloatProperty(name="Taper Angle", default=0.0, unit='ROTATION')
    starting_angle: FloatProperty(name="Start Angle", default=0.0, unit='ROTATION')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        import math
        from OCP.gp import gp_Pnt, gp_Dir
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        center = inputs[0].location
        # Use second input as start point, or default to X+5 offset
        if len(inputs) >= 2:
            start = inputs[1].location
        else:
            start = type(center)((center.x + 5, center.y, center.z))
        pitch = params.get("pitch", 10); h = params.get("height", 50)
        n_turns = h / pitch; n_points = max(int(n_turns * 30), 10)
        r = math.sqrt((start.x - center.x)**2 + (start.y - center.y)**2)

        points = []; prev_edge = None
        for i in range(n_points + 1):
            t = i / n_points; angle = 2 * math.pi * n_turns * t + params.get("starting_angle", 0)
            z = center.z + t * h; rr = r * (1 + params.get("taper_angle", 0) * t / 90)
            px = center.x + rr * math.cos(angle); py = center.y + rr * math.sin(angle)
            points.append(gp_Pnt(px, py, z))

        wire_builder = BRepBuilderAPI_MakeWire()
        for i in range(len(points) - 1):
            seg = GC_MakeSegment(points[i], points[i + 1]).Value()
            wire_builder.Add(BRepBuilderAPI_MakeEdge(seg).Edge())
        wire_builder.Build()
        return wire_builder.Wire()

class GSD_OT_Spiral(GsdBaseOperator):
    bl_idname = "gsd.spiral"; bl_label = "Spiral"; gsd_command = "Spiral"
    spiral_type: EnumProperty(name="Type", items=[(t.value, t.value, "") for t in SpiralType], default=SpiralType.ANGLE_RADIUS.value)
    start_radius: FloatProperty(name="Start Radius", default=1.0, unit='LENGTH')
    end_radius: FloatProperty(name="End Radius", default=20.0, unit='LENGTH')
    end_angle: FloatProperty(name="End Angle", default=3600.0, unit='ROTATION')
    nb_revolutions: IntProperty(name="Revolutions", default=5, min=1, max=100)
    orientation: EnumProperty(name="Orientation", items=[(t.value, t.value, "") for t in SpiralOrientation], default=SpiralOrientation.COUNTER_CLOCKWISE.value)
    def min_inputs(self): return 1  # center
    def compute_ocp_result(self, inputs, params):
        import math
        from OCP.gp import gp_Pnt, gp_Dir
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire

        center = inputs[0].location; n_rev = params.get("nb_revolutions", 5)
        r_start = params.get("start_radius", 1); r_end = params.get("end_radius", 20)
        n_points = n_rev * 20; points = []

        for i in range(n_points + 1):
            t = i / n_points; angle = 2 * math.pi * n_rev * t
            r = r_start + t * (r_end - r_start)
            px = center.x + r * math.cos(angle); py = center.y + r * math.sin(angle)
            points.append(gp_Pnt(px, py, center.z))

        wire_builder = BRepBuilderAPI_MakeWire()
        for i in range(len(points) - 1):
            seg = GC_MakeSegment(points[i], points[i + 1]).Value()
            wire_builder.Add(BRepBuilderAPI_MakeEdge(seg).Edge())
        wire_builder.Build()
        return wire_builder.Wire()

class GSD_OT_Spine(GsdBaseOperator):
    bl_idname = "gsd.spine"; bl_label = "Spine"; gsd_command = "Spine"
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        from OCP.GC import GC_MakeSegment
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
        locs = [obj.location for obj in inputs]
        pts = [gp_Pnt(l.x, l.y, l.z) for l in locs]
        wire_builder = BRepBuilderAPI_MakeWire()
        for i in range(len(pts) - 1):
            seg = GC_MakeSegment(pts[i], pts[i+1]).Value()
            wire_builder.Add(BRepBuilderAPI_MakeEdge(seg).Edge())
        wire_builder.Build()
        return wire_builder.Wire()

_curve_classes = [GSD_OT_Circle, GSD_OT_Corner, GSD_OT_ConnectCurve, GSD_OT_Conic, GSD_OT_Spline, GSD_OT_Helix, GSD_OT_Spiral, GSD_OT_Spine]

def register():
    for cls in _curve_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_curve_classes): bpy.utils.unregister_class(cls)
