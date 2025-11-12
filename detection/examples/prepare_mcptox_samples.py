"""Split MCPTox pure_tool.json into per-tool JSON files with keyword tags."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

SUSPICIOUS_KEYWORDS: Dict[str, List[str]] = {
    "command_exec": [
        "exec",
        "bash",
        "eval",
        "shell",
        "chmod",
        "chown",
        "rm -rf",
    ],
    "file_read": [
        "~/.ssh",
        "~/.cursor",
        "/etc/passwd",
        "read file",
        "extract",
        "steal",
    ],
    "file_write": [
        "overwrite",
        "write",
        "append",
        "log",
        "modify",
    ],
    "network_outbound": [
        "http://",
        "https://",
        "curl",
        "post",
        "upload",
    ],
    "network_inbound": [
        "listen",
        "webhook",
        "callback",
        "port",
        "server",
    ],
    "env_access": [
        "api key",
        "environment variable",
        "secret",
        "token",
        "credential",
    ],
}


def normalize_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug.lower() or "sample"


def detect_keywords(text: str) -> List[dict]:
    lower = text.lower()
    matches = []
    for capability, keywords in SUSPICIOUS_KEYWORDS.items():
        hit_words = sorted({kw for kw in keywords if kw.lower() in lower})
        if hit_words:
            matches.append({"capability": capability, "keywords": hit_words})
    return matches


def write_sample(base_dir: Path, server: str, key: str, record: dict) -> None:
    folder = base_dir / normalize_slug(server or "unknown")
    folder.mkdir(parents=True, exist_ok=True)
    slug = normalize_slug(key)
    content = record.get("tool_content", "")
    record["high_risk_indicators"] = detect_keywords(content)
    output_path = folder / f"{slug}.json"
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)


def main() -> None:
    src = Path("samples/mcptox/pure_tool.json")
    dst = Path("examples/mcptox_samples")
    if not src.exists():
        raise SystemExit(f"Source file not found: {src}")
    dst.mkdir(parents=True, exist_ok=True)

    with src.open("r", encoding="utf-8") as fh:
        entries = json.load(fh)

    for group in entries:
        for key, record in group.items():
            server = record.get("server_name", "unknown")
            write_sample(dst, server, key, record)

    print(f"Wrote samples to {dst}")


if __name__ == "__main__":
    main()
