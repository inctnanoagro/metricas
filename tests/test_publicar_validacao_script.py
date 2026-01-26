"""Tests for publicar_validacao.sh script."""

from pathlib import Path
import re


SCRIPT_PATH = Path('scripts/publicar_validacao.sh')


def test_publicar_validacao_has_timestamp_and_relative_paths() -> None:
    content = SCRIPT_PATH.read_text(encoding='utf-8')

    assert 'outputs/dry_run_' in content
    assert 'outputs/validation_' in content

    timestamp_re = re.compile(r'date \+"%Y%m%d-%H%M%S"')
    assert timestamp_re.search(content)

    assert '/Users/' not in content
    assert '/home/' not in content
