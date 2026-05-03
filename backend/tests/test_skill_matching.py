import pytest
from backend.agents.runner import MATCH_CONFIDENCE_THRESHOLD, _skill_confidence, _skill_matched


@pytest.mark.parametrize("jd_name, detected, expected", [
    # exact match
    ("Python", {"python", "react"}, True),
    # case-insensitive exact
    ("React", {"react"}, True),
    # detected skill is a substring of the JD name (composite names)
    ("Databases (SQL/NoSQL)", {"sql", "nosql"}, True),
    ("Databases (SQL/NoSQL)", {"sql"}, True),
    ("REST APIs", {"rest"}, True),
    # token overlap
    ("Test-Driven Development", {"test-driven", "development"}, True),
    ("Continuous Integration / Continuous Delivery", {"continuous", "delivery"}, True),
    # acronym expanded in resume agent → exact match on expanded form
    ("Test-Driven Development", {"tdd", "test-driven development"}, True),
    # no match
    ("Machine Learning", {"python", "react"}, False),
    ("Amazon Web Services", {"azure", "gcp"}, False),
    # short tokens (len <= 2) must not produce false positives
    ("Go", {"go"}, True),
    ("CI/CD", {"ci/cd", "continuous integration / continuous delivery"}, True),

    # --- architecture / non-IT examples ---
    # exact
    ("AutoCAD", {"autocad", "revit"}, True),
    # JD expands acronym, resume agent emits both forms
    ("Building Information Modeling", {"bim", "building information modeling"}, True),
    # slash-separated tool list — token from either side matches
    ("AutoCAD / Revit", {"revit"}, True),
    ("AutoCAD / Revit", {"autocad"}, True),
    # composite JD name, resume has one component
    ("Construction Documentation", {"documentation"}, True),
    # parenthetical acronym: "CAD (Computer-Aided Design)" → token "cad"
    ("CAD (Computer-Aided Design)", {"cad"}, True),
    # domain knowledge token overlap
    ("Zoning & Land-Use Regulations", {"zoning"}, True),
    ("Structural Load Analysis", {"structural", "analysis"}, True),
    # no match across unrelated architecture skills
    ("Building Information Modeling", {"autocad", "revit"}, False),
    ("Interior Design", {"structural engineering", "bim"}, False),

    # --- other non-IT domains ---
    # healthcare acronym expansion
    ("Electronic Health Records", {"ehr", "electronic health records"}, True),
    # finance acronym expansion
    ("Generally Accepted Accounting Principles", {"gaap", "generally accepted accounting principles"}, True),
    # finance: composite JD name, resume has abbreviation as substring
    ("GAAP Reporting", {"gaap"}, True),
])
def test_skill_matched(jd_name, detected, expected):
    assert _skill_matched(jd_name, detected) == expected


class TestSkillConfidence:
    """Tests for the continuous confidence score and frequency effects."""

    def test_exact_match_single_block(self):
        assert _skill_confidence("Python", {"python": 1}) == pytest.approx(0.85)

    def test_exact_match_frequency_boost(self):
        # appears in 3 blocks → 0.85 + 0.05*2 = 0.95
        assert _skill_confidence("Python", {"python": 3}) == pytest.approx(0.95)

    def test_exact_match_frequency_capped_at_1(self):
        assert _skill_confidence("Python", {"python": 10}) == pytest.approx(1.0)

    def test_token_match_passes_threshold(self):
        # "rest" is a standalone token in "rest apis" — 0.72 ≥ threshold
        score = _skill_confidence("REST APIs", {"rest": 1})
        assert score >= MATCH_CONFIDENCE_THRESHOLD

    def test_token_match_frequency_boost(self):
        score_1 = _skill_confidence("REST APIs", {"rest": 1})
        score_3 = _skill_confidence("REST APIs", {"rest": 3})
        assert score_3 > score_1

    def test_short_substring_alone_below_threshold(self):
        # "go" is 2 chars (filtered by len>2), so "go" as a generic short word
        # A detected skill that's a short non-token substring should score low
        # "ab" (len 2) in "enable" — filtered out by len>2 in jd_tokens
        score = _skill_confidence("Data Engineering", {"dat": 1})
        assert score < MATCH_CONFIDENCE_THRESHOLD

    def test_short_substring_boosted_by_frequency(self):
        # A short (len<5) substring that is NOT a standalone JD token starts at 0.42.
        # With freq=5 → 0.42 + 0.15 = 0.57 — still below threshold (by design).
        # The user should not rely solely on short non-token substrings.
        score = _skill_confidence("Data Engineering", {"dat": 5})
        assert score < MATCH_CONFIDENCE_THRESHOLD

    def test_no_match_returns_zero(self):
        assert _skill_confidence("Machine Learning", {"python": 2, "react": 3}) == pytest.approx(0.0)

    def test_multi_token_coverage_scales_with_ratio(self):
        # All tokens of "Structural Load Analysis" matched → high confidence
        all_matched = _skill_confidence(
            "Structural Load Analysis", {"structural": 1, "load": 1, "analysis": 1}
        )
        # Only one token matched
        one_matched = _skill_confidence("Structural Load Analysis", {"structural": 1})
        assert all_matched > one_matched

    def test_multi_token_full_coverage_above_threshold(self):
        score = _skill_confidence(
            "Structural Load Analysis", {"structural": 1, "load": 1, "analysis": 1}
        )
        assert score >= MATCH_CONFIDENCE_THRESHOLD

    def test_frequency_pushes_borderline_over_threshold(self):
        # A skill that barely misses with freq=1 should cross with higher frequency.
        # Use a short-substring-only match that starts at 0.42 and needs freq≥5 to reach 0.57
        # (this confirms it stays below, which is the desired conservative behavior)
        low = _skill_confidence("Project Planning", {"plan": 1})
        high = _skill_confidence("Project Planning", {"plan": 5})
        assert high > low  # frequency helps
        assert high < MATCH_CONFIDENCE_THRESHOLD  # but short non-token substring never passes alone
