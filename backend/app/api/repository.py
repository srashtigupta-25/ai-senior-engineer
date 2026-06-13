from fastapi import APIRouter

from app.services.repository_service import clone_repository
from app.services.file_loader import load_repository_files


router = APIRouter()

@router.post("/clone")
def clone_repo(payload: dict):
    repo_url = payload["repo_url"]
    repo_info = clone_repository(repo_url)
    files = load_repository_files(
        repo_info["repo_path"]
    )
    return {
        "repository": repo_info,
        "total_files": len(files)
    }