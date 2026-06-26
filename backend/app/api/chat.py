from fastapi import APIRouter

from app.services.search_service import search_repository
from app.services.llm_service import generate_answer


router = APIRouter()


LOW_SIGNAL_PATH_PARTS = [
    "/tests/",
    "/test/",
    "/docs/",
    "/examples/",
    "/scripts/",
    "/.github/"
]


def normalize_path(file_path: str):
    return file_path.replace("\\", "/")


def is_low_signal_path(file_path: str):
    normalized_path = normalize_path(file_path)

    return any(
        part in normalized_path
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

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    paired_results = []

    for index, document in enumerate(documents):
        file_path = normalize_path(
            metadatas[index].get("file_path", "unknown file")
        )

        paired_results.append(
            {
                "file_path": file_path,
                "document": document,
                "is_low_signal": is_low_signal_path(file_path)
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
        context_blocks.append(
            f"""
Source File:
{item["file_path"]}

Code Snippet:
{item["document"]}
"""
        )

    return "\n\n".join(context_blocks)


@router.post("/ask")
def ask_repository(payload: dict):
    question = payload["question"]

    results = search_repository(
        question,
        top_k=30
    )

    context = build_context_from_results(
        results,
        question
    )

    answer = generate_answer(
        question,
        context
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