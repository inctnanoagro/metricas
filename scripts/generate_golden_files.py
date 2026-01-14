#!/usr/bin/env python3
"""
Generate golden files for parser tests.

Golden files are reference outputs that can be used to detect
unintended changes in parser behavior.

Usage:
    python3 scripts/generate_golden_files.py [--limit N]
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metricas_lattes.parser_router import parse_fixture


def generate_golden_file(fixture_path: Path, output_dir: Path, overwrite: bool = False):
    """Generate a golden file for a fixture"""
    output_path = output_dir / (fixture_path.stem + '.json')

    if output_path.exists() and not overwrite:
        print(f"  ⊘ Skipped (exists): {output_path.name}")
        return False

    # Parse fixture
    result = parse_fixture(fixture_path)

    # Write golden file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Generated: {output_path.name} ({len(result['items'])} items)")
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate golden files for parser tests')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing golden files')
    parser.add_argument('--only', type=str, help='Only process files matching this pattern')
    args = parser.parse_args()

    # Setup paths
    fixtures_dir = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes'
    output_dir = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'expected'

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating golden files...")
    print(f"  Fixtures: {fixtures_dir}")
    print(f"  Output: {output_dir}")
    print()

    # Get fixtures
    fixtures = [
        f for f in sorted(fixtures_dir.glob('*.html'))
        if 'full_profile' not in str(f)
    ]

    if args.only:
        fixtures = [f for f in fixtures if args.only.lower() in f.name.lower()]
        print(f"Filtered to {len(fixtures)} files matching '{args.only}'")

    if args.limit:
        fixtures = fixtures[:args.limit]
        print(f"Limited to first {args.limit} files")

    print()

    # Generate golden files
    generated = 0
    skipped = 0

    for fixture_path in fixtures:
        try:
            if generate_golden_file(fixture_path, output_dir, args.overwrite):
                generated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ✗ Failed: {fixture_path.name}: {e}")

    # Summary
    print()
    print(f"{'='*80}")
    print(f"Generated: {generated}")
    print(f"Skipped: {skipped}")
    print(f"Total: {len(fixtures)}")
    print()
    print(f"Golden files saved to: {output_dir}")


if __name__ == '__main__':
    main()
