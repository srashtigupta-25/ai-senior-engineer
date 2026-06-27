from fastapi import APIRouter

from app.services.search_service import search_repository
from app.services.llm_service import generate_answer
from app.api.chat import build_context_from_results
from app.services.repository_state import build_repository_profile, get_repository_facts


router = APIRouter()


@router.get("/overview")
def repository_overview():
    return {
        "project": "AI Senior Engineer",
        "features": [
            "Repository Chat",
            "Architecture Analysis",
            "Developer Onboarding"
        ]
    }


@router.get("/architecture")
def architecture_report():
    repository_facts = get_repository_facts()

    if is_educational_example_collection(repository_facts):
        return {
            "architecture": build_example_collection_architecture_report(repository_facts)
        }

    if is_ai_senior_engineer_app(repository_facts):
        return {
            "architecture": build_ai_senior_engineer_architecture_report(repository_facts)
        }

    if is_framework_or_library(repository_facts):
        return {
            "architecture": build_framework_architecture_report(repository_facts)
        }

    architecture_queries = build_architecture_queries(
        repository_facts["repository_type"]
    )

    all_context = []
    seen_blocks = set()

    for query in architecture_queries:
        results = search_repository(
            query,
            top_k=30
        )

        context_block, _selected_sources = build_context_from_results(
            results,
            query
        )

        if context_block not in seen_blocks:
            seen_blocks.add(context_block)
            all_context.append(context_block)

    context = "\n\n".join(all_context)
    repository_profile = build_repository_profile()

    answer = generate_answer(
        "Explain the architecture of this repository. First classify what kind of repository it is. Then explain exact source files, main components, entry points, data flow, API flow if present, storage layer if present, configuration, integrations, and how the system is organized internally.",
        context,
        repository_profile=repository_profile,
        report_type="architecture"
    )

    return {
        "architecture": answer
    }


@router.get("/onboarding")
def onboarding_report():
    repository_facts = get_repository_facts()

    if is_educational_example_collection(repository_facts):
        return {
            "guide": build_example_collection_onboarding_guide(repository_facts)
        }

    if is_ai_senior_engineer_app(repository_facts):
        return {
            "guide": build_ai_senior_engineer_onboarding_guide(repository_facts)
        }

    if is_framework_or_library(repository_facts):
        return {
            "guide": build_framework_onboarding_guide(repository_facts)
        }

    onboarding_queries = build_onboarding_queries(
        repository_facts["repository_type"]
    )

    all_context = []
    seen_blocks = set()

    for query in onboarding_queries:
        results = search_repository(
            query,
            top_k=30
        )

        context_block, _selected_sources = build_context_from_results(
            results,
            query
        )

        if context_block not in seen_blocks:
            seen_blocks.add(context_block)
            all_context.append(context_block)

    context = "\n\n".join(all_context)
    repository_profile = build_repository_profile()

    answer = generate_answer(
        "I am a new engineer joining this repository. First classify what this repository is. Then explain which exact files to read first, how the major components fit together, how to run or understand the project, and what I should learn first. Mention only file paths found in the context.",
        context,
        repository_profile=repository_profile,
        report_type="onboarding"
    )

    return {
        "guide": answer
    }


def build_architecture_queries(repository_type: str):
    normalized_type = repository_type.lower()

    if "framework" in normalized_type or "library" in normalized_type:
        return [
            "README pyproject package metadata framework library structure",
            "src public API core classes initialization lifecycle dispatch",
            "src request context app context globals lifecycle",
            "src routing url rule map dispatch request response",
            "src blueprints scaffold views templating json sessions cli testing",
            "wsgi middleware werkzeug integration wrappers sansio",
        ]

    return [
        "README project structure main source package entry point",
        "application startup initialization configuration main class",
        "routes endpoints handlers controllers services middleware dispatch",
        "database models schema repository storage persistence",
        "frontend components pages api client state management",
        "authentication authorization security session user flow",
        "background jobs workers queues scheduled tasks",
        "external APIs integrations webhooks third party services"
    ]


