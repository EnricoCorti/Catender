"""Transform Operators — Translate, Rotate, Symmetry, Scaling, Affinity."""
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, FloatVectorProperty, EnumProperty
from .base_operator import GsdBaseOperator
from ..core.gsd_types import RepeatMode

class GSD_OT_Translate(GsdBaseOperator):
    bl_idname = "gsd.translate"; bl_label = "Translate"; gsd_command = "Translate"
    distance: FloatProperty(name="Distance", default=10.0, unit='LENGTH')
    repeat: BoolProperty(name="Repeat", default=False)
    repeat_count: IntProperty(name="Count", default=1, min=1, max=100)
    def min_inputs(self): return 2  # element + direction
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Vec, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        direction = inputs[1].matrix_world.col[2].xyz
        d = params.get("distance", 10)
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(direction.x * d, direction.y * d, direction.z * d))
        return BRepBuilderAPI_Transform(shape, trsf, True).Shape()

class GSD_OT_Rotate(GsdBaseOperator):
    bl_idname = "gsd.rotate"; bl_label = "Rotate"; gsd_command = "Rotate"
    angle: FloatProperty(name="Angle", default=90.0, unit='ROTATION')
    repeat: BoolProperty(name="Repeat", default=False)
    repeat_count: IntProperty(name="Count", default=1, min=1, max=100)
    def min_inputs(self): return 2  # element + axis
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax1, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from ..core.ocp_bridge import bl_to_ocp_shape
        import math
        shape = bl_to_ocp_shape(inputs[0])
        axis_loc = inputs[1].location; axis_dir = inputs[1].matrix_world.col[2].xyz
        ax1 = gp_Ax1(gp_Pnt(axis_loc.x, axis_loc.y, axis_loc.z), gp_Dir(axis_dir.x, axis_dir.y, axis_dir.z))
        trsf = gp_Trsf()
        trsf.SetRotation(ax1, params.get("angle", 90) * math.pi / 180)
        return BRepBuilderAPI_Transform(shape, trsf, True).Shape()

class GSD_OT_Symmetry(GsdBaseOperator):
    bl_idname = "gsd.symmetry"; bl_label = "Symmetry"; gsd_command = "Symmetry"
    def min_inputs(self): return 2  # element + reference (plane)
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        ref_loc = inputs[1].location; ref_dir = inputs[1].matrix_world.col[2].xyz
        ax2 = gp_Ax2(gp_Pnt(ref_loc.x, ref_loc.y, ref_loc.z), gp_Dir(ref_dir.x, ref_dir.y, ref_dir.z))
        trsf = gp_Trsf()
        trsf.SetMirror(ax2)
        return BRepBuilderAPI_Transform(shape, trsf, True).Shape()

class GSD_OT_Scaling(GsdBaseOperator):
    bl_idname = "gsd.scaling"; bl_label = "Scaling"; gsd_command = "Scaling"
    factor: FloatProperty(name="Factor", default=1.0, min=0.001)
    def min_inputs(self): return 2  # element + reference point
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        ref = inputs[1].location
        trsf = gp_Trsf()
        trsf.SetScale(gp_Pnt(ref.x, ref.y, ref.z), params.get("factor", 1.0))
        return BRepBuilderAPI_Transform(shape, trsf, True).Shape()

class GSD_OT_Affinity(GsdBaseOperator):
    bl_idname = "gsd.affinity"; bl_label = "Affinity"; gsd_command = "Affinity"
    x_factor: FloatProperty(name="X Factor", default=1.0, min=0.001)
    y_factor: FloatProperty(name="Y Factor", default=1.0, min=0.001)
    z_factor: FloatProperty(name="Z Factor", default=1.0, min=0.001)
    def min_inputs(self): return 2  # element + axis system
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
        from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        mat = gp_Mat(params.get("x_factor", 1), 0, 0, 0, params.get("y_factor", 1), 0, 0, 0, params.get("z_factor", 1))
        gtrsf = gp_GTrsf(mat, gp_XYZ(0, 0, 0))
        return BRepBuilderAPI_GTransform(shape, gtrsf, True).Shape()

_transform_classes = [GSD_OT_Translate, GSD_OT_Rotate, GSD_OT_Symmetry, GSD_OT_Scaling, GSD_OT_Affinity]
def register():
    for cls in _transform_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_transform_classes): bpy.utils.unregister_class(cls)
