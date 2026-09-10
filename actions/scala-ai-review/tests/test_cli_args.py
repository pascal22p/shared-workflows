import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def test_run_ai_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-review" / "scripts" / "run_ai_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--api-key" in result.stdout
    assert "--max-tokens" in result.stdout
    assert "--context-dir" in result.stdout


def test_run_ai_frontend_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-frontend-review" / "scripts" / "run_ai_frontend_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--api-key" in result.stdout
    assert "--max-tokens" in result.stdout
    assert "--context-dir" in result.stdout


def test_run_ai_test_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-test-review" / "scripts" / "run_ai_test_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--api-key" in result.stdout
    assert "--max-tokens" in result.stdout
    assert "--context-dir" in result.stdout


def test_run_ai_cleanup_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-review-cleanup" / "scripts" / "run_ai_cleanup_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--review-file" in result.stdout
    assert "--output-file" in result.stdout
    assert "--log-file" in result.stdout
    assert "--context-file" in result.stdout
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--api-key" in result.stdout
    assert "--max-tokens" in result.stdout
    assert "--context-dir" in result.stdout


def test_publish_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-review-publish" / "scripts" / "publish_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--repository" in result.stdout
    assert "--pr-number" in result.stdout
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--review-file" in result.stdout
    assert "--review-title" in result.stdout
    assert "--context-dir" in result.stdout


def test_standalone_pr_review_help():
    script = ROOT_DIR / "standalone_pr_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--repository" in result.stdout
    assert "--pr" in result.stdout
    assert "--github-token" in result.stdout
    assert "--openai-token" in result.stdout
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--max-tokens" in result.stdout
    assert "--source-root" in result.stdout
    assert "--output-root" in result.stdout


def test_read_changed_files_args():
    script = ROOT_DIR / "actions" / "scala-ai-review-prepare" / "scripts" / "read_changed_files.sh"
    # Testing missing arguments fails with exit code 1
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Missing required arguments" in result.stderr


def test_read_additional_files_args():
    script = ROOT_DIR / "actions" / "scala-ai-review-prepare" / "scripts" / "read_additional_files.sh"
    # Testing missing arguments fails with exit code 1
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Missing required arguments" in result.stderr
