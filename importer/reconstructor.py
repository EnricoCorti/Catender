"""CATPart Geometry Reconstructor — Execute CATPart feature tree in Blender.

Takes the mapped GSM→Catender import plan and creates actual 3D geometry
by executing Catender operators in dependency order, tracking created objects
for cross-referencing between commands.
"""

import bpy
from typing import Dict, List, Any, Optional


class ReconstructionContext:
    """Tracks objects created during CATPart reconstruction.
    
    Maps CATIA feature names (e.g., "Point.1", "Line.3") to Blender objects
    so subsequent commands can find their inputs.
    """
    
    def __init__(self, collection: bpy.types.Collection):
        self.collection = collection
        self.objects: Dict[str, bpy.types.Object] = {}  # name -> object
        self.counters: Dict[str, int] = {}  # type -> next number
        self.command_log: List[Dict] = []
    
    def _next_name(self, catia_type: str) -> str:
        """Generate the next Blender name for a feature type."""
        # Map CATIA type to short name
        short_names = {
            "Point": "Point", "Line": "Line", "Plane": "Plane",
            "Circle": "Circle", "Spline": "Spline", "Helix": "Helix",
            "Spiral": "Spiral", "Spine": "Spine",
            "Extrude": "Extrude", "Sphere": "Sphere", "Cylinder": "Cylinder",
            "Sweep": "Sweep", "Loft": "Loft", "Fill": "Fill", "Blend": "Blend",
            "Translate": "Translate", "Rotate": "Rotate",
            "Split": "Split", "Trim": "Trim", "Join": "Join",
        }
        
        # Detect type from GSM command
        for gsm_prefix, short in short_names.items():
            if gsm_prefix in catia_type:
                count = self.counters.get(short, 0) + 1
                self.counters[short] = count
                return f"{short}.{count}"
        
        # Generic fallback
        count = self.counters.get("Feature", 0) + 1
        self.counters["Feature"] = count
        return f"Feature.{count}"
    
    def register_object(self, obj: bpy.types.Object, name: str):
        """Register a created object for future reference."""
        self.objects[name] = obj
        # Also register without number suffix for dependency lookup
        base = name.rsplit(".", 1)[0]
        if base not in self.objects:
            self.objects[base] = obj
    
    def find_input(self, name: str) -> Optional[bpy.types.Object]:
        """Find an input object by name (exact or partial match)."""
        if name in self.objects:
            return self.objects[name]
        # Try base name without number
        if "." in name:
            base = name.split(".")[0]
            if base in self.objects:
                return self.objects[base]
        return None
    
    def select(self, *names: str):
        """Select objects by name for operator input."""
        bpy.ops.object.select_all(action='DESELECT')
        objs = []
        for name in names:
            obj = self.find_input(name)
            if obj:
                obj.select_set(True)
                objs.append(obj)
        if objs:
            bpy.context.view_layer.objects.active = objs[0]
        return objs


def reconstruct_catpart(plan: List[Dict], collection_name: str) -> ReconstructionContext:
    """Execute a CATPart import plan, creating Blender geometry.
    
    Args:
        plan: List of mapped commands from gsm_mapper.get_import_plan().
        collection_name: Name for the Blender collection.
        
    Returns:
        ReconstructionContext with all created objects.
    """
    # Create collection
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    
    ctx = ReconstructionContext(collection)
    
    # Process commands in order (CATParts store them in dependency order)
    success_count = 0
    fail_count = 0
    
    for i, step in enumerate(plan):
        op_id = step['operator_id']
        params = step['parameters']
        catia_type = step['catia_type']
        
        try:
            obj = _execute_operator(ctx, op_id, params, catia_type)
            if obj:
                # Move object to our collection
                for c in obj.users_collection:
                    c.objects.unlink(obj)
                collection.objects.link(obj)
                
                name = ctx._next_name(catia_type)
                obj.name = name
                obj['gsd_type'] = name.split(".")[0]
                ctx.register_object(obj, name)
                
                success_count += 1
                ctx.command_log.append({
                    "index": i,
                    "catia_type": catia_type,
                    "operator": op_id,
                    "params": params,
                    "result": name,
                    "status": "OK",
                })
            else:
                fail_count += 1
                ctx.command_log.append({
                    "index": i,
                    "catia_type": catia_type,
                    "operator": op_id,
                    "params": params,
                    "status": "NO_RESULT",
                })
        except Exception as e:
            fail_count += 1
            ctx.command_log.append({
                "index": i,
                "catia_type": catia_type,
                "operator": op_id,
                "params": params,
                "status": f"ERROR: {e}",
            })
    
    print(f"Reconstruction: {success_count} OK, {fail_count} FAIL, {len(plan)} total")
    return ctx


