"""GSD Add-on Preferences.

Accessible via Edit > Preferences > Add-ons > CATIA GSD.
"""

import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty


class GSDAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]  # "catia_gsd"

    # Default tolerances
    default_modeling_tolerance: FloatProperty(
        name="Default Modeling Tolerance",
        description="Default NURBS precision for new scenes (mm)",
        default=0.001, min=0.00001, max=10.0, precision=6,
    )
    default_angular_tolerance: FloatProperty(
        name="Default Angular Tolerance",
        description="Default angular precision (deg)",
        default=0.5, min=0.001, max=90.0, precision=3,
    )
    default_merging_distance: FloatProperty(
        name="Default Merging Distance",
        description="Default gap tolerance for join/heal (mm)",
        default=0.001, min=0.00001, max=10.0, precision=6,
    )

    # Display
    show_control_polygon: BoolProperty(
        name="Show Control Polygon",
        description="Display NURBS control polygon wireframe",
        default=True,
    )
    control_polygon_color: EnumProperty(
        name="Control Polygon Color",
        items=[
            ('YELLOW', 'Yellow', ''),
            ('WHITE', 'White', ''),
            ('CYAN', 'Cyan', ''),
            ('MAGENTA', 'Magenta', ''),
        ],
        default='YELLOW',
    )

    # Behavior
    auto_update: BoolProperty(
        name="Auto-Update",
        description="Automatically recompute dependents when inputs change",
        default=True,
    )
    live_preview: BoolProperty(
        name="Live Preview",
        description="Show ghost preview during parameter adjustment",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Default Tolerances", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(self, "default_modeling_tolerance")
        col.prop(self, "default_angular_tolerance")
        col.prop(self, "default_merging_distance")

        box = layout.box()
        box.label(text="Display", icon='RESTRICT_VIEW_OFF')
        col = box.column(align=True)
        col.prop(self, "show_control_polygon")
        col.prop(self, "control_polygon_color")

        box = layout.box()
        box.label(text="Behavior", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(self, "auto_update")
        col.prop(self, "live_preview")


def register():
    bpy.utils.register_class(GSDAddonPreferences)


def unregister():
    bpy.utils.unregister_class(GSDAddonPreferences)
