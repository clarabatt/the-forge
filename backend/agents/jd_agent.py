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
      "rank": <integer, 1 = most critical>,
      "required": <true | false>
    }
  ]
}

Rules:
- Extract up to 20 skills, ranked by criticality to the role.
- confidence reflects how explicitly the skill is emphasised in the JD.
- required: true for skills in sections labelled "Required", "Must have", "Essential",
  "Minimum qualifications", or stated as mandatory. false for skills in sections labelled
  "Preferred", "Nice to have", "Bonus", "Plus", "Asset", or "Desired". When no section
  labels are present, use your judgment: core technical skills for the role are required,
  supplementary or domain-adjacent skills are preferred.
- company_name and job_title must come from the JD text, not be inferred.
- Deduplicate: if the same skill appears under different names or in multiple sections,
  emit it only once using the most canonical name. Merge acronym and expansion into one entry.
- Only include Soft Skills that are explicitly stated in the JD text (e.g. "excellent
  communication skills", "team player", "leadership"). Do NOT infer soft skills from the
  role type or industry.
- Acronym handling: always expand acronyms to their full, canonical skill name.
  Common examples: MO → Microsoft Office, MS → Microsoft Suite, PP → PowerPoint,
  XL/Excel → Microsoft Excel, GS → Google Sheets, CRM → Customer Relationship Management,
  ERP → Enterprise Resource Planning, BI → Business Intelligence, ETL → Extract Transform Load,
  ML → Machine Learning, AI → Artificial Intelligence, NLP → Natural Language Processing,
  CI/CD → Continuous Integration / Continuous Delivery, IaC → Infrastructure as Code,
  k8s → Kubernetes, AWS → Amazon Web Services, GCP → Google Cloud Platform, AZ → Azure.
  If an acronym is industry-specific and unambiguous in context, expand it and use the
  full name as the skill name. If genuinely ambiguous, keep the acronym.
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
        "usage": {
            "input_tokens": response.usage_metadata.prompt_token_count or 0,
            "output_tokens": response.usage_metadata.candidates_token_count or 0,
        },
    }