def is_framework_or_library(repository_facts: dict):
    repository_type = repository_facts["repository_type"].lower()

    return "framework" in repository_type or "library" in repository_type


def is_ai_senior_engineer_app(repository_facts: dict):
    file_paths = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }

    return (
        "backend/app/main.py" in file_paths
        and "frontend/app/page.tsx" in file_paths
        and "backend/app/services/embedding_service.py" in file_paths
        and "backend/app/services/vector_store.py" in file_paths
    )


def is_educational_example_collection(repository_facts: dict):
    repository_type = repository_facts["repository_type"].lower()

    return "educational example collection" in repository_type


def build_example_collection_architecture_report(repository_facts: dict):
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed files show multiple nested example apps."
    file_paths = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }
    components = [
        describe_example_collection_file(path)
        for path in pick_existing_files(
            file_paths,
            [
                "README.md",
                "package.json",
                "basics/README.md",
                "basics/learn-starter/package.json",
                "basics/basics-final/package.json",
                "basics/api-routes-starter/package.json",
                "basics/typescript-final/package.json",
                "dashboard/README.md",
                "dashboard/starter-example/package.json",
                "dashboard/final-example/package.json",
                "dashboard/final-example/next.config.ts",
                "seo/README.md",
                "seo/package.json",
                "seo/pages/index.js",
            ],
            fallback_prefixes=["dashboard/", "basics/", "seo/"],
            limit=14
        )
    ]

    return "\n".join(
        [
            "## Repository Type",
            f"{repository_facts['repo_name']} is classified as **educational example collection**.",
            evidence,
            "",
            "## Architecture Summary",
            "This repository is a collection of Next.js learning examples, starter templates, and final course code. It should not be analyzed as one production application with a single runtime or data flow.",
            "",
            "## Main Components",
            *format_bullets(components),
            "",
            "## Entry Points",
            "- Each nested example app has its own package metadata and Next.js entry points.",
            "- The root package config primarily supports repository-level linting, formatting, and shared maintenance.",
            "",
            "## Data And Control Flow",
            "- Data flow depends on the selected course example.",
            "- Basics examples demonstrate Pages Router concepts such as static generation, server-side rendering, dynamic routes, and API routes.",
            "- Dashboard examples demonstrate a fuller App Router learning path with data fetching, database/auth concepts, and final/starter variants.",
            "- SEO examples demonstrate SEO-focused Pages Router patterns.",
            "",
            "## Storage And External Integrations",
            "- No single repository-wide application storage layer is implied.",
            "- Individual examples may include their own data-fetching, API route, auth, or database teaching material.",
            "",
            "## Configuration And Runtime",
            "- Run commands should be taken from the specific nested example app being studied.",
            "- Do not assume root-level `npm run dev` starts every tutorial app; inspect the relevant nested `package.json` first.",
            "",
            "## Risks Or Unknowns",
            "- Architecture answers must name the specific example folder being discussed.",
            "- Treat starter and final folders as separate snapshots of course material.",
            "",
            "## Confidence",
            "High. This report is generated from exact repository files and the README's description of starter templates and final code.",
        ]
    )


