"""Surface Operators — Extrude, Revolve, Sphere, Cylinder, Offset."""
import bpy, math
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_Extrude(GsdBaseOperator):
    bl_idname = "gsd.extrude"; bl_label = "Extrude"; gsd_command = "Extrude"
    limit1: FloatProperty(name="Limit 1", default=20.0, unit='LENGTH')
    limit2: FloatProperty(name="Limit 2", default=0.0, unit='LENGTH')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Vec
        from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
        from ..core.ocp_bridge import bl_to_ocp_surface
        surf = bl_to_ocp_surface(inputs[0])
        l1 = params.get("limit1", 20)
        vec = gp_Vec(0, 0, l1)
        prism = BRepPrimAPI_MakePrism(surf, vec, False).Shape()
        return prism

class GSD_OT_Revolve(GsdBaseOperator):
    bl_idname = "gsd.revolve"; bl_label = "Revolve"; gsd_command = "Revolve"
    angle1: FloatProperty(name="Angle 1", default=360.0, unit='ROTATION')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax1
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
        from ..core.ocp_bridge import bl_to_ocp_shape
        
        shape = bl_to_ocp_shape(inputs[0])
        ax1 = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
        angle = params.get("angle1", 360) * math.pi / 180
        
        # Use the shape directly if it has faces
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_FACE
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        if explorer.More():
            return BRepPrimAPI_MakeRevol(shape, ax1, angle, False).Shape()
        
        # Fallback: create a face from wire
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        from ..core.ocp_bridge import bl_to_ocp_curve
        wire = bl_to_ocp_curve(inputs[0])
        face = BRepBuilderAPI_MakeFace(wire).Face()
        return BRepPrimAPI_MakeRevol(face, ax1, angle, False).Shape()

class GSD_OT_Sphere(GsdBaseOperator):
    bl_idname = "gsd.sphere_surface"; bl_label = "Sphere"; gsd_command = "Sphere"
    radius: FloatProperty(name="Radius", default=10.0, unit='LENGTH')
    parallel_start: FloatProperty(name="Lat Start", default=-90.0, unit='ROTATION')
    parallel_end: FloatProperty(name="Lat End", default=90.0, unit='ROTATION')
    meridian_start: FloatProperty(name="Long Start", default=0.0, unit='ROTATION')
    meridian_end: FloatProperty(name="Long End", default=360.0, unit='ROTATION')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere
        center = inputs[0].location; r = params.get("radius", 10)
        ax2 = gp_Ax2(gp_Pnt(center.x, center.y, center.z), gp_Dir(0, 0, 1))
        return BRepPrimAPI_MakeSphere(ax2, r, 2*math.pi).Shape()

class GSD_OT_Cylinder(GsdBaseOperator):
    bl_idname = "gsd.cylinder_surface"; bl_label = "Cylinder"; gsd_command = "Cylinder"
    radius: FloatProperty(name="Radius", default=10.0, unit='LENGTH')
    length1: FloatProperty(name="Length 1", default=20.0, unit='LENGTH')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
        center = inputs[0].location; r = params.get("radius", 10); h = params.get("length1", 20)
        ax2 = gp_Ax2(gp_Pnt(center.x, center.y, center.z), gp_Dir(0, 0, 1))
        return BRepPrimAPI_MakeCylinder(ax2, r, h).Shape()

class GSD_OT_Offset(GsdBaseOperator):
    bl_idname = "gsd.offset"; bl_label = "Offset"; gsd_command = "Offset"
    offset_type: EnumProperty(name="Type", items=[("Offset","Offset",""),("VariableOffset","Variable Offset",""),("RoughOffset","Rough Offset","")], default="Offset")
    offset_distance: FloatProperty(name="Distance", default=5.0, unit='LENGTH')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
        from ..core.ocp_bridge import bl_to_ocp_surface
        surf = bl_to_ocp_surface(inputs[0])
        d = params.get("offset_distance", 5)
        offsetter = BRepOffsetAPI_MakeOffset()
        offsetter.PerformByJoin(surf, d, 0.001)
        return offsetter.Shape()

class GSD_OT_VariableOffset(GsdBaseOperator):
    bl_idname = "gsd.var_offset"; bl_label = "Var Offset"; gsd_command = "VariableOffset"
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_RoughOffset(GsdBaseOperator):
    bl_idname = "gsd.rough_offset"; bl_label = "Rough Offset"; gsd_command = "RoughOffset"
    offset_distance: FloatProperty(name="Distance", default=5.0, unit='LENGTH')
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
        from ..core.ocp_bridge import bl_to_ocp_surface
        surf = bl_to_ocp_surface(inputs[0])
        d = params.get("offset_distance", 5)
        offsetter = BRepOffsetAPI_MakeOffset()
        offsetter.PerformByJoin(surf, d, 0.001)
        return offsetter.Shape()

_surface_classes = [GSD_OT_Extrude, GSD_OT_Revolve, GSD_OT_Sphere, GSD_OT_Cylinder, GSD_OT_Offset, GSD_OT_VariableOffset, GSD_OT_RoughOffset]
def register():
    for cls in _surface_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_surface_classes): bpy.utils.unregister_class(cls)
