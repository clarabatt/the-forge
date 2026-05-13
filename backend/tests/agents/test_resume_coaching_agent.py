import json
from unittest.mock import MagicMock, patch

from backend.agents import resume_coaching_agent

_COACHING_PAYLOAD = {
    "overall_score": "decent",
    "global_issues": ["No quantified metrics across most bullets"],
    "summary_feedback": {
        "detected_text": "Experienced software engineer.",
        "issues": ["Too generic, no value proposition"],
        "coaching_questions": ["What type of role are you targeting?"],
    },
    "skills_feedback": {
        "detected_skills": ["Python", "FastAPI"],
        "issues": [],
        "coaching_questions": [],
    },
    "experience_blocks": [
        {
            "employer": "Acme Corp",
            "date_range": "2022–2024",
            "bullets": [
                {
                    "text": "Built backend services.",
                    "framework_score": "weak",
                    "issues": ["No action verb, no outcome"],
                    "coaching_questions": ["What did the backend services enable?"],
                }
            ],
        }
    ],
}

_BLOCKS = [
    {"type": "summary", "text": "Experienced software engineer.", "employer": None, "date_range": None},
    {"type": "accomplishment", "text": "Built backend services.", "employer": "Acme Corp", "date_range": "2022–2024"},
]


def _mock_response(payload: dict, input_tokens: int = 10, output_tokens: int = 5) -> MagicMock:
    response = MagicMock()
    response.text = json.dumps(payload)
    response.usage_metadata.prompt_token_count = input_tokens
    response.usage_metadata.candidates_token_count = output_tokens
    return response


def test_coaching_agent_returns_overall_score():
    with patch("backend.agents.resume_coaching_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(_COACHING_PAYLOAD)

        result = resume_coaching_agent.run(_BLOCKS)

    assert result["overall_score"] == "decent"


def test_coaching_agent_returns_all_sections():
    with patch("backend.agents.resume_coaching_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(_COACHING_PAYLOAD)

        result = resume_coaching_agent.run(_BLOCKS)

    assert "summary_feedback" in result
    assert "skills_feedback" in result
    assert "experience_blocks" in result
    assert "global_issues" in result


def test_coaching_agent_returns_experience_bullets():
    with patch("backend.agents.resume_coaching_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(_COACHING_PAYLOAD)

        result = resume_coaching_agent.run(_BLOCKS)

    blocks = result["experience_blocks"]
    assert len(blocks) == 1
    assert blocks[0]["employer"] == "Acme Corp"
    bullet = blocks[0]["bullets"][0]
    assert bullet["framework_score"] == "weak"
    assert len(bullet["coaching_questions"]) == 1


def test_coaching_agent_returns_usage_metadata():
    with patch("backend.agents.resume_coaching_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response(
            _COACHING_PAYLOAD, input_tokens=100, output_tokens=200
        )

        result = resume_coaching_agent.run(_BLOCKS)

    assert result["usage"]["input_tokens"] == 100
    assert result["usage"]["output_tokens"] == 200


def test_coaching_agent_falls_back_on_missing_fields():
    with patch("backend.agents.resume_coaching_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _mock_response({})

        result = resume_coaching_agent.run(_BLOCKS)

    assert result["overall_score"] == "needs_work"
    assert result["global_issues"] == []
    assert result["experience_blocks"] == []


def test_coaching_agent_strips_markdown_fences():
    wrapped = f"```json\n{json.dumps(_COACHING_PAYLOAD)}\n```"
    response = MagicMock()
    response.text = wrapped
    response.usage_metadata.prompt_token_count = 10
    response.usage_metadata.candidates_token_count = 5

    with patch("backend.agents.resume_coaching_agent.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = response

        result = resume_coaching_agent.run(_BLOCKS)

    assert result["overall_score"] == "decent"
