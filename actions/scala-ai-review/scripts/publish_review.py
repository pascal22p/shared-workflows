import json
import os
import re
import subprocess

from pathlib import Path


def gh_api(*args):
    result = subprocess.run(
        [
            "gh",
            "api",
            *args
        ],
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise SystemExit(result.returncode)

    return result.stdout


def parse_diff(diff: str) -> dict[str, set[int]]:
    """
    Determine which lines are valid "RIGHT-side" targets from a unified diff.
    Returns a mapping of filename to a set of valid line numbers.
    """
    valid_lines = {}
    current_file = None
    new_line = None

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            current_file = None
            new_line = None
            continue

        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue

        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if match:
                new_line = int(match.group(1))
            continue

        if current_file is None or new_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            valid_lines.setdefault(current_file, set()).add(new_line)
            new_line += 1
            continue

        if not line.startswith("-") and not line.startswith("---"):
            # context line: still a valid RIGHT-side target
            valid_lines.setdefault(current_file, set()).add(new_line)
            new_line += 1
    
    return valid_lines


def map_findings(findings: list[dict], valid_lines: dict[str, set[int]], review_model: str) -> list[dict]:
    """
    Map AI findings to valid lines in the diff, snapping to nearest valid line if needed.
    """
    comments = []
    for finding in findings:
        file = finding.get("file")
        line = finding.get("line")

        if not file or not line:
            continue

        try:
            line = int(line)
        except Exception:
            continue

        file_lines = valid_lines.get(file, set())
        target_line = line

        if line not in file_lines:
            # AI line numbers are sometimes off by one or
            # two from the exact diff hunk boundary; snap to
            # the nearest valid line within a small window
            # rather than dropping the finding outright.
            candidates = [
                l for l in file_lines
                if abs(l - line) <= 3
            ]

            if candidates:
                target_line = min(
                    candidates,
                    key=lambda l: abs(l - line)
                )
            else:
                print(f"Cannot map finding: {file}:{line}")
                continue

        severity = finding.get("severity", "MEDIUM")
        title = finding.get("title", "Code review finding")
        body = finding.get("body", "")

        comments.append({
            "path": file,
            "line": target_line,
            "side": "RIGHT",
            "body": (
                f"**{severity} — {title}**\n\n"
                f"{body}\n\n"
                "_Scala 3 SemanticDB + "
                f"OVH {review_model}"
            )
        })
    return comments


def main():
    repo = os.environ["REPOSITORY"]
    pr = os.environ["PR_NUMBER"]
    review_model = os.environ["REVIEW_MODEL"]
    reasoning_effort = os.environ["REASONING_EFFORT"]

    # --------------------------------------------------------
    # Get diff
    # --------------------------------------------------------

    diff = gh_api(
        f"repos/{repo}/pulls/{pr}",
        "-H",
        "Accept: application/vnd.github.v3.diff"
    )

    # --------------------------------------------------------
    # Load review
    # --------------------------------------------------------

    review_path = Path("review-context/review.json")
    if not review_path.exists():
        print("review.json not found")
        return

    review = json.loads(review_path.read_text())
    findings = review.get("findings", [])

    # --------------------------------------------------------
    # Determine which lines are valid "RIGHT-side" targets
    # --------------------------------------------------------

    valid_lines = parse_diff(diff)

    # --------------------------------------------------------
    # Build inline comments
    # --------------------------------------------------------

    comments = map_findings(findings, valid_lines, review_model)
    comments = comments[:50]

    summary = review.get("summary", "AI code review completed.")
    risk = review.get("risk", "LOW")

    review_body = (
        "## 🤖 Scala AI Code Review\n\n"
        f"**Risk:** `{risk}`\n\n"
        f"{summary}\n\n"
        "Review context:\n"
        "- build.sbt, project/*\n"
        "- Complete BEFORE source\n"
        "- Complete AFTER source\n"
        "- Complete PR diff\n"
        f"- Reasoning effort: `{reasoning_effort}`\n"
        f"- OVH `{review_model}`\n"
    )

    # --------------------------------------------------------
    # Try full review with inline comments.
    # --------------------------------------------------------

    payload = {
        "body": review_body,
        "event": "COMMENT",
        "comments": comments,
    }

    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls/{pr}/reviews",
            "--method",
            "POST",
            "--input",
            "-"
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("Inline comment review failed, falling back to summary-only:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        fallback_payload = {
            "body": review_body,
            "event": "COMMENT",
        }

        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/pulls/{pr}/reviews",
                "--method",
                "POST",
                "--input",
                "-"
            ],
            input=json.dumps(fallback_payload),
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            raise SystemExit(result.returncode)

        print("Published summary-only review (inline comments failed).")
    else:
        print(f"Published {len(comments)} inline comments.")


if __name__ == "__main__":
    main()
