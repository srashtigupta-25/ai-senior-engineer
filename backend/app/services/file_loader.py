from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".md"
}

def load_repository_files(repo_path: str):

    documents = []
    repo = Path(repo_path)
    for file in repo.rglob("*"):
        if file.suffix not in ALLOWED_EXTENSIONS:
            continue
        try:
            content = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )
            documents.append({
                "file_path": str(file),
                "content": content
            })
        except Exception:
            pass
    return documents