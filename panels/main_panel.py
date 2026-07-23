"""CATIA GSD Main Panel — clean Blender N-Panel UI following SurfacePsycho patterns."""
import bpy

# ===========================================================================
# MAIN PANEL
# ===========================================================================

class GSD_PT_MainPanel(bpy.types.Panel):
    bl_idname = "GSD_PT_MainPanel"
    bl_label = "CATIA GSD"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GSD"

    def draw(self, context):
        pass  # Parent panel — sub-panels contain the actual UI


# ===========================================================================
# WIREFRAME
# ===========================================================================

class GSD_PT_Wireframe(bpy.types.Panel):
    bl_idname = "GSD_PT_Wireframe"
    bl_parent_id = "GSD_PT_MainPanel"
    bl_label = "Wireframe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GSD"

    def draw(self, context):
        layout = self.layout
        if context.mode != "OBJECT":
            layout.label(text="Switch to Object Mode")
            return

        row = layout.row(align=True)
        row.operator("gsd.point", text="Point", icon="DOT")
        row.operator("gsd.line", text="Line", icon="MOD_LINEART")
        row.operator("gsd.plane", text="Plane", icon="MESH_PLANE")

        row = layout.row(align=True)
        row.operator("gsd.circle", text="Circle", icon="MESH_CIRCLE")
        row.operator("gsd.spline", text="Spline", icon="RNDCURVE")
        row.operator("gsd.helix", text="Helix", icon="FORCE_LENNARDJONES")

        row = layout.row(align=True)
        row.operator("gsd.spiral", text="Spiral", icon="FORCE_TURBULENCE")
        row.operator("gsd.spine", text="Spine", icon="MOD_SIMPLE_DEFORM")
        row.operator("gsd.polyline", text="Polyline", icon="OUTLINER_OB_CURVE")

        row = layout.row(align=True)
        row.operator("gsd.corner", text="Corner", icon="SPHERECURVE")
        row.operator("gsd.connect_curve", text="Connect", icon="IPO_EASE_IN_OUT")
        row.operator("gsd.conic", text="Conic", icon="MESH_CAPSULE")

        row = layout.row(align=True)
        row.operator("gsd.projection", text="Project", icon="MOD_MIRROR")
        row.operator("gsd.combine", text="Combine", icon="MOD_BOOLEAN")
        row.operator("gsd.intersection", text="Intersect", icon="MOD_BOOLEAN")

        row = layout.row(align=True)
        row.operator("gsd.reflect_line", text="Reflect", icon="MOD_MIRROR")
        row.operator("gsd.parallel_curve", text="Parallel", icon="MOD_ARRAY")
        row.operator("gsd.curve_3d_offset", text="3D Offset", icon="MOD_OFFSET")

        row = layout.row(align=True)
        row.operator("gsd.point_repetition", text="PtRepeat", icon="MOD_ARRAY")
        row.operator("gsd.extremum", text="Extremum", icon="SORT_ASC")
        row.operator("gsd.axis", text="Axis", icon="EMPTY_AXIS")


# ===========================================================================
# SURFACES
# ===========================================================================

class GSD_PT_Surfaces(bpy.types.Panel):
    bl_idname = "GSD_PT_Surfaces"
    bl_parent_id = "GSD_PT_MainPanel"
    bl_label = "Surfaces"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GSD"

    def draw(self, context):
        layout = self.layout
        if context.mode != "OBJECT":
            layout.label(text="Switch to Object Mode")
            return

        row = layout.row(align=True)
        row.operator("gsd.extrude", text="Extrude", icon="MOD_SOLIDIFY")
        row.operator("gsd.revolve", text="Revolve", icon="DRIVER_ROTATIONAL")
        row.operator("gsd.sphere_surface", text="Sphere", icon="MESH_UVSPHERE")

        row = layout.row(align=True)
        row.operator("gsd.cylinder_surface", text="Cylinder", icon="MESH_CYLINDER")
        row.operator("gsd.offset", text="Offset", icon="MOD_OFFSET")
        row.operator("gsd.sweep", text="Sweep", icon="MOD_CURVE")

        row = layout.row(align=True)
        row.operator("gsd.loft", text="Loft", icon="SURFACE_NSURFACE")
        row.operator("gsd.fill", text="Fill", icon="SURFACE_NCURVE")
        row.operator("gsd.blend", text="Blend", icon="IPO_EASE_IN_OUT")

        row = layout.row(align=True)
        row.operator("gsd.var_offset", text="VarOffset", icon="MOD_OFFSET")
        row.operator("gsd.rough_offset", text="RoughOffs", icon="MOD_OFFSET")


# ===========================================================================
# OPERATIONS
# ===========================================================================

