def chunk_documents(documents):
    chunks = []
    max_chunk_chars = 1800
    overlap_lines = 8

    for doc in documents:
        lines = doc["content"].splitlines()
        start_line = 0

        while start_line < len(lines):
            chunk_lines = []
            current_size = 0
            current_line = start_line

            while current_line < len(lines):
                line = lines[current_line]
                next_size = current_size + len(line) + 1

                if chunk_lines and next_size > max_chunk_chars:
                    break

                chunk_lines.append(line)
                current_size = next_size
                current_line += 1

            end_line = current_line
            chunk_text = "\n".join(chunk_lines).strip()

            if not chunk_text:
                start_line = current_line + 1
                continue

            chunks.append(
                {
                    "file_path": doc["file_path"],
                    "content": chunk_text,
                    "language": doc["language"],
                    "symbols": doc["symbols"],
                    "start_line": start_line + 1,
                    "end_line": end_line,
                }
            )

            if current_line >= len(lines):
                break

            start_line = max(
                current_line - overlap_lines,
                start_line + 1
            )

    return chunks
