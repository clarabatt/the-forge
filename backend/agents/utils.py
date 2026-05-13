import re


def parse_json_response(text: str | None) -> dict:
    """Parse a JSON response from Gemini, stripping markdown fences if present."""
    if not text:
        raise ValueError("Empty response from model")
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    import json
    return json.loads(stripped)
