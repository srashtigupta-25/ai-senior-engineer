import os
import re

import requests

from app.services.repository_state import get_repository_facts

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3:8b"
)


def generate_answer(question, context, repository_profile="", report_type="question"):
    format_instructions = get_format_instructions(report_type)
    repository_facts = get_repository_facts()
    framework_rules = get_framework_rules(repository_facts)

    prompt = f"""
You are an expert senior software engineer analyzing a real GitHub repository.

Use ONLY the repository profile and source context provided below.
Do not invent file names.
Do not invent modules.
Do not invent functions or classes.
Always use exact file paths from the repository profile or source context.
If evidence is missing, say what is missing instead of guessing.

The repository profile contains a field named "Detected repository type".
Use that detected type as the primary classification unless the source context clearly contradicts it.
If it says framework/library, never describe the repository as an application built with that framework.
If it says Python package or JavaScript/TypeScript package, explain whether the evidence supports library, CLI, app, or unknown.

Do not assume the repository is a web application.
If the repository appears to be a framework or library, explain it as framework or library source code, not as an application built with that framework.

Never mention conventional files such as views.py, routes.py, controllers.py, models.py, or app.py unless they appear in the repository profile or source context.
Ground every important claim in one or more cited source files.
Prefer specific implementation details over generic framework explanations.
When explaining flow, mention the concrete functions, classes, modules, or config files that support each step.
If a user asks a broad "how does it work internally" question, explain the major internal subsystems, not only one matching keyword.
Use relative file paths exactly as shown. Do not prefix paths with ../repositories/ or any local clone directory.
Do not shorten a path to only its basename. For example, write src/flask/app.py, not app.py.
Do not include a Repository Type section that contradicts the detected repository type.

Additional repository-specific rules:
{framework_rules}

Repository Profile:
{repository_profile}

Source Context:
{context}

User Question:
{question}

{format_instructions}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        },
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    return sanitize_answer(
        data["response"],
        repository_facts
    )


def get_framework_rules(repository_facts):
    repository_type = repository_facts["repository_type"].lower()

    if "framework" not in repository_type and "library" not in repository_type:
        return "- No extra framework-specific rules."

    indexed_paths = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }

    if any(path.startswith("src/flask/") for path in indexed_paths):
        return """
- This repository is framework or library source code, not a user application built with it.
- Do not say users should run python app.py unless that exact file and command are present.
- Do not describe views.py as user route handlers; if src/flask/views.py exists, it is framework implementation code for class-based views.
- Do not invent models.py, controllers.py, or user app view modules.
- Do not say src/flask/app.py defines routes for this repository. It implements the Flask application object and request dispatch machinery.
- Do not say AppContext represents a single request. AppContext is application context; RequestContext is request context.
- Do not mention requirements.txt unless it appears in the repository profile or context.
- Do not invent clone URLs, production deployment questions, --config options, or database/API integration tasks.
- Onboarding should focus on package metadata, src/ implementation modules, tests, and framework extension points.
- Architecture should describe framework internals: application object, context lifecycle, routing, dispatch, blueprints, CLI, templating, JSON, testing, and WSGI integration when those files are present.
"""

    if any(path.startswith("httpx/") for path in indexed_paths):
        return """
- This repository is HTTP client library source code, not an application.
- Do not invent app routes, controllers, servers, or database models.
- Use exact HTTPX file paths such as httpx/_client.py, httpx/_models.py, and httpx/_transports/default.py when those files appear in context.
- Do not mention httpx/client.py, httpx/request.py, httpx/response.py, or httpx/transport.py unless those exact files appear in context.
- Explain request sending through client orchestration, request/response models, configuration, auth/redirect handling, and transport abstractions.
"""

    return """
