# Schema do JSON de validação

Este documento descreve o **formato de saída** do botão **"Baixar validação (JSON)"** do viewer em `docs/validacao/` e propõe um schema estável para uso pelo time técnico.

> Status em fev/2026: o código atual já gera um JSON muito próximo do schema proposto abaixo. Onde houver diferenças, isso está marcado em **Observações de implementação**.

---

## Visão geral

O JSON de validação representa:

1. **Metadados** da exportação e do pesquisador
2. **Lista de produções**, preservando a ordem do prefill e incluindo, por item:
   - dados essenciais da produção
   - marcação "Pertence ao INCT?" (bool)
   - edições feitas pelo pesquisador (campos corrigidos)
   - campo reservado para observações livres
3. **Resumo por seção**, indicando quantas produções foram marcadas / não marcadas em cada tipo de produção.

---

## Schema proposto (alto nível)

```jsonc
{
  "schema_version_validacao": "1.0.0",      // versão do schema DESTE arquivo de validação
  "prefill_schema_version": "2.0.0",        // copiado de prefill.schema_version

  "researcher": {
    "lattes_id": "4741480538883395",
    "full_name": "Nome completo",
    "slug": "nome-completo",               // opcional, herdado do prefill
    "last_update": "27/12/2025"            // opcional, herdado do prefill
  },

  "prefill_source": "...",                 // de onde veio o JSON original (URL ou nome do arquivo)
  "exported_at": "2026-02-19T22:34:12Z",   // timestamp ISO da exportação

  "summary": [
    {
      "section": "Artigos completos publicados em periódicos",
      "production_type": "temp__artigos-completos-publicados-em-periodicos", // quando disponível no prefill.metadata.sections
      "total": 36,                 // total de itens da seção no conjunto filtrado
      "marked_inct": 20,          // quantos foram marcados como pertencentes ao INCT
      "unmarked": 16              // total - marked_inct
    }
    // ...demais seções
  ],

  "items": [
    {
      "fingerprint_sha1": "91ffe6c5fa...", // identificador estável da produção (quando disponível)
      "item_id": "Artigos completos publicados em periódicos::3::Delivering metribuzin...", // fallback determinístico (quando não houver fingerprint)

      "pertence_inct": true,               // marcação "INCT?" feita pelo pesquisador
      "observacao": "Uso direto em projeto XYZ do INCT.",

      "production_type": "Artigos completos publicados em periódicos", // rótulo exibido na UI
      "section_tipo_producao": "temp__artigos-completos-publicados-em-periodicos", // opcional: código técnico da seção, quando disponível

      // Campos originais essenciais (como exibidos ao pesquisador)
      "titulo": "Delivering metribuzin from biodegradable nanocarriers...",
      "ano": 2025,
      "mes": null,
      "doi": "10.1016/j.ijbiomac.2024.138153",       // quando existir
      "veiculo": "Environmental Science-Nano",
      "autores": "AUTOR A; AUTOR B; ...",

      // Campos opcionais que podem existir em alguns tipos de produção
      "issn": "1234-5678",
      "isbn": "978-85-123-4567-8",
      "url": "https://...",
      "volume": "10",
      "numero": "2",
      "paginas": "123-145",
      "editora": "Editora X",
      "local": "Cidade/UF",
      "organizadores": "Nome do organizador, ...",
      "tipo_orientacao": "Doutorado em andamento",
      "natureza": "Trabalho de conclusão",

      // Campos técnicos internos para reprocessamento, quando necessário
      "raw": "...",                     // texto bruto usado na extração
      "source_file": "...html",         // arquivo HTML Lattes original

      // Edições feitas pelo pesquisador via modal de edição rápida
      "edits": {
        "titulo": "Título corrigido",
        "veiculo": "Veículo corrigido",
        "ano": 2024,
        "doi": "10.1234/xyz.2024.0001",
        "autores": "Lista de autores corrigida"
      }
    }
    // ...demais itens
  ]
}
```

---

## Como o viewer atual preenche esse schema

Trechos relevantes de implementação: `docs/validacao/index.html`.

### 1. Carregamento do prefill

