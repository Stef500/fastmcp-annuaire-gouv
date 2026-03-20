"""Tests for the categories module."""

import pytest

from annuaire_mcp.categories import (
    CATEGORIES,
    CATEGORY_SYSTEM,
    build_type_token,
    get_category_code,
)


def test_all_categories_have_code_and_label() -> None:
    for key, (code, label) in CATEGORIES.items():
        assert code.isdigit(), f"Category {key} has non-numeric code: {code}"
        assert label, f"Category {key} has empty label"


def test_get_category_code_known() -> None:
    assert get_category_code("EHPAD") == "500"
    assert get_category_code("IME") == "182"
    assert get_category_code("MAS") == "437"
    assert get_category_code("EEAP") == "183"
    assert get_category_code("RESIDENCE_AUTONOMIE") == "202"


def test_get_category_code_case_insensitive() -> None:
    assert get_category_code("ehpad") == "500"
    assert get_category_code("Ehpad") == "500"


def test_get_category_code_unknown() -> None:
    assert get_category_code("UNKNOWN_TYPE") is None


def test_build_type_token() -> None:
    token = build_type_token("500")
    assert token == f"{CATEGORY_SYSTEM}|500"


@pytest.mark.parametrize("key", list(CATEGORIES.keys()))
def test_all_categories_are_retrievable(key: str) -> None:
    code = get_category_code(key)
    assert code is not None
    assert build_type_token(code).startswith(CATEGORY_SYSTEM)
