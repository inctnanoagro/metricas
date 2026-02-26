#!/usr/bin/env python
"""Compare Lattes HTML full profiles with final JSON outputs.

This script is **non-destructive**: it only reads existing inputs and writes
new diagnostic files under an output directory.

Usage example:
    python scripts/compare_html_vs_json.py \
        --html-dir data/full_profiles \
        --json-dir outputs \
        --batch <nome_batch> \
        --out outputs/<nome_batch>/diagnostics

See the project docs or scripts/README.md for more details.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from metricas_lattes.batch_full_profile import extract_production_sections_from_html


LOGGER = logging.getLogger(__name__)
LATTES_ID_RE = re.compile(r"^(?P<id>\d{16})")


@dataclass
class SectionComparison:
    section: str
    html_count: int
    json_count: int
    delta: int
    status: str  # "ok" or "mismatch"


@dataclass
class ResearcherReport:
    lattes_id: str
    html_path: str
    json_path: Optional[str]
    sections: List[SectionComparison]
    status: str  # "ok", "mismatch", or "missing_pair"


@dataclass
class SummaryReport:
    batch: str
    html_dir: str
    json_root_dir: str
    out_dir: str
    total_profiles: int
    total_with_pair: int
    total_missing_pair: int
    total_ok: int
    total_mismatch: int
    problematic_sections: Dict[str, int]


def iter_html_profiles(html_dir: Path) -> Iterable[Tuple[str, Path]]:
    """Yield (lattes_id, html_path) for each *_full_profile.html under html_dir.

    The lattes_id is derived from the 16-digit prefix of the filename, when present.
    Files without such a prefix are skipped.
    """

    pattern = "*.full_profile.html"
    for path in sorted(html_dir.rglob(pattern)):
        match = LATTES_ID_RE.match(path.name)
        if not match:
            LOGGER.debug("Skipping HTML without 16-digit prefix: %s", path)
            continue
        lattes_id = match.group("id")
        yield lattes_id, path


def find_json_for_lattes_id(json_batch_dir: Path, lattes_id: str) -> Optional[Path]:
    """Find the JSON file for a given lattes_id in the batch researchers dir.

    Pattern: <batch>/researchers/<lattes_id>__*.json
    Returns the first match if multiple exist.
    """

    pattern = f"{lattes_id}__*.json"
    candidates = sorted((json_batch_dir / "researchers").glob(pattern))
    if not candidates:
        return None
    return candidates[0]


def derive_json_section_counts(json_data: Dict) -> Dict[str, int]:
    """Derive counts per section from the final JSON researcher data.

    We try to respect the taxonomy used by
    `extract_production_sections_from_html`, which returns something like:
        {section_name: {"item_count": int, ...}, ...}

    The JSON structure is expected to contain production items with fields
    such as `production_type`, `source`, and `metadata.sections`.

    This function returns a dict mapping section name -> count.
    """

    counts: Dict[str, int] = {}

    productions = json_data.get("productions") or []
    for prod in productions:
        prod_type = prod.get("production_type")
        source = prod.get("source")
        metadata = prod.get("metadata") or {}

        # `sections` may be a list of section names or uma string,
        # mas em alguns casos a API pode trazer objetos mais ricos.
        # Vamos filtrar tudo para string e, se nada sobrar, cair no fallback.
        sections = metadata.get("sections")
        section_names: List[str] = []
        if isinstance(sections, str):
            section_names = [sections]
        elif isinstance(sections, list):
            for s in sections:
                if isinstance(s, str):
                    section_names.append(s)
                elif isinstance(s, dict):
                    # Se vier um dict, tenta usar algum campo textual comum.
                    label = s.get("section_title") or s.get("name") or s.get("tipo_producao")
                    if isinstance(label, str):
                        section_names.append(label)

        if not section_names:
            # Fallback: derive a synthetic section name from type/source
            parts: List[str] = []
            if isinstance(prod_type, str):
                parts.append(prod_type)
            if isinstance(source, str):
                parts.append(source)
            elif isinstance(source, dict):
                # Tentativa de label textual a partir da provenance
                src_label = source.get("production_type") or source.get("file")
                if isinstance(src_label, str):
                    parts.append(src_label)

            if not parts:
                section_name = "_unknown_"
            else:
                section_name = " / ".join(parts)
            section_names = [section_name]

        for section_name in section_names:
            counts[section_name] = counts.get(section_name, 0) + 1

    return counts


def compare_sections(
    html_sections: Dict[str, Dict], json_counts: Dict[str, int]
) -> List[SectionComparison]:
    """Compare item counts between HTML sections and JSON-derived sections."""

    section_names = set(html_sections.keys()) | set(json_counts.keys())
    comparisons: List[SectionComparison] = []

    for name in sorted(section_names):
        html_count = int(html_sections.get(name, {}).get("item_count", 0))
        json_count = int(json_counts.get(name, 0))
        delta = json_count - html_count
        status = "ok" if delta == 0 else "mismatch"
        comparisons.append(
            SectionComparison(
                section=name,
                html_count=html_count,
                json_count=json_count,
                delta=delta,
                status=status,
            )
        )

    return comparisons


def build_researcher_report(
    lattes_id: str, html_path: Path, json_path: Optional[Path]
) -> ResearcherReport:
    """Build a detailed report for a single researcher."""

    # Extract sections from HTML
    # Returns List[Dict[str, Any]] with keys: section_title, item_count, etc.
    html_sections_list = extract_production_sections_from_html(str(html_path))
    
    # Convert list to dict keyed by section title
    html_sections = {}
    for section in html_sections_list:
        title = section.get("section_title")
        if title:
            html_sections[title] = section

    if json_path is None:
        LOGGER.info("No JSON found for %s", lattes_id)
        return ResearcherReport(
            lattes_id=lattes_id,
            html_path=str(html_path),
            json_path=None,
            sections=[],
            status="missing_pair",
        )

    with json_path.open("r", encoding="utf-8") as f:
        json_data = json.load(f)

    json_counts = derive_json_section_counts(json_data)
    comparisons = compare_sections(html_sections, json_counts)

    if not comparisons:
        status = "ok"
    elif all(c.status == "ok" for c in comparisons):
        status = "ok"
    else:
        status = "mismatch"

    return ResearcherReport(
        lattes_id=lattes_id,
        html_path=str(html_path),
        json_path=str(json_path),
        sections=comparisons,
        status=status,
    )


def write_researcher_report(out_dir: Path, report: ResearcherReport) -> None:
    """Write the per-researcher diagnostic JSON.

    File name pattern: <lattes_id>__diagnostic.json
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report.lattes_id}__diagnostic.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)
    LOGGER.debug("Wrote report for %s to %s", report.lattes_id, out_path)


