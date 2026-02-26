"""Diagnóstico de itens de produção sem ano inferível.

Percorre um diretório de perfis HTML full_profile, extrai as seções de
produções, faz o parse com a infraestrutura existente e aplica a mesma
lógica de inferência de ano usada em `filter_productions_by_year`
(`_infer_year_from_item`).

Saída: JSON consolidado com contagens por `production_type`.

Importante: este script é somente diagnóstico e não altera nenhum
comportamento da pipeline nem os JSONs finais.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from metricas_lattes.batch_full_profile import (
    _infer_year_from_item,
    _normalize_section_label,
    add_provenance_to_items,
    extract_production_sections_from_html,
    parse_section_html,
    _apply_citacao_fallbacks,
)


def scan_directory(html_dir: Path) -> Dict[str, Any]:
    """Percorre todos os HTMLs em `html_dir` e gera estatísticas.

    Retorna um dicionário com:
    - total_items
    - total_sem_ano
    - por_tipo: {production_type: {"total": int, "sem_ano": int}}
    """

    html_files = sorted(
        [p for p in html_dir.iterdir() if p.suffix.lower() == ".html"]
    )

    total_items = 0
    total_sem_ano = 0
    por_tipo_total: Counter[str] = Counter()
    por_tipo_sem_ano: Counter[str] = Counter()

    for html_path in html_files:
        print(f"Processando {html_path.name}...")

        sections_html = extract_production_sections_from_html(html_path)

        # Usamos uma pasta temporária por arquivo, como em batch_full_profile
        import tempfile

        temp_dir = Path(tempfile.mkdtemp(prefix="metricas_diag_"))
        try:
            all_items: List[Dict[str, Any]] = []

            for section in sections_html:
                section_title = section["section_title"]
                section_label = _normalize_section_label(section_title)
                if not section_label:
                    section_label = "Produções"

                section_html = section["html_content"]

                parsed = parse_section_html(section_html, section_title, temp_dir)

                items_with_provenance = add_provenance_to_items(
                    parsed["items"],
                    lattes_id="unknown",  # apenas diagnóstico; ID real não é necessário
                    source_file=html_path.name,
                    production_type=section_label,
                )

                all_items.extend(items_with_provenance)
        finally:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir)

        # Aplicar os mesmos fallbacks de citação antes de tentar inferir ano
        _apply_citacao_fallbacks(all_items)

        for item in all_items:
            total_items += 1

            src = item.get("source") or {}
            prod_type = src.get("production_type") or item.get("production_type") or "<sem_tipo>"

            por_tipo_total[prod_type] += 1

            year = _infer_year_from_item(item)
            if year is None:
                total_sem_ano += 1
                por_tipo_sem_ano[prod_type] += 1

    # Montar estrutura final
    por_tipo: Dict[str, Dict[str, int]] = {}
    for tipo in sorted(por_tipo_total.keys() | por_tipo_sem_ano.keys()):
        por_tipo[tipo] = {
            "total": int(por_tipo_total.get(tipo, 0)),
            "sem_ano": int(por_tipo_sem_ano.get(tipo, 0)),
        }

    return {
        "html_dir": str(html_dir),
        "total_items": int(total_items),
        "total_sem_ano": int(total_sem_ano),
        "por_tipo": por_tipo,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Diagnosticar itens de produção sem ano inferível",
    )
    parser.add_argument(
        "html_dir",
        type=Path,
        help="Diretório com arquivos *.full_profile.html (ex.: data/full_profiles_20250114)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/diagnostics_missing_years.json"),
        help="Caminho do arquivo JSON de saída (default: outputs/diagnostics_missing_years.json)",
    )

    args = parser.parse_args(argv)

    html_dir: Path = args.html_dir
    out_path: Path = args.output

    if not html_dir.is_dir():
        raise SystemExit(f"Diretório não encontrado: {html_dir}")

    result = scan_directory(html_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print()
    print("Resumo do diagnóstico:")
    print(f"  Diretório: {result['html_dir']}")
    print(f"  Total de itens: {result['total_items']}")
    print(f"  Itens sem ano inferível: {result['total_sem_ano']}")
    print("  Por tipo de produção:")
    for tipo, stats in result["por_tipo"].items():
        print(
            f"    - {tipo}: total={stats['total']}, "
            f"sem_ano={stats['sem_ano']}"
        )


if __name__ == "__main__":  # pragma: no cover
    main()
