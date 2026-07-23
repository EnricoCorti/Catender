"""GSD type definitions and enumerations.

All CATIA GSD parameter enums and type constants.
Matches CATIA V5 GSD command dialog options exactly.
"""

from enum import Enum, auto


# ---------------------------------------------------------------------------
# Continuity levels (G0–G3)
# ---------------------------------------------------------------------------

class Continuity(str, Enum):
    """Surface/curve continuity constraint levels."""
    G0_POINT = "Point"        # Position match only
    G1_TANGENT = "Tangent"    # Equal tangent direction
    G2_CURVATURE = "Curvature"  # Equal curvature value
    G3_ACCELERATION = "Acceleration"  # Equal rate-of-change of curvature

    def __str__(self):
        return self.value


# ---------------------------------------------------------------------------
# Sweep families and sub-types
# ---------------------------------------------------------------------------

class SweepFamily(str, Enum):
    EXPLICIT = "Explicit"
    LINE = "Line"
    CIRCLE = "Circle"
    CONIC = "Conic"


class SweepExplicitSubType(str, Enum):
    REFERENCE_SURFACE = "WithReferenceSurface"
    PULLING_DIRECTION = "WithPullingDirection"
    TWO_GUIDES = "WithTwoGuideCurves"
    TANGENCY_SURFACE = "WithTangencySurface"


class SweepLineSubType(str, Enum):
    TWO_LIMITS = "TwoLimits"
    LIMIT_MIDDLE = "LimitAndMiddle"
    REFERENCE_SURFACE = "WithReferenceSurface"
    REFERENCE_CURVE = "WithReferenceCurve"
    TANGENCY_SURFACE = "WithTangencySurface"
    DRAFT_DIRECTION = "WithDraftDirection"


class SweepCircleSubType(str, Enum):
    THREE_GUIDES = "ThreeGuides"
    TWO_GUIDES_RADIUS = "TwoGuidesAndRadius"
    CENTER_TWO_ANGLES = "CenterAndTwoAngles"
    CENTER_RADIUS = "CenterAndRadius"
    TWO_GUIDES_TANGENCY = "TwoGuidesAndTangencySurface"
    ONE_GUIDE_TANGENCY = "OneGuideAndTangencySurface"


class SweepConicSubType(str, Enum):
    THREE_GUIDES = "ThreeGuides"
    TWO_GUIDES_PARAM = "TwoGuidesAndParameter"
    FOUR_GUIDES_TANGENT = "FourGuidesAndTangentSurface"
    FIVE_GUIDES = "FiveGuides"


# ---------------------------------------------------------------------------
# Positioning modes (for Sweep)
# ---------------------------------------------------------------------------

class PositioningMode(str, Enum):
    NO_POSITIONING = "NoPositioning"
    POSITIONING_AND_ROTATION = "PositioningAndRotation"


class SmoothingMode(str, Enum):
    NO_SMOOTHING = "NoSmoothing"
    MANUAL = "ManualSmoothing"
    AUTOMATIC = "AutomaticSmoothing"


# ---------------------------------------------------------------------------
# Loft coupling modes
# ---------------------------------------------------------------------------

class CouplingMode(str, Enum):
    RATIO = "Ratio"
    TANGENCY = "Tangency"
    TANGENCY_THEN_CURVATURE = "TangencyThenCurvature"
    VERTICES = "Vertices"


# ---------------------------------------------------------------------------
# Fill / Blend continuity per boundary
# ---------------------------------------------------------------------------

class BoundaryContinuity(str, Enum):
    POINT = "Point"
    TANGENT = "Tangent"
    CURVATURE = "Curvature"


# ---------------------------------------------------------------------------
# Fillet types
# ---------------------------------------------------------------------------

class FilletExtremity(str, Enum):
    SMOOTH = "Smooth"
    STRAIGHT = "Straight"
    MAXIMUM = "Maximum"
    MINIMUM = "Minimum"


class FilletPropagation(str, Enum):
    TANGENT = "Tangent"
    MINIMAL = "Minimal"
    INTERSECTION = "Intersection"


# ---------------------------------------------------------------------------
# Point creation types
# ---------------------------------------------------------------------------

class PointCreationType(str, Enum):
    COORDINATES = "Coordinates"
    ON_CURVE = "OnCurve"
    ON_PLANE = "OnPlane"
    ON_SURFACE = "OnSurface"
    CENTER = "CircleSphereCenter"
    TANGENT = "Tangent"
    BETWEEN = "Between"


