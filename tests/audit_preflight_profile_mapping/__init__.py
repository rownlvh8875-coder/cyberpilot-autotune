"""Pure diagnostic mapping only;no target H receipt,reader or runtime bridge."""

from .contracts import (
    MappingReason,
    PreflightMappingDecision,
    PreflightRunBinding,
    SourceDiagnostic,
    TargetGap,
)
from .mapping import map_registered_preflight

__all__ = [
    "MappingReason",
    "PreflightMappingDecision",
    "PreflightRunBinding",
    "SourceDiagnostic",
    "TargetGap",
    "map_registered_preflight",
]
