"""GSD Dependency Graph — Feature dependency tracking and update propagation.

Mirrors CATIA's update mechanism:
  - When an input element is modified, all dependents recompute in order.
  - Topological sort ensures correct evaluation order.
  - "Update" button triggers recomputation of all dirty elements.
"""

import bpy
from typing import Dict, List, Callable, Optional
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Maps GSD type -> operator class (for recompute dispatching)
_OPERATOR_REGISTRY: Dict[str, type] = {}

# Maps object name -> GsdElement
_ELEMENT_REGISTRY: Dict[str, "GsdElement"] = {}  # type: ignore

# Dirty tracking: set of element names that need recomputation
_DIRTY_ELEMENTS: set = set()


def register_operator(gsd_type: str, operator_cls: type):
    """Register an operator class for a GSD command type."""
    _OPERATOR_REGISTRY[gsd_type] = operator_cls


def get_operator_registry() -> Dict[str, type]:
    """Get the operator registry."""
    return _OPERATOR_REGISTRY


def register_element(element: "GsdElement"):
    """Register a GSD element in the dependency graph."""
    from .gsd_element import GsdElement
    if isinstance(element, GsdElement):
        _ELEMENT_REGISTRY[element.bl_object.name] = element


def unregister_element(obj_name: str):
    """Remove an element from the dependency graph."""
    _ELEMENT_REGISTRY.pop(obj_name, None)
    _DIRTY_ELEMENTS.discard(obj_name)


def get_element(obj_name: str) -> Optional["GsdElement"]:
    """Get a registered GSD element by object name."""
    return _ELEMENT_REGISTRY.get(obj_name)


def mark_dirty(obj_name: str):
    """Mark an element as needing recomputation."""
    _DIRTY_ELEMENTS.add(obj_name)


def mark_all_dirty():
    """Mark all elements dirty."""
    _DIRTY_ELEMENTS.update(_ELEMENT_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Dependency graph traversal
# ---------------------------------------------------------------------------

def get_dependents(obj_name: str) -> List[str]:
    """Get all elements that depend on the given element (reverse edges)."""
    dependents = []
    for name, element in _ELEMENT_REGISTRY.items():
        if obj_name in element.inputs:
            dependents.append(name)
    return dependents


def get_direct_dependencies(obj_name: str) -> List[str]:
    """Get all elements the given element depends on (forward edges)."""
    element = _ELEMENT_REGISTRY.get(obj_name)
    if element is None:
        return []
    return list(element.inputs)


def topological_order(entry_points: List[str]) -> List[str]:
    """Compute topological order of a set of elements and their dependencies."""
    # Build adjacency (dependency -> dependent)
    graph: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = defaultdict(int)

    # Collect all nodes in the subgraph
    all_nodes = set(entry_points)
    queue = deque(entry_points)
    while queue:
        node = queue.popleft()
        for dep in get_direct_dependencies(node):
            if dep in _ELEMENT_REGISTRY and dep not in all_nodes:
                all_nodes.add(dep)
                queue.append(dep)
        for dep in get_dependents(node):
            if dep in _ELEMENT_REGISTRY and dep not in all_nodes:
                all_nodes.add(dep)
                queue.append(dep)

    # Build edges
    for node in all_nodes:
        for dep in get_direct_dependencies(node):
            if dep in all_nodes:
                graph[dep].append(node)  # dep -> node
                in_degree[node] += 1

    for node in all_nodes:
        if node not in in_degree:
            in_degree[node] = 0

    # Kahn's algorithm
    result = []
    q = deque([n for n in all_nodes if in_degree[n] == 0])

    while q:
        node = q.popleft()
        result.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                q.append(neighbor)

    if len(result) != len(all_nodes):
        # Cycle detected — try to recover
        remaining = all_nodes - set(result)
        print(f"WARNING: Dependency cycle detected among: {remaining}")
        result.extend(remaining)

    return result


# ---------------------------------------------------------------------------
# Update propagation
# ---------------------------------------------------------------------------

def update_element(obj_name: str) -> bool:
    """Recompute a single element and all of its dependents.

    Returns True if successful, False on error.
    """
    element = _ELEMENT_REGISTRY.get(obj_name)
    if element is None:
        return False

    try:
        element.recompute()
        _DIRTY_ELEMENTS.discard(obj_name)
        return True
    except Exception as e:
        print(f"ERROR recomputing '{obj_name}': {e}")
        return False


def update_all() -> int:
    """Recompute all dirty elements in dependency order.

    Returns the number of elements successfully updated.
    """
    if not _DIRTY_ELEMENTS:
        return 0

    order = topological_order(list(_DIRTY_ELEMENTS))
    updated = 0

    for name in order:
        if name in _DIRTY_ELEMENTS:
            if update_element(name):
                updated += 1

    return updated


def update_from(obj_name: str) -> int:
    """Recompute an element and all downstream dependents.

    Args:
        obj_name: The element that changed.

    Returns:
        Number of elements recomputed.
    """
    element = _ELEMENT_REGISTRY.get(obj_name)
    if element is None:
        return 0

    # Mark this element and all dependents dirty
    mark_dirty(obj_name)
    for dep in get_dependents(obj_name):
        mark_dirty(dep)
        # Recursively mark transitive dependents
        _mark_dependents_recursive(dep)

    return update_all()


def _mark_dependents_recursive(obj_name: str):
    """Recursively mark all transitive dependents dirty."""
    for dep in get_dependents(obj_name):
        if dep not in _DIRTY_ELEMENTS:
            mark_dirty(dep)
            _mark_dependents_recursive(dep)


# ---------------------------------------------------------------------------
# Scene monitoring
# ---------------------------------------------------------------------------

def on_object_update(scene, obj: bpy.types.Object):
    """Handler for object updates — marks dependents dirty."""
    if obj and obj.name in _ELEMENT_REGISTRY:
        mark_dirty(obj.name)
        for dep in get_dependents(obj.name):
            mark_dirty(dep)


def on_object_delete(obj: bpy.types.Object):
    """Handler for object deletion — cleanup."""
    if obj and obj.name in _ELEMENT_REGISTRY:
        unregister_element(obj.name)
        # Mark anything that depended on this dirty
        for name, element in list(_ELEMENT_REGISTRY.items()):
            if obj.name in element.inputs:
                mark_dirty(name)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register():
    """Register dependency graph handlers."""
    # TODO: Add Blender app handlers for dependency tracking
    # bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    pass


def unregister():
    """Clean up."""
    _OPERATOR_REGISTRY.clear()
    _ELEMENT_REGISTRY.clear()
    _DIRTY_ELEMENTS.clear()
