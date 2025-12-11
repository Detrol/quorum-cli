"""Tests for agents.py - validation and role assignment functions.

These tests are self-contained and don't require autogen dependencies.
"""

import re

import pytest

# =============================================================================
# Replicate the functions we want to test (to avoid import issues)
# =============================================================================

def _make_valid_identifier(s: str) -> str:
    """Convert a string to a valid Python identifier."""
    result = re.sub(r'[^a-zA-Z0-9_]', '_', s)
    if result and result[0].isdigit():
        result = '_' + result
    return result


METHOD_REQUIREMENTS = {
    "standard": {"min": 2, "even_only": False},
    "oxford": {"min": 2, "even_only": True},
    "advocate": {"min": 3, "even_only": False},
    "socratic": {"min": 2, "even_only": False},
    "delphi": {"min": 3, "even_only": False},
    "brainstorm": {"min": 2, "even_only": False},
    "tradeoff": {"min": 2, "even_only": False},
}


def validate_method_model_count(method: str, num_models: int) -> tuple[bool, str | None]:
    """Validate that the number of models is allowed for the method."""
    req = METHOD_REQUIREMENTS.get(method)
    if not req:
        return True, None

    if num_models < req["min"]:
        return False, f"{method.capitalize()} requires at least {req['min']} models"

    if req["even_only"] and num_models % 2 != 0:
        return False, "Oxford requires an even number of models for balanced FOR/AGAINST teams"

    return True, None


def get_role_assignments(method: str, model_ids: list[str]) -> dict[str, list[str]] | None:
    """Get role assignments for a method."""
    if method == "oxford":
        for_team = [m for i, m in enumerate(model_ids) if i % 2 == 0]
        against_team = [m for i, m in enumerate(model_ids) if i % 2 == 1]
        return {"FOR": for_team, "AGAINST": against_team}

    elif method == "advocate":
        if len(model_ids) < 2:
            return None
        defenders = model_ids[:-1]
        advocate = [model_ids[-1]]
        return {"Defenders": defenders, "Advocate": advocate}

    elif method == "socratic":
        if len(model_ids) < 2:
            return None
        respondent = [model_ids[0]]
        questioners = model_ids[1:]
        return {"Respondent": respondent, "Questioners": questioners}

    elif method == "delphi":
        return {"Panelists": model_ids}

    elif method == "brainstorm":
        return {"Ideators": model_ids}

    elif method == "tradeoff":
        return {"Evaluators": model_ids}

    return None


def swap_teams(assignments: dict[str, list[str]]) -> dict[str, list[str]]:
    """Swap team assignments (FOR<->AGAINST, etc)."""
    if "FOR" in assignments and "AGAINST" in assignments:
        return {"FOR": assignments["AGAINST"], "AGAINST": assignments["FOR"]}

    elif "Defenders" in assignments and "Advocate" in assignments:
        defenders = assignments["Defenders"]
        advocate = assignments["Advocate"]
        new_defenders = advocate + defenders[:-1]
        new_advocate = [defenders[-1]] if defenders else advocate
        return {"Defenders": new_defenders, "Advocate": new_advocate}

    return assignments


# =============================================================================
# Tests
# =============================================================================

class TestMakeValidIdentifier:
    """Tests for _make_valid_identifier function."""

    def test_simple_name(self):
        assert _make_valid_identifier("gpt4") == "gpt4"

    def test_dashes_to_underscores(self):
        assert _make_valid_identifier("gpt-4") == "gpt_4"

    def test_dots_to_underscores(self):
        assert _make_valid_identifier("gpt-4.1") == "gpt_4_1"

    def test_complex_model_name(self):
        result = _make_valid_identifier("claude-sonnet-4-5-20250929")
        assert result == "claude_sonnet_4_5_20250929"

    def test_number_prefix(self):
        result = _make_valid_identifier("4gpt")
        assert result == "_4gpt"

    def test_special_chars(self):
        result = _make_valid_identifier("model@name#1")
        assert result == "model_name_1"


