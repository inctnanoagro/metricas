#!/usr/bin/env python3
"""
Script manual para testar parsers sem pytest.

Uso:
    python3 scripts/test_parsers_manual.py
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metricas_lattes.parser_router import parse_fixture, PARSER_REGISTRY


def test_single_file(fixture_path: Path):
    """Test parsing a single file"""
    print(f"\n{'='*80}")
    print(f"Testing: {fixture_path.name}")
    print(f"{'='*80}")

    try:
        result = parse_fixture(fixture_path)

        print(f"\n✓ Parse successful!")
        print(f"  - Schema version: {result.get('schema_version')}")
        print(f"  - Type: {result.get('tipo_producao')}")
        print(f"  - Items parsed: {len(result.get('items', []))}")

        # Show first 2 items
        items = result.get('items', [])
        if items:
            print(f"\n  First item:")
            item = items[0]
            print(f"    - numero_item: {item.get('numero_item')}")
            print(f"    - autores: {item.get('autores', 'N/A')[:80]}")
            print(f"    - titulo: {item.get('titulo', 'N/A')[:80]}")
            print(f"    - ano: {item.get('ano', 'N/A')}")
            print(f"    - raw (first 100 chars): {item.get('raw', '')[:100]}...")

            if len(items) > 1:
                print(f"\n  Last item:")
                item = items[-1]
                print(f"    - numero_item: {item.get('numero_item')}")
                print(f"    - autores: {item.get('autores', 'N/A')[:80]}")

        # Check metadata
        meta = result.get('parse_metadata', {})
        if meta.get('parse_errors', 0) > 0:
            print(f"\n  ⚠ Parse errors: {meta['parse_errors']}")
            warnings = meta.get('warnings', [])[:3]
            for warning in warnings:
                print(f"    - {warning}")

        return True

    except Exception as e:
        print(f"\n✗ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("="*80)
    print("LATTES PARSER MANUAL TEST")
    print("="*80)

    # Show registry
    print(f"\nRegistered parsers:")
    for pattern, parser_class in PARSER_REGISTRY.items():
        print(f"  - {pattern}: {parser_class.__name__}")

    # Find fixtures
    fixtures_dir = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes'

    if not fixtures_dir.exists():
        print(f"\n✗ Fixtures directory not found: {fixtures_dir}")
        return 1

    # Get all HTML files (exclude full_profile)
    fixtures = [
        f for f in sorted(fixtures_dir.glob('*.html'))
        if 'full_profile' not in str(f)
    ]

    print(f"\nFound {len(fixtures)} fixtures")

    # Test a few representative files
    test_files = [
        'Artigos aceitos para publicação.html',
        'Artigos completos publicados em periódicos.html',
        'Capítulos de livros publicados.html',
        'Textos em jornais de notícias_revistas.html',
    ]

    success_count = 0
    total_count = 0

    for test_name in test_files:
        fixture_path = fixtures_dir / test_name
        if fixture_path.exists():
            total_count += 1
            if test_single_file(fixture_path):
                success_count += 1
        else:
            print(f"\n⚠ Fixture not found: {test_name}")

    # Test all remaining with generic parser (just count items)
    print(f"\n{'='*80}")
    print("TESTING ALL FIXTURES (Summary)")
    print(f"{'='*80}\n")

    all_results = []
    for fixture_path in fixtures:
        try:
            result = parse_fixture(fixture_path)
            num_items = len(result.get('items', []))
            parser_type = "Specific" if any(
                pattern in fixture_path.stem.lower()
                for pattern in PARSER_REGISTRY.keys()
            ) else "Generic"

            all_results.append({
                'name': fixture_path.name,
                'items': num_items,
                'parser': parser_type,
                'status': '✓'
            })
        except Exception as e:
            all_results.append({
                'name': fixture_path.name,
                'items': 0,
                'parser': 'Error',
                'status': f'✗ {str(e)[:40]}'
            })

    # Print table
    print(f"{'File':<60} {'Items':>6} {'Parser':>10} {'Status':>10}")
    print("-" * 90)
    for r in all_results:
        print(f"{r['name']:<60} {r['items']:>6} {r['parser']:>10} {r['status']:>10}")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total fixtures: {len(all_results)}")
    print(f"Successful: {sum(1 for r in all_results if r['status'] == '✓')}")
    print(f"Failed: {sum(1 for r in all_results if r['status'].startswith('✗'))}")
    print(f"Total items parsed: {sum(r['items'] for r in all_results)}")

    return 0 if success_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())
