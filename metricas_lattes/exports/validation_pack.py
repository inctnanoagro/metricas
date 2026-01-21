"""Generate human validation packs from canonical researcher JSONs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from metricas_lattes.parsers.utils import split_citacao

COLUMN_ORDER = [
    'numero_item',
    'ano',
    'titulo',
    'autores',
    'veiculo_ou_livro',
    'doi',
    'paginas',
    'volume',
    'source_file',
    'section',
    'pertence_INCT',
    'observacoes',
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def _safe_text(value: Any) -> str:
    if value is None:
        return ''
    return str(value)


def _extract_field(item: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = item.get(key)
        if value not in (None, ''):
            return _safe_text(value)
    return ''


def _looks_like_author_list(text: str) -> bool:
    if not text or ';' not in text:
        return False
    matches = re.findall(r'\b[A-ZÀ-Ú]{2,},\s*[A-Z]\.', text)
    return len(matches) >= 2


def _split_raw_blocks(raw: str) -> List[str]:
    normalized = re.sub(r'\s+', ' ', raw).strip()
    if not normalized:
        return []
    parts = re.split(r'\s+\.\s+', normalized)
    if len(parts) < 2:
        parts = re.split(r'\s*\.\s+', normalized)
    return [part.strip() for part in parts if part.strip()]


def _autores_tem_ano(autores: str) -> bool:
    if not autores:
        return False
    return re.search(r'(?:\b|\.)\s*(19|20)\d{2}\b', autores) is not None


def _autores_parecem_lista(autores: str) -> bool:
    if not autores:
        return False
    if ';' in autores:
        return True
    return re.search(r'\b[A-ZÀ-Ú]{2,},\s*[A-Z]', autores) is not None


def _compute_display_fields(item: Dict[str, Any]) -> Tuple[str, str]:
    raw = _safe_text(item.get('raw') or '')
    titulo = _extract_field(item, ['titulo', 'title'])
    autores = _extract_field(item, ['autores'])
    split_autores, split_titulo, _split_veiculo = split_citacao(raw)

    display_titulo = titulo
    display_autores = autores

    if split_autores and _autores_parecem_lista(split_autores):
        if not display_autores or _autores_tem_ano(display_autores):
            display_autores = split_autores
        display_autores = split_autores

    titulo_precisa_fallback = (
        not display_titulo
        or (raw and display_titulo.strip() == raw.strip())
        or _looks_like_author_list(display_titulo)
    )

    if raw and titulo_precisa_fallback:
        if split_titulo:
            display_titulo = split_titulo
        else:
            parts = _split_raw_blocks(raw)
            if len(parts) >= 2:
                display_titulo = parts[1]
            elif not display_titulo:
                display_titulo = raw

        if not display_autores and split_autores:
            display_autores = split_autores

    if raw and not display_autores and _looks_like_author_list(raw):
        if split_autores:
            display_autores = split_autores
        else:
            parts = _split_raw_blocks(raw)
            if parts:
                display_autores = parts[0]

    return display_titulo, display_autores


def _compute_veiculo_ou_livro(item: Dict[str, Any]) -> str:
    veiculo = _extract_field(item, ['veiculo', 'livro', 'veiculo_ou_livro', 'periodico', 'revista'])
    if veiculo:
        return veiculo
    raw = _safe_text(item.get('raw') or '')
    _, _, split_veiculo = split_citacao(raw)
    return split_veiculo


def _group_by_production_type(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        source = item.get('source') or {}
        production_type = _normalize_section_name(source.get('production_type'))
        grouped[production_type].append(item)
    return grouped


def _normalize_section_name(value: Any) -> str:
    name = _safe_text(value or '').strip()
    if not name:
        return 'Desconhecido'
    if name.startswith('temp__'):
        name = name[len('temp__'):]
        name = name.replace('_', ' ')
        name = name.lower().strip()
    return name or 'Desconhecido'


def _sanitize_sheet_name(name: str, used: set) -> str:
    base = ''.join(ch for ch in name if ch not in '[]:*?/\\')
    if not base:
        base = 'Sheet'
    base = base[:31]
    candidate = base
    counter = 1
    while candidate in used:
        suffix = f"_{counter}"
        candidate = (base[: 31 - len(suffix)] + suffix) if len(base) > len(suffix) else base + suffix
        counter += 1
    used.add(candidate)
    return candidate


def _ordered_section_names(
    sections_metadata: List[Dict[str, Any]],
    grouped: Dict[str, List[Dict[str, Any]]],
) -> List[str]:
    grouped_keys = list(grouped.keys())
    ordered: List[str] = []
    for section in sections_metadata:
        title = section.get('section_title') or section.get('tipo_producao')
        name = _normalize_section_name(title)
        if name in grouped and name not in ordered:
            ordered.append(name)
    for name in grouped_keys:
        if name not in ordered:
            ordered.append(name)
    return ordered


def _render_html_researcher(
    researcher: Dict[str, Any],
    productions: List[Dict[str, Any]],
    section_order: List[str] | None = None,
) -> str:
    full_name = _safe_text(researcher.get('full_name') or 'Pesquisador(a)')
    lattes_id = _safe_text(researcher.get('lattes_id') or 'N/A')

    grouped = _group_by_production_type(productions)
    section_names = section_order or list(grouped.keys())
    sections = []

    for section_name in section_names:
        if section_name not in grouped:
            continue
        items = grouped[section_name]
        rows = []
        for item in items:
            numero_item = _safe_text(item.get('numero_item'))
            display_titulo, display_autores = _compute_display_fields(item)
            veiculo = _compute_veiculo_ou_livro(item)
            ano = _safe_text(item.get('ano') or '')
            rows.append(
                """
                <tr>
                  <td class="numero">{numero_item}</td>
                  <td>{titulo}</td>
                  <td>{autores}</td>
                  <td>{veiculo}</td>
                  <td class="ano">{ano}</td>
                  <td class="checkbox"><input type="checkbox" aria-label="Pertence ao INCT"></td>
                  <td><textarea rows="2" placeholder="Observacoes"></textarea></td>
                </tr>
                """.format(
                    numero_item=escape(numero_item),
                    titulo=escape(display_titulo),
                    autores=escape(display_autores),
                    veiculo=escape(veiculo),
                    ano=escape(ano),
                )
            )

        sections.append(
            """
            <section>
              <h2>{section_name}</h2>
              <table>
                <thead>
                  <tr>
                    <th>numero_item</th>
                    <th>titulo</th>
                    <th>autores</th>
                    <th>veiculo/livro</th>
                    <th>ano</th>
                    <th>Pertence ao INCT?</th>
                    <th>observacoes</th>
                  </tr>
                </thead>
                <tbody>
                  {rows}
                </tbody>
              </table>
            </section>
            """.format(
                section_name=escape(section_name),
                rows='\n'.join(rows),
            )
        )

    return """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Validacao - {full_name}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f5ef;
      --ink: #1f1f1f;
      --accent: #2f6f3e;
      --muted: #5f5f5f;
      --table: #ffffff;
      --border: #d9d3c7;
    }}
    body {{
      margin: 0;
      padding: 24px;
      font-family: "Georgia", "Times New Roman", serif;
      background: var(--bg);
      color: var(--ink);
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 28px;
    }}
    .meta {{
      margin-bottom: 24px;
      color: var(--muted);
    }}
    section {{
      margin-bottom: 32px;
    }}
    h2 {{
      margin-bottom: 8px;
      font-size: 20px;
      color: var(--accent);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--table);
      border: 1px solid var(--border);
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 8px;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      background: #efe9dd;
      text-align: left;
    }}
    textarea {{
      width: 100%;
      border: 1px solid var(--border);
      resize: vertical;
      font-family: inherit;
      font-size: 13px;
    }}
    .numero, .ano {{
      white-space: nowrap;
      text-align: center;
    }}
    .checkbox {{
      text-align: center;
    }}
  </style>
