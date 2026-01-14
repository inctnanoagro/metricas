"""Base classes for Lattes parsers"""

import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class ParsedProduction:
    """Base production with traceability"""
    categoria: str
    titulo: Optional[str]
    ano: Optional[int]
    ordem_lattes: Optional[int]
    raw_text: str
    html_snippet: str
    
    def to_dict(self, include_trace: bool = False) -> Dict[str, Any]:
        """Export to dict, optionally excluding traceability fields"""
        d = asdict(self)
        if not include_trace:
            d.pop('raw_text', None)
            d.pop('html_snippet', None)
        return {k: v for k, v in d.items() if v is not None}


class BaseParser(ABC):
    """Abstract base parser for Lattes productions"""
    
    @abstractmethod
    def parse_html(self, html: str) -> list:
        """Parse Lattes HTML and return structured productions"""
        pass
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize text (whitespace, non-breaking spaces)"""
        text = text.replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()