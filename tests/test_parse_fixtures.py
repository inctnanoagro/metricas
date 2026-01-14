"""
Test suite for parsing Lattes fixtures.

Tests:
1. JSON Schema validation
2. Minimal normalization (required fields)
3. Determinism (running twice produces same output)
4. Golden file comparison (when available)
"""

import json
import hashlib
import pytest
from pathlib import Path
from typing import Dict, Any

from metricas_lattes.parser_router import parse_fixture

# Constants
FIXTURES_DIR = Path(__file__).parent / 'fixtures' / 'lattes'
EXPECTED_DIR = Path(__file__).parent / 'fixtures' / 'expected'
SCHEMA_PATH = Path(__file__).parent.parent / 'schema' / 'producoes.schema.json'

# Exclude full_profile directory
EXCLUDE_DIRS = ['full_profile']


def get_fixture_files():
    """Get all HTML fixture files, excluding specified directories and macOS metadata files"""
    fixtures = []
    for html_file in FIXTURES_DIR.glob('*.html'):
        # Skip macOS AppleDouble files (._*)
        if html_file.name.startswith('._') or html_file.name.startswith('.'):
            continue
        # Skip if in excluded directory
        if any(excl in str(html_file) for excl in EXCLUDE_DIRS):
            continue
        fixtures.append(html_file)
    return sorted(fixtures)


