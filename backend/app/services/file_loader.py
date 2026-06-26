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
    ".toml"
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


def load_repository_files(repo_path: str):
    documents = []

    repo = Path(repo_path)

    for file in repo.rglob("*"):
        if any(part in IGNORE_DIRS for part in file.parts):
            continue

        if file.suffix not in ALLOWED_EXTENSIONS:
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

            documents.append(
                {
                    "file_path": str(file),
                    "content": content
                }
            )

        except Exception:
            pass

    return documents