import sys
from pathlib import Path

# Add scripts directory to sys.path to allow importing build_review_context
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from build_review_context import fence_lang, build_context


def test_fence_lang():
    assert fence_lang("test.scala") == "scala"
    assert fence_lang("test.scala.html") == "html"
    assert fence_lang("test.js") == "js"
    assert fence_lang("test.css") == "css"
    assert fence_lang("test.conf") == "conf"
    assert fence_lang("test.txt") == "txt"
    assert fence_lang("test") == ""


def test_build_context(tmp_path):
    output_path = tmp_path / "full-context.md"
    before_dir = tmp_path / "before"
    after_dir = tmp_path / "after"
    additional_dir = tmp_path / "additional"
    diff_path = tmp_path / "pr.diff"

    before_dir.mkdir()
    after_dir.mkdir()
    additional_dir.mkdir()

    (before_dir / "file1.scala").write_text("old content")
    (after_dir / "file1.scala").write_text("new content")
    (additional_dir / "file2.scala").write_text("additional content")
    diff_path.write_text("diff content")

    build_context(
        output_path,
        before_dir,
        after_dir,
        additional_dir,
        diff_path
    )

    content = output_path.read_text()
    assert "# 1. Changed files" in content
    assert "file1.scala" in content
    assert "# 2. Additional context files (unchanged by the PR)" in content
    assert "file2.scala" in content
    assert "additional content" in content
    assert "# 3. Source of the changed files before the PR" in content
    assert "old content" in content
    assert "# 4. Source of the changed files after the PR" in content
    assert "new content" in content
    assert "# 5. Complete PR diff" in content
    assert "diff content" in content
