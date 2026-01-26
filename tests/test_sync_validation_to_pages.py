"""Tests for sync_validation_to_pages script."""

from __future__ import annotations

import json
from pathlib import Path
import importlib.util


SCRIPT_PATH = Path('scripts/sync_validation_to_pages.py')


def _load_script_module():
    spec = importlib.util.spec_from_file_location('sync_validation_to_pages', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extract_lattes_id() -> None:
    module = _load_script_module()
    assert module.extract_lattes_id('4741480538883395__leonardo.json') == '4741480538883395'
    assert module.extract_lattes_id('4741480538883395__leonardo-fernandes-fraceto.json') == '4741480538883395'
    assert module.extract_lattes_id('short__name.json') is None
    assert module.extract_lattes_id('nounderscore.json') is None


def test_manifest_order_deterministic(tmp_path: Path) -> None:
    module = _load_script_module()

    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'out'
    input_dir.mkdir()
    output_dir.mkdir()

    (input_dir / '9999999999999999__zeta.json').write_text('{"ok": true}', encoding='utf-8')
    (input_dir / '1111111111111111__alpha.json').write_text('{"ok": true}', encoding='utf-8')
    (input_dir / 'not_a_json.txt').write_text('x', encoding='utf-8')

    manifest = module.sync_validation_to_pages(input_dir, output_dir)

    manifest_path = output_dir / 'manifest.json'
    assert manifest_path.exists()
    manifest_on_disk = json.loads(manifest_path.read_text(encoding='utf-8'))

    expected_order = ['1111111111111111', '9999999999999999']
    assert list(manifest['by_lattes_id'].keys()) == expected_order
    assert list(manifest_on_disk['by_lattes_id'].keys()) == expected_order
    assert (output_dir / '1111111111111111__alpha.json').exists()
    assert (output_dir / '9999999999999999__zeta.json').exists()
