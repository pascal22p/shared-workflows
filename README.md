# Shared Workflows

This repository contains shared GitHub Actions and workflows used for code quality and automated reviews, primarily focused on Scala projects.

## Actions

### Scala AI Review (`actions/scala-ai-review`)

A composite action that performs automated code reviews on Scala projects using AI via OVH AI Endpoints. It leverages SemanticDB information to provide deep, semantically aware context to the Large Language Model.

#### Features
- **Before/After Analysis**: Captures both original and modified versions of files for comprehensive comparison.
- **Multi-Model Support**: Configurable to use various models available through OVH AI Endpoints.
- **Automated Feedback**: Automatically publishes AI-generated comments as a review on the Pull Request.

#### Inputs
| Name | Description | Required |
|------|-------------|----------|
| `model` | The OVH AI model name to use. | Yes |
| `reasoning_effort` | Reasoning depth for the model (e.g., `low`, `medium`, `high`). | Yes |
| `ovh_api_key` | API key for OVH AI Endpoints. | Yes |
| `pr_number` | The number of the Pull Request to review. | Yes |

#### Requirements
- Python 3.x with `openai` packages (installed automatically by the action).
- An active OVH AI Endpoints API key.

---

## Workflows

### AI Review Workflow (`.github/workflows/AIreview.yml`)

A reusable workflow (`workflow_call`) that orchestrates the Scala AI Review process. It streamlines the setup by handling PR metadata extraction and artifact retrieval.

#### Workflow Steps:
1. **Identify PR**: Determines the Pull Request associated with the triggering CI run.
3. **Capture Context**: Fetches the full content of changed files (Scala, JS, CSS, etc.) at both the base and head SHAs.
4. **Execute Review**: Calls the `scala-ai-review` action with the gathered context.
5. **Artifact Storage**: Uploads the complete review context for audit and debugging purposes.

#### Usage Example:
```yaml
jobs:
  review:
    uses: pascal22p/shared-workflows/.github/workflows/AIreview.yml@{version}
    with:
      run_id: ${{ github.run_id }}
      model: "chosen-model-name"
      reasoning_effort: "high"
    secrets:
      OVH_AI_ENDPOINTS_API_KEY: ${{ secrets.OVH_AI_ENDPOINTS_API_KEY }}
```

### Qodana Code Quality (`.github/workflows/qodana_code_quality.yml`)

Integrates [JetBrains Qodana](https://www.jetbrains.com/qodana/) for static analysis.

---

## License

This project is released into the public domain under the [Unlicense](LICENSE).
