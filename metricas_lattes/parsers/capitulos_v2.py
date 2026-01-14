"""Parser for book chapters (Capítulos de livros) - v2"""

import re
import hashlib
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CapituloParser:
    """Parser for book chapters following ingestao_v4 logic"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse book chapters from Lattes HTML"""
        # Reset errors for each run
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

                # Check if it looks like a chapter
                texto = self.clean_text(transform_span.get_text())
                if 'In:' not in texto or '(Org.)' not in texto:
                    continue

                capitulo = self._parse_capitulo(transform_span, numero, cell_11)
                if capitulo:
                    results.append(capitulo)

            except Exception as e:
                logger.debug(f"Failed to parse chapter at index {idx}: {e}")
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

    def _parse_capitulo(self, transform_span, numero_item: int, parent_div) -> Optional[Dict[str, Any]]:
        """Parse a single book chapter"""
        # Get text
        texto = self.clean_text(transform_span.get_text())
        raw_text = texto

        # Extract DOI
        doi = self._extract_doi(parent_div)

        # Extract ISBN
        isbn = self._extract_isbn(texto)

        # Extract autores
        autores = self._extract_autores(texto)

        # Extract titulo
        titulo = self._extract_titulo(texto)

        # Extract livro and edicao
        livro, edicao = self._extract_livro_edicao(texto)

        # Extract editora
        editora = self._extract_editora(texto)

        # Extract ano
        ano = self._extract_ano(texto)

        # Extract paginas
        paginas = self._extract_paginas(texto)

        # Compute fingerprint
        fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()

        return {
            'numero_item': numero_item,
            'raw': raw_text,
            'autores': autores,
            'titulo': titulo,
            'ano': ano,
            'livro': livro,
            'editora': editora,
            'edicao': edicao,
            'paginas': paginas,
            'isbn': isbn,
            'doi': doi,
            'fingerprint_sha1': fingerprint,
            'html_snippet': str(parent_div)[:500]
        }

    def _extract_doi(self, div) -> Optional[str]:
        """Extract DOI from icone-doi link"""
        doi_link = div.find('a', class_='icone-doi')
        if not doi_link or not doi_link.get('href'):
            return None

        href = doi_link['href']
        match = re.search(r'10\.\d+/[^\s]+', href)
        if match:
            return match.group(0)
        return None

    def _extract_isbn(self, texto: str) -> Optional[str]:
        """Extract ISBN from text"""
        match = re.search(r'ISBN[:\s]*([\d\-]+)', texto, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_autores(self, texto: str) -> Optional[str]:
        """Extract authors before title and 'In:'"""
        # Pattern: AUTORES. TITULO. In:
        match = re.search(r'^(.+?)\.\s+[^.]+\.\s+In:', texto)
        if match:
            autores_raw = match.group(1).strip()
            # Clean and normalize
            autores_list = []
            for autor in autores_raw.split(';'):
                autor = self.clean_text(autor)
                if len(autor) > 2:
                    autores_list.append(autor)
            return '; '.join(autores_list) if autores_list else None
        return None

    def _extract_titulo(self, texto: str) -> Optional[str]:
        """Extract chapter title"""
        # Pattern: AUTORES. TITULO. In:
        match = re.search(r'\.\s+([^.]+)\.\s+In:', texto)
        if match:
            return self.clean_text(match.group(1))
        return None

    def _extract_livro_edicao(self, texto: str) -> tuple:
        """Extract book name and edition"""
        # Pattern: (Org.). LIVRO. NEDed
        match = re.search(r'\(Org\.\)\.\s+([^.]+)\.\s+(\d+)ed', texto)
        if match:
            livro = self.clean_text(match.group(1))
            edicao = match.group(2)
            return livro, edicao

        # Try without edition number
        match = re.search(r'\(Org\.\)\.\s+([^.]+)\.', texto)
        if match:
            livro = self.clean_text(match.group(1))
            return livro, None

        return None, None

    def _extract_editora(self, texto: str) -> Optional[str]:
        """Extract publisher"""
        # Pattern: : EDITORA, YEAR
        match = re.search(r':\s+([^,]+),\s+\d{4}', texto)
        if match:
            return self.clean_text(match.group(1))
        return None

    def _extract_ano(self, texto: str) -> Optional[int]:
        """Extract year"""
        # Pattern: , YEAR,
        match = re.search(r',\s+(\d{4}),', texto)
        if match:
            return int(match.group(1))
        return None

    def _extract_paginas(self, texto: str) -> Optional[str]:
        """Extract pages"""
        # Pattern: p. PAGES
        match = re.search(r'p\.\s+([\d\-—–]+)', texto)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize text (whitespace, non-breaking spaces)"""
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
