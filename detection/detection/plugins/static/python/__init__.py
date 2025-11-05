"""Python static analysis plugin placeholder."""

from __future__ import annotations

from pathlib import Path
from typing import List

from detection.core.models import CapabilityFinding, EvidenceSource
from detection.core.registry import DetectorRegistry
from detection.core.session import DetectionSession


def register(registry: DetectorRegistry) -> None:
    """Register Python static detectors with the shared registry."""

    registry.register_detector("static", python_keyword_detector)


def python_keyword_detector(session: DetectionSession) -> List[CapabilityFinding]:
    """Very lightweight keyword-based detector stub."""

    # TODO: Replace with YAML-driven keyword scanning.
    findings: List[CapabilityFinding] = []
    for path in _iter_python_files(session.target_path):
        if "subprocess" in path.read_text(encoding="utf-8", errors="ignore"):
            findings.append(
                CapabilityFinding(
                    name="command_exec",
                    description=f"Potential process execution in {path.name}",
                    score_weight=25.0,
                    confidence=0.3,
                    sources=[EvidenceSource.STATIC],
                    evidence=[str(path)],
                )
            )
    return findings


def _iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        yield path
