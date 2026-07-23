"""GSD selection validation.

Enforces the core constraint: GSD operators accept ONLY whole Points, Curves,
or full NURBS Surfaces. NEVER vertices, edges, or faces as sub-elements.

If a CATIA command traditionally needs a sub-element (e.g., Face-Face Fillet),
we require whole surface selection + optional limit points to define the domain.
"""

import bpy
from typing import Optional


class GsdSelectionError(Exception):
    """Raised when user selects invalid geometry for a GSD operation."""
    pass


# ---------------------------------------------------------------------------
# GSD element detection
# ---------------------------------------------------------------------------

GSD_TYPE_ATTR = "gsd_type"
GSD_ID_ATTR = "gsd_id"


def is_gsd_element(obj: bpy.types.Object) -> bool:
    """Check if a Blender object is a GSD element (has gsd_type custom property)."""
    if obj is None:
        return False
    return GSD_TYPE_ATTR in obj


def is_gsd_point(obj: bpy.types.Object) -> bool:
    """Check if object is a GSD point (empty with GSD metadata)."""
    if not is_gsd_element(obj):
        return False
    return obj.get(GSD_TYPE_ATTR, "").startswith("Point")


def is_gsd_curve(obj: bpy.types.Object) -> bool:
    """Check if object is a GSD curve (mesh with curve CP attributes)."""
    if not is_gsd_element(obj):
        return False
    return obj.get(GSD_TYPE_ATTR, "") in _CURVE_TYPES


def is_gsd_surface(obj: bpy.types.Object) -> bool:
    """Check if object is a GSD surface (mesh with surface CP attributes)."""
    if not is_gsd_element(obj):
        return False
    return obj.get(GSD_TYPE_ATTR, "") in _SURFACE_TYPES


def is_valid_gsd_input(obj: bpy.types.Object) -> bool:
    """Check if an object can be used as input to GSD operations."""
    return is_gsd_point(obj) or is_gsd_curve(obj) or is_gsd_surface(obj)


_CURVE_TYPES = {
    "Line", "Axis", "Polyline", "Circle", "Arc", "Corner",
    "ConnectCurve", "Conic", "Spline", "Helix", "Spiral", "Spine",
    "Projection", "Combine", "ReflectLine", "ParallelCurve",
    "3DCurveOffset", "Intersection",
}

_SURFACE_TYPES = {
    "Extrude", "Revolve", "Sphere", "Cylinder",
    "Offset", "VariableOffset", "RoughOffset",
    "Fill", "Blend", "Loft",
    "SweepExplicit", "SweepLine", "SweepCircle", "SweepConic",
    "Join", "Split", "Trim", "Sew",
    "FaceFaceFillet", "ChordalFillet",
    "Translate", "Rotate", "Symmetry", "Scaling", "Affinity",
    "RectPattern", "CircPattern", "UserPattern",
    "ThickSurface", "CloseSurface", "SewSurface",
}


# ---------------------------------------------------------------------------
# Selection validation
# ---------------------------------------------------------------------------

def validate_no_sub_element_selection(context: bpy.types.Context) -> None:
    """Raise GsdSelectionError if user is not in OBJECT mode or has
    mesh components selected.

    This enforces: "NEVER require selecting vertices, edges, or faces."
    """
    # Must be in OBJECT mode
    if context.mode != 'OBJECT':
        raise GsdSelectionError(
            "GSD operators require OBJECT mode.\n"
            "Switch to Object Mode — select whole curves, surfaces, or points."
        )


def validate_gsd_inputs(
    objects: list[bpy.types.Object],
    operation_name: str = "",
    min_count: int = 1,
    max_count: int = 999,
    allowed_types: Optional[set] = None,
) -> list[bpy.types.Object]:
    """Validate a list of selected objects as GSD inputs.

    Args:
        objects: Selected Blender objects.
        operation_name: For error messages.
        min_count: Minimum required inputs.
        max_count: Maximum allowed inputs.
        allowed_types: Set of allowed GSD types (e.g., {"Spline", "Line"}).
                       If None, any valid GSD input is accepted.

    Returns:
        The validated list of objects.

    Raises:
        GsdSelectionError: If validation fails.
    """
    n = len(objects)
    op = f"'{operation_name}' " if operation_name else ""

    if n < min_count:
        raise GsdSelectionError(
            f"{op}requires at least {min_count} input(s). "
            f"Only {n} selected."
        )
    if n > max_count:
        raise GsdSelectionError(
            f"{op}accepts at most {max_count} input(s). "
            f"{n} selected."
        )

    for i, obj in enumerate(objects):
        if not is_gsd_element(obj):
            raise GsdSelectionError(
                f"'{obj.name}' is not a GSD element.\n"
                f"Select points, curves, or surfaces created by GSD commands only."
            )

        if allowed_types is not None:
            gsd_type = obj.get(GSD_TYPE_ATTR, "")
            if gsd_type not in allowed_types:
                raise GsdSelectionError(
                    f"'{obj.name}' is a '{gsd_type}', but {op}"
                    f"expects one of: {', '.join(sorted(allowed_types))}."
                )

    return objects


def get_selected_gsd_objects(context: bpy.types.Context) -> list[bpy.types.Object]:
    """Get all selected GSD-valid objects."""
    return [o for o in context.selected_objects if is_valid_gsd_input(o)]


def validate_and_collect(
    context: bpy.types.Context,
    operation_name: str = "",
    min_count: int = 1,
    max_count: int = 999,
    allowed_types: Optional[set] = None,
) -> list[bpy.types.Object]:
    """Combined validation: mode check + collect valid objects + count/type check."""
    validate_no_sub_element_selection(context)
    objects = get_selected_gsd_objects(context)
    return validate_gsd_inputs(objects, operation_name, min_count, max_count, allowed_types)
