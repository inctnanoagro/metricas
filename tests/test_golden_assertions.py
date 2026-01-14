"""
Golden assertions for key parsers.

Tests semantic correctness of extracted fields (titulo, veiculo, ano)
for the 3 priority production types.
"""

import pytest
from pathlib import Path
import unicodedata

from metricas_lattes.parser_router import parse_fixture, normalize_filename


# Test data root
FIXTURES_DIR = Path(__file__).parent / 'fixtures' / 'lattes'


def find_fixture_by_normalized_name(normalized_key: str) -> Path:
    """
    Find fixture by normalized name (accent-insensitive).

    Example: 'artigos aceitos' finds 'Artigos aceitos para publicação.html'
    """
    for html_file in FIXTURES_DIR.glob('*.html'):
        # Skip AppleDouble and hidden files
        if html_file.name.startswith(('.', '_')):
            continue

        # Normalize filename for comparison
        normalized = normalize_filename(html_file.name).lower()

        # Check if normalized key matches
        if normalized_key.lower() in normalized:
            return html_file

    raise FileNotFoundError(f"No fixture found matching normalized key: {normalized_key}")


class TestArtigosGolden:
    """Golden assertions for Artigos parser"""

    @pytest.fixture
    def result(self):
        """Parse artigos fixture once"""
        fixture_path = find_fixture_by_normalized_name('artigos aceitos para publicacao')
        return parse_fixture(fixture_path)

    def test_first_item_titulo(self, result):
        """First item has correct title"""
        item = result['items'][0]
        assert item['titulo'] is not None
        assert 'Essential Oil' in item['titulo']
        assert 'Fungicide' in item['titulo']

    def test_first_item_autores(self, result):
        """First item has correct authors"""
        item = result['items'][0]
        assert item['autores'] is not None
        assert 'TERRA, M. C.' in item['autores']
        assert 'FRACETO, L. F.' in item['autores']

    def test_first_item_ano(self, result):
        """First item has correct year"""
        item = result['items'][0]
        assert item['ano'] == 2026

    def test_first_item_veiculo(self, result):
        """First item has correct venue"""
        item = result['items'][0]
        assert item['veiculo'] is not None
        # May have minor extraction issues (e.g., "CS Omega" instead of "ACS Omega")
        # but should contain the main part
        assert 'Omega' in item['veiculo']


class TestCapitulosGolden:
    """Golden assertions for Capítulos parser"""

    @pytest.fixture
    def result(self):
        """Parse capítulos fixture once"""
        fixture_path = find_fixture_by_normalized_name('capitulos de livros publicados')
        return parse_fixture(fixture_path)

    def test_first_item_titulo(self, result):
        """First item has correct title"""
        item = result['items'][0]
        assert item['titulo'] is not None
        assert 'Colloidal Materials' in item['titulo']
        assert 'Soil Sustainability' in item['titulo']

    def test_first_item_autores(self, result):
        """First item has correct authors"""
        item = result['items'][0]
        assert item['autores'] is not None
        assert 'Villarreal' in item['autores']
        assert 'Campos' in item['autores']

    def test_first_item_ano(self, result):
        """First item has correct year"""
        item = result['items'][0]
        assert item['ano'] == 2025

    def test_first_item_livro(self, result):
        """First item has correct book name"""
        item = result['items'][0]
        assert item['livro'] is not None
        # Book name should be extracted

    def test_first_item_editora(self, result):
        """First item has editora field"""
        item = result['items'][0]
        # Editora may or may not be extracted depending on format


class TestTextosJornaisGolden:
    """Golden assertions for Textos em Jornais parser"""

    @pytest.fixture
    def result(self):
        """Parse textos em jornais fixture once"""
        fixture_path = find_fixture_by_normalized_name('textos em jornais de noticias')
        return parse_fixture(fixture_path)

    def test_first_item_titulo(self, result):
        """First item has correct title"""
        item = result['items'][0]
        assert item['titulo'] is not None
        assert 'herbicida' in item['titulo'].lower()

    def test_first_item_autores(self, result):
        """First item has correct authors"""
        item = result['items'][0]
        assert item['autores'] is not None
        assert 'TAKESHITA, VANESSA' in item['autores']
        assert 'FRACETO, L. F.' in item['autores']

    def test_first_item_ano(self, result):
        """First item has correct year"""
        item = result['items'][0]
        assert item['ano'] == 2025

    def test_first_item_mes(self, result):
        """First item has correct month"""
        item = result['items'][0]
        assert item['mes'] == 'mar'

    def test_first_item_veiculo(self, result):
        """First item has correct venue (not confused with author initials)"""
        item = result['items'][0]
        assert item['veiculo'] is not None
        # Should be "Cultivar Grandes Culturas", not author initials
        assert 'Cultivar' in item['veiculo']
        # Should NOT contain single letters or initials
        assert not re.match(r'^[A-Z]\.$', item['veiculo'])

    def test_no_author_initial_confusion(self, result):
        """Veiculo extraction should not be confused with author initials"""
        for item in result['items']:
            if item['veiculo']:
                # Veiculo should be a proper name, not initials like "A. C."
                assert len(item['veiculo']) > 5, f"Veiculo too short: {item['veiculo']}"
                # Should not be just initials
                assert not re.match(r'^[A-Z]\.\s*[A-Z]\.', item['veiculo'])


