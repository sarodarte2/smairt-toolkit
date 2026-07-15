#!/usr/bin/env python3
"""Validate SMAIRT's public documentation and repository presentation."""

from __future__ import annotations

import re
import struct
import sys
import tomllib
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DESCRIPTION = (
    "A scientific method framework that helps researchers use AI while preserving evidence, "
    "provenance, and human judgment."
)
REPOSITORY_URL = "https://github.com/sarodarte2/smairt-toolkit"
UPSTREAM_URL = "https://github.com/PNNL-CompBio/smairt-template"

ROOT_DOCUMENTS = (
    "README.md",
    "ACKNOWLEDGMENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
)
REQUIRED_PATHS = (
    *ROOT_DOCUMENTS,
    "docs/README.md",
    "docs/getting-started/installation.md",
    "docs/getting-started/quickstart.md",
    "docs/guides/research-workflow.md",
    "docs/guides/integrations.md",
    "docs/guides/hpc.md",
    "docs/guides/troubleshooting.md",
    "docs/concepts/scientific-workflow.md",
    "docs/concepts/architecture.md",
    "docs/concepts/safety.md",
    "docs/reference/cli.md",
    "docs/reference/harnesses.md",
    "docs/development/developer-guide.md",
    "docs/development/release.md",
    "examples/enzyme-kinetics-demo/README.md",
    "docs/assets/social-preview.png",
)
REMOVED_PATHS = (
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "QUICKSTART.md",
    "TUTORIAL.md",
    "DEMO.md",
    "REPO_MAP.md",
    "docs/assets/demo.cast",
    "docs/harnesses/antigravity-feasibility.md",
)
UPSTREAM_LINK_ALLOWLIST = {
    Path("README.md"),
    Path("ACKNOWLEDGMENTS.md"),
    Path("scripts/validate_docs.py"),
    Path("src/smairt/scaffold.py"),
}
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".svg", ".sh"}
IGNORED_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "build", "dist"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_SOURCE_RE = re.compile(r"\b(?:src|href)=[\"']([^\"']+)[\"']")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")


def _relative(path: Path) -> Path:
    """Return a repository-relative path for stable diagnostics."""
    return path.resolve().relative_to(ROOT)


def _without_fenced_code(text: str) -> str:
    """Replace fenced code with blank lines while preserving line positions."""
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            output.append("")
        elif fence is None:
            output.append(line)
        else:
            output.append("")
    return "\n".join(output)


def _public_markdown() -> list[Path]:
    """Return narrative Markdown documents governed by heading conventions."""
    paths = [ROOT / name for name in ROOT_DOCUMENTS]
    paths.extend(sorted((ROOT / "docs").rglob("*.md")))
    paths.append(ROOT / "examples/enzyme-kinetics-demo/README.md")
    return paths


def _linked_markdown() -> list[Path]:
    """Return Markdown sources whose local links must resolve."""
    paths = _public_markdown()
    paths.extend(sorted((ROOT / ".github").glob("*.md")))
    paths.extend(sorted((ROOT / "examples/enzyme-kinetics-demo").glob("*.md")))
    return sorted(set(paths))


def _iter_text_files() -> list[Path]:
    """Return repository text files relevant to public identity checks."""
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix in TEXT_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
    ]


def _link_destination(source: Path, raw: str) -> Path | None:
    """Resolve one local Markdown or HTML link, or return None for a remote URL."""
    candidate = raw.strip().split(maxsplit=1)[0].strip("<>")
    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        return None
    path_text = unquote(parsed.path)
    if not path_text:
        return source
    if path_text.startswith("/"):
        return ROOT / path_text.lstrip("/")
    return (source.parent / path_text).resolve()


def _local_links(source: Path) -> list[Path]:
    """Resolve all local Markdown and HTML links outside fenced code blocks."""
    text = _without_fenced_code(source.read_text(encoding="utf-8"))
    raw_links = LINK_RE.findall(text) + HTML_SOURCE_RE.findall(text)
    return [target for raw in raw_links if (target := _link_destination(source, raw)) is not None]


