"""Transition Surface Operators — Loft, Fill, Blend."""
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_Loft(GsdBaseOperator):
    bl_idname = "gsd.loft"; bl_label = "Loft"; gsd_command = "Loft"
    coupling: EnumProperty(name="Coupling", items=[("Ratio","Ratio",""),("Tangency","Tangency",""),("TangencyThenCurvature","Tang+Curv",""),("Vertices","Vertices","")], default="Ratio")
    relimitation: BoolProperty(name="Relimitation", default=True)
    canonical_detection: BoolProperty(name="Canonical Detect", default=False)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
        from ..core.ocp_bridge import bl_to_ocp_curve
        builder = BRepOffsetAPI_ThruSections(False, False, 0.001)
        for obj in inputs:
            wire = bl_to_ocp_curve(obj)
            builder.AddWire(wire)
        builder.Build()
        return builder.Shape()

class GSD_OT_Fill(GsdBaseOperator):
    bl_idname = "gsd.fill"; bl_label = "Fill"; gsd_command = "Fill"
    continuity: EnumProperty(name="Continuity", items=[("Point","Point",""),("Tangent","Tangent",""),("Curvature","Curvature","")], default="Tangent")
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepFill import BRepFill_Filling
        from ..core.ocp_bridge import bl_to_ocp_shape
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_EDGE
        from OCP.TopoDS import TopoDS
        from OCP.GeomAbs import GeomAbs_C0
        filler = BRepFill_Filling()
        for obj in inputs:
            shape = bl_to_ocp_shape(obj)
            explorer = TopExp_Explorer(shape, TopAbs_EDGE)
            while explorer.More():
                edge = TopoDS.Edge_s(explorer.Current())
                filler.Add(edge, GeomAbs_C0)
                explorer.Next()
        filler.Build()
        return filler.Face()

class GSD_OT_Blend(GsdBaseOperator):
    bl_idname = "gsd.blend"; bl_label = "Blend"; gsd_command = "Blend"
    continuity1: EnumProperty(name="Continuity 1", items=[("Point","Point",""),("Tangent","Tangent",""),("Curvature","Curvature","")], default="Tangent")
    continuity2: EnumProperty(name="Continuity 2", items=[("Point","Point",""),("Tangent","Tangent",""),("Curvature","Curvature","")], default="Tangent")
    tension1: FloatProperty(name="Tension 1", default=1.0, min=0.01)
    tension2: FloatProperty(name="Tension 2", default=1.0, min=0.01)
    trim_support1: BoolProperty(name="Trim Support 1", default=True)
    trim_support2: BoolProperty(name="Trim Support 2", default=True)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepFill import BRepFill_Filling
        from ..core.ocp_bridge import bl_to_ocp_shape
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_EDGE
        from OCP.TopoDS import TopoDS
        from OCP.GeomAbs import GeomAbs_C0
        filler = BRepFill_Filling()
        for obj in inputs:
            shape = bl_to_ocp_shape(obj)
            explorer = TopExp_Explorer(shape, TopAbs_EDGE)
            while explorer.More():
                edge = TopoDS.Edge_s(explorer.Current())
                filler.Add(edge, GeomAbs_C0)
                explorer.Next()
        filler.Build()
        return filler.Face()

_transition_classes = [GSD_OT_Loft, GSD_OT_Fill, GSD_OT_Blend]
def register():
    for cls in _transition_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_transition_classes): bpy.utils.unregister_class(cls)