def _execute_operator(
    ctx: ReconstructionContext,
    op_id: str,
    params: Dict[str, Any],
    catia_type: str
) -> Optional[bpy.types.Object]:
    """Execute a single Catender operator and return the created object."""
    
    # Get the operator function
    op_func = _get_operator(op_id)
    if op_func is None:
        print(f"  Unknown operator: {op_id}")
        return None
    
    # Select inputs based on the command type
    _select_inputs(ctx, catia_type, params)
    
    # Prepare filtered params (remove non-operator properties)
    filtered_params = _filter_params(op_id, params)
    
    # Execute the operator
    try:
        result = op_func('EXEC_DEFAULT', **filtered_params)
        if result == {'FINISHED'}:
            # Return the newly created active object
            return bpy.context.view_layer.objects.active
    except Exception as e:
        # Try with fewer params
        try:
            result = op_func('EXEC_DEFAULT')
            if result == {'FINISHED'}:
                return bpy.context.view_layer.objects.active
        except:
            pass
    
    return None


def _get_operator(op_id: str):
    """Get the Blender operator function from its id."""
    parts = op_id.split(".")
    if len(parts) != 2:
        return None
    module_name, op_name = parts
    module = getattr(bpy.ops, module_name, None)
    if module is None:
        return None
    return getattr(module, op_name, None)


def _select_inputs(ctx: ReconstructionContext, catia_type: str, params: Dict):
    """Select appropriate input objects for the command."""
    # Map of GSM commands to their input parameter names
    input_params = {
        "GSMPointCoord": [],
        "GSMPointOnCurve": ["Curve"],
        "GSMPointOnPlane": ["Plane"],
        "GSMPointOnSurface": ["Surface"],
        "GSMPointBetween": ["Point1", "Point2"],
        "GSMPointCenter": ["Element"],
        "GSMPointTangent": ["Curve"],
        "GSMLinePtPt": ["Point1", "Point2"],
        "GSMLinePtDir": ["Point"],
        "GSMLineAngle": ["Curve", "Point"],
        "GSMLineNormal": ["Surface", "Point"],
        "GSMPlaneOffset": ["Plane"],
        "GSMPlaneAngle": ["Plane", "Axis"],
        "GSMPlaneThreePoints": ["Point1", "Point2", "Point3"],
        "GSMCircleCtrRad": ["Center", "Support"],
        "GSMCircleCenterAxisRadius": ["Center", "Axis"],
        "GSMCircleBitangentRadRadius": ["Element1", "Element2"],
        "GSMExtrude": ["Profile", "Direction"],
        "GSMSphere": ["Center"],
        "GSMSweep": ["Profile", "Guide"],
        "GSMTranslate": ["Element", "Direction"],
        "GSMRotate": ["Element", "Axis"],
        "GSMAffinity": ["Element", "AxisSystem"],
        "GSMSplit": ["ElementToCut", "CuttingElement"],
        "GSMTrim": ["Element1", "Element2"],
        "GSMIntersect": ["Element1", "Element2"],
        "GSMExtrapol": ["Surface", "Edge"],
        "GSMAssemble": ["Elements"],
        "GSMProject": ["Element", "Support"],
        "GSMNear": ["Element"],
        "GSMAxisToAxis": [],
    }
    
    # Find the matching input parameter list
    input_names = []
    for prefix, names in input_params.items():
        if catia_type.startswith(prefix):
            input_names = names
            break
    
    if not input_names:
        return
    
    # Select the inputs
    select_names = []
    for name in input_names:
        if name in params:
            obj = ctx.find_input(params[name])
            if obj:
                select_names.append(obj.name)
    
    if select_names:
        ctx.select(*select_names)


def _filter_params(op_id: str, params: Dict) -> Dict:
    """Filter params to only those accepted by the operator."""
    # Map operators to their accepted parameter names
    OPERATOR_PARAMS = {
        "gsd.point": ["point_type", "x", "y", "z", "ratio", "offset"],
        "gsd.line": ["line_type", "start_length", "end_length", "angle", "length_type"],
        "gsd.plane": ["plane_type", "offset_distance", "angle"],
        "gsd.circle": ["circle_type", "radius", "start_angle", "end_angle"],
        "gsd.spline": ["spline_type", "closure"],
        "gsd.helix": ["pitch", "height", "orientation", "taper_angle", "starting_angle"],
        "gsd.spiral": ["spiral_type", "start_radius", "end_radius", "end_angle", "nb_revolutions"],
        "gsd.spine": [],
        "gsd.extrude": ["limit1", "limit2"],
        "gsd.revolve": ["angle1"],
        "gsd.sphere_surface": ["radius"],
        "gsd.cylinder_surface": ["radius", "length1"],
        "gsd.sweep": ["sweep_family"],
        "gsd.loft": ["coupling", "relimitation"],
        "gsd.fill": ["continuity"],
        "gsd.blend": ["continuity1", "continuity2", "tension1", "tension2"],
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
    
    allowed = set(OPERATOR_PARAMS.get(op_id, []))
    if not allowed:
        return {}  # No params accepted
    
    return {k: v for k, v in params.items() if k in allowed}
