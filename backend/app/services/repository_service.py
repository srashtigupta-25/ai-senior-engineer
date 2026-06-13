from git import Repo
from pathlib import Path
import shutil


REPO_FOLDER = Path("repositories")


def clone_repository(repo_url: str):

    repo_name = repo_url.split("/")[-1]

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    repo_path = REPO_FOLDER / repo_name

    if repo_path.exists():
        shutil.rmtree(repo_path)

    Repo.clone_from(repo_url, repo_path)

    return {
        "repo_name": repo_name,
        "repo_path": str(repo_path)
    }