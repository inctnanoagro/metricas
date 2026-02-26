# Scripts de Validação

## apply_validation_json.py

Este script aplica os dados validados pelos pesquisadores (exportados do viewer web) de volta aos arquivos JSON originais do pipeline.

### O que ele faz
1. Lê arquivos de validação (`.json`) de um diretório.
2. Identifica o pesquisador correspondente no diretório de outputs do batch.
3. Cruza cada produção pelo `fingerprint_sha1`.
4. Adiciona o bloco `validacao_inct` em cada item, contendo:
   - `pertence_inct`: booleano (True/False).
   - `observacao`: texto (se houver).
   - `edits`: correções manuais (título, ano, etc.).
5. Salva os novos arquivos em uma pasta `validated/`.
6. Gera um relatório global `validation_report.json`.

### Uso

```bash
python scripts/apply_validation_json.py \
  --validation-dir data/validacao_recebida \
  --researchers-dir outputs/dry_run_20260128-142813/researchers \
  --validated-output-dir outputs/dry_run_20260128-142813/validated \
  --backup-dir outputs/dry_run_20260128-142813/backups
```

### Formato de Saída (JSON Enriquecido)

```json
{
  "researcher": { ... },
  "productions": [
    {
      "titulo": "...",
      "validacao_inct": {
        "applied": true,
        "pertence_inct": true,
        "observacao": "Projeto CNPq 123",
        "fingerprint_match": true
      }
    }
  ],
  "meta_validacao_inct": {
    "processed_at": "2026-02-20T...",
    "stats": { "marked_inct_true": 15, ... }
  }
}
```
