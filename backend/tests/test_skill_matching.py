import pytest
from backend.agents.runner import _skill_matched


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
