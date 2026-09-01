import argparse
import json
import os
import sys

from pathlib import Path

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent


def run_review(context_dir: Path) -> dict:
    context = Path(
        context_dir / "context-test-review.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    core_prompt = Path(
        context_dir / "core_review_prompt.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    review_prompt = (
            SCRIPT_DIR / "test_system_prompt.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    system_prompt = review_prompt.replace(
        "{{CORE_PROMPT}}",
        core_prompt,
    )

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
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": context,
            },
        ],
        temperature=float(os.environ["TEMPERATURE"]),
        response_format={"type": "json_object"},
        reasoning_effort=os.environ["REASONING_EFFORT"],
        max_tokens=40000,
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
        "temperature: "
        f"{os.environ['TEMPERATURE']}, "
        "reasoning_effort: "
        f"{os.environ['REASONING_EFFORT']}, "
        "model: "
        f"{os.environ['REVIEW_MODEL']}",
        file=sys.stderr,
    )

    raw = choice.message.content or ""

    print(
        f"response length: {len(raw)}",
        file=sys.stderr,
    )

    if choice.finish_reason == "length":
        raise RuntimeError(
            "OVH model response was truncated because it reached "
            "the output token limit"
        )

    try:
        review = json.loads(raw)
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

    context_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    (context_dir / "review-test.json").write_text(
        json.dumps(
            review,
            indent=2,
        ),
        encoding="utf-8",
    )

    return review


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI test review."
    )

    parser.add_argument(
        "--context-dir",
        type=Path,
        default=Path("review-context"),
        help=(
            "Directory containing "
            "core_review_prompt.md and "
            "context-test-review.md. "
            "Defaults to review-context."
        ),
    )

    args = parser.parse_args()

    review = run_review(args.context_dir)

    print(
        json.dumps(
            review,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
