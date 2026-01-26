#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*"
}

usage() {
  cat <<'EOF'
Uso: scripts/publicar_validacao.sh [--in <pasta_htmls>] [--years "2024,2025"] [--dry-run] [--no-sync] [--no-validation]

Opcoes:
  --in <pasta_htmls>   Pasta com full_profile.html (default: data/full_profiles_20250114 se existir)
  --years "2024,2025"  Filtro de anos (repassa para batch_full_profile; use 'all' para desativar)
  --dry-run            Gera apenas outputs/dry_run_<timestamp> (sem validation_pack e sem sync)
  --no-sync            Nao sincroniza docs/prefill
  --no-validation      Nao gera validation_pack (apenas batch + sync)
EOF
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

if [[ ! -f "venv/bin/activate" ]]; then
  echo "Erro: venv/bin/activate nao encontrado. Crie o venv em ./venv primeiro." >&2
  exit 1
fi

# shellcheck disable=SC1091
source venv/bin/activate

input_dir=""
years=""
dry_run=false
no_sync=false
no_validation=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in)
      input_dir="$2"
      shift 2
      ;;
    --years)
      years="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --no-sync)
      no_sync=true
      shift
      ;;
    --no-validation)
      no_validation=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Erro: argumento desconhecido: $1" >&2
      usage
      exit 1
      ;;
  esac
 done

if [[ -z "$input_dir" ]]; then
  if [[ -d "data/full_profiles_20250114" ]]; then
    input_dir="data/full_profiles_20250114"
  else
    echo "Erro: informe --in <pasta_htmls> (default data/full_profiles_20250114 nao existe)." >&2
    exit 1
  fi
fi

if [[ ! -d "$input_dir" ]]; then
  echo "Erro: pasta de entrada nao existe: $input_dir" >&2
  exit 1
fi

stamp="$(date +"%Y%m%d-%H%M%S")"
output_dry="outputs/dry_run_${stamp}"
researchers_dir="$output_dry/researchers"

log "Batch: $input_dir -> $output_dry"
cmd=(python3 -m metricas_lattes.batch_full_profile --in "$input_dir" --out "$output_dry" --schema "schema/producoes.schema.json")
if [[ -n "$years" ]]; then
  cmd+=(--years "$years")
fi
"${cmd[@]}"

if [[ "$dry_run" == true ]]; then
  count=$(find "$researchers_dir" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')
  log "Dry-run: pulando validation_pack e sync."
  cat <<EOF
Resumo
- batch_out: $output_dry
- researchers_dir: $researchers_dir
- pesquisadores: $count
- viewer: http://localhost:8000/docs/validacao/?prefill=<lattes_id>
- lista: http://localhost:8000/docs/validacao/lista.html
EOF
  exit 0
fi

validation_dir="outputs/validation_${stamp}"
if [[ "$no_validation" == false ]]; then
  log "Validation pack: $researchers_dir -> $validation_dir"
  python3 -m metricas_lattes.exports.validation_pack \
    --in "$researchers_dir" \
    --out "$validation_dir" \
    --format html xlsx
else
  log "No-validation: pulando validation_pack."
fi

synced_count=0
if [[ "$no_sync" == false ]]; then
  log "Sync: $researchers_dir -> docs/prefill"
  python3 scripts/sync_validation_to_pages.py --in "$researchers_dir"
  if [[ -f "docs/prefill/manifest.json" ]]; then
    synced_count=$(python3 - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path('docs/prefill/manifest.json').read_text(encoding='utf-8'))
print(len(manifest.get('by_lattes_id', {})))
PY
)
  fi
else
  log "No-sync: pulando sync para docs/prefill."
fi

cat <<EOF
Resumo
- batch_out: $output_dry
- researchers_dir: $researchers_dir
- validation_out: $validation_dir
- synced_researchers: $synced_count
- viewer: http://localhost:8000/docs/validacao/?prefill=<lattes_id>
- lista: http://localhost:8000/docs/validacao/lista.html
EOF
