"""Integration tests for CLI prefill tool"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def fixture_path():
    """Path to article sample fixture"""
    return Path(__file__).parent / 'fixtures' / 'artigo_sample.html'


@pytest.fixture
def output_dir():
    """Output directory for prefill JSON"""
    return Path(__file__).parent.parent / 'docs' / 'prefill'


@pytest.fixture
def cli_script():
    """Path to CLI script"""
    return Path(__file__).parent.parent / 'scripts' / 'prefill_from_lattes.py'


def test_cli_basic_usage(fixture_path, output_dir, cli_script):
    """Test basic CLI usage with sample fixture"""
    # Clean up if exists
    output_file = output_dir / "test_researcher.json"
    errors_file = output_dir / "test_researcher.errors.json"
    if output_file.exists():
        output_file.unlink()
    if errors_file.exists():
        errors_file.unlink()
    
    # Run CLI
    result = subprocess.run(
        [sys.executable, str(cli_script), str(fixture_path), '--pesquisador', 'test_researcher'],
        capture_output=True,
        text=True
    )
    
    # Check exit code
    assert result.returncode == 0
    
    # Check output files exist
    assert output_file.exists()
    assert errors_file.exists()
    
    # Load and validate main JSON
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['pesquisador'] == 'test_researcher'
    assert 'generated_at' in data
    assert data['source_html'] == 'artigo_sample.html'
    assert 'producoes' in data
    assert 'artigos' in data['producoes']
    assert data['counts']['artigos'] == 3
    
    # Validate articles
    articles = data['producoes']['artigos']
    assert len(articles) == 3
    
    # Check first article (should have ordem_lattes=1)
    first = articles[0]
    assert first['ordem_lattes'] == 1
    assert first['categoria'] == 'artigo'
    assert 'titulo' in first
    assert 'autores' in first
    assert 'raw_text' in first  # include_trace=True
    assert 'html_snippet' in first
    
    # Check sorting (ordem_lattes ascending)
    assert articles[0]['ordem_lattes'] == 1
    assert articles[1]['ordem_lattes'] == 2
    assert articles[2]['ordem_lattes'] == 3
    
    # Load and validate errors JSON
    with open(errors_file, 'r', encoding='utf-8') as f:
        errors_data = json.load(f)
    
    assert errors_data['pesquisador'] == 'test_researcher'
    assert errors_data['source_html'] == 'artigo_sample.html'
    assert 'errors' in errors_data
    assert errors_data['errors'] == []  # No errors in sample fixture
    
    # Clean up
    output_file.unlink()
    errors_file.unlink()


def test_cli_missing_input_file(cli_script):
    """Test CLI with missing input file"""
    result = subprocess.run(
        [sys.executable, str(cli_script), 'nonexistent.html', '--pesquisador', 'test'],
        capture_output=True,
        text=True
    )
    
    # Should exit with code 2
    assert result.returncode == 2
    assert 'not found' in result.stderr.lower()


def test_cli_conflicting_input_args(fixture_path, cli_script):
    """Test CLI with both positional and --input flag"""
    result = subprocess.run(
        [sys.executable, str(cli_script), str(fixture_path), '--input', str(fixture_path), '--pesquisador', 'test'],
        capture_output=True,
        text=True
    )
    
    # Should exit with code 2
    assert result.returncode == 2
    assert 'cannot specify both' in result.stderr.lower()


def test_cli_alternative_input_flag(fixture_path, output_dir, cli_script):
    """Test CLI with --input flag"""
    output_file = output_dir / "test_alt.json"
    errors_file = output_dir / "test_alt.errors.json"
    if output_file.exists():
        output_file.unlink()
    if errors_file.exists():
        errors_file.unlink()
    
    result = subprocess.run(
        [sys.executable, str(cli_script), '--input', str(fixture_path), '--pesquisador', 'test_alt'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert output_file.exists()
    assert errors_file.exists()
    
    # Clean up
    output_file.unlink()
    errors_file.unlink()


def test_cli_with_errors(output_dir, cli_script, tmp_path):
    """Test CLI handles parsing errors correctly"""
    # Create malformed HTML
    malformed_html = tmp_path / "malformed.html"
    malformed_html.write_text("""
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>1.</b></div>
        <!-- Missing required structure -->
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
    """, encoding='utf-8')
    
    output_file = output_dir / "test_errors.json"
    errors_file = output_dir / "test_errors.errors.json"
    if output_file.exists():
        output_file.unlink()
    if errors_file.exists():
        errors_file.unlink()
    
    result = subprocess.run(
        [sys.executable, str(cli_script), str(malformed_html), '--pesquisador', 'test_errors'],
        capture_output=True,
        text=True
    )
    
    # Should still exit 0
    assert result.returncode == 0
    
    # Check errors were logged
    with open(errors_file, 'r', encoding='utf-8') as f:
        errors_data = json.load(f)
    
    assert len(errors_data['errors']) == 1
    assert errors_data['errors'][0]['ordem_lattes'] == 1
    assert errors_data['errors'][0]['reason'] == 'missing_structure'
    
    # Check valid article was parsed
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['counts']['artigos'] == 1
    assert data['producoes']['artigos'][0]['ordem_lattes'] == 2
    
    # Clean up
    output_file.unlink()
    errors_file.unlink()


def test_cli_sorting_with_none_ordem(output_dir, cli_script, tmp_path):
    """Test deterministic sorting with None ordem_lattes values"""
    # Create HTML with missing ordem values
    html_with_none = tmp_path / "mixed_ordem.html"
    html_with_none.write_text("""
    <div class="artigo-completo">
        <div class="layout-cell-pad-5"><span data-tipo-ordenacao="ano">2024</span></div>
        <div class="layout-cell-11">
            <span class="transform">
                AUTHOR, A. . Zebra title. Journal, v. 1, p. 1-5, 2024.
            </span>
        </div>
    </div>
    <div class="artigo-completo">
        <div class="layout-cell-1"><b>1.</b></div>
        <div class="layout-cell-pad-5"><span data-tipo-ordenacao="ano">2024</span></div>
        <div class="layout-cell-11">
            <span class="transform">
                AUTHOR, B. . Alpha title. Journal, v. 1, p. 1-5, 2024.
            </span>
        </div>
    </div>
    <div class="artigo-completo">
        <div class="layout-cell-pad-5"><span data-tipo-ordenacao="ano">2024</span></div>
        <div class="layout-cell-11">
            <span class="transform">
                AUTHOR, C. . Beta title. Journal, v. 1, p. 1-5, 2024.
            </span>
        </div>
    </div>
    """, encoding='utf-8')
    
    output_file = output_dir / "test_sorting.json"
    errors_file = output_dir / "test_sorting.errors.json"
    if output_file.exists():
        output_file.unlink()
    if errors_file.exists():
        errors_file.unlink()
    
    result = subprocess.run(
        [sys.executable, str(cli_script), str(html_with_none), '--pesquisador', 'test_sorting'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data['producoes']['artigos']
    assert len(articles) == 3
    
    # First should be ordem=1
    assert articles[0]['ordem_lattes'] == 1
    assert 'Alpha title' in articles[0]['titulo']
    
    # Next two should be None ordem, sorted by title
    assert articles[1]['ordem_lattes'] is None
    assert 'Beta title' in articles[1]['titulo']
    assert articles[2]['ordem_lattes'] is None
    assert 'Zebra title' in articles[2]['titulo']
    
    # Clean up
    output_file.unlink()
    errors_file.unlink()