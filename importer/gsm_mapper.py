"""CATIA GSM → Catender Operator Mapper.

Maps extracted GSM commands to Catender Blender operators.
Each CATIA command type maps to a specific Catender operator with
parameter translation.
"""

from typing import Dict, Any, Optional
from .catpart_reader import GsmCommand, CatPartFeatureTree


# ---------------------------------------------------------------------------
# Command mapping table: CATIA GSM → Catender operator
# ---------------------------------------------------------------------------

GSM_TO_CATENDER = {
    # Points
    "GSMPoint": "gsd.point",
    "GSMPointCoord": "gsd.point",
    "GSMPointOnCurve": "gsd.point",
    "GSMPointOnPlane": "gsd.point",
    "GSMPointOnSurface": "gsd.point",
    "GSMPointBetween": "gsd.point",
    "GSMPointCenter": "gsd.point",
    "GSMPointTangent": "gsd.point",
    "GSMPointBoundary": "gsd.point",
    
    # Lines
    "GSMLine": "gsd.line",
    "GSMLinePtPt": "gsd.line",
    "GSMLinePtDir": "gsd.line",
    "GSMLineAngle": "gsd.line",
    "GSMLineNormal": "gsd.line",
    "GSMLineBiTangent": "gsd.line",
    
    # Planes
    "GSMPlane": "gsd.plane",
    "GSMPlaneOffset": "gsd.plane",
    "GSMPlaneAngle": "gsd.plane",
    "GSMPlaneThreePoints": "gsd.plane",
    
    # Circles
    "GSMCircle": "gsd.circle",
    "GSMCircleCtrRad": "gsd.circle",
    "GSMCircleCenterAxisRadius": "gsd.circle",
    "GSMCircleBitangentRadRadius": "gsd.circle",
    
    # Curves
    "GSMSpline": "gsd.spline",
    "GSMCorner": "gsd.corner",
    "GSMConnectCurve": "gsd.connect_curve",
    "GSMConic": "gsd.conic",
    "GSMHelix": "gsd.helix",
    "GSMSpiral": "gsd.spiral",
    "GSMSpine": "gsd.spine",
    
    # Surfaces
    "GSMExtrude": "gsd.extrude",
    "GSMRevolve": "gsd.revolve",
    "GSMSphere": "gsd.sphere_surface",
    "GSMCylinder": "gsd.cylinder_surface",
    "GSMOffset": "gsd.offset",
    "GSMSweep": "gsd.sweep",
    "GSMLoft": "gsd.loft",
    "GSMFill": "gsd.fill",
    "GSMBlend": "gsd.blend",
    
    # Operations
    "GSMJoin": "gsd.join",
    "GSMAssemble": "gsd.join",
    "GSMHealing": "gsd.healing",
    "GSMUntrim": "gsd.untrim",
    "GSMDisassemble": "gsd.disassemble",
    "GSMSplit": "gsd.split",
    "GSMTrim": "gsd.trim",
    "GSMSew": "gsd.sew",
    "GSMExtrapol": "gsd.extrapolate",
    "GSMFillet": "gsd.fillet",
    "GSMNear": "gsd.near",
    
    # Transforms
    "GSMTranslate": "gsd.translate",
    "GSMRotate": "gsd.rotate",
    "GSMSymmetry": "gsd.symmetry",
    "GSMScaling": "gsd.scaling",
    "GSMAffinity": "gsd.affinity",
    
    # Patterns
    "GSMRectPattern": "gsd.rectangular_pattern",
    "GSMCircPattern": "gsd.circular_pattern",
    "GSMUserPattern": "gsd.user_pattern",
    
    # Projection
    "GSMProject": "gsd.projection",
    "GSMProjectNormal": "gsd.projection",
    "GSMIntersect": "gsd.intersection",
    
    # Tools
    "GSMAxisToAxis": "gsd.axis_system",
    "GSMWorkingSupport": "gsd.working_support",
}


