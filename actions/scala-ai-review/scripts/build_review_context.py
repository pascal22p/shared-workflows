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


def build_context(
    output_path: Path,
    semantic_path: Path,
    changed_files_path: Path,
    before_dir: Path,
    after_dir: Path,
    diff_path: Path
):
    with output_path.open("w", encoding="utf-8") as out:
        # ----------------------------------------------------
        # Changed files
        # ----------------------------------------------------
        out.write("# 1. Changed files plus build.sbt, project/*\n\n")
        if changed_files_path.exists():
            out.write(changed_files_path.read_text(encoding="utf-8"))
        out.write("\n\n")

        # ----------------------------------------------------
        # BEFORE
        # ----------------------------------------------------
        out.write("# 2. Source of the files in section 1. before the PR\n\n")
        if before_dir.exists():
            for file in sorted(before_dir.iterdir()):
                out.write(f"## {file.name}\n\n")
                out.write(f"```{fence_lang(file.name)}\n")
                out.write(file.read_text(encoding="utf-8", errors="ignore"))
                out.write("\n```\n\n")

        # ----------------------------------------------------
        # AFTER
        # ----------------------------------------------------
        out.write("# 3. Source of the files in section 1. after the PR\n\n")
        if after_dir.exists():
            for file in sorted(after_dir.iterdir()):
                out.write(f"## {file.name}\n\n")
                out.write(f"```{fence_lang(file.name)}\n")
                out.write(file.read_text(encoding="utf-8", errors="ignore"))
                out.write("\n```\n\n")

        # ----------------------------------------------------
        # DIFF
        # ----------------------------------------------------
        out.write("# 4. Complete PR diff\n\n")
        out.write("```diff\n")
        if diff_path.exists():
            out.write(diff_path.read_text(encoding="utf-8", errors="ignore"))
        out.write("\n```\n")


def main():
    output = Path("review-context/full-context.md")
    semantic = Path("review-context/semanticdb.md")
    changed_files = Path("changed-files.txt")
    before = Path("review-context/before")
    after = Path("review-context/after")
    pr_diff = Path("review-context/pr.diff")

    build_context(
        output,
        semantic,
        changed_files,
        before,
        after,
        pr_diff
    )

    if output.exists():
        print(f"Context size: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
