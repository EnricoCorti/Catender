"""Tools Operators — Axis System, Working Support, Geometric Set, Update, Delete Useless."""
import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from .base_operator import GsdBaseOperator
from ..core.gsd_types import AxisSystemType

class GSD_OT_AxisSystem(GsdBaseOperator):
    bl_idname = "gsd.axis_system"; bl_label = "Axis System"; gsd_command = "AxisSystem"
    axis_type: EnumProperty(name="Type", items=[(t.value, t.value, "") for t in AxisSystemType], default=AxisSystemType.STANDARD.value)
    def min_inputs(self): return 1  # origin point
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        origin = inputs[0].location
        ax3 = gp_Ax3(gp_Pnt(origin.x, origin.y, origin.z), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
        from OCP.gp import gp_Pln
        pln = gp_Pln(ax3)
        return BRepBuilderAPI_MakeFace(pln, -50, 50, -50, 50).Face()

class GSD_OT_WorkingSupport(GsdBaseOperator):
    bl_idname = "gsd.working_support"; bl_label = "Working Support"; gsd_command = "WorkingSupport"
    def min_inputs(self): return 0
    def compute_ocp_result(self, inputs, params):
        from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Pln
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        ax3 = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(1, 0, 0))
        pln = gp_Pln(ax3)
        return BRepBuilderAPI_MakeFace(pln, -1000, 1000, -1000, 1000).Face()

class GSD_OT_GeometricSet(GsdBaseOperator):
    bl_idname = "gsd.geometric_set"; bl_label = "Geometric Set"; gsd_command = "GeometricSet"
    set_name: StringProperty(name="Name", default="Geometrical Set")
    ordered: BoolProperty(name="Ordered", default=False)
    def min_inputs(self): return 0
    def compute_ocp_result(self, inputs, params):
        name = params.get("set_name", "Geometrical Set")
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection

    def _create_result_object(self, result_shape, name):
        # Return a placeholder empty to mark the geometric set
        if isinstance(result_shape, bpy.types.Collection):
            # Collection created — no object needed, but create an empty marker
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'CUBE'
            obj.empty_display_size = 0.5
            bpy.context.collection.objects.link(obj)
            return obj
        return super()._create_result_object(result_shape, name)

class GSD_OT_Update(GsdBaseOperator):
    bl_idname = "gsd.update"; bl_label = "Update"; gsd_command = "Update"
    def min_inputs(self): return 0
    def compute_ocp_result(self, inputs, params):
        from ..core import gsd_dependency_graph as dg
        count = dg.update_all()
        self.report({'INFO'}, f"Updated {count} element(s)")
        from OCP.gp import gp_Pnt
        return gp_Pnt(0, 0, 0)  # dummy — no visual result

    def _create_result_object(self, result_shape, name):
        return None  # Update produces no visible object

class GSD_OT_DeleteUseless(GsdBaseOperator):
    bl_idname = "gsd.delete_useless"; bl_label = "Delete Useless"; gsd_command = "DeleteUseless"
    def min_inputs(self): return 0
    def compute_ocp_result(self, inputs, params):
        # Find and remove unreferenced GSD objects
        from ..core import gsd_dependency_graph as dg
        import json
        referenced = set()
        for name, elem in dg._ELEMENT_REGISTRY.items():
            inputs_str = elem.bl_object.get("gsd_inputs", "[]")
            try:
                for inp in json.loads(inputs_str):
                    referenced.add(inp)
            except:
                pass

        removed = 0
        for obj in list(bpy.data.objects):
            if "gsd_type" in obj and obj.name not in referenced:
                # Check it's not referenced by anything
                is_referenced = False
                for name2, elem2 in dg._ELEMENT_REGISTRY.items():
                    if obj.name in elem2.inputs:
                        is_referenced = True
                        break
                if not is_referenced and len(obj.users_scene) <= 1:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed += 1

        self.report({'INFO'}, f"Removed {removed} useless element(s)")
        from OCP.gp import gp_Pnt
        return gp_Pnt(0, 0, 0)

    def _create_result_object(self, result_shape, name):
        return None

_tools_classes = [GSD_OT_AxisSystem, GSD_OT_WorkingSupport, GSD_OT_GeometricSet, GSD_OT_Update, GSD_OT_DeleteUseless]
def register():
    for cls in _tools_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_tools_classes): bpy.utils.unregister_class(cls)
