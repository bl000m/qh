"""Guard every inner module, including type-only imports and relative imports."""

import ast
from importlib.util import resolve_name
from pathlib import Path
import subprocess
import sys

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = API_ROOT / "app"
STDLIB = {"__future__", "dataclasses", "enum", "typing"}
LAYERS = {
    "core": {"app.core"},
    "policy": {"app.core", "app.policy"},
    "projections": {"app.core", "app.projections"},
    "chat": {"app.core", "app.policy", "app.projections", "app.chat"},
}


def boundary_violations(source: str, package: str, allowed: set[str]) -> list[str]:
    violations = []
    for node in ast.walk(ast.parse(source)):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                try:
                    module = resolve_name("." * node.level + (node.module or ""), package)
                except (ImportError, ValueError):
                    violations.append("invalid relative import")
                    continue
            else:
                module = node.module or ""
            modules = [module]
            # Resolve imported children too: 'from app import adapters' must fail.
            if module == "app" or node.module is None:
                modules = [f"{module}.{alias.name}" for alias in node.names]
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                violations.append("dynamic code/import")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                violations.append("dynamic import")
        for module in modules:
            if module in STDLIB:
                continue
            if not any(module == prefix or module.startswith(prefix + ".") for prefix in allowed):
                violations.append(module)
    return violations


INNER_FILES = [
    path for layer in LAYERS for path in (APP_ROOT / layer).rglob("*.py")
] + [APP_ROOT / "composition.py", APP_ROOT / "__init__.py"]


@pytest.mark.parametrize("path", INNER_FILES, ids=lambda p: str(p.relative_to(APP_ROOT)))
def test_inner_modules_obey_dependency_direction(path: Path) -> None:
    relative = path.relative_to(APP_ROOT)
    if relative.parts[0] in LAYERS:
        allowed = LAYERS[relative.parts[0]]
    elif relative.name == "composition.py":
        allowed = set().union(*LAYERS.values())
    else:
        allowed = set()  # Root __init__ must not load infrastructure on import.
    package = ".".join(("app", *relative.parent.parts))
    assert not boundary_violations(path.read_text(), package, allowed), str(relative)


@pytest.mark.parametrize("source", [
    "import fastapi",
    "from graphiti_core import Graphiti",
    "from neo4j import GraphDatabase",
    "from mcp.server import FastMCP",
    "from openai import OpenAI",
    "import anthropic",
    "from ..api import health",
    "from app import adapters",
    "from app.policy.services import PolicyService",
    "if TYPE_CHECKING:\n    from openai import OpenAI",
    "__import__('fastapi')",
    "loader.import_module('fastapi')",
])
def test_guard_rejects_infrastructure_and_outward_core_dependencies(source: str) -> None:
    assert boundary_violations(source, "app.core", LAYERS["core"])


def test_domain_imports_work_without_site_packages_or_frameworks() -> None:
    code = """
import sys
sys.path.insert(0, sys.argv[1])
from app.core.ports import ContextEngine, LLMProvider
from app.core.services import ContextService
from app.policy.services import PolicyService
from app.projections.services import ProjectionService
from app.chat.services import ChatService
from app.composition import ApplicationServices
"""
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", code, str(API_ROOT)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
