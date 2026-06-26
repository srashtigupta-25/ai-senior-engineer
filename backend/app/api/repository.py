from fastapi import APIRouter, HTTPException

from app.services.repository_service import clone_repository
from app.services.file_loader import load_repository_files
from app.services.chunk_service import chunk_documents
from app.services.embedding_service import create_embeddings
from app.services.vector_store import store_chunks, reset_collection
from app.services.repository_state import save_repository_state


router = APIRouter()


@router.post("/clone")
def clone_repo(payload: dict):
    repo_url = payload.get("repo_url")

    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail="repo_url is required"
        )

    try:
        repo_info = clone_repository(
            repo_url
        )

        files = load_repository_files(
            repo_info["repo_path"]
        )

        if not files:
            raise ValueError("No supported source files were found in this repository.")

        chunks = chunk_documents(
            files
        )

        embeddings = create_embeddings(
            chunks
        )

        reset_collection()

        store_chunks(
            chunks,
            embeddings
        )

        save_repository_state(
            repo_info,
            files,
            len(chunks)
        )

        return {
            "repository": repo_info,
            "files": len(files),
            "chunks": len(chunks),
            "status": "indexed"
        }
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error
