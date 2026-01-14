"""Tests for validation pack exports."""

from pathlib import Path
import json
import shutil

import pytest

from metricas_lattes.exports.validation_pack import generate_validation_pack


FIXTURE_PATH = Path(
    'outputs/dry_run_20260114-140804/researchers/8926782971408348__erika-alvim-de-sa-e-benevides.json'
)


def test_generate_validation_pack_html(tmp_path: Path) -> None:
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture not found: {FIXTURE_PATH}")

    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'out'
    input_dir.mkdir()

    fixture_copy = input_dir / FIXTURE_PATH.name
    shutil.copyfile(FIXTURE_PATH, fixture_copy)

    generate_validation_pack(input_dir, output_dir, ['html'])

    html_path = output_dir / 'researchers' / '8926782971408348__' / 'VALIDACAO.html'
    assert html_path.exists()

    data = json.loads(fixture_copy.read_text(encoding='utf-8'))
    full_name = data['researcher']['full_name']
    html = html_path.read_text(encoding='utf-8')
    assert full_name in html
