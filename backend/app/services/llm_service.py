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

    return """
- This repository is framework or library source code, not a user application built with it.
- Do not say users should run python app.py unless that exact file and command are present.
- Do not describe views.py as user route handlers; if src/flask/views.py exists, it is framework implementation code for class-based views.
- Onboarding should focus on package metadata, src/ implementation modules, tests, and framework extension points.
- Architecture should describe framework internals: application object, context lifecycle, routing, dispatch, blueprints, CLI, templating, JSON, testing, and WSGI integration when those files are present.
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

    repository_type_section = build_repository_type_section(repository_facts)

    if re.search(r"^##\s+Repository Type\b", cleaned_answer, flags=re.MULTILINE):
        return re.sub(
            r"^##\s+Repository Type\b.*?(?=^##\s+|\Z)",
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


def get_format_instructions(report_type):
    if report_type == "architecture":
        return """
Write the answer in this exact Markdown format:

## Repository Type
Classify the repository and justify the classification from files.

## Architecture Summary
Explain the system in practical terms.

## Main Components
List the major components, their exact files, and responsibilities.

## Entry Points
Explain startup or public entry points. If none are visible, say so.

## Data And Control Flow
Explain request, command, library, or runtime flow step by step, depending on the repository type.

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

## Local Setup
Explain how to install and run the project using only commands or files visible in context. If a command is inferred from package files, say it is inferred.

## Mental Model
Explain how the main parts fit together.

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
