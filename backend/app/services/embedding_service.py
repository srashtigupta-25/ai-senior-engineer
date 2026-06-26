from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

def create_embeddings(chunks):
    texts = [
        chunk["content"]
        for chunk in chunks
    ]
    embeddings = model.encode(
    texts,
    batch_size=16,
    show_progress_bar=True
    )
    return embeddings