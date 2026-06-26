import os

import requests

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

    return data["response"]


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
