def chunk_documents(documents):
    chunks = []
    chunk_size = 500
    overlap = 100
    for doc in documents:
        content = doc["content"]
        file_path = doc["file_path"]
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(
                {
                    "file_path": file_path,
                    "content": chunk
                }
            )
            start += chunk_size - overlap
    return chunks