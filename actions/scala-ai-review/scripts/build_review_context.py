from pathlib import Path
import argparse


FRONTEND_EXTENSIONS = {
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}


def fence_lang(name: str) -> str:
    return Path(name).suffix.lstrip(".")


def is_test_file(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}

    return bool(parts & {"test", "it"})


def is_frontend_file(path: Path) -> bool:
    name = path.name.lower()

    return (
            name.endswith(".scala.xml")
            or name.endswith(".scala.txt")
            or any(
        name.endswith(extension)
        for extension in FRONTEND_EXTENSIONS
    )
    )


def is_code_review_file(path: Path) -> bool:
    return not is_test_file(path) and not is_frontend_file(path)


def write_directory(
        out,
        directory: Path,
) -> None:
    if not directory.exists():
        return

    for file in sorted(directory.rglob("*")):
        if not file.is_file():
            continue

        relative_path = file.relative_to(directory)

        if not is_code_review_file(relative_path):
            continue

        out.write(f"## {relative_path}\n\n")
        out.write(f"```{fence_lang(file.name)}\n")
        out.write(
            file.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )
        out.write("\n```\n\n")


def build_context(
        output_path: Path,
        before_dir: Path,
        after_dir: Path,
        additional_dir: Path,
        diff_path: Path,
):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w", encoding="utf-8") as out:
        # ----------------------------------------------------
        # Changed files
        # ----------------------------------------------------
        out.write("# 1. Changed files\n\n")

        write_directory(
            out,
            after_dir,
        )

        # ----------------------------------------------------
        # Additional context files
        # ----------------------------------------------------
        out.write(
            "# 2. Additional context files "
            "(unchanged by the PR)\n\n"
        )

        write_directory(
            out,
            additional_dir,
        )

        # ----------------------------------------------------
        # BEFORE
        # ----------------------------------------------------
        out.write(
            "# 3. Source of the changed files before the PR\n\n"
        )

        write_directory(
            out,
            before_dir,
        )

        # ----------------------------------------------------
        # AFTER
        # ----------------------------------------------------
        out.write(
            "# 4. Source of the changed files after the PR\n\n"
        )

        write_directory(
            out,
            after_dir,
        )

        # ----------------------------------------------------
        # DIFF
        # ----------------------------------------------------
        out.write("# 5. Complete PR diff\n\n")
        out.write("```diff\n")

        if diff_path.exists():
            out.write(
                diff_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

        out.write("\n```\n")


def main():
    parser = argparse.ArgumentParser(
        description="Build the PR review context."
    )

    parser.add_argument(
        "output",
        help="Path of the generated context file.",
    )

    parser.add_argument(
        "--context-dir",
        type=Path,
        default=Path("review-context"),
        help=(
            "Directory containing before/, after/, additional/, "
            "and pr.diff. Defaults to review-context."
        ),
    )

    args = parser.parse_args()

    context_dir = args.context_dir

    before = context_dir / "before"
    after = context_dir / "after"
    additional = context_dir / "additional"
    pr_diff = context_dir / "pr.diff"

    build_context(
        Path(args.output),
        before,
        after,
        additional,
        pr_diff,
    )

    output = Path(args.output)

    if output.exists():
        print(
            f"Context size: {output.stat().st_size:,} bytes"
        )


if __name__ == "__main__":
    main()