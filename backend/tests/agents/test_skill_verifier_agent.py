import json
from unittest.mock import MagicMock, patch

from backend.agents import skill_verifier_agent

_RESUME_BLOCKS = [
    {"type": "accomplishment", "text": "Built Python REST APIs", "skills_detected": ["Python", "REST APIs"]},
    {"type": "skills_list", "text": "Python, FastAPI, PostgreSQL", "skills_detected": ["Python", "FastAPI", "PostgreSQL"]},
]


def _mock_response(verifications: list, input_tokens: int = 8, output_tokens: int = 4) -> MagicMock:
    response = MagicMock()
    response.text = json.dumps({"verifications": verifications})
    response.usage_metadata.prompt_token_count = input_tokens
    response.usage_metadata.candidates_token_count = output_tokens
    return response


def test_verifier_marks_genuine_skills_as_verified():
    verifications = [
        {"skill_name": "Python", "verified": True, "reason": "Explicitly in skills list"},
        {"skill_name": "FastAPI", "verified": True, "reason": "Listed under technical skills"},
    ]
    with patch("backend.agents.skill_verifier_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(verifications)

        result = skill_verifier_agent.run(
            skills_to_verify=["Python", "FastAPI"],
            resume_blocks=_RESUME_BLOCKS,
        )

    verified = {v["skill_name"] for v in result["verifications"] if v["verified"]}
    assert verified == {"Python", "FastAPI"}


def test_verifier_rejects_false_positive_skills():
    verifications = [
        {"skill_name": "Go", "verified": False, "reason": "Only appears in 'go-to-market', not as a skill"},
    ]
    with patch("backend.agents.skill_verifier_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(verifications)

        result = skill_verifier_agent.run(
            skills_to_verify=["Go"],
            resume_blocks=_RESUME_BLOCKS,
        )

    verified = [v for v in result["verifications"] if v["verified"]]
    assert len(verified) == 0


def test_verifier_returns_usage_metadata():
    verifications = [{"skill_name": "Python", "verified": True, "reason": "Listed"}]
    with patch("backend.agents.skill_verifier_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(
            verifications, input_tokens=30, output_tokens=12
        )

        result = skill_verifier_agent.run(
            skills_to_verify=["Python"],
            resume_blocks=_RESUME_BLOCKS,
        )

    assert result["usage"]["input_tokens"] == 30
    assert result["usage"]["output_tokens"] == 12
