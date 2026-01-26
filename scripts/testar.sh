#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Uso: ./scripts/testar.sh [--in <dir_html>] [--out <dir_outputs_base>] [--schema <schema_path>] [--dry-run]

Defaults:
  --in     data/full_profiles_20250114
  --out    outputs
  --schema schema/producoes.schema.json
EOF
}

INPUT_DIR="data/full_profiles_20250114"
OUTPUT_BASE="outputs"
SCHEMA_PATH="schema/producoes.schema.json"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in)
      INPUT_DIR="${2:-}"
      shift 2
      ;;
    --out)
      OUTPUT_BASE="${2:-}"
      shift 2
      ;;
    --schema)
      SCHEMA_PATH="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Erro: argumento desconhecido: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "Erro: .venv nao encontrado em ./.venv. Crie o venv antes de rodar." >&2
  exit 1
fi

if [[ ! -f "$SCHEMA_PATH" ]]; then
  echo "Erro: schema nao encontrado em $SCHEMA_PATH" >&2
  exit 1
fi

if [[ ! -d "$INPUT_DIR" ]]; then
  if [[ -d "data" ]]; then
    candidate=$(find data -maxdepth 2 -type f -name "*.html" ! -name "._*" ! -name ".DS_Store" 2>/dev/null | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -nr | head -n 1 | awk '{print $2}')
    if [[ -n "$candidate" ]]; then
      echo "Erro: pasta de entrada nao encontrada: $INPUT_DIR" >&2
      echo "Sugestao: use --in $candidate" >&2
      exit 1
    fi
  fi
  echo "Erro: pasta de entrada nao encontrada: $INPUT_DIR" >&2
  exit 1
fi

html_count=$(find "$INPUT_DIR" -type f -name "*.html" ! -name "._*" ! -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$html_count" -eq 0 ]]; then
  echo "Erro: nenhum .html encontrado em $INPUT_DIR" >&2
  exit 1
fi

timestamp=$(date "+%Y%m%d-%H%M%S")
batch_out="$OUTPUT_BASE/dry_run_${timestamp}"
validation_out="$OUTPUT_BASE/validation_${timestamp}"

mkdir -p "$batch_out"

source .venv/bin/activate

python3 -m metricas_lattes.batch_full_profile \
  --in "$INPUT_DIR" \
  --out "$batch_out" \
  --schema "$SCHEMA_PATH"

researchers_dir="$batch_out/researchers"
if [[ ! -d "$researchers_dir" ]]; then
  echo "Erro: pasta researchers nao foi criada em $researchers_dir" >&2
  exit 1
fi

json_count=$(find "$researchers_dir" -type f -name "*.json" ! -name "._*" ! -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$json_count" -eq 0 ]]; then
  echo "Erro: nenhum JSON gerado em $researchers_dir" >&2
  exit 1
fi

export_html="nao"
export_xlsx="nao"

if [[ "$DRY_RUN" == "false" ]]; then
  mkdir -p "$validation_out"
  python3 -m metricas_lattes.exports.validation_pack \
    --in "$researchers_dir" \
    --out "$validation_out" \
    --format html xlsx

  if find "$validation_out" -type f -name "VALIDACAO.html" ! -name "._*" 2>/dev/null | grep -q .; then
    export_html="sim"
  fi
  if find "$validation_out" -type f -name "VALIDACAO.xlsx" ! -name "._*" 2>/dev/null | grep -q .; then
    export_xlsx="sim"
  fi
else
  validation_out="(dry-run)"
fi

echo "OK"
echo "Batch output: $batch_out"
echo "Validation output: ${validation_out}"
echo "JSONs gerados em researchers/: $json_count"
echo "Export HTML: $export_html"
echo "Export XLSX: $export_xlsx"
