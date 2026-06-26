import json
from collections import Counter
from pathlib import Path
from typing import Any


STATE_FILE = Path(__file__).resolve().parents[2] / ".repository_state.json"


def save_repository_state(repo_info: dict[str, Any], files: list[dict[str, Any]], chunks_count: int):
    languages = Counter(
        file["language"]
        for file in files
    )

    directories = Counter()

    for file in files:
        path = Path(file["file_path"])
        top_level = path.parts[0] if len(path.parts) > 1 else "."
        directories[top_level] += 1

    repository_type, classification_evidence = classify_repository(files)

    state = {
        "repository": {
            "repo_name": repo_info["repo_name"],
            "repo_url": repo_info.get("repo_url", ""),
            "repo_path": repo_info["repo_path"],
        },
        "detected_repository_type": repository_type,
        "classification_evidence": classification_evidence,
        "files_indexed": len(files),
        "chunks_stored": chunks_count,
        "languages": dict(languages.most_common()),
        "top_level_directories": dict(directories.most_common(20)),
        "files": [
            {
                "file_path": file["file_path"],
                "language": file["language"],
                "line_count": file["line_count"],
                "symbols": file["symbols"][:20],
            }
            for file in files
        ],
    }

    STATE_FILE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )

    return state


def load_repository_state():
    if not STATE_FILE.exists():
        return None

    return json.loads(
        STATE_FILE.read_text(encoding="utf-8")
    )


def get_repository_facts():
    state = load_repository_state()

    if not state:
        return {
            "repo_name": "unknown",
            "repository_type": "unknown",
            "classification_evidence": [],
            "files": [],
        }

    return {
        "repo_name": state["repository"]["repo_name"],
        "repository_type": state.get("detected_repository_type", "unknown"),
        "classification_evidence": state.get("classification_evidence", []),
        "files": state.get("files", []),
    }


def build_repository_profile(max_files: int = 80):
    state = load_repository_state()

    if not state:
        return "No repository has been indexed yet."

    file_lines = []

    important_files = sorted(
        state["files"],
        key=lambda file: _file_priority(file["file_path"])
    )[:max_files]

    for file in important_files:
        symbols = ", ".join(file.get("symbols", [])[:8])
        symbol_text = f" | symbols: {symbols}" if symbols else ""
        file_lines.append(
            f"- {file['file_path']} ({file['language']}, {file['line_count']} lines){symbol_text}"
        )

    return "\n".join(
        [
            f"Repository: {state['repository']['repo_name']}",
            f"GitHub URL: {state['repository'].get('repo_url', '')}",
            f"Detected repository type: {state.get('detected_repository_type', 'unknown')}",
            f"Classification evidence: {state.get('classification_evidence', [])}",
            f"Files indexed: {state['files_indexed']}",
            f"Chunks stored: {state['chunks_stored']}",
            f"Languages: {state['languages']}",
            f"Top-level directories: {state['top_level_directories']}",
            "Indexed file map:",
            *file_lines,
        ]
    )


def _file_priority(file_path: str):
    path = file_path.lower()

    priority_markers = [
        ("readme", 0),
        ("pyproject.toml", 1),
        ("package.json", 1),
        ("requirements", 1),
        ("app.py", 2),
        ("main.py", 2),
        ("index.", 2),
        ("src/", 3),
        ("app/", 3),
        ("lib/", 4),
        ("tests/", 8),
        ("docs/", 9),
    ]

    for marker, priority in priority_markers:
        if marker in path:
            return priority, path

    return 6, path


def classify_repository(files: list[dict[str, Any]]):
    path_map = {
        file["file_path"].lower(): file
        for file in files
    }

    paths = set(path_map)
    evidence = []

    readme_text = _content_for_first_matching(path_map, ["readme.md", "readme.rst", "readme.txt"])
    pyproject_text = _content_for_first_matching(path_map, ["pyproject.toml"])
    package_text = _content_for_first_matching(path_map, ["package.json"])
    requirements_text = _content_for_first_matching(path_map, ["requirements.txt"])
    combined_metadata = "\n".join(
        [
            readme_text[:3000],
            pyproject_text[:3000],
            package_text[:2000],
            requirements_text[:2000],
        ]
    ).lower()

    if "framework :: flask" in combined_metadata or "web framework" in combined_metadata and "flask" in combined_metadata:
        evidence.append("Metadata or README describes the project as a web framework.")
        return "framework/library", evidence

    if "framework" in combined_metadata and any(path.startswith("src/") for path in paths):
        evidence.append("Project metadata describes a framework and source lives under src/.")
        return "framework/library", evidence

    if "library" in combined_metadata and any(path.startswith("src/") for path in paths):
        evidence.append("Project metadata describes a library and source lives under src/.")
        return "library", evidence

    has_frontend = any(
        path.startswith(("app/", "pages/", "components/", "src/app/", "src/pages/", "src/components/"))
        for path in paths
    ) and "package.json" in paths

    has_backend = any(
        marker in paths
        for marker in ["main.py", "app/main.py", "src/main.py"]
    ) or any(
        token in combined_metadata
        for token in ["fastapi", "flask", "django", "uvicorn"]
    )

    if has_frontend and has_backend:
        evidence.append("Repository has frontend package metadata and backend runtime files or dependencies.")
        return "full-stack app", evidence

    if has_frontend:
        evidence.append("Repository has frontend app directories and package.json.")
        return "frontend app", evidence

    if has_backend:
        evidence.append("Repository has backend entry points or backend framework dependencies.")
        return "backend service", evidence

    if any(path.startswith(("cli/", "src/")) for path in paths) and any("click" in text for text in [combined_metadata]):
        evidence.append("Repository includes CLI dependency metadata.")
        return "CLI tool", evidence

    if package_text:
        evidence.append("Repository has package.json but no clear frontend app structure.")
        return "JavaScript/TypeScript package", evidence

    if pyproject_text:
        evidence.append("Repository has pyproject.toml but no clear application entry point.")
        return "Python package", evidence

    evidence.append("No strong framework, app, CLI, or package signals were detected.")
    return "unknown", evidence


def _content_for_first_matching(path_map: dict[str, dict[str, Any]], names: list[str]):
    for name in names:
        if name in path_map:
            return path_map[name].get("content", "")

    for path, file in path_map.items():
        if any(path.endswith(f"/{name}") for name in names):
            return file.get("content", "")

    return ""
