from fastapi import APIRouter

from app.services.search_service import search_repository
from app.services.llm_service import generate_answer
from app.services.repository_state import build_repository_profile, get_repository_facts


router = APIRouter()


LOW_SIGNAL_PATH_PARTS = [
    "tests",
    "test",
    "docs",
    "examples",
    "scripts",
    ".github",
    "changelog.md"
]


def normalize_path(file_path: str):
    return file_path.replace("\\", "/")


def is_low_signal_path(file_path: str):
    normalized_path = normalize_path(file_path).strip("/").lower()
    path_parts = normalized_path.split("/")

    return any(
        part in path_parts
        for part in LOW_SIGNAL_PATH_PARTS
    )


def question_needs_tests(question: str):
    lowered_question = question.lower()

    test_words = [
        "test",
        "tests",
        "testing",
        "pytest",
        "unit test",
        "integration test"
    ]

    return any(
        word in lowered_question
        for word in test_words
    )


def build_context_from_results(results, question: str = ""):
    context_blocks = []
    selected_sources = []
    repository_facts = get_repository_facts()

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    paired_results = []

    for index, document in enumerate(documents):
        file_path = normalize_path(
            metadatas[index].get("file_path", "unknown file")
        )

        paired_results.append(
            {
                "file_path": file_path,
                "document": document,
                "is_low_signal": is_low_signal_path(file_path),
                "language": metadatas[index].get("language", ""),
                "start_line": metadatas[index].get("start_line", 1),
                "end_line": metadatas[index].get("end_line", 1),
                "symbols": metadatas[index].get("symbols", "")
            }
        )

    high_signal_results = [
        item for item in paired_results
        if not item["is_low_signal"]
    ]

    low_signal_results = [
        item for item in paired_results
        if item["is_low_signal"]
    ]

    if question_needs_tests(question):
        selected_results = paired_results[:12]
    else:
        selected_results = sorted(
            high_signal_results,
            key=lambda item: source_priority(item["file_path"], repository_facts)
        )[:12]

        if len(selected_results) < 6:
            selected_results = selected_results + sorted(
                low_signal_results,
                key=lambda item: source_priority(item["file_path"], repository_facts)
            )[: 6 - len(selected_results)]

    for item in selected_results:
        selected_sources.append(item["file_path"])
        line_range = f"{item['start_line']}-{item['end_line']}"
        symbol_text = f"\nDetected Symbols: {item['symbols']}" if item["symbols"] else ""

        context_blocks.append(
            f"""
Source File:
{item["file_path"]}
Lines:
{line_range}
Language:
{item["language"]}{symbol_text}

Code Snippet:
{item["document"]}
"""
        )

    return "\n\n".join(context_blocks), selected_sources


def source_priority(file_path: str, repository_facts: dict | None = None):
    normalized_path = normalize_path(file_path)
    source_roots = []

    if repository_facts:
        source_roots = repository_facts.get("source_roots", [])

    if normalized_path.startswith("src/"):
        return 0, normalized_path

    normalized_roots = [
        root.lower()
        for root in source_roots
    ]

    if any(normalized_path.lower().startswith(f"{root}/") for root in normalized_roots):
        return 0, normalized_path

    if normalized_path in {"README.md", "pyproject.toml", "package.json"}:
        return 1, normalized_path

    if normalized_path.startswith("app/") or normalized_path.startswith("backend/") or normalized_path.startswith("frontend/"):
        return 2, normalized_path

    if is_low_signal_path(normalized_path):
        return 9, normalized_path

    return 4, normalized_path


def build_context_for_question(question: str):
    queries = build_search_queries(question)
    unique_items = {}

    for query in queries:
        results = search_repository(
            query,
            top_k=24
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for index, document in enumerate(documents):
            metadata = metadatas[index]
            key = (
                normalize_path(metadata.get("file_path", "unknown file")),
                metadata.get("start_line", 1),
                metadata.get("end_line", 1)
            )

            if key not in unique_items:
                unique_items[key] = {
                    "document": document,
                    "metadata": metadata
                }

    merged_results = {
        "documents": [[item["document"] for item in unique_items.values()]],
        "metadatas": [[item["metadata"] for item in unique_items.values()]]
    }

    return build_context_from_results(
        merged_results,
        question
    )


def build_search_queries(question: str):
    lowered_question = question.lower()
    queries = [question]
    repository_facts = get_repository_facts()
    repo_name = repository_facts["repo_name"]
    source_roots = repository_facts.get("source_roots", [])

    if "internally" in lowered_question or "how does" in lowered_question or "architecture" in lowered_question:
        queries.extend(
            [
                "main entry point initialization lifecycle dispatch flow",
                "core class public API request context routing configuration",
                "important modules services controllers handlers storage",
            ]
        )

    if "flask" in lowered_question:
        queries.extend(
            [
                "src flask app Flask wsgi_app full_dispatch_request dispatch_request finalize_request",
                "src flask ctx request_context app_context globals lifecycle",
                "Flask class wsgi_app full_dispatch_request dispatch_request finalize_request",
                "route add_url_rule url_map request_context app_context blueprint",
            ]
        )

    if "framework" in repository_facts["repository_type"].lower() or "library" in repository_facts["repository_type"].lower():
        queries.extend(
            [
                "src package public API core classes lifecycle dispatch configuration",
                "pyproject README package metadata framework library architecture",
            ]
        )

        for root in source_roots:
            queries.extend(
                [
                    f"{root} client request response transport send build handle",
                    f"{root} public API core models config exceptions",
                ]
            )

    if repo_name.lower() == "httpx" or "httpx" in lowered_question:
        queries.extend(
            [
                "httpx _client Client send request build_request send_handling_auth send_handling_redirects send_single_request",
                "httpx _transports base default handle_request handle_async_request HTTPTransport AsyncHTTPTransport",
                "httpx _models Request Response Headers URL",
                "httpx _api get post request stream Client AsyncClient",
            ]
        )

    if question_needs_tests(question):
        queries.append("tests fixtures assertions integration unit")

    return list(dict.fromkeys(queries))


@router.post("/ask")
def ask_repository(payload: dict):
    question = payload["question"]

    context, selected_sources = build_context_for_question(
        question
    )

    repository_profile = build_repository_profile()

    answer = generate_answer(
        question,
        context,
        repository_profile=repository_profile,
        report_type="question"
    )

    unique_sources = list(dict.fromkeys(selected_sources))

    return {
        "answer": answer,
        "sources": unique_sources
    }
