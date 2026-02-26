#!/usr/bin/env python3
"""
Aplica validações (JSONs exportados pelo viewer) aos arquivos researcher_output.json.

Este script:
1. Lê os arquivos de validação em --validation-dir.
2. Encontra o researcher_output.json correspondente em --researchers-dir (via lattes_id).
3. Cruza os itens por `fingerprint_sha1` e aplica as marcações (pertence_inct, observacao).
4. Gera novos JSONs enriquecidos em --validated-output-dir.
5. Gera um relatório consolidado `validation_report.json`.

Uso:
    python scripts/apply_validation_json.py \
        --validation-dir data/validacao \
        --researchers-dir outputs/batch/researchers \
        --validated-output-dir outputs/batch/validated
"""

import argparse
import json
import logging
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configuração de log
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_lattes_id_from_validation(data: Dict[str, Any]) -> Optional[str]:
    # Tenta pegar do objeto researcher
    researcher = data.get("researcher")
    if isinstance(researcher, dict) and "lattes_id" in researcher:
        return str(researcher["lattes_id"])
    
    # Fallback: tentar extrair do prefill_source se for um ID
    source = data.get("prefill_source")
    if source and isinstance(source, str):
        # Se for apenas números e tiver 16 digitos
        clean = source.strip()
        if len(clean) == 16 and clean.isdigit():
            return clean
            
    return None


def get_lattes_id_from_researcher_output(data: Dict[str, Any]) -> Optional[str]:
    researcher = data.get("researcher")
    if isinstance(researcher, dict) and "lattes_id" in researcher:
        return str(researcher["lattes_id"])
    return None


