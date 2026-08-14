import json
import os

from pathlib import Path

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent

context = Path(
    "review-context/full-context.md"
).read_text(
    encoding="utf-8",
    errors="ignore"
)

system_prompt = (
        SCRIPT_DIR / "system_prompt.md"
).read_text(
    encoding="utf-8",
)

client = OpenAI(
    base_url="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
    api_key=os.environ["OVH_AI_ENDPOINTS_API_KEY"],
    timeout=600.0,
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
    temperature=0,
    reasoning_effort=os.environ["REASONING_EFFORT"],
    max_tokens=10000,
)

raw = response.choices[0].message.content

review = json.loads(raw)

Path(
    "review-context/review.json"
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