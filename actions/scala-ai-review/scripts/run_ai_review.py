import json
import os

from pathlib import Path

from openai import OpenAI

SCRIPT_DIR = Path(__file__).resolve().parent

CORE_PROMPT = Path(
    "review-context/core_review_prompt.md"
).read_text(
    encoding="utf-8",
    errors="ignore",
)

REVIEW_PROMPT = (
        SCRIPT_DIR / "system_prompt.md"
).read_text(
    encoding="utf-8",
    errors="ignore",
)

system_prompt = REVIEW_PROMPT.replace(
    "{{CORE_PROMPT}}",
    CORE_PROMPT,
)

context = Path(
    "review-context/context-code-review.md"
).read_text(
    encoding="utf-8",
    errors="ignore"
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
    max_tokens=60000,
    timeout=1800.0,
)

choice = response.choices[0]

print(f"finish_reason: {choice.finish_reason}")
print(f"usage: {response.usage}")
print("=== MODEL PARAMETERS ===")
print(f"temperature: {os.environ['TEMPERATURE']}, reasoning_effort: {os.environ['REASONING_EFFORT']}, model: {os.environ['REVIEW_MODEL']}")

raw = choice.message.content or ""

print(f"response length: {len(raw)}")

if choice.finish_reason == "length":
    raise RuntimeError(
        "OVH model response was truncated because it reached the output token limit"
    )

try:
    review = json.loads(raw)
except json.JSONDecodeError:
    print("=== RAW MODEL RESPONSE START ===")
    print(raw)
    print("=== RAW MODEL RESPONSE END ===")
    raise

Path(
    "review-context/review-frontend.json"
).write_text(
    json.dumps(
        review,
        indent=2
    ),
    encoding="utf-8"
)

print(
    json.dumps(
        review,
        indent=2
    )
)