class DistanceMode(str, Enum):
    GEODESIC = "Geodesic"
    EUCLIDEAN = "Euclidean"


# ---------------------------------------------------------------------------
# Line creation types
# ---------------------------------------------------------------------------

class LineCreationType(str, Enum):
    POINT_POINT = "PointPoint"
    POINT_DIRECTION = "PointDirection"
    ANGLE_NORMAL = "AngleNormal"
    TANGENT = "TangentToCurve"
    NORMAL_TO_SURFACE = "NormalToSurface"
    BISECTING = "Bisecting"


class LineLengthType(str, Enum):
    LENGTH = "Length"
    INFINITE_START = "InfiniteStart"
    INFINITE_END = "InfiniteEnd"
    INFINITE = "Infinite"


# ---------------------------------------------------------------------------
# Plane creation types
# ---------------------------------------------------------------------------

class PlaneCreationType(str, Enum):
    OFFSET = "OffsetFromPlane"
    PARALLEL_THROUGH_POINT = "ParallelThroughPoint"
    ANGLE_NORMAL = "AngleNormalToPlane"
    THREE_POINTS = "ThroughThreePoints"
    TWO_LINES = "ThroughTwoLines"
    POINT_AND_LINE = "ThroughPointAndLine"
    PLANAR_CURVE = "ThroughPlanarCurve"
    NORMAL_TO_CURVE = "NormalToCurve"
    TANGENT_TO_SURFACE = "TangentToSurface"
    EQUATION = "Equation"
    MEAN = "MeanThroughPoints"


# ---------------------------------------------------------------------------
# Circle creation types
# ---------------------------------------------------------------------------

class CircleCreationType(str, Enum):
    CENTER_RADIUS = "CenterRadius"
    CENTER_POINT = "CenterPoint"
    TWO_POINTS_RADIUS = "TwoPointsRadius"
    THREE_POINTS = "ThreePoints"
    CENTER_AXIS = "CenterAxis"
    BITANGENT_RADIUS = "BitangentRadius"
    BITANGENT_POINT = "BitangentPoint"
    TRITANGENT = "Tritangent"
    CENTER_TANGENT = "CenterTangent"


# ---------------------------------------------------------------------------
# Spline types
# ---------------------------------------------------------------------------

class SplineType(str, Enum):
    THROUGH_POINTS = "ThroughPoints"
    CONTROL_POINTS = "ControlPoints"
    NEAR_POINTS = "NearPoints"


# ---------------------------------------------------------------------------
# Spiral types
# ---------------------------------------------------------------------------

class SpiralType(str, Enum):
    ANGLE_RADIUS = "AngleRadius"
    ANGLE_PITCH = "AnglePitch"
    RADIUS_PITCH = "RadiusPitch"


class SpiralOrientation(str, Enum):
    CLOCKWISE = "Clockwise"
    COUNTER_CLOCKWISE = "CounterClockwise"


# ---------------------------------------------------------------------------
# Helix parameters
# ---------------------------------------------------------------------------

class HelixOrientation(str, Enum):
    CLOCKWISE = "Clockwise"
    COUNTER_CLOCKWISE = "CounterClockwise"


# ---------------------------------------------------------------------------
# Projection types
# ---------------------------------------------------------------------------

class ProjectionDirectionType(str, Enum):
    NORMAL = "Normal"
    ALONG_DIRECTION = "AlongDirection"


# ---------------------------------------------------------------------------
# Reflect line types
# ---------------------------------------------------------------------------

class ReflectLineType(str, Enum):
    CYLINDRICAL = "Cylindrical"
    CONICAL = "Conical"


# ---------------------------------------------------------------------------
# Parallel curve types
# ---------------------------------------------------------------------------

class ParallelMode(str, Enum):
    EUCLIDEAN = "Euclidean"
    GEODESIC = "Geodesic"


class ParallelCornerType(str, Enum):
    SHARP = "Sharp"
    ROUND = "Round"


# ---------------------------------------------------------------------------
# Transform / Pattern enums
# ---------------------------------------------------------------------------

class RepeatMode(str, Enum):
    ABSOLUTE = "Absolute"
    RELATIVE = "Relative"