def map_command_to_catender(cmd: GsmCommand) -> Optional[Dict[str, Any]]:
    """Map a GSM command to Catender operator call parameters.
    
    Args:
        cmd: The extracted GSM command.
        
    Returns:
        Dict with 'operator_id' and 'parameters' keys, or None if unmappable.
    """
    # Find the base command
    base_cmd = _find_base(cmd.catia_type)
    
    # Some parameter-only commands should be skipped (they modify the parent command)
    _SKIP_COMMANDS = {
        "GSMPointCoordValues", "GSMPointOnCurveValues",
        "GSMPointOnPlaneValues", "GSMPointOnSurfaceValues",
        "GSMPointBetweenValues", "GSMPointBoundary",
        "GSMPointDistanceType", "GSMPointType",
        "GSMLinePtPtLinePtPtLengths",
        "GSMPlaneValues", "GSMPlaneType", "GSMPlaneRatio",
        "GSMCircleAngle", "GSMCircleAxisComputation", "GSMCircleDiameterMode",
        "GSMCircleCenterAxisProjectionMode", "GSMCircleLimits", "GSMCircleTrim", "GSMCircleType",
        "GSMCircleCtrRadRadius", "GSMCircle2PointsRadRadius",
        "GSMCircleBitangentRadRadius", "GSMCircleCenterAxisRadius",
        "GSMTranslateDistance", "GSMTranslateType",
        "GSMRotateAngle", "GSMRotateRotationType",
        "GSMAffinityRatio",
        "GSMSphereAngle", "GSMSphereRadius",
        "GSMSweepAngle", "GSMSweepGuideDeviation",
        "GSMSplitIgnoreNoIntersecting", "GSMSplitKeepHalfSpace",
        "GSMExtrapolExtrapolationElements",
        "GSMIntersectIntExtrapolateMode", "GSMIntersectIntExtendMode",
        "GSMIntersectIntIntersectMode", "GSMIntersectSolutionPoint",
        "GSMExtractCurvatureThreshold", "GSMExtractDistanceThreshold",
        "GSMExtractAngularThreshold", "GSMExtractEXTRACTSOLIDE",
        "GSMExtractExtractType", "GSMExtractFederation",
        "GSMApproximation", "GSMApproximationApproximationMode",
        "GSMApproximationCustomDeviationActivity", "GSMApproximationDeviation",
        "GSMApproximationMaxOrderU", "GSMApproximationMaxOrderV",
        "GSMApproximationMaxSegmentsU", "GSMApproximationMaxSegmentsV",
        "GSMBoundaryType", "GSMInternal", "GSMLockState",
        "GSMInverseLocal", "GSMUINonConnexChoice",
        "GSMZeroDim", "GSMBiDim", "GSMMonoDim",
        "GSMIntersectIntersectSolid", "GSMIntersectstrGSMIntersectSolutionPoint",
        "GSMCurve", "GSMTool",
    }
    
    if cmd.catia_type in _SKIP_COMMANDS:
        return None
    
    operator_id = GSM_TO_CATENDER.get(base_cmd)
    if operator_id is None:
        return None
    
    # Translate parameters
    params = {}
    for param in cmd.parameters:
        catia_name = param.name
        catender_name = _translate_param_name(catia_name)
        catender_value = _translate_param_value(param.value)
        params[catender_name] = catender_value
    
    # Handle special translations
    _translate_point_type(cmd, params)
    _translate_line_type(cmd, params)
    _translate_plane_type(cmd, params)
    _translate_circle_type(cmd, params)
    
    return {
        "operator_id": operator_id,
        "parameters": params,
        "catia_type": cmd.catia_type,
    }


def _find_base(cmd_name: str) -> str:
    """Find the base command name by stripping modifiers."""
    # Remove trailing modifiers
    if cmd_name.endswith('Values'): cmd_name = cmd_name[:-6]
    if cmd_name.endswith('Type'): cmd_name = cmd_name[:-4]
    if cmd_name.endswith('Angle'): cmd_name = cmd_name[:-5]
    if cmd_name.endswith('Radius'): cmd_name = cmd_name[:-6]
    if cmd_name.endswith('Limits'): cmd_name = cmd_name[:-6]
    if cmd_name.endswith('Trim'): cmd_name = cmd_name[:-4]
    if cmd_name.endswith('Distance'): cmd_name = cmd_name[:-8]
    if cmd_name.endswith('Lengths'): cmd_name = cmd_name[:-7]
    
    # First try exact match
    if cmd_name in GSM_TO_CATENDER:
        return cmd_name
    
    # Try removing trailing modifiers
    base = cmd_name
    while len(base) > 4:
        if base in GSM_TO_CATENDER:
            return base
        # Strip last capital letter group
        match = _re.match(r'^(GSM[A-Z][a-z]+)', base)
        if match and match.group(1) in GSM_TO_CATENDER:
            return match.group(1)
        base = base[:-1]
    
    return cmd_name


