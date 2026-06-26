from fastapi import APIRouter

from app.services.repository_service import clone_repository
from app.services.file_loader import load_repository_files
from app.services.chunk_service import chunk_documents
from app.services.embedding_service import create_embeddings
from app.services.vector_store import store_chunks, reset_collection


router = APIRouter()


@router.post("/clone")
def clone_repo(payload: dict):
    repo_url = payload["repo_url"]

    repo_info = clone_repository(
        repo_url
    )

    files = load_repository_files(
        repo_info["repo_path"]
    )

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

    return {
        "repository": repo_info,
        "files": len(files),
        "chunks": len(chunks),
        "status": "indexed"
    }