1. O viewer lê a querystring:
   - `source=https://.../algum.json` → usa esta URL diretamente.
   - `prefill=<arquivo>.json` → resolve para `../prefill/<arquivo>.json`.
   - `prefill=<lattes_id>` (16 dígitos) → carrega `../prefill/manifest.json` e usa `by_lattes_id[lattes_id]` para resolver o arquivo em `docs/prefill/`.
2. A função `loadData()` chama `resolveSourceUrl()` e depois `fetch(sourceUrl)`.
3. O JSON esperado precisa ter a forma (exemplo de `docs/prefill/4741480538883395__*.json`):

```jsonc
{
  "schema_version": "2.0.0",
  "researcher": { ... },
  "metadata": {
    "extracted_at": "...",
    "total_productions": 224,
    "sections": [
      { "section_title": "Artigos completos publicados em periódicos", "item_count": 36, "tipo_producao": "temp__..." },
      // ...
    ],
    "filters": {
      "years": [2024, 2025]
    }
  },
  "productions": [
    {
      "numero_item": 3,
      "raw": "...",
      "autores": "...",
      "titulo": "...",
      "ano": 2025,
      "mes": null,
      "doi": "...",
      "fingerprint_sha1": "...",
      "production_type": "Artigos completos publicados em periódicos",
      "veiculo": "...",
      "source": {
        "file": "...html",
        "lattes_id": "4741480538883395",
        "production_type": "...",
        "extracted_at": "..."
      }
    }
    // ...demais produções
  ]
}
```

### 2. Como as marcações "Pertence ao INCT" são mantidas

- O estado global do viewer contém:

```js
const state = {
  selections: {},  // marcações "INCT?" por item
  edits: {},       // edições rápidas por item (título, veículo, ano, DOI, autores)
  // ...demais campos
};
```

- A chave de cada item (`itemKey`) é calculada por `getItemKey(item, groupKey, index)`:
  - Se existir `item.fingerprint_sha1`, a chave é esse valor.
  - Caso contrário, usa um fallback determinístico: `"<grupo>::<numero_item>::<slice do raw>"`.
- As marcações são armazenadas em `state.selections[itemKey] = true|false`.
- O estado é persistido em `localStorage` usando `state.storageKey = "inct_validacao::<lattes_id ou prefillParam>"`.

**Mapeamento para o schema proposto:**

- `pertence_inct` **≙** `Boolean(state.selections[itemKey])`.
- `item_id` **≙** `getItemKey(...)` (quando não houver `fingerprint_sha1`).

### 3. Como as edições são mantidas

- Ao clicar em **"Editar"**, abre-se um modal que permite alterar:
  - título
  - veículo
  - ano
  - DOI
  - autores
- Ao salvar, o viewer grava em `state.edits[itemKey]` um objeto da forma:

```js
{
  titulo: string,
  veiculo: string,
  ano: number | "",
  doi: string,
  autores: string,
}
```

- `applyEditsToProductions()` gera `state.productions` aplicando as edições sobre `state.productionsRaw`.
- As edições são persistidas no mesmo registro de `localStorage` que as seleções.

**Mapeamento para o schema proposto:**

- Campo `edits` do item de saída é exatamente `state.edits[itemKey]` (ou `null` se não houver edição).

### 4. Como o botão de download gera o JSON

O fluxo é:

1. Clique em **"Baixar validação (JSON)"** chama `downloadValidationJson()`.
2. Esta função constrói o payload via `buildExportPayload()`:

```js
const payload = {
  schema_version: state.schemaVersion,      // copiado do prefill
  researcher: state.researcher || null,     // objeto researcher do prefill
  prefill_source: state.prefillSource,      // valor de ?prefill ou ?source
  exported_at: new Date().toISOString(),
  summary: [
    {
      section: categoryLabel,
      total: totalCount,
      selected: selectedCount,             // número de itens marcados como INCT na seção
    },
    // ...uma entrada por seção com itens
  ],
  items: state.productions.map((item, index) => {
    const category = getCategory(item);
    const key = getItemKey(item, category, index);
    return {
      fingerprint_sha1: item.fingerprint_sha1 || null,
      selected: Boolean(state.selections[key]),
      production_type: category,
      titulo: item.titulo ?? item.title ?? null,
      ano: getYear(item) ?? null,
      doi: item.doi ?? null,
      veiculo: item.veiculo ?? item.vehicle ?? null,
      edits: state.edits[key] || null,
    };
  }),
};
```

