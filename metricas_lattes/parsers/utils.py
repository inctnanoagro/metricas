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


def split_citacao(raw: str) -> tuple[str, str, str]:
    """
    Split a citation string into autores, titulo, and veiculo/livro using " . " delimiters.

    Never raises exceptions; always returns strings (possibly empty).
    """
    try:
        if not raw:
            return '', '', ''

        raw_text = str(raw)
        parts = [part.strip() for part in raw_text.split(' . ') if part.strip()]
        autores_raw = parts[0] if len(parts) >= 1 else ''
        titulo_raw = parts[1] if len(parts) >= 2 else ''
        resto_raw = ' . '.join(parts[2:]).strip() if len(parts) >= 3 else ''

        if len(parts) == 1 and raw_text:
            match = re.search(r'^(.+?)\.\s+[A-ZÀ-Ú]{2,}', raw_text)
            if match:
                autores_raw = match.group(1).strip()

        autores = autores_raw
        if autores:
            autores = autores.replace(' ; ', '; ')
            autores = re.sub(r'([A-Z]\.)\s*(19\d{2}|20\d{2})', r'\1', autores)
            autores = re.sub(r'(?<=\s)\b(19\d{2}|20\d{2})\b(?=\s*(?:;|,|$))', '', autores)
            autores = re.sub(r'\s+', ' ', autores).strip()
            autores = autores.rstrip('.').strip()

        titulo = ''
        if titulo_raw:
            titulo = titulo_raw.strip().strip('.')
        else:
            match = re.search(r'\s\.\s(.*?)\s\.\s', str(raw))
            if match:
                titulo = match.group(1).strip().strip('.')
            else:
                for match in re.finditer(r'\.\s+([^.]+?)\.', str(raw)):
                    candidate = match.group(1).strip().strip('.')
                    if len(candidate) > 10:
                        titulo = candidate
                        break

        if titulo_raw and not resto_raw and '. ' in titulo_raw:
            title_candidate, rest_candidate = titulo_raw.split('. ', 1)
            if title_candidate and rest_candidate:
                titulo = title_candidate.strip().strip('.')
                resto_raw = rest_candidate.strip()
        elif titulo and not resto_raw:
            if titulo in raw_text:
                remainder = raw_text.split(titulo, 1)[1]
                remainder = remainder.lstrip('. ').strip()
                if remainder:
                    resto_raw = remainder

        veiculo_ou_livro = ''
        if resto_raw:
            veiculo_ou_livro = resto_raw.split(',', 1)[0].strip().strip('.')

        if 'In:' in resto_raw or 'In:' in titulo_raw or 'In:' in str(raw):
            in_match = re.search(r'In:\s*([^,\.]+)', str(raw))
            if in_match:
                veiculo_ou_livro = in_match.group(1).strip().strip('.')

        return autores, titulo, veiculo_ou_livro
    except Exception:
        return '', '', ''
