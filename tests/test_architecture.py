"""Structural rules of the code after the migration to Reed."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "skyweaver"
REPO_ROOT = PACKAGE_ROOT.parents[1]

SOURCES = sorted(PACKAGE_ROOT.rglob("*.py"))
PYTHON_FILES = SOURCES + sorted(
    path
    for folder in ("tests", "tools", "examples")
    for path in (REPO_ROOT / folder).rglob("*.py")
) + [REPO_ROOT / "experiments.py"]


def module_name(path: Path) -> str:
    parts = path.relative_to(PACKAGE_ROOT.parent).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_no_module_imports_the_old_core() -> None:
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {name}"
        for path in PYTHON_FILES
        for name in imported_modules(path)
        if name == "skyweaver.core" or name.startswith("skyweaver.core.")
    ]
    assert offenders == []
    assert not list((PACKAGE_ROOT / "core").rglob("*.py"))


def test_no_module_reads_is_traversable() -> None:
    offenders = []
    for path in PYTHON_FILES:
        if path == Path(__file__).resolve():
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                "is_traversable",
                "set_restricted",
                "set_available",
            ):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno} {node.attr}")
    assert offenders == []


@pytest.mark.parametrize("path", SOURCES, ids=module_name)
def test_every_module_imports(path: Path) -> None:
    importlib.import_module(module_name(path))
