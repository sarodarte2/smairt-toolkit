"""Fast, local-only suggestions shared by terminal completion surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandSuggestion:
    """Describe one safe action without executing or preloading it."""

    value: str
    label: str
    description: str
    effect: str = "read-only"
    keywords: tuple[str, ...] = ()

    @property
    def search_text(self) -> str:
        """Return normalized text used by Prompt Toolkit fuzzy matching."""
        return " ".join((self.value, self.label, self.description, *self.keywords))


PROJECT_ACTIONS = (
    CommandSuggestion(
        "next",
        "Continue research",
        "Show the recommended bounded action and prompt",
        keywords=("workflow", "recommendation"),
    ),
    CommandSuggestion(
        "references",
        "References",
        "Search, import, inspect, and verify literature",
        effect="may use network",
        keywords=("doi", "zotero", "openalex", "semantic scholar", "pdf"),
    ),
    CommandSuggestion(
        "setup",
        "Project & people",
        "Edit project details and contributor settings",
        effect="changes settings",
        keywords=("configuration", "people", "contributor"),
    ),
    CommandSuggestion(
        "tools",
        "Tools & compute",
        "Manage environment, harness, local connections, and optional HPC",
        effect="changes local setup",
        keywords=("profile", "harness", "conda", "slurm"),
    ),
    CommandSuggestion(
        "health",
        "Health & updates",
        "Validate the project and preview unified maintenance",
        keywords=("doctor", "validate", "repair", "migration", "update"),
    ),
    CommandSuggestion(
        "sharing",
        "Safety & sharing",
        "Inspect safety policy and sharing readiness",
        effect="read-only unless changing mode",
        keywords=("release", "visibility", "strict"),
    ),
    CommandSuggestion("exit", "Return to shell", "Close the SMAIRT menu", keywords=("quit",)),
)


def project_identifiers(root: Path, kind: str) -> list[str]:
    """Return bounded public identifiers without reading protected artifact content."""
    patterns = {
        "reference": (root / "references", "index.yaml"),
        "hypothesis": (root / "hypotheses", "HYPOTHESIS_*.md"),
        "experiment": (root / "experiments", "EXPERIMENT_*"),
        "run": (root / "results", "**/RUN_*/run.json"),
    }
    if kind not in patterns:
        return []
    directory, pattern = patterns[kind]
    if kind == "reference":
        try:
            from smairt.references import load_index

            return [item.id for item in load_index(root)]
        except (OSError, ValueError):
            return []
    if not directory.exists():
        return []
    if kind == "run":
        return sorted(path.parent.name for path in directory.glob(pattern))
    identifiers = []
    for path in directory.glob(pattern):
        parts = path.name.split("_", 2)
        if len(parts) >= 2:
            identifiers.append("_".join(parts[:2]))
    return sorted(identifiers)
