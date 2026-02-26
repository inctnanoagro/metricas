# Manual Técnico e Operacional - Métricas INCT (Fev/2026)

> **Status:** Estável / Em Produção  
> **Arquitetura:** Ingestão Batch -> Validação Web (Pages) -> Aplicação (Loopback)

Este documento mapeia o funcionamento do sistema de métricas, scripts de manutenção e o fluxo de validação dos pesquisadores. Use este guia antes de alterar qualquer pipeline.

---

## 1. Arquitetura do Pipeline

O sistema funciona em **4 estágios**:

1.  **Ingestão (Batch):** `HTML Lattes` -> `JSON Canônico`.
2.  **Diagnóstico:** Validação técnica (HTML vs JSON).
3.  **Validação Humana:** GitHub Pages (Viewer) -> `JSON Validado`.
4.  **Aplicação:** `JSON Validado` -> `JSON Enriquecido` (Database final).

---

## 2. Ingestão (Batch Full Profile)

O script principal que transforma o caos do HTML em dados estruturados.

- **Script:** `metricas_lattes/batch_full_profile.py`
- **Entrada:** Pasta com arquivos `*full_profile.html`.
- **Saída:** Pasta `outputs/<batch>/researchers/*.json`.

### Regras de Negócio Críticas (O "Recorte")
Ao contrário de um parser puro, este batch aplica **filtros de negócio**:
1.  **Filtro de Ano:** Por padrão (e no dry_run de jan/2026), **apenas produções de 2024 e 2025** são mantidas. Todo o histórico anterior é descartado.
    - *Isso explica a redução drástica de contagem de itens (ex: 300 artigos no HTML -> 30 no JSON).*
2.  **Itens sem Ano:** Se o parser não conseguir inferir o ano (pelo campo ou regex no texto), o item é descartado.
    - *Diagnóstico:* Menos de 0,15% dos itens sofrem disso.

---

## 3. Scripts de Diagnóstico

Ferramentas criadas para garantir que o parser não está "comendo" dados indevidamente.

### 3.1. Comparador HTML vs JSON
- **Script:** `scripts/compare_html_vs_json.py`
- **Função:** Conta quantos itens existem em cada seção do HTML original e compara com o JSON gerado.
- **Uso:**
  ```bash
  python scripts/compare_html_vs_json.py \
    --html-dir data/full_profiles_20250114 \
    --json-dir outputs \
    --batch dry_run_20260128-142813 \
    --out outputs/dry_run.../diagnostics
  ```
- **Interpretação:** É normal haver `mismatch` (diferença) se o batch tiver filtro de anos ativo. O script serve para detectar seções vazias ou erros de parser grosseiros.

### 3.2. Scanner de Anos Perdidos
- **Script:** `scripts/scan_missing_years.py`
- **Função:** Varre os HTMLs e lista quais produções não têm ano identificável.
- **Resultado (2025):** Apenas ~28 itens em 21.000 não tiveram ano.

---

## 4. Sistema de Validação (O Viewer)

O pesquisador não edita o repo. Ele usa uma interface web estática.

- **Código:** `docs/validacao/index.html` (Hospedado no GitHub Pages).
- **Fonte de Dados:** Lê os JSONs da pasta `docs/prefill/`.
- **Sync:** O script `scripts/sync_validation_to_pages.py` copia os outputs do batch para a pasta `docs/prefill`.

### O JSON Exportado (Schema de Validação v1.0.0)
Quando o pesquisador clica em "Baixar Validação", o navegador gera um JSON com:
- `pertence_inct`: booleano (True/False).
- `marked_inct` / `unmarked`: contadores.
- `items`: lista preservando a ordem original, chaveada por `fingerprint_sha1`.
- `observacao`: campo reservado para notas (ainda não exposto na UI, mas suportado no schema).

> **Nota de Compatibilidade:** O viewer mantém o campo legado `selected` junto com o novo `pertence_inct` para não quebrar versões antigas.

---

## 5. Pipeline de Aplicação (O Retorno)

Como trazer os dados validados de volta para o sistema.

- **Script:** `scripts/apply_validation_json.py`
- **Entrada:** Uma pasta contendo os JSONs que os pesquisadores enviaram.
- **Lógica:**
  1. Identifica o pesquisador pelo `lattes_id`.
  2. Carrega o `researcher_output.json` original.
  3. Usa o `fingerprint_sha1` para casar cada item.
  4. Injera o bloco `validacao_inct` dentro de cada produção.
- **Saída:** Novos arquivos em `outputs/<batch>/validated/`.

**Comando:**
```bash
python scripts/apply_validation_json.py \
  --validation-dir data/validacao_recebida \
  --researchers-dir outputs/dry_run.../researchers \
  --validated-output-dir outputs/dry_run.../validated
```

---

## 6. Glossário de Variáveis

- **fingerprint_sha1:** Hash único de uma produção (gerado a partir do título normalizado). É a chave-mestra para cruzar dados.
- **lattes_id:** 16 dígitos.
- **production_type:** Nome da seção (ex: "Artigos completos...").
- **dry_run:** Nome dado aos lotes de processamento de teste.

---

*Documento gerado por Case (OpenClaw) em 19/02/2026.*
