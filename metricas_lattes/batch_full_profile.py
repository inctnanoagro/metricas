#!/usr/bin/env python3
"""
Batch processor for full_profile.html files.

Processes a directory of researcher full_profile HTMLs and generates:
- Individual JSON per researcher
- Summary report
- Errors report
- Audit report

Usage:
    python3 -m metricas_lattes.batch_full_profile --in <input_dir> --out <output_dir> [--schema <schema_path>]
"""

import argparse
import json
import sys
import re
import html as html_lib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Iterable
from bs4 import BeautifulSoup
import unicodedata
import hashlib

# Import existing parser infrastructure
from metricas_lattes.parser_router import parse_fixture, PARSER_REGISTRY
from metricas_lattes.parsers.utils import split_citacao

DEFAULT_ALLOWED_YEARS = [2024, 2025]
_MOJIBAKE_MARKERS = ('Ã', 'Â', 'â€', 'â€œ', 'â€', 'â€™', 'â€“', 'â€”', 'ðŸ', 'ï¿½')


def _count_mojibake_markers(text: str) -> int:
    return sum(text.count(marker) for marker in _MOJIBAKE_MARKERS)


def _maybe_fix_mojibake(text: str, codec: str, strict: bool) -> Optional[str]:
    try:
        return text.encode(codec, errors='strict' if strict else 'ignore').decode('utf-8', errors='strict' if strict else 'ignore')
    except UnicodeError:
        return None