import re as _re


def _translate_param_name(catia_name: str) -> str:
    """Translate CATIA parameter name to Catender property name."""
    translations = {
        "X": "x", "Y": "y", "Z": "z",
        "Radius": "radius",
        "StartAngle": "start_angle",
        "EndAngle": "end_angle",
        "Limit1": "limit1",
        "Limit2": "limit2",
        "Angle": "angle",
        "Distance": "distance",
        "Offset": "offset_distance",
        "Ratio": "ratio",
        "Orientation": "orientation",
        "StartLength": "start_length",
        "EndLength": "end_length",
    }
    return translations.get(catia_name, catia_name.lower())


def _translate_param_value(value: str) -> Any:
    """Translate a CATIA parameter value string to Python type."""
    value = value.strip()
    # Try float
    try:
        return float(value)
    except ValueError:
        pass
    # Try bool
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    return value


def _translate_point_type(cmd: GsmCommand, params: Dict):
    """Set the point_type parameter based on the GSM command."""
    if "PointCoord" in cmd.catia_type:
        params["point_type"] = "Coordinates"
    elif "PointOnCurve" in cmd.catia_type:
        params["point_type"] = "OnCurve"
    elif "PointOnPlane" in cmd.catia_type:
        params["point_type"] = "OnPlane"
    elif "PointOnSurface" in cmd.catia_type:
        params["point_type"] = "OnSurface"
    elif "PointBetween" in cmd.catia_type:
        params["point_type"] = "Between"
    elif "PointCenter" in cmd.catia_type:
        params["point_type"] = "CircleSphereCenter"


def _translate_line_type(cmd: GsmCommand, params: Dict):
    """Set the line_type parameter."""
    if "LinePtPt" in cmd.catia_type:
        params["line_type"] = "PointPoint"
    elif "LinePtDir" in cmd.catia_type:
        params["line_type"] = "PointDirection"
    elif "LineAngle" in cmd.catia_type:
        params["line_type"] = "AngleNormal"
    elif "LineNormal" in cmd.catia_type:
        params["line_type"] = "NormalToSurface"


def _translate_plane_type(cmd: GsmCommand, params: Dict):
    """Set the plane_type parameter."""
    if "PlaneOffset" in cmd.catia_type:
        params["plane_type"] = "OffsetFromPlane"
    elif "PlaneAngle" in cmd.catia_type:
        params["plane_type"] = "AngleNormalToPlane"


def _translate_circle_type(cmd: GsmCommand, params: Dict):
    """Set the circle_type parameter."""
    if "CircleCtrRad" in cmd.catia_type:
        params["circle_type"] = "CenterRadius"
    elif "CircleCenterAxis" in cmd.catia_type:
        params["circle_type"] = "CenterAxis"
    elif "CircleBitangent" in cmd.catia_type:
        params["circle_type"] = "BitangentRadius"


def get_import_plan(tree: CatPartFeatureTree) -> list:
    """Generate an ordered import plan from a feature tree.
    
    Returns a list of (operator_id, parameters) tuples in dependency order.
    Parameter-only commands are filtered out.
    """
    plan = []
    for cmd in tree.commands:
        mapped = map_command_to_catender(cmd)
        if mapped:
            plan.append(mapped)
    return plan


def stats(tree: CatPartFeatureTree) -> Dict[str, int]:
    """Get import statistics for a feature tree."""
    stats = {"total": len(tree.commands), "mapped": 0, "skipped": 0, "unmapped": 0}
    
    mapped_types = set()
    for cmd in tree.commands:
        result = map_command_to_catender(cmd)
        if result:
            stats["mapped"] += 1
            mapped_types.add(result["operator_id"])
        else:
            stats["skipped"] += 1
    
    stats["unique_operators"] = len(mapped_types)
    return stats
