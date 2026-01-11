"""Definitions for Topological Intent and Steering."""

from enum import Enum, auto
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TopologyFamily(str, Enum):
    """
    primary topological families that PlaneBrane can generate.

    These represent the fundamental class of the output manifold.
    """

    PLANAR_RELIEF = "planar_relief"  # Default: Standard heightmap
    TOROIDAL = "toroidal"  # Closed loop, donut-like
    SPHEROID = "spheroid"  # Sphere-like, closed surface
    HELICAL = "helical"  # Spirals, solenoids, vortices
    LATTICE_RESONATOR = "lattice_resonator"  # Grid-based, discrete nodes
    COMPACTIFIED_FOLDED = "compactified"  # Calabi-Yau-like, high curvature internal folding
    KLEIN_BOTTLE = "klein_bottle"  # Non-orientable (Use with extreme caution; orientation_rule must NOT be PRESERVE)


class PhaseBehavior(str, Enum):
    """
    Describes how the phase of the pattern behaves over the geometry.
    """

    STATIC = "static"  # Phase is fixed to surface coordinates (Standard)
    FLOWING = "flowing"  # Phase implies motion/direction vector
    QUANTIZED = "quantized"  # Phase snaps to discrete values (Grid/Lattice)


class OrientationRule(str, Enum):
    """Rules for surface normal orientation."""

    PRESERVE = "preserve"  # Strict orientability
    ALLOW_FLIP = "allow_flip"  # Allow normal flips
    MOBIUS_TWIST = "mobius_twist"  # Intentionally introduce one twist


class BoundaryCondition(str, Enum):
    """Edge behavior for the manifold."""

    OPEN = "open"  # Edges are distinct
    CLOSED_LOOP = "closed_loop"  # Edges meet (seam)
    COMPACTIFIED = "compactified"  # Dimensions wrap internally


class Dimensionality(str, Enum):
    """Embedding target dimension."""

    DIM_3D = "3d"
    PSEUDO_4D = "pseudo_4d"


from pydantic import ConfigDict

class SteeringProfile(BaseModel):
    """
    Configuration for steering the topological outcome.

    This acts as a constraint and permission set for the geometry engine.
    """

    model_config = ConfigDict(use_enum_values=True)

    allowed_families: List[TopologyFamily] = Field(
        default_factory=lambda: [
            TopologyFamily.PLANAR_RELIEF,
            TopologyFamily.TOROIDAL,
            TopologyFamily.SPHEROID,
            TopologyFamily.HELICAL,
        ]
    )
    force_family: Optional[TopologyFamily] = None

    phase_behavior: PhaseBehavior = Field(default=PhaseBehavior.STATIC)

    orientation_rule: OrientationRule = Field(default=OrientationRule.PRESERVE)
    boundary_condition: BoundaryCondition = Field(default=BoundaryCondition.CLOSED_LOOP)
    dimensionality: Dimensionality = Field(default=Dimensionality.DIM_3D)

    @field_validator("force_family", mode="after")
    @classmethod
    def force_family_must_be_allowed(cls, v, info):
        if v is not None and "allowed_families" in info.data:
            allowed = info.data.get("allowed_families", [])
            allowed_values = {a.value if isinstance(a, TopologyFamily) else str(a) for a in allowed}
            v_value = v.value if isinstance(v, TopologyFamily) else str(v)
            if v_value not in allowed_values:
                raise ValueError("force_family must be in allowed_families")
        return v

    @model_validator(mode="after")
    def check_orientation_conflicts(self):
        if self.force_family is not None and self.orientation_rule is not None:
            ff_val = self.force_family.value if isinstance(self.force_family, TopologyFamily) else str(self.force_family)
            or_val = self.orientation_rule.value if isinstance(self.orientation_rule, OrientationRule) else str(self.orientation_rule)
            if ff_val == TopologyFamily.KLEIN_BOTTLE.value and or_val == OrientationRule.PRESERVE.value:
                raise ValueError("KLEIN_BOTTLE cannot be produced when orientation_rule == PRESERVE")
        return self

    # Legacy config class removed; use model_config above
