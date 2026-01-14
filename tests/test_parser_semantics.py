"""Semantic parser tests for authors, titles, and numbering."""

from pathlib import Path
import re

import pytest

from metricas_lattes.parser_router import parse_fixture


def _write_fixture(tmp_path: Path, filename: str, body: str) -> Path:
    html = f"""
    <html><body>
      {body}
    </body></html>
    """
    path = tmp_path / filename
    path.write_text(html, encoding='utf-8')
    return path


def test_autores_cleaned_and_renumbered_for_artigos(tmp_path: Path) -> None:
    body = """
    <div class="layout-cell-1"><b>7.</b></div>
    <div class="layout-cell-11">
      <span class="transform">SILVA, A.2020; SOUZA, B. . Titulo do artigo. Revista X, v. 1, p. 10-20, 2020.</span>
    </div>
    """
    fixture = _write_fixture(tmp_path, 'Artigos completos publicados em periodicos.html', body)
    result = parse_fixture(fixture)

    assert result['items']
    item = result['items'][0]
    assert item['numero_item'] == 1
    assert item['autores'] is not None
    assert re.search(r'\b(19|20)\d{2}\b', item['autores']) is None


def test_filter_invalid_titles_and_renumber_for_bancas(tmp_path: Path) -> None:
    body = """
    <div class="layout-cell-1"><b>1.</b></div>
    <div class="layout-cell-11">
      <span class="transform">SILVA, A.; SOUZA, B. . A . 2020.</span>
    </div>
    <div class="layout-cell-1"><b>2.</b></div>
    <div class="layout-cell-11">
      <span class="transform">PEREIRA, C. . TEST . 2021.</span>
    </div>
    <div class="layout-cell-1"><b>3.</b></div>
    <div class="layout-cell-11">
      <span class="transform">ALMEIDA, D. . Estudo sobre nanomateriais em bancas. 2022.</span>
    </div>
    """
    fixture = _write_fixture(tmp_path, 'temp__bancas.html', body)
    result = parse_fixture(fixture)

    assert len(result['items']) == 1
    assert result['items'][0]['numero_item'] == 1
    assert 'Estudo sobre nanomateriais' in (result['items'][0].get('titulo') or '')


def test_autores_without_years_in_generic(tmp_path: Path) -> None:
    body = """
    <div class="layout-cell-1"><b>9.</b></div>
    <div class="layout-cell-11">
      <span class="transform">COSTA, M.2021; LIMA, R. . Trabalho tecnico. 2021.</span>
    </div>
    """
    fixture = _write_fixture(tmp_path, 'temp__eventos.html', body)
    result = parse_fixture(fixture)

    assert result['items']
    autores = result['items'][0].get('autores') or ''
    assert re.search(r'\b(19|20)\d{2}\b', autores) is None
