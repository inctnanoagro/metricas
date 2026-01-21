"""Regression tests for order preservation in validation pack exports."""

from pathlib import Path
import json
import re

from metricas_lattes.exports.validation_pack import generate_validation_pack


def _extract_titles_from_html(html: str) -> list[str]:
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", html, re.S)
    assert tbody_match is not None
    tbody = tbody_match.group(1)
    rows = re.findall(r"<tr>\s*(.*?)\s*</tr>", tbody, re.S)
    titles: list[str] = []
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) >= 2:
            title = re.sub(r"<.*?>", "", cells[1]).strip()
            titles.append(title)
    return titles


def test_validation_pack_preserves_input_order(tmp_path: Path) -> None:
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'out'
    input_dir.mkdir()

    data = {
        'researcher': {'lattes_id': '123', 'full_name': 'Tester'},
        'productions': [
            {
                'numero_item': 1,
                'titulo': 'A1',
                'source': {'production_type': 'Artigos'},
            },
            {
                'numero_item': 2,
                'titulo': 'A2',
                'source': {'production_type': 'Artigos'},
            },
            {
                'numero_item': 1,
                'titulo': 'B1',
                'source': {'production_type': 'Artigos'},
            },
            {
                'numero_item': 2,
                'titulo': 'B2',
                'source': {'production_type': 'Artigos'},
            },
        ],
        'metadata': {'sections': [{'section_title': 'Artigos'}]},
    }

    json_path = input_dir / '123__tester.json'
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    generate_validation_pack(input_dir, output_dir, ['html'])

    html_path = output_dir / 'researchers' / '123__' / 'VALIDACAO.html'
    html = html_path.read_text(encoding='utf-8')

    assert _extract_titles_from_html(html) == ['A1', 'A2', 'B1', 'B2']
