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
    Determine which lines are valid RIGHT-side targets from a unified diff.

    Returns:
        Mapping of filename to a set of valid RIGHT-side line numbers.
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
            valid_lines.setdefault(
                current_file,
                set()
            ).add(new_line)

            new_line += 1
            continue

        if not line.startswith("-") and not line.startswith("---"):
            # Context line:
            # still a valid RIGHT-side review target.
            valid_lines.setdefault(
                current_file,
                set()
            ).add(new_line)

            new_line += 1

    return valid_lines


def is_frontend_file(file: str) -> bool:
    """
    Return True if the given path is a frontend file this review
    covers: a Twirl template (.scala.html, .scala.xml, .scala.txt),
    CSS/Sass (.css, .scss, .sass), or JavaScript (.js).
    """
    return bool(
        re.search(
            r"\.(scala\.(html|xml|txt)|css|scss|sass|js)$",
            file,
        )
    )


def map_findings(
        findings: list[dict],
        valid_lines: dict[str, set[int]],
        review_model: str,
        reasoning_effort: str
) -> tuple[list[dict], list[dict]]:
    """
    Split findings into two groups.

    1. Inline comments:
       Findings that can be mapped to a valid RIGHT-side PR line.

    2. Outside-scope findings:
       Findings that cannot be mapped to a PR diff line.

    Outside-scope findings are NOT discarded. They are included in
    the top-level review body.

    Findings that are not located in a Twirl, CSS/Sass, or
    JavaScript file are dropped entirely (with a log message),
    since this script only publishes findings from the frontend
    review.
    """
    comments = []
    outside_scope = []

    for finding in findings:
        file = finding.get("file")
        line = finding.get("line")

        # --------------------------------------------------------
        # Only accept findings located in frontend files
        # --------------------------------------------------------

        if not file or not is_frontend_file(file):
            print(
                f"Finding not located in a frontend file "
                f"({file}); dropping."
            )

            continue

        # --------------------------------------------------------
        # Missing or invalid location
        # --------------------------------------------------------

        if not line:
            print(
                "Finding has no valid line; "
                "adding to outside-scope findings."
            )

            outside_scope.append(finding)
            continue

        try:
            line = int(line)
        except Exception:
            print(
                f"Invalid finding line: {file}:{line}; "
                "adding to outside-scope findings."
            )

            outside_scope.append(finding)
            continue

        # --------------------------------------------------------
        # Check whether the line exists in the PR diff
        # --------------------------------------------------------

        file_lines = valid_lines.get(
            file,
            set()
        )

        target_line = line

        if line not in file_lines:
            # AI line numbers can occasionally be off by a small
            # amount. Try to find a nearby valid RIGHT-side line.
            candidates = [
                candidate
                for candidate in file_lines
                if abs(candidate - line) <= 3
            ]

            if candidates:
                target_line = min(
                    candidates,
                    key=lambda candidate: abs(
                        candidate - line
                    )
                )

                print(
                    f"Mapped finding "
                    f"{file}:{line} "
                    f"to changed line "
                    f"{target_line}"
                )

            else:
                print(
                    f"Finding outside PR diff: "
                    f"{file}:{line}"
                )

                outside_scope.append(finding)
                continue

        # --------------------------------------------------------
        # Build inline GitHub comment
        # --------------------------------------------------------

        severity = finding.get(
            "severity",
            "MEDIUM"
        )

        title = finding.get(
            "title",
            "Frontend finding"
        )

        body = finding.get(
            "body",
            ""
        )

        comments.append({
            "path": file,
            "line": target_line,
            "side": "RIGHT",
            "body": (
                f"**{severity} — {title}**\n\n"
                f"{body}\n\n"
                "reviewed by "
                f"OVH {review_model} "
                f"with reasoning effort {reasoning_effort}"
            )
        })

    return comments, outside_scope


