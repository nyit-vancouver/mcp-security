"""Dynamic analysis plugin namespace."""

from __future__ import annotations

from detection.core.registry import DetectorRegistry


def register(registry: DetectorRegistry) -> None:
    """Register dynamic detectors once sandbox support is available."""

    # Implemented during Phase 3.
    pass
