from sentence_transformers import SentenceTransformer
import chromadb


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

    query_embedding = model.encode(
        query
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results