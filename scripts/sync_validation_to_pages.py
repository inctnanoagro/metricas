#!/usr/bin/env python3
"""Sync validation JSONs into docs/prefill and generate manifest.json."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, Optional


def extract_lattes_id(filename: str) -> Optional[str]:
    """Extract 16-digit lattes_id from <id>__*.json filenames."""
    base = Path(filename).name
    if '__' not in base:
        return None
    prefix = base.split('__', 1)[0]
    if len(prefix) != 16 or not prefix.isdigit():
        return None
    return prefix


def build_manifest(id_to_filename: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Build deterministic manifest sorted by lattes_id."""
    ordered = {key: id_to_filename[key] for key in sorted(id_to_filename)}
    return {"by_lattes_id": ordered}


def sync_validation_to_pages(input_dir: Path, output_dir: Path) -> Dict[str, Dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    id_to_filename: Dict[str, str] = {}

    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() != '.json':
            continue
        lattes_id = extract_lattes_id(path.name)
        if not lattes_id:
            print(f"Ignorando arquivo sem lattes_id valido: {path.name}")
            continue
        dest = output_dir / path.name
        shutil.copy2(path, dest)
        if lattes_id in id_to_filename and id_to_filename[lattes_id] != path.name:
            print(
                "Aviso: lattes_id duplicado. Substituindo "
                f"{id_to_filename[lattes_id]} por {path.name}."
            )
        id_to_filename[lattes_id] = path.name

    manifest = build_manifest(id_to_filename)
    (output_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync validation JSONs into docs/prefill and generate manifest.json"
    )
    parser.add_argument(
        "--in",
        dest="input_dir",
        required=True,
        help="Input dir with researchers JSONs (e.g., outputs/<batch>/researchers)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser()
    if not input_dir.exists():
        raise SystemExit(f"Input dir not found: {input_dir}")

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / 'docs' / 'prefill'

    manifest = sync_validation_to_pages(input_dir, output_dir)
    print(
        f"Sincronizado: {len(manifest['by_lattes_id'])} arquivos -> {output_dir}"
    )


if __name__ == '__main__':
    main()
