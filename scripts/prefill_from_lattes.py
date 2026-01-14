#!/usr/bin/env python3
"""CLI for generating prefill JSON from Lattes HTML"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Temporary: add parent to path until proper packaging/install
sys.path.insert(0, str(Path(__file__).parent.parent))

from metricas_lattes.parsers.artigos import ArtigoParser


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate prefill JSON from Lattes HTML (articles only)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'input_file',
        nargs='?',
        help='Path to Lattes HTML file'
    )
    parser.add_argument(
        '--input',
        dest='input_file_alt',
        help='Path to Lattes HTML file (alternative)'
    )
    parser.add_argument(
        '--pesquisador',
        required=True,
        help='Researcher slug (used for output filename)'
    )

    return parser.parse_args()


def sort_producoes(producoes):
    """Sort productions deterministically by ordem_lattes (None last), then titulo"""
    def sort_key(p):
        ordem = p.ordem_lattes if p.ordem_lattes is not None else float('inf')
        titulo = p.titulo or ""
        return (ordem, titulo)

    return sorted(producoes, key=sort_key)


def main():
    """Main CLI entry point"""
    args = parse_args()

    # Check for conflicting input arguments
    if args.input_file and args.input_file_alt:
        print("Error: cannot specify both positional input and --input flag", file=sys.stderr)
        sys.exit(2)

    # Determine input file
    input_file = args.input_file or args.input_file_alt
    if not input_file:
        print("Error: input file required (positional argument or --input)", file=sys.stderr)
        sys.exit(2)

    input_path = Path(input_file)

    # Check input file exists
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    # Read HTML
    try:
        html_content = input_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error: failed to read input file: {e}", file=sys.stderr)
        sys.exit(2)

    # Parse articles
    parser = ArtigoParser()
    articles = parser.parse_html(html_content)

    # Sort deterministically
    articles_sorted = sort_producoes(articles)

    # Build output structure
    output_data = {
        "pesquisador": args.pesquisador,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_html": input_path.name,
        "producoes": {
            "artigos": [art.to_dict(include_trace=True) for art in articles_sorted]
        },
        "counts": {
            "artigos": len(articles_sorted)
        }
    }

    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs" / "prefill"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write main JSON
    output_file = output_dir / f"{args.pesquisador}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Write errors JSON
    errors_file = output_dir / f"{args.pesquisador}.errors.json"
    errors_data = {
        "pesquisador": args.pesquisador,
        "source_html": input_path.name,
        "errors": parser.errors
    }
    with open(errors_file, 'w', encoding='utf-8') as f:
        json.dump(errors_data, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"✓ Parsed {len(articles_sorted)} article(s)")
    print(f"✓ Output: {output_file}")
    if parser.errors:
        print(f"⚠ {len(parser.errors)} parsing error(s) logged to: {errors_file}")
    else:
        print(f"✓ No errors: {errors_file}")

    sys.exit(0)


if __name__ == "__main__":
    main()
