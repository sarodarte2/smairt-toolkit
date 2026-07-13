"""Index and validate Python code for human and machine readability."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import yaml

from smairt.locking import mutating
from smairt.utils import atomic_write, ensure_no_symlink


def _safe_python(root: Path, path: Path) -> Path:
    """Resolve a project-contained Python file without following symlinks."""
    resolved = ensure_no_symlink(root, path)
    if not resolved.is_file() or resolved.suffix != ".py":
        raise ValueError(f"not a project Python file: {path}")
    return resolved


def _python_files(root: Path) -> list[Path]:
    """Discover experiment and shared Python modules while excluding caches."""
    files = list((root / "experiments").glob("EXPERIMENT_*/iterations/ITERATION_*/*.py"))
    files.extend((root / "scripts/shared").rglob("*.py"))
    return sorted(_safe_python(root, path) for path in files if "__pycache__" not in path.parts)


def _literal_constants(tree: ast.Module) -> list[str]:
    """Collect module-level uppercase names that expose configuration landmarks."""
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    names.append(target.id)
    return names


def inspect_python(path: Path, root: Path) -> dict[str, Any]:
    """Return a stable, AST-derived summary without importing research code."""
    root = root.resolve()
    path = _safe_python(root, path)
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(path))
    functions = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [argument.arg for argument in statement.args.args]
            functions.append(
                {
                    "name": statement.name,
                    "arguments": arguments,
                    "typed": all(
                        argument.annotation is not None for argument in statement.args.args
                    )
                    and statement.returns is not None,
                    "documented": bool(ast.get_docstring(statement)),
                }
            )
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return {
        "path": str(path.relative_to(root)),
        "purpose": ast.get_docstring(tree) or "",
        "functions": functions,
        "constants": _literal_constants(tree),
        "imports": sorted(set(imports)),
        "uses_smairt_outputs": "SMAIRT_RESULTS_DIR" in content,
        "uses_smairt_figures": "SMAIRT_FIGURES_DIR" in content,
    }


@mutating("code index")
def build_code_index(root: Path, *, write: bool = True) -> dict[str, Any]:
    """Build the project code index and optionally persist it."""
    modules = [inspect_python(path, root) for path in _python_files(root)]
    payload = {"schema_version": 1, "modules": modules}
    if write:
        atomic_write(root / "scripts/CODE_INDEX.yaml", yaml.safe_dump(payload, sort_keys=False))
    return payload


def validate_code(root: Path, target: Path | None = None) -> list[dict[str, str]]:
    """Return warning-oriented readability findings for research Python files."""
    if target and target.is_file():
        paths = [target]
    elif target and target.is_dir():
        paths = sorted(target.rglob("*.py"))
    else:
        paths = _python_files(root)
    findings: list[dict[str, str]] = []
    for requested in paths:
        try:
            path = _safe_python(root, requested)
            relative = str(path.relative_to(root.resolve()))
            summary = inspect_python(path, root)
        except (OSError, SyntaxError, ValueError) as exc:
            findings.append(
                {
                    "severity": "error",
                    "code": "code.parse",
                    "artifact": str(requested),
                    "message": str(exc),
                }
            )
            continue
        content = path.read_text(encoding="utf-8")
        if not summary["purpose"]:
            findings.append(
                _warning(
                    "code.module_docstring",
                    relative,
                    "Add a module purpose and provenance docstring",
                )
            )
        if not any(item["name"] == "main" for item in summary["functions"]):
            findings.append(
                _warning("code.main", relative, "Add a clear main() execution boundary")
            )
        if "TODO: implement experiment" in content:
            findings.append(
                _warning(
                    "code.placeholder",
                    relative,
                    "Experiment still contains implementation placeholder",
                )
            )
        if path.parent.name.startswith("ITERATION_"):
            if not summary["uses_smairt_outputs"]:
                findings.append(
                    _warning(
                        "code.results_path", relative, "Use SMAIRT_RESULTS_DIR for result artifacts"
                    )
                )
            if "validate" not in content.lower() and "assert " not in content:
                findings.append(
                    _warning(
                        "code.input_validation",
                        relative,
                        "Add explicit input or configuration validation",
                    )
                )
        for function in summary["functions"]:
            if function["name"].startswith("_"):
                continue
            if not function["typed"]:
                findings.append(
                    _warning(
                        "code.type_hints",
                        relative,
                        f"Add complete type hints to {function['name']}()",
                    )
                )
            if function["name"] != "main" and not function["documented"]:
                findings.append(
                    _warning(
                        "code.function_docstring",
                        relative,
                        f"Document the purpose of {function['name']}()",
                    )
                )
    return findings


def _warning(code: str, artifact: str, message: str) -> dict[str, str]:
    """Build one consistently shaped warning for JSON and human output."""
    return {"severity": "warning", "code": code, "artifact": artifact, "message": message}
