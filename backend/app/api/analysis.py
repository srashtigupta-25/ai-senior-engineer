from fastapi import APIRouter

from app.services.search_service import search_repository
from app.services.llm_service import generate_answer
from app.api.chat import build_context_from_results


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
    architecture_queries = [
        "README project structure main source package entry point",
        "application startup initialization configuration main class",
        "routes endpoints handlers controllers services middleware dispatch",
        "database models schema repository storage persistence",
        "frontend components pages api client state management",
        "authentication authorization security session user flow",
        "background jobs workers queues scheduled tasks",
        "external APIs integrations webhooks third party services"
    ]

    all_context = []

    for query in architecture_queries:
        results = search_repository(
            query,
            top_k=30
        )

        all_context.append(
            build_context_from_results(
                results,
                query
            )
        )

    context = "\n\n".join(all_context)

    answer = generate_answer(
        "Explain the architecture of this repository. First classify what kind of repository it is. Then explain exact source files, main components, entry points, data flow, API flow if present, storage layer if present, configuration, integrations, and how the system is organized internally.",
        context
    )

    return {
        "architecture": answer
    }


@router.get("/onboarding")
def onboarding_report():
    onboarding_queries = [
        "README setup installation project structure",
        "main source package entry point initialization configuration",
        "routes controllers services models database",
        "tests examples development workflow contributing"
    ]

    all_context = []

    for query in onboarding_queries:
        results = search_repository(
            query,
            top_k=30
        )

        all_context.append(
            build_context_from_results(
                results,
                query
            )
        )

    context = "\n\n".join(all_context)

    answer = generate_answer(
        "I am a new engineer joining this repository. First classify what this repository is. Then explain which exact files to read first, how the major components fit together, how to run or understand the project, and what I should learn first. Mention only file paths found in the context.",
        context
    )

    return {
        "guide": answer
    }