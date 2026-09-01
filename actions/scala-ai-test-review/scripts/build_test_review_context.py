from pathlib import Path
import argparse


def fence_lang(name: str) -> str:
    return Path(name).suffix.lstrip(".")


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
            "# 2. Additional context files (unchanged by the PR)\n\n"
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
        description="Build the test review context."
    )

    parser.add_argument(
        "output",
        help="Path to the generated context file.",
    )

    parser.add_argument(
        "--context-dir",
        type=Path,
        default=Path("review-context"),
        help=(
            "Directory containing before/, after/, "
            "additional/, and pr.diff."
        ),
    )

    args = parser.parse_args()

    context_dir = args.context_dir
    output = Path(args.output)

    build_context(
        output,
        context_dir / "before",
        context_dir / "after",
        context_dir / "additional",
        context_dir / "pr.diff",
        )

    if output.exists():
        print(
            f"Context size: {output.stat().st_size:,} bytes"
        )


if __name__ == "__main__":
    main()