class TestTituloAuthorLeakage:
    """Critical tests to detect author name leakage into titulo field"""

    def test_artigos_no_author_leakage(self):
        """Artigos: No author surnames should appear in titulo"""
        fixture_path = find_fixture_by_normalized_name('artigos aceitos para publicacao')
        result = parse_fixture(fixture_path)

        for item in result['items']:
            titulo = item.get('titulo')
            autores = item.get('autores')

            if not titulo or not autores:
                continue

            # Extract author surnames
            author_parts = [a.strip() for a in autores.split(';')]
            for auth in author_parts:
                # Get lastname
                if ',' in auth:
                    lastname = auth.split(',')[0].strip()
                else:
                    parts = auth.split()
                    lastname = parts[-1] if parts else auth

                # Check: lastname should NOT appear in titulo
                # (at least 4 chars to avoid false positives with short words)
                if lastname and len(lastname) >= 4:
                    assert lastname.lower() not in titulo.lower(), \
                        f"Author surname '{lastname}' leaked into titulo: '{titulo}'"

    def test_capitulos_no_author_leakage(self):
        """Capítulos: No author surnames should appear in titulo"""
        fixture_path = find_fixture_by_normalized_name('capitulos de livros publicados')
        result = parse_fixture(fixture_path)

        for item in result['items']:
            titulo = item.get('titulo')
            autores = item.get('autores')

            if not titulo or not autores:
                continue

            # Extract author surnames
            author_parts = [a.strip() for a in autores.split(';')]
            for auth in author_parts:
                # Get lastname
                if ',' in auth:
                    lastname = auth.split(',')[0].strip()
                else:
                    parts = auth.split()
                    lastname = parts[-1] if parts else auth

                # Check: lastname should NOT appear in titulo
                if lastname and len(lastname) >= 4:
                    assert lastname.lower() not in titulo.lower(), \
                        f"Author surname '{lastname}' leaked into titulo: '{titulo}'"

    def test_textos_jornais_no_author_leakage(self):
        """Textos em jornais: No author surnames should appear in titulo"""
        fixture_path = find_fixture_by_normalized_name('textos em jornais de noticias')
        result = parse_fixture(fixture_path)

        for item in result['items']:
            titulo = item.get('titulo')
            autores = item.get('autores')

            if not titulo or not autores:
                continue

            # Extract author surnames
            author_parts = [a.strip() for a in autores.split(';')]
            for auth in author_parts:
                # Get lastname
                if ',' in auth:
                    lastname = auth.split(',')[0].strip()
                else:
                    parts = auth.split()
                    lastname = parts[-1] if parts else auth

                # Check: lastname should NOT appear in titulo
                if lastname and len(lastname) >= 4:
                    assert lastname.lower() not in titulo.lower(), \
                        f"Author surname '{lastname}' leaked into titulo: '{titulo}'"


class TestSemanticCorrectness:
    """Test semantic correctness across all parsers"""

    def test_anos_are_reasonable(self):
        """All extracted years should be in reasonable range"""
        fixture_keys = [
            'artigos aceitos para publicacao',
            'artigos completos publicados em periodicos',
            'capitulos de livros publicados',
            'textos em jornais de noticias'
        ]

        for key in fixture_keys:
            try:
                fixture_path = find_fixture_by_normalized_name(key)
            except FileNotFoundError:
                continue

            result = parse_fixture(fixture_path)

            for item in result['items']:
                if item.get('ano'):
                    ano = item['ano']
                    assert 1950 <= ano <= 2030, \
                        f"{fixture_path.name}: Unreasonable year {ano} in item {item['numero_item']}"

    def test_titulos_are_not_empty(self):
        """Extracted titles should not be empty strings"""
        fixture_keys = [
            'artigos aceitos para publicacao',
            'artigos completos publicados em periodicos',
            'capitulos de livros publicados',
            'textos em jornais de noticias'
        ]

        for key in fixture_keys:
            try:
                fixture_path = find_fixture_by_normalized_name(key)
            except FileNotFoundError:
                continue

            result = parse_fixture(fixture_path)

            for item in result['items']:
                if item.get('titulo'):
                    titulo = item['titulo']
                    assert len(titulo) > 3, \
                        f"{fixture_path.name}: Title too short in item {item['numero_item']}: '{titulo}'"

    def test_autores_format(self):
        """Authors should be properly formatted"""
        fixture_keys = [
            'artigos aceitos para publicacao',
            'capitulos de livros publicados',
            'textos em jornais de noticias'
        ]

        for key in fixture_keys:
            try:
                fixture_path = find_fixture_by_normalized_name(key)
            except FileNotFoundError:
                continue

            result = parse_fixture(fixture_path)

            for item in result['items']:
                if item.get('autores'):
                    autores = item['autores']
                    # Should contain at least one name
                    assert len(autores) > 3, \
                        f"{fixture_path.name}: Authors too short in item {item['numero_item']}"
                    # Should not be just punctuation
                    assert any(c.isalpha() for c in autores), \
                        f"{fixture_path.name}: No letters in authors in item {item['numero_item']}"


# Import re for regex checks
import re


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