def format_outside_scope_findings(
        findings: list[dict],
) -> str:
    """
    Format findings that cannot be attached to a changed PR line.
    """
    if not findings:
        return ""

    body = (
        "## Findings outside the scope of the PR\n\n"
        "The following frontend findings are relevant to the "
        "changed behaviour but could not be attached to a changed "
        "line in the PR diff. They are included here rather than "
        "as inline comments.\n\n"
    )

    for finding in findings:
        severity = finding.get(
            "severity",
            "MEDIUM"
        )

        title = finding.get(
            "title",
            "Frontend finding"
        )

        file = finding.get(
            "file",
            "Unknown file"
        )

        line = finding.get(
            "line",
            "Unknown line"
        )

        finding_body = finding.get(
            "body",
            ""
        )

        body += (
            f"### {severity} — {title}\n\n"
            f"**Location:** `{file}:{line}`\n\n"
            f"{finding_body}\n\n"
        )

    return body


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
    # Load frontend review
    # --------------------------------------------------------

    review_path = Path(
        "review-context/frontend-review.json"
    )

    if not review_path.exists():
        print(
            "frontend-review.json not found"
        )
        return

    review = json.loads(
        review_path.read_text(
            encoding="utf-8"
        )
    )

    findings = review.get(
        "findings",
        []
    )

    # --------------------------------------------------------
    # Determine valid RIGHT-side diff lines
    # --------------------------------------------------------

    valid_lines = parse_diff(
        diff
    )

    # --------------------------------------------------------
    # Map findings
    # --------------------------------------------------------

    comments, outside_scope = map_findings(
        findings,
        valid_lines,
        review_model,
        reasoning_effort
    )

    # GitHub has a practical limit on review comments.
    comments = comments[:50]

    # --------------------------------------------------------
    # Review metadata
    # --------------------------------------------------------

    summary = review.get(
        "summary",
        "AI frontend review completed."
    )

    risk = review.get(
        "risk",
        "LOW"
    )

    # --------------------------------------------------------
    # Build review body
    # --------------------------------------------------------

    review_body = (
        "## 🤖 Scala AI Frontend Review\n\n"
        f"**Risk:** `{risk}`\n\n"
        f"{summary}\n\n"
    )

    # --------------------------------------------------------
    # Add findings that cannot be attached to the PR diff
    # --------------------------------------------------------

    review_body += format_outside_scope_findings(
        outside_scope
    )

    # --------------------------------------------------------
    # Context information
    # --------------------------------------------------------

    review_body += (
        "## Review context\n\n"
        "- build.sbt, project/*\n"
        "- Complete BEFORE source\n"
        "- Complete AFTER source\n"
        "- Complete PR diff\n\n"
        "reviewed by "
        f"OVH {review_model} "
        f"with reasoning effort {reasoning_effort}"
    )

    # --------------------------------------------------------
    # Print statistics
    # --------------------------------------------------------

    print(
        f"Total frontend findings: "
        f"{len(findings)}"
    )

    print(
        f"Inline findings: "
        f"{len(comments)}"
    )

    print(
        f"Outside-scope findings: "
        f"{len(outside_scope)}"
    )

    # --------------------------------------------------------
    # Build GitHub review payload
    # --------------------------------------------------------

    payload = {
        "body": review_body,
        "event": "COMMENT",
        "comments": comments,
    }

    # --------------------------------------------------------
    # Try full review with inline comments
    # --------------------------------------------------------

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
        print(
            "Inline comment review failed, "
            "falling back to summary-only:"
        )

        print(
            "STDOUT:",
            result.stdout
        )

        print(
            "STDERR:",
            result.stderr
        )

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
            input=json.dumps(
                fallback_payload
            ),
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            print(
                "STDOUT:",
                result.stdout
            )

            print(
                "STDERR:",
                result.stderr
            )

            raise SystemExit(
                result.returncode
            )

        print(
            "Published summary-only frontend review "
            "(inline comments failed)."
        )

    else:
        print(
            f"Published {len(comments)} "
            "frontend review inline comments."
        )

        if outside_scope:
            print(
                f"Published {len(outside_scope)} "
                "frontend findings in the top-level review."
            )


if __name__ == "__main__":
    main()