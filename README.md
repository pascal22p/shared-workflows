# Shared Workflows

This repository contains shared GitHub Actions and workflows used for code quality and automated reviews, primarily focused on Scala projects.

## Actions

### Scala AI Review Components

The AI review process is split into several specialized actions to provide focused feedback on different parts of the codebase. All review actions leverage SemanticDB information (where applicable) and OVH AI Endpoints.

#### 1. Core Review (`actions/scala-ai-review`)
Performs the primary automated code review on Scala logic and implementation.

#### 2. Test Review (`actions/scala-ai-test-review`)
Specialized review for Scala test files, focusing on test coverage, style, and correctness.

#### 3. Frontend Review (`actions/scala-ai-frontend-review`)
Focused on frontend-related files (JS, CSS, etc.) within the Scala project.

#### Common Features
- **Before/After Analysis**: Captures both original and modified versions of files for comprehensive comparison.
- **Multi-Model Support**: Configurable to use various models available through OVH AI Endpoints.
- **Automated Feedback**: Automatically publishes AI-generated comments as a review on the Pull Request.

#### Inputs (Review Actions)
| Name | Description | Required |
|------|-------------|----------|
| `model` | The OVH AI model name to use. | Yes |
| `reasoning_effort` | Reasoning depth for the model (e.g., `low`, `medium`, `high`). | Yes |
| `ovh_api_key` | API key for OVH AI Endpoints. | Yes |
| `pr_number` | The number of the Pull Request to review. | Yes |

#### Preparation Action (`actions/scala-ai-review-prepare`)
A prerequisite action that gathers the necessary context (diffs, files, SemanticDB) used by the review components.

#### Requirements
- Python 3.x with `openai` packages (installed automatically by the actions).
- An active OVH AI Endpoints API key.

---

## Workflows

### AI Review Workflow (`.github/workflows/AIreview.yml`)

A reusable workflow (`workflow_call`) that orchestrates the Scala AI Review components. It runs the preparation step followed by three parallel review jobs for core code, tests, and frontend.

#### Workflow Jobs:
1. **Prepare**: Gathers context and uploads it as an artifact.
2. **Code Review**: Executes the Core AI review.
3. **Test Review**: Executes the Test AI review.
4. **Frontend Review**: Executes the Frontend AI review.

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

---

## License

This project is released into the public domain under the [Unlicense](LICENSE).