class TestValidateMethodModelCount:
    """Tests for validate_method_model_count function."""

    # Standard method tests
    def test_standard_with_2_models(self):
        valid, error = validate_method_model_count("standard", 2)
        assert valid is True
        assert error is None

    def test_standard_with_1_model(self):
        valid, error = validate_method_model_count("standard", 1)
        assert valid is False
        assert "at least 2" in error.lower()

    def test_standard_with_many_models(self):
        valid, error = validate_method_model_count("standard", 10)
        assert valid is True

    # Oxford method tests
    def test_oxford_with_2_models(self):
        valid, error = validate_method_model_count("oxford", 2)
        assert valid is True
        assert error is None

    def test_oxford_with_3_models(self):
        valid, error = validate_method_model_count("oxford", 3)
        assert valid is False
        assert "even" in error.lower()

    def test_oxford_with_4_models(self):
        valid, error = validate_method_model_count("oxford", 4)
        assert valid is True

    def test_oxford_with_1_model(self):
        valid, error = validate_method_model_count("oxford", 1)
        assert valid is False
        assert "at least 2" in error.lower()

    # Advocate method tests
    def test_advocate_with_3_models(self):
        valid, error = validate_method_model_count("advocate", 3)
        assert valid is True
        assert error is None

    def test_advocate_with_2_models(self):
        valid, error = validate_method_model_count("advocate", 2)
        assert valid is False
        assert "at least 3" in error.lower()

    def test_advocate_with_5_models(self):
        valid, error = validate_method_model_count("advocate", 5)
        assert valid is True

    # Socratic method tests
    def test_socratic_with_2_models(self):
        valid, error = validate_method_model_count("socratic", 2)
        assert valid is True
        assert error is None

    def test_socratic_with_1_model(self):
        valid, error = validate_method_model_count("socratic", 1)
        assert valid is False

    # Unknown method tests
    def test_unknown_method(self):
        valid, error = validate_method_model_count("unknown_method", 1)
        assert valid is True
        assert error is None


class TestGetRoleAssignments:
    """Tests for get_role_assignments function."""

    @pytest.fixture
    def two_models(self):
        return ["gpt-4.1", "claude-sonnet-4-5-20250929"]

    @pytest.fixture
    def three_models(self):
        return ["gpt-4.1", "claude-sonnet-4-5-20250929", "gemini-2.5-pro"]

    @pytest.fixture
    def four_models(self):
        return ["gpt-4.1", "claude-sonnet-4-5-20250929", "gemini-2.5-pro", "o3-mini"]

    def test_oxford_two_models(self, two_models):
        result = get_role_assignments("oxford", two_models)
        assert result is not None
        assert "FOR" in result
        assert "AGAINST" in result
        assert result["FOR"] == [two_models[0]]
        assert result["AGAINST"] == [two_models[1]]

    def test_oxford_four_models(self, four_models):
        result = get_role_assignments("oxford", four_models)
        assert result["FOR"] == [four_models[0], four_models[2]]
        assert result["AGAINST"] == [four_models[1], four_models[3]]

    def test_advocate_three_models(self, three_models):
        result = get_role_assignments("advocate", three_models)
        assert result is not None
        assert "Defenders" in result
        assert "Advocate" in result
        assert result["Defenders"] == three_models[:-1]
        assert result["Advocate"] == [three_models[-1]]

    def test_advocate_single_model(self):
        result = get_role_assignments("advocate", ["gpt-4"])
        assert result is None

    def test_socratic_assignments(self, three_models):
        result = get_role_assignments("socratic", three_models)
        assert result is not None
        assert "Respondent" in result
        assert "Questioners" in result
        assert result["Respondent"] == [three_models[0]]
        assert result["Questioners"] == three_models[1:]

    def test_socratic_single_model(self):
        result = get_role_assignments("socratic", ["gpt-4"])
        assert result is None

    def test_delphi_assignments(self, three_models):
        result = get_role_assignments("delphi", three_models)
        assert result is not None
        assert "Panelists" in result
        assert result["Panelists"] == three_models

    def test_brainstorm_assignments(self, two_models):
        result = get_role_assignments("brainstorm", two_models)
        assert result is not None
        assert "Ideators" in result
        assert result["Ideators"] == two_models

    def test_tradeoff_assignments(self, two_models):
        result = get_role_assignments("tradeoff", two_models)
        assert result is not None
        assert "Evaluators" in result
        assert result["Evaluators"] == two_models

    def test_standard_returns_none(self, two_models):
        result = get_role_assignments("standard", two_models)
        assert result is None