def normalize_text(value: Any, *, unescape_html: bool = True) -> Any:
    """
    Normalize mixed-encoding text (mojibake + HTML entities) to clean UTF-8.
    Accepts str or bytes; other types are returned unchanged.
    """
    if isinstance(value, bytes):
        text = value.decode('utf-8', errors='surrogateescape')
        if any(0xDC80 <= ord(ch) <= 0xDCFF for ch in text):
            chars = []
            for ch in text:
                code = ord(ch)
                if 0xDC80 <= code <= 0xDCFF:
                    chars.append(chr(code - 0xDC00))
                else:
                    chars.append(ch)
            text = ''.join(chars)
    elif isinstance(value, str):
        text = value
    else:
        return value

    if unescape_html:
        text = html_lib.unescape(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    for _ in range(2):
        if not any(marker in text for marker in _MOJIBAKE_MARKERS):
            break
        current_score = _count_mojibake_markers(text)
        candidate = (
            _maybe_fix_mojibake(text, 'latin-1', strict=True)
            or _maybe_fix_mojibake(text, 'cp1252', strict=True)
        )
        if candidate is None or _count_mojibake_markers(candidate) >= current_score:
            candidate = (
                _maybe_fix_mojibake(text, 'latin-1', strict=False)
                or _maybe_fix_mojibake(text, 'cp1252', strict=False)
            )
        if candidate is None or _count_mojibake_markers(candidate) >= current_score:
            break
        text = candidate

    return text


def normalize_html_text(raw_bytes: bytes) -> str:
    """
    Normalize mixed-encoding HTML bytes to clean UTF-8 text.
    """
    text = raw_bytes.decode('utf-8', errors='surrogateescape')
    if any(0xDC80 <= ord(ch) <= 0xDCFF for ch in text):
        chars = []
        for ch in text:
            code = ord(ch)
            if 0xDC80 <= code <= 0xDCFF:
                chars.append(chr(code - 0xDC00))
            else:
                chars.append(ch)
        text = ''.join(chars)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Force charset to UTF-8 to prevent BeautifulSoup/lxml from re-encoding
    # based on incorrect meta tags (Lattes often claims ISO-8859-1 but is UTF-8)
    text = re.sub(
        r'<meta[^>]+charset=[^>]+>',
        '<meta charset="utf-8">',
        text,
        flags=re.IGNORECASE
    )
    return text


def normalize_nested_text(value: Any, *, exclude_keys: Optional[set] = None) -> Any:
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            if exclude_keys and key in exclude_keys:
                normalized[key] = item
            else:
                normalized[key] = normalize_nested_text(item, exclude_keys=exclude_keys)
        return normalized
    if isinstance(value, list):
        return [normalize_nested_text(item, exclude_keys=exclude_keys) for item in value]
    if isinstance(value, str):
        return normalize_text(value, unescape_html=True)
    return value


def _basic_schema_validation(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in schema.get('required', []):
        if key not in data:
            errors.append(f"Missing required field: {key}")

    schema_version = data.get('schema_version')
    expected_version = (
        schema.get('properties', {})
        .get('schema_version', {})
        .get('const')
    )
    if expected_version is not None and schema_version != expected_version:
        errors.append(f"Invalid schema_version: {schema_version}")

    return errors


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return _basic_schema_validation(data, schema)

    validator = Draft202012Validator(schema)
    errors: List[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda err: list(err.path)):
        path = '.'.join(str(part) for part in error.path)
        if path:
            errors.append(f"{path}: {error.message}")
        else:
            errors.append(error.message)
    return errors


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.

    Example: "Leonardo Fernandes Fraceto" -> "leonardo-fernandes-fraceto"
    """
    # Normalize unicode (NFD decomposition)
    text = unicodedata.normalize('NFD', text)
    # Remove combining marks
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    # Collapse multiple hyphens
    text = re.sub(r'-+', '-', text)
    return text


def extract_lattes_id_from_filename(filename: str) -> Optional[str]:
    """
    Extract Lattes ID from filename.

    Expected pattern: <lattes_id>__<slug>.full_profile.html
    Example: 8657413561406750__leonardo-fernandes-fraceto.full_profile.html

    Returns Lattes ID or None if not found.
    """
    # Pattern: digits followed by __
    match = re.match(r'^(\d+)__', filename)
    if match:
        return match.group(1)
    return None


def extract_researcher_metadata_from_html(html_path: Path) -> Dict[str, Any]:
    """
    Extract researcher metadata from full_profile HTML.

    Extracts:
    - lattes_id (from URL or ID Lattes field)
    - full_name
    - slug (generated from name)

    Returns dict with metadata.
    """
    with open(html_path, 'rb') as f:
        raw_bytes = f.read()
    html = normalize_html_text(raw_bytes)

    soup = BeautifulSoup(html, 'lxml')

    metadata = {
        'lattes_id': None,
        'full_name': None,
        'slug': None,
        'last_update': None
    }

    # Extract Lattes ID from URL
    # Pattern: http://lattes.cnpq.br/NNNNNNNNNNNNNNNN
    url_match = re.search(r'lattes\.cnpq\.br/(\d{16})', html)
    if url_match:
        metadata['lattes_id'] = url_match.group(1)

    # Extract name from h2.nome
    nome_tag = soup.find('h2', class_='nome')
    if nome_tag:
        full_name = nome_tag.get_text(strip=True)
        # Remove "Bolsista de..." suffix if present
        if not full_name.startswith('Bolsista'):
            metadata['full_name'] = full_name
            metadata['slug'] = slugify(full_name)

    # Extract last update date
    # Pattern: "Última atualização do currículo em DD/MM/YYYY"
    update_match = re.search(r'Última atualização do currículo em (\d{2}/\d{2}/\d{4})', html)
    if update_match:
        metadata['last_update'] = update_match.group(1)

    return metadata


def extract_production_sections_from_html(html_path: Path) -> List[Dict[str, Any]]:
    """
    Extract all production sections from full_profile HTML.

    Returns list of dicts with:
    - section_title: Title of production section
    - html_content: HTML content of section
    - item_count: Number of items found
    """
    with open(html_path, 'rb') as f:
        raw_bytes = f.read()
    html = normalize_html_text(raw_bytes)

    soup = BeautifulSoup(html, 'lxml')
    sections = []

    def _count_items(fragment_html: str) -> int:
        fragment_soup = BeautifulSoup(fragment_html, 'lxml')
        return len(fragment_soup.find_all('div', class_='layout-cell-1'))

    def _split_production_subsections(wrapper) -> List[Dict[str, Any]]:
        data_cell = wrapper.find('div', class_='data-cell')
        if not data_cell:
            return []
        children = [child for child in data_cell.children if str(child).strip()]
        subsections: List[Dict[str, Any]] = []
        current_label: Optional[str] = None
        current_nodes: List[Any] = []

        def flush() -> None:
            if not current_label:
                return
            html_fragment = ''.join(str(node) for node in current_nodes)
            item_count = _count_items(html_fragment)
            if item_count == 0:
                return
            subsections.append({
                'section_title': current_label,
                'html_content': html_fragment,
                'item_count': item_count,
            })

        for child in children:
            header_div = None
            if getattr(child, 'name', None) == 'div':
                if 'cita-artigos' in (child.get('class') or []):
                    header_div = child
                else:
                    header_div = child.find('div', class_='cita-artigos')
            if header_div is not None:
                flush()
                current_label = normalize_text(header_div.get_text(' ', strip=True))
                current_nodes = [child]
            else:
                if current_label is not None:
                    current_nodes.append(child)
        flush()
        return subsections

    # Find all title-wrapper divs (these contain production sections)
    title_wrappers = soup.find_all('div', class_='title-wrapper')

    for wrapper in title_wrappers:
        # Find h1 or h2 with section title
        title_tag = wrapper.find(['h1', 'h2'])
        if not title_tag:
            continue

        section_title = normalize_text(title_tag.get_text(strip=True))

        # Skip non-production sections
        skip_sections = [
            'Identificação',
            'Endereço',
            'Formação acadêmica',
            'Formação Complementar',
            'Pós-doutorado',
            'Atuação profissional',
            'Áreas de atuação',
            'Idiomas',
            'Prêmios e títulos'
        ]

        if any(skip in section_title for skip in skip_sections):
            continue

        # Count items in this section (layout-cell-1 divs with numero_item)
        data_cells = wrapper.find_all('div', class_='data-cell')
        item_count = 0
        for cell in data_cells:
            if cell.find('div', class_='layout-cell-1'):
                item_count += 1

        if item_count > 0:
            if section_title == 'Produções':
                subsections = _split_production_subsections(wrapper)
                if subsections:
                    sections.extend(subsections)
                    continue
            sections.append({
                'section_title': section_title,
                'html_content': str(wrapper),
                'item_count': item_count
            })

    return sections


def parse_section_html(
    section_html: str,
    section_title: str,
    temp_dir: Path
) -> Dict[str, Any]:
    """
    Parse a production section HTML using existing parser infrastructure.

    Creates a temporary HTML file and uses parse_fixture() to parse it.
    """
    # Create a temporary HTML file
    temp_filename = f"temp__{slugify(section_title)}.html"
    temp_path = temp_dir / temp_filename

    # Write section HTML to temp file
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(section_html)

    try:
        # Use existing parser
        parsed = parse_fixture(temp_path)
        return parsed
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


def _normalize_section_label(label: Optional[str]) -> str:
    if not label:
        return ''
    return ' '.join(str(label).split())


def _apply_section_label(item: Dict[str, Any], section_label: str) -> None:
    if not section_label:
        return
    current_type = item.get('production_type')
    if current_type not in (None, '') and current_type != section_label:
        if item.get('section') in (None, ''):
            item['section'] = section_label
    else:
        item['production_type'] = section_label


def _apply_source_section_label(source: Dict[str, Any], section_label: str) -> None:
    if not section_label:
        return
    current_type = source.get('production_type')
    if current_type not in (None, '') and current_type != section_label:
        if source.get('section') in (None, ''):
            source['section'] = section_label
    else:
        source['production_type'] = section_label


def add_provenance_to_items(
    items: List[Dict],
    lattes_id: str,
    source_file: str,
    production_type: str,
) -> List[Dict]:
    """
    Add provenance metadata (source.*) to each item without overwriting existing fields.

    Adds:
    - source.file
    - source.lattes_id
    - source.production_type (section title)
    - source.section (optional redundancy if conflict)
    - source.extracted_at
    """
    extracted_at = datetime.now().isoformat()

    for item in items:
        _apply_section_label(item, production_type)
        source = item.get('source') or {}
        if 'file' not in source:
            source['file'] = source_file
        if 'lattes_id' not in source:
            source['lattes_id'] = lattes_id
        _apply_source_section_label(source, production_type)
        if 'extracted_at' not in source:
            source['extracted_at'] = extracted_at
        item['source'] = source

    return items


def _autores_tem_ano(autores: Optional[str]) -> bool:
    if not autores:
        return False
    return re.search(r'(?:\b|\.)\s*(19|20)\d{2}\b', autores) is not None


def _autores_parecem_lista(autores: Optional[str]) -> bool:
    if not autores:
        return False
    if ';' in autores:
        return True
    return re.search(r'\b[A-ZÀ-Ú]{2,},\s*[A-Z]', autores) is not None


def _item_parece_capitulo(raw_text: str) -> bool:
    return 'In:' in (raw_text or '')


def _apply_citacao_fallbacks(items: List[Dict[str, Any]]) -> None:
    for item in items:
        raw_text = item.get('raw') or ''
        autores, titulo, veiculo_ou_livro = split_citacao(raw_text)

        if autores and _autores_parecem_lista(autores):
            if not item.get('autores') or _autores_tem_ano(item.get('autores')):
                item['autores'] = autores

        if titulo and not item.get('titulo'):
            item['titulo'] = titulo

        if veiculo_ou_livro:
            if _item_parece_capitulo(raw_text):
                if not item.get('livro'):
                    item['livro'] = veiculo_ou_livro
            else:
                if not item.get('veiculo'):
                    item['veiculo'] = veiculo_ou_livro


def _infer_year_from_item(item: Dict[str, Any]) -> Optional[int]:
    ano = item.get('ano')
    if isinstance(ano, int):
        return ano
    if isinstance(ano, str) and ano.strip().isdigit():
        return int(ano.strip())

    raw = item.get('raw') or ''
    matches = re.findall(r'\b(?:19|20)\d{2}\b', raw)
    if matches:
        return int(matches[-1])
    return None


def filter_productions_by_year(
    items: List[Dict[str, Any]],
    allowed_years: Optional[Iterable[int]],
) -> List[Dict[str, Any]]:
    if allowed_years is None:
        return list(items)

    allowed_set = {int(year) for year in allowed_years}
    filtered: List[Dict[str, Any]] = []
    for item in items:
        year = _infer_year_from_item(item)
        if year is None:
            continue
        if year in allowed_set:
            filtered.append(item)
    return filtered


def process_researcher_file(
    filepath: Path,
    output_dir: Path,
    schema: Optional[Dict] = None,
    allowed_years: Optional[Iterable[int]] = DEFAULT_ALLOWED_YEARS,
) -> Dict[str, Any]:
    """
    Process a single researcher full_profile HTML.

    Parses all production sections and saves individual researcher JSON.

    Returns:
    {
        'filepath': str,
        'filename': str,
        'lattes_id': str,
        'full_name': str,
        'slug': str,
        'success': bool,
        'sections': List[Dict],  # Parsed production sections
        'total_items': int,
        'schema_errors': List,
        'error': str (if failed),
        'output_json': str (path to saved JSON)
    }
    """
    print(f"  Processing: {filepath.name}...", end=" ")

    result = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'lattes_id': None,
        'full_name': None,
        'slug': None,
        'success': False,
        'sections': [],
        'total_items': 0,
        'schema_errors': [],
        'error': None,
        'output_json': None
    }

    try:
        # Step 1: Extract lattes_id and metadata
        # Priority 1: From filename
        lattes_id_from_filename = extract_lattes_id_from_filename(filepath.name)

        # Fallback: From HTML
        metadata = extract_researcher_metadata_from_html(filepath)

        # Use filename ID if available, otherwise HTML ID
        result['lattes_id'] = lattes_id_from_filename or metadata['lattes_id'] or 'unknown'
        result['full_name'] = metadata['full_name'] or 'Unknown Researcher'
        result['slug'] = metadata['slug'] or slugify(result['full_name'])
        result['last_update'] = metadata.get('last_update')

        # Step 2: Extract production sections
        sections_html = extract_production_sections_from_html(filepath)

        # Step 3: Parse each section
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix='metricas_batch_'))

        try:
            all_productions = []
            sections_metadata = []

            for section in sections_html:
                section_title = section['section_title']
                section_label = _normalize_section_label(section_title)
                if not section_label:
                    section_label = 'Produções'
                    print(f"  ⚠ Section title vazio em {filepath.name}; usando fallback 'Produções'")
                section_html = section['html_content']

                # Parse this section
                parsed = parse_section_html(section_html, section_title, temp_dir)

                # Add provenance to each item
                items_with_provenance = add_provenance_to_items(
                    parsed['items'],
                    result['lattes_id'],
                    filepath.name,
                    section_label
                )

                all_productions.extend(items_with_provenance)

                sections_metadata.append({
                    'section_title': section_title,
                    'item_count': len(items_with_provenance),
                    'tipo_producao': parsed['tipo_producao']
                })
        finally:
            # Clean up temp dir
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)

        _apply_citacao_fallbacks(all_productions)
        all_productions = filter_productions_by_year(all_productions, allowed_years)

        section_counts: Dict[str, int] = {}
        for item in all_productions:
            source = item.get('source') or {}
            section_name = source.get('production_type')
            if section_name:
                section_counts[section_name] = section_counts.get(section_name, 0) + 1

        for section in sections_metadata:
            section_name = section.get('section_title')
            if section_name in section_counts:
                section['item_count'] = section_counts[section_name]
            else:
                section['item_count'] = 0

        result['sections'] = sections_metadata
        result['total_items'] = len(all_productions)

        # Step 4: Create researcher JSON
        researcher_json = {
            'schema_version': '2.0.0',
            'researcher': {
                'lattes_id': result['lattes_id'],
                'full_name': result['full_name'],
                'slug': result['slug'],
                'last_update': result.get('last_update')
            },
            'metadata': {
                'extracted_at': datetime.now().isoformat(),
                'source_file': filepath.name,
                'total_productions': len(all_productions),
                'sections': sections_metadata,
                'filters': {
                    'years': 'all' if allowed_years is None else list(allowed_years)
                },
            },
            'productions': all_productions
        }

        # HTML do Lattes pode conter encoding misto; normalizamos campos textuais
        # preservando o raw para evitar efeitos em fingerprints/forense.
        researcher_json = normalize_nested_text(
            researcher_json,
            exclude_keys={'raw', 'raw_text'}
        )

        schema_errors: List[str] = []
        if schema is not None:
            schema_errors = validate_against_schema(researcher_json, schema)

        # Step 5: Save researcher JSON
        json_filename = f"{result['lattes_id']}__{result['slug']}.json"
        json_path = output_dir / 'researchers' / json_filename

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(researcher_json, f, indent=2, ensure_ascii=False)

        result['output_json'] = str(json_path)
        result['schema_errors'] = schema_errors

        if schema_errors:
            result['success'] = False
            result['error'] = f"Schema validation failed ({len(schema_errors)} errors)"
            print(f"✗ Schema validation failed ({len(schema_errors)} errors)")
        else:
            result['success'] = True
            print(f"✓ OK ({result['lattes_id']}, {result['total_items']} items)")

    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
        print(f"✗ ERROR: {str(e)[:50]}")

    return result


def generate_audit_report(results: List[Dict], output_dir: Path) -> None:
    """Generate markdown audit report."""
    report_path = output_dir / 'audit_report.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Batch Processing Audit Report\n\n")
        f.write(f"**Generated at:** {datetime.now().isoformat()}\n\n")

        # Summary stats
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success
        total_items = sum(r['total_items'] for r in results if r['success'])

        f.write("## Summary\n\n")
        f.write(f"- **Total files processed:** {total}\n")
        f.write(f"- **Successful:** {success}\n")
        f.write(f"- **Failed:** {failed}\n")
        f.write(f"- **Total items extracted:** {total_items}\n\n")

        # Per-researcher details
        f.write("## Researcher Details\n\n")
        f.write("| Lattes ID | Name | Items | Status |\n")
        f.write("|-----------|------|-------|--------|\n")

        for r in results:
            status = "✓ OK" if r['success'] else "✗ FAIL"
            f.write(f"| {r['lattes_id']} | {r['full_name']} | {r['total_items']} | {status} |\n")

        # Errors (if any)
        errors = [r for r in results if not r['success']]
        if errors:
            f.write("\n## Errors\n\n")
            for r in errors:
                f.write(f"### {r['filename']}\n\n")
                f.write(f"```\n{r.get('error', 'Unknown error')}\n```\n\n")

    print(f"✓ Audit report saved: {report_path}")


def parse_years_arg(value: Optional[str]) -> Optional[List[int]]:
    if value is None:
        return list(DEFAULT_ALLOWED_YEARS)
    normalized = value.strip().lower()
    if normalized == 'all':
        return None
    parts = [part.strip() for part in value.split(',') if part.strip()]
    if not parts:
        raise ValueError("Parametro --years invalido: forneca anos ou 'all'")
    years: List[int] = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"Parametro --years invalido: {part}")
        years.append(int(part))
    return years


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch processor for researcher full_profile HTMLs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--in', dest='input_dir', required=True,
        help='Input directory with full_profile HTML files'
    )
    parser.add_argument(
        '--out', dest='output_dir', required=True,
        help='Output directory for JSONs and reports'
    )
    parser.add_argument(
        '--schema', dest='schema_path',
        default='schema/researcher_output.schema.json',
        help='Path to JSON Schema (default: schema/researcher_output.schema.json)'
    )
    parser.add_argument(
        '--years', dest='years',
        default=None,
        help="Filtro de anos (ex: 2024,2025) ou 'all' para desativar"
    )

    args = parser.parse_args()
    try:
        allowed_years = parse_years_arg(args.years)
    except ValueError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1

    # Paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    schema_path = Path(args.schema_path)

    # Validate input
    if not input_dir.exists():
        print(f"✗ Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    # Create output structure
    output_dir.mkdir(parents=True, exist_ok=True)
    researchers_dir = output_dir / 'researchers'
    researchers_dir.mkdir(exist_ok=True)

    # Load schema (optional)
    schema = None
    if schema_path.exists():
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            print(f"✓ Schema loaded: {schema_path}")
        except Exception as e:
            print(f"✗ Error loading schema: {e}", file=sys.stderr)
            return 1
    else:
        print(f"⚠ Schema not found: {schema_path} - skipping validation")

    # Find full_profile HTML files
    html_files = [
        f for f in sorted(input_dir.glob('*.html'))
        if not f.name.startswith('._')
        and 'full_profile' in f.name.lower()
    ]

    if not html_files:
        print(f"✗ No full_profile HTML files found in {input_dir}", file=sys.stderr)
        return 1

    print(f"\nFound {len(html_files)} full_profile HTML files")
    print(f"Output: {output_dir}")
    print()

    # Process files
    results = []
    for filepath in html_files:
        result = process_researcher_file(
            filepath,
            output_dir,
            schema,
            allowed_years=allowed_years,
        )
        results.append(result)

    # Generate summary
    print()
    print("="*60)
    print("SUMMARY")
    print("="*60)

    total = len(results)
    success_count = sum(1 for r in results if r['success'])
    fail_count = total - success_count
    total_items = sum(r['total_items'] for r in results if r['success'])

    print(f"Total files: {total}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total items extracted: {total_items}")

    # Save summary.json
    summary = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'input_dir': str(input_dir),
            'output_dir': str(output_dir),
            'schema_path': str(schema_path) if schema else None,
            'schema_validation': schema is not None
        },
        'summary': {
            'total_files': total,
            'success': success_count,
            'failed': fail_count,
            'total_items': total_items
        },
        'researchers': [
            {
                'lattes_id': r['lattes_id'],
                'full_name': r['full_name'],
                'slug': r['slug'],
                'filename': r['filename'],
                'success': r['success'],
                'total_items': r['total_items']
            }
            for r in results
        ]
    }

    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Summary saved: {summary_path}")

    # Save errors.json (if any)
    errors_report = {
        'metadata': {
            'generated_at': datetime.now().isoformat()
        },
        'errors': [
            {
                'lattes_id': r['lattes_id'],
                'filename': r['filename'],
                'error': r.get('error')
            }
            for r in results
            if not r['success']
        ]
    }

    if errors_report['errors']:
        errors_path = output_dir / 'errors.json'
        with open(errors_path, 'w', encoding='utf-8') as f:
            json.dump(errors_report, f, indent=2, ensure_ascii=False)
        print(f"✓ Errors report saved: {errors_path}")
    else:
        print(f"\n✓ No errors!")

    # Generate audit report
    generate_audit_report(results, output_dir)

    print()
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
