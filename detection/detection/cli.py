"""Command-line interface for running detection pipelines."""

from __future__ import annotations

import argparse
from pathlib import Path

from detection.core.registry import DetectorRegistry
from detection.pipelines import run_dynamic_pipeline, run_rag_pipeline, run_static_pipeline
from detection.reporting import ReportBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP security detection toolkit.")
    parser.add_argument("target", type=Path, help="Path to the MCP server repository.")
    parser.add_argument("--pipeline", choices=["static", "dynamic", "rag"], default="static")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--policy-dir", type=Path, default=Path("detection/mitigation/policy_templates"))
    args = parser.parse_args()

    registry = DetectorRegistry()
    _load_builtin_plugins(registry)

    if args.pipeline == "static":
        result = run_static_pipeline(args.target, registry, args.policy_dir)
    elif args.pipeline == "dynamic":
        result = run_dynamic_pipeline(args.target, registry)
    else:
        result = run_rag_pipeline(args.target, registry)

    report = ReportBuilder(format_=args.format).render(result)
    print(report)


def _load_builtin_plugins(registry: DetectorRegistry) -> None:
    from detection.plugins.static import python as python_static

    python_static.register(registry)
    # Future phases will import additional plugins here.


if __name__ == "__main__":
    main()
