import argparse
import json
import sys

from pathlib import Path

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent


def run_review(
        context_dir: Path,
        model: str,
        reasoning_effort: str,
        temperature: float,
        api_key: str,
) -> dict:
    core_prompt = Path(
        context_dir / "core_review_prompt.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    review_prompt = (
            SCRIPT_DIR / "frontend_system_prompt.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    system_prompt = review_prompt.replace(
        "{{CORE_PROMPT}}",
        core_prompt,
    )

    context = Path(
        context_dir / "context-frontend-review.md"
    ).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    client = OpenAI(
        base_url="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        api_key=api_key,
        timeout=1800.0,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model=model,
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
        temperature=temperature,
        response_format={"type": "json_object"},
        reasoning_effort=reasoning_effort,
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
        f"{temperature}, "
        "reasoning_effort: "
        f"{reasoning_effort}, "
        "model: "
        f"{model}",
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

    (context_dir / "review-frontend.json").write_text(
        json.dumps(
            review,
            indent=2,
        ),
        encoding="utf-8",
    )

    return review


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI frontend review."
    )

    parser.add_argument(
        "--context-dir",
        type=Path,
        default=Path("review-context"),
        help=(
            "Directory containing "
            "core_review_prompt.md and "
            "context-frontend-review.md. "
            "Defaults to review-context."
        ),
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
        help="Reasoning depth.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Temperature for the AI model. Defaults to 0.2.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="OVH AI Endpoints API key.",
    )

    args = parser.parse_args()

    review = run_review(
        context_dir=args.context_dir,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        temperature=args.temperature,
        api_key=args.api_key,
    )

    print(
        json.dumps(
            review,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
