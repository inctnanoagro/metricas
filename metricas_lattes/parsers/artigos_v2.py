"""Parser for journal articles (Artigos em periódicos) - v2"""

import re
import hashlib
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .utils import clean_autores

logger = logging.getLogger(__name__)


class ArtigoParser:
    """Parser for journal articles following ingestao_v2 logic"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse articles from Lattes HTML"""
        # Reset errors for each run
        self.errors = []

        soup = BeautifulSoup(html, 'lxml')

        # Find all article blocks - try both patterns
        artigo_divs = soup.find_all('div', class_='artigo-completo')

        # If no artigo-completo divs, try layout-cell-11 pattern
        if not artigo_divs:
            return self._parse_layout_cell_pattern(soup)

        results = []
        for idx, div in enumerate(artigo_divs):
            try:
                artigo = self.parse_single_artigo(div)
                if artigo:
                    results.append(artigo)
                else:
                    ordem = self._extract_ordem_lattes(div)
                    self.errors.append({
                        'index': idx,
                        'ordem_lattes': ordem,
                        'reason': 'missing_structure'
                    })
            except Exception as e:
                ordem = self._extract_ordem_lattes(div)
                self.errors.append({
                    'index': idx,
                    'ordem_lattes': ordem,
                    'reason': 'exception',
                    'error': str(e)
                })
                logger.debug(f"Failed to parse article at index {idx}: {e}")
                continue

        return results

    def _parse_layout_cell_pattern(self, soup) -> List[Dict[str, Any]]:
        """Parse using layout-cell-1 + layout-cell-11 pattern"""
        results = []
        cell_1_divs = soup.find_all('div', class_='layout-cell-1')

        for idx, cell_1 in enumerate(cell_1_divs):
            try:
                # Find corresponding cell-11
                cell_11 = cell_1.find_next_sibling('div', class_='layout-cell-11')
                if not cell_11:
                    continue

                # Extract numero
                numero = self._extract_numero_from_cell1(cell_1)
                if numero is None:
                    continue

                # Extract content
                transform_span = cell_11.find('span', class_='transform')
                if not transform_span:
                    continue

                artigo = self._parse_from_span(transform_span, numero, cell_11)
                if artigo:
                    results.append(artigo)

            except Exception as e:
                logger.debug(f"Failed to parse article at index {idx}: {e}")
                continue

        return results

    def _extract_numero_from_cell1(self, cell_1) -> Optional[int]:
        """Extract item number from layout-cell-1"""
        b_tag = cell_1.find('b')
        if not b_tag:
            return None

        match = re.search(r'(\d+)', b_tag.get_text())
        if match:
            return int(match.group(1))
        return None

    def _parse_from_span(self, transform_span, numero_item: int, parent_div) -> Optional[Dict[str, Any]]:
        """Parse article from transform span"""
        # Get raw text
        raw_text = self.clean_text(transform_span.get_text(separator=' '))

        if not raw_text:
            return None

        # Extract DOI from parent
        doi = self._extract_doi_from_parent(parent_div)

        # Extract autores
        autores = self._extract_autores(raw_text)

        # Extract ano
        ano = self._extract_ano_from_text(raw_text)

        # Extract metadata
        titulo, veiculo, volume, paginas = self._extract_metadata(raw_text, autores)

        # Compute fingerprint
        fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()

        return {
            'numero_item': numero_item,
            'raw': raw_text,
            'autores': autores,
            'titulo': titulo,
            'ano': ano,
            'veiculo': veiculo,
            'volume': volume,
            'paginas': paginas,
            'doi': doi,
            'fingerprint_sha1': fingerprint,
            'html_snippet': str(parent_div)[:500]
        }

    def parse_single_artigo(self, artigo_div) -> Optional[Dict[str, Any]]:
        """Parse a single article block (artigo-completo pattern)"""

        # 1. Extract ordem_lattes
        ordem_lattes = self._extract_ordem_lattes(artigo_div)
        if ordem_lattes is None:
            return None

        # 2. Extract DOI
        doi = self._extract_doi(artigo_div)

        # 3. Extract ano from data attribute
        ano = self._extract_ano(artigo_div)

        # 4. Extract main content text
        main_content = artigo_div.find('div', class_='layout-cell-11')
        if not main_content:
            return None

        transform_span = main_content.find('span', class_='transform')
        if not transform_span:
            return None

        # Get cleaned text
        texto_completo = self.clean_text(transform_span.get_text(separator=' '))
        raw_text = texto_completo

        # 5. Parse autores
        autores = self._extract_autores(texto_completo)

        # 6. Parse title and metadata
        titulo, veiculo, volume, paginas = self._extract_metadata(texto_completo, autores)

        # Compute fingerprint
        fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()

        return {
            'numero_item': ordem_lattes,
            'raw': raw_text,
            'autores': autores,
            'titulo': titulo,
            'ano': ano,
            'veiculo': veiculo,
            'volume': volume,
            'paginas': paginas,
            'doi': doi,
            'fingerprint_sha1': fingerprint,
            'html_snippet': str(artigo_div)[:500]
        }

    def _extract_ordem_lattes(self, div) -> Optional[int]:
        """Extract Lattes numbering from layout-cell-1"""
        cell_1 = div.find('div', class_='layout-cell-1')
        if not cell_1:
            return None

        b_tag = cell_1.find('b')
        if not b_tag:
            return None

        match = re.search(r'(\d+)', b_tag.get_text())
        if match:
            return int(match.group(1))
        return None

    def _extract_doi(self, div) -> Optional[str]:
        """Extract DOI from icone-doi link"""
        doi_link = div.find('a', class_='icone-doi')
        if not doi_link or not doi_link.get('href'):
            return None

        href = doi_link['href']
        # Remove prefix
        doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', href)
        return doi.strip() if doi else None

    def _extract_doi_from_parent(self, div) -> Optional[str]:
        """Extract DOI from parent div"""
        return self._extract_doi(div)

    def _extract_ano(self, div) -> Optional[int]:
        """Extract year from data-tipo-ordenacao span"""
        ano_span = div.find('span', {'data-tipo-ordenacao': 'ano'})
        if not ano_span:
            return None

        ano_text = ano_span.get_text().strip()
        match = re.search(r'(\d{4})', ano_text)
        if match:
            return int(match.group(1))
        return None

    def _extract_ano_from_text(self, text: str) -> Optional[int]:
        """Extract year from text using heuristic"""
        matches = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        if matches:
            return int(matches[-1])
        return None

    def _extract_autores(self, texto: str) -> Optional[str]:
        """Extract authors from beginning of text"""
        # Authors are before first " . " followed by uppercase
        match = re.search(r'^(.+?)\s+\.\s+[A-ZÀ-Ú]', texto)
        if not match or match.start() < 0:
            return None

        autores_raw = match.group(1)

        # Split by semicolon and clean
        autores_list = []
        for autor in autores_raw.split(';'):
            autor_clean = self._normalize_author_name(autor)
            if len(autor_clean) > 2:
                autores_list.append(autor_clean)

        cleaned = '; '.join(autores_list) if autores_list else None
        return clean_autores(cleaned) if cleaned else None

    def _normalize_author_name(self, name: str) -> str:
        """Clean author name"""
        # Remove HTML tags
        name = re.sub(r'<[^>]+>', '', name)
        return clean_autores(self.clean_text(name))

    def _extract_metadata(self, texto: str, autores: Optional[str]) -> tuple:
        """Extract title, venue, volume, pages from text"""
        titulo = None
        veiculo = None
        volume = None
        paginas = None

        # STRUCTURAL DELIMITER: Authors end with " . " (space-dot-space)
        # Find this delimiter to locate where title begins
        texto_sem_autores = texto

        # Find " . " delimiter (space-dot-space) - this separates authors from title
        match = re.search(r'\s+\.\s+', texto)
        if match:
            # Skip past the delimiter to get text after authors
            texto_sem_autores = texto[match.end():]
        elif autores:
            # Fallback: if we extracted autores, try to skip past it
            # This handles edge cases where the pattern might be slightly different
            try:
                # Autores are at the beginning, find where they end
                # Look for the transition from author names to title (uppercase letter after period)
                fallback_match = re.search(r'^\S.*?\s+\.\s+([A-ZÀ-Ú])', texto)
                if fallback_match:
                    # Start from the uppercase letter (beginning of title)
                    texto_sem_autores = texto[fallback_match.start(1):]
            except:
                pass

        # Pattern: TITLE. VENUE, v. VOLUME, p. PAGES
        match = re.search(
            r'^(.+?)\.\s*([^,]+),\s*v\.\s*(\S+),\s*p\.\s*([\d\-—–]+)',
            texto_sem_autores
        )

        if match:
            titulo = self.clean_text(match.group(1))
            veiculo = self.clean_text(match.group(2))
            volume = match.group(3).strip()
            paginas = match.group(4).strip()
        else:
            # Fallback: try to extract at least title
            title_match = re.search(r'^(.+?)(?:\.\s+[A-ZÀ-Ú]|,\s*v\.|\.\s*$)', texto_sem_autores)
            if title_match:
                titulo = self.clean_text(title_match.group(1))

                # Try to extract venue
                resto = texto_sem_autores[title_match.end():].strip()
                venue_match = re.search(r'^\.?\s*([^,]+)', resto)
                if venue_match:
                    veiculo = self.clean_text(venue_match.group(1).lstrip('.').strip())
            else:
                # Last resort: first sentence as title
                primeira_frase = texto_sem_autores.split('.')[0] if '.' in texto_sem_autores else texto_sem_autores
                titulo = self.clean_text(primeira_frase)

        # Clean HTML entities in venue
        if veiculo:
            veiculo = veiculo.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

        return titulo, veiculo, volume, paginas

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize text (whitespace, non-breaking spaces)"""
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
