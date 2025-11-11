"""Run static detection on each MCPTox sample individually."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

from detection.core.models import DetectionResult
from detection.core.registry import DetectorRegistry
from detection.pipelines import run_static_pipeline
from detection.plugins.static import metadata as metadata_static
from detection.plugins.static import python as python_static
from detection.rules import RuleBook, load_rulebook

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = PROJECT_ROOT / "detection" / "rules" / "keywords.toml"
POLICY_DIR = PROJECT_ROOT / "detection" / "mitigation" / "policy_templates"
SAMPLES_DIR = PROJECT_ROOT / "examples" / "mcptox_samples"
OUTPUT_FILE = SAMPLES_DIR / "per_file_detection.jsonl"
SUMMARY_FILE = SAMPLES_DIR / "per_file_detection_summary.json"

EXCLUDE_FILES = {
    "detection_summary.json",
    "high_risk_keywords_summary.json",
    "per_file_detection.jsonl",
    "per_file_detection_summary.json",
}


def _build_registry() -> DetectorRegistry:
    registry = DetectorRegistry()
    rulebook = load_rulebook(RULES_FILE)
    python_static.register(registry, rulebook)
    metadata_static.register(registry, rulebook)
    return registry


def _evaluate_sample(sample_path: Path, registry: DetectorRegistry) -> DetectionResult:
    with tempfile.TemporaryDirectory(prefix="mcptox-sample-") as temp_dir:
        temp_dir_path = Path(temp_dir)
        target_dir = temp_dir_path / "target"
        target_dir.mkdir()
        shutil.copy2(sample_path, target_dir / sample_path.name)
        result = run_static_pipeline(target_dir, registry, POLICY_DIR)

    for finding in result.findings:
        remapped: List[str] = []
        for entry in finding.evidence:
            parts = entry.split(":", 1)
            snippet = parts[1] if len(parts) == 2 else entry
            remapped.append(f"{sample_path}:{snippet}")
        finding.evidence = remapped
        finding.metadata = {"files": [str(sample_path)]}
    result.notes = None
    result.server_name = sample_path.name
    return result


def _serialize_result(result: DetectionResult, sample_path: Path) -> Dict[str, object]:
    return {
        "sample": str(sample_path.relative_to(PROJECT_ROOT)),
        "risk_level": result.risk_level,
        "total_score": result.total_score,
        "findings": [
            {
                "name": finding.name,
                "confidence": finding.confidence,
                "score_weight": finding.score_weight,
                "evidence": list(finding.evidence),
            }
            for finding in result.findings
        ],
    }


def main() -> None:
    if not SAMPLES_DIR.exists():
        raise SystemExit(f"Samples directory not found: {SAMPLES_DIR}")

    registry = _build_registry()
    samples = sorted(
        path
        for path in SAMPLES_DIR.rglob("*.json")
        if path.name not in EXCLUDE_FILES
    )
    if not samples:
        raise SystemExit("No sample files found.")

    OUTPUT_FILE.unlink(missing_ok=True)

    coverage: Dict[str, int] = {}
    with OUTPUT_FILE.open("w", encoding="utf-8") as fh:
        for sample_path in samples:
            result = _evaluate_sample(sample_path, registry)
            for finding in result.findings:
                coverage[finding.name] = coverage.get(finding.name, 0) + 1
            serialized = _serialize_result(result, sample_path)
            data = json.loads(sample_path.read_text(encoding="utf-8"))
            serialized["high_risk_indicators"] = data.get("high_risk_indicators", [])
            fh.write(json.dumps(serialized, ensure_ascii=False))
            fh.write("\n")

    summary_payload = {
        "samples": len(samples),
        "capability_coverage": coverage,
        "output": str(OUTPUT_FILE.relative_to(PROJECT_ROOT)),
    }
    SUMMARY_FILE.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    print(f"Analyzed {len(samples)} samples. Results saved to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
