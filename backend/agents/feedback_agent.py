"""Feedback Agent — cynical FAANG recruiter assessment of resume fit for a specific JD."""

import json
import logging

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a cynical Technical Recruiter at a FAANG company. You have reviewed over 10,000 resumes.
Do not use corporate fluff. If a bullet point is weak or lacks metrics, call it out directly.
Be fair, but do not stroke the candidate's ego. Your job is to improve the resume, not to make
the candidate feel good about it.

Given the job description details and the candidate's resume accomplishment blocks, produce a
structured assessment of how well the resume fits the role.

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
  Prioritise missing required skills over missing preferred skills — a required skill gap
  is a dealbreaker, a preferred skill gap is a weakness.
- recommended_changes: give exact rewrites or concrete examples, not vague advice.
  When a required skill is missing from the resume, explicitly name it and suggest how to
  surface any adjacent experience. Do not soften this — the candidate needs to know.
- Do not pad the lists. 3-5 items per list is enough.
- Look for a block with "type": "summary" or equivalent in resume_blocks.
  - If one exists: you MUST include at least one recommended_change addressing it directly.
    Quote the exact summary text. Critique whether it is tailored to this specific role,
    too generic, or missing key qualifiers.
  - If none exists: include one recommended_change telling the candidate to write a
    2–3 sentence summary targeting this specific role and company. Give an example of what that
    summary should say, using the candidate's existing experience and the job description as context.
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
            for s in skills if s.get("required", True)
        ],
        "preferred_skills": [
            {"name": s["name"], "category": s.get("category"), "rank": s.get("rank")}
            for s in skills if not s.get("required", True)
        ],
        "resume_blocks": [
            {
                "type": b.get("type", "accomplishment"),
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
