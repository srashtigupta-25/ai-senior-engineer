import chromadb
import uuid


client = chromadb.PersistentClient(
    path="./chroma_db"
)


COLLECTION_NAME = "repository_chunks"


def get_collection():
    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )


def reset_collection():
    try:
        client.delete_collection(
            name=COLLECTION_NAME
        )
    except Exception:
        pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME
    )


def store_chunks(chunks, embeddings):
    collection = get_collection()

    ids = []
    documents = []
    metadatas = []
    vectors = []

    for index, chunk in enumerate(chunks):
        ids.append(str(uuid.uuid4()))

        documents.append(
            chunk["content"]
        )

        metadatas.append(
            {
                "file_path": str(chunk["file_path"])
            }
        )

        vectors.append(
            embeddings[index].tolist()
        )

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=vectors
    )