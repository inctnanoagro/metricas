# Scripts

Este diretório contém scripts auxiliares para a pipeline do projeto.

## compare_html_vs_json.py

Script **não-destrutivo** para comparar os perfis HTML completos do Lattes com
os JSONs finais gerados pela pipeline (`batch_full_profile`). Ele:

- percorre `data/full_profiles` (ou outro diretório passado em `--html-dir`)
  em busca de arquivos `*_full_profile.html` com prefixo de 16 dígitos
  (Lattes ID);
- para cada Lattes ID, tenta localizar o JSON correspondente em
  `outputs/<batch>/researchers/<lattes_id>__*.json`;
- para cada par HTML+JSON encontrado, extrai as seções de produção do HTML
  usando `metricas_lattes.batch_full_profile.extract_production_sections_from_html`
  e deriva contagens de itens por seção a partir do JSON (campos
  `production_type`/`source`/`metadata.sections`);
- compara as contagens por seção e grava um relatório por pesquisador em
  `outputs/<batch>/diagnostics/<lattes_id>__diagnostic.json`;
- gera um `summary.json` em `outputs/<batch>/diagnostics/` com visão geral
  (quantos perfis com par HTML+JSON em que tudo bate, quantos com mismatch,
  quantos sem par, e em quais seções existem discrepâncias).

O script não altera nenhum arquivo existente em `data/`, `outputs/` ou
`metricas_lattes/` — apenas lê e grava novos relatórios na pasta de
`diagnostics` informada.

### Exemplo de uso

Dentro do repositório `metricas`:

```bash
python3 scripts/compare_html_vs_json.py \
  --html-dir data/full_profiles \
  --json-dir outputs \
  --batch dry_run_20260128-142127 \
  --out outputs/dry_run_20260128-142127/diagnostics
```

> Observação: o script só roda a comparação se existir o diretório
> `outputs/<batch>/researchers`. Caso não exista, apenas registra um aviso no
> log e termina sem escrever nada.
