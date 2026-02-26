"""Parser for newspaper/magazine texts (Textos em jornais de notícias/revistas)"""

import re
import hashlib
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TextoJornalParser:
    """
    Parser for newspaper/magazine articles.

    Uses robust parsing strategy to avoid confusion with author initials:
    1. Split on literal " . " (space-dot-space) to separate authors from content
    2. Extract title from first sentence
    3. Parse veiculo from content before first comma
    """

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse newspaper texts from Lattes HTML"""
        self.errors = []

        soup = BeautifulSoup(html, 'lxml')

        results = []
        cell_1_divs = soup.find_all('div', class_='layout-cell-1')

        for idx, cell_1 in enumerate(cell_1_divs):
            try:
                # Find corresponding cell-11
                cell_11 = cell_1.find_next_sibling('div', class_='layout-cell-11')
                if not cell_11:
                    continue

                # Extract numero
                numero = self._extract_numero(cell_1)
                if numero is None:
                    continue

                # Extract content
                transform_span = cell_11.find('span', class_='transform')
                if not transform_span:
                    continue

                item = self._parse_item(transform_span, numero, cell_11)
                if item:
                    results.append(item)

            except Exception as e:
                logger.debug(f"Failed to parse text at index {idx}: {e}")
                self.errors.append({
                    'index': idx,
                    'reason': 'exception',
                    'error': str(e)
                })
                continue

        return results

    def _extract_numero(self, cell_1) -> Optional[int]:
        """Extract item number from layout-cell-1"""
        b_tag = cell_1.find('b')
        if not b_tag:
            return None

        match = re.search(r'(\d+)', b_tag.get_text())
        if match:
            return int(match.group(1))
        return None

    def _parse_item(self, transform_span, numero_item: int, parent_div) -> Optional[Dict[str, Any]]:
        """Parse a single newspaper text item using robust strategy"""
        # Get raw text and normalize whitespace
        raw_text = self.clean_text(transform_span.get_text())

        if not raw_text:
            return None

        # ROBUST PARSING STRATEGY:
        # Prefer " . " (space-dot-space) to avoid author initials confusion.
        # Fallback to ". " when the prefix looks like a valid author block.
        autores_raw, remainder = self._split_authors_and_remainder(raw_text)
        if not autores_raw or not remainder:
            # Malformed: no separator found
            # Extract what we can
            ano, mes = self._extract_data(raw_text)
            fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()

            return {
                'numero_item': numero_item,
                'raw': raw_text,
                'autores': None,
                'titulo': None,
                'veiculo': None,
                'local': None,
                'paginas': None,
                'ano': ano,
                'mes': mes,
                'fingerprint_sha1': fingerprint,
                'html_snippet': str(parent_div)[:500]
            }

        # Extract autores
        autores = self._normalize_autores(autores_raw)

        # Extract titulo (first sentence from remainder)
        titulo = self._extract_titulo_from_remainder(remainder)

        # Extract veiculo (after title, before first comma)
        veiculo = self._extract_veiculo_from_remainder(remainder)

        # Extract other fields
        local = self._extract_local(remainder)
        paginas = self._extract_paginas(remainder)
        ano, mes = self._extract_data(remainder)

        # Compute fingerprint
        fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()

        return {
            'numero_item': numero_item,
            'raw': raw_text,
            'autores': autores,
            'titulo': titulo,
            'veiculo': veiculo,
            'local': local,
            'paginas': paginas,
            'ano': ano,
            'mes': mes,
            'fingerprint_sha1': fingerprint,
            'html_snippet': str(parent_div)[:500]
        }

    def _split_authors_and_remainder(self, raw_text: str) -> tuple:
        if ' . ' in raw_text:
            parts = raw_text.split(' . ', 1)
            return parts[0].strip(), parts[1].strip()

        match = re.search(r'^(.+?)\.\s+(.+)$', raw_text)
        if match:
            autores_raw = self.clean_text(match.group(1))
            remainder = self.clean_text(match.group(2))
            if self._looks_like_author_block(autores_raw):
                return autores_raw, remainder

        return None, None

    @staticmethod
    def _looks_like_author_block(text: str) -> bool:
        if not text:
            return False
        if ';' in text:
            return True
        return re.search(r'\b[A-ZÀ-Ú]{2,},\s*[A-Z]', text) is not None

    def _normalize_autores(self, autores_raw: str) -> Optional[str]:
        """Normalize author names"""
        if not autores_raw:
            return None

        # Split by semicolon and clean
        autores_list = []
        for autor in autores_raw.split(';'):
            autor_clean = self.clean_text(autor)
            if len(autor_clean) > 2:
                autores_list.append(autor_clean)

        return '; '.join(autores_list) if autores_list else None

    def _extract_titulo_from_remainder(self, remainder: str) -> Optional[str]:
        """Extract title from remainder (first sentence before next period)"""
        # Title is before the next period
        match = re.search(r'^([^.]+)\.', remainder)
        if match:
            return self.clean_text(match.group(1))

        # Fallback: take everything up to first comma
        if ',' in remainder:
            return self.clean_text(remainder.split(',')[0])

        return None

    def _extract_veiculo_from_remainder(self, remainder: str) -> Optional[str]:
        """
        Extract veiculo (newspaper/magazine name) from remainder.

        Strategy: After title period, take text up to first comma.
        """
        # Skip first sentence (title)
        match = re.search(r'^[^.]+\.\s+([^,]+)', remainder)
        if match:
            candidate = self.clean_text(match.group(1))
            # Make sure it's not a date or page number
            if not re.search(r'\d{4}', candidate) and not candidate.startswith('p'):
                return candidate

        return None

    def _extract_local(self, texto: str) -> Optional[str]:
        """Extract publication location/city"""
        # Pattern: VEICULO, LOCATION, p. PAGES
        match = re.search(r',\s+([^,]+),\s+p\.', texto)
        if match:
            candidate = self.clean_text(match.group(1))
            # Make sure it's not a date
            if not re.search(r'\d{4}', candidate) and not re.search(r'(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)', candidate, re.IGNORECASE):
                return candidate

        return None

    def _extract_paginas(self, texto: str) -> Optional[str]:
        """Extract page numbers"""
        # Pattern: p. PAGES
        match = re.search(r'p\.\s+([\w\d\-—–\s]+?)(?:,|\.|$)', texto)
        if match:
            return self.clean_text(match.group(1))

        return None

    def _extract_data(self, texto: str) -> tuple:
        """Extract year and month"""
        # Pattern: DD mes. YYYY or just mes. YYYY
        match = re.search(r'(\d{1,2}\s+)?(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.\s+(\d{4})', texto, re.IGNORECASE)
        if match:
            mes = match.group(2).lower()
            ano = int(match.group(3))
            return ano, mes

        # Fallback: just year
        matches = re.findall(r'\b(19\d{2}|20\d{2})\b', texto)
        if matches:
            return int(matches[-1]), None

        return None, None

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize text (whitespace, non-breaking spaces)"""
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
