from pathlib import Path


def fence_lang(name: str) -> str:
    if name.endswith(".scala.html"):
        return "html"
    if name.endswith(".scala"):
        return "scala"
    if name.endswith(".js"):
        return "javascript"
    if name.endswith(".css"):
        return "css"
    if name.endswith(".conf"):
        return "conf"
    return ""


output = Path(
    "review-context/full-context.md"
)

with output.open(
    "w",
    encoding="utf-8",
) as out:

    # ----------------------------------------------------
    # SemanticDB
    # ----------------------------------------------------

    out.write(
        "# 1. SCALA SEMANTICDB\n\n"
    )

    semantic = Path(
        "review-context/semanticdb.md"
    )

    out.write(
        semantic.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    )

    out.write("\n\n")

    # ----------------------------------------------------
    # Changed files
    # ----------------------------------------------------

    out.write(
        "# 2. CHANGED FILES\n\n"
    )

    out.write(
        Path(
            "changed-files.txt"
        ).read_text(
            encoding="utf-8"
        )
    )

    out.write("\n\n")

    # ----------------------------------------------------
    # BEFORE
    # ----------------------------------------------------

    out.write(
        "# 3. COMPLETE SOURCE BEFORE PR\n\n"
    )

    before = Path(
        "review-context/before"
    )

    for file in sorted(
        before.iterdir()
    ):

        out.write(
            f"## {file.name}\n\n"
        )

        out.write(
            f"```{fence_lang(file.name)}\n"
        )

        out.write(
            file.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        )

        out.write(
            "\n```\n\n"
        )

    # ----------------------------------------------------
    # AFTER
    # ----------------------------------------------------

    out.write(
        "# 4. COMPLETE SOURCE AFTER PR\n\n"
    )

    after = Path(
        "review-context/after"
    )

    for file in sorted(
        after.iterdir()
    ):

        out.write(
            f"## {file.name}\n\n"
        )

        out.write(
            f"```{fence_lang(file.name)}\n"
        )

        out.write(
            file.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        )

        out.write(
            "\n```\n\n"
        )

    # ----------------------------------------------------
    # DIFF
    # ----------------------------------------------------

    out.write(
        "# 5. COMPLETE PR DIFF\n\n"
    )

    out.write(
        "```diff\n"
    )

    out.write(
        Path(
            "review-context/pr.diff"
        ).read_text(
            encoding="utf-8",
            errors="ignore"
        )
    )

    out.write(
        "\n```\n"
    )

print(
    f"Context size: "
    f"{output.stat().st_size:,} bytes"
)