</head>
<body>
  <h1>{full_name}</h1>
  <div class="meta">Lattes ID: {lattes_id}</div>
  {sections}
</body>
</html>
""".format(
        full_name=escape(full_name),
        lattes_id=escape(lattes_id),
        sections='\n'.join(sections),
    )


def _write_xlsx(
    output_path: Path,
    productions: List[Dict[str, Any]],
    section_order: List[str] | None = None,
) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("openpyxl nao esta instalado. Adicione em requirements.txt") from exc

    grouped = _group_by_production_type(productions)
    workbook = Workbook()
    default_sheet = workbook.active
    used_names: set = set()
    headers = COLUMN_ORDER[:]

    if not grouped:
        default_sheet.title = "Produções"
        default_sheet.append(headers)
        workbook.save(output_path)
        return

    workbook.remove(default_sheet)

    section_names = section_order or list(grouped.keys())
    for section_name in section_names:
        if section_name not in grouped:
            continue
        sheet_name = _sanitize_sheet_name(section_name, used_names)
        sheet = workbook.create_sheet(title=sheet_name)
        sheet.append(headers)

        for item in grouped[section_name]:
            display_titulo, display_autores = _compute_display_fields(item)
            source = item.get('source') or {}
            row = []
            for column in COLUMN_ORDER:
                if column == 'numero_item':
                    row.append(item.get('numero_item'))
                elif column == 'ano':
                    row.append(item.get('ano'))
                elif column == 'titulo':
                    row.append(display_titulo)
                elif column == 'autores':
                    row.append(display_autores)
                elif column == 'veiculo_ou_livro':
                    row.append(_compute_veiculo_ou_livro(item))
                elif column == 'doi':
                    row.append(item.get('doi'))
                elif column == 'paginas':
                    row.append(item.get('paginas'))
                elif column == 'volume':
                    row.append(item.get('volume'))
                elif column == 'source_file':
                    row.append(source.get('file'))
                elif column == 'section':
                    row.append(section_name)
                elif column == 'pertence_INCT':
                    row.append('')
                elif column == 'observacoes':
                    row.append('')
                else:
                    row.append('')
            sheet.append(row)

    workbook.save(output_path)


def _collect_json_files(input_dir: Path) -> List[Path]:
    return sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == '.json')


def _resolve_lattes_id(researcher: Dict[str, Any], filename: str) -> str:
    lattes_id = researcher.get('lattes_id')
    if lattes_id:
        return str(lattes_id)
    if '__' in filename:
        return filename.split('__', 1)[0]
    return 'unknown'


def generate_validation_pack(input_dir: Path, output_dir: Path, formats: List[str]) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    researchers_root = output_dir / 'researchers'
    researchers_root.mkdir(parents=True, exist_ok=True)

    json_files = _collect_json_files(input_dir)
    if not json_files:
        print(f"Nenhum JSON encontrado em {input_dir}")

    manifest_entries = []
    index_rows = []

    for json_path in json_files:
        try:
            data = _load_json(json_path)
        except json.JSONDecodeError as exc:
            print(f"Falha ao ler {json_path.name}: {exc}")
            continue

        researcher = data.get('researcher', {})
        productions = data.get('productions', [])
        lattes_id = _resolve_lattes_id(researcher, json_path.name)
        full_name = _safe_text(researcher.get('full_name') or json_path.stem)

        sections_metadata = (data.get('metadata') or {}).get('sections', [])
        grouped = _group_by_production_type(productions)
        section_order = _ordered_section_names(sections_metadata, grouped)

        researcher_dir = researchers_root / f"{lattes_id}__"
        researcher_dir.mkdir(parents=True, exist_ok=True)

        dados_path = researcher_dir / 'dados.json'
        shutil.copyfile(json_path, dados_path)

        if 'html' in formats:
            html_content = _render_html_researcher(
                researcher,
                productions,
                section_order=section_order,
            )
            (researcher_dir / 'VALIDACAO.html').write_text(html_content, encoding='utf-8')

        if 'xlsx' in formats:
            _write_xlsx(
                researcher_dir / 'VALIDACAO.xlsx',
                productions,
                section_order=section_order,
            )

        total_items = len(productions)
        index_rows.append(
            {
                'lattes_id': lattes_id,
                'full_name': full_name,
                'total_items': total_items,
                'html_path': f"researchers/{lattes_id}__/VALIDACAO.html",
            }
        )
        manifest_entries.append(
            {
                'lattes_id': lattes_id,
                'full_name': full_name,
                'total_items': total_items,
                'source_json': json_path.name,
                'output_dir': f"researchers/{lattes_id}__/",
            }
        )

    index_rows.sort(key=lambda row: row['lattes_id'])
    manifest_entries.sort(key=lambda row: row['lattes_id'])

    index_html = _render_index(index_rows, formats)
    (output_dir / 'index.html').write_text(index_html, encoding='utf-8')

    manifest = {
        'generated_at': datetime.now().isoformat(),
        'formats': sorted(set(formats)),
        'researchers': manifest_entries,
    }
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    return manifest


def _render_index(rows: List[Dict[str, Any]], formats: List[str]) -> str:
    rows_html = []
    for row in rows:
        link = escape(row['html_path'])
        name = escape(row['full_name'])
        lattes_id = escape(row['lattes_id'])
        total = escape(str(row['total_items']))
        if 'html' in formats:
            name_html = f"<a href=\"{link}\">{name}</a>"
        else:
            name_html = name
        rows_html.append(
            f"<tr><td>{lattes_id}</td><td>{name_html}</td><td>{total}</td></tr>"
        )

    return """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pacote de Validacao</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      font-family: "Georgia", "Times New Roman", serif;
      background: #f7f5ef;
      color: #1f1f1f;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      border: 1px solid #d9d3c7;
    }}
    th, td {{
      border: 1px solid #d9d3c7;
      padding: 8px;
      text-align: left;
      font-size: 14px;
    }}
    th {{
      background: #efe9dd;
    }}
  </style>
