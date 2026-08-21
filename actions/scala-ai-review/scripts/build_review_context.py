from pathlib import Path


def fence_lang(name: str) -> str:
    return Path(name).suffix.lstrip(".")


def build_context(
        output_path: Path,
        changed_files_path: Path,
        additional_files_path: Path,
        before_dir: Path,
        after_dir: Path,
        diff_path: Path,
):
    with output_path.open("w", encoding="utf-8") as out:
        # ----------------------------------------------------
        # Changed files
        # ----------------------------------------------------
        out.write("# 1. Changed files\n\n")

        if changed_files_path.exists():
            out.write(
                changed_files_path.read_text(encoding="utf-8")
            )

        out.write("\n\n")

        # ----------------------------------------------------
        # Additional context files
        # ----------------------------------------------------
        out.write("# 2. Additional context files (unchanged by the PR)\n\n")

        additional_files = []

        if additional_files_path.exists():
            additional_files = [
                line.strip()
                for line in additional_files_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

            out.write(
                additional_files_path.read_text(encoding="utf-8")
            )

        out.write("\n\n")

        # ----------------------------------------------------
        # BEFORE
        # ----------------------------------------------------
        out.write(
            "# 3. Source of the changed files before the PR\n\n"
        )

        if before_dir.exists():
            for file in sorted(before_dir.iterdir()):
                out.write(f"## {file.name}\n\n")
                out.write(f"```{fence_lang(file.name)}\n")
                out.write(
                    file.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )
                out.write("\n```\n\n")

        # ----------------------------------------------------
        # AFTER
        # ----------------------------------------------------
        out.write(
            "# 4. Source of the changed files after the PR\n\n"
        )

        if after_dir.exists():
            for file in sorted(after_dir.iterdir()):
                out.write(f"## {file.name}\n\n")
                out.write(f"```{fence_lang(file.name)}\n")
                out.write(
                    file.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )
                out.write("\n```\n\n")

        # ----------------------------------------------------
        # ADDITIONAL FILE CONTENT
        # ----------------------------------------------------
        out.write(
            "# 5. Source of additional context files\n\n"
        )

        if additional_files:
            for filename in sorted(additional_files):
                file = Path(filename)

                # Additional files are expected to be available
                # in the after directory at the PR HEAD.
                source = after_dir / Path(filename).name

                if not source.exists():
                    # Fall back to the file name directly if the
                    # directory structure isn't preserved.
                    source = after_dir / file.name

                if not source.exists():
                    out.write(
                        f"## {filename}\n\n"
                        f"File not found in additional context source.\n\n"
                    )
                    continue

                out.write(f"## {filename}\n\n")
                out.write(f"```{fence_lang(filename)}\n")
                out.write(
                    source.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )
                out.write("\n```\n\n")

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
    output = Path("review-context/full-context.md")

    changed_files = Path("changed-files.txt")
    additional_files = Path("additional-files.txt")

    before = Path("review-context/before")
    after = Path("review-context/after")

    pr_diff = Path("review-context/pr.diff")

    build_context(
        output,
        changed_files,
        additional_files,
        before,
        after,
        pr_diff,
    )

    if output.exists():
        print(
            f"Context size: {output.stat().st_size:,} bytes"
        )


if __name__ == "__main__":
    main()