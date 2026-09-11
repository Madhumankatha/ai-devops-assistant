# Agent Workspace

This directory contains repository-local guidance and artifacts for AI-assisted engineering workflows.

## Purpose

- Keep agent-specific working guidance separate from application code.
- Document repeatable engineering workflows.
- Store lightweight prompts, checklists, and agent notes when needed.

## Current Workflow

1. Inspect the current branch and implementation.
2. Make the smallest change that solves the problem.
3. Run `pytest -q`.
4. Review the diff for secrets, generated files, and unnecessary complexity.
5. Update README/documentation when behavior changes.
6. Commit focused changes to `feature/agentic_ai`.

Do not store secrets, credentials, model weights, production logs, or sensitive incident data here.
