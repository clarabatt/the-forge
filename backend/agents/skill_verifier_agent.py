"""Skill Verifier Agent — confirms that confidence-matched skills are genuinely in the resume."""

import json
import logging

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a strict resume auditor. An automated system has scanned a resume and flagged a list
of skills as "found". Your job is to verify each one by reading the actual resume text.

A skill is verified ONLY if the candidate demonstrably has it — they used it in a project,
listed it in a skills section, or described work that clearly relies on it.

Reject a skill if:
- The only evidence is a word that coincidentally overlaps (e.g. "learning" in "e-learning",
  "rest" in "rest of the team", "go" in "go-to-market").
- The skill appears only as part of an unrelated compound phrase.
- There is no concrete evidence of actual use or knowledge.

Return ONLY valid JSON:
{
  "verifications": [
    {
      "skill_name": "<exact name from the input list>",
      "verified": true,
      "reason": "<one sentence citing the specific evidence in the resume>"
    },
    {
      "skill_name": "<exact name from the input list>",
      "verified": false,
      "reason": "<one sentence explaining why the match is not genuine>"
    }
  ]
}

Every skill in the input list must appear exactly once in the output.
"""


def run(skills_to_verify: list[str], resume_blocks: list[dict]) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    context = {
        "skills_to_verify": skills_to_verify,
        "resume": [
            {
                "employer": b.get("employer"),
                "date_range": b.get("date_range"),
                "text": b["text"],
            }
            for b in resume_blocks
        ],
    }

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=json.dumps(context),
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )

    result = json.loads(response.text)
    verifications = result.get("verifications", [])

    # Warn if the model dropped or added entries
    returned_names = {v["skill_name"] for v in verifications}
    expected_names = set(skills_to_verify)
    if returned_names != expected_names:
        missing = expected_names - returned_names
        extra = returned_names - expected_names
        if missing:
            logger.warning("skill verifier did not return results for: %s", missing)
        if extra:
            logger.warning("skill verifier returned unexpected skills: %s", extra)

    return {
        "verifications": verifications,
        "usage": {
            "input_tokens": response.usage_metadata.prompt_token_count or 0,
            "output_tokens": response.usage_metadata.candidates_token_count or 0,
        },
    }
