"""Sweep Operators — Safe implementation."""
import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_Sweep(GsdBaseOperator):
    bl_idname = "gsd.sweep"; bl_label = "Sweep"; gsd_command = "SweepExplicit"
    sweep_family: EnumProperty(name="Family", items=[
        ("Explicit","Explicit",""),("Line","Line (implicit)",""),
        ("Circle","Circle (implicit)",""),("Conic","Conic (implicit)","")], default="Explicit")
    angle: FloatProperty(name="Angle", default=0.0, unit='ROTATION')
    radius: FloatProperty(name="Radius", default=5.0, unit='LENGTH')
    length1: FloatProperty(name="Length 1", default=10.0, unit='LENGTH')
    length2: FloatProperty(name="Length 2", default=10.0, unit='LENGTH')
    draft_angle: FloatProperty(name="Draft Angle", default=0.0, unit='ROTATION')
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
        from ..core.ocp_bridge import bl_to_ocp_curve
        try:
            profile = bl_to_ocp_curve(inputs[0])
            guide = bl_to_ocp_curve(inputs[1])
            pipe = BRepOffsetAPI_MakePipeShell(guide)
            pipe.SetMode(True)
            pipe.Add(profile)
            pipe.Build()
            if pipe.IsDone():
                return pipe.Shape()
        except Exception:
            pass
        return bl_to_ocp_curve(inputs[0])

_sweep_classes = [GSD_OT_Sweep]
def register():
    for cls in _sweep_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_sweep_classes): bpy.utils.unregister_class(cls)
