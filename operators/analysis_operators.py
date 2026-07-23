"""Analysis Operators — Connect Checker, Draft, Curvature, Porcupine, Distance, Surface Curvature, Highlight, Deviation, Feature ID."""
import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from .base_operator import GsdBaseOperator

class GSD_OT_ConnectChecker(GsdBaseOperator):
    bl_idname = "gsd.connect_checker"; bl_label = "Connect Checker"; gsd_command = "ConnectChecker"
    check_type: EnumProperty(name="Check", items=[("G0","G0",""),("G1","G1",""),("G2","G2",""),("G3","G3","")], default="G1")
    tolerance_g0: FloatProperty(name="G0 Tolerance", default=0.001, precision=6)
    tolerance_g1: FloatProperty(name="G1 Tolerance", default=0.5, precision=3)
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

class GSD_OT_DraftAnalysis(GsdBaseOperator):
    bl_idname = "gsd.draft_analysis"; bl_label = "Draft Analysis"; gsd_command = "DraftAnalysis"
    draft_angle: FloatProperty(name="Draft Angle", default=5.0, unit='ROTATION')
    def min_inputs(self): return 2  # surface + direction
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_CurvatureAnalysis(GsdBaseOperator):
    bl_idname = "gsd.curvature_analysis"; bl_label = "Curvature Analysis"; gsd_command = "CurvatureAnalysis"
    analysis_type: EnumProperty(name="Type", items=[("Curvature","Curvature",""),("RadiusOfCurvature","Radius","")], default="Curvature")
    amplitude: FloatProperty(name="Amplitude", default=1.0)
    density: FloatProperty(name="Density", default=20.0)
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_curve
        return bl_to_ocp_curve(inputs[0])

class GSD_OT_Porcupine(GsdBaseOperator):
    bl_idname = "gsd.porcupine"; bl_label = "Porcupine"; gsd_command = "Porcupine"
    ratio: FloatProperty(name="Ratio", default=1.0)
    nb_spikes: IntProperty(name="Spikes", default=50, min=5, max=500)
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_curve
        return bl_to_ocp_curve(inputs[0])

class GSD_OT_DistanceAnalysis(GsdBaseOperator):
    bl_idname = "gsd.distance_analysis"; bl_label = "Distance Analysis"; gsd_command = "DistanceAnalysis"
    measure_type: EnumProperty(name="Measure", items=[("MinimumDistance","Min",""),("MaximumDistance","Max",""),("AlongDirection","Along Dir",""),("BandAnalysis","Band","")], default="MinimumDistance")
    def min_inputs(self): return 2
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

class GSD_OT_SurfaceCurvature(GsdBaseOperator):
    bl_idname = "gsd.surface_curvature"; bl_label = "Surface Curvature"; gsd_command = "SurfaceCurvature"
    curvature_type: EnumProperty(name="Type", items=[("Gaussian","Gaussian",""),("Mean","Mean",""),("Min","Min",""),("Max","Max","")], default="Gaussian")
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_Highlight(GsdBaseOperator):
    bl_idname = "gsd.highlight"; bl_label = "Highlight"; gsd_command = "HighlightAnalysis"
    nb_lines: IntProperty(name="Lines", default=10, min=1, max=100)
    spacing: FloatProperty(name="Spacing", default=20.0, unit='LENGTH')
    def min_inputs(self): return 2  # surface + direction
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_surface
        return bl_to_ocp_surface(inputs[0])

class GSD_OT_Deviation(GsdBaseOperator):
    bl_idname = "gsd.deviation"; bl_label = "Deviation"; gsd_command = "DeviationAnalysis"
    tolerance: FloatProperty(name="Tolerance", default=0.1, unit='LENGTH')
    def min_inputs(self): return 2  # reference + target
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

class GSD_OT_FeatureIdentification(GsdBaseOperator):
    bl_idname = "gsd.feature_identification"; bl_label = "Feature ID"; gsd_command = "FeatureIdentification"
    def min_inputs(self): return 1
    def compute_ocp_result(self, inputs, params):
        from ..core.ocp_bridge import bl_to_ocp_shape
        return bl_to_ocp_shape(inputs[0])

_analysis_classes = [GSD_OT_ConnectChecker, GSD_OT_DraftAnalysis, GSD_OT_CurvatureAnalysis, GSD_OT_Porcupine, GSD_OT_DistanceAnalysis, GSD_OT_SurfaceCurvature, GSD_OT_Highlight, GSD_OT_Deviation, GSD_OT_FeatureIdentification]
def register():
    for cls in _analysis_classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(_analysis_classes): bpy.utils.unregister_class(cls)
