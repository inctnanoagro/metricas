"""Parser for book chapters (Capítulos de livros)"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .base import ParsedProduction, BaseParser

logger = logging.getLogger(__name__)


@dataclass
class CapituloProduction(ParsedProduction):
    """Book chapter production with specific fields"""
    autores: Optional[str] = None
    livro: Optional[str] = None
    editora: Optional[str] = None
    edicao: Optional[str] = None
    paginas: Optional[str] = None
    isbn: Optional[str] = None
    doi: Optional[str] = None
    
    def __post_init__(self):
        self.categoria = "capitulo"


class CapituloParser(BaseParser):
    """Parser for book chapters following ingestao_v4 logic"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
    
    def parse_html(self, html: str) -> List[CapituloProduction]:
        """Parse book chapters from Lattes HTML"""
        # Reset errors for each run
        self.errors = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all layout-cell-11 elements (chapters use this, not artigo-completo)
        celulas = soup.find_all('div', class_='layout-cell-11')
        
        results = []
        for idx, div in enumerate(celulas):
            try:
                capitulo = self.parse_single_capitulo(div)
                if capitulo:
                    results.append(capitulo)
                else:
                    # None returned - missing structure or not a chapter
                    ordem = None
                    try:
                        ordem = self._extract_ordem_lattes(div)
                    except Exception:
                        pass
                    
                    # Only log as error if it looks like a chapter (has "In:" and "(Org.)")
                    transform_span = div.find('span', class_='transform')
                    if transform_span:
                        texto = transform_span.get_text()
                        if 'In:' in texto and '(Org.)' in texto:
                            error_info = {
                                'index': idx,
                                'ordem_lattes': ordem,
                                'reason': 'missing_structure',
                                'html_snippet': str(div)[:500]
                            }
                            self.errors.append(error_info)
                            logger.debug(f"Missing structure at index {idx}, ordem={ordem}")
            except Exception as e:
                # Exception during parsing
                ordem = None
                try:
                    ordem = self._extract_ordem_lattes(div)
                except Exception:
                    pass
                
                error_info = {
                    'index': idx,
                    'ordem_lattes': ordem,
                    'reason': 'exception',
                    'error': str(e),
                    'html_snippet': str(div)[:500]
                }
                self.errors.append(error_info)
                logger.debug(f"Failed to parse chapter at index {idx}, ordem={ordem}: {e}")
                continue
        
        return results
    
    def parse_single_capitulo(self, div) -> Optional[CapituloProduction]:
        """Parse a single book chapter"""
        
        # Preserve original HTML
        html_snippet = str(div)[:500]
        
        # Get transform span
        transform_span = div.find('span', class_='transform')
        if not transform_span:
            return None
        
        # Get text
        texto = self.clean_text(transform_span.get_text())
        
        # Must contain both "In:" and "(Org.)" to be a chapter
        if 'In:' not in texto or '(Org.)' not in texto:
            return None
        
        raw_text = texto
        
        # Extract ordem_lattes from parent structure
        ordem_lattes = self._extract_ordem_lattes(div)
        
        # Extract DOI
        doi = self._extract_doi(div)
        
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
        
        return CapituloProduction(
            categoria="capitulo",
            titulo=titulo,
            autores=autores,
            ano=ano,
            livro=livro,
            editora=editora,
            edicao=edicao,
            paginas=paginas,
            isbn=isbn,
            doi=doi,
            ordem_lattes=ordem_lattes,
            raw_text=raw_text,
            html_snippet=html_snippet
        )
    
    def _extract_ordem_lattes(self, div) -> Optional[int]:
        """Extract Lattes numbering from parent structure"""
        # Look for parent with layout-cell-1
        parent = div.parent
        if parent:
            cell_1 = parent.find('div', class_='layout-cell-1')
            if cell_1:
                b_tag = cell_1.find('b')
                if b_tag:
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