import json
import os

from pathlib import Path

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent

review_file = Path("review-context") / os.environ["REVIEW_FILE"]

output_file = Path("review-context") / os.environ.get("CLEANUP_OUTPUT_FILE")

log_file = Path("review-context") / os.environ.get("CLEANUP_LOG_FILE")

context_file = Path("review-context") / os.environ["REVIEW_CONTEXT_FILE"]

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

print(f"finish_reason: {choice.finish_reason}")
print(f"usage: {response.usage}")

print("=== MODEL PARAMETERS ===")
print(f"temperature: {os.environ['TEMPERATURE']}")
print(f"reasoning_effort: {os.environ['REASONING_EFFORT']}")
print(f"model: {os.environ['REVIEW_MODEL']}")

print("=== FILES ===")
print(f"review_file: {review_file}")
print(f"output_file: {output_file}")
print(f"log_file: {log_file}")

raw = choice.message.content or ""

print(f"response length: {len(raw)}")

if choice.finish_reason == "length":
    raise RuntimeError(
        "Cleanup model response was truncated because it reached "
        "the output token limit"
    )

try:
    result = json.loads(raw)
except json.JSONDecodeError:
    print("=== RAW MODEL RESPONSE START ===")
    print(raw)
    print("=== RAW MODEL RESPONSE END ===")
    raise

review = result["review"]
cleanup_log = result["cleanup"]

output_file.write_text(
    json.dumps(review, indent=2),
    encoding="utf-8",
)

log_file.write_text(
    json.dumps(cleanup_log, indent=2),
    encoding="utf-8",
)

print(f"review output: {output_file}")
print(f"cleanup log: {log_file}")
