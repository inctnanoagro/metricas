# apply_validation_json.py

Aplica JSONs de validação (exportados do viewer `docs/validacao`) sobre JSONs de pesquisador, usando:
- `lattes_id` para encontrar o arquivo do pesquisador
- `fingerprint_sha1` para casar item validado com produção

## Uso

```bash
python3 scripts/apply_validation_json.py \
  --validation-dir <dir_json_validacao> \
  --researchers-dir <dir_researchers> \
  --validated-output-dir <dir_saida> \
  [--backup-dir <dir_backup>]
```

## O que o script faz

- Lê todos os `*.json` de `--validation-dir`
- Resolve `lattes_id` (payload `researcher.lattes_id`, com fallback no nome do arquivo)
- Encontra o `researcher_output` correspondente em `--researchers-dir`
- Para cada produção com `fingerprint_sha1` casado, adiciona bloco `validacao_inct`
- Adiciona `meta_validacao_inct` na raiz do JSON do pesquisador
- Salva o JSON final em `--validated-output-dir` preservando estrutura relativa
- Gera `validation_report.json` com contagens globais e por pesquisador

## Backup opcional

Se `--backup-dir` for informado, o script salva:
- cópia dos arquivos de origem em `source/`
- cópia do arquivo de saída anterior (se já existir) em `validated_output_previous/`
