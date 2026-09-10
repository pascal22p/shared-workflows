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
    assert "--context-dir" in result.stdout


def test_run_ai_frontend_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-frontend-review" / "scripts" / "run_ai_frontend_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--api-key" in result.stdout
    assert "--context-dir" in result.stdout


def test_run_ai_test_review_help():
    script = ROOT_DIR / "actions" / "scala-ai-test-review" / "scripts" / "run_ai_test_review.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--model" in result.stdout
    assert "--reasoning-effort" in result.stdout
    assert "--temperature" in result.stdout
    assert "--api-key" in result.stdout
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
