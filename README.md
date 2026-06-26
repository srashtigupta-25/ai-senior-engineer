# AI Senior Engineer

AI Senior Engineer is a local codebase intelligence app. Paste a public GitHub repository URL, index the source files, then ask engineering questions, generate an architecture report, or create a developer onboarding guide.

The app has two parts:

- `backend/`: FastAPI service that clones repositories, loads source files, chunks code with metadata, stores embeddings in ChromaDB, retrieves relevant snippets, and calls Ollama.
- `frontend/`: Next.js UI for indexing repositories and viewing grounded Markdown reports.

## What It Does

- Clones a public GitHub repository.
- Indexes supported source and config files.
- Stores embeddings in a local ChromaDB collection.
- Builds a repository profile with languages, directories, files, line counts, and detected symbols.
- Answers questions using retrieved source context and the repository profile.
- Generates architecture and onboarding reports with separate prompts.
- Shows retrieved source files in the UI so users can see what grounded the answer.

## Requirements

- Python 3.11+
- Node.js 20+
- Git
- Ollama running locally
- The `llama3:8b` model by default

Install the default Ollama model:

```bash
ollama pull llama3:8b
ollama serve
```

You can change the model or Ollama URL with environment variables:

```bash
export OLLAMA_MODEL=llama3:8b
export OLLAMA_URL=http://localhost:11434/api/generate
```

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API runs at:

```text
http://127.0.0.1:8000
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --port 3001
```

Open:

```text
http://localhost:3001
```

The frontend uses `http://127.0.0.1:8000` by default. To point it somewhere else:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --port 3001
```

## API Endpoints

### Index A Repository

```http
POST /repository/clone
```

Body:

```json
{
  "repo_url": "https://github.com/pallets/flask"
}
```

Returns repository metadata, indexed file count, and stored chunk count.

### Ask A Question

```http
POST /chat/ask
```

Body:

```json
{
  "question": "How does Flask work internally?"
}
```

Returns a grounded answer and retrieved source files.

### Generate Architecture

```http
GET /analysis/architecture
```

Returns a structured architecture report.

### Generate Onboarding Guide

```http
GET /analysis/onboarding
```

Returns a first-day developer onboarding guide.

## How The Analysis Pipeline Works

1. `backend/app/api/repository.py` receives a GitHub URL.
2. `backend/app/services/repository_service.py` clones the repository into `repositories/`.
3. `backend/app/services/file_loader.py` loads supported files, normalizes paths, detects languages, counts lines, and extracts symbols.
4. `backend/app/services/chunk_service.py` creates line-aware chunks with source ranges.
5. `backend/app/services/embedding_service.py` embeds chunks with SentenceTransformers.
6. `backend/app/services/vector_store.py` stores chunks and metadata in ChromaDB.
7. `backend/app/services/repository_state.py` saves a lightweight repository profile for later prompts.
8. `backend/app/api/chat.py` expands broad questions into several retrieval queries and builds grounded source context.
9. `backend/app/services/llm_service.py` sends the repository profile, retrieved snippets, and report-specific instructions to Ollama.

## Supported Files

The indexer currently supports common source, documentation, and config files:

- Python
- JavaScript and TypeScript
- React JSX and TSX
- Markdown
- JSON
- YAML
- TOML
- INI and config files
- CSS and HTML
- Shell scripts
- SQL
- Dockerfile
- `.env.example`

Large files, dependency folders, build artifacts, virtual environments, and Git metadata are ignored.

## Verification

Useful checks:

```bash
cd backend
python3 -m compileall app
```

```bash
cd frontend
npm run lint
npm run build
```

## Troubleshooting

- If indexing fails, make sure the repository URL is a public `https://github.com/...` URL.
- If answers fail, make sure Ollama is running and the configured model is installed.
- If the frontend cannot reach the API, confirm FastAPI is running on port `8000` and `NEXT_PUBLIC_API_URL` matches it.
- If answers look shallow, re-index the repository after backend changes so chunks include the latest metadata.
- This app keeps one active ChromaDB collection at a time. Indexing a new repository replaces the previous repository context.

## Notes

This is a local developer tool, not a hosted multi-tenant service. Repositories are cloned to the local `repositories/` directory and embeddings are stored in the local `backend/chroma_db` database.
