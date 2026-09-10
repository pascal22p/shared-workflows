# Shared Workflows

Shared GitHub Actions, reusable workflows, and CLI tools for automated AI-powered code reviews, specialized for Scala projects using OVH AI Endpoints.

---

## Table of Contents

- [Overview](#overview)
- [Reusable Workflow (`AIreview.yml`)](#reusable-workflow-githubworkflowsaireviewyml)
- [Standalone Local Runner (`standalone_pr_review.py`)](#standalone-local-runner-standalone_pr_reviewpy)
- [Requirements](#requirements)
- [License](#license)

---

## Overview

This repository provides an end-to-end automated pull-request review suite. The pipeline captures before-and-after source code, executes multi-perspective AI code reviews (core logic, test coverage, and frontend), applies a forensic cleanup validation step to eliminate false positives, and posts verified findings directly onto GitHub pull requests.

### Key Highlights
- **Multi-Perspective Reviews**: Dedicated review agents for core Scala backend code, test suites, and frontend assets.
- **Two-Stage Review & Cleanup**: High-recall candidate generation followed by a strict forensic cleanup agent that cross-checks findings against git diffs, models, database schemas, and source code.
- **Before / After Context**: Passes complete pre-PR and post-PR file context along with unified diffs for precise analysis.
- **OVH AI Endpoints**: Built to work with models hosted on OVHcloud AI Endpoints (compatible with OpenAI client format).
- **Reusable Workflow & Standalone CLI**: Can run either in GitHub Actions CI or locally via `standalone_pr_review.py`.

---

## Reusable Workflow (`.github/workflows/AIreview.yml`)

This reusable workflow orchestrates the entire preparation, parallel review (core, test, frontend), cleanup, and publication process.

### Inputs & Secrets

**Workflow Inputs:**

| Input | Description | Required | Default |
|---|---|---|---|
| `run_id` | CI run ID from the triggering workflow | Yes | - |
| `model` | OVH AI model name | Yes | - |
| `reasoning_effort` | Reasoning effort (`low`, `medium`, `high`) | Yes | - |
| `temperature` | Model temperature | No | `"0.2"` |
| `max_tokens` | Max tokens for AI models | No | `"60000"` |

**Workflow Secrets:**

| Secret | Description | Required |
|---|---|---|
| `OVH_AI_ENDPOINTS_API_KEY` | API key for OVH AI Endpoints | Yes |

### Example Usage

```yaml
name: Trigger AI Code Review

on:
  workflow_run:
    workflows:
      - Scala CI
    types:
      - completed

jobs:
  review:
    if: >
      github.event.workflow_run.conclusion == 'success' &&
      github.event.workflow_run.event == 'pull_request'
    uses: pascal22p/shared-workflows/.github/workflows/AIreview.yml@main
    with:
      run_id: ${{ github.event.workflow_run.id }}
      model: "Qwen3.8-27B"
      reasoning_effort: "medium"
      temperature: "0.0"
      max_tokens: "60000"
    secrets:
      OVH_AI_ENDPOINTS_API_KEY: ${{ secrets.OVH_AI_ENDPOINTS_API_KEY }}
```

---

## Standalone Local Runner (`standalone_pr_review.py`)

A local CLI script to run the complete review pipeline outside GitHub Actions on any repository and PR.

### CLI Options

```bash
python standalone_pr_review.py [OPTIONS]
```

| Argument | Description | Required | Default |
|---|---|---|---|
| `--repository` | Target GitHub repository (`owner/repo`) | Yes | - |
| `--pr` | Pull request number | Yes | - |
| `--github-token` | GitHub API token (`gh` / API access) | Yes | - |
| `--openai-token` | OVH AI Endpoints API token | Yes | - |
| `--model` | OVH AI model name | Yes | - |
| `--reasoning-effort` | Reasoning effort (e.g., `high`, `medium`, `low`) | Yes | - |
| `--temperature` | Model sampling temperature | No | `0.2` |
| `--max-tokens` | Maximum token limit for AI model | No | `40000` |
| `--source-root` | Path to the `shared-workflows` repository | No | `.` |
| `--output-root` | Destination folder for review artifacts | No | `review-runs` |

### Example

```bash
python standalone_pr_review.py \
  --repository owner/my-scala-repo \
  --pr 42 \
  --github-token "$GITHUB_TOKEN" \
  --openai-token "$OVH_AI_ENDPOINTS_API_KEY" \
  --model "deepseek-ai/DeepSeek-R1" \
  --reasoning-effort "high" \
  --max-tokens 40000
```

Review artifacts (context files, candidate reviews, cleanup logs, and final review JSONs) will be generated in `review-runs/run-<timestamp>/`.

---

## Requirements

- **Python 3.10+** with `openai` package installed:
  ```bash
  pip install openai
  ```
- **GitHub CLI (`gh`)** installed and authenticated (or a valid GitHub personal access token).
- **OVHcloud AI Endpoints API Key** with access to the configured LLM models.

---

## License

This project is released into the public domain under the [Unlicense](LICENSE).