- This repository is framework or library source code, not a user application built with it.
- Do not invent app routes, controllers, servers, or database models.
- Use exact source paths from the repository profile or source context.
- Explain how consumers call into the package and how the package handles the work internally.
"""


def sanitize_answer(answer, repository_facts):
    cleaned_answer = answer.strip()
    cleaned_answer = remove_local_clone_prefixes(
        cleaned_answer,
        repository_facts["repo_name"]
    )
    cleaned_answer = expand_unique_basenames(
        cleaned_answer,
        repository_facts["files"]
    )
    cleaned_answer = expand_preferred_source_basenames(
        cleaned_answer,
        repository_facts
    )
    cleaned_answer = expand_partial_source_paths(
        cleaned_answer,
        repository_facts
    )
    cleaned_answer = correct_framework_language(
        cleaned_answer,
        repository_facts
    )
    cleaned_answer = remove_framework_hallucinations(
        cleaned_answer,
        repository_facts
    )
    cleaned_answer = correct_httpx_language(
        cleaned_answer,
        repository_facts
    )
    cleaned_answer = remove_unindexed_framework_file_claims(
        cleaned_answer,
        repository_facts
    )

    repository_type_section = build_repository_type_section(repository_facts)

    repository_heading_pattern = r"^(?:#{1,3}\s*)?Repository Type\b.*?(?=^(?:#{1,3}\s*)?(?:Direct Answer|Architecture Summary|First Day Reading Path|Summary|Relevant Files|Main Components|Execution Flow|Entry Points|Local Setup)\b|^##\s+|\Z)"

    if re.search(repository_heading_pattern, cleaned_answer, flags=re.MULTILINE | re.DOTALL):
        return re.sub(
            repository_heading_pattern,
            repository_type_section + "\n\n",
            cleaned_answer,
            count=1,
            flags=re.MULTILINE | re.DOTALL
        ).strip()

    return f"{repository_type_section}\n\n{cleaned_answer}".strip()


def build_repository_type_section(repository_facts):
    evidence = repository_facts["classification_evidence"]
    evidence_text = " ".join(evidence) if evidence else "No explicit classification evidence was stored."

    return "\n".join(
        [
            "## Repository Type",
            f"{repository_facts['repo_name']} is classified as **{repository_facts['repository_type']}**.",
            evidence_text,
        ]
    )


def remove_local_clone_prefixes(answer, repo_name):
    if not repo_name or repo_name == "unknown":
        return answer

    patterns = [
        rf"\.\./repositories/{re.escape(repo_name)}/",
        rf"repositories/{re.escape(repo_name)}/",
        rf".*/repositories/{re.escape(repo_name)}/",
    ]

    cleaned_answer = answer

    for pattern in patterns:
        cleaned_answer = re.sub(
            pattern,
            "",
            cleaned_answer
        )

    return cleaned_answer


def correct_framework_language(answer, repository_facts):
    repository_type = repository_facts["repository_type"].lower()

    if "framework" not in repository_type and "library" not in repository_type:
        return answer

    cleaned_answer = answer

    replacements = {
        r"\ba Flask application\b": "the Flask framework source repository",
        r"\bA Flask application\b": "The Flask framework source repository",
        r"\bFlask application\b": "Flask framework source repository",
        r"\bFlask-based web application\b": "Flask framework source repository",
        r"\bPython-based web application repository\b": "Python framework/library repository",
    }

    for pattern, replacement in replacements.items():
        cleaned_answer = re.sub(
            pattern,
            replacement,
            cleaned_answer
        )

    return cleaned_answer


def remove_framework_hallucinations(answer, repository_facts):
    repository_type = repository_facts["repository_type"].lower()

    if "framework" not in repository_type and "library" not in repository_type:
        return answer

    cleaned_answer = answer

    bad_line_patterns = [
        r"^.*models\.py.*(?:\n|$)",
        r"^.*python\s+src/flask/app\.py.*(?:\n|$)",
        r"^.*python\s+app\.py.*(?:\n|$)",
        r"^.*--config command-line option.*(?:\n|$)",
        r"^.*production deployment strategy.*(?:\n|$)",
    ]

    for pattern in bad_line_patterns:
        cleaned_answer = re.sub(
            pattern,
            "",
            cleaned_answer,
            flags=re.IGNORECASE | re.MULTILINE
        )

    replacements = {
        r"src/flask/app\.py: This file contains the main application logic and defines the routes for the application\.": "src/flask/app.py: Implements the Flask application object, WSGI entry method, request dispatch, response finalization, and setup APIs.",
        r"src/flask/app\.py: This file contains the main Flask framework source repository code, including the definition of the App class\.": "src/flask/app.py: Implements the Flask application object, WSGI entry method, request dispatch, response finalization, and setup APIs.",
        r"src/flask/app\.py \(found in the root directory\)": "src/flask/app.py",
        r"src/flask/views\.py \(found in the root directory\)": "src/flask/views.py",
        r"src/flask/sansio/README\.md \(found in the root directory\)": "src/flask/sansio/README.md",
        r"src/flask/views\.py: A collection of view functions that handle HTTP requests and return responses\.": "src/flask/views.py: Implements Flask's class-based view abstractions, not an application's own view functions.",
        r"src/flask/views\.py: This file contains view functions that handle HTTP requests\.": "src/flask/views.py: Implements Flask's class-based view abstractions, not an application's own view functions.",
        r"src/flask/views\.py file contains view functions that handle HTTP requests\.": "src/flask/views.py implements Flask's class-based view abstractions.",
        r"src/flask/views\.py: This file contains the view functions that handle requests and return responses\.": "src/flask/views.py: Implements Flask's class-based view abstractions, not an application's own view functions.",
        r"The views in src/flask/views\.py are called when a route is matched\.": "User-defined view functions are registered through Flask's routing machinery; src/flask/views.py provides reusable class-based view support.",
        r"Creating a new route or view function\.": "Working on framework routing, dispatch, blueprint, or class-based view behavior.",
        r"Creating a new route for handling HTTP requests\.": "Working on framework routing, dispatch, blueprint, or class-based view behavior.",
        r"Implementing authentication and authorization mechanisms\.": "Reviewing framework hooks and extension points that applications can use for authentication or authorization.",
        r"Modifying existing code in src/flask/app\.py or src/flask/views\.py\.": "Modifying framework internals in files such as src/flask/app.py, src/flask/sansio/app.py, src/flask/blueprints.py, or src/flask/views.py.",
        r"The architecture revolves around the concept of \"blueprints,\"": "Blueprints are one major organizational feature, but the architecture also centers on the Flask application object, request and application contexts, routing, dispatch, CLI, templating, and JSON support.",
        r"blueprints,\" which are essentially routes for handling HTTP requests\.": "blueprints, which group routes and related setup behavior before registration on an application.",
        r"which are essentially routes for handling HTTP requests\.": "which group routes and related setup behavior before registration on an application.",
        r"support\. which group routes and related setup behavior before registration on an application\.": "support. Blueprints group routes and related setup behavior before registration on an application.",
        r"Blueprints can be registered with the application, allowing developers to define custom routes and handlers\.": "Blueprints are registered on an application and contribute URL rules, hooks, static/template configuration, and related setup behavior.",
        r"The framework also includes support for templates, internationalization, and debugging tools\.": "The framework also includes template integration, debugging helpers, JSON support, session support, CLI behavior, and testing utilities when those modules are present.",
        r"Run pip install -r requirements\.txt to install dependencies\.": "Setup commands are not visible in the retrieved context; check project metadata such as pyproject.toml and contributor documentation.",
        r"Install dependencies: pip install -r requirements\.txt\.": "Setup commands are not visible in the retrieved context; check project metadata such as pyproject.toml and contributor documentation.",
        r"Clone the repository: git clone https://github\.com/your-repo-name\.git": "Clone the actual GitHub repository URL shown in the indexed repository metadata.",
        r"Install dependencies: pip install -r requirements\.txt \(inferred from package files\)": "Setup commands are not visible in the retrieved context; check project metadata such as pyproject.toml and contributor documentation.",
        r"The data flow in this repository is primarily focused on handling HTTP requests and responses\.": "The runtime flow is primarily focused on how a user-created Flask application object handles HTTP requests and responses.",
        r"The control flow is managed by the Flask class, which routes requests to the appropriate blueprint\.": "Control flow is managed by the Flask application object, URL map/rules, request context, dispatch methods, and optional blueprint-registered behavior.",
        r"src/flask/app\.py file is the entry point for the Flask framework source repository\.": "src/flask/app.py implements the main Flask application class and WSGI dispatch behavior.",
        r"The application code in src/flask/app\.py defines routes and view functions that handle HTTP requests\.": "src/flask/app.py implements the framework APIs that let users register routes and dispatch requests.",
        r"The AppContext object is responsible for managing the request context": "RequestContext manages request-specific state, while AppContext manages application-specific state",
        r"Flask creates an instance of AppContext which represents the current request\.": "Flask uses RequestContext for request-specific state and AppContext for application-specific state.",
        r"Flask creates an AppContext object, which represents the current request context\.": "Flask uses RequestContext for request-specific state and AppContext for application-specific state.",
        r"AppContext object, which represents the current request context": "RequestContext object, which represents request-specific state",
        r"This context is used to store information about the request, such as the URL, method, and query parameters\.": "Request information such as URL, method, and query parameters belongs to the request object inside RequestContext.",
        r"A request is made to the application, which triggers the creation of an instance of AppContext\.": "A request reaches a user-created Flask application object, and Flask creates/pushes request and application context objects as needed.",
        r"The AppContext instance is created and initialized with information from the WSGI environment\.": "RequestContext is built from the WSGI environment; AppContext tracks application-scoped state.",
        r"The context is pushed onto a stack, allowing developers to access request data such as request, session, g, and current_app\.": "Context variables make request, session, g, and current_app available while the request/application contexts are active.",
        r"When the context is popped off the stack, the request data is no longer available\.": "When the request/application contexts are popped, those context-local proxies are no longer bound.",
        r"AppContext class, which represents the current request": "RequestContext class, which represents the current request context",
        r"AppContext: Represents the current request and provides access to request data\.": "AppContext: Represents application-scoped context. RequestContext represents request-scoped state and request data.",
        r"AppContext: This class represents the current request context and provides access to request data\.": "AppContext: Represents application-scoped context. RequestContext represents request-scoped state and request data.",
        r"app function in src/flask/app\.py, which creates an instance of the Flask class and returns it\.": "Flask class in src/flask/app.py, which users instantiate to create an application object.",
        r"run function in src/flask/cli\.py, which runs the Flask framework source repository using the WSGI protocol\.": "CLI commands in src/flask/cli.py, which locate and run user Flask applications during development.",
        r"shell command in src/flask/cli\.py, which provides an interactive shell for running Python code in the context of the Flask framework source repository\.": "shell command in src/flask/cli.py, which opens an interactive shell in an application context for a user Flask app.",
        r"Writing tests for your code using Flask's testing framework\.": "Writing or updating framework regression tests for routing, contexts, CLI, blueprints, JSON, templating, and testing helpers.",
        r"You would touch files in the app directory \(e\.g\., src/flask/app\.py\) and possibly create new routes or views in the views directory \(e\.g\., src/flask/views\.py\)\.": "You would usually touch framework implementation files under src/flask/ and matching regression tests under tests/.",
        r"How to integrate with a specific database system\.": "Which extension points and compatibility boundaries should be preserved for third-party integrations.",
        r"A request is made to the Flask framework source repository": "A request reaches a Flask application object created by a user of the framework",
        r"request is made to the Flask framework source repository": "request reaches a Flask application object created by a user of the framework",
    }

    for pattern, replacement in replacements.items():
        cleaned_answer = re.sub(
            pattern,
            replacement,
            cleaned_answer
        )

    return cleaned_answer


def correct_httpx_language(answer, repository_facts):
    indexed_files = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }

    if not any(path.startswith("httpx/") for path in indexed_files):
        return answer

    replacements = {
        r"httpx/client\.py": "httpx/_client.py",
        r"httpx/transport\.py": "httpx/_transports/base.py and httpx/_transports/default.py",
        r"httpx/request\.py": "httpx/_models.py",
        r"httpx/response\.py": "httpx/_models.py",
        r"(?<![\w/.-])_request\.py(?![\w/.-])": "httpx/_models.py",
        r"(?<![\w/.-])_response\.py(?![\w/.-])": "httpx/_models.py",
        r"httpx\.Transport": "httpx transport classes",
        r"(?<![\w/.-])_request: This is a private method used by the client to construct and send requests\.": "Client send methods in httpx/_client.py coordinate request construction with models from httpx/_models.py and transports from httpx/_transports/.",
        r"This is a private method used by the client to construct and send requests\.": "Request construction and sending are implemented through client methods in httpx/_client.py and request/response models in httpx/_models.py.",
        r"The transport layer will send the request over the network using the underlying protocol \(e\.g\., TCP/IP\)\.": "The selected transport implements the sync or async network I/O and returns a response model.",
    }

    cleaned_answer = answer

    for pattern, replacement in replacements.items():
        cleaned_answer = re.sub(
            pattern,
            replacement,
            cleaned_answer
        )

    return cleaned_answer


def remove_unindexed_framework_file_claims(answer, repository_facts):
    repository_type = repository_facts["repository_type"].lower()

    if "framework" not in repository_type and "library" not in repository_type:
        return answer

    indexed_files = {
        file.get("file_path", "")
        for file in repository_facts["files"]
    }

    conventional_app_files = [
        "urls.py",
        "routes.py",
        "controllers.py",
        "models.py",
        "tests/test_routes.py",
    ]

    cleaned_answer = answer

    for file_path in conventional_app_files:
        if file_path in indexed_files:
            continue

        cleaned_answer = re.sub(
            rf"^.*{re.escape(file_path)}.*(?:\n|$)",
            "",
            cleaned_answer,
            flags=re.IGNORECASE | re.MULTILINE
        )

    return cleaned_answer


def expand_unique_basenames(answer, files):
    basename_to_paths = {}

    for file in files:
        path = file.get("file_path", "")
        basename = path.split("/")[-1]

        if not basename:
            continue

        basename_to_paths.setdefault(basename, set()).add(path)

    cleaned_answer = answer

    for basename, paths in basename_to_paths.items():
        if len(paths) != 1 or "/" not in next(iter(paths)):
            continue

        full_path = next(iter(paths))

        cleaned_answer = re.sub(
            rf"(?<![\w/.-]){re.escape(basename)}(?![\w/.-])",
            full_path,
            cleaned_answer
        )

    return cleaned_answer


def expand_preferred_source_basenames(answer, repository_facts):
    repository_type = repository_facts["repository_type"].lower()

    if "framework" not in repository_type and "library" not in repository_type:
        return answer

    basename_to_paths = {}

    for file in repository_facts["files"]:
        path = file.get("file_path", "")
        basename = path.split("/")[-1]

        if basename:
            basename_to_paths.setdefault(basename, set()).add(path)

    cleaned_answer = answer

    for basename, paths in basename_to_paths.items():
        preferred_paths = sorted(
            path
            for path in paths
            if path.startswith("src/") and "/tests/" not in path and not path.startswith("tests/")
        )

        if not preferred_paths:
            continue

        preferred_path = preferred_paths[0]
        cleaned_answer = re.sub(
            rf"(?<![\w/.-]){re.escape(basename)}(?![\w/.-])",
            preferred_path,
            cleaned_answer
        )

    return cleaned_answer


def expand_partial_source_paths(answer, repository_facts):
    repository_type = repository_facts["repository_type"].lower()

    if "framework" not in repository_type and "library" not in repository_type:
        return answer

    cleaned_answer = answer

    for file in repository_facts["files"]:
        full_path = file.get("file_path", "")

        if not full_path.startswith("src/"):
            continue

        partial_path = full_path.removeprefix("src/")

        if partial_path == full_path:
            continue

        cleaned_answer = re.sub(
            rf"(?<![\w/.-]){re.escape(partial_path)}(?![\w/.-])",
            full_path,
            cleaned_answer
        )

    return cleaned_answer


def get_format_instructions(report_type):
    if report_type == "architecture":
        return """
