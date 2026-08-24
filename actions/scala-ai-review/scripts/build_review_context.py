from pathlib import Path
import sys


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
        # ADDITIONAL FILE CONTENT
        # ----------------------------------------------------
        out.write(
            "# 5. Source of additional context files\n\n"
        )

        write_directory(
            out,
            additional_dir,
        )

        # ----------------------------------------------------
        # DIFF
        # ----------------------------------------------------
        out.write("# 6. Complete PR diff\n\n")
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
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: build_review_context.py <output-path>"
        )

    output = Path(sys.argv[1])

    before = Path("review-context/before")
    after = Path("review-context/after")
    additional = Path("review-context/additional")
    pr_diff = Path("review-context/pr.diff")

    build_context(
        output,
        before,
        after,
        additional,
        pr_diff,
    )

    if output.exists():
        print(
            f"Context size: {output.stat().st_size:,} bytes"
        )


if __name__ == "__main__":
    main()