"""JD Agent — extracts structured skill data from a raw job description."""

import json
import logging

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a technical recruiter assistant. Given a job description, extract structured information.

Return ONLY valid JSON matching this exact schema:
{
  "company_name": "<string — company posting the role>",
  "job_title": "<string — exact role title>",
  "skills": [
    {
      "name": "<skill name>",
      "category": "<Hard Skill | Soft Skill | Tool | Domain Knowledge>",
      "confidence": <float 0.0–1.0>,
      "rank": <integer, 1 = most critical>
    }
  ],
  "vibe_check": "<2–3 sentence description of company culture and what the role values>",
  "must_have_count": <integer — how many top-ranked skills are truly non-negotiable>
}

Rules:
- Extract up to 10 skills, ranked by criticality to the role.
- confidence reflects how explicitly the skill is emphasised in the JD.
- must_have_count is typically 3–6.
- company_name and job_title must come from the JD text, not be inferred.
"""


def run(job_description: str) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=job_description,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    result = json.loads(response.text)

    return {
        "company_name": result.get("company_name", "Unknown Company"),
        "job_title": result.get("job_title", "Unknown Role"),
        "skills": result.get("skills", []),
        "vibe_check": result.get("vibe_check", ""),
        "must_have_count": result.get("must_have_count", 0),
        "usage": {
            "input_tokens": response.usage_metadata.prompt_token_count or 0,
            "output_tokens": response.usage_metadata.candidates_token_count or 0,
        },
    }
