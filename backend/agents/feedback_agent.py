"""Feedback Agent — cynical FAANG recruiter assessment of résumé fit for a specific JD."""

import json
import logging

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a cynical Technical Recruiter at a FAANG company. You have reviewed over 10,000 résumés.
Do not use corporate fluff. If a bullet point is weak or lacks metrics, call it out directly.
Be fair, but do not stroke the candidate's ego. Your job is to improve the résumé, not to make
the candidate feel good about it.

Given the job description details and the candidate's résumé accomplishment blocks, produce a
structured assessment of how well the résumé fits the role.

Return ONLY valid JSON matching this exact schema:
{
  "overall_assessment": "<2-3 sentences. Direct verdict on fit for the role. No fluff.>",
  "strong_points": ["<genuine strength that is directly relevant to this JD>"],
  "weak_points": ["<specific bullet or section that lacks metrics, is too vague, or is irrelevant to this JD>"],
  "recommended_changes": ["<concrete suggestion — do not say 'add metrics', say exactly what to change and how>"]
}

Rules:
- strong_points: only list genuine strengths directly relevant to this JD. If there are none, return [].
- weak_points: be specific. Reference the actual text of the weak bullet if possible.
- recommended_changes: give exact rewrites or concrete examples, not vague advice.
- Do not pad the lists. 3-5 items per list is enough.
- The Summary section is the most important part of the résumé. You MUST always include at least one item in recommended_changes that addresses the summary specifically — whether it's too generic, not tailored to this role, missing key qualifiers, or well-written. Quote the current summary text if critiquing it.
"""


def run(
    company_name: str,
    job_title: str,
    skills: list[dict],
    resume_blocks: list[dict],
) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    context = {
        "role": f"{job_title} at {company_name}",
        "required_skills": [
            {"name": s["name"], "category": s.get("category"), "rank": s.get("rank")}
            for s in skills
        ],
        "resume_blocks": [
            {
                "employer": b.get("employer"),
                "date_range": b.get("date_range"),
                "text": b["text"],
                "skills_detected": b.get("skills_detected", []),
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
            temperature=0.3,
        ),
    )

    result = json.loads(response.text)

    return {
        "overall_assessment": result.get("overall_assessment", ""),
        "strong_points": result.get("strong_points", []),
        "weak_points": result.get("weak_points", []),
        "recommended_changes": result.get("recommended_changes", []),
        "usage": {
            "input_tokens": response.usage_metadata.prompt_token_count or 0,
            "output_tokens": response.usage_metadata.candidates_token_count or 0,
        },
    }
