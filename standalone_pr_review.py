#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

GITHUB_API = "https://api.github.com"


def github_api(
        token: str,
        path: str,
        accept: str = "application/vnd.github+json",
) -> bytes:
    request = Request(
        f"{GITHUB_API}{path}",
        headers={
            "Accept": accept,
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urlopen(request) as response:
            return response.read()
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"GitHub API request failed ({error.code}): {body}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"GitHub API request failed: {error}"
        ) from error


def github_json(token: str, path: str):
    return json.loads(
        github_api(token, path).decode("utf-8", errors="ignore")
    )


def github_diff(token: str, repository: str, pr_number: int) -> str:
    return github_api(
        token,
        f"/repos/{repository}/pulls/{pr_number}",
        accept="application/vnd.github.v3.diff",
    ).decode("utf-8", errors="ignore")


def run_python_script(
        script: Path,
        cwd: Path,
        environment: dict[str, str],
        *args: str,
):
    command = [sys.executable, str(script), *args]

    print(f"Running: {' '.join(command)}", file=sys.stderr)

    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        raise RuntimeError(
            f"{script.name} failed with exit code {result.returncode}"
        )


def run_shell_script(
        script: Path,
        cwd: Path,
        environment: dict[str, str],
):
    command = ["bash", str(script)]

    print(f"Running: {' '.join(command)}", file=sys.stderr)

    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        raise RuntimeError(
            f"{script.name} failed with exit code {result.returncode}"
        )


def require_file(path: Path):
    if not path.exists():
        raise RuntimeError(f"Required file does not exist: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the Scala AI PR review locally."
    )

    parser.add_argument(
        "--repository",
        required=True,
        help="GitHub repository, e.g. owner/repository.",
    )
    parser.add_argument(
        "--pr",
        type=int,
        required=True,
        help="Pull request number.",
    )
    parser.add_argument(
        "--github-token",
        required=True,
        help="GitHub API token.",
    )
    parser.add_argument(
        "--openai-token",
        required=True,
        help="OVH AI Endpoints API token.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="OVH AI model.",
    )
    parser.add_argument(
        "--reasoning-effort",
        required=True,
        help="Reasoning effort.",
    )
    parser.add_argument(
        "--temperature",
        default="0.2",
        help="Model temperature. Defaults to 0.2.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("."),
        help="Root of the shared-workflows checkout.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("review-runs"),
        help="Directory containing individual review runs.",
    )

    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()

    prepare_scripts = (
            source_root
            / "actions"
            / "scala-ai-review-prepare"
            / "scripts"
    )
    code_scripts = (
            source_root
            / "actions"
            / "scala-ai-review"
            / "scripts"
    )
    test_scripts = (
            source_root
            / "actions"
            / "scala-ai-test-review"
            / "scripts"
    )
    frontend_scripts = (
            source_root
            / "actions"
            / "scala-ai-frontend-review"
            / "scripts"
    )
    cleanup_scripts = (
            source_root
            / "actions"
            / "scala-ai-review-cleanup"
            / "scripts"
    )

    required_files = [
        prepare_scripts / "core_review_prompt.md",
        prepare_scripts / "read_changed_files.sh",
        prepare_scripts / "read_additional_files.sh",
        code_scripts / "build_review_context.py",
        code_scripts / "run_ai_review.py",
        test_scripts / "build_test_review_context.py",
        test_scripts / "run_ai_test_review.py",
        frontend_scripts / "build_frontend_review_context.py",
        frontend_scripts / "run_ai_frontend_review.py",
        cleanup_scripts / "cleanup_prompt.md",
        cleanup_scripts / "run_ai_cleanup_review.py",
        ]

    for path in required_files:
        require_file(path)

    print(f"Getting PR #{args.pr} information...", file=sys.stderr)

    pr = github_json(
        args.github_token,
        f"/repos/{args.repository}/pulls/{args.pr}",
    )

    base_sha = pr["base"]["sha"]
    head_sha = pr["head"]["sha"]

    print(f"Base SHA: {base_sha}", file=sys.stderr)
    print(f"Head SHA: {head_sha}", file=sys.stderr)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    output_root.mkdir(parents=True, exist_ok=True)

    run_dir = output_root / f"pr-{args.pr}-{timestamp}"

    suffix = 1
    while run_dir.exists():
        run_dir = output_root / f"pr-{args.pr}-{timestamp}-{suffix}"
        suffix += 1

    run_dir.mkdir(parents=True, exist_ok=False)

    print(f"Run directory: {run_dir}", file=sys.stderr)

    (run_dir / "pr.json").write_text(
        json.dumps(pr, indent=2),
        encoding="utf-8",
    )

    print("Getting PR files...", file=sys.stderr)

    pr_files = github_json(
        args.github_token,
        f"/repos/{args.repository}/pulls/{args.pr}/files?per_page=100",
    )

    (run_dir / "pr-files.json").write_text(
        json.dumps(pr_files, indent=2),
        encoding="utf-8",
    )

    changed_files = [item["filename"] for item in pr_files]

    (run_dir / "changed-files.txt").write_text(
        "\n".join(changed_files) + "\n",
        encoding="utf-8",
        )

    core_prompt_source = prepare_scripts / "core_review_prompt.md"
    core_prompt_target = (
            run_dir / "review-context" / "core_review_prompt.md"
    )

    core_prompt_target.parent.mkdir(parents=True, exist_ok=True)

    core_prompt_target.write_text(
        core_prompt_source.read_text(
            encoding="utf-8",
            errors="ignore",
        ),
        encoding="utf-8",
    )

    require_file(core_prompt_target)

    print("Getting complete PR diff...", file=sys.stderr)

    diff = github_diff(
        args.github_token,
        args.repository,
        args.pr,
    )

    (run_dir / "review-context" / "pr.diff").write_text(
        diff,
        encoding="utf-8",
    )

    environment = os.environ.copy()

    environment.update({
        "REPOSITORY": args.repository,
        "PR_NUMBER": str(args.pr),
        "BASE_SHA": base_sha,
        "HEAD_SHA": head_sha,
        "GH_TOKEN": args.github_token,
        "GITHUB_TOKEN": args.github_token,
        "OVH_AI_ENDPOINTS_API_KEY": args.openai_token,
        "REVIEW_MODEL": args.model,
        "REASONING_EFFORT": args.reasoning_effort,
        "TEMPERATURE": args.temperature,
        "CONTEXT_DIR": "review-context",
    })

    run_shell_script(
        prepare_scripts / "read_changed_files.sh",
        run_dir,
        environment,
        )

    run_shell_script(
        prepare_scripts / "read_additional_files.sh",
        run_dir,
        environment,
        )

    run_python_script(
        code_scripts / "build_review_context.py",
        run_dir,
        environment,
        "review-context/context-code-review.md",
        )

    run_python_script(
        test_scripts / "build_test_review_context.py",
        run_dir,
        environment,
        "review-context/context-test-review.md",
        )

    run_python_script(
        frontend_scripts / "build_frontend_review_context.py",
        run_dir,
        environment,
        "review-context/context-frontend-review.md",
        )

    run_python_script(
        code_scripts / "run_ai_review.py",
        run_dir,
        environment,
        )

    run_python_script(
        test_scripts / "run_ai_test_review.py",
        run_dir,
        environment,
        )

    run_python_script(
        frontend_scripts / "run_ai_frontend_review.py",
        run_dir,
        environment,
        )

    cleanup_jobs = [
        {
            "review_file": "review.json",
            "output_file": "review-final.json",
            "log_file": "review-log.json",
            "context_file": "context-code-review.md",
        },
        {
            "review_file": "review-test.json",
            "output_file": "review-test-final.json",
            "log_file": "review-test-log.json",
            "context_file": "context-test-review.md",
        },
        {
            "review_file": "review-frontend.json",
            "output_file": "review-frontend-final.json",
            "log_file": "review-frontend-log.json",
            "context_file": "context-frontend-review.md",
        },
    ]

    for job in cleanup_jobs:
        environment.update({
            "REVIEW_FILE": job["review_file"],
            "CLEANUP_OUTPUT_FILE": job["output_file"],
            "CLEANUP_LOG_FILE": job["log_file"],
            "REVIEW_CONTEXT_FILE": job["context_file"],
        })

        run_python_script(
            cleanup_scripts / "run_ai_cleanup_review.py",
            run_dir,
            environment,
            )

    final_files = {
        "code": run_dir / "review-context" / "review-final.json",
        "test": run_dir / "review-context" / "review-test-final.json",
        "frontend": (
                run_dir
                / "review-context"
                / "review-frontend-final.json"
        ),
    }

    final_reviews = {}

    for name, path in final_files.items():
        require_file(path)

        final_reviews[name] = json.loads(
            path.read_text(encoding="utf-8")
        )

    result = {
        "repository": args.repository,
        "pull_request": args.pr,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "run_directory": str(run_dir),
        "reviews": final_reviews,
    }

    result_file = run_dir / "review-result.json"

    result_file.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    markdown = build_review_markdown(
        args.repository,
        args.pr,
        final_reviews,
    )

    markdown_file = run_dir / "review-result.md"

    markdown_file.write_text(
        markdown,
        encoding="utf-8",
    )

    print(
        f"\nMarkdown review: {markdown_file}"
    )

def review_to_markdown(title: str, review: dict) -> str:
    lines = [
        f"# {title}",
        "",
    ]

    summary = review.get("summary")
    risk = review.get("risk")

    if risk is not None:
        lines.extend([
            f"**Risk:** `{risk}`",
            "",
        ])

    if summary:
        lines.extend([
            "## Summary",
            "",
            str(summary),
            "",
        ])

    findings = review.get("findings", [])

    lines.extend([
        f"## Findings ({len(findings)})",
        "",
    ])

    if not findings:
        lines.extend([
            "No findings.",
            "",
        ])
        return "\n".join(lines)

    for index, finding in enumerate(findings, start=1):
        severity = finding.get("severity", "MEDIUM")
        finding_title = finding.get(
            "title",
            "Code review finding",
        )
        file = finding.get("file")
        line = finding.get("line")
        body = finding.get("body", "")

        location = ""
        if file:
            location = f"`{file}"
            if line:
                location += f":{line}"
            location += "`"

        lines.extend([
            f"### {index}. {severity} — {finding_title}",
            "",
        ])

        if location:
            lines.extend([
                f"**Location:** {location}",
                "",
            ])

        if body:
            lines.extend([
                body,
                "",
            ])

    return "\n".join(lines)


def build_review_markdown(
        repository: str,
        pull_request: int,
        reviews: dict[str, dict],
) -> str:
    lines = [
        "# Scala AI Pull Request Review",
        "",
        f"**Repository:** `{repository}`  ",
        f"**Pull Request:** `#{pull_request}`",
        "",
        "---",
        "",
    ]

    sections = [
        ("Code Review", "code"),
        ("Test Review", "test"),
        ("Frontend Review", "frontend"),
    ]

    for title, key in sections:
        lines.append(
            review_to_markdown(
                title,
                reviews[key],
            )
        )
        lines.extend([
            "---",
            "",
        ])

    return "\n".join(lines)

if __name__ == "__main__":
    main()
