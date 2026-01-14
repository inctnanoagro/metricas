"""
Router for parsing Lattes HTML fixtures by production type.

This module provides a unified entry point for parsing different types
of Lattes productions, with automatic routing based on filename.
"""

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from .parsers.artigos_v2 import ArtigoParser
from .parsers.capitulos_v2 import CapituloParser
from .parsers.textos_jornais import TextoJornalParser


class GenericParser:
    """
    Generic fallback parser for any Lattes production type.

    Extracts minimal guaranteed fields:
    - numero_item (ordinal number)
    - raw (text content)
    - autores (heuristic extraction)
    - ano (heuristic extraction)
    """

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse generic Lattes HTML structure"""
        soup = BeautifulSoup(html, 'lxml')

        # Find all numbered items using layout-cell-1 + layout-cell-11 pattern
        items = []

        # Find all layout-cell-1 divs (containing numbering)
        cell_1_divs = soup.find_all('div', class_='layout-cell-1')

        for cell_1 in cell_1_divs:
            try:
                # Extract number
                numero_item = self._extract_numero(cell_1)
                if numero_item is None:
                    continue

                # Find corresponding layout-cell-11 (next sibling)
                cell_11 = cell_1.find_next_sibling('div', class_='layout-cell-11')
                if not cell_11:
                    continue

                # Extract transform span
                transform_span = cell_11.find('span', class_='transform')
                if not transform_span:
                    continue

                # Get raw text
                raw_text = self._clean_text(transform_span.get_text(separator=' '))

                # Heuristic extractions
                autores = self._extract_autores_heuristic(transform_span)
                titulo = self._extract_titulo_heuristic(raw_text, autores)
                ano = self._extract_ano_heuristic(raw_text)
                mes = self._extract_mes_heuristic(raw_text)
                doi = self._extract_doi_heuristic(cell_11)

                # Compute fingerprint
                fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()

                item = {
                    'numero_item': numero_item,
                    'raw': raw_text,
                    'autores': autores,
                    'titulo': titulo,
                    'ano': ano,
                    'mes': mes,
                    'doi': doi,
                    'fingerprint_sha1': fingerprint,
                    'html_snippet': str(cell_11)[:500]
                }

                items.append(item)

            except Exception as e:
                # Skip problematic items but continue
                continue

        return items

    def _extract_numero(self, cell_1) -> Optional[int]:
        """Extract item number from layout-cell-1"""
        b_tag = cell_1.find('b')
        if not b_tag:
            return None

        match = re.search(r'(\d+)', b_tag.get_text())
        if match:
            return int(match.group(1))
        return None

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace and remove non-breaking spaces"""
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([A-Z]\.)\s*(\d{4})([A-Z]{2,},)', r'\1 \2 \3', text)
        text = re.sub(r'(\b[A-Z]{2,},\s*[A-Z]\.)\s*(\d{4})\s*\1', r'\1 \2', text)
        return text.strip()

    def _extract_autores_heuristic(self, transform_span) -> Optional[str]:
        """
        Extract authors using heuristic: look for names with links or bold tags.
        Authors usually appear at the beginning, separated by semicolons.
        """
        # Get text before first sentence ending
        full_text = self._clean_text(transform_span.get_text(separator=' '))

        # Try to find author pattern: ends with " . " followed by uppercase
        match = re.search(r'^(.+?)\s+\.\s+[A-ZÀ-Ú]', full_text)
        if match:
            autores_raw = match.group(1)

            # Clean up
            autores_list = []
            for autor in autores_raw.split(';'):
                autor_clean = re.sub(r'<[^>]+>', '', autor)  # Remove HTML tags
                autor_clean = self._clean_text(autor_clean)
                if len(autor_clean) > 2:
                    autores_list.append(autor_clean)

            if autores_list:
                return '; '.join(autores_list)

        return None

    def _extract_titulo_heuristic(self, text: str, autores: Optional[str]) -> Optional[str]:
        """
        Extract title using structural delimiter heuristic.

        STRUCTURAL RULE: Authors end with " . " (space-dot-space).
        Title is the text between this delimiter and the next period.

        This prevents author names from leaking into the title field.
        """
        # STRUCTURAL DELIMITER: " . " separates authors from title
        # Find this delimiter to locate where title begins
        match = re.search(r'\s+\.\s+', text)
        if match:
            # Skip past the delimiter to get text after authors
            texto_sem_autores = text[match.end():]

            # Extract title: text up to next period
            title_match = re.search(r'^([^.]+)\.', texto_sem_autores)
            if title_match:
                titulo = self._clean_text(title_match.group(1))
                # Make sure it's not too short (avoid extracting noise)
                if len(titulo) > 10:
                    return titulo

        return None

    def _extract_ano_heuristic(self, text: str) -> Optional[int]:
        """Extract year using heuristic patterns"""
        # Look for 4-digit year
        matches = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        if matches:
            # Return the last year found (usually publication year)
            return int(matches[-1])
        return None

    def _extract_mes_heuristic(self, text: str) -> Optional[str]:
        """Extract month abbreviation if present"""
        meses = [
            r'jan\.', r'fev\.', r'mar\.', r'abr\.', r'mai\.', r'jun\.',
            r'jul\.', r'ago\.', r'set\.', r'out\.', r'nov\.', r'dez\.'
        ]

        for mes in meses:
            if re.search(mes, text, re.IGNORECASE):
                return mes.replace(r'\.', '')

        return None

    def _extract_doi_heuristic(self, cell_div) -> Optional[str]:
        """Extract DOI from icone-doi link if present"""
        doi_link = cell_div.find('a', class_='icone-doi')
        if not doi_link or not doi_link.get('href'):
            return None

        href = doi_link['href']
        # Remove URL prefix to get clean DOI
        doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', href)
        return doi.strip() if doi else None