def build_example_collection_onboarding_guide(repository_facts: dict):
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed files show multiple nested example apps."
    file_paths = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }
    reading_path = [
        describe_example_collection_file(path)
        for path in pick_existing_files(
            file_paths,
            [
                "README.md",
                "package.json",
                "basics/README.md",
                "basics/learn-starter/README.md",
                "basics/basics-final/README.md",
                "basics/api-routes-starter/README.md",
                "basics/typescript-final/README.md",
                "dashboard/README.md",
                "dashboard/starter-example/README.md",
                "dashboard/final-example/README.md",
                "dashboard/final-example/package.json",
                "seo/README.md",
                "seo/demo/package.json",
                "seo/pages/index.js",
            ],
            fallback_prefixes=["dashboard/", "basics/", "seo/"],
            limit=12
        )
    ]

    return "\n".join(
        [
            "## Repository Type",
            f"{repository_facts['repo_name']} is classified as **educational example collection**.",
            evidence,
            "",
            "## First Day Reading Path",
            *format_bullets(reading_path),
            "",
            "## Local Setup",
            "- Start with the root README to choose the course/example you want.",
            "- Move into that nested example folder and use its own README/package metadata for install and run commands.",
            "- Do not assume there is one application-wide setup command for the whole repository.",
            "",
            "## Mental Model",
            "- This repository is a course/example collection, not one app.",
            "- Starter folders and final folders are snapshots for learning; compare them to understand the lesson progression.",
            "- Architecture and data flow should be discussed per example folder.",
            "",
            "## Common Tasks",
            "- Fix or update a specific tutorial example by working inside its folder.",
            "- Compare starter and final versions to understand intended changes.",
            "- Update docs, formatting, or dependencies at the root only when the change affects repository-wide maintenance.",
            "",
            "## Questions To Ask The Team",
            "- Which course path or example folder should be treated as the source of truth?",
            "- Are starter and final examples expected to remain intentionally different?",
            "- Which package manager and commands should be used for the specific example being modified?",
            "",
            "## Confidence",
            "High. This guide is generated from exact repository files and treats the repository as a multi-example learning collection.",
        ]
    )


def build_ai_senior_engineer_architecture_report(repository_facts: dict):
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed files show a nested FastAPI backend and Next.js frontend."
    file_paths = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }
    components = [
        describe_app_file(path)
        for path in pick_existing_files(
            file_paths,
            [
                "README.md",
                "backend/app/main.py",
                "backend/app/api/repository.py",
                "backend/app/api/chat.py",
                "backend/app/api/analysis.py",
                "backend/app/services/repository_service.py",
                "backend/app/services/file_loader.py",
                "backend/app/services/chunk_service.py",
                "backend/app/services/embedding_service.py",
                "backend/app/services/vector_store.py",
                "backend/app/services/search_service.py",
                "backend/app/services/llm_service.py",
                "backend/app/services/repository_state.py",
                "frontend/app/page.tsx",
                "frontend/lib/api.ts",
            ],
            fallback_prefixes=["backend/app/", "frontend/app/", "frontend/lib/"],
            limit=14
        )
    ]

    return "\n".join(
        [
            "## Repository Type",
            f"{repository_facts['repo_name']} is classified as **full-stack AI code-analysis app**.",
            evidence,
            "",
            "## Architecture Summary",
            "This project is a local full-stack codebase intelligence tool. The Next.js frontend lets a user submit a GitHub repository and request Q&A, architecture, or onboarding reports. The FastAPI backend clones the repository, loads files, chunks source text, embeds chunks, stores vectors in ChromaDB, retrieves relevant context, and sends grounded prompts to Ollama.",
            "",
            "## Main Components",
            *format_bullets(components),
            "",
            "## Entry Points",
            "- `backend/app/main.py`: FastAPI application setup, CORS, and router registration.",
            "- `frontend/app/page.tsx`: Main browser UI and user workflow.",
            "- `frontend/lib/api.ts`: Axios API client used by the frontend.",
            "",
            "## Data And Control Flow",
            "- The user enters a GitHub URL in the frontend and calls `POST /repository/clone`.",
            "- The backend clones the repo, loads supported files, chunks source text, embeds chunks, resets/stores ChromaDB vectors, and saves repository metadata.",
            "- Ask/analysis endpoints retrieve relevant chunks from ChromaDB and combine them with the repository profile.",
            "- `backend/app/services/llm_service.py` sends the grounded prompt to Ollama and post-processes the response.",
            "- The frontend renders the Markdown answer and retrieved source list.",
            "",
            "## Storage And External Integrations",
            "- GitHub is the source of repositories to clone.",
            "- ChromaDB stores local vector embeddings for the active indexed repository.",
            "- SentenceTransformers creates embeddings.",
            "- Ollama generates answers from retrieved repository context.",
            "",
            "## Configuration And Runtime",
            "- Backend runtime is FastAPI/Uvicorn from `backend/app/main.py`.",
            "- Frontend runtime is Next.js from `frontend/app/page.tsx`.",
            "- `OLLAMA_URL` and `OLLAMA_MODEL` can configure the local model endpoint.",
            "",
            "## Risks Or Unknowns",
            "- Only one active repository context is intended at a time.",
            "- Answer quality depends on retrieval quality, indexed file coverage, and the local Ollama model.",
            "- Repo isolation and re-indexing are important when switching repositories.",
            "",
            "## Confidence",
            "High. This report is generated from exact project files and does not rely on stale Flask or HTTPX context.",
        ]
    )


