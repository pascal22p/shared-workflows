import json
import os
import re
import subprocess

from pathlib import Path


repo = os.environ["REPOSITORY"]
pr = os.environ["PR_NUMBER"]


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

        raise SystemExit(
            result.returncode
        )

    return result.stdout


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

review = json.loads(
    Path(
        "review-context/review.json"
    ).read_text()
)

findings = review.get(
    "findings",
    []
)

# --------------------------------------------------------
# Determine which lines are valid "RIGHT-side" targets
#
# GitHub's review API accepts `line` + `side` directly
# instead of a hand-computed `position` offset. This
# avoids manually reconstructing GitHub's diff-position
# math (which is easy to get subtly wrong per-file).
#
# GitHub still requires the (file, line) to actually
# appear in the diff it computed, so we build the set of
# valid lines per file: any line shown on the right-hand
# side of a hunk (added lines AND unchanged context
# lines), since GitHub allows comments on context lines
# too, not only added ones.
# --------------------------------------------------------

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

        match = re.search(
            r"\+(\d+)(?:,(\d+))?",
            line
        )

        if match:

            new_line = int(
                match.group(1)
            )

        continue

    if (
        current_file is None
        or new_line is None
    ):
        continue

    if (
        line.startswith("+")
        and not line.startswith("+++")
    ):

        valid_lines.setdefault(
            current_file, set()
        ).add(new_line)

        new_line += 1

        continue

    if (
        not line.startswith("-")
        and not line.startswith("---")
    ):

        # context line: still a valid RIGHT-side target
        valid_lines.setdefault(
            current_file, set()
        ).add(new_line)

        new_line += 1

# --------------------------------------------------------
# Build inline comments
# --------------------------------------------------------

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

            print(
                f"Cannot map finding: "
                f"{file}:{line}"
            )

            continue

    severity = finding.get(
        "severity",
        "MEDIUM"
    )

    title = finding.get(
        "title",
        "Code review finding"
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
            "_Scala 3 SemanticDB + "
            f"OVH {os.environ['REVIEW_MODEL']}"
        )
    })

comments = comments[:50]

summary = review.get(
    "summary",
    "AI code review completed."
)

risk = review.get(
    "risk",
    "LOW"
)

review_body = (
    "## 🤖 Scala AI Code Review\n\n"
    f"**Risk:** `{risk}`\n\n"
    f"{summary}\n\n"
    "Review context:\n"
    "- Scala 3 SemanticDB\n"
    "- Complete BEFORE source\n"
    "- Complete AFTER source\n"
    "- Complete PR diff\n"
    f"- Reasoning effort: `{os.environ['REASONING_EFFORT']}`\n"
    f"- OVH `{os.environ['REVIEW_MODEL']}`\n"
)

# --------------------------------------------------------
# Try full review with inline comments.
# Fall back to a summary-only review if GitHub rejects
# any of the inline comments (e.g. bad position mapping),
# so a single bad comment never fails the whole review.
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

        raise SystemExit(
            result.returncode
        )

    print(
        "Published summary-only review "
        "(inline comments failed)."
    )

else:

    print(
        f"Published {len(comments)} "
        "inline comments."
    )
