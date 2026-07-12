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
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "smairt-project"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write(path: Path, content: str) -> None:
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
    atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def next_numeric_id(paths: list[Path], prefix: str, width: int = 3) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)")
    values: list[int] = []
    for path in paths:
        match = pattern.match(path.name)
        if match:
            values.append(int(match.group(1)))
    return f"{prefix}{max(values, default=0) + 1:0{width}d}"
