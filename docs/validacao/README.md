# Validação (viewer)

Este viewer carrega um JSON de produções e renderiza em HTML **preservando a ordem original do array**.

## Acessos

- Viewer:
  - `https://inctnanoagro.github.io/metricas/validacao/?prefill=4741480538883395__leonardo-fernandes-fraceto.json`
  - `https://inctnanoagro.github.io/metricas/validacao/?prefill=4741480538883395` (resolve via `docs/prefill/manifest.json`)
  - `https://inctnanoagro.github.io/metricas/validacao/?source=https://.../algum.json`
- Índice (lista):
  - `https://inctnanoagro.github.io/metricas/validacao/lista.html`

## Parâmetros

- `prefill=`
  - `prefill=<filename>.json` → busca em `docs/prefill/<filename>.json`
  - `prefill=<lattes_id>` (16 dígitos) → resolve via `docs/prefill/manifest.json`
- `source=`
  - URL absoluta de um JSON (prioridade sobre `prefill`)

## Como publicar JSONs no Pages

1. Gere o batch normalmente.
2. Sincronize:

```bash
python3 scripts/sync_validation_to_pages.py --in outputs/<batch>/researchers
```

Isso copia os JSONs para `docs/prefill/` e recria `docs/prefill/manifest.json`.

## Teste local

Sirva os arquivos por HTTP para testar querystring:

```bash
python3 -m http.server
```

Depois acesse:

- `http://localhost:8000/docs/validacao/?prefill=<filename>.json`
- `http://localhost:8000/docs/validacao/lista.html`
