"""GSD Scene Properties.

Stored on bpy.types.Scene — accessible via context.scene.gsd_props.
"""

import bpy
from bpy.props import (
    FloatProperty, IntProperty, BoolProperty, EnumProperty,
    StringProperty, CollectionProperty, PointerProperty,
)


class GSDToleranceProps(bpy.types.PropertyGroup):
    """Per-scene GSD tolerance settings."""
    modeling_tolerance: FloatProperty(
        name="Modeling Tolerance",
        description="NURBS/surface creation precision (mm)",
        default=0.001, min=0.00001, max=10.0, precision=6,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )
    angular_tolerance: FloatProperty(
        name="Angular Tolerance",
        description="Angle tolerance for join/intersect operations (deg)",
        default=0.5, min=0.001, max=90.0, precision=3,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )
    merging_distance: FloatProperty(
        name="Merging Distance",
        description="Gap tolerance for join/heal/sew (mm)",
        default=0.001, min=0.00001, max=10.0, precision=6,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )
    display_discretization: FloatProperty(
        name="Display Discretization",
        description="Surface visualization mesh density (mm)",
        default=1.0, min=0.01, max=100.0, precision=2,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )
    curve_discretization: FloatProperty(
        name="Curve Discretization",
        description="Curve visualization density (mm)",
        default=0.1, min=0.01, max=10.0, precision=2,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )
    canonical_tolerance: FloatProperty(
        name="Canonical Tolerance",
        description="Plane/cylinder/sphere detection tolerance (mm)",
        default=0.01, min=0.0001, max=1.0, precision=4,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )
    smoothing_tolerance: FloatProperty(
        name="Smoothing Tolerance",
        description="Sweep/loft/fill smoothing deviation (mm)",
        default=0.01, min=0.0001, max=1.0, precision=4,
        update=lambda self, ctx: _sync_tolerances(ctx),
    )


def _sync_tolerances(context):
    """Sync Blender property changes to global tolerance singleton."""
    from ..core import tolerance
    scene = context.scene
    tolerances = scene.gsd_tolerances
    tol = tolerance.get()
    tol.modeling_tolerance = tolerances.modeling_tolerance
    tol.angular_tolerance = tolerances.angular_tolerance
    tol.merging_distance = tolerances.merging_distance
    tol.display_discretization = tolerances.display_discretization
    tol.curve_discretization = tolerances.curve_discretization
    tol.canonical_tolerance = tolerances.canonical_tolerance
    tol.smoothing_tolerance = tolerances.smoothing_tolerance


class GSDSceneProps(bpy.types.PropertyGroup):
    """Main GSD scene property group."""
    current_geometric_set: StringProperty(
        name="Current Geometric Set",
        description="Active geometric set for new elements",
        default="Geometrical Set.1",
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register():
    bpy.utils.register_class(GSDToleranceProps)
    bpy.utils.register_class(GSDSceneProps)
    bpy.types.Scene.gsd_tolerances = PointerProperty(type=GSDToleranceProps)
    bpy.types.Scene.gsd_props = PointerProperty(type=GSDSceneProps)


def unregister():
    del bpy.types.Scene.gsd_props
    del bpy.types.Scene.gsd_tolerances
    bpy.utils.unregister_class(GSDSceneProps)
    bpy.utils.unregister_class(GSDToleranceProps)
