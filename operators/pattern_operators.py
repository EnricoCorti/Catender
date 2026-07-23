"""Pattern Operators — Rectangular, Circular, User Pattern, Explode."""
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty
from .base_operator import GsdBaseOperator

class GSD_OT_RectangularPattern(GsdBaseOperator):
    bl_idname = "gsd.rectangular_pattern"; bl_label = "Rect Pattern"; gsd_command = "RectPattern"
    count1: IntProperty(name="Count Dir 1", default=3, min=1, max=100)
    spacing1: FloatProperty(name="Spacing Dir 1", default=10.0, unit='LENGTH')
    count2: IntProperty(name="Count Dir 2", default=1, min=1, max=100)
    spacing2: FloatProperty(name="Spacing Dir 2", default=10.0, unit='LENGTH')
    def min_inputs(self): return 3  # element + direction1 + direction2
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Vec, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        d1 = inputs[1].matrix_world.col[2].xyz; d2 = inputs[2].matrix_world.col[2].xyz
        c1 = params.get("count1", 3); s1 = params.get("spacing1", 10)
        c2 = params.get("count2", 1); s2 = params.get("spacing2", 10)

        result = shape
        for i in range(c1):
            for j in range(c2):
                if i == 0 and j == 0: continue
                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(d1.x * s1 * i + d2.x * s2 * j, d1.y * s1 * i + d2.y * s2 * j, d1.z * s1 * i + d2.z * s2 * j))
                instance = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
                fuse = BRepAlgoAPI_Fuse(result, instance); fuse.Build()
                result = fuse.Shape()
        return result

class GSD_OT_CircularPattern(GsdBaseOperator):
    bl_idname = "gsd.circular_pattern"; bl_label = "Circ Pattern"; gsd_command = "CircPattern"
    instance_count: IntProperty(name="Instances", default=6, min=2, max=100)
    angular_spacing: FloatProperty(name="Angular Spacing", default=60.0, unit='ROTATION')
    def min_inputs(self): return 2  # element + axis
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax1, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
        from ..core.ocp_bridge import bl_to_ocp_shape
        import math
        shape = bl_to_ocp_shape(inputs[0])
        axis_loc = inputs[1].location; axis_dir = inputs[1].matrix_world.col[2].xyz
        ax1 = gp_Ax1(gp_Pnt(axis_loc.x, axis_loc.y, axis_loc.z), gp_Dir(axis_dir.x, axis_dir.y, axis_dir.z))
        n = params.get("instance_count", 6); spacing = params.get("angular_spacing", 60) * math.pi / 180

        result = shape
        for i in range(1, n):
            trsf = gp_Trsf()
            trsf.SetRotation(ax1, spacing * i)
            instance = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
            fuse = BRepAlgoAPI_Fuse(result, instance); fuse.Build()
            result = fuse.Shape()
        return result

class GSD_OT_UserPattern(GsdBaseOperator):
    bl_idname = "gsd.user_pattern"; bl_label = "User Pattern"; gsd_command = "UserPattern"
    def min_inputs(self): return 2  # element + position points
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Vec, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        result = shape
        for obj in inputs[1:]:
            pos = obj.location
            trsf = gp_Trsf()
            trsf.SetTranslation(gp_Vec(pos.x, pos.y, pos.z))
            instance = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
            fuse = BRepAlgoAPI_Fuse(result, instance); fuse.Build()
            result = fuse.Shape()
        return result

class GSD_OT_Explode(GsdBaseOperator):
    bl_idname = "gsd.explode"; bl_label = "Explode"; gsd_command = "Explode"
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

_pattern_classes = [GSD_OT_RectangularPattern, GSD_OT_CircularPattern, GSD_OT_UserPattern, GSD_OT_Explode]
def register():
    for cls in _pattern_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_pattern_classes): bpy.utils.unregister_class(cls)