Write the answer in this exact Markdown format:

## Repository Type
Classify the repository and justify the classification from files.

## Architecture Summary
Explain the system in practical terms.
For framework/library repositories, explain the framework internals and public API, not a sample application built with the framework.

## Main Components
List the major components, their exact files, and responsibilities.
Do not list models, controllers, or app-specific view functions unless exact files appear in context.

## Entry Points
Explain startup or public entry points. If none are visible, say so.
For framework/library repositories, entry points can include package exports, CLI modules, WSGI callable methods, and public classes.

## Data And Control Flow
Explain request, command, library, or runtime flow step by step, depending on the repository type.
For Flask-like framework repositories, distinguish the framework's application object from user applications built with it.

## Storage And External Integrations
Describe persistence, vector stores, databases, APIs, models, or external services only when supported by files.

## Configuration And Runtime
Mention package files, environment variables, config modules, and run commands visible from the context.

## Risks Or Unknowns
Call out missing context, likely fragile areas, or parts that need human review.

## Confidence
Give a confidence level: High, Medium, or Low.
Explain briefly why.
"""

    if report_type == "onboarding":
        return """
Write the answer in this exact Markdown format:

## Repository Type
Classify the repository and explain why.

## First Day Reading Path
Give an ordered list of exact files to read first and what each teaches.
For framework/library repositories, prioritize README, package metadata, src/ public API files, core implementation modules, and tests.

