from pathlib import Path
import shutil
from urllib.parse import urlparse

from git import Repo


REPO_FOLDER = Path(__file__).resolve().parents[3] / "repositories"


def clone_repository(repo_url: str):
    parsed_url = urlparse(repo_url)

    if parsed_url.scheme not in {"http", "https"} or parsed_url.netloc != "github.com":
        raise ValueError("Only public GitHub repository URLs are supported.")

    repo_name = Path(parsed_url.path).name

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if not repo_name:
        raise ValueError("Could not determine a repository name from the URL.")

    repo_path = REPO_FOLDER / repo_name

    if repo_path.exists():
        shutil.rmtree(repo_path)

    REPO_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    Repo.clone_from(repo_url, repo_path)

    return {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "repo_path": str(repo_path)
    }
