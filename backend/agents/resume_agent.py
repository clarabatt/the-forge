"""Resume Agent — parses raw résumé text into structured accomplishment blocks."""

import json
import logging
import uuid

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a résumé parser. Given plain-text résumé content, extract every accomplishment
or responsibility bullet point into structured blocks.

Return ONLY valid JSON matching this exact schema:
{
  "blocks": [
    {
      "id": "<uuid string>",
      "type": "accomplishment",
      "text": "<exact bullet text as written>",
      "employer": "<company or institution name, or null>",
      "date_range": "<date range string as written, or null>",
      "skills_detected": ["<skill1>", "<skill2>"]
    }
  ]
}

Rules:
- Preserve the exact wording of each bullet — never paraphrase.
- One block per bullet point or sentence of substance.
- Skip section headings, contact info, and blank lines.
- Generate a fresh UUID (v4 format) for each block id.
- employer and date_range come from the surrounding section context, not the bullet itself.
"""


def run(raw_text: str) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )

    result = json.loads(response.text)
    blocks = result.get("blocks", [])

    for block in blocks:
        if not block.get("id"):
            block["id"] = str(uuid.uuid4())

    return {
        "blocks": blocks,
        "usage": {
            "input_tokens": response.usage_metadata.prompt_token_count or 0,
            "output_tokens": response.usage_metadata.candidates_token_count or 0,
        },
    }
