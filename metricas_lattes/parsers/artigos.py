"""Parser for journal articles (Artigos em periódicos)"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .base import ParsedProduction, BaseParser

logger = logging.getLogger(__name__)


@dataclass
class ArtigoProduction(ParsedProduction):
    """Article production with specific fields"""
    autores: Optional[str] = None
    veiculo: Optional[str] = None
    volume: Optional[str] = None
    paginas: Optional[str] = None
    doi: Optional[str] = None
    
    def __post_init__(self):
        self.categoria = "artigo"


class ArtigoParser(BaseParser):
    """Parser for journal articles following ingestao_v2 logic"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
    
    def parse_html(self, html: str) -> List[ArtigoProduction]:
        """Parse articles from Lattes HTML"""
        # Reset errors for each run
        self.errors = []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all article blocks
        artigo_divs = soup.find_all('div', class_='artigo-completo')
        
        results = []
        for idx, div in enumerate(artigo_divs):
            try:
                artigo = self.parse_single_artigo(div)
                if artigo:
                    results.append(artigo)
                else:
                    # None returned - missing structure
                    ordem = None
                    try:
                        ordem = self._extract_ordem_lattes(div)
                    except Exception:
                        pass
                    
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
                logger.debug(f"Failed to parse article at index {idx}, ordem={ordem}: {e}")
                continue
        
        return results
    
    def parse_single_artigo(self, artigo_div) -> Optional[ArtigoProduction]:
        """Parse a single article block"""
        
        # Preserve original HTML
        html_snippet = str(artigo_div)[:500]  # First 500 chars for trace
        
        # 1. Extract ordem_lattes
        ordem_lattes = self._extract_ordem_lattes(artigo_div)
        
        # 2. Extract DOI
        doi = self._extract_doi(artigo_div)
        
        # 3. Extract ano
        ano = self._extract_ano(artigo_div)
        
        # 4. Extract main content text
        main_content = artigo_div.find('div', class_='layout-cell-11')
        if not main_content:
            return None
        
        transform_span = main_content.find('span', class_='transform')
        if not transform_span:
            return None
        
        # Clone and clean
        clone = BeautifulSoup(str(transform_span), 'html.parser')
        
        # Remove unwanted elements
        for selector in ['.informacao-artigo', '.icone-producao', 'sup', 'img', '.citado']:
            for el in clone.select(selector):
                el.decompose()
        
        # Get cleaned text
        texto_completo = self.clean_text(clone.get_text())
        raw_text = texto_completo
        
        # 5. Parse autores
        autores = self._extract_autores(texto_completo)
        if autores:
            # Remove autores from text
            texto_completo = re.sub(r'^.+?\.\s+', '', texto_completo, count=1)
        
        # 6. Parse title and metadata
        titulo, veiculo, volume, paginas = self._extract_metadata(texto_completo)
        
        return ArtigoProduction(
            categoria="artigo",
            titulo=titulo,
            autores=autores,
            ano=ano,
            veiculo=veiculo,
            volume=volume,
            paginas=paginas,
            doi=doi,
            ordem_lattes=ordem_lattes,
            raw_text=raw_text,
            html_snippet=html_snippet
        )
    
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
    
    def _extract_autores(self, texto: str) -> Optional[str]:
        """Extract authors from beginning of text"""
        # Authors are before first " . " followed by uppercase
        match = re.search(r'\s+\.\s+[A-Z]', texto)
        if not match or match.start() <= 0:
            return None
        
        autores_raw = texto[:match.start()]
        
        # Split by semicolon and clean
        autores_list = []
        for autor in autores_raw.split(';'):
            autor = self._normalize_author_name(autor)
            if len(autor) > 2:
                autores_list.append(autor)
        
        return '; '.join(autores_list) if autores_list else None
    
    def _normalize_author_name(self, name: str) -> str:
        """Clean author name"""
        # Remove HTML tags
        name = re.sub(r'<[^>]+>', '', name)
        return self.clean_text(name)
    
    def _extract_metadata(self, texto: str) -> tuple:
        """Extract title, venue, volume, pages from text"""
        titulo = None
        veiculo = None
        volume = None
        paginas = None
        
        # Pattern: TITLE. VENUE, v. VOLUME, p. PAGES
        match = re.search(
            r'^(.+?)\.\s*([^,]+),\s*v\.\s*(\S+),\s*p\.\s*([\d\-—–]+)',
            texto
        )
        
        if match:
            titulo = self.clean_text(match.group(1))
            veiculo = self.clean_text(match.group(2))
            volume = match.group(3).strip()
            paginas = match.group(4).strip()
        else:
            # Fallback: try to extract at least title
            title_match = re.search(r'^(.+?)(?:\.\s+[A-Z]|,\s*v\.)', texto)
            if title_match:
                titulo = self.clean_text(title_match.group(1))
                
                # Try to extract venue
                resto = texto[title_match.end():].strip()
                venue_match = re.search(r'^([^,]+)', resto)
                if venue_match:
                    veiculo = self.clean_text(venue_match.group(1).lstrip('.').strip())
            else:
                # Last resort: first sentence as title
                primeira_frase = texto.split('.')[0] if '.' in texto else texto
                titulo = self.clean_text(primeira_frase)
        
        # Clean HTML entities in venue
        if veiculo:
            veiculo = veiculo.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        
        return titulo, veiculo, volume, paginas