## Local Setup
Explain how to install and run the project using only commands or files visible in context. If a command is inferred from package files, say it is inferred.
Do not tell the user to run python app.py for a framework/library unless that exact command is documented in context.
For framework/library repositories, prefer development setup and test commands over "run the app" instructions. If commands are not visible, say setup commands are not visible in the retrieved context.

## Mental Model
Explain how the main parts fit together.
For framework/library repositories, explain how consumers call into the library and how the library handles the work internally.

## Common Tasks
Describe practical tasks a new engineer might do and which files they would touch.

## Questions To Ask The Team
List unknowns or decisions not answerable from the repository.

## Confidence
Give a confidence level: High, Medium, or Low.
Explain briefly why.
"""

    return """
Write the answer in this exact Markdown format:

## Repository Type
State what kind of repository this appears to be and why.

## Direct Answer
Answer the user's question using specific implementation details from this repository.

## Relevant Files
List only exact file paths that appear in the repository profile or source context.
For each file, explain why it matters.

## Execution Flow
Explain the flow step by step using only the provided evidence.

## Important Functions Or Classes
Mention only functions, classes, decorators, or modules that appear in the context.

## What This Means For A New Engineer
Explain what a developer should understand from this part of the codebase.

## Confidence
Give a confidence level: High, Medium, or Low.
Explain briefly why.
"""
