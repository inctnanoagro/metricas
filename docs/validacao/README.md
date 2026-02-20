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

## Como salvar/exportar a validação

Use o botão **"Baixar validação (JSON)"** no topo do viewer: o arquivo gerado inclui as seleções INCT?, as edições rápidas por item e um resumo por seção. O nome do arquivo usa o `lattes_id` (quando disponível) e timestamp para facilitar o retorno ao time técnico.

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

### Validação manual (3 passos)

1. `python3 -m http.server`
2. Abra `http://localhost:8000/docs/validacao/?prefill=4741480538883395`
3. Confira:
   - Seções continuam separadas
   - Colunas mudam por seção (Artigos mostra DOI/ISSN quando houver; Livros/Capítulos mostra ISBN/Editora/Páginas quando houver)
   - Busca e filtros continuam funcionando