def write_summary(out_dir: Path, summary: SummaryReport) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summary.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(summary), f, ensure_ascii=False, indent=2)
    LOGGER.info("Wrote summary to %s", out_path)


def generate_summary(
    batch: str,
    html_dir: Path,
    json_root_dir: Path,
    out_dir: Path,
    reports: List[ResearcherReport],
) -> SummaryReport:
    total_profiles = len(reports)
    total_missing_pair = sum(1 for r in reports if r.status == "missing_pair")
    total_with_pair = total_profiles - total_missing_pair

    total_ok = sum(1 for r in reports if r.status == "ok")
    total_mismatch = sum(1 for r in reports if r.status == "mismatch")

    problematic_sections: Dict[str, int] = {}
    for r in reports:
        for sec in r.sections:
            if sec.status == "mismatch":
                problematic_sections[sec.section] = (
                    problematic_sections.get(sec.section, 0) + 1
                )

    return SummaryReport(
        batch=batch,
        html_dir=str(html_dir),
        json_root_dir=str(json_root_dir),
        out_dir=str(out_dir),
        total_profiles=total_profiles,
        total_with_pair=total_with_pair,
        total_missing_pair=total_missing_pair,
        total_ok=total_ok,
        total_mismatch=total_mismatch,
        problematic_sections=problematic_sections,
    )


def run_comparison(
    html_dir: Path, json_root_dir: Path, batch: str, out_dir: Path
) -> None:
    """Main comparison routine.

    This function only reads existing inputs and writes new diagnostics
    under out_dir. It does not modify any existing files.
    """

    html_dir = html_dir.resolve()
    json_root_dir = json_root_dir.resolve()
    out_dir = out_dir.resolve()

    json_batch_dir = json_root_dir / batch

    # Safety check: only run if researchers dir exists.
    researchers_dir = json_batch_dir / "researchers"
    if not researchers_dir.is_dir():
        LOGGER.warning(
            "Batch researchers dir not found: %s. "
            "Skipping comparison (nothing will be written)",
            researchers_dir,
        )
        return

    LOGGER.info("Using HTML dir: %s", html_dir)
    LOGGER.info("Using JSON batch dir: %s", json_batch_dir)
    LOGGER.info("Diagnostics out dir: %s", out_dir)

    reports: List[ResearcherReport] = []

    for lattes_id, html_path in iter_html_profiles(html_dir):
        json_path = find_json_for_lattes_id(json_batch_dir, lattes_id)
        report = build_researcher_report(lattes_id, html_path, json_path)
        reports.append(report)
        write_researcher_report(out_dir, report)

    summary = generate_summary(batch, html_dir, json_root_dir, out_dir, reports)
    write_summary(out_dir, summary)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Lattes HTML full profiles with final JSON outputs.",
    )

    parser.add_argument(
        "--html-dir",
        required=True,
        type=Path,
        help="Directory containing *_full_profile.html files (e.g. data/full_profiles)",
    )

    parser.add_argument(
        "--json-dir",
        required=True,
        type=Path,
        help="Root directory for JSON outputs (e.g. outputs)",
    )

    parser.add_argument(
        "--batch",
        required=True,
        help="Batch name (subdirectory under --json-dir)",
    )

    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help=(
            "Directory for diagnostics (e.g. outputs/<batch>/diagnostics). "
            "Will be created if it does not exist."
        ),
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="[%(levelname)s] %(message)s",
    )

    run_comparison(
        html_dir=args.html_dir,
        json_root_dir=args.json_dir,
        batch=args.batch,
        out_dir=args.out,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
