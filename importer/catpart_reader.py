"""CATPart Reader — Extract GSM feature trees from CATIA V5 binary files.

CATPart files (V5 format) contain ASCII-embedded GSM (Generative Shape Design)
command identifiers and their parameters. This module scans the binary, extracts
all GSM commands, and structures them into a feature tree.
"""

import re
import struct
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class GsmParameter:
    """A single parameter of a GSM command."""
    name: str
    value: str  # Raw string value from binary


@dataclass
class GsmCommand:
    """A single GSM feature command extracted from a CATPart."""
    catia_type: str  # e.g., "GSMPointCoord", "GSMLinePtPt", "GSMExtrude"
    position: int     # Byte offset in file
    parameters: List[GsmParameter] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)  # Referenced feature names
    raw_context: bytes = field(default=b'')


@dataclass
class CatPartFeatureTree:
    """Complete feature tree extracted from a CATPart file."""
    filename: str
    file_size: int
    commands: List[GsmCommand] = field(default_factory=list)
    body_structure: Dict[str, List[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# GSM Command definitions
# ---------------------------------------------------------------------------

# Known GSM command types and their parameter names
GSM_COMMANDS = {
    # Points
    "GSMPoint": ["Type", "X", "Y", "Z"],
    "GSMPointCoord": ["Type", "X", "Y", "Z", "RefPoint", "AxisSystem"],
    "GSMPointOnCurve": ["Type", "Curve", "Distance", "Ratio", "Offset", "Orientation"],
    "GSMPointOnPlane": ["Type", "Plane", "X", "Y"],
    "GSMPointOnSurface": ["Type", "Surface", "Direction", "Distance"],
    "GSMPointBetween": ["Type", "Point1", "Point2", "Ratio"],
    "GSMPointCenter": ["Type", "Element"],
    "GSMPointTangent": ["Type", "Curve", "Direction"],
    
    # Lines
    "GSMLine": ["Type"],
    "GSMLinePtPt": ["Type", "Point1", "Point2", "StartLength", "EndLength"],
    "GSMLinePtDir": ["Type", "Point", "Direction", "StartLength", "EndLength"],
    "GSMLineAngle": ["Type", "Curve", "Point", "Angle", "StartLength", "EndLength"],
    "GSMLineNormal": ["Type", "Surface", "Point", "StartLength", "EndLength"],
    "GSMLineBiTangent": ["Type", "Line1", "Line2"],
    
    # Planes
    "GSMPlane": ["Type"],
    "GSMPlaneOffset": ["Type", "Plane", "Offset", "Reverse"],
    "GSMPlaneAngle": ["Type", "Plane", "Axis", "Angle"],
    "GSMPlaneThreePoints": ["Type", "Point1", "Point2", "Point3"],
    
    # Circles
    "GSMCircle": ["Type"],
    "GSMCircleCtrRad": ["Type", "Center", "Support", "Radius", "StartAngle", "EndAngle"],
    "GSMCircleCenterAxisRadius": ["Type", "Center", "Axis", "Radius"],
    "GSMCircleBitangentRadRadius": ["Type", "Element1", "Element2", "Support", "Radius"],
    
    # Surfaces
    "GSMExtrude": ["Profile", "Direction", "Limit1", "Limit2"],
    "GSMSphere": ["Center", "Radius"],
    "GSMSweep": ["Profile", "Guide", "Angle"],
    
    # Transforms
    "GSMTranslate": ["Element", "Direction", "Distance"],
    "GSMRotate": ["Element", "Axis", "Angle"],
    "GSMAffinity": ["Element", "AxisSystem", "XFactor", "YFactor", "ZFactor"],
    
    # Operations
    "GSMSplit": ["ElementToCut", "CuttingElement", "Orientation"],
    "GSMTrim": ["Element1", "Element2", "Orientation1", "Orientation2"],
    "GSMIntersect": ["Element1", "Element2"],
    "GSMExtrapol": ["Surface", "Edge", "Limit", "Continuity"],
    
    # Other
    "GSMAssemble": ["Elements", "MergingDistance"],
    "GSMProject": ["Element", "Support", "Direction"],
    "GSMNear": ["Element", "ReferencePoint"],
}


def read_catpart(filepath: str) -> CatPartFeatureTree:
    """Read a CATPart file and extract its GSM feature tree.
    
    Args:
        filepath: Path to the .CATPart file.
        
    Returns:
        CatPartFeatureTree with all extracted commands.
    """
    import os
    
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    tree = CatPartFeatureTree(filename=filename, file_size=file_size)
    
    # Extract body structure (PartBody, GeometricalSet, etc.)
    body_markers = [b'PartBody', b'GeometricalSet', b'Body']
    for marker in body_markers:
        positions = []
        pos = 0
        while True:
            p = data.find(marker, pos)
            if p == -1:
                break
            # Extract the name that follows the marker
            end = data.find(b'\x00', p)
            name = data[p:end].decode('ascii', errors='replace') if end > 0 else marker.decode()
            positions.append(name)
            pos = p + 1
        if positions:
            tree.body_structure[marker.decode()] = positions
    
    # Extract all GSM commands
    gsm_pattern = re.compile(rb'GSM[A-Z][a-zA-Z]+')
    seen_positions = set()
    
    for match in gsm_pattern.finditer(data):
        cmd_name = match.group().decode('ascii')
        pos = match.start()
        
        # Avoid duplicates (same command at same position)
        if pos in seen_positions:
            continue
        seen_positions.add(pos)
        
        # Extract context around the command (next ~200 bytes)
        end = min(len(data), pos + 300)
        context = data[pos:end]
        
        cmd = GsmCommand(
            catia_type=cmd_name,
            position=pos,
            raw_context=context,
        )
        
        # Try to extract parameters
        _extract_parameters(cmd, context)
        
        # Try to find input references
        _extract_inputs(cmd, context)
        
        tree.commands.append(cmd)
    
    return tree


def _extract_parameters(cmd: GsmCommand, context: bytes):
    """Extract named parameters from the command context block."""
    # Parameters are usually ASCII strings separated by null bytes
    # after the GSM command name
    
    # Skip the command name itself
    name_len = len(cmd.catia_type.encode())
    param_data = context[name_len:]
    
    # Find ASCII strings that look like parameter names and values
    parts = param_data.split(b'\x00')
    
    for part in parts:
        try:
            text = part.decode('ascii').strip()
            if not text or len(text) < 2:
                continue
            
            # Skip binary garbage
            if any(c < 32 and c != 0 for c in part):
                continue
            
            # Identify parameter name-value pairs
            # Pattern: ParamName followed by value
            if len(text) > 3 and text[0].isupper():
                # Check if there's a known parameter name
                base_cmd = _get_base_command(cmd.catia_type)
                if base_cmd in GSM_COMMANDS:
                    known_params = GSM_COMMANDS[base_cmd]
                    for pname in known_params:
                        if text.startswith(pname):
                            # The value follows the same part or next part
                            if len(text) > len(pname):
                                value = text[len(pname):].strip('= :')
                            else:
                                value = text
                            cmd.parameters.append(GsmParameter(name=pname, value=value))
                            break
        except:
            pass


def _extract_inputs(cmd: GsmCommand, context: bytes):
    """Try to find input feature references."""
    # Look for patterns like "Point.1", "Line.2", "Plane.3"
    input_pattern = re.compile(rb'(Point|Line|Plane|Circle|Spline|Extrude|Sphere|Sweep|Plane|Axis)\x00*\.\x00*\d+')
    matches = input_pattern.findall(context)
    for match in matches:
        try:
            if isinstance(match, tuple):
                name = match[0].decode('ascii')
            else:
                name = match.decode('ascii')
            if name not in cmd.inputs:
                cmd.inputs.append(name)
        except:
            pass


def _get_base_command(full_cmd: str) -> str:
    """Get the base command type from a parameter-specific name.
    
    E.g., "GSMPointCoordValues" -> "GSMPoint"
          "GSMLinePtPtLinePtPtLengths" -> "GSMLinePtPt"
    """
    # Strip trailing modifiers
    for base in GSM_COMMANDS:
        if full_cmd.startswith(base) and len(full_cmd) > len(base):
            # Check if the remainder is just modifiers (Values, Type, etc.)
            remainder = full_cmd[len(base):]
            if remainder in ('Values', 'Type', 'Angle', 'Radius', 'Limits',
                            'ProjectionMode', 'DiameterMode', 'Trim', 'AxisComputation'):
                return base
    return full_cmd



def extract_udfs(filepath: str) -> list:
    """Extract User Defined Feature (GSMTool) definitions from a CATPart.
    
    Returns list of dicts with: name, commands, publications, position
    """
    import os
    filename = os.path.basename(filepath)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Search for GSMTool in hex bytes
    gsm_hex = b'GSMTool'
    udfs = []
    pos = 0
    
    while True:
        idx = data.find(gsm_hex, pos)
        if idx == -1:
            break
        
        # Extract context
        start = max(0, idx - 50)
        end = min(len(data), idx + 500)
        ctx_bytes = data[start:end]
        ctx_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx_bytes)
        
        # Extract name
        name = "Unnamed"
        name_match = __import__('re').search(r'GSMTool\.(\w+)', ctx_text)
        if name_match:
            name = name_match.group(1)
        
        # Extract GSM commands
        cmd_matches = __import__('re').findall(r'GSM[A-Z][a-zA-Z]+', ctx_text)
        commands = list(set(cmd_matches))
        
        # Extract publications (inputs/outputs)
        pub_matches = __import__('re').findall(r'(?:Publication|INPUT|ResultOUT)\.?(\w*)', ctx_text)
        pubs = [p for p in pub_matches if p]
        
        udfs.append({
            'file': filename,
            'name': name,
            'position': idx,
            'commands': commands,
            'publications': pubs,
            'context': ctx_text[:300]
        })
        
        pos = idx + 1
    
    return udfs

def summarize_tree(tree: CatPartFeatureTree) -> str:
    """Generate a human-readable summary of the feature tree."""
    lines = []
    lines.append(f"=== {tree.filename} ({tree.file_size/1024:.0f} KB) ===")
    lines.append(f"Commands: {len(tree.commands)}")
    
    # Categorize
    categories = {}
    for cmd in tree.commands:
        cat = _categorize(cmd.catia_type)
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    for cat, count in sorted(categories.items()):
        lines.append(f"  {cat}: {count}")
    
    # Body structure
    if tree.body_structure:
        lines.append("Body structure:")
        for body, names in tree.body_structure.items():
            for name in names:
                lines.append(f"  {body}: {name}")
    
    return "\n".join(lines)


def _categorize(cmd_name: str) -> str:
    """Categorize a GSM command."""
    if 'Point' in cmd_name: return "Point"
    if cmd_name.startswith('GSMLine'): return "Line"
    if cmd_name.startswith('GSMPlane'): return "Plane"
    if cmd_name.startswith('GSMCircle'): return "Circle"
    if any(s in cmd_name for s in ['Spline','Corner','Connect','Conic','Helix','Spiral','Spine']): return "Curve"
    if any(s in cmd_name for s in ['Extrude','Revolve','Sphere','Cylinder','Offset','Sweep','Loft','Fill','Blend']): return "Surface"
    if any(s in cmd_name for s in ['Translate','Rotate','Symmetr','Scal','Affinit']): return "Transform"
    if any(s in cmd_name for s in ['Join','Split','Trim','Sew','Fillet','Extrapo','Healing','Assemble']): return "Operation"
    if any(s in cmd_name for s in ['Intersect','Project','Near']): return "Projection"
    return "Other"
