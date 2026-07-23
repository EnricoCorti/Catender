"""Join/Trim Operators — Join, Healing, Untrim, Disassemble, Split, Trim, Sew."""
import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_Join(GsdBaseOperator):
    bl_idname = "gsd.join"; bl_label = "Join"; gsd_command = "Join"
    merging_distance: FloatProperty(name="Merging Distance", default=0.001, precision=6)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
        from ..core.ocp_bridge import bl_to_ocp_shape
        result = bl_to_ocp_shape(inputs[0])
        for obj in inputs[1:]:
            shape = bl_to_ocp_shape(obj)
            fuse = BRepAlgoAPI_Fuse(result, shape)
            fuse.Build()
            result = fuse.Shape()
        return result

class GSD_OT_Healing(GsdBaseOperator):
    bl_idname = "gsd.healing"; bl_label = "Healing"; gsd_command = "Healing"
    merging_distance: FloatProperty(name="Merging Distance", default=0.001, precision=6)
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.ShapeFix import ShapeFix_Shape
        from ..core.ocp_bridge import bl_to_ocp_shape
        shape = bl_to_ocp_shape(inputs[0])
        fixer = ShapeFix_Shape(shape)
        fixer.Perform()
        return fixer.Shape()

class GSD_OT_Untrim(GsdBaseOperator):
    bl_idname = "gsd.untrim"; bl_label = "Untrim"; gsd_command = "Untrim"
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_Disassemble(GsdBaseOperator):
    bl_idname = "gsd.disassemble"; bl_label = "Disassemble"; gsd_command = "Disassemble"
    mode: EnumProperty(name="Mode", items=[("Domains","Domains",""),("Cells","Cells",""),("AllCells","All Cells","")], default="Domains")
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

class GSD_OT_Split(GsdBaseOperator):
    bl_idname = "gsd.split"; bl_label = "Split"; gsd_command = "Split"
    keep_both_sides: BoolProperty(name="Keep Both Sides", default=False)
    def min_inputs(self): return 2  # element + cutting element
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
        from ..core.ocp_bridge import bl_to_ocp_shape
        splitter = BRepAlgoAPI_Splitter()
        splitter.SetArguments([bl_to_ocp_shape(inputs[0])])
        splitter.SetTools([bl_to_ocp_shape(inputs[1])])
        splitter.Build()
        return splitter.Shape()

class GSD_OT_Trim(GsdBaseOperator):
    bl_idname = "gsd.trim"; bl_label = "Trim"; gsd_command = "Trim"
    orientation1: BoolProperty(name="Keep Side 1", default=True)
    orientation2: BoolProperty(name="Keep Side 2", default=True)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
        from ..core.ocp_bridge import bl_to_ocp_shape
        s1 = bl_to_ocp_shape(inputs[0]); s2 = bl_to_ocp_shape(inputs[1])
        common = BRepAlgoAPI_Common(s1, s2)
        common.Build()
        return common.Shape() if common.IsDone() else s1

class GSD_OT_Sew(GsdBaseOperator):
    bl_idname = "gsd.sew"; bl_label = "Sew"; gsd_command = "Sew"
    tolerance: FloatProperty(name="Tolerance", default=0.001, precision=6)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
        from ..core.ocp_bridge import bl_to_ocp_shape
        sewer = BRepBuilderAPI_Sewing(params.get("tolerance", 0.001))
        for obj in inputs:
            sewer.Add(bl_to_ocp_shape(obj))
        sewer.Perform()
        return sewer.SewedShape()

class GSD_OT_Extrapolate(GsdBaseOperator):
    bl_idname = "gsd.extrapolate"; bl_label = "Extrapolate"; gsd_command = "Extrapolate"
    limit: FloatProperty(name="Limit", default=10.0, unit='LENGTH')
    continuity: EnumProperty(name="Continuity", items=[("Tangent","Tangent",""),("Curvature","Curvature","")], default="Tangent")
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_Invert(GsdBaseOperator):
    bl_idname = "gsd.invert"; bl_label = "Invert"; gsd_command = "Invert"
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        surf = bl_to_ocp_surface(inputs[0])
        surf.Reverse()
        return surf

class GSD_OT_Near(GsdBaseOperator):
    bl_idname = "gsd.near"; bl_label = "Near"; gsd_command = "Near"
    def min_inputs(self): return 2  # element + reference point
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt
        return gp_Pnt(inputs[1].location.x, inputs[1].location.y, inputs[1].location.z)

    def _create_result_object(self, result_shape, name):
        from ..core.ocp_bridge import ocp_to_bl_point
        return ocp_to_bl_point(result_shape, name)

_jointrim_classes = [GSD_OT_Join, GSD_OT_Healing, GSD_OT_Untrim, GSD_OT_Disassemble, GSD_OT_Split, GSD_OT_Trim, GSD_OT_Sew, GSD_OT_Extrapolate, GSD_OT_Invert, GSD_OT_Near]
def register():
    for cls in _jointrim_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_jointrim_classes): bpy.utils.unregister_class(cls)
