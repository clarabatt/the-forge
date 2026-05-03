"""Cover Letter Agent — generates a tailored cover letter draft for a specific role."""

import json
import logging

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert career coach and professional writer who specialises in cover letters
that get interviews. You write in a confident, direct, and authentic tone — no corporate
fluff, no clichés ("I am excited to apply…", "I am a passionate…"), and no fabricated
experience. Every claim must be grounded in the candidate's actual resume.

Given the job details and the candidate's resume, write a cover letter draft.

Return ONLY valid JSON matching this exact schema:
{
  "content": "<full cover letter text, plain text, newlines allowed>",
  "questions": [
    "<specific provocation to help the candidate personalise the letter further>"
  ]
}

Structure the letter as follows (plain text, no markdown):
1. Opening paragraph (2–3 sentences): Name the specific role and company. Lead with the
   candidate's most relevant strength for this role — not a generic statement of interest.
2. Body paragraph 1 (3–4 sentences): Highlight 2–3 concrete accomplishments from the resume
   that directly map to the top-ranked required skills. Be specific — use numbers or outcomes
   where the resume provides them.
3. Body paragraph 2 (2–3 sentences): Address the company context (industry, product, mission)
   and why the candidate's background is a natural fit. Do not invent knowledge about the company
   beyond what the job description states.
4. Closing paragraph (2 sentences): Express clear interest, invite next steps. Do not say
   "thank you for your time and consideration" — be direct.

Rules for content:
- Do NOT fabricate experience, skills, or metrics not present in the resume blocks.
- Do NOT use bullet points or headers — flowing paragraphs only.
- Do NOT mention missing skills or weaknesses.
- Keep the letter under 350 words.
- Address it generically (no "Dear Hiring Manager") — omit the salutation entirely.
- Omit the date and address block — start directly with the opening paragraph.

Rules for questions:
- Write exactly 3–4 questions, no more.
- Every question must reference something specific from the resume or the job description
  (an employer name, a skill, a job title, a product area — never speak in generalities).
- Each question should prompt the candidate to add a named project, a concrete metric,
  an anecdote, or a specific outcome that would make the letter less generic.
- Frame them as provocations, not instructions. Good example:
  "Your resume mentions improving performance at [Employer] — what was the actual
  percentage or time saved? Adding that number to paragraph 2 would make it memorable."
  Bad example: "Add metrics to your bullet points."
- Do NOT ask about skills not in the resume or requirements not in the JD.
"""


def run(
    company_name: str,
    job_title: str,
    skills: list[dict],
    resume_blocks: list[dict],
    feedback: dict,
) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)

    context = {
        "role": f"{job_title} at {company_name}",
        "top_required_skills": [
            {"name": s["name"], "category": s.get("category"), "rank": s.get("rank")}
            for s in sorted(skills, key=lambda x: x.get("rank", 99))[:10]
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
        "strong_points": feedback.get("strong_points", []),
    }

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=json.dumps(context),
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.5,
        ),
    )

    result = json.loads(response.text)

    return {
        "content": result.get("content", ""),
        "questions": result.get("questions", []),
        "usage": {
            "input_tokens": response.usage_metadata.prompt_token_count or 0,
            "output_tokens": response.usage_metadata.candidates_token_count or 0,
        },
    }
