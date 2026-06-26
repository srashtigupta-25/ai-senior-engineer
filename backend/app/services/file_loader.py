import ast
import re
from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".css",
    ".html",
    ".sh",
    ".sql",
    ".env",
    ".example"
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    "__pycache__",
    ".venv",
    "venv",
    "coverage",
    ".pytest_cache",
    ".mypy_cache"
}

MAX_FILE_SIZE = 80000

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".json": "JSON",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".css": "CSS",
    ".html": "HTML",
    ".sh": "Shell",
    ".sql": "SQL",
}


def load_repository_files(repo_path: str):
    documents = []

    repo = Path(repo_path)

    for file in repo.rglob("*"):
        if any(part in IGNORE_DIRS for part in file.parts):
            continue

        if file.suffix not in ALLOWED_EXTENSIONS and file.name not in {"Dockerfile", ".env.example"}:
            continue

        if not file.is_file():
            continue

        try:
            if file.stat().st_size > MAX_FILE_SIZE:
                continue

            content = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if len(content.strip()) < 50:
                continue

            relative_path = file.relative_to(repo)
            symbols = extract_symbols(
                content,
                file.suffix
            )

            documents.append(
                {
                    "file_path": str(relative_path),
                    "absolute_path": str(file),
                    "content": content,
                    "language": LANGUAGE_BY_EXTENSION.get(file.suffix, file.suffix.lstrip(".") or file.name),
                    "line_count": len(content.splitlines()),
                    "symbols": symbols
                }
            )

        except Exception:
            pass

    return documents


def extract_symbols(content: str, suffix: str):
    if suffix == ".py":
        return extract_python_symbols(content)

    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return extract_javascript_symbols(content)

    return []


def extract_python_symbols(content: str):
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    symbols = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            symbols.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(f"def {node.name}")

    return symbols


def extract_javascript_symbols(content: str):
    patterns = [
        r"\bexport\s+default\s+function\s+([A-Za-z0-9_]+)",
        r"\bexport\s+function\s+([A-Za-z0-9_]+)",
        r"\bfunction\s+([A-Za-z0-9_]+)",
        r"\b(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\(",
        r"\bclass\s+([A-Za-z0-9_]+)",
    ]

    symbols = []

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            symbols.append(match.group(1))

    return list(dict.fromkeys(symbols))