3. O blob JSON é baixado com nome no formato:

```text
<lattes_id-ou-prefill>__validacao_<YYYYMMDD-hhmmss>.json
```

---

## Diferenças entre o código atual e o schema proposto

### Topo do JSON

- **Hoje:**
  - `schema_version`: copia `data.schema_version` do prefill (ex.: `"2.0.0"`).
- **Proposto:**
  - manter `schema_version` como está (versão do prefill),
  - **e adicionar** `schema_version_validacao` (ex.: `"1.0.0"`) para versionar o formato específico de validação.

### Campos de pesquisador

- **Hoje:**
  - `researcher`: é copiado diretamente do prefill (`researcher.lattes_id`, `full_name`, `slug`, `last_update`).
- **Proposto:**
  - manter exatamente esse comportamento; o schema apenas especifica que esses campos existem quando presentes no prefill.

### Itens / produções

- **Hoje:**
  - Campo booleando de marcação se chama `selected`.
  - Não há campo de observação textual.
  - Nem todos os campos exibidos na tabela são incluídos no JSON (hoje só vão `titulo`, `ano`, `doi`, `veiculo`).

- **Proposto:**
  - `pertence_inct`: campo booleano no JSON de validação que **espelha** o checkbox "INCT?". 
    - Implementação mínima: renomear `selected` → `pertence_inct` na saída ou manter ambos por compatibilidade de curto prazo.
  - `observacao`: string opcional para comentários livres do pesquisador sobre por que a produção pertence (ou não) ao INCT.
    - **Hoje** não existe campo na UI; o valor seria sempre `null`/ausente.
    - Sugerido: futuro ajuste no viewer para permitir preencher essa observação por item, armazenando em `state.observations[itemKey]` e incluindo no payload.
  - Campos adicionais (`autores`, `issn`, `isbn`, etc.):
    - **Hoje**: não são exportados, embora estejam disponíveis em `item`.
    - Proposto: opcionalmente ampliar o payload para incluir esses campos, facilitando conferências e reprocessamento.

### Resumo por seção

- **Hoje:**
  - Cada entrada de `summary` tem:

    ```jsonc
    { "section": "Artigos...", "total": 36, "selected": 20 }
    ```

- **Proposto:**
  - Adicionar campos derivados para separar marcados e não marcados:

    ```jsonc
    {
      "section": "Artigos completos publicados em periódicos",
      "production_type": "temp__artigos-completos-publicados-em-periodicos", // opcional
      "total": 36,
      "marked_inct": 20,      // == selected
      "unmarked": 16          // == total - selected
    }
    ```

  - Implementação mínima: durante `buildExportPayload()`, calcular `unmarked = total - selected` e renomear `selected` para `marked_inct` (ou manter ambos por compatibilidade).

---

## Ajustes mínimos sugeridos para alinhar código ↔ schema

1. **Versionamento do JSON de validação**

   - No `buildExportPayload()`:

   ```js
   const payload = {
     schema_version: state.schemaVersion,           // mantém para referenciar o prefill
     schema_version_validacao: "1.0.0",            // NOVO: versão do schema de validação
     // ...restante
   };
   ```

2. **Campo de marcação explícito `pertence_inct`**

   - Ainda em `buildExportPayload()`:

   ```js
   items: state.productions.map((item, index) => {
     const category = getCategory(item);
     const key = getItemKey(item, category, index);
     const selected = Boolean(state.selections[key]);

     return {
       fingerprint_sha1: item.fingerprint_sha1 || null,
       pertence_inct: selected,           // NOVO nome semanticamente claro
       selected,                          // opcional: manter durante período de transição
       production_type: category,
       // ...demais campos
     };
   }),
   ```