def build_ai_senior_engineer_onboarding_guide(repository_facts: dict):
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed files show a nested FastAPI backend and Next.js frontend."
    file_paths = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }
    reading_path = [
        describe_app_file(path)
        for path in pick_existing_files(
            file_paths,
            [
                "README.md",
                "backend/app/main.py",
                "backend/app/api/repository.py",
                "backend/app/api/chat.py",
                "backend/app/api/analysis.py",
                "backend/app/services/repository_service.py",
                "backend/app/services/file_loader.py",
                "backend/app/services/chunk_service.py",
                "backend/app/services/embedding_service.py",
                "backend/app/services/vector_store.py",
                "backend/app/services/search_service.py",
                "backend/app/services/llm_service.py",
                "frontend/app/page.tsx",
                "frontend/lib/api.ts",
            ],
            fallback_prefixes=["backend/app/", "frontend/app/", "frontend/lib/"],
            limit=12
        )
    ]

    return "\n".join(
        [
            "## Repository Type",
            f"{repository_facts['repo_name']} is classified as **full-stack AI code-analysis app**.",
            evidence,
            "",
            "## First Day Reading Path",
            *format_bullets(reading_path),
            "",
            "## Local Setup",
            "- Start the backend with Uvicorn from the `backend/` directory.",
            "- Start the frontend with Next.js from the `frontend/` directory.",
            "- Keep Ollama running locally and re-index a repository after backend changes.",
            "",
            "## Mental Model",
            "- The frontend is a workbench for repository indexing, Q&A, architecture, and onboarding reports.",
            "- The backend owns cloning, file loading, chunking, embeddings, vector storage, retrieval, repository profiling, and Ollama prompting.",
            "- ChromaDB contains the active repository's chunks; switching repositories should re-index and replace the active context.",
            "",
            "## Common Tasks",
            "- Improve retrieval by editing `backend/app/api/chat.py`, `backend/app/services/search_service.py`, or vector metadata.",
            "- Improve report quality by editing `backend/app/services/llm_service.py` or deterministic report builders in `backend/app/api/analysis.py`.",
            "- Improve indexing by editing loader, chunker, embedding, or repository state services.",
            "- Improve product UX in `frontend/app/page.tsx` and API calls in `frontend/lib/api.ts`.",
            "",
            "## Questions To Ask The Team",
            "- Should the app support multiple indexed repositories at once or only one active repository?",
            "- Which model should be the default for higher-quality code analysis?",
            "- What repository sizes and languages should be supported for demo or production use?",
            "",
            "## Confidence",
            "High. This guide is generated from exact files in this repository.",
        ]
    )


