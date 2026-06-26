import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_answer(question, context):
    prompt = f"""
You are an expert senior software engineer analyzing a real GitHub repository.

Use ONLY the repository context provided below.
Do not invent file names.
Do not invent modules.
Do not invent functions or classes.
Always use exact file paths from the repository context.
If a file path is not shown in the context, do not mention it.

First classify what kind of repository this appears to be:
library, framework, CLI tool, backend service, frontend app, full-stack app, AI system, data pipeline, or unknown.

Do not assume the repository is a web application.
If the repository appears to be a framework or library, explain it as framework or library source code, not as an application built with that framework.

Do not describe an internal folder as a separate framework unless the context explicitly says that.
If you are unsure, describe it as an internal module or source file.

Focus on how this specific repository is implemented internally.
If the answer is not clearly supported by the provided context, say that the available context is not enough.

Repository Context:
{context}

User Question:
{question}

Write the answer in this exact format:

## Repository Type
State what kind of repository this appears to be and why.

## Summary
Explain the answer in simple and accurate language.

## Relevant Files
List only exact file paths that appear in the repository context.
For each file, explain why it matters.

## Execution Flow
Explain the flow step by step using only the provided context.

## Important Functions or Classes
Mention only functions, classes, decorators, or modules that appear in the context.

## What This Means For A New Engineer
Explain what a developer should understand from this part of the codebase.

## Confidence
Give a confidence level: High, Medium, or Low.
Explain briefly why.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3:8b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]