"""CATPart Importer — Extract and reproduce CATIA V5 parts in Blender."""
from .catpart_reader import read_catpart, summarize_tree, CatPartFeatureTree, GsmCommand
from .gsm_mapper import map_command_to_catender, get_import_plan, GSM_TO_CATENDER
from .catpart_import_operator import register as register_ops, unregister as unregister_ops

def register():
    register_ops()

def unregister():
    unregister_ops()
