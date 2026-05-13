import json
import re


def parse_json_response(text: str | None, *, repair_truncated: bool = False) -> dict:
    """Parse a JSON response from Gemini, stripping markdown fences if present."""
    if not text:
        raise ValueError("Empty response from model")
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        if repair_truncated:
            return _repair_truncated_blocks_json(stripped)
        raise


def _repair_truncated_blocks_json(text: str) -> dict:
    """Salvage complete blocks from a truncated {"blocks": [...]} response."""
    # Walk backwards to find the last '}' that closes a complete block object.
    last_close = text.rfind("},")
    if last_close == -1:
        last_close = text.rfind("}")
    if last_close == -1:
        raise ValueError("Cannot repair truncated JSON — no complete block found")
    repaired = text[: last_close + 1] + "\n  ]\n}"
    return json.loads(repaired)
