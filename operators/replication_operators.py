"""Replication Operators — PowerCopy, UserFeature."""
import bpy
from bpy.props import StringProperty
from .base_operator import GsdBaseOperator

class GSD_OT_PowerCopy(GsdBaseOperator):
    bl_idname = "gsd.power_copy"; bl_label = "PowerCopy"; gsd_command = "PowerCopy"
    name: StringProperty(name="Name", default="PowerCopy.1")
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

class GSD_OT_UserFeature(GsdBaseOperator):
    bl_idname = "gsd.user_feature"; bl_label = "User Feature"; gsd_command = "UserFeature"
    type_name: StringProperty(name="Type Name", default="UserFeature")
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

_replication_classes = [GSD_OT_PowerCopy, GSD_OT_UserFeature]
def register():
    for cls in _replication_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_replication_classes): bpy.utils.unregister_class(cls)
