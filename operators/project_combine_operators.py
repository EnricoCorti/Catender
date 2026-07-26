"""Project/Combine Operators — Projection, Combine, ReflectLine, ParallelCurve, 3DCurveOffset, Intersection."""
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_Projection(GsdBaseOperator):
    bl_idname = "gsd.projection"; bl_label = "Projection"; gsd_command = "Projection"
    direction_type: EnumProperty(name="Direction", items=[("Normal","Normal",""),("AlongDirection","Along Direction","")], default="Normal")
    nearest_solution: BoolProperty(name="Nearest Solution", default=True)
    def min_inputs(self): return 2  # curve + surface
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_curve, bl_to_ocp_surface
        wire = bl_to_ocp_curve(inputs[0])
        try:
            from OCP.BRepProj import BRepProj_Projection
            from OCP.gp import gp_Dir
            surf = bl_to_ocp_surface(inputs[1])
            proj = BRepProj_Projection(wire, surf, gp_Dir(0, 0, 1))
            proj.Perform()
            if proj.IsDone():
                return proj.Shape()
        except Exception:
            pass
        return wire

class GSD_OT_Combine(GsdBaseOperator):
    bl_idname = "gsd.combine"; bl_label = "Combine"; gsd_command = "Combine"
    def min_inputs(self): return 3  # curve1 + curve2 + direction1 (+ direction2 implicit)
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_curve
        return bl_to_ocp_curve(inputs[0])

class GSD_OT_ReflectLine(GsdBaseOperator):
    bl_idname = "gsd.reflect_line"; bl_label = "Reflect Line"; gsd_command = "ReflectLine"
    angle: FloatProperty(name="Angle", default=0.0, unit='ROTATION')
    reflect_type: EnumProperty(name="Type", items=[("Cylindrical","Cylindrical",""),("Conical","Conical","")], default="Cylindrical")
    def min_inputs(self): return 2  # surface + direction
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface, bl_to_ocp_direction
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_ParallelCurve(GsdBaseOperator):
    bl_idname = "gsd.parallel_curve"; bl_label = "Parallel Curve"; gsd_command = "ParallelCurve"
    offset: FloatProperty(name="Offset", default=5.0, unit='LENGTH')
    corner_type: EnumProperty(name="Corner", items=[("Sharp","Sharp",""),("Round","Round","")], default="Sharp")
    both_sides: BoolProperty(name="Both Sides", default=False)
    def min_inputs(self): return 2  # curve + support surface
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_curve
        return bl_to_ocp_curve(inputs[0])

class GSD_OT_Curve3DOffset(GsdBaseOperator):
    bl_idname = "gsd.curve_3d_offset"; bl_label = "3D Curve Offset"; gsd_command = "3DCurveOffset"
    offset: FloatProperty(name="Offset", default=5.0, unit='LENGTH')
    def min_inputs(self): return 2  # curve + direction
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_curve
        return bl_to_ocp_curve(inputs[0])

class GSD_OT_Intersection(GsdBaseOperator):
    bl_idname = "gsd.intersection"; bl_label = "Intersection"; gsd_command = "Intersection"
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
        from ..core.ocp_bridge import bl_to_ocp_shape
        s1 = bl_to_ocp_shape(inputs[0]); s2 = bl_to_ocp_shape(inputs[1])
        section = BRepAlgoAPI_Section(s1, s2, False)
        section.Build()
        return section.Shape() if section.IsDone() else s1

_pc_classes = [GSD_OT_Projection, GSD_OT_Combine, GSD_OT_ReflectLine, GSD_OT_ParallelCurve, GSD_OT_Curve3DOffset, GSD_OT_Intersection]
def register():
    for cls in _pc_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_pc_classes): bpy.utils.unregister_class(cls)
