import json
from unittest.mock import MagicMock, patch

from backend.agents import jd_agent


def _mock_response(payload: dict, input_tokens: int = 10, output_tokens: int = 5) -> MagicMock:
    response = MagicMock()
    response.text = json.dumps(payload)
    response.usage_metadata.prompt_token_count = input_tokens
    response.usage_metadata.candidates_token_count = output_tokens
    return response


_JD_PAYLOAD = {
    "company_name": "Acme Corp",
    "job_title": "Backend Engineer",
    "skills": [
        {"name": "Python", "category": "Hard Skill", "confidence": 0.9, "rank": 1, "required": True},
        {"name": "PostgreSQL", "category": "Tool", "confidence": 0.8, "rank": 2, "required": False},
    ],
}


def test_jd_agent_parses_company_and_skills():
    with patch("backend.agents.jd_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(_JD_PAYLOAD)

        result = jd_agent.run("We are Acme Corp looking for a Backend Engineer.")

    assert result["company_name"] == "Acme Corp"
    assert result["job_title"] == "Backend Engineer"
    assert len(result["skills"]) == 2
    assert result["skills"][0]["name"] == "Python"
    assert result["skills"][0]["required"] is True
    assert result["skills"][1]["name"] == "PostgreSQL"
    assert result["skills"][1]["required"] is False


def test_jd_agent_returns_usage_metadata():
    with patch("backend.agents.jd_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(
            _JD_PAYLOAD, input_tokens=42, output_tokens=17
        )

        result = jd_agent.run("Some job description.")

    assert result["usage"]["input_tokens"] == 42
    assert result["usage"]["output_tokens"] == 17


def test_jd_agent_falls_back_on_missing_fields():
    with patch("backend.agents.jd_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response({})

        result = jd_agent.run("Incomplete job description.")

    assert result["company_name"] == "Unknown Company"
    assert result["job_title"] == "Unknown Role"
    assert result["skills"] == []
