"""CATIA GSD — Self-reporting on load."""
import bpy, os, json

# Module-level marker — BEFORE any imports, write that we were loaded
import os as _os
_tmp = _os.path.join(_os.environ.get('TEMP', '.'), 'gsd_module_imported.txt')
open(_tmp, 'w').write('GSD __init__.py was imported\n')

bl_info = {
    "name": "Catender",
    "version": (0, 1, 0),
    "blender": (5, 1, 0),
    "location": "3D View > Sidebar > GSD",
    "category": "3D View",
}

def _report_loaded():
    """Write a file to TEMP confirming we loaded."""
    try:
        out = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', '.')), 'gsd_loaded.txt')
        with open(out, 'w') as f:
            f.write(f"GSD LOADED OK\n")
            f.write(f"time={__import__('time').time()}\n")
    except:
        pass

def register():
    import sys, traceback
    try:
        local = bpy.utils.resource_path('LOCAL')
        ocp = os.path.join(local, 'extensions', '.local', 'lib', 'python3.13', 'site-packages')
        if os.path.isdir(ocp) and ocp not in sys.path:
            sys.path.insert(0, ocp)

        from .core import tolerance
        tolerance.init_tolerances()
        from .props import gsd_properties
        gsd_properties.register()
        from .preferences import gsd_preferences
        gsd_preferences.register()
        from .operators import wireframe_operators, curve_operators, surface_operators, transition_operators, join_trim_operators, fillet_operators, transform_operators, pattern_operators, project_combine_operators, sweep_operators, analysis_operators, replication_operators, tools_operators
        wireframe_operators.register(); curve_operators.register(); surface_operators.register()
        transition_operators.register(); join_trim_operators.register(); fillet_operators.register()
        transform_operators.register(); pattern_operators.register(); project_combine_operators.register()
        sweep_operators.register(); analysis_operators.register(); replication_operators.register(); tools_operators.register()
        from .panels import main_panel
        main_panel.register()
        from .core import gsd_dependency_graph
        gsd_dependency_graph.register()
        # Defer bpy.data access to after full startup
        def _finish_init():
            from .core.gsd_element import scan_existing_names
            scan_existing_names()
            _report_loaded()
            return None
        bpy.app.timers.register(_finish_init, first_interval=1.0)
        
        print("[CATIA GSD] Ready — GSD tab in sidebar")
    except Exception as e:
        print(f"[CATIA GSD] FAIL: {e}")
        traceback.print_exc()

def unregister():
    try:
        from .panels import main_panel; main_panel.unregister()
        from .operators import tools_operators, replication_operators, analysis_operators, sweep_operators, project_combine_operators, pattern_operators, transform_operators, fillet_operators, join_trim_operators, transition_operators, surface_operators, curve_operators, wireframe_operators
        tools_operators.unregister(); replication_operators.unregister(); analysis_operators.unregister()
        sweep_operators.unregister(); project_combine_operators.unregister(); pattern_operators.unregister()
        transform_operators.unregister(); fillet_operators.unregister(); join_trim_operators.unregister()
        transition_operators.unregister(); surface_operators.unregister(); curve_operators.unregister(); wireframe_operators.unregister()
        from .core import gsd_dependency_graph; gsd_dependency_graph.unregister()
        from .preferences import gsd_preferences; gsd_preferences.unregister()
        from .props import gsd_properties; gsd_properties.unregister()
        from .core import tolerance; tolerance.cleanup_tolerances()
        print("[CATIA GSD] Unregistered")
    except Exception as e:
        print(f"[CATIA GSD] Unregister error: {e}")

if __name__ == "__main__":
    register()
