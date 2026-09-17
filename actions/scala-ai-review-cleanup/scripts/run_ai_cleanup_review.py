import argparse
import json
import sys
import time

from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cleanup(
        context_dir: Path,
        review_file: str,
        output_file: str,
        log_file: str,
        context_file: str,
        model: str,
        reasoning_effort: str,
        temperature: float,
        api_key: str,
        max_tokens: int
) -> dict:
    started_at = utc_now()
    start_time = time.perf_counter()

    review_path = context_dir / review_file
    output_path = context_dir / output_file
    log_path = context_dir / log_file
    context_path = context_dir / context_file
    metadata_path = context_dir / "review-cleanup-metadata.json"

    context = context_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    cleanup_prompt = Path(
        SCRIPT_DIR / "cleanup_prompt.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    candidate_review = json.loads(
        review_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    )

    candidate_review_json = json.dumps(
        candidate_review,
        indent=2,
    )

    user_prompt = f"""
# ORIGINAL REVIEW CONTEXT

{context}

# CANDIDATE FINDINGS

{candidate_review_json}
"""

    client = OpenAI(
        base_url="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        api_key=api_key,
        timeout=1800.0,
        max_retries=0,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": cleanup_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            timeout=1800.0,
        )
    except Exception as exc:
        duration_seconds = time.perf_counter() - start_time

        metadata = {
            "status": "error",
            "started_at": started_at,
            "completed_at": utc_now(),
            "duration_seconds": round(duration_seconds, 3),

            "request": {
                "model": model,
                "temperature": temperature,
                "reasoning_effort": reasoning_effort,
                "max_tokens": max_tokens,
                "response_format": "json_object",
            },

            "input": {
                "cleanup_prompt_chars": len(cleanup_prompt),
                "context_chars": len(context),
                "candidate_review_chars": len(candidate_review_json),
                "user_prompt_chars": len(user_prompt),
            },

            "files": {
                "review_file": str(review_path),
                "output_file": str(output_path),
                "log_file": str(log_path),
                "context_file": str(context_path),
            },

            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }

        context_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

        raise

    duration_seconds = time.perf_counter() - start_time

    choice = response.choices[0]
    usage = response.usage

    completion_tokens_details = getattr(
        usage,
        "completion_tokens_details",
        None,
    )

    prompt_tokens_details = getattr(
        usage,
        "prompt_tokens_details",
        None,
    )

    metadata = {
        "status": "success",
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_seconds": round(duration_seconds, 3),

        "request": {
            "model": model,
            "temperature": temperature,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "response_format": "json_object",
        },

        "response": {
            "id": response.id,
            "model": response.model,
            "finish_reason": choice.finish_reason,
            "response_length_chars": len(
                choice.message.content or ""
            ),
        },

        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "prompt_tokens_details": (
                prompt_tokens_details.model_dump()
                if prompt_tokens_details is not None
                else None
            ),
            "completion_tokens_details": (
                completion_tokens_details.model_dump()
                if completion_tokens_details is not None
                else None
            ),
        },

        "input": {
            "cleanup_prompt_chars": len(cleanup_prompt),
            "context_chars": len(context),
            "candidate_review_chars": len(candidate_review_json),
            "user_prompt_chars": len(user_prompt),
        },

        "files": {
            "review_file": str(review_path),
            "output_file": str(output_path),
            "log_file": str(log_path),
            "context_file": str(context_path),
        },
    }

    print(
        f"finish_reason: {choice.finish_reason}",
        file=sys.stderr,
    )

    print(
        f"duration: {duration_seconds:.3f}s",
        file=sys.stderr,
    )

    print(
        f"usage: {usage}",
        file=sys.stderr,
    )

    print(
        "=== MODEL PARAMETERS ===",
        file=sys.stderr,
    )

    print(
        f"temperature: {temperature}",
        file=sys.stderr,
    )

    print(
        f"reasoning_effort: {reasoning_effort}",
        file=sys.stderr,
    )

    print(
        f"model: {model}",
        file=sys.stderr,
    )

    print(
        f"max_tokens: {max_tokens}",
        file=sys.stderr,
    )

    print(
        "=== FILES ===",
        file=sys.stderr,
    )

    print(
        f"review_file: {review_path}",
        file=sys.stderr,
    )

    print(
        f"output_file: {output_path}",
        file=sys.stderr,
    )

    print(
        f"log_file: {log_path}",
        file=sys.stderr,
    )

    raw = choice.message.content or ""

    print(
        f"response length: {len(raw)}",
        file=sys.stderr,
    )

    if choice.finish_reason == "length":
        metadata["status"] = "error"
        metadata["error"] = {
            "type": "RuntimeError",
            "message": (
                "Cleanup model response was truncated because it reached "
                "the output token limit"
            ),
        }

        context_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

        raise RuntimeError(
            "Cleanup model response was truncated because it reached "
            "the output token limit"
        )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(
            "=== RAW MODEL RESPONSE START ===",
            file=sys.stderr,
        )
        print(
            raw,
            file=sys.stderr,
        )
        print(
            "=== RAW MODEL RESPONSE END ===",
            file=sys.stderr,
        )

        metadata["status"] = "error"
        metadata["error"] = {
            "type": "JSONDecodeError",
            "message": "Model response was not valid JSON",
        }

        context_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

        raise

    review = result["review"]
    cleanup_log = result["cleanup"]

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(review, indent=2),
        encoding="utf-8",
    )

    log_path.write_text(
        json.dumps(cleanup_log, indent=2),
        encoding="utf-8",
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"review output: {output_path}",
        file=sys.stderr,
    )

    print(
        f"cleanup log: {log_path}",
        file=sys.stderr,
    )

    return review


def main():
    parser = argparse.ArgumentParser(
        description="Clean up the AI review."
    )

    parser.add_argument(
        "--context-dir",
        type=Path,
        default=Path("review-context"),
        help=(
            "Directory containing the review context and "
            "review files. Defaults to review-context."
        ),
    )

    parser.add_argument(
        "--review-file",
        type=str,
        required=True,
        help="Candidate review JSON filename relative to context-dir.",
    )

    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help=(
            "Output path for the cleaned review JSON "
            "relative to context-dir."
        ),
    )

    parser.add_argument(
        "--log-file",
        type=str,
        required=True,
        help=(
            "Output path for the cleanup decision log "
            "relative to context-dir."
        ),
    )

    parser.add_argument(
        "--context-file",
        type=str,
        required=True,
        help="Review context file relative to context-dir.",
    )

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="The OVH model name.",
    )

    parser.add_argument(
        "--reasoning-effort",
        type=str,
        required=True,
        help="Reasoning depth for cleanup.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for the AI model. Defaults to 0.0.",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="OVH AI Endpoints API key.",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        required=True,
        help="Maximum number of tokens to use.",
    )

    args = parser.parse_args()

    run_cleanup(
        context_dir=args.context_dir,
        review_file=args.review_file,
        output_file=args.output_file,
        log_file=args.log_file,
        context_file=args.context_file,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        temperature=args.temperature,
        api_key=args.api_key,
        max_tokens=args.max_tokens,
    )


if __name__ == "__main__":
    main()
