"""Fillet Operators — Face-Face Fillet, Chordal Fillet."""
import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_Fillet(GsdBaseOperator):
    bl_idname = "gsd.fillet"; bl_label = "Fillet"; gsd_command = "FaceFaceFillet"
    fillet_type: EnumProperty(name="Type", items=[("FaceFaceFillet","Face-Face Fillet",""),("ChordalFillet","Chordal Fillet","")], default="FaceFaceFillet")
    radius: FloatProperty(name="Radius", default=5.0, unit='LENGTH')
    chord_length: FloatProperty(name="Chord Length", default=5.0, unit='LENGTH')
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
        from ..core.ocp_bridge import bl_to_ocp_shape
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_EDGE

        ft = params.get("fillet_type", "FaceFaceFillet")
        s1 = bl_to_ocp_shape(inputs[0]); s2 = bl_to_ocp_shape(inputs[1])
        filletter = BRepFilletAPI_MakeFillet(s1)

        if ft == "ChordalFillet":
            cl = params.get("chord_length", 5)
            explorer = TopExp_Explorer(s1, TopAbs_EDGE)
            while explorer.More():
                filletter.Add(cl, explorer.Current())
                explorer.Next()
        else:
            r = params.get("radius", 5)
            explorer = TopExp_Explorer(s1, TopAbs_EDGE)
            while explorer.More():
                filletter.Add(r, explorer.Current())
                explorer.Next()

        filletter.Build()
        return filletter.Shape()

_fillet_classes = [GSD_OT_Fillet]
def register():
    for cls in _fillet_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_fillet_classes): bpy.utils.unregister_class(cls)
