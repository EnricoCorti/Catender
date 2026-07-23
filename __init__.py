"""CATIA Generative Shape Design (GSD) for Blender 5.2+"""
import sys, os

bl_info = {
    "name": "CATIA GSD",
    "author": "GSD Blender Team",
    "version": (0, 1, 0),
    "blender": (5, 1, 0),
    "location": "3D View > Sidebar > GSD",
    "description": "CATIA V5 Generative Shape Design — NURBS surface modeling",
    "category": "3D View",
}

# Ensure OCP is importable
def _setup_ocp():
    try:
        import bpy
        local = bpy.utils.resource_path('LOCAL')
        ocp_path = os.path.join(local, 'extensions', '.local', 'lib', 'python3.13', 'site-packages')
        if os.path.isdir(ocp_path) and ocp_path not in sys.path:
            sys.path.insert(0, ocp_path)
    except Exception:
        pass


def register():
    _setup_ocp()

    # Import and register all components
    from .core import tolerance
    tolerance.init_tolerances()

    from .props import gsd_properties
    gsd_properties.register()

    from .preferences import gsd_preferences
    gsd_preferences.register()

    from .operators import (
        base_operator,
        wireframe_operators,
        curve_operators,
        surface_operators,
        transition_operators,
        join_trim_operators,
        fillet_operators,
        transform_operators,
        pattern_operators,
        project_combine_operators,
        sweep_operators,
        analysis_operators,
        replication_operators,
        tools_operators,
    )
    wireframe_operators.register()
    curve_operators.register()
    surface_operators.register()
    transition_operators.register()
    join_trim_operators.register()
    fillet_operators.register()
    transform_operators.register()
    pattern_operators.register()
    project_combine_operators.register()
    sweep_operators.register()
    analysis_operators.register()
    replication_operators.register()
    tools_operators.register()

    from .panels import main_panel
    main_panel.register()

    from .core import gsd_dependency_graph
    gsd_dependency_graph.register()

    from .core.gsd_element import scan_existing_names
    scan_existing_names()

    print("[CATIA GSD] Ready — GSD tab in 3D View sidebar")


def unregister():
    from .panels import main_panel
    main_panel.unregister()

    from .operators import (
        tools_operators, replication_operators, analysis_operators,
        sweep_operators, project_combine_operators, pattern_operators,
        transform_operators, fillet_operators, join_trim_operators,
        transition_operators, surface_operators, curve_operators,
        wireframe_operators,
    )
    tools_operators.unregister()
    replication_operators.unregister()
    analysis_operators.unregister()
    sweep_operators.unregister()
    project_combine_operators.unregister()
    pattern_operators.unregister()
    transform_operators.unregister()
    fillet_operators.unregister()
    join_trim_operators.unregister()
    transition_operators.unregister()
    surface_operators.unregister()
    curve_operators.unregister()
    wireframe_operators.unregister()

    from .core import gsd_dependency_graph
    gsd_dependency_graph.unregister()

    from .preferences import gsd_preferences
    gsd_preferences.unregister()

    from .props import gsd_properties
    gsd_properties.unregister()

    from .core import tolerance
    tolerance.cleanup_tolerances()

    print("[CATIA GSD] Unregistered")


if __name__ == "__main__":
    register()
