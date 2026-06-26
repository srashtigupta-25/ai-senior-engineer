from fastapi import APIRouter

from app.services.search_service import search_repository
from app.services.llm_service import generate_answer
from app.services.repository_state import build_repository_profile


router = APIRouter()


LOW_SIGNAL_PATH_PARTS = [
    "tests",
    "test",
    "docs",
    "examples",
    "scripts",
    ".github"
]


def normalize_path(file_path: str):
    return file_path.replace("\\", "/")


def is_low_signal_path(file_path: str):
    normalized_path = normalize_path(file_path).strip("/")
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
        selected_results = high_signal_results[:12]

        if len(selected_results) < 6:
            selected_results = selected_results + low_signal_results[: 6 - len(selected_results)]

    for item in selected_results:
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

    return "\n\n".join(context_blocks)


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
    ), merged_results


def build_search_queries(question: str):
    lowered_question = question.lower()
    queries = [question]

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
                "Flask class wsgi_app full_dispatch_request dispatch_request finalize_request",
                "route add_url_rule url_map request_context app_context blueprint",
            ]
        )

    if question_needs_tests(question):
        queries.append("tests fixtures assertions integration unit")

    return list(dict.fromkeys(queries))


@router.post("/ask")
def ask_repository(payload: dict):
    question = payload["question"]

    context, results = build_context_for_question(
        question
    )

    repository_profile = build_repository_profile()

    answer = generate_answer(
        question,
        context,
        repository_profile=repository_profile,
        report_type="question"
    )

    sources = [
        normalize_path(metadata.get("file_path", "unknown file"))
        for metadata in results["metadatas"][0]
    ]

    unique_sources = list(dict.fromkeys(sources))

    return {
        "answer": answer,
        "sources": unique_sources
    }