class GSD_PT_Operations(bpy.types.Panel):
    bl_idname = "GSD_PT_Operations"
    bl_parent_id = "GSD_PT_MainPanel"
    bl_label = "Operations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GSD"

    def draw(self, context):
        layout = self.layout
        if context.mode != "OBJECT":
            layout.label(text="Switch to Object Mode")
            return

        row = layout.row(align=True)
        row.operator("gsd.join", text="Join", icon="ADD")
        row.operator("gsd.healing", text="Healing", icon="TOOL_SETTINGS")
        row.operator("gsd.untrim", text="Untrim", icon="UV_SYNC_SELECT")

        row = layout.row(align=True)
        row.operator("gsd.split", text="Split", icon="MOD_BOOLEAN")
        row.operator("gsd.trim", text="Trim", icon="MOD_BOOLEAN")
        row.operator("gsd.sew", text="Sew", icon="MOD_SOLIDIFY")

        row = layout.row(align=True)
        row.operator("gsd.disassemble", text="Disassemble", icon="MOD_EXPLODE")
        row.operator("gsd.extrapolate", text="Extrapolate", icon="MOD_ARRAY")
        row.operator("gsd.invert", text="Invert", icon="NORMALS_FACE")

        row = layout.row(align=True)
        row.operator("gsd.near", text="Near", icon="DOT")
        row.operator("gsd.fillet", text="Fillet", icon="SPHERECURVE")


# ===========================================================================
# TRANSFORM
# ===========================================================================

class GSD_PT_Transform(bpy.types.Panel):
    bl_idname = "GSD_PT_Transform"
    bl_parent_id = "GSD_PT_MainPanel"
    bl_label = "Transform"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GSD"

    def draw(self, context):
        layout = self.layout
        if context.mode != "OBJECT":
            layout.label(text="Switch to Object Mode")
            return

        row = layout.row(align=True)
        row.operator("gsd.translate", text="Translate", icon="EXPORT")
        row.operator("gsd.rotate", text="Rotate", icon="DRIVER_ROTATIONAL")
        row.operator("gsd.symmetry", text="Symmetry", icon="MOD_MIRROR")

        row = layout.row(align=True)
        row.operator("gsd.scaling", text="Scaling", icon="FULLSCREEN_ENTER")
        row.operator("gsd.affinity", text="Affinity", icon="MOD_LATTICE")

        layout.separator()
        layout.label(text="Patterns")
        row = layout.row(align=True)
        row.operator("gsd.rectangular_pattern", text="Rect", icon="MOD_ARRAY")
        row.operator("gsd.circular_pattern", text="Circ", icon="FORCE_TURBULENCE")
        row.operator("gsd.user_pattern", text="User", icon="MOD_ARRAY")
        row.operator("gsd.explode", text="Explode", icon="MOD_EXPLODE")


# ===========================================================================
# TOOLS
# ===========================================================================

class GSD_PT_Tools(bpy.types.Panel):
    bl_idname = "GSD_PT_Tools"
    bl_parent_id = "GSD_PT_MainPanel"
    bl_label = "Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GSD"

    def draw(self, context):
        layout = self.layout
        if context.mode != "OBJECT":
            layout.label(text="Switch to Object Mode")
            return

        layout.label(text="Analysis")
        row = layout.row(align=True)
        row.operator("gsd.connect_checker", text="Connect", icon="MOD_WIREFRAME")
        row.operator("gsd.draft_analysis", text="Draft", icon="MOD_MULTIRES")
        row.operator("gsd.curvature_analysis", text="Curvature", icon="RNDCURVE")

        row = layout.row(align=True)
        row.operator("gsd.porcupine", text="Porcupine", icon="OUTLINER_DATA_CURVE")
        row.operator("gsd.distance_analysis", text="Distance", icon="DRIVER_DISTANCE")
        row.operator("gsd.surface_curvature", text="SurfCurv", icon="SURFACE_NSURFACE")

        row = layout.row(align=True)
        row.operator("gsd.highlight", text="Highlight", icon="LIGHT_SPOT")
        row.operator("gsd.deviation", text="Deviation", icon="DRIVER_DISTANCE")
        row.operator("gsd.feature_identification", text="FeatID", icon="VIEWZOOM")

        layout.separator()
        layout.label(text="Manage")
        row = layout.row(align=True)
        row.operator("gsd.axis_system", text="Axis", icon="EMPTY_AXIS")
        row.operator("gsd.working_support", text="WorkPlane", icon="MESH_PLANE")
        row.operator("gsd.geometric_set", text="GeoSet", icon="OUTLINER_COLLECTION")

        row = layout.row(align=True)
        row.operator("gsd.update", text="Update", icon="FILE_REFRESH")
        row.operator("gsd.delete_useless", text="Clean", icon="TRASH")
        row.operator("gsd.power_copy", text="PwrCopy", icon="DUPLICATE")
        row.operator("gsd.user_feature", text="UsrFeat", icon="PREFERENCES")


# ===========================================================================
# Registration
# ===========================================================================

_panel_classes = [
    GSD_PT_MainPanel,
    GSD_PT_Wireframe,
    GSD_PT_Surfaces,
    GSD_PT_Operations,
    GSD_PT_Transform,
    GSD_PT_Tools,
]


def register():
    for cls in _panel_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_panel_classes):
        bpy.utils.unregister_class(cls)
