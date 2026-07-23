"""GSD global tolerance system.

Maps CATIA's tolerance model to OCP's precision system.
All GSD operations reference these values for consistency.
"""

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Tolerance data model
# ---------------------------------------------------------------------------

@dataclass
class GSDTolerances:
    """Global tolerance settings matching CATIA V5 GSD defaults."""
    modeling_tolerance: float = 0.001      # mm — NURBS/surface creation precision
    angular_tolerance: float = 0.5         # deg — Angle tolerance for join/intersect
    merging_distance: float = 0.001        # mm — Gap tolerance for join/heal/sew
    display_discretization: float = 1.0    # mm — Surface visualization mesh density
    curve_discretization: float = 0.1      # mm — Curve visualization density
    canonical_tolerance: float = 0.01      # mm — Plane/cylinder/sphere detection
    smoothing_tolerance: float = 0.01      # mm — Sweep/loft/fill smoothing


# Singleton instance
_TOLERANCES: GSDTolerances = GSDTolerances()


def get() -> GSDTolerances:
    """Return the current global tolerance settings."""
    return _TOLERANCES


def update_from_scene(scene_tolerances):
    """Sync from Blender scene properties."""
    global _TOLERANCES
    _TOLERANCES.modeling_tolerance = scene_tolerances.modeling_tolerance
    _TOLERANCES.angular_tolerance = scene_tolerances.angular_tolerance
    _TOLERANCES.merging_distance = scene_tolerances.merging_distance
    _TOLERANCES.display_discretization = scene_tolerances.display_discretization
    _TOLERANCES.curve_discretization = scene_tolerances.curve_discretization
    _TOLERANCES.canonical_tolerance = scene_tolerances.canonical_tolerance
    _TOLERANCES.smoothing_tolerance = scene_tolerances.smoothing_tolerance


def init_tolerances():
    """Called on add-on registration."""
    global _TOLERANCES
    _TOLERANCES = GSDTolerances()


def cleanup_tolerances():
    """Called on add-on unregistration."""
    global _TOLERANCES
    _TOLERANCES = None
