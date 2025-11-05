"""Dynamic pipeline placeholder for sandbox-driven analysis."""

from __future__ import annotations

from pathlib import Path

from detection.core.models import DetectionResult
from detection.core.registry import DetectorRegistry


def run_dynamic_pipeline(
    target_path: Path,
    registry: DetectorRegistry,
) -> DetectionResult:
    """Placeholder dynamic pipeline to be implemented in Phase 3."""

    raise NotImplementedError("Dynamic pipeline not yet implemented.")
