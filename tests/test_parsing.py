"""Tests for parsing functions in team.py."""

import re


# Replicate the parsing logic from team.py for testing
def parse_critique(source: str, content: str) -> dict:
    """Parse structured critique from model response."""
    agreements = ""
    disagreements = ""
    missing = ""

    agree_match = re.search(
        r'AGREEMENTS?:\s*(.+?)(?=DISAGREEMENTS?:|MISSING:|$)',
        content, re.DOTALL | re.IGNORECASE
    )
    disagree_match = re.search(
        r'DISAGREEMENTS?:\s*(.+?)(?=AGREEMENTS?:|MISSING:|$)',
        content, re.DOTALL | re.IGNORECASE
    )
    missing_match = re.search(
        r'MISSING:\s*(.+?)(?=AGREEMENTS?:|DISAGREEMENTS?:|$)',
        content, re.DOTALL | re.IGNORECASE
    )

    if agree_match:
        agreements = agree_match.group(1).strip()
    if disagree_match:
        disagreements = disagree_match.group(1).strip()
    if missing_match:
        missing = missing_match.group(1).strip()

    # If parsing failed, use raw content
    if not agreements and not disagreements and not missing:
        agreements = content

    return {
        "source": source,
        "agreements": agreements,
        "disagreements": disagreements,
        "missing": missing,
    }


def parse_final_position(source: str, content: str) -> dict:
    """Parse final position and confidence from model response."""
    position = content
    confidence = "MEDIUM"

    pos_match = re.search(
        r'POSITION:\s*(.+?)(?=CONFIDENCE:|$)',
        content, re.DOTALL | re.IGNORECASE
    )
    conf_match = re.search(
        r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)',
        content, re.IGNORECASE
    )

    if pos_match:
        position = pos_match.group(1).strip()
    if conf_match:
        confidence = conf_match.group(1).upper()

    return {
        "source": source,
        "position": position,
        "confidence": confidence,
    }


class TestParseCritique:
    """Tests for critique parsing."""

    def test_well_formatted_critique(self):
        content = """
AGREEMENTS: The main point about Python is valid.
DISAGREEMENTS: I don't think Java is outdated.
MISSING: No one mentioned Rust.
"""
        result = parse_critique("agent", content)
        assert "Python" in result["agreements"]
        assert "Java" in result["disagreements"]
        assert "Rust" in result["missing"]

    def test_singular_keywords(self):
        content = """
AGREEMENT: Python is great.
DISAGREEMENT: Java is slow.
MISSING: Rust was not mentioned.
"""
        result = parse_critique("agent", content)
        assert "Python" in result["agreements"]
        assert "Java" in result["disagreements"]

    def test_case_insensitive(self):
        content = """
agreements: Lower case works too.
Disagreements: This is mixed case.
missing: Should still parse.
"""
        result = parse_critique("agent", content)
        assert "Lower case" in result["agreements"]
        assert "mixed case" in result["disagreements"]
        assert "Should still" in result["missing"]

    def test_partial_structure(self):
        content = """
AGREEMENTS: Only agreements present.
Some other text here.
"""
        result = parse_critique("agent", content)
        assert "Only agreements" in result["agreements"]
        assert result["disagreements"] == ""
        assert result["missing"] == ""

    def test_no_structure_fallback(self):
        content = "Just some random text without any structure."
        result = parse_critique("agent", content)
        # Should use raw content as agreements
        assert result["agreements"] == content
        assert result["disagreements"] == ""
        assert result["missing"] == ""

    def test_multiline_content(self):
        content = """
AGREEMENTS:
- Point 1 is valid
- Point 2 makes sense
- Point 3 is accurate

DISAGREEMENTS:
- I disagree with X
- Y is also wrong

MISSING:
- Nobody mentioned Z
"""
        result = parse_critique("agent", content)
        assert "Point 1" in result["agreements"]
        assert "Point 2" in result["agreements"]
        assert "disagree with X" in result["disagreements"]
        assert "Nobody mentioned Z" in result["missing"]

    def test_different_order(self):
        content = """
MISSING: This is mentioned first.
AGREEMENTS: This comes second.
DISAGREEMENTS: This is last.
"""
        result = parse_critique("agent", content)
        assert "mentioned first" in result["missing"]
        assert "comes second" in result["agreements"]
        assert "last" in result["disagreements"]


class TestParseFinalPosition:
    """Tests for final position parsing."""

    def test_well_formatted_position(self):
        content = """
POSITION: Python is the best choice for beginners.
CONFIDENCE: HIGH
"""
        result = parse_final_position("agent", content)
        assert "Python" in result["position"]
        assert result["confidence"] == "HIGH"

    def test_low_confidence(self):
        content = """
POSITION: This is uncertain.
CONFIDENCE: LOW
"""
        result = parse_final_position("agent", content)
        assert result["confidence"] == "LOW"

    def test_medium_confidence(self):
        content = """
POSITION: Somewhat confident.
CONFIDENCE: MEDIUM
"""
        result = parse_final_position("agent", content)
        assert result["confidence"] == "MEDIUM"

    def test_default_confidence(self):
        content = """
POSITION: No confidence specified.
"""
        result = parse_final_position("agent", content)
        assert result["confidence"] == "MEDIUM"

    def test_case_insensitive_confidence(self):
        content = """
POSITION: Something.
confidence: high
"""
        result = parse_final_position("agent", content)
        assert result["confidence"] == "HIGH"

    def test_no_structure(self):
        content = "Just a plain response without structure."
        result = parse_final_position("agent", content)
        # Should use full content as position
        assert result["position"] == content
        assert result["confidence"] == "MEDIUM"

    def test_multiline_position(self):
        content = """
POSITION:
This is a detailed position.
It spans multiple lines.
With various points.

CONFIDENCE: HIGH
"""
        result = parse_final_position("agent", content)
        assert "detailed position" in result["position"]
        assert "multiple lines" in result["position"]
        assert result["confidence"] == "HIGH"

    def test_invalid_confidence_ignored(self):
        content = """
POSITION: Something.
CONFIDENCE: VERY_HIGH
"""
        result = parse_final_position("agent", content)
        # Invalid confidence should be ignored, default to MEDIUM
        assert result["confidence"] == "MEDIUM"
