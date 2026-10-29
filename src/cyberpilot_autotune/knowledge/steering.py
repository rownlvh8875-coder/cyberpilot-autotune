"""Explicit revision selection. No live values, latest fallback or policy conversion."""

from ._catalog_data import CATALOGS
from .contracts import KnowledgeRegistry


def get_registry(exact_revision: str) -> KnowledgeRegistry | None:
    """Return audited descriptive data only for an exact, explicitly selected pin."""
    return next((r for r in CATALOGS if r.source_revision == exact_revision), None)
