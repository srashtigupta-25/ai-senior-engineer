from sentence_transformers import SentenceTransformer
import chromadb

from app.services.repository_state import get_repository_facts


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


client = chromadb.PersistentClient(
    path="./chroma_db"
)


def search_repository(query: str, top_k: int = 10):
    collection = client.get_or_create_collection(
        name="repository_chunks"
    )
    repository_facts = get_repository_facts()
    repo_name = repository_facts.get("repo_name", "unknown")

    query_embedding = model.encode(
        query
    ).tolist()

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": top_k
    }

    if repo_name != "unknown":
        query_kwargs["where"] = {
            "repo_name": repo_name
        }

    results = collection.query(
        **query_kwargs
    )

    return results