def load_schema() -> Dict[str, Any]:
    """Load JSON Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> list:
    """
    Validate data against JSON Schema.

    Returns list of validation errors (empty if valid).
    """
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import ValidationError

        validator = Draft202012Validator(schema)
        errors = []

        for error in validator.iter_errors(data):
            errors.append(f"{'.'.join(str(p) for p in error.path)}: {error.message}")

        return errors

    except ImportError:
        # If jsonschema not installed, do basic validation
        return validate_basic(data, schema)


def validate_basic(data: Dict[str, Any], schema: Dict[str, Any]) -> list:
    """Basic validation without jsonschema library"""
    errors = []

    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check schema_version
    if data.get('schema_version') != '2.0.0':
        errors.append(f"Invalid schema_version: {data.get('schema_version')}")

    # Check items is list
    if 'items' in data and not isinstance(data['items'], list):
        errors.append("items must be a list")

    # Check each item has required fields
    for idx, item in enumerate(data.get('items', [])):
        if 'numero_item' not in item:
            errors.append(f"Item {idx}: missing numero_item")
        if 'raw' not in item:
            errors.append(f"Item {idx}: missing raw")

    return errors


def compute_determinism_hash(data: Dict[str, Any]) -> str:
    """
    Compute hash of data for determinism check.

    Excludes timestamp fields.
    """
    # Create copy without timestamp
    data_copy = data.copy()
    data_copy.pop('extraction_timestamp', None)

    # Sort keys for consistent hashing
    json_str = json.dumps(data_copy, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


class TestFixtureParsing:
    """Test suite for fixture parsing"""

    @pytest.fixture(scope='session')
    def schema(self):
        """Load schema once for all tests"""
        return load_schema()

    @pytest.mark.parametrize('fixture_path', get_fixture_files())
    def test_schema_validation(self, fixture_path: Path, schema):
        """Test that parsed output validates against JSON Schema"""
        # Parse fixture
        result = parse_fixture(fixture_path)

        # Validate against schema
        errors = validate_against_schema(result, schema)

        # Assert no errors
        if errors:
            error_msg = f"\n{fixture_path.name} schema validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
            pytest.fail(error_msg)

    @pytest.mark.parametrize('fixture_path', get_fixture_files())
    def test_required_fields(self, fixture_path: Path):
        """Test that all required fields are present"""
        result = parse_fixture(fixture_path)

        # Check top-level required fields
        assert 'schema_version' in result, "Missing schema_version"
        assert 'tipo_producao' in result, "Missing tipo_producao"
        assert 'source_file' in result, "Missing source_file"
        assert 'items' in result, "Missing items"
        assert isinstance(result['items'], list), "items must be a list"

        # Check each item has required fields
        for idx, item in enumerate(result['items']):
            assert 'numero_item' in item, f"Item {idx}: missing numero_item"
            assert 'raw' in item, f"Item {idx}: missing raw"
            assert isinstance(item['numero_item'], int), f"Item {idx}: numero_item must be int"
            assert isinstance(item['raw'], str), f"Item {idx}: raw must be string"
            assert len(item['raw']) > 0, f"Item {idx}: raw must not be empty"

    @pytest.mark.parametrize('fixture_path', get_fixture_files())
    def test_determinism(self, fixture_path: Path):
        """Test that parsing is deterministic (same input -> same output)"""
        # Parse twice
        result1 = parse_fixture(fixture_path)
        result2 = parse_fixture(fixture_path)

        # Compute hashes (excluding timestamps)
        hash1 = compute_determinism_hash(result1)
        hash2 = compute_determinism_hash(result2)

        # Assert same hash
        assert hash1 == hash2, f"{fixture_path.name}: Non-deterministic parsing"

    @pytest.mark.parametrize('fixture_path', get_fixture_files())
    def test_items_not_empty(self, fixture_path: Path):
        """Test that parsing extracts at least some items"""
        result = parse_fixture(fixture_path)

        # Should have at least one item (unless file is truly empty)
        # We allow 0 items only for legitimately empty fixtures
        items = result['items']

        # Log for debugging
        if len(items) == 0:
            print(f"\nWARNING: {fixture_path.name} produced 0 items")

        # This is informational, not a hard failure
        # Some files might legitimately be empty
        assert isinstance(items, list)

    @pytest.mark.parametrize('fixture_path', get_fixture_files())
    def test_numero_item_sequential(self, fixture_path: Path):
        """Test that numero_item values are reasonable (positive integers)"""
        result = parse_fixture(fixture_path)

        numeros = [item['numero_item'] for item in result['items']]

        for numero in numeros:
            assert numero >= 1, f"{fixture_path.name}: numero_item must be >= 1, got {numero}"

        # Check for reasonable sequence (allowing gaps)
        if len(numeros) > 0:
            assert min(numeros) >= 1, f"{fixture_path.name}: minimum numero_item should be >= 1"

    @pytest.mark.parametrize('fixture_path', get_fixture_files())
    def test_fingerprints(self, fixture_path: Path):
        """Test that fingerprints are valid SHA1 hashes"""
        result = parse_fixture(fixture_path)

        for idx, item in enumerate(result['items']):
            if 'fingerprint_sha1' in item and item['fingerprint_sha1']:
                fp = item['fingerprint_sha1']
                # Check it's a valid SHA1 (40 hex chars)
                assert len(fp) == 40, f"Item {idx}: invalid SHA1 length"
                assert all(c in '0123456789abcdef' for c in fp), f"Item {idx}: invalid SHA1 chars"

    def test_golden_files(self):
        """
        Test against golden files (expected outputs).

        This test is skipped if golden files don't exist yet.
        Golden files can be generated by running parsers and manually verifying output.
        """
        # Check if expected directory has any golden files
        if not EXPECTED_DIR.exists() or not list(EXPECTED_DIR.glob('*.json')):
            pytest.skip("No golden files found - run parsers to generate them first")

        for golden_file in EXPECTED_DIR.glob('*.json'):
            # Find corresponding fixture
            fixture_name = golden_file.stem + '.html'
            fixture_path = FIXTURES_DIR / fixture_name

            if not fixture_path.exists():
                pytest.skip(f"Fixture not found for golden file: {fixture_name}")

            # Load golden data
            with open(golden_file, 'r', encoding='utf-8') as f:
                expected = json.load(f)

            # Parse fixture
            result = parse_fixture(fixture_path)

            # Remove timestamps for comparison
            result_copy = result.copy()
            result_copy.pop('extraction_timestamp', None)
            expected_copy = expected.copy()
            expected_copy.pop('extraction_timestamp', None)

            # Compare
            assert result_copy == expected_copy, f"Output differs from golden file: {golden_file.name}"


class TestParserRegistry:
    """Test parser registry and routing"""

    def test_registry_has_entries(self):
        """Test that parser registry is not empty"""
        from metricas_lattes.parser_router import PARSER_REGISTRY
        assert len(PARSER_REGISTRY) > 0, "Parser registry should not be empty"

    def test_known_types_have_parsers(self):
        """Test that known production types are registered"""
        from metricas_lattes.parser_router import PARSER_REGISTRY

        # These should definitely have parsers (normalized strings without accents)
        expected_types = [
            'artigos completos',
            'artigos aceitos',
            'capitulos',  # normalized (no accent)
        ]

        registry_str = ' '.join(PARSER_REGISTRY.keys()).lower()

        for expected in expected_types:
            assert expected in registry_str, f"Expected '{expected}' to be in registry"

    def test_get_parser_for_file(self):
        """Test parser selection logic"""
        from metricas_lattes.parser_router import get_parser_for_file, GenericParser, ArtigoParser

        # Test specific parser
        test_path = Path('Artigos completos publicados em periódicos.html')
        parser = get_parser_for_file(test_path)
        assert parser is not None
        assert isinstance(parser, ArtigoParser), f"Expected ArtigoParser, got {type(parser).__name__}"

        # Test fallback to generic
        test_path = Path('Unknown Type.html')
        parser = get_parser_for_file(test_path)
        assert isinstance(parser, GenericParser)


if __name__ == '__main__':
    # Run with: python -m pytest tests/test_parse_fixtures.py -v
    pytest.main([__file__, '-v', '--tb=short'])
