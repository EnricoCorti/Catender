"""GSD Base Operator — Shared pattern for all GSD command operators.

Every GSD operator extends GsdBaseOperator and:
  1. Collects selected GSD objects as inputs
  2. Validates no sub-element selection
  3. Calls OCP to compute the result
  4. Creates a Blender mesh with GSD attributes
  5. Registers the new GsdElement in the dependency graph
"""

import bpy
from typing import List, Dict, Any, Optional
from ..core.selection import (
    validate_no_sub_element_selection,
    validate_gsd_inputs,
    get_selected_gsd_objects,
)
from ..core.gsd_element import create_gsd_element, next_name
from ..core.gsd_dependency_graph import register_operator
from ..core.tolerance import get as get_tolerances


class GsdBaseOperator(bpy.types.Operator):
    """Base class for all GSD command operators.

    Subclasses must override:
        gsd_command: str  — The GSD command identifier (e.g., "Extrude", "SweepExplicit")
        gsd_input_types: set  — Accepted GSD types for inputs (optional)

    Subclasses typically override:
        compute_ocp_result() — The OCP geometric operation
        draw() — Custom parameter UI in the redo panel
    """

    bl_options = {'REGISTER', 'UNDO'}

    # Must be set by subclass
    gsd_command: str = ""
    gsd_input_types: Optional[set] = None

    # Standard properties (subclasses add more)
    name_override: bpy.props.StringProperty(
        name="Name",
        description="Custom name for the result (auto-generated if empty)",
        default="",
    )

    @classmethod
    def poll(cls, context):
        """Only active in OBJECT mode with GSD objects selected."""
        return context.mode == 'OBJECT'

    def execute(self, context):
        """Standard execution flow for all GSD operators."""
        # 1. Validate and collect inputs
        validate_no_sub_element_selection(context)
        inputs = get_selected_gsd_objects(context)

        if len(inputs) < self.min_inputs():
            self.report({'ERROR'}, f"Select at least {self.min_inputs()} GSD element(s)")
            return {'CANCELLED'}

        # 2. Build parameter dict from operator properties
        params = self._collect_parameters()

        # 3. Perform the OCP operation
        try:
            result_shape = self.compute_ocp_result(inputs, params)
        except Exception as e:
            self.report({'ERROR'}, f"Operation failed: {e}")
            return {'CANCELLED'}

        if result_shape is None:
            self.report({'ERROR'}, "Operation produced no result")
            return {'CANCELLED'}

        # 4. Create Blender object
        name = self.name_override or next_name(self.gsd_command)
        result_obj = self._create_result_object(result_shape, name)

        # Handle operators that produce no visible object
        if result_obj is None:
            self.report({'INFO'}, f"{self.gsd_command} completed")
            return {'FINISHED'}

        # 5. Register GSD element
        create_gsd_element(result_obj, self.gsd_command, inputs, params)

        # 6. Select result, deselect inputs
        for obj in context.selected_objects:
            obj.select_set(False)
        result_obj.select_set(True)
        context.view_layer.objects.active = result_obj

        self.report({'INFO'}, f"Created {name}")
        return {'FINISHED'}

    # ---- Override points ----

    def min_inputs(self) -> int:
        """Minimum number of input objects required."""
        return 1

    def max_inputs(self) -> int:
        """Maximum number of input objects allowed."""
        return 999

    def compute_ocp_result(self, inputs: List[bpy.types.Object], params: Dict[str, Any]):
        """Perform the OCP geometric operation. Override in subclass.

        Args:
            inputs: List of selected GSD Blender objects.
            params: Dict of operator property values.

        Returns:
            An OCP TopoDS_Shape result, OR a Blender object directly.
        """
        raise NotImplementedError("Subclasses must implement compute_ocp_result()")

    def draw_parameters(self, layout, context):
        """Draw custom parameters in the operator redo panel. Override in subclass."""
        pass

    # ---- Internal helpers ----

    def _collect_parameters(self) -> Dict[str, Any]:
        """Collect all operator properties into a parameter dict."""
        params = {}
        # Collect all custom properties
        for key, prop_info in self.__class__.__dict__.items():
            if isinstance(prop_info, tuple) and len(prop_info) >= 2:
                # Blender property tuple
                params[key] = getattr(self, key, prop_info[0])
                continue
            # Skip Blender-internal attrs
            if key.startswith("bl_") or key.startswith("_"):
                continue
            if key in ('gsd_command', 'gsd_input_types', 'name_override',
                       'min_inputs', 'max_inputs', 'compute_ocp_result',
                       'draw_parameters', 'execute', 'poll', 'draw',
                       'invoke', 'modal', 'check', 'cancel'):
                continue
            if not key.startswith("__"):
                try:
                    val = getattr(self, key)
                    if not callable(val) and not isinstance(val, (property, classmethod, staticmethod)):
                        params[key] = val
                except Exception:
                    pass
        return params

    def _create_result_object(self, result_shape, name: str) -> bpy.types.Object:
        """Convert OCP shape to Blender object."""
        from ..core.ocp_bridge import ocp_to_bl_mesh, ocp_to_bl_point, ocp_to_bl_curve
        from OCP.TopoDS import TopoDS_Vertex

        if result_shape is None:
            raise ValueError("Result shape is None")

        # Detect if it's a point
        try:
            if hasattr(result_shape, 'ShapeType'):
                from OCP.TopAbs import TopAbs_VERTEX
                if result_shape.ShapeType() == TopAbs_VERTEX:
                    from OCP.TopExp import TopExp_Explorer
                    from OCP.TopAbs import TopAbs_VERTEX as TV
                    from OCP.BRep import BRep_Tool
                    explorer = TopExp_Explorer(result_shape, TV)
                    if explorer.More():
                        pnt = BRep_Tool.Pnt(explorer.Current())
                        return ocp_to_bl_point(pnt, name)
        except Exception:
            pass

        # Detect curve vs surface based on GSD command
        from ..core.ocp_bridge import _CURVE_TYPES, _SURFACE_TYPES

        if self.gsd_command in _CURVE_TYPES:
            return ocp_to_bl_curve(result_shape, name)
        else:
            return ocp_to_bl_mesh(result_shape, name)

    def draw(self, context):
        """Standard draw for redo panel."""
        layout = self.layout
        layout.prop(self, "name_override")
        self.draw_parameters(layout, context)

    @classmethod
    def recompute_element(cls, element):
        """Recompute a GsdElement from its stored inputs + parameters.

        Called by the dependency graph when an input changes.
        """
        inputs = [bpy.data.objects[name] for name in element.inputs
                  if name in bpy.data.objects]
        params = element.parameters

        # Create a temporary operator instance
        op = cls()
        op.gsd_command = element.gsd_type

        try:
            result_shape = op.compute_ocp_result(inputs, params)
            if result_shape is not None:
                # Update the existing object's mesh
                op._update_object_mesh(element.bl_object, result_shape)
        except Exception as e:
            print(f"Recompute failed for {element.bl_object.name}: {e}")

    def _update_object_mesh(self, obj, result_shape):
        """Update an existing object's mesh with new OCP result."""
        from OCP.TopoDS import TopoDS_Vertex
        from ..core.ocp_bridge import _triangulate_shape, _store_surface_attributes

        verts, faces = _triangulate_shape(result_shape)

        mesh = obj.data
        mesh.clear_geometry()
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        _store_surface_attributes(obj, result_shape)


# ---------------------------------------------------------------------------
# Operator registration helper
# ---------------------------------------------------------------------------

def register_gsd_operator(cls):
    """Register a GSD operator and its dependency graph entry."""
    gsd_type = getattr(cls, 'gsd_command', None)
    if gsd_type:
        register_operator(gsd_type, cls)
