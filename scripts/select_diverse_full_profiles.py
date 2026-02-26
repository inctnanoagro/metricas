#!/usr/bin/env python3
"""
Selects 3 diverse full_profile HTML files based on file size:
smallest, median, and largest.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import List


def select_diverse_profiles(input_dir: Path, count: int = 3) -> List[Path]:
    html_files = [
        path
        for path in input_dir.glob("*.html")
        if path.is_file() and not path.name.startswith("._")
    ]
    if not html_files:
        return []

    html_files.sort(key=lambda path: path.stat().st_size)
    indices = [0, len(html_files) // 2, len(html_files) - 1]
    selected = []
    seen = set()
    for index in indices:
        if index < 0 or index >= len(html_files):
            continue
        candidate = html_files[index]
        if candidate in seen:
            continue
        selected.append(candidate)
        seen.add(candidate)
        if len(selected) >= count:
            break
    return selected


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select diverse full_profile HTMLs by size.",
    )
    parser.add_argument(
        "--in",
        dest="input_dir",
        default="data/full_profiles_20250114",
        help="Input directory with full_profile HTML files",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy selected HTMLs into an output folder",
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        default=None,
        help="Output directory for copies (default: outputs/_sample_full_profiles/<timestamp>/)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Erro: pasta de entrada nao existe: {input_dir}")
        return 1

    selected = select_diverse_profiles(input_dir)
    if not selected:
        print(f"Nenhum HTML encontrado em {input_dir}")
        return 1

    if args.copy:
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_dir = Path("outputs") / "_sample_full_profiles" / stamp
        output_dir.mkdir(parents=True, exist_ok=True)
        for path in selected:
            shutil.copy2(path, output_dir / path.name)
        print(str(output_dir))
    else:
        for path in selected:
            print(str(path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