3. **Campo reservado para observações (`observacao`)**

   - Especificação do schema já inclui `observacao` como string; no código atual, pode ser iniciado como `null` para futura expansão:

   ```js
   return {
     // ...
     pertence_inct: selected,
     observacao: null,              // por enquanto sempre nulo
     // ...
   };
   ```

   - Em uma etapa futura (não implementada agora), o viewer poderia:
     - adicionar um campo de texto por linha ou no modal,
     - armazenar em algo como `state.observations[key]`,
     - e incluir em `observacao` no payload.

4. **Resumo com marcados/não marcados**

   - Na parte que monta `summary` dentro de `buildExportPayload()`:

   ```js
   summary.push({
     section: category,
     total,
     marked_inct: selectedCount,      // NOVO nome
     unmarked: total - selectedCount, // NOVO campo derivado
   });
   ```

   - Opcional: quando disponível, incluir também o identificador técnico da seção (`tipo_producao`) a partir de `state.metadataSections`.

---

## Fluxo de validação (visão lado pesquisador → JSON baixado)

1. **Acesso ao viewer**
   - O pesquisador recebe um link de validação, por exemplo:
     - `https://inctnanoagro.github.io/metricas/validacao/?prefill=4741480538883395` ou
     - `https://inctnanoagro.github.io/metricas/validacao/?prefill=4741480538883395__nome.json`.
   - O viewer resolve esse parâmetro para um arquivo em `docs/prefill/` (via `manifest.json` ou nome direto) e carrega o JSON de produções.

2. **Carregamento e exibição**
   - O viewer lê o JSON de prefill e:
     - preenche os metadados (nome do pesquisador, Lattes ID, data de extração, total de produções);
     - organiza as produções por **seção/tipo**, preservando a ordem original do array;
     - constrói as tabelas com colunas apropriadas por tipo de produção (título, veículo, DOI, etc.);
     - exibe filtros por **ano**, **seção** e **busca textual**.

3. **Marcação de produções que pertencem ao INCT**
   - Para cada linha há uma coluna **"INCT?"** com um checkbox:
     - desmarcado: produção não é considerada como pertencente ao INCT;
     - marcado: produção será considerada no relatório do INCT.
   - O pesquisador marca/desmarca conforme o entendimento sobre participação no INCT.
   - As marcações são salvas em `localStorage`, permitindo voltar ao mesmo link sem perder o progresso local.

4. **Edição rápida de campos**
   - Para cada produção há um botão **"Editar"** que abre um modal com campos editáveis:
     - Título
     - Veículo
     - Ano
     - DOI
     - Autores
   - O pesquisador pode corrigir pequenas inconsistências (typos, ano, DOI, etc.).
   - Ao salvar:
     - as edições são aplicadas apenas na camada de visualização,
     - são registradas em `state.edits[itemKey]` e persistidas em `localStorage`.

5. **Geração do JSON de validação**
   - Quando o pesquisador clica em **"Baixar validação (JSON)"**:
     1. O viewer percorre todas as produções (já com edições aplicadas).
     2. Para cada produção, monta um registro com:
        - identificador (`fingerprint_sha1` ou `item_id` derivado),
        - status de marcação (`pertence_inct` / `selected`),
        - dados essenciais (título, ano, DOI, veículo, etc.),
        - edições feitas (`edits`).
     3. Em paralelo, consolida um **resumo por seção** com:
        - total de produções na seção,
        - quantas foram marcadas como pertencentes ao INCT,
        - quantas não foram marcadas.
     4. Adiciona metadados de exportação (timestamp, fonte do prefill, schema_version).
     5. Gera o arquivo JSON e dispara o download com um nome que inclui o `lattes_id` e um timestamp.

6. **Envio ao time técnico**
   - O pesquisador envia o JSON baixado (por e-mail, formulário, etc.).
   - O time técnico:
     - lê os campos de resumo por seção,
     - reprocessa as produções marcadas (`pertence_inct = true`),
     - pode usar `fingerprint_sha1` / `item_id` para reconciliar com outras bases.

Esse fluxo já é suportado quase integralmente pelo código atual; os ajustes sugeridos são apenas para tornar o JSON de saída mais explícito em relação ao INCT e facilitar o consumo automatizado do arquivo de validação.