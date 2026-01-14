"""Parser utilities for text normalization."""

from __future__ import annotations

import re
from html import unescape


def clean_autores(raw_autores: str) -> str:
    """Clean author string, removing year artifacts and extra whitespace."""
    if not raw_autores:
        return ''

    text = unescape(raw_autores)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\xa0', ' ')

    # Remove year tokens and glued year artifacts
    text = re.sub(r'([A-Z]\.)\s*(19\d{2}|20\d{2})', r'\1', text)
    text = re.sub(r'\b(19\d{2}|20\d{2})\b', '', text)
    text = re.sub(r'(\b[A-Z]{2,},\s*[A-Z]\.)\s*(19\d{2}|20\d{2})\s*\1', r'\1', text)

    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*;\s*', '; ', text)
    return text.strip(' ;')
