#!/usr/bin/env python3
"""
Validador batch para fixtures Lattes.

Processa uma pasta inteira de HTMLs, valida contra schema,
e gera relatórios consolidados.

Usage:
    python3 scripts/validate_folder.py --in tests/fixtures/lattes --out outputs
    python3 scripts/validate_folder.py --in tests/fixtures/lattes --out outputs --schema schema/producoes.schema.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metricas_lattes.parser_router import parse_fixture, PARSER_REGISTRY


def load_schema(schema_path: Path) -> dict:
    """Load JSON Schema"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_against_schema(data: dict, schema: dict) -> list:
    """Validate data against JSON Schema"""
    try:
        from jsonschema import Draft7Validator
    except ImportError:
        try:
            from jsonschema import Draft202012Validator as Draft7Validator
        except ImportError:
            return ["jsonschema não instalado - não é possível validar"]

    validator = Draft7Validator(schema)
    errors = []

    for error in validator.iter_errors(data):
        path = '.'.join(str(p) for p in error.path) if error.path else 'root'
        errors.append({
            'path': path,
            'message': error.message
        })

    return errors


def process_file(filepath: Path, schema: dict = None) -> dict:
    """Process a single file and return result"""
    print(f"  Processing: {filepath.name}...", end=" ")

    try:
        # Parse
        result = parse_fixture(filepath)

        # Validate if schema provided
        schema_errors = []
        if schema:
            schema_errors = validate_against_schema(result, schema)

        # Determine success
        success = len(schema_errors) == 0 if schema else True

        if success:
            print(f"✓ OK ({len(result['items'])} items)")
        else:
            print(f"✗ FAIL ({len(schema_errors)} schema errors)")

        return {
            'filepath': str(filepath),
            'filename': filepath.name,
            'success': success,
            'items_count': len(result['items']),
            'schema_errors': schema_errors,
            'result': result
        }

    except Exception as e:
        print(f"✗ ERROR: {str(e)[:50]}")
        return {
            'filepath': str(filepath),
            'filename': filepath.name,
            'success': False,
            'items_count': 0,
            'error': str(e),
            'result': None
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Batch validator for Lattes HTML fixtures",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--in', dest='input_dir', required=True,
        help='Input directory with HTML files'
    )
    parser.add_argument(
        '--out', dest='output_dir', required=True,
        help='Output directory for JSONs and reports'
    )
    parser.add_argument(
        '--schema', dest='schema_path',
        default='schema/producoes.schema.json',
        help='Path to JSON Schema (default: schema/producoes.schema.json)'
    )
    parser.add_argument(
        '--skip-individual', action='store_true',
        help='Skip individual JSON output (only summary + errors)'
    )

    args = parser.parse_args()

    # Paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    schema_path = Path(args.schema_path)

    # Validate inputs
    if not input_dir.exists():
        print(f"✗ Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    # Create output dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load schema
    schema = None
    if schema_path.exists():
        try:
            schema = load_schema(schema_path)
            print(f"✓ Schema loaded: {schema_path}")
        except Exception as e:
            print(f"✗ Error loading schema: {e}", file=sys.stderr)
            return 1
    else:
        print(f"⚠ Schema not found: {schema_path} - skipping validation")

    # Find HTML files
    html_files = [
        f for f in sorted(input_dir.glob('*.html'))
        if not f.name.startswith('._')  # Skip AppleDouble
        and 'full_profile' not in str(f)  # Skip full_profile
    ]

    if not html_files:
        print(f"✗ No HTML files found in {input_dir}", file=sys.stderr)
        return 1

    print(f"\nFound {len(html_files)} HTML files")
    print(f"Output: {output_dir}")
    print()

    # Process files
    results = []
    for filepath in html_files:
        result = process_file(filepath, schema)
        results.append(result)

        # Save individual JSON
        if not args.skip_individual and result['result']:
            output_path = output_dir / f"{filepath.stem}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result['result'], f, indent=2, ensure_ascii=False)

    # Generate summary
    print()
    print("="*60)
    print("SUMMARY")
    print("="*60)

    total = len(results)
    success_count = sum(1 for r in results if r['success'])
    fail_count = total - success_count
    total_items = sum(r['items_count'] for r in results)

    print(f"Total files: {total}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total items extracted: {total_items}")

    summary = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'input_dir': str(input_dir),
            'output_dir': str(output_dir),
            'schema_path': str(schema_path) if schema else None,
            'schema_validation': schema is not None
        },
        'summary': {
            'total_files': total,
            'success': success_count,
            'failed': fail_count,
            'total_items': total_items
        },
        'files': [
            {
                'filename': r['filename'],
                'success': r['success'],
                'items_count': r['items_count'],
                'has_errors': 'error' in r or len(r.get('schema_errors', [])) > 0
            }
            for r in results
        ]
    }

    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Summary saved: {summary_path}")

    # Generate errors report
    errors_report = {
        'metadata': {
            'generated_at': datetime.now().isoformat()
        },
        'errors': [
            {
                'filename': r['filename'],
                'parse_error': r.get('error'),
                'schema_errors': r.get('schema_errors', [])
            }
            for r in results
            if 'error' in r or r.get('schema_errors')
        ]
    }

    if errors_report['errors']:
        errors_path = output_dir / 'errors.json'
        with open(errors_path, 'w', encoding='utf-8') as f:
            json.dump(errors_report, f, indent=2, ensure_ascii=False)

        print(f"✓ Errors report saved: {errors_path}")

        print(f"\nErrors summary:")
        for err in errors_report['errors'][:5]:
            print(f"  - {err['filename']}: ", end="")
            if err.get('parse_error'):
                print(f"parse error")
            else:
                print(f"{len(err['schema_errors'])} schema errors")
    else:
        print(f"\n✓ No errors!")

    print()
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
