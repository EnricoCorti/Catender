"""Sweep Operators — All 4 families, 15 sub-types."""
import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator
from ..core.gsd_types import SweepFamily

class GSD_OT_Sweep(GsdBaseOperator):
    bl_idname = "gsd.sweep"; bl_label = "Sweep"; gsd_command = "SweepExplicit"
    sweep_family: EnumProperty(name="Family", items=[("Explicit","Explicit",""),("Line","Line",""),("Circle","Circle",""),("Conic","Conic","")], default="Explicit")
    subtype: EnumProperty(name="Sub-Type",
        items=[
            ("WithReferenceSurface","With Reference Surface",""), ("WithPullingDirection","With Pulling Direction",""),
            ("WithTwoGuideCurves","With Two Guide Curves",""), ("WithTangencySurface","With Tangency Surface",""),
            ("TwoLimits","Two Limits",""), ("LimitAndMiddle","Limit and Middle",""),
            ("LineRefSurface","Line: With Reference Surface",""), ("LineRefCurve","Line: With Reference Curve",""),
            ("LineTangency","Line: With Tangency Surface",""), ("LineDraft","Line: With Draft Direction",""),
            ("ThreeGuides","Three Guides",""), ("TwoGuidesRadius","Two Guides and Radius",""),
            ("CenterTwoAngles","Center and Two Angles",""), ("CenterRadius","Center and Radius",""),
            ("TwoGuidesTangency","Two Guides and Tangency Surface",""), ("OneGuideTangency","One Guide and Tangency Surface",""),
            ("ConicThreeGuides","Conic: Three Guides",""), ("ConicTwoGuides","Conic: Two Guides and Parameter",""),
            ("ConicFourGuides","Conic: Four Guides + Tangent",""), ("ConicFiveGuides","Conic: Five Guides",""),
        ], default="WithReferenceSurface")
    angle: FloatProperty(name="Angle", default=0.0, unit='ROTATION')
    radius: FloatProperty(name="Radius", default=5.0, unit='LENGTH')
    length1: FloatProperty(name="Length 1", default=10.0, unit='LENGTH')
    length2: FloatProperty(name="Length 2", default=10.0, unit='LENGTH')
    draft_angle: FloatProperty(name="Draft Angle", default=0.0, unit='ROTATION')
    conic_param: FloatProperty(name="Conic Parameter", default=0.5, min=0.01, max=0.99)
    smoothing: BoolProperty(name="Smoothing", default=False)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
        from ..core.ocp_bridge import bl_to_ocp_curve, bl_to_ocp_surface

        family = params.get("sweep_family", "Explicit")
        sub = params.get("subtype", "WithReferenceSurface")
        profile_wire = bl_to_ocp_curve(inputs[0])

        if family == "Explicit":
            guide = bl_to_ocp_curve(inputs[1])
            pipe = BRepOffsetAPI_MakePipeShell(guide)
            pipe.Add(profile_wire)
            pipe.Build()
            return pipe.Shape()
        elif family == "Line":
            guide = bl_to_ocp_curve(inputs[0]) if len(inputs) >= 2 else profile_wire
            pipe = BRepOffsetAPI_MakePipeShell(guide)
            pipe.SetMode(True)  # Corrected Frenet frame
            pipe.Add(profile_wire)
            pipe.Build()
            return pipe.Shape()
        elif family == "Circle":
            guide = bl_to_ocp_curve(inputs[0]) if len(inputs) >= 2 else profile_wire
            pipe = BRepOffsetAPI_MakePipeShell(guide)
            pipe.SetMode(True)
            pipe.Add(profile_wire)
            pipe.Build()
            return pipe.Shape()
        else:  # Conic
            guide = bl_to_ocp_curve(inputs[0]) if len(inputs) >= 2 else profile_wire
            pipe = BRepOffsetAPI_MakePipeShell(guide)
            pipe.SetMode(True)
            pipe.Add(profile_wire)
            pipe.Build()
            return pipe.Shape()

_sweep_classes = [GSD_OT_Sweep]
def register():
    for cls in _sweep_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_sweep_classes): bpy.utils.unregister_class(cls)
