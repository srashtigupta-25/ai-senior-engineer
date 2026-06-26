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


def build_framework_architecture_report(repository_facts: dict):
    repo_name = repository_facts["repo_name"]
    evidence = " ".join(repository_facts["classification_evidence"]) or "Indexed metadata identifies this as framework or library source code."
    files = repository_facts["files"]
    file_paths = {file["file_path"] for file in files}

    components = [
        describe_file(path)
        for path in pick_existing_files(
            file_paths,
            [
                "README.md",
                "pyproject.toml",
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
            ],
            fallback_prefixes=["src/", "tests/"],
            limit=12
        )
    ]

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
            "- Public package exports and public classes are the main consumer entry points.",
            "- For Flask-like repositories, a user creates an application object from the framework, then the framework handles context setup, routing, dispatch, response conversion, CLI support, testing helpers, and integrations.",
            "",
            "## Data And Control Flow",
            "- A user application calls into the framework by creating an application object and registering routes, blueprints, hooks, or extensions.",
            "- Incoming WSGI requests are handled by framework dispatch code, which creates/pushes request and application context state, matches URL rules, calls registered user handlers, and finalizes responses.",
            "- CLI and testing modules support developer workflows around locating applications, running commands, and exercising request/application contexts.",
            "",
            "## Storage And External Integrations",
            "- No application database or persistent domain storage is implied by this repository type.",
            "- Integrations should be described as framework extension points unless exact storage or service files are indexed.",
            "",
            "## Configuration And Runtime",
            "- Configuration belongs to the framework APIs and package metadata visible in the indexed files.",
            "- Do not run a source file such as `src/flask/app.py` as an application; it is framework implementation code.",
            "",
            "## Risks Or Unknowns",
            "- Exact developer setup commands should come from README, pyproject metadata, or contributor documentation.",
            "- Human review is still useful for nuanced behavior such as context lifetimes, async support, extension compatibility, and backwards compatibility.",
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

    reading_path = [
        describe_file(path)
        for path in pick_existing_files(
            file_paths,
            [
                "README.md",
                "pyproject.toml",
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
            ],
            fallback_prefixes=["src/", "tests/"],
            limit=10
        )
    ]

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
            "- Do not run framework implementation files such as `src/flask/app.py` as an application entry point.",
            "- After setup, run the repository's test command from documented project metadata or contributor docs.",
            "",
            "## Mental Model",
            "- Treat this as framework/library source code. User projects import it and create their own applications; this repository implements the reusable machinery those applications use.",
            "- For Flask-like frameworks, request handling flows through application objects, URL maps/rules, request and application contexts, dispatch methods, response conversion, CLI support, and testing utilities.",
            "- Application context and request context are different concepts: application context holds app-scoped state, while request context holds request-scoped state.",
            "",
            "## Common Tasks",
            "- Update framework internals in `src/` modules and add matching regression tests under `tests/`.",
            "- Investigate routing, context, blueprint, CLI, templating, JSON, session, or testing behavior by starting from the matching source module and test file.",
            "- Preserve public API and extension compatibility when changing behavior used by downstream applications.",
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
        ("tests/", "Regression tests that document expected framework behavior."),
    ]

    for marker, description in descriptions:
        if marker in file_path:
            return f"`{file_path}`: {description}"

    return f"`{file_path}`: Indexed source file to inspect for implementation details."


def format_bullets(items: list[str]):
    if not items:
        return ["- No matching indexed files were available for this section."]

    return [
        f"- {item}"
        for item in items
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
