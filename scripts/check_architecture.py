"""Check import boundaries and glossary names without importing the application."""

import argparse
import ast
import re
from importlib.util import resolve_name
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
GLOSSARY = ROOT / "docs/domain/ubiquitous-language.md"
CONTEXTS = {"Доступ": "access", "Расчёты": "billing", "Прозрачность": "transparency"}
FORBIDDEN_IMPORTS = {
    "asyncpg",
    "fastapi",
    "httpx",
    "psycopg",
    "psycopg2",
    "requests",
    "sqlalchemy",
    "sqlite3",
    "starlette",
    "structlog",
    "uvicorn",
}
FORBIDDEN_SUFFIXES = ("Manager", "Data", "Helper", "Util", "Info", "Processor")


def import_targets(node: ast.Import | ast.ImportFrom, package: str) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    base = node.module or ""
    if node.level:
        base = resolve_name("." * node.level + base, package)
    return [f"{base}.{alias.name}" for alias in node.names]


def boundary_errors(trees: dict[Path, ast.Module]) -> list[str]:
    errors = []
    for path, tree in trees.items():
        parts = path.parts
        if len(parts) < 5 or parts[:2] != ("domprozrachno", "modules"):
            continue
        module, layer = parts[2:4]
        if layer not in {"domain", "application"}:
            continue
        internal = f"domprozrachno.modules.{module}."
        allowed = (internal + "domain.",)
        if layer == "application":
            allowed += (internal + "application.",)
        package = ".".join(parts[:-1])
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for target in import_targets(node, package):
                root = target.split(".")[0]
                if root in FORBIDDEN_IMPORTS or (
                    root == "domprozrachno" and not (target + ".").startswith(allowed)
                ):
                    errors.append(f"{path}:{node.lineno}: {layer} cannot import {target}")
    return errors


def language_errors(trees: dict[Path, ast.Module], glossary: str) -> list[str]:
    errors = []
    definitions: set[tuple[str, str]] = set()
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith(FORBIDDEN_SUFFIXES):
                errors.append(f"{path}:{node.lineno}: forbidden class name {node.name}")
        parts = path.parts
        if len(parts) >= 5 and parts[:2] == ("domprozrachno", "modules") and parts[3] == "domain":
            definitions.update(
                (parts[2], node.name) for node in tree.body if isinstance(node, ast.ClassDef)
            )

    header = "| Термин | Имя в коде | Определение | Контекст | Состояние |"
    _, separator, table = glossary.partition(header)
    if not separator:
        return [*errors, "Glossary terms table is missing"]
    active_terms = 0
    for line in table.strip().splitlines()[1:]:
        if not line.startswith("|"):
            break
        _, name, _, context, state = (cell.strip() for cell in line.split("|")[1:-1])
        if state:
            continue
        active_terms += 1
        if re.fullmatch(r"`[A-Za-z_]\w*`", name) is None or context not in CONTEXTS:
            errors.append(f"Invalid glossary row: {line}")
        elif (CONTEXTS[context], name.strip("`")) not in definitions:
            errors.append(f"{name} is missing from {CONTEXTS[context]}/domain")

    if not active_terms:
        errors.append("Glossary has no implemented terms")
    return errors


def self_test(trees: dict[Path, ast.Module], glossary: str, check: str) -> None:
    model = Path("domprozrachno/modules/billing/domain/models.py")
    if check == "boundaries":
        imports = (
            "import fastapi as framework",
            "from ..infrastructure import adapters",
            "from ...access import application",
            "from sqlalchemy.orm import Session",
        )
        for source in imports:
            assert boundary_errors({**trees, model: ast.parse(source)}), source
        print("Rejected a framework, an adapter, a foreign module and a database import.")
    else:
        changed = glossary.replace("`Charge` |", "`MissingTerm` |", 1)
        assert any("MissingTerm" in error for error in language_errors(trees, changed))
        added = Path("domprozrachno/api/example.py")
        named_badly = {**trees, added: ast.parse("class ChargeManager: pass")}
        assert any("ChargeManager" in error for error in language_errors(named_badly, glossary))
        print("Rejected a missing glossary term and a forbidden class name.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=("boundaries", "language"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    trees = {
        path.relative_to(SOURCE): ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in sorted(SOURCE.rglob("*.py"))
    }
    if not trees:
        parser.error("No application sources found.")
    glossary = GLOSSARY.read_text(encoding="utf-8")
    errors = (
        boundary_errors(trees) if args.check == "boundaries" else language_errors(trees, glossary)
    )
    for error in errors:
        print(error)
    print(f"{args.check}: {len(errors)} errors")
    if not errors and args.self_test:
        self_test(trees, glossary, args.check)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