def _check_required_structure(errors: list[str]) -> None:
    """Check canonical and intentionally removed repository paths."""
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required documentation: {relative}")
    for relative in REMOVED_PATHS:
        if (ROOT / relative).exists():
            errors.append(f"retired documentation still exists: {relative}")


def _check_headings(errors: list[str]) -> None:
    """Require one H1 and a non-skipping heading hierarchy in public documents."""
    for path in _public_markdown():
        if not path.exists():
            continue
        headings: list[tuple[int, int]] = []
        for line_number, line in enumerate(
            _without_fenced_code(path.read_text(encoding="utf-8")).splitlines(), start=1
        ):
            if match := HEADING_RE.match(line):
                headings.append((len(match.group(1)), line_number))
        relative = _relative(path)
        h1_count = sum(level == 1 for level, _ in headings)
        if h1_count != 1:
            errors.append(f"{relative}: expected exactly one H1, found {h1_count}")
        if headings and headings[0][0] != 1:
            errors.append(f"{relative}:{headings[0][1]}: first heading must be H1")
        previous = 0
        for level, line_number in headings:
            if previous and level > previous + 1:
                errors.append(
                    f"{relative}:{line_number}: heading level jumps from H{previous} to H{level}"
                )
            previous = level

    expected_harness_sections = [
        "Audience fit",
        "Prerequisites",
        "Setup",
        "Generated files",
        "Capabilities",
        "Limitations",
        "Official references",
    ]
    for path in sorted((ROOT / "docs/reference/harnesses").glob("*.md")):
        sections = [
            line.removeprefix("## ")
            for line in _without_fenced_code(path.read_text(encoding="utf-8")).splitlines()
            if line.startswith("## ")
        ]
        if sections != expected_harness_sections:
            errors.append(f"{_relative(path)}: harness sections are not standardized")


def _check_links_and_index(errors: list[str]) -> None:
    """Check local destinations and reachability from the documentation hub."""
    edges: dict[Path, set[Path]] = defaultdict(set)
    for source in _linked_markdown():
        if not source.exists():
            continue
        for target in _local_links(source):
            try:
                relative_target = _relative(target)
            except ValueError:
                errors.append(f"{_relative(source)}: local link escapes the repository: {target}")
                continue
            if not target.exists():
                errors.append(f"{_relative(source)}: missing local link target: {relative_target}")
                continue
            if target.suffix == ".md":
                edges[_relative(source)].add(relative_target)

    documentation = {path.relative_to(ROOT) for path in (ROOT / "docs").rglob("*.md")}
    reached: set[Path] = set()
    pending = [Path("docs/README.md")]
    while pending:
        current = pending.pop()
        if current in reached:
            continue
        reached.add(current)
        pending.extend(target for target in edges[current] if target in documentation)
    for missing in sorted(documentation - reached):
        errors.append(f"documentation is not reachable from docs/README.md: {missing}")


