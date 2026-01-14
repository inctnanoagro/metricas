from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

@dataclass
class ParsedProduction:
    """Base production with traceability"""
    categoria: str
    titulo: Optional[str]
    ano: Optional[int]
    ordem_lattes: Optional[int]
    raw_text: str                      # For audit trail
    html_snippet: str                  # Original HTML segment
    
    def to_dict(self) -> Dict[str, Any]:
        """Export without traceability fields"""
        pass

class BaseParser(ABC):
    @abstractmethod
    def parse_html(self, html: str) -> List[ParsedProduction]:
        """Parse Lattes HTML and return structured productions"""
        pass
    
    def extract_ordem_lattes(self, element) -> Optional[int]:
        """Extract Lattes numbering from element"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Normalize text (whitespace, entities)"""
        pass