"""Tests for article parser"""

import pytest
from pathlib import Path
from metricas_lattes.parsers.artigos import ArtigoParser


@pytest.fixture
def sample_html():
    """Load sample HTML fixture"""
    fixture_path = Path(__file__).parent / 'fixtures' / 'artigo_sample.html'
    return fixture_path.read_text(encoding='utf-8')


@pytest.fixture
def parser():
    """Create parser instance"""
    return ArtigoParser()


def test_parse_multiple_articles(parser, sample_html):
    """Test parsing multiple articles from HTML"""
    articles = parser.parse_html(sample_html)
    
    assert len(articles) == 3
    assert all(a.categoria == "artigo" for a in articles)


def test_parse_complete_article(parser, sample_html):
    """Test parsing article with all fields"""
    articles = parser.parse_html(sample_html)
    
    # First article has all fields
    first = articles[0]
    assert first.ordem_lattes == 1
    assert first.titulo == "Nanotechnology applications in agriculture: A comprehensive review"
    assert first.autores == "SILVA, J. A.; SANTOS, M. B.; OLIVEIRA, P. C."
    assert first.veiculo == "Journal of Agricultural Science"
    assert first.volume == "142"
    assert first.paginas == "1-15"
    assert first.ano == 2024
    assert first.doi == "10.1234/jas.2024.001"
    assert first.raw_text is not None
    assert first.html_snippet is not None


def test_parse_article_without_doi(parser, sample_html):
    """Test parsing article without DOI"""
    articles = parser.parse_html(sample_html)
    
    # Second article has no DOI
    second = articles[1]
    assert second.ordem_lattes == 2
    assert second.titulo == "Polymeric nanoparticles for pesticide delivery"
    assert second.autores == "FRACETO, L. F.; GRILLO, R.; MEDINA, V."
    assert second.doi is None
    assert second.ano == 2023


def test_parse_article_missing_pages(parser, sample_html):
    """Test parsing article with incomplete metadata"""
    articles = parser.parse_html(sample_html)
    
    # Third article missing pages
    third = articles[2]
    assert third.ordem_lattes == 3
    assert third.titulo == "Sustainable nanotechnology in crop protection"
    assert third.autores == "COSTA, A. R."
    assert third.veiculo == "Nature Nanotechnology"
    assert third.volume == "17"
    assert third.ano == 2022
    assert third.doi == "10.1038/nnano.2022.123"


