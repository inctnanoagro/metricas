"""Tests for validation pack exports."""

from pathlib import Path
import json
import re
import shutil

import pytest

from metricas_lattes.exports.validation_pack import (
    generate_validation_pack,
    _ordered_section_names,
    _section_identity,
)
from metricas_lattes.batch_full_profile import process_researcher_file


FIXTURE_PATH = Path('tests/fixtures/validation_pack/carlos_alberto_perez.json')
FRACETO_FIXTURE = Path('tests/fixtures/lattes/full_profile/full_profile_leonardo_fraceto.html')


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

    headings = [
        re.sub(r'\s*\(\d+\)\s*$', '', heading).strip()
        for heading in re.findall(r'<h2>(.*?)</h2>', html)
    ]
    productions = data.get('productions', [])
    grouped = {}
    labels = {}
    for item in productions:
        key, label = _section_identity(item)
        if key not in grouped:
            grouped[key] = []
        if key not in labels:
            labels[key] = label

    section_order = _ordered_section_names(data.get('metadata', {}).get('sections', []), grouped)
    expected = [labels[key] for key in section_order]

    assert headings == expected


def test_validation_pack_sections_from_fraceto(tmp_path: Path) -> None:
    if not FRACETO_FIXTURE.exists():
        pytest.skip(f"Fixture not found: {FRACETO_FIXTURE}")

    batch_dir = tmp_path / 'batch'
    (batch_dir / 'researchers').mkdir(parents=True)

    result = process_researcher_file(FRACETO_FIXTURE, batch_dir, schema=None, allowed_years=None)
    assert result['success'] is True

    output_dir = tmp_path / 'out'
    generate_validation_pack(batch_dir / 'researchers', output_dir, ['html'])

    lattes_id = result['lattes_id']
    html_path = output_dir / 'researchers' / f'{lattes_id}__' / 'VALIDACAO.html'
    html = html_path.read_text(encoding='utf-8')
    headings = [
        re.sub(r'\s*\(\d+\)\s*$', '', heading).strip()
        for heading in re.findall(r'<h2>(.*?)</h2>', html)
    ]

    assert len(set(headings)) > 1
    assert any(heading != 'Produções' for heading in headings)