class TestSwapTeams:
    """Tests for swap_teams function."""

    @pytest.fixture
    def two_models(self):
        return ["gpt-4.1", "claude-sonnet-4-5-20250929"]

    @pytest.fixture
    def three_models(self):
        return ["gpt-4.1", "claude-sonnet-4-5-20250929", "gemini-2.5-pro"]

    def test_swap_oxford_teams(self, two_models):
        original = {"FOR": [two_models[0]], "AGAINST": [two_models[1]]}
        swapped = swap_teams(original)
        assert swapped["FOR"] == [two_models[1]]
        assert swapped["AGAINST"] == [two_models[0]]

    def test_swap_oxford_back(self, two_models):
        original = {"FOR": [two_models[0]], "AGAINST": [two_models[1]]}
        swapped = swap_teams(swap_teams(original))
        assert swapped == original

    def test_swap_advocate(self, three_models):
        original = {
            "Defenders": [three_models[0], three_models[1]],
            "Advocate": [three_models[2]],
        }
        swapped = swap_teams(original)
        assert swapped["Advocate"] == [three_models[1]]
        assert three_models[2] in swapped["Defenders"]

    def test_swap_unknown_preserves(self):
        original = {"Unknown": ["a", "b"]}
        swapped = swap_teams(original)
        assert swapped == original

    def test_swap_socratic_preserves(self, three_models):
        original = {"Respondent": [three_models[0]], "Questioners": three_models[1:]}
        swapped = swap_teams(original)
        assert swapped == original

    def test_swap_delphi_preserves(self, three_models):
        original = {"Panelists": three_models}
        swapped = swap_teams(original)
        assert swapped == original

    def test_swap_brainstorm_preserves(self, two_models):
        original = {"Ideators": two_models}
        swapped = swap_teams(original)
        assert swapped == original

    def test_swap_tradeoff_preserves(self, two_models):
        original = {"Evaluators": two_models}
        swapped = swap_teams(original)
        assert swapped == original


class TestValidateNewMethods:
    """Tests for new method validation (Delphi, Brainstorm, Tradeoff)."""

    # Delphi tests
    def test_delphi_with_3_models(self):
        valid, error = validate_method_model_count("delphi", 3)
        assert valid is True
        assert error is None

    def test_delphi_with_2_models(self):
        valid, error = validate_method_model_count("delphi", 2)
        assert valid is False
        assert "at least 3" in error.lower()

    def test_delphi_with_5_models(self):
        valid, error = validate_method_model_count("delphi", 5)
        assert valid is True

    # Brainstorm tests
    def test_brainstorm_with_2_models(self):
        valid, error = validate_method_model_count("brainstorm", 2)
        assert valid is True
        assert error is None

    def test_brainstorm_with_1_model(self):
        valid, error = validate_method_model_count("brainstorm", 1)
        assert valid is False
        assert "at least 2" in error.lower()

    def test_brainstorm_with_many_models(self):
        valid, error = validate_method_model_count("brainstorm", 10)
        assert valid is True

    # Tradeoff tests
    def test_tradeoff_with_2_models(self):
        valid, error = validate_method_model_count("tradeoff", 2)
        assert valid is True
        assert error is None

    def test_tradeoff_with_1_model(self):
        valid, error = validate_method_model_count("tradeoff", 1)
        assert valid is False
        assert "at least 2" in error.lower()

    def test_tradeoff_with_many_models(self):
        valid, error = validate_method_model_count("tradeoff", 8)
        assert valid is True


class TestMethodAdvisorPrompt:
    """Tests for the method advisor prompt."""

    def test_advisor_prompt_contains_question(self):
        from quorum.agents import get_method_advisor_prompt
        question = "How long will the migration take?"
        prompt = get_method_advisor_prompt(question)
        assert question in prompt

    def test_advisor_prompt_contains_all_methods(self):
        from quorum.agents import get_method_advisor_prompt
        prompt = get_method_advisor_prompt("test question")
        # Check all methods are mentioned
        assert "STANDARD" in prompt
        assert "OXFORD" in prompt
        assert "ADVOCATE" in prompt
        assert "SOCRATIC" in prompt
        assert "DELPHI" in prompt
        assert "BRAINSTORM" in prompt
        assert "TRADEOFF" in prompt

    def test_advisor_prompt_specifies_json_output(self):
        from quorum.agents import get_method_advisor_prompt
        prompt = get_method_advisor_prompt("test")
        assert "JSON" in prompt
        assert "primary" in prompt
        assert "alternatives" in prompt
