"""Tests for year filtering in batch_full_profile."""

import json
from pathlib import Path

import pytest

from metricas_lattes.batch_full_profile import (
    DEFAULT_ALLOWED_YEARS,
    _infer_year_from_item,
    filter_productions_by_year,
    parse_years_arg,
    process_researcher_file,
)


def test_filter_default_years():
    items = [
        {"id": "a", "ano": 2024, "raw": "Item 2024"},
        {"id": "b", "ano": 2023, "raw": "Item 2023"},
        {"id": "c", "ano": None, "raw": "Algo em 2025."},
        {"id": "d", "ano": None, "raw": "Sem ano aqui"},
    ]
    filtered = filter_productions_by_year(items, DEFAULT_ALLOWED_YEARS)
    assert [item["id"] for item in filtered] == ["a", "c"]


def test_filter_override_all():
    items = [
        {"id": "a", "ano": 2024, "raw": "Item 2024"},
        {"id": "b", "ano": 2023, "raw": "Item 2023"},
    ]
    filtered = filter_productions_by_year(items, None)
    assert [item["id"] for item in filtered] == ["a", "b"]


def test_parse_years_arg():
    assert parse_years_arg(None) == DEFAULT_ALLOWED_YEARS
    assert parse_years_arg("all") is None
    assert parse_years_arg("2023, 2024") == [2023, 2024]


def test_batch_default_filter_metadata(tmp_path: Path):
    fixture_path = Path("tests/fixtures/lattes/full_profile/full_profile_leonardo_fraceto.html")
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")

    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "researchers").mkdir(exist_ok=True)

    result = process_researcher_file(
        fixture_path,
        output_dir,
        schema=None,
        allowed_years=DEFAULT_ALLOWED_YEARS,
    )

    json_path = Path(result["output_json"])
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["metadata"]["filters"]["years"] == [2024, 2025]

    productions = data["productions"]
    assert productions, "Expected productions after filtering"
    for item in productions:
        year = _infer_year_from_item(item)
        assert year in DEFAULT_ALLOWED_YEARS
