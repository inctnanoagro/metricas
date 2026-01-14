"""
Tests for batch_full_profile module.

Tests batch processing of researcher full_profile HTMLs.
"""

import pytest
import json
import shutil
from pathlib import Path

from metricas_lattes.batch_full_profile import (
    slugify,
    extract_lattes_id_from_filename,
    extract_researcher_metadata_from_html,
    extract_production_sections_from_html,
    process_researcher_file
)


# Test data
FIXTURES_DIR = Path(__file__).parent / 'fixtures' / 'lattes' / 'full_profile'
TEST_OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'test_batch'


class TestSlugify:
    """Test slugify function."""

    def test_simple_name(self):
        """Simple name becomes lowercase with hyphens"""
        assert slugify("Leonardo Fernandes Fraceto") == "leonardo-fernandes-fraceto"

    def test_accents(self):
        """Accents are removed"""
        assert slugify("José María García") == "jose-maria-garcia"

    def test_special_chars(self):
        """Special chars become hyphens"""
        assert slugify("Name (with) special.chars!") == "name-with-special-chars"

    def test_multiple_spaces(self):
        """Multiple spaces collapse to single hyphen"""
        assert slugify("Name  with   spaces") == "name-with-spaces"


class TestExtractLattesIdFromFilename:
    """Test Lattes ID extraction from filename."""

    def test_standard_format(self):
        """Standard format: <id>__<slug>.full_profile.html"""
        filename = "8657413561406750__leonardo-fernandes-fraceto.full_profile.html"
        assert extract_lattes_id_from_filename(filename) == "8657413561406750"

    def test_no_id_in_filename(self):
        """No ID in filename returns None"""
        filename = "full_profile_leonardo_fraceto.html"
        assert extract_lattes_id_from_filename(filename) is None

    def test_malformed_filename(self):
        """Malformed filename returns None"""
        filename = "abc__something.html"
        assert extract_lattes_id_from_filename(filename) is None


class TestExtractResearcherMetadata:
    """Test researcher metadata extraction from HTML."""

    def test_extract_from_fraceto_fixture(self):
        """Extract metadata from Leonardo Fraceto fixture"""
        fixture_path = FIXTURES_DIR / 'full_profile_leonardo_fraceto.html'

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        metadata = extract_researcher_metadata_from_html(fixture_path)

        assert metadata['lattes_id'] == '4741480538883395'
        assert metadata['full_name'] == 'Leonardo Fernandes Fraceto'
        assert metadata['slug'] == 'leonardo-fernandes-fraceto'
        assert metadata['last_update'] is not None


class TestExtractProductionSections:
    """Test production section extraction."""

    def test_extract_sections_from_fraceto(self):
        """Extract sections from Leonardo Fraceto fixture"""
        fixture_path = FIXTURES_DIR / 'full_profile_leonardo_fraceto.html'

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        sections = extract_production_sections_from_html(fixture_path)

        # Should have multiple production sections
        assert len(sections) > 0

        # Each section should have required fields
        for section in sections:
            assert 'section_title' in section
            assert 'html_content' in section
            assert 'item_count' in section
            assert section['item_count'] > 0

        # Check for known sections
        section_titles = [s['section_title'] for s in sections]
        # At least "Produções" should be present
        assert any('Produções' in title or 'Produ' in title for title in section_titles)


class TestProcessResearcherFile:
    """Test full researcher file processing."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Setup: create output dir
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (TEST_OUTPUT_DIR / 'researchers').mkdir(exist_ok=True)

        yield

        # Teardown: clean up
        if TEST_OUTPUT_DIR.exists():
            shutil.rmtree(TEST_OUTPUT_DIR)

    def test_process_fraceto_fixture(self):
        """Process Leonardo Fraceto fixture"""
        fixture_path = FIXTURES_DIR / 'full_profile_leonardo_fraceto.html'

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        result = process_researcher_file(fixture_path, TEST_OUTPUT_DIR, schema=None)

        # Check result metadata
        assert result['success'] is True
        assert result['lattes_id'] == '4741480538883395'
        assert result['full_name'] == 'Leonardo Fernandes Fraceto'
        assert result['slug'] == 'leonardo-fernandes-fraceto'
        assert result['total_items'] > 0
        assert len(result['sections']) > 0
        assert result['error'] is None
        assert result['output_json'] is not None

        # Check that JSON was created
        json_path = Path(result['output_json'])
        assert json_path.exists()

        # Check JSON structure
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['schema_version'] == '2.0.0'
        assert 'researcher' in data
        assert 'metadata' in data
        assert 'productions' in data

        # Check researcher metadata
        assert data['researcher']['lattes_id'] == '4741480538883395'
        assert data['researcher']['full_name'] == 'Leonardo Fernandes Fraceto'
        assert data['researcher']['slug'] == 'leonardo-fernandes-fraceto'

        # Check productions structure
        assert len(data['productions']) > 0

        # Check first production has provenance
        first_item = data['productions'][0]
        assert 'source' in first_item
        assert first_item['source']['file'] == fixture_path.name
        assert first_item['source']['lattes_id'] == '4741480538883395'
        assert 'production_type' in first_item['source']
        assert 'extracted_at' in first_item['source']

        # Check required fields in item
        assert 'numero_item' in first_item
        assert 'raw' in first_item
        assert 'fingerprint_sha1' in first_item


class TestBatchIntegration:
    """Integration tests for batch processing."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Setup
        TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (TEST_OUTPUT_DIR / 'researchers').mkdir(exist_ok=True)

        yield

        # Teardown
        if TEST_OUTPUT_DIR.exists():
            shutil.rmtree(TEST_OUTPUT_DIR)

    def test_batch_processing_determinism(self):
        """Batch processing should be deterministic"""
        fixture_path = FIXTURES_DIR / 'full_profile_leonardo_fraceto.html'

        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        # Process twice
        result1 = process_researcher_file(fixture_path, TEST_OUTPUT_DIR, schema=None)

        # Verify first result succeeded
        if not result1['success']:
            pytest.fail(f"First processing failed: {result1.get('error')}")

        result2 = process_researcher_file(fixture_path, TEST_OUTPUT_DIR, schema=None)

        # Verify second result succeeded
        if not result2['success']:
            pytest.fail(f"Second processing failed: {result2.get('error')}")

        # Results should be identical
        assert result1['lattes_id'] == result2['lattes_id']
        assert result1['total_items'] == result2['total_items']
        assert result1['success'] == result2['success']

        # Load both JSONs
        with open(result1['output_json'], 'r', encoding='utf-8') as f:
            data1 = json.load(f)

        with open(result2['output_json'], 'r', encoding='utf-8') as f:
            data2 = json.load(f)

        # Same number of productions
        assert len(data1['productions']) == len(data2['productions'])

        # Same fingerprints (determinism)
        fingerprints1 = [item['fingerprint_sha1'] for item in data1['productions']]
        fingerprints2 = [item['fingerprint_sha1'] for item in data2['productions']]
        assert fingerprints1 == fingerprints2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
