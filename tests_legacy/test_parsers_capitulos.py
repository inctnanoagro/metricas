"""Tests for book chapter parser"""

import pytest
from pathlib import Path
from metricas_lattes.parsers.capitulos import CapituloParser


@pytest.fixture
def sample_html():
    """Load sample HTML fixture"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'capitulo_sample.html'
    return fixture_path.read_text(encoding='utf-8')


@pytest.fixture
def parser():
    """Create parser instance"""
    return CapituloParser()


def test_parse_multiple_chapters(parser, sample_html):
    """Test parsing multiple chapters from HTML"""
    chapters = parser.parse_html(sample_html)
    
    assert len(chapters) == 3
    assert all(c.categoria == "capitulo" for c in chapters)


def test_parse_complete_chapter(parser, sample_html):
    """Test parsing chapter with all fields"""
    chapters = parser.parse_html(sample_html)
    
    # First chapter has all basic fields
    first = chapters[0]
    assert first.ordem_lattes == 1
    assert first.titulo == "Nanotechnology in sustainable agriculture"
    assert first.autores == "SILVA, J. A.; SANTOS, M. B."
    assert first.livro == "Advances in Agricultural Science"
    assert first.editora == "Editora Científica"
    assert first.edicao == "1"
    assert first.ano == 2024
    assert first.paginas == "45-67"
    assert first.doi == "10.1234/book.2024.001"
    assert first.isbn is None
    assert first.raw_text is not None
    assert first.html_snippet is not None


def test_parse_chapter_with_isbn(parser, sample_html):
    """Test parsing chapter with ISBN"""
    chapters = parser.parse_html(sample_html)
    
    # Second chapter has ISBN
    second = chapters[1]
    assert second.ordem_lattes == 2
    assert second.titulo == "Polymeric nanoparticles for pesticide delivery systems"
    assert second.autores == "FRACETO, L. F.; GRILLO, R."
    assert second.livro == "Nanomaterials in Agriculture"
    assert second.edicao == "2"
    assert second.ano == 2023
    assert second.isbn == "978-85-1234-567-8"
    assert second.doi is None


def test_parse_chapter_without_isbn_or_doi(parser, sample_html):
    """Test parsing chapter with minimal metadata"""
    chapters = parser.parse_html(sample_html)
    
    # Third chapter
    third = chapters[2]
    assert third.ordem_lattes == 3
    assert third.titulo == "Environmental impact of nanotechnology"
    assert third.autores == "MEDINA, V."
    assert third.livro == "Green Technologies"
    assert third.ano == 2022
    assert third.doi == "10.5678/green.2022.003"


def test_extract_doi_variations(parser):
    """Test DOI extraction with different URL formats"""
    html = """
    <div class="layout-cell-11">
        <span class="transform">AUTHOR. Title. In: EDITOR (Org.). Book. 1ed. City: Pub, 2024, p. 1-10.</span>
        <a class="icone-doi" href="https://dx.doi.org/10.1234/test"></a>
    </div>
    """
    
    chapters = parser.parse_html(html)
    assert len(chapters) == 1
    assert chapters[0].doi == "10.1234/test"


def test_extract_isbn(parser):
    """Test ISBN extraction"""
    html = """
    <div class="layout-cell-11">
        <span class="transform">AUTHOR. Title. In: EDITOR (Org.). Book. 1ed. City: Pub, 2024, p. 1-10. ISBN 978-1-234-56789-0.</span>
    </div>
    """
    
    chapters = parser.parse_html(html)
    assert len(chapters) == 1
    assert chapters[0].isbn == "978-1-234-56789-0"


def test_to_dict_without_trace(parser, sample_html):
    """Test export without traceability fields"""
    chapters = parser.parse_html(sample_html)
    first = chapters[0]
    
    d = first.to_dict(include_trace=False)
    assert 'raw_text' not in d
    assert 'html_snippet' not in d
    assert 'titulo' in d
    assert 'autores' in d


def test_to_dict_with_trace(parser, sample_html):
    """Test export with traceability fields"""
    chapters = parser.parse_html(sample_html)
    first = chapters[0]
    
    d = first.to_dict(include_trace=True)
    assert 'raw_text' in d
    assert 'html_snippet' in d


def test_empty_html(parser):
    """Test parsing empty HTML"""
    chapters = parser.parse_html("")
    assert chapters == []


def test_non_chapter_content_ignored(parser):
    """Test that non-chapter content is ignored"""
    html = """
    <div class="layout-cell-11">
        <span class="transform">Some other content without In: or (Org.)</span>
    </div>
    """
    chapters = parser.parse_html(html)
    assert len(chapters) == 0
    assert len(parser.errors) == 0  # Not logged as error since it's not a chapter


def test_error_tracking_malformed_chapter(parser):
    """Test that errors are tracked for malformed chapters"""
    html = """
    <div class="layout-cell-11">
        <div class="layout-cell-1"><b>99.</b></div>
        <span class="transform">AUTHOR. Incomplete In: something (Org.) but missing structure</span>
    </div>
    """
    chapters = parser.parse_html(html)
    
    # Should track error with missing_structure reason
    assert len(parser.errors) == 1
    assert parser.errors[0]['ordem_lattes'] == 99
    assert parser.errors[0]['reason'] == 'missing_structure'


def test_error_tracking_continues_parsing(parser):
    """Test that parsing continues after error"""
    html = """
    <div class="layout-cell-11">
        <div class="layout-cell-1"><b>1.</b></div>
        <span class="transform">MALFORMED. In: something (Org.) incomplete</span>
    </div>
    <div class="layout-cell-11">
        <div class="layout-cell-1"><b>2.</b></div>
        <span class="transform">VALID, A. . Valid chapter. In: EDITOR (Org.). Book. 1ed. City: Pub, 2024, p. 1-5.</span>
    </div>
    """
    chapters = parser.parse_html(html)
    
    # Should parse valid chapter despite first error
    assert len(chapters) == 1
    assert chapters[0].ordem_lattes == 2
    assert len(parser.errors) == 1


def test_error_reset_between_runs(parser):
    """Test that errors are reset between parse runs"""
    html = """
    <div class="layout-cell-11">
        <span class="transform">MALFORMED. In: (Org.) incomplete</span>
    </div>
    """
    
    # First run
    parser.parse_html(html)
    first_error_count = len(parser.errors)
    assert first_error_count > 0
    
    # Second run should reset errors
    parser.parse_html("")
    assert len(parser.errors) == 0


def test_error_tracking_exception(parser, monkeypatch):
    """Test that exceptions are tracked with exception reason"""
    html = """
    <div class="layout-cell-11">
        <div class="layout-cell-1"><b>5.</b></div>
        <span class="transform">AUTHOR. Title. In: EDITOR (Org.). Book. 1ed. City: Pub, 2024, p. 1-5.</span>
    </div>
    """
    
    # Force an exception during extraction
    def mock_extract_livro(self, texto):
        raise ValueError("Forced test exception")
    
    monkeypatch.setattr(CapituloParser, '_extract_livro_edicao', mock_extract_livro)
    
    chapters = parser.parse_html(html)
    
    # Should track exception
    assert len(chapters) == 0
    assert len(parser.errors) == 1
    assert parser.errors[0]['ordem_lattes'] == 5
    assert parser.errors[0]['reason'] == 'exception'
    assert 'Forced test exception' in parser.errors[0]['error']