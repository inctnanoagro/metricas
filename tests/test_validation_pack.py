"""Tests for validation pack exports."""

from pathlib import Path
import json
import re
import shutil

import pytest

from metricas_lattes.exports.validation_pack import (
    generate_validation_pack,
    _normalize_section_name,
)


FIXTURE_PATH = Path('tests/fixtures/validation_pack/carlos_alberto_perez.json')


def test_generate_validation_pack_html(tmp_path: Path) -> None:
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture not found: {FIXTURE_PATH}")

    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'out'
    input_dir.mkdir()

    fixture_copy = input_dir / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, fixture_copy)

    generate_validation_pack(input_dir, output_dir, ['html'])

    lattes_id = json.loads(fixture_copy.read_text(encoding='utf-8'))['researcher']['lattes_id']
    html_path = output_dir / 'researchers' / f'{lattes_id}__' / 'VALIDACAO.html'
    assert html_path.exists()

    full_name = json.loads(fixture_copy.read_text(encoding='utf-8'))['researcher']['full_name']
    html = html_path.read_text(encoding='utf-8')
    assert full_name in html


def test_validation_pack_section_order(tmp_path: Path) -> None:
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture not found: {FIXTURE_PATH}")

    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'out'
    input_dir.mkdir()

    fixture_copy = input_dir / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, fixture_copy)

    generate_validation_pack(input_dir, output_dir, ['html'])

    data = json.loads(fixture_copy.read_text(encoding='utf-8'))
    lattes_id = data['researcher']['lattes_id']
    html_path = output_dir / 'researchers' / f'{lattes_id}__' / 'VALIDACAO.html'
    html = html_path.read_text(encoding='utf-8')

    headings = re.findall(r'<h2>(.*?)</h2>', html)
    productions = data.get('productions', [])
    grouped = set()
    for item in productions:
        source = item.get('source') or {}
        grouped.add(_normalize_section_name(source.get('production_type')))

    expected = []
    for section in data.get('metadata', {}).get('sections', []):
        name = _normalize_section_name(section.get('section_title'))
        if name in grouped and name not in expected:
            expected.append(name)
    for name in sorted(grouped):
        if name not in expected:
            expected.append(name)

    assert headings == expected