</head>
<body>
  <h1>Pacote de Validacao</h1>
  <p>Total de pesquisadores: {total}</p>
  <table>
    <thead>
      <tr>
        <th>Lattes ID</th>
        <th>Pesquisador</th>
        <th>Total de producoes</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
""".format(
        total=len(rows),
        rows='\n'.join(rows_html),
    )


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Gera pacote de validacao humana a partir de JSONs canonicos.',
    )
    parser.add_argument(
        '--in',
        dest='input_dir',
        required=True,
        help='Pasta contendo os JSONs canonicos (researchers/)',
    )
    parser.add_argument(
        '--out',
        dest='output_dir',
        required=True,
        help='Pasta de saida do pacote de validacao',
    )
    parser.add_argument(
        '--format',
        dest='formats',
        nargs='+',
        choices=['html', 'xlsx'],
        default=['html'],
        help='Formatos a gerar (html, xlsx)',
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    formats = [fmt.lower() for fmt in args.formats]
    print(f"Lendo JSONs em: {input_dir}")
    print(f"Saida: {output_dir}")
    print(f"Formatos: {', '.join(formats)}")

    if not input_dir.exists():
        print(f"Erro: pasta de entrada nao existe: {input_dir}")
        return 1
    if not input_dir.is_dir():
        print(f"Erro: entrada nao e uma pasta: {input_dir}")
        return 1

    generate_validation_pack(input_dir, output_dir, formats)
    print("Pacote de validacao gerado com sucesso.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