def _check_identity_and_claims(errors: list[str]) -> None:
    """Check terminology, repository ownership, and unverified-demo language."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if CANONICAL_DESCRIPTION not in " ".join(readme.split()):
        errors.append("README.md: canonical repository description is missing")
    if "research preview" not in readme.lower():
        errors.append("README.md: research-preview status is missing")

    for path in _iter_text_files():
        text = path.read_text(encoding="utf-8")
        relative = _relative(path)
        if UPSTREAM_URL in text and relative not in UPSTREAM_LINK_ALLOWLIST:
            errors.append(f"{relative}: stale template URL outside an upstream-origin statement")

    demo_files = [
        path
        for path in (ROOT / "examples/enzyme-kinetics-demo").iterdir()
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    ]
    prohibited = {
        "independently checked": re.compile(r"independently checked", re.IGNORECASE),
        "independently verified": re.compile(r"independently verified", re.IGNORECASE),
        "verified demo": re.compile(r"verified (?:local )?demo", re.IGNORECASE),
        "release gate": re.compile(r"release[- ]gate", re.IGNORECASE),
    }
    for path in demo_files:
        text = path.read_text(encoding="utf-8")
        for label, pattern in prohibited.items():
            if pattern.search(text):
                errors.append(f"{_relative(path)}: prohibited demo claim: {label}")
    demo_readme = (ROOT / "examples/enzyme-kinetics-demo/README.md").read_text(encoding="utf-8")
    if "Status: unverified" not in demo_readme:
        errors.append("examples/enzyme-kinetics-demo/README.md: unverified status is missing")
    demo_script = (ROOT / "examples/enzyme-kinetics-demo/run-demo.sh").read_text(encoding="utf-8")
    if "non-validating smoke example" not in demo_script:
        errors.append("examples/enzyme-kinetics-demo/run-demo.sh: non-validating label is missing")


def _check_metadata(errors: list[str]) -> None:
    """Check package metadata and public repository routes."""
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if metadata.get("version") != "0.2.0-beta.3":
        errors.append("pyproject.toml: research-preview version must remain 0.2.0-beta.3")
    if metadata.get("authors"):
        errors.append("pyproject.toml: authorship must remain unset pending review")
    expected_urls = {
        "Repository": REPOSITORY_URL,
        "Documentation": f"{REPOSITORY_URL}/tree/main/docs",
        "Issues": f"{REPOSITORY_URL}/issues",
        "Changelog": f"{REPOSITORY_URL}/blob/main/CHANGELOG.md",
    }
    if metadata.get("urls") != expected_urls:
        errors.append("pyproject.toml: public project URLs do not match the canonical repository")
    issue_config = (ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
    if REPOSITORY_URL not in issue_config or UPSTREAM_URL in issue_config:
        errors.append(".github/ISSUE_TEMPLATE/config.yml: support routes are not canonical")


def _check_visuals_and_diagrams(errors: list[str]) -> None:
    """Check diagram count plus SVG dimensions and accessible labels."""
    mermaid_count = sum(
        path.read_text(encoding="utf-8").count("```mermaid")
        for path in ROOT.rglob("*.md")
        if not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
    )
    if mermaid_count != 3:
        errors.append(f"expected exactly three Mermaid diagrams, found {mermaid_count}")

    dimensions = {
        "docs/assets/smairt-banner.svg": ("1200", "300", "0 0 1200 300"),
        "docs/assets/smairt-mark.svg": ("128", "128", "0 0 128 128"),
        "docs/assets/social-preview.svg": ("1280", "640", "0 0 1280 640"),
    }
    for relative, expected in dimensions.items():
        # These are repository-owned, fixed SVG assets rather than external XML input.
        root = ET.parse(ROOT / relative).getroot()  # noqa: S314
        if (root.get("width"), root.get("height"), root.get("viewBox")) != expected:
            errors.append(f"{relative}: width, height, or viewBox is not canonical")
        if root.get("role") != "img" or root.get("aria-labelledby") != "title desc":
            errors.append(f"{relative}: accessible image metadata is incomplete")
        children = {child.tag.rsplit("}", 1)[-1]: child for child in root}
        if children.get("title") is None or children.get("desc") is None:
            errors.append(f"{relative}: title and description elements are required")

    png = (ROOT / "docs/assets/social-preview.png").read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n" or len(png) < 24:
        errors.append("docs/assets/social-preview.png: expected a valid PNG file")
    elif struct.unpack(">II", png[16:24]) != (1280, 640):
        errors.append("docs/assets/social-preview.png: expected exact 1280 by 640 dimensions")


def validate_repository() -> list[str]:
    """Return every documentation validation error without stopping at the first one."""
    errors: list[str] = []
    _check_required_structure(errors)
    _check_headings(errors)
    _check_links_and_index(errors)
    _check_identity_and_claims(errors)
    _check_metadata(errors)
    _check_visuals_and_diagrams(errors)
    return errors


def main() -> int:
    """Print validation results and return a shell-friendly status code."""
    errors = validate_repository()
    if errors:
        print("Documentation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
