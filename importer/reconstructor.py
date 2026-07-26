"""Enhanced CATPart Reconstructor — Sequential dependency resolution.

Since CATPart binary stores feature references in structured Geometric Component
blocks (not inline with GSM commands), we use a sequential tracking approach:
each new command uses the most recently created object of the required input type.
This mirrors how CATIA's specification tree resolves dependencies in order.
"""

import bpy
from typing import Dict, List, Any, Optional

# Type hierarchy for input resolution
# Maps what input types each GSM command category needs
INPUT_TYPES = {
    "Point": [],  # Points are leaf nodes, no inputs needed
    "Line": ["Point", "Direction"],
    "Plane": ["Plane", "Point", "Axis"],
    "Circle": ["Point", "Plane"],
    "Spline": ["Point"],
    "Curve": ["Point", "Curve"],
    "Extrude": ["Curve", "Direction"],
    "Revolve": ["Curve", "Axis"],
    "Sphere": ["Point"],
    "Cylinder": ["Point", "Direction"],
    "Sweep": ["Curve", "Curve"],
    "Loft": ["Curve"],
    "Fill": ["Curve"],
    "Blend": ["Curve"],
    "Split": ["Surface", "Surface"],
    "Trim": ["Surface", "Surface"],
    "Join": ["Surface"],
    "Translate": ["Any", "Direction"],
    "Rotate": ["Any", "Axis"],
    "Symmetry": ["Any", "Plane"],
    "Scaling": ["Any", "Point"],
    "Affinity": ["Any"],
    "Project": ["Curve", "Surface"],
    "Intersect": ["Any", "Any"],
    "Fillet": ["Surface"],
    "Offset": ["Surface"],
    "Near": ["Any", "Point"],
    "Extrapolate": ["Surface"],
    "Axis": ["Any"],
    "Direction": ["Line"],
}