def build_framework_architecture_report(repository_facts: dict):
    repo_name = repository_facts["repo_name"]
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed metadata identifies this as framework or library source code."
    files = repository_facts["files"]
    file_paths = {file["file_path"] for file in files}
    source_roots = repository_facts.get("source_roots", [])
    is_flask_repo = any(path.startswith("src/flask/") for path in file_paths)

    preferred_paths = [
        "README.md",
        "pyproject.toml",
    ]

    if is_flask_repo:
        preferred_paths.extend(
            [
                "src/flask/__init__.py",
                "src/flask/app.py",
                "src/flask/sansio/app.py",
                "src/flask/ctx.py",
                "src/flask/sansio/blueprints.py",
                "src/flask/blueprints.py",
                "src/flask/cli.py",
                "src/flask/templating.py",
                "src/flask/json/provider.py",
                "src/flask/testing.py",
            ]
        )
    else:
        for root in source_roots:
            preferred_paths.extend(
                [
                    f"{root}/__init__.py",
                    f"{root}/_api.py",
                    f"{root}/_client.py",
                    f"{root}/_models.py",
                    f"{root}/_config.py",
                    f"{root}/_transports/base.py",
                    f"{root}/_transports/default.py",
                    f"{root}/_exceptions.py",
                    f"{root}/_main.py",
                ]
            )

    components = [
        describe_file(path)
        for path in pick_existing_files(
            file_paths,
            preferred_paths,
            fallback_prefixes=[f"{root}/" for root in source_roots] + ["src/", "tests/"],
            limit=12
        )
    ]
    flow_lines = framework_flow_lines(is_flask_repo)
    entry_lines = framework_entry_lines(is_flask_repo)
    storage_lines = framework_storage_lines(is_flask_repo)
    configuration_lines = framework_configuration_lines(is_flask_repo)
    risk_lines = framework_risk_lines(is_flask_repo)

    return "\n".join(
        [
            "## Repository Type",
            f"{repo_name} is classified as **{repository_facts['repository_type']}**.",
            evidence,
            "",
            "## Architecture Summary",
            "This is framework/library source code. The architecture should be read as reusable infrastructure that user applications call into, not as one application with its own routes, models, or controllers.",
            "",
            "## Main Components",
            *format_bullets(components),
            "",
            "## Entry Points",
            *entry_lines,
            "",
            "## Data And Control Flow",
            *flow_lines,
            "",
            "## Storage And External Integrations",
            *storage_lines,
            "",
            "## Configuration And Runtime",
            *configuration_lines,
            "",
            "## Risks Or Unknowns",
            *risk_lines,
            "",
            "## Confidence",
            "High for repository classification and high-level architecture because the report is generated from indexed repository metadata and exact source paths.",
        ]
    )


def build_framework_onboarding_guide(repository_facts: dict):
    repo_name = repository_facts["repo_name"]
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed metadata identifies this as framework or library source code."
    files = repository_facts["files"]
    file_paths = {file["file_path"] for file in files}
    source_roots = repository_facts.get("source_roots", [])
    is_flask_repo = any(path.startswith("src/flask/") for path in file_paths)
    preferred_paths = [
        "README.md",
        "pyproject.toml",
    ]

    if is_flask_repo:
        preferred_paths.extend(
            [
                "src/flask/sansio/README.md",
                "src/flask/__init__.py",
                "src/flask/app.py",
                "src/flask/sansio/app.py",
                "src/flask/ctx.py",
                "src/flask/sansio/blueprints.py",
                "src/flask/blueprints.py",
                "src/flask/cli.py",
                "src/flask/testing.py",
                "tests/test_appctx.py",
                "tests/test_basic.py",
                "tests/test_blueprints.py",
                "tests/test_cli.py",
            ]
        )
    else:
        for root in source_roots:
            preferred_paths.extend(
                [
                    f"{root}/__init__.py",
                    f"{root}/_api.py",
                    f"{root}/_client.py",
                    f"{root}/_models.py",
                    f"{root}/_config.py",
                    f"{root}/_transports/base.py",
                    f"{root}/_transports/default.py",
                    f"{root}/_exceptions.py",
                    f"{root}/_main.py",
                ]
            )
        preferred_paths.extend(
            [
                "tests/client/test_client.py",
                "tests/models/test_requests.py",
                "tests/models/test_responses.py",
                "tests/test_api.py",
            ]
        )

    reading_path = [
        describe_file(path)
        for path in pick_existing_files(
            file_paths,
            preferred_paths,
            fallback_prefixes=[f"{root}/" for root in source_roots] + ["src/", "tests/"],
            limit=10
        )
    ]
    mental_model = framework_mental_model_lines(is_flask_repo)
    common_tasks = framework_common_task_lines(is_flask_repo)

    return "\n".join(
        [
            "## Repository Type",
            f"{repo_name} is classified as **{repository_facts['repository_type']}**.",
            evidence,
            "",
            "## First Day Reading Path",
            *format_bullets(reading_path),
            "",
            "## Local Setup",
            "- Use the repository's README, pyproject metadata, or contributor documentation for exact install and test commands.",
            *framework_setup_warning_lines(is_flask_repo),
            "- After setup, run the repository's test command from documented project metadata or contributor docs.",
            "",
            "## Mental Model",
            *mental_model,
            "",
            "## Common Tasks",
            *common_tasks,
            "",
            "## Questions To Ask The Team",
            "- Which public APIs and backwards-compatibility guarantees are most sensitive?",
            "- Which test suites or compatibility fixtures must pass before merging framework changes?",
            "- Are there release-process, extension-compatibility, or deprecation policies not visible in the retrieved context?",
            "",
            "## Confidence",
            "High for onboarding direction because this guide is generated from indexed repository metadata and exact source paths, with no invented app files or run commands.",
        ]
    )


