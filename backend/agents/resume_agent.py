"""Resume Agent — parses raw resume text into structured accomplishment blocks."""

import json
import logging
import uuid

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a resume parser. Given plain-text resume content, extract the summary section,
every accomplishment or responsibility bullet point, and any skills inventory section
into structured blocks.

Return ONLY valid JSON matching this exact schema:
{
  "blocks": [
    {
      "id": "<uuid string>",
      "type": "summary | accomplishment | skills_list",
      "text": "<exact text as written>",
      "employer": "<company or institution name, or null>",
      "date_range": "<date range string as written, or null>",
      "skills_detected": ["<skill1>", "<skill2>"]
    }
  ]
}

Skill extraction guidance for skills_detected:
- Include ALL of: programming languages, frameworks, libraries, cloud services, tools,
  databases, methodologies (Agile, CI/CD, TDD), and domain knowledge
  (e.g. "distributed systems", "ML pipelines", "payment processing").
- Extract the canonical skill name, not a full phrase.
- Example: "Built and deployed ML pipelines on AWS SageMaker using Python and Airflow"
  → skills_detected: ["ML pipelines", "AWS SageMaker", "Python", "Airflow"]
- Example: "Led cross-functional Agile teams delivering microservices on Kubernetes"
  → skills_detected: ["Agile", "microservices", "Kubernetes"]
- If a block mentions no identifiable skill, return [].
- Acronym expansion: when a skill appears as a common acronym, include BOTH the acronym
  and its full expanded form so it can be matched against job descriptions that use either form.
  Examples: "TDD" → ["TDD", "Test-Driven Development"], "BDD" → ["BDD", "Behaviour-Driven Development"],
  "CI/CD" → ["CI/CD", "Continuous Integration / Continuous Delivery"],
  "OOP" → ["OOP", "Object-Oriented Programming"], "REST" → ["REST", "REST APIs"],
  "ML" → ["ML", "Machine Learning"], "AI" → ["AI", "Artificial Intelligence"],
  "NLP" → ["NLP", "Natural Language Processing"],
  "AWS" → ["AWS", "Amazon Web Services"], "GCP" → ["GCP", "Google Cloud Platform"],
  "k8s" → ["k8s", "Kubernetes"], "IaC" → ["IaC", "Infrastructure as Code"].

Rules:
- If the resume contains a Summary, Professional Summary, Profile, or About section,
  extract the entire paragraph text as ONE block with type "summary".
  employer and date_range must be null for summary blocks.
- If the resume contains a Skills, Technical Skills, Core Competencies, Technologies,
  or similar inventory section (a flat list, comma-separated list, or grouped list of
  skill names), extract it as ONE block with type "skills_list". Set employer and
  date_range to null. Set skills_detected to every individual skill name in the list.
  Do NOT skip this section — it is the most direct source of verified skills.
- Skip only the bare section heading lines (e.g. the word "Experience", "Education",
  "Certifications" standing alone) and contact info lines. Never skip section content.
- Preserve the exact wording of each bullet — never paraphrase.
- One block per bullet point or sentence of substance.
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
