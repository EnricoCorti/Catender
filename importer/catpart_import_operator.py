"""CATPart Import Operator — Import CATIA V5 parts into Blender via Catender."""
import bpy
import os
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper


class CATPART_OT_Import(Operator, ImportHelper):
    """Import a CATIA V5 CATPart file into Blender using Catender operators."""
    bl_idname = "catpart.import"
    bl_label = "Import CATPart"
    bl_description = "Import CATIA V5 part file, extracting its GSM feature tree"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".CATPart"
    filter_glob: StringProperty(default="*.CATPart", options={'HIDDEN'})
    
    create_dependencies: BoolProperty(
        name="Create Dependencies",
        description="Recreate the full feature dependency tree",
        default=True,
    )
    
    skip_unknown: BoolProperty(
        name="Skip Unknown Commands",
        description="Skip commands that cannot be mapped to Catender",
        default=True,
    )
    
    def execute(self, context):
        filepath = self.filepath
        filename = os.path.basename(filepath)
        
        # Import the reader and mapper
        from .catpart_reader import read_catpart, summarize_tree
        from .gsm_mapper import get_import_plan, stats as mapper_stats
        
        # Read the CATPart
        self.report({'INFO'}, f"Reading {filename}...")
        try:
            tree = read_catpart(filepath)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read CATPart: {e}")
            return {'CANCELLED'}
        
        # Print summary to console
        print(summarize_tree(tree))
        
        # Get import plan
        plan = get_import_plan(tree)
        st = mapper_stats(tree)
        
        print(f"Import plan: {st['mapped']} commands mapped to {st['unique_operators']} Catender operators")
        print(f"Skipped: {st['skipped']} parameter-only commands")
        
        # Create a collection for this import
        collection_name = os.path.splitext(filename)[0]
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)
        
        # Store feature tree info as scene property
        context.scene['catpart_import'] = {
            'filename': filename,
            'commands_total': st['total'],
            'commands_mapped': st['mapped'],
            'operators_used': st['unique_operators'],
        }
        
        # Report each command for debugging
        for i, step in enumerate(plan):
            op_id = step['operator_id']
            params = step['parameters']
            catia_type = step['catia_type']
            print(f"  [{i+1}/{len(plan)}] {catia_type} -> {op_id}: {params}")
        
        # EXECUTE GEOMETRY RECONSTRUCTION
        if self.create_dependencies and plan:
            from .reconstructor import SequentialReconstructor
            recon = SequentialReconstructor(collection_name)
            result = recon.execute_plan(plan)
            
            self.report(
                {'INFO'},
                f"Created {result['ok']} features from {filename} ({result['fail']} skipped)"
            )
        else:
            self.report(
                {'INFO'},
                f"Scanned {filename}: {st['mapped']}/{st['total']} commands"
            )
        
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "create_dependencies")
        layout.prop(self, "skip_unknown")


class CATPART_OT_ImportMultiple(Operator):
    """Batch import multiple CATPart files."""
    bl_idname = "catpart.import_multiple"
    bl_label = "Import CATPart Folder"
    bl_description = "Import all CATPart files from a folder"
    bl_options = {'REGISTER', 'UNDO'}
    
    directory: StringProperty(subtype='DIR_PATH')
    
    def execute(self, context):
        import glob
        catparts = glob.glob(os.path.join(self.directory, "*.CATPart"))
        
        if not catparts:
            self.report({'ERROR'}, f"No CATPart files found in {self.directory}")
            return {'CANCELLED'}
        
        from .catpart_reader import read_catpart
        from .gsm_mapper import get_import_plan, stats as mapper_stats
        
        total_mapped = 0
        total_cmds = 0
        
        for filepath in catparts:
            filename = os.path.basename(filepath)
            try:
                tree = read_catpart(filepath)
                plan = get_import_plan(tree)
                st = mapper_stats(tree)
                total_mapped += st['mapped']
                total_cmds += st['total']
                print(f"  {filename}: {st['mapped']}/{st['total']} mapped")
            except Exception as e:
                print(f"  {filename}: ERROR - {e}")
        
        self.report(
            {'INFO'},
            f"Scanned {len(catparts)} files: {total_mapped}/{total_cmds} commands mapped"
        )
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = [
    CATPART_OT_Import,
    CATPART_OT_ImportMultiple,
]


def menu_import_catpart(self, context):
    """Add CATPart import to File > Import menu."""
    self.layout.operator(CATPART_OT_Import.bl_idname, text="CATIA V5 (.CATPart)")


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import_catpart)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_import_catpart)
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