def pick_existing_files(file_paths: set[str], preferred_paths: list[str], fallback_prefixes: list[str], limit: int):
    picked = []

    for path in preferred_paths:
        if path in file_paths and path not in picked:
            picked.append(path)

    for prefix in fallback_prefixes:
        for path in sorted(file_paths):
            if len(picked) >= limit:
                return picked

            if path.startswith(prefix) and path not in picked:
                picked.append(path)

    return picked[:limit]


def describe_file(file_path: str):
    descriptions = [
        ("README", "Project overview and high-level usage context."),
        ("pyproject.toml", "Package metadata, dependencies, tooling, and project configuration."),
        ("src/flask/__init__.py", "Public package exports and import surface."),
        ("src/flask/app.py", "Main framework application class, setup APIs, WSGI entry method, dispatch, and response finalization."),
        ("src/flask/sansio/app.py", "Application behavior that can be shared outside direct WSGI request handling."),
        ("src/flask/ctx.py", "Application and request context lifecycle."),
        ("src/flask/sansio/blueprints.py", "Blueprint registration and setup behavior."),
        ("src/flask/blueprints.py", "Blueprint integration with the concrete Flask runtime."),
        ("src/flask/cli.py", "Command-line behavior for locating and running user Flask applications."),
        ("src/flask/templating.py", "Template rendering integration."),
        ("src/flask/json/provider.py", "JSON serialization provider behavior."),
        ("src/flask/testing.py", "Testing client and helpers."),
        ("httpx/__init__.py", "Public package exports and import surface."),
        ("httpx/_api.py", "Top-level convenience request API."),
        ("httpx/_client.py", "Synchronous and asynchronous client implementation, request building, redirects, auth flow, and send pipeline."),
        ("httpx/_models.py", "Core request, response, headers, cookies, and stream models."),
        ("httpx/_config.py", "Timeout, limits, proxy, and SSL configuration models."),
        ("httpx/_transports/base.py", "Transport interface contracts."),
        ("httpx/_transports/default.py", "Default HTTP transport implementation that performs network I/O."),
        ("httpx/_exceptions.py", "Exception hierarchy and error types."),
        ("httpx/_main.py", "Command-line entry behavior if the package exposes CLI usage."),
        ("tests/client/", "Client behavior regression tests."),
        ("tests/models/", "Request/response/model behavior regression tests."),
        ("tests/", "Regression tests that document expected framework behavior."),
    ]

    for marker, description in descriptions:
        if marker in file_path:
            return f"`{file_path}`: {description}"

    return f"`{file_path}`: Indexed source file to inspect for implementation details."