# Parser registry mapping filename patterns to parser classes
# Keys should be normalized (no accents, lowercase, etc) to match normalize_filename() output
PARSER_REGISTRY: Dict[str, Callable] = {
    'artigos completos publicados em periodicos': ArtigoParser,
    'artigos aceitos para publicacao': ArtigoParser,
    'capitulos de livros publicados': CapituloParser,
    'textos em jornais de noticias revistas': TextoJornalParser,
    # More specific parsers will be added here
}


def normalize_filename(filename: str) -> str:
    """
    Normalize filename for matching against registry.

    Removes file extension, converts to lowercase, removes accents and diacritics.
    """
    # Remove extension
    name = Path(filename).stem

    # Convert to lowercase
    name = name.lower()

    # Remove accents and diacritics (NFD normalization + filter)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')

    # Normalize common variations
    name = name.replace('_', ' ')
    name = name.replace(':', ' ')

    # Normalize multiple spaces to single space
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def get_parser_for_file(filepath: Path) -> Any:
    """
    Get appropriate parser for a given file.

    Returns specific parser if registered, otherwise GenericParser.
    """
    normalized_name = normalize_filename(filepath.name)

    # Check registry
    for pattern, parser_class in PARSER_REGISTRY.items():
        if pattern in normalized_name:
            return parser_class()

    # Fallback to generic parser
    return GenericParser()


def parse_fixture(filepath: Path) -> Dict[str, Any]:
    """
    Main entry point for parsing a Lattes HTML fixture.

    Args:
        filepath: Path to HTML fixture file

    Returns:
        Dictionary conforming to producoes.schema.json v2

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Fixture not found: {filepath}")

    # Read HTML
    html_content = filepath.read_text(encoding='utf-8')

    if not html_content.strip():
        raise ValueError(f"Empty file: {filepath}")

    # Get appropriate parser
    parser = get_parser_for_file(filepath)

    # Parse items
    items = parser.parse_html(html_content)

    # Get tipo_producao from filename
    tipo_producao = Path(filepath).stem

    # Build result conforming to schema
    result = {
        'schema_version': '2.0.0',
        'tipo_producao': tipo_producao,
        'source_file': filepath.name,
        'extraction_timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'items': items,
        'parse_metadata': {
            'parser_version': '1.0.0',
            'total_items': len(items),
            'parse_errors': 0,
            'warnings': []
        }
    }

    # Add error tracking if parser supports it
    if hasattr(parser, 'errors') and parser.errors:
        result['parse_metadata']['parse_errors'] = len(parser.errors)
        result['parse_metadata']['warnings'] = [
            f"Item {err.get('ordem_lattes', err.get('index'))}: {err.get('reason', 'unknown')}"
            for err in parser.errors[:10]  # Limit warnings
        ]

    return result