def build_validation_map(validation_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Cria um mapa: fingerprint_sha1 -> item de validação.
    """
    mapping = {}
    for item in validation_items:
        fp = item.get("fingerprint_sha1")
        if fp:
            mapping[fp] = item
    return mapping


def apply_validation_to_researcher(
    researcher_data: Dict[str, Any],
    validation_data: Dict[str, Any],
    validation_file_path: Path
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Retorna (novo_json_pesquisador, estatisticas_deste_arquivo).
    """
    # Copia profunda para não alterar o original se fosse mutável (aqui carregamos de novo)
    # Mas como estamos gerando um novo dict, vamos construindo.
    output_data = researcher_data.copy()
    
    # Prepara mapa de validação
    val_items = validation_data.get("items", [])
    val_map = build_validation_map(val_items)
    
    # Estatísticas
    stats = {
        "total_items": 0,
        "matched": 0,
        "marked_inct_true": 0,
        "marked_inct_false": 0,
        "unmarked": 0,
        "sections": defaultdict(lambda: {"total": 0, "matched": 0, "inct": 0})
    }
    
    processed_productions = []
    
    productions = researcher_data.get("productions", [])
    for item in productions:
        stats["total_items"] += 1
        
        # Identifica seção para estatística
        section = item.get("production_type", "Unknown")
        stats["sections"][section]["total"] += 1
        
        fp = item.get("fingerprint_sha1")
        
        # Bloco de validação a ser inserido
        validacao_block = {
            "applied": False,
            "pertence_inct": None,
            "observacao": None,
            "edits": None,
            "source_validation_file": validation_file_path.name,
            "applied_at": datetime.now(timezone.utc).isoformat()
        }
        
        if fp and fp in val_map:
            # Match!
            val_item = val_map[fp]
            
            # Normaliza campos do schema de validação
            # O schema proposto usa 'pertence_inct', mas o viewer atual pode exportar 'selected'
            pertence = val_item.get("pertence_inct")
            if pertence is None:
                pertence = val_item.get("selected") # Fallback legado
            
            obs = val_item.get("observacao")
            edits = val_item.get("edits")
            
            validacao_block.update({
                "applied": True,
                "pertence_inct": pertence,
                "observacao": obs,
                "edits": edits,
                "fingerprint_match": True
            })
            
            stats["matched"] += 1
            stats["sections"][section]["matched"] += 1
            
            if pertence is True:
                stats["marked_inct_true"] += 1
                stats["sections"][section]["inct"] += 1
            elif pertence is False:
                stats["marked_inct_false"] += 1
            else:
                stats["unmarked"] += 1
                
        else:
            # Sem match (item novo ou fingerprint mudou ou não validado)
            validacao_block["fingerprint_match"] = False
            stats["unmarked"] += 1
            
        # Injeta o bloco no item
        item_copy = item.copy()
        item_copy["validacao_inct"] = validacao_block
        processed_productions.append(item_copy)
        
    output_data["productions"] = processed_productions
    
    # Adiciona metadados de validação no topo
    output_data["meta_validacao_inct"] = {
        "schema_version": "1.0.0",
        "source_validation_file": validation_file_path.name,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "stats": {k: v for k, v in stats.items() if k != "sections"}
    }
    
    return output_data, stats


def main():
    parser = argparse.ArgumentParser(description="Aplica validações JSON aos outputs dos pesquisadores.")
    parser.add_argument("--validation-dir", required=True, type=Path, help="Diretório com JSONs de validação.")
    parser.add_argument("--researchers-dir", required=True, type=Path, help="Diretório com researcher_output.json originais.")
    parser.add_argument("--validated-output-dir", required=True, type=Path, help="Onde salvar os JSONs enriquecidos.")
    parser.add_argument("--backup-dir", type=Path, help="Se informado, faz backup dos arquivos originais antes de processar.")
    
    args = parser.parse_args()
    
    if not args.validation_dir.exists():
        logger.error(f"Diretório de validação não encontrado: {args.validation_dir}")
        sys.exit(1)
        
    if not args.researchers_dir.exists():
        logger.error(f"Diretório de pesquisadores não encontrado: {args.researchers_dir}")
        sys.exit(1)
        
    args.validated_output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.backup_dir:
        args.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup ativado em: {args.backup_dir}")

    # Indexar researcher_outputs por lattes_id
    logger.info("Indexando arquivos de pesquisadores...")
    researcher_map = {} # lattes_id -> path
    for f in args.researchers_dir.glob("*.json"):
        try:
            data = load_json(f)
            lid = get_lattes_id_from_researcher_output(data)
            if lid:
                researcher_map[lid] = f
        except Exception as e:
            logger.warning(f"Erro ao ler {f}: {e}")

    logger.info(f"Encontrados {len(researcher_map)} arquivos de pesquisadores válidos.")

    # Processar validações
    validation_files = list(args.validation_dir.glob("*.json"))
    logger.info(f"Encontrados {len(validation_files)} arquivos de validação.")
    
    global_stats = {
        "files_processed": 0,
        "files_matched": 0,
        "total_items_validated": 0,
        "total_inct_true": 0,
        "by_section": defaultdict(lambda: {"total": 0, "inct": 0})
    }
    
    for val_file in validation_files:
        try:
            val_data = load_json(val_file)
            lid = get_lattes_id_from_validation(val_data)
            
            if not lid:
                logger.warning(f"Ignorando {val_file.name}: não foi possível identificar lattes_id.")
                continue
                
            if lid not in researcher_map:
                logger.warning(f"Ignorando {val_file.name}: lattes_id {lid} não encontrado em researchers-dir.")
                continue
                
            # Temos par!
            target_file = researcher_map[lid]
            researcher_data = load_json(target_file)
            
            # Backup se solicitado
            if args.backup_dir:
                shutil.copy2(target_file, args.backup_dir / target_file.name)
            
            # Aplica validação
            new_data, stats = apply_validation_to_researcher(researcher_data, val_data, val_file)
            
            # Salva
            out_path = args.validated_output_dir / target_file.name
            save_json(out_path, new_data)
            
            # Atualiza stats globais
            global_stats["files_processed"] += 1
            global_stats["files_matched"] += 1
            global_stats["total_items_validated"] += stats["matched"]
            global_stats["total_inct_true"] += stats["marked_inct_true"]
            
            for sec, s_data in stats["sections"].items():
                global_stats["by_section"][sec]["total"] += s_data["total"]
                global_stats["by_section"][sec]["inct"] += s_data["inct"]
                
            logger.info(f"Processado: {lid} -> {out_path.name} (INCT: {stats['marked_inct_true']})")
            
        except Exception as e:
            logger.error(f"Erro processando {val_file.name}: {e}")

    # Salva relatório global
    report_path = args.validated_output_dir / "validation_report.json"
    save_json(report_path, global_stats)
    logger.info(f"Relatório global salvo em: {report_path}")
    logger.info("Concluído.")

if __name__ == "__main__":
    main()