class RadialAlignment(str, Enum):
    RADIAL = "Radial"
    ALIGN_TO_INSTANCE = "AlignToInstance"


class PatternSpacingMode(str, Enum):
    CONSTANT_SPACING = "ConstantSpacing"
    CONSTANT_SPACING_FROM_END = "ConstantSpacingFromEnd"


# ---------------------------------------------------------------------------
# Trim / Split options
# ---------------------------------------------------------------------------

class TrimOption(str, Enum):
    NO_TRIM = "NoTrim"
    TRIMMED = "Trimmed"
    TRIMMED_AND_ASSEMBLE = "TrimmedAndAssemble"


class TrimMode(str, Enum):
    NO_TRIM = "NoTrim"
    TRIM_BOTH = "TrimBoth"
    TRIM_FIRST = "TrimFirst"
    TRIM_SECOND = "TrimSecond"


class PropagationMode(str, Enum):
    NO_PROPAGATION = "NoPropagation"
    TANGENT_PROPAGATION = "TangentPropagation"
    POINT_PROPAGATION = "PointPropagation"
    COMPLETE_PROPAGATION = "CompletePropagation"


# ---------------------------------------------------------------------------
# Offset parameters
# ---------------------------------------------------------------------------

class ExtrapolateContinuity(str, Enum):
    TANGENT = "Tangent"
    CURVATURE = "Curvature"


class ExtrapolateLimitType(str, Enum):
    LENGTH = "Length"
    UNTIL_ELEMENT = "UntilElement"


class ExtrapolateExtremity(str, Enum):
    NORMAL = "Normal"
    TANGENT = "Tangent"


# ---------------------------------------------------------------------------
# Law types
# ---------------------------------------------------------------------------

class LawType(str, Enum):
    CONSTANT = "Constant"
    LINEAR = "Linear"
    S_TYPE = "S-Type"
    ADVANCED = "Advanced"


# ---------------------------------------------------------------------------
# Analysis enums
# ---------------------------------------------------------------------------

class CheckType(str, Enum):
    G0 = "G0"
    G1 = "G1"
    G2 = "G2"
    G3 = "G3"


class DraftDisplayMode(str, Enum):
    COLOR_SCALE = "ColorScale"
    COLOR_SCALE_AND_VALUE = "ColorScaleAndValue"


class CurvatureAnalysisType(str, Enum):
    CURVATURE = "Curvature"
    RADIUS_OF_CURVATURE = "RadiusOfCurvature"


class SurfaceCurvatureType(str, Enum):
    GAUSSIAN = "Gaussian"
    MEAN = "Mean"
    MIN = "Min"
    MAX = "Max"
    ABSOLUTE = "Absolute"
    NORMAL = "Normal"


class DistanceMeasureType(str, Enum):
    MINIMUM_DISTANCE = "MinimumDistance"
    MAXIMUM_DISTANCE = "MaximumDistance"
    ALONG_DIRECTION = "AlongDirection"
    BAND_ANALYSIS = "BandAnalysis"


class FeatureIDType(str, Enum):
    FILLET = "Fillet"
    HOLE = "Hole"
    CHAMFER = "Chamfer"
    PAD = "Pad"
    POCKET = "Pocket"


# ---------------------------------------------------------------------------
# Join / Federation
# ---------------------------------------------------------------------------

class FederationMode(str, Enum):
    ALL = "All"
    NONE = "None"
    WITHOUT_PROPAGATION = "WithoutPropagation"


# ---------------------------------------------------------------------------
# Disassemble modes
# ---------------------------------------------------------------------------

class DisassembleMode(str, Enum):
    DOMAINS = "Domains"
    CELLS = "Cells"
    ALL_CELLS = "AllCells"


# ---------------------------------------------------------------------------
# Untrim modes
# ---------------------------------------------------------------------------

class UntrimMode(str, Enum):
    ALL = "All"
    SELECTIVE = "Selective"


# ---------------------------------------------------------------------------
# Axis System types
# ---------------------------------------------------------------------------

class AxisSystemType(str, Enum):
    STANDARD = "Standard"
    AXIS_ROTATION = "AxisRotation"
    EULER_ANGLES = "EulerAngles"


# ---------------------------------------------------------------------------
# Variable radius variation mode
# ---------------------------------------------------------------------------

class VariationMode(str, Enum):
    LINEAR = "Linear"
    CUBIC = "Cubic"