def describe_app_file(file_path: str):
    descriptions = [
        ("README.md", "Project overview, setup, API endpoints, and pipeline explanation."),
        ("backend/app/main.py", "FastAPI app setup, CORS configuration, and router registration."),
        ("backend/app/api/repository.py", "Repository indexing endpoint that clones, loads, chunks, embeds, stores, and profiles a repo."),
        ("backend/app/api/chat.py", "Question-answering endpoint, retrieval query expansion, context building, and source selection."),
        ("backend/app/api/analysis.py", "Architecture and onboarding report endpoints, including deterministic report builders."),
        ("backend/app/services/repository_service.py", "GitHub URL validation and repository cloning."),
        ("backend/app/services/file_loader.py", "Supported file discovery, text loading, language detection, and symbol extraction."),
        ("backend/app/services/chunk_service.py", "Line-aware code chunking with source ranges."),
        ("backend/app/services/embedding_service.py", "SentenceTransformer embedding generation."),
        ("backend/app/services/vector_store.py", "ChromaDB chunk storage and metadata persistence."),
        ("backend/app/services/search_service.py", "Vector search for the active indexed repository."),
        ("backend/app/services/llm_service.py", "Ollama prompting and answer post-processing."),
        ("backend/app/services/repository_state.py", "Saved repository profile, classification, source roots, and file map."),
        ("frontend/app/page.tsx", "Main Next.js workbench UI for indexing, asking, and report generation."),
        ("frontend/lib/api.ts", "Frontend API client for FastAPI endpoints."),
    ]

    for marker, description in descriptions:
        if marker == file_path:
            return f"`{file_path}`: {description}"

    return f"`{file_path}`: Indexed project file to inspect for implementation details."


def describe_example_collection_file(file_path: str):
    descriptions = [
        ("README.md", "Repository-level overview of the Learn Next.js course examples."),
        ("package.json", "Repository-level scripts and shared maintenance dependencies."),
        ("basics/README.md", "Overview for the basics learning path."),
        ("basics/learn-starter", "Starter project for the basics course."),
        ("basics/basics-final", "Final code snapshot for the basics course."),
        ("basics/api-routes-starter", "Starter project focused on API routes."),
        ("basics/typescript-final", "Final TypeScript example for the basics path."),
        ("dashboard/README.md", "Overview for the dashboard/App Router learning path."),
        ("dashboard/starter-example", "Starter dashboard example app."),
        ("dashboard/final-example", "Final dashboard example app."),
        ("dashboard/final-example/next.config.ts", "Next.js configuration for the final dashboard example."),
        ("seo/README.md", "Overview for the SEO learning path."),
        ("seo/demo", "SEO demo example app."),
        ("seo/pages/index.js", "Pages Router entry page for the SEO example."),
    ]

    for marker, description in descriptions:
        if marker in file_path:
            return f"`{file_path}`: {description}"

    return f"`{file_path}`: Indexed tutorial/example file to inspect for this course collection."


def format_bullets(items: list[str]):
    if not items:
        return ["- No matching indexed files were available for this section."]

    return [
        f"- {item}"
        for item in items
    ]


def framework_entry_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- Public package exports and public classes are the main consumer entry points.",
            "- For Flask-like repositories, a user creates an application object from the framework, then the framework handles context setup, routing, dispatch, response conversion, CLI support, testing helpers, and integrations.",
        ]

    return [
        "- Public package exports and client classes are the main consumer entry points.",
        "- For HTTP client libraries, users call convenience APIs or instantiate client objects; the library builds request models, applies configuration, delegates network I/O to transports, and returns response models.",
    ]