class SequentialReconstructor:
    """Reconstructs CATPart geometry by tracking the last created object
    of each type and using them as inputs for subsequent commands."""
    
    def __init__(self, collection_name: str):
        self.collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(self.collection)
        
        # Track last object of each type
        self.last_of_type: Dict[str, bpy.types.Object] = {}
        # Track all objects
        self.objects: Dict[str, bpy.types.Object] = {}
        # Name counters
        self.counters: Dict[str, int] = {}
        # Log
        self.log: List[Dict] = []
    
    def _next_name(self, catia_type: str) -> str:
        """Generate next name based on CATIA feature type."""
        type_map = {
            "GSMPoint": "Point", "GSMLine": "Line", "GSMPlane": "Plane",
            "GSMCircle": "Circle", "GSMSpline": "Spline", "GSMHelix": "Helix",
            "GSMSpiral": "Spiral", "GSMSpine": "Spine",
            "GSMExtrude": "Extrude", "GSMSphere": "Sphere", "GSMCylinder": "Cylinder",
            "GSMSweep": "Sweep", "GSMLoft": "Loft", "GSMFill": "Fill", "GSMBlend": "Blend",
            "GSMOffset": "Offset",
            "GSMSplit": "Split", "GSMTrim": "Trim", "GSMJoin": "Join", "GSMAssemble": "Join",
            "GSMTranslate": "Translate", "GSMRotate": "Rotate",
            "GSMSymmetry": "Symmetry", "GSMScaling": "Scaling", "GSMAffinity": "Affinity",
            "GSMProject": "Project", "GSMIntersect": "Intersection",
            "GSMFillet": "Fillet", "GSMNear": "Near",
        }
        for prefix, short in type_map.items():
            if catia_type.startswith(prefix):
                c = self.counters.get(short, 0) + 1
                self.counters[short] = c
                return f"{short}.{c}"
        c = self.counters.get("Feature", 0) + 1
        self.counters["Feature"] = c
        return f"Feature.{c}"
    
    def _get_input_object(self, input_type: str) -> Optional[bpy.types.Object]:
        """Get the most recent object of the given input type."""
        if input_type == "Any":
            # Return any available object
            for t in ["Point", "Line", "Plane", "Circle", "Curve", "Surface", "Extrude"]:
                if t in self.last_of_type:
                    return self.last_of_type[t]
            return None
        
        # Category matching
        categories = {
            "Point": ["Point"],
            "Line": ["Line"],
            "Plane": ["Plane"],
            "Curve": ["Line", "Circle", "Spline", "Helix", "Spiral", "Spine", "Curve"],
            "Surface": ["Extrude", "Sphere", "Cylinder", "Sweep", "Loft", "Fill", "Blend", "Offset", "Plane", "Surface"],
            "Direction": ["Line", "Axis"],
            "Axis": ["Axis", "Line"],
            "Any": ["Point", "Line", "Plane", "Circle", "Curve", "Surface", "Extrude"],
        }
        
        types_to_try = categories.get(input_type, [input_type])
        for t in types_to_try:
            if t in self.last_of_type:
                return self.last_of_type[t]
        return None
    
    def _get_catia_category(self, gsm_type: str) -> str:
        """Get the category of a GSM command for tracking."""
        for prefix in ["GSMPoint", "GSMLine", "GSMPlane", "GSMCircle",
                        "GSMSpline", "GSMHelix", "GSMSpiral", "GSMSpine",
                        "GSMExtrude", "GSMSphere", "GSMCylinder", "GSMSweep",
                        "GSMLoft", "GSMFill", "GSMBlend", "GSMOffset",
                        "GSMTranslate", "GSMRotate", "GSMAffinity",
                        "GSMSplit", "GSMTrim", "GSMJoin", "GSMAssemble",
                        "GSMFillet", "GSMNear", "GSMProject", "GSMIntersect"]:
            if gsm_type.startswith(prefix):
                return prefix
        return "GSMOther"
    
    def execute_plan(self, plan: List[Dict]) -> Dict[str, int]:
        """Execute the import plan, creating Blender geometry."""
        ok = 0
        fail = 0
        
        for i, step in enumerate(plan):
            op_id = step['operator_id']
            params = step['parameters']
            catia_type = step['catia_type']
            
            try:
                obj = self._execute_one(op_id, params, catia_type)
                if obj:
                    # Move to collection
                    for c in list(obj.users_collection):
                        c.objects.unlink(obj)
                    self.collection.objects.link(obj)
                    
                    name = self._next_name(catia_type)
                    obj.name = name
                    obj['gsd_type'] = name.split(".")[0]
                    
                    self.objects[name] = obj
                    cat = self._get_catia_category(catia_type)
                    self.last_of_type[cat] = obj
                    # Also store under the short type
                    short = name.split(".")[0]
                    self.last_of_type[short] = obj
                    
                    ok += 1
                    self.log.append({"index": i, "cmd": catia_type, "op": op_id, "result": name, "status": "OK"})
                else:
                    fail += 1
                    self.log.append({"index": i, "cmd": catia_type, "op": op_id, "result": None, "status": "NO_RESULT"})
            except Exception as e:
                fail += 1
                self.log.append({"index": i, "cmd": catia_type, "op": op_id, "status": f"ERROR: {e}"})
        
        print(f"Sequential reconstruction: {ok} OK, {fail} FAIL")
        return {"ok": ok, "fail": fail}
    
    def _execute_one(self, op_id: str, params: Dict, catia_type: str) -> Optional[bpy.types.Object]:
        """Execute a single Catender operator."""
        op_func = self._get_op(op_id)
        if op_func is None:
            return None
        
        # Determine required input types
        cat = self._get_catia_category(catia_type)
        needed = INPUT_TYPES.get(cat.replace("GSM", ""), [])
        
        # Select inputs
        bpy.ops.object.select_all(action='DESELECT')
        input_objs = []
        for itype in needed:
            obj = self._get_input_object(itype)
            if obj:
                obj.select_set(True)
                input_objs.append(obj)
        
        if input_objs:
            bpy.context.view_layer.objects.active = input_objs[0]
        
        # Filter params
        filtered = self._filter_params(op_id, params)
        
        try:
            result = op_func('EXEC_DEFAULT', **filtered)
            if result == {'FINISHED'}:
                return bpy.context.view_layer.objects.active
        except:
            try:
                result = op_func('EXEC_DEFAULT')
                if result == {'FINISHED'}:
                    return bpy.context.view_layer.objects.active
            except:
                pass
        
        return None
    
    def _get_op(self, op_id: str):
        parts = op_id.split(".")
        if len(parts) != 2: return None
        mod = getattr(bpy.ops, parts[0], None)
        if mod is None: return None
        return getattr(mod, parts[1], None)
    
    def _filter_params(self, op_id: str, params: Dict) -> Dict:
        OP_PARAMS = {
            "gsd.point": ["point_type", "x", "y", "z", "ratio", "offset"],
            "gsd.line": ["line_type", "start_length", "end_length", "angle"],
            "gsd.plane": ["plane_type", "offset_distance", "angle"],
            "gsd.circle": ["circle_type", "radius", "start_angle", "end_angle"],
            "gsd.spline": ["spline_type", "closure"],
            "gsd.helix": ["pitch", "height"],
            "gsd.spiral": ["spiral_type", "start_radius", "end_radius"],
            "gsd.spine": [],
            "gsd.extrude": ["limit1", "limit2"],
            "gsd.revolve": ["angle1"],
            "gsd.sphere_surface": ["radius"],
            "gsd.cylinder_surface": ["radius", "length1"],
            "gsd.sweep": ["sweep_family"],
            "gsd.loft": ["coupling"],
            "gsd.fill": ["continuity"],
            "gsd.blend": ["continuity1", "continuity2"],
            "gsd.translate": ["distance"],
            "gsd.rotate": ["angle"],
            "gsd.symmetry": [],
            "gsd.scaling": ["factor"],
            "gsd.affinity": ["x_factor", "y_factor", "z_factor"],
            "gsd.join": ["merging_distance"],
            "gsd.split": [],
            "gsd.trim": [],
            "gsd.sew": ["tolerance"],
            "gsd.fillet": ["fillet_type", "radius"],
            "gsd.near": [],
            "gsd.offset": ["offset_type", "offset_distance"],
            "gsd.projection": [],
            "gsd.intersection": [],
        }
        allowed = set(OP_PARAMS.get(op_id, []))
        return {k: v for k, v in params.items() if k in allowed} if allowed else {}
