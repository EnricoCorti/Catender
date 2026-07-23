"""GSD Element — Feature data model + registry.

Every GSD command creates a GsdElement that wraps a Blender object
and tracks its inputs, parameters, and type for dependency management.
"""

import bpy
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class GsdElement:
    """A single GSD feature wrapping a Blender object."""
    bl_object: bpy.types.Object
    gsd_type: str
    inputs: List[str]
    parameters: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def recompute(self):
        from . import gsd_dependency_graph as dg
        op_registry = dg.get_operator_registry()
        if self.gsd_type in op_registry:
            operator_cls = op_registry[self.gsd_type]
            operator_cls.recompute_element(self)
        else:
            print(f"WARNING: No recompute handler for GSD type '{self.gsd_type}'")

    def is_valid(self) -> bool:
        for name in self.inputs:
            if name not in bpy.data.objects:
                return False
        return self.bl_object is not None and self.bl_object.name in bpy.data.objects

    def to_dict(self) -> dict:
        return {
            "gsd_type": self.gsd_type,
            "inputs": self.inputs,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_object(cls, obj: bpy.types.Object) -> Optional["GsdElement"]:
        if "gsd_type" not in obj:
            return None
        inputs_str = obj.get("gsd_inputs", "[]")
        params_str = obj.get("gsd_params", "{}")
        try:
            inputs = json.loads(inputs_str)
        except json.JSONDecodeError:
            inputs = []
        try:
            parameters = json.loads(params_str)
        except json.JSONDecodeError:
            parameters = {}
        return cls(bl_object=obj, gsd_type=obj["gsd_type"], inputs=inputs, parameters=parameters)

    def write_to_object(self):
        obj = self.bl_object
        obj["gsd_type"] = self.gsd_type
        obj["gsd_id"] = obj.name
        obj["gsd_inputs"] = json.dumps(self.inputs)
        obj["gsd_params"] = json.dumps(self.parameters)


def create_gsd_element(obj, gsd_type, inputs, parameters):
    if obj is None:
        print(f"WARNING: create_gsd_element called with None object for type '{gsd_type}'")
        return None
    input_names = [i.name for i in inputs] if inputs else []
    element = GsdElement(bl_object=obj, gsd_type=gsd_type, inputs=input_names, parameters=parameters)
    element.write_to_object()
    from . import gsd_dependency_graph as dg
    dg.register_element(element)
    return element


# Naming convention
_COUNTERS: Dict[str, int] = {}

def next_name(gsd_type: str) -> str:
    short_name = _SHORT_NAMES.get(gsd_type, gsd_type)
    count = _COUNTERS.get(short_name, 0) + 1
    _COUNTERS[short_name] = count
    return f"{short_name}.{count}"

def reset_counters():
    global _COUNTERS
    _COUNTERS.clear()

def scan_existing_names():
    global _COUNTERS
    _COUNTERS.clear()
    for obj in bpy.data.objects:
        gsd_type = obj.get("gsd_type", "")
        if gsd_type:
            short = _SHORT_NAMES.get(gsd_type, gsd_type)
            parts = obj.name.rsplit(".", 1)
            if len(parts) == 2 and parts[1].isdigit():
                num = int(parts[1])
                if short not in _COUNTERS or num > _COUNTERS[short]:
                    _COUNTERS[short] = num

_SHORT_NAMES = {
    "Point": "Point", "PointRepetition": "PointRep",
    "Extremum": "Extremum",
    "Line": "Line", "Axis": "Axis", "Polyline": "Polyline",
    "Plane": "Plane",
    "Circle": "Circle", "Corner": "Corner",
    "ConnectCurve": "Connect", "Conic": "Conic",
    "Spline": "Spline", "Helix": "Helix",
    "Spiral": "Spiral", "Spine": "Spine",
    "Projection": "Project", "Combine": "Combine",
    "ReflectLine": "ReflectLine", "ParallelCurve": "Parallel",
    "3DCurveOffset": "CurveOffset", "Intersection": "Intersect",
    "Extrude": "Extrude", "Revolve": "Revolve",
    "Sphere": "Sphere", "Cylinder": "Cylinder",
    "Offset": "Offset", "VariableOffset": "VarOffset",
    "RoughOffset": "RoughOffset",
    "Fill": "Fill", "Blend": "Blend", "Loft": "Loft",
    "SweepExplicit": "Sweep", "SweepLine": "Sweep",
    "SweepCircle": "Sweep", "SweepConic": "Sweep",
    "Join": "Join", "Healing": "Healing",
    "Untrim": "Untrim", "Disassemble": "Disassemble",
    "Split": "Split", "Trim": "Trim", "Sew": "Sew",
    "Extrapolate": "Extrapolate", "Invert": "Invert", "Near": "Near",
    "FaceFaceFillet": "Fillet", "ChordalFillet": "Fillet",
    "Translate": "Translate", "Rotate": "Rotate",
    "Symmetry": "Symmetry", "Scaling": "Scaling", "Affinity": "Affinity",
    "RectPattern": "RectPattern", "CircPattern": "CircPattern",
    "UserPattern": "UserPattern", "Explode": "Explode",
    "Law": "Law", "ThickSurface": "ThickSurf",
    "CloseSurface": "CloseSurf", "SewSurface": "SewSurf",
    "AutoFillet": "AutoFillet",
    "ConnectChecker": "ConnectCheck", "DraftAnalysis": "DraftAnalysis",
    "CurvatureAnalysis": "Curvature", "Porcupine": "Porcupine",
    "DistanceAnalysis": "Distance", "SurfaceCurvature": "SurfCurvature",
    "HighlightAnalysis": "Highlight", "DeviationAnalysis": "Deviation",
    "FeatureIdentification": "FeatureID",
    "PowerCopy": "PowerCopy", "UserFeature": "UserFeature",
    "AxisSystem": "AxisSystem", "WorkingSupport": "WorkSupport",
    "GeometricSet": "GeoSet", "Update": "Update",
    "DeleteUseless": "DeleteUseless",
}