def test_extract_ordem_lattes(parser):
    """Test extraction of Lattes numbering"""
    html = """
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>42.</b></div>
    </div>
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find('div', class_='artigo-completo')
    
    ordem = parser._extract_ordem_lattes(div)
    assert ordem == 42


def test_extract_doi_variations(parser):
    """Test DOI extraction with different URL formats"""
    html_doi = """
    <div class="artigo-completo">
        <a class="icone-doi" href="https://doi.org/10.1234/test"></a>
    </div>
    """
    html_dx_doi = """
    <div class="artigo-completo">
        <a class="icone-doi" href="https://dx.doi.org/10.5678/test2"></a>
    </div>
    """
    
    from bs4 import BeautifulSoup
    
    div1 = BeautifulSoup(html_doi, 'html.parser').find('div')
    doi1 = parser._extract_doi(div1)
    assert doi1 == "10.1234/test"
    
    div2 = BeautifulSoup(html_dx_doi, 'html.parser').find('div')
    doi2 = parser._extract_doi(div2)
    assert doi2 == "10.5678/test2"


def test_clean_text_normalization(parser):
    """Test text cleaning with special characters"""
    text = "Text   with\xa0multiple   spaces"
    cleaned = parser.clean_text(text)
    assert cleaned == "Text with multiple spaces"


def test_normalize_author_name(parser):
    """Test author name normalization"""
    name = "  SILVA, João  A.  "
    normalized = parser._normalize_author_name(name)
    assert normalized == "SILVA, João A."


def test_to_dict_without_trace(parser, sample_html):
    """Test export without traceability fields"""
    articles = parser.parse_html(sample_html)
    first = articles[0]
    
    d = first.to_dict(include_trace=False)
    assert 'raw_text' not in d
    assert 'html_snippet' not in d
    assert 'titulo' in d
    assert 'autores' in d


def test_to_dict_with_trace(parser, sample_html):
    """Test export with traceability fields"""
    articles = parser.parse_html(sample_html)
    first = articles[0]
    
    d = first.to_dict(include_trace=True)
    assert 'raw_text' in d
    assert 'html_snippet' in d


def test_empty_html(parser):
    """Test parsing empty HTML"""
    articles = parser.parse_html("")
    assert articles == []


def test_malformed_html(parser):
    """Test graceful handling of malformed HTML"""
    html = "<div class='artigo-completo'><p>Invalid structure</p></div>"
    articles = parser.parse_html(html)
    # Should not crash, may return empty or skip malformed entries
    assert isinstance(articles, list)


def test_special_characters_in_title(parser):
    """Test handling special characters in title"""
    html = """
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>1.</b></div>
        <div class="layout-cell-pad-5"><span data-tipo-ordenacao="ano">2024</span></div>
        <div class="layout-cell-11">
            <span class="transform">
                AUTHOR, A. . Title with special chars: α, β, γ &amp; symbols. Journal Name, v. 1, p. 1-10, 2024.
            </span>
        </div>
    </div>
    """
    articles = parser.parse_html(html)
    assert len(articles) == 1
    assert "α, β, γ" in articles[0].titulo
    assert "&" in articles[0].veiculo or "symbols" in articles[0].titulo


def test_error_tracking_malformed(parser):
    """Test that errors are tracked for malformed articles"""
    html = """
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>99.</b></div>
        <!-- Missing required structure -->
    </div>
    """
    articles = parser.parse_html(html)
    
    # Should track error with missing_structure reason
    assert len(parser.errors) == 1
    assert parser.errors[0]['ordem_lattes'] == 99
    assert parser.errors[0]['reason'] == 'missing_structure'
    assert 'html_snippet' in parser.errors[0]
    assert len(parser.errors[0]['html_snippet']) <= 500


def test_error_tracking_continues_parsing(parser):
    """Test that parsing continues after error"""
    html = """
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>1.</b></div>
        <!-- Malformed - no layout-cell-11 -->
    </div>
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>2.</b></div>
        <div class="layout-cell-pad-5"><span data-tipo-ordenacao="ano">2024</span></div>
        <div class="layout-cell-11">
            <span class="transform">
                VALID, A. . Valid article. Journal, v. 1, p. 1-5, 2024.
            </span>
        </div>
    </div>
    """
    articles = parser.parse_html(html)
    
    # Should parse valid article despite first error
    assert len(articles) == 1
    assert articles[0].ordem_lattes == 2
    assert len(parser.errors) == 1
    assert parser.errors[0]['ordem_lattes'] == 1
    assert parser.errors[0]['reason'] == 'missing_structure'


def test_error_tracking_exception(parser, monkeypatch):
    """Test that exceptions are tracked with exception reason"""
    html = """
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>5.</b></div>
        <div class="layout-cell-11">
            <span class="transform">AUTHOR, A. . Title. Journal, v. 1, p. 1-5, 2024.</span>
        </div>
    </div>
    """
    
    # Force an exception during metadata extraction
    def mock_extract_metadata(self, texto):
        raise ValueError("Forced test exception")
    
    monkeypatch.setattr(parser, '_extract_metadata', mock_extract_metadata.__get__(parser, ArtigoParser))
    
    articles = parser.parse_html(html)
    
    # Should track exception
    assert len(articles) == 0
    assert len(parser.errors) == 1
    assert parser.errors[0]['ordem_lattes'] == 5
    assert parser.errors[0]['reason'] == 'exception'
    assert 'error' in parser.errors[0]
    assert 'Forced test exception' in parser.errors[0]['error']


def test_error_reset_between_runs(parser):
    """Test that errors are reset between parse runs"""
    html = """
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>1.</b></div>
    </div>
    """
    
    # First run
    parser.parse_html(html)
    assert len(parser.errors) == 1
    
    # Second run should reset errors
    parser.parse_html("")
    assert len(parser.errors) == 0