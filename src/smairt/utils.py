"""Filesystem, hashing, and serialization helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    """Convert user text into a stable, filesystem-safe lowercase slug."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "smairt-project"


def sha256_file(path: Path) -> str:
    """Stream a file into SHA-256 without loading large research files into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of UTF-8 text for managed-file tracking."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write(path: Path, content: str) -> None:
    """Replace a text file atomically so interrupted writes cannot corrupt state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write deterministic, human-readable JSON through the atomic writer."""
    atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def next_numeric_id(paths: list[Path], prefix: str, width: int = 3) -> str:
    """Return the next zero-padded ID after scanning existing artifact names."""
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)")
    values: list[int] = []
    for path in paths:
        match = pattern.match(path.name)
        if match:
            values.append(int(match.group(1)))
    return f"{prefix}{max(values, default=0) + 1:0{width}d}"