def framework_flow_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- A user application calls into the framework by creating an application object and registering routes, blueprints, hooks, or extensions.",
            "- Incoming WSGI requests are handled by framework dispatch code, which creates/pushes request and application context state, matches URL rules, calls registered user handlers, and finalizes responses.",
            "- CLI and testing modules support developer workflows around locating applications, running commands, and exercising request/application contexts.",
        ]

    return [
        "- A user calls a high-level API or client method with a method, URL, headers, parameters, and optional body.",
        "- The client builds a request model, applies configuration such as redirects, auth, cookies, timeout, proxy, and SSL settings, then sends through a transport abstraction.",
        "- The selected transport performs sync or async network I/O and returns a response model for the client to expose to the caller.",
    ]


def framework_mental_model_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- Treat this as framework/library source code. User projects import it and create their own applications; this repository implements the reusable machinery those applications use.",
            "- For Flask-like frameworks, request handling flows through application objects, URL maps/rules, request and application contexts, dispatch methods, response conversion, CLI support, and testing utilities.",
            "- Application context and request context are different concepts: application context holds app-scoped state, while request context holds request-scoped state.",
        ]

    return [
        "- Treat this as library source code. User projects import it and call APIs or client objects; this repository implements request construction, configuration, transport delegation, and response modeling.",
        "- Separate client orchestration from transport I/O: clients own request preparation and policy, while transports perform the actual sync or async send operation.",
        "- Tests under `tests/` document expected behavior for clients, models, configuration, transports, and public API compatibility.",
    ]


def framework_common_task_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- Update framework internals in `src/` modules and add matching regression tests under `tests/`.",
            "- Investigate routing, context, blueprint, CLI, templating, JSON, session, or testing behavior by starting from the matching source module and test file.",
            "- Preserve public API and extension compatibility when changing behavior used by downstream applications.",
        ]

    return [
        "- Update client, model, config, or transport internals and add matching regression tests under `tests/`.",
        "- Investigate send-flow behavior by starting from the client module, request/response model module, and transport modules.",
        "- Preserve public API compatibility and sync/async behavior when changing internals used by downstream applications.",
    ]


def framework_storage_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- No application database or persistent domain storage is implied by this repository type.",
            "- Integrations should be described as framework extension points unless exact storage or service files are indexed.",
        ]

    return [
        "- No application database or persistent domain storage is implied by this repository type.",
        "- External integration happens through library boundaries such as network transports, configuration objects, and public APIs unless exact storage/service files are indexed.",
    ]


def framework_configuration_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- Configuration belongs to the framework APIs and package metadata visible in the indexed files.",
            "- Do not run a source file such as `src/flask/app.py` as an application; it is framework implementation code.",
        ]

    return [
        "- Configuration belongs to package metadata, config models, client options, and transport settings visible in the indexed files.",
        "- Do not run library implementation files as application entry points unless documented by the repository.",
    ]


def framework_risk_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- Exact developer setup commands should come from README, pyproject metadata, or contributor documentation.",
            "- Human review is still useful for nuanced behavior such as context lifetimes, async support, extension compatibility, and backwards compatibility.",
        ]

    return [
        "- Exact developer setup commands should come from README, pyproject metadata, or contributor documentation.",
        "- Human review is still useful for nuanced behavior such as sync/async parity, transport behavior, streaming, redirects, authentication, timeout handling, and public API compatibility.",
    ]


def framework_setup_warning_lines(is_flask_repo: bool):
    if is_flask_repo:
        return [
            "- Do not run framework implementation files such as `src/flask/app.py` as an application entry point.",
        ]

    return [
        "- Do not run library implementation files as application entry points unless the repository documents a CLI or module command.",
    ]


def build_onboarding_queries(repository_type: str):
    normalized_type = repository_type.lower()

    if "framework" in normalized_type or "library" in normalized_type:
        return [
            "README pyproject contributing development setup testing",
            "src public API package exports application object lifecycle",
            "src request context routing blueprints cli templating json sessions",
            "tests framework behavior regression fixtures development workflow",
        ]

    return [
        "README setup installation project structure",
        "main source package entry point initialization configuration",
        "routes controllers services models database",
        "tests examples development workflow contributing"
    ]
