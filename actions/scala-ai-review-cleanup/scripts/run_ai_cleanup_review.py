import argparse
import json
import os
import sys

from pathlib import Path

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent


def run_cleanup(context_dir: Path) -> dict:
    review_file = context_dir / os.environ["REVIEW_FILE"]

    output_file = context_dir / os.environ["CLEANUP_OUTPUT_FILE"]

    log_file = context_dir / os.environ["CLEANUP_LOG_FILE"]

    context_file = context_dir / os.environ["REVIEW_CONTEXT_FILE"]

    context = context_file.read_text(
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
        review_file.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    )

    user_prompt = f"""
# ORIGINAL REVIEW CONTEXT

{context}

# CANDIDATE FINDINGS

{json.dumps(candidate_review, indent=2)}
"""

    client = OpenAI(
        base_url="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        api_key=os.environ["OVH_AI_ENDPOINTS_API_KEY"],
        timeout=1800.0,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model=os.environ["REVIEW_MODEL"],
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
        temperature=float(os.environ["TEMPERATURE"]),
        response_format={"type": "json_object"},
        reasoning_effort=os.environ["REASONING_EFFORT"],
        max_tokens=60000,
        timeout=1800.0,
    )

    choice = response.choices[0]

    print(
        f"finish_reason: {choice.finish_reason}",
        file=sys.stderr,
    )
    print(
        f"usage: {response.usage}",
        file=sys.stderr,
    )

    print(
        "=== MODEL PARAMETERS ===",
        file=sys.stderr,
    )
    print(
        f"temperature: {os.environ['TEMPERATURE']}",
        file=sys.stderr,
    )
    print(
        f"reasoning_effort: {os.environ['REASONING_EFFORT']}",
        file=sys.stderr,
    )
    print(
        f"model: {os.environ['REVIEW_MODEL']}",
        file=sys.stderr,
    )

    print(
        "=== FILES ===",
        file=sys.stderr,
    )
    print(
        f"review_file: {review_file}",
        file=sys.stderr,
    )
    print(
        f"output_file: {output_file}",
        file=sys.stderr,
    )
    print(
        f"log_file: {log_file}",
        file=sys.stderr,
    )

    raw = choice.message.content or ""

    print(
        f"response length: {len(raw)}",
        file=sys.stderr,
    )

    if choice.finish_reason == "length":
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
        raise

    review = result["review"]
    cleanup_log = result["cleanup"]

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(review, indent=2),
        encoding="utf-8",
    )

    log_file.write_text(
        json.dumps(cleanup_log, indent=2),
        encoding="utf-8",
    )

    print(
        f"review output: {output_file}",
        file=sys.stderr,
    )
    print(
        f"cleanup log: {log_file}",
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

    args = parser.parse_args()

    run_cleanup(args.context_dir)


if __name__ == "__main__":
    main()