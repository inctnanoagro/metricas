# INCT NanoAgro - Métricas - Claude Context

## Project Overview

This repository consolidates scientific production data from researchers affiliated with INCT NanoAgro. The project extracts, parses, and validates data from Lattes CVs to create a structured institutional database for accountability, impact reporting, and strategic analysis.

## Key Objectives

- Extract and parse scientific production records from Lattes HTML CVs
- Validate and organize data using a JSON schema
- Support institutional reporting and impact analysis
- Provide a structured layer on top of official sources (Lattes)

## Project Structure

```
metricas/
├── scripts/                    # Main workflow scripts
│   ├── ingestao_lattes.py     # Lattes HTML ingestion
│   ├── agregacao.py           # Data aggregation
│   ├── validacao.py           # Schema validation
│   └── prefill_from_lattes.py # Prefill from Lattes data
├── metricas_lattes/           # Core parsing library
│   └── parsers/               # HTML parsers for different record types
│       ├── base.py            # Base parser functionality
│       ├── artigos.py         # Article parser
│       └── capitulos.py       # Book chapter parser
├── schema/                    # JSON Schema definitions
│   └── producoes.schema.json  # Production records schema v1.1.0
├── tests/                     # Unit tests
│   ├── test_parsers_artigos.py
│   ├── test_parsers_capitulos.py
│   └── test_cli_prefill.py
├── data/                      # Input/source data (gitignored)
├── outputs/                   # Generated outputs (gitignored)
└── docs/                      # Documentation and manuals
```

## Data Schema (v1.1.0 — 2026-01-14)

The project uses a strict JSON Schema for all production records. Key components:

### Record Types
- TEXTOS_JORNAIS_REVISTAS
- LIVRO
- CAPITULO_DE_LIVRO
- TRABALHO_COMPLETO_EM_ANAIS
- RESUMO_EXPANDIDO_EM_ANAIS
- ARTIGO_ACEITO_PARA_PUBLICACAO

### Schema Structure
Each record contains:
- **schema_version**: Version identifier (1.1.0)
- **record_id**: Stable identifier (SHA1-based)
- **record_type**: Production type enum
- **provenance**: Source tracking and audit trail
  - source_system: LATTES_HTML
  - source_doc_id: Source file identifier
  - extraction_timestamp_utc: ISO 8601 timestamp
  - section_key: Canonical section identifier
  - item_number: Ordinal number from Lattes
- **content**: Extracted data
  - raw_text: Exact text from HTML
  - raw_html: HTML snippet (optional)
  - doi_url: DOI link if available
  - people: Authors/organizers with Lattes URIs
  - bibliography: Parsed bibliographic fields
- **fingerprints**: Deduplication and integrity
  - text_sha1: SHA1 of raw text
  - text_sha256: SHA256 of raw text
  - dedupe_key: Deterministic deduplication key
- **quality**: Parse confidence and warnings


### Schema file location and versioning

- **Canonical (current) schema** MUST live at: `schema/producoes.schema.json`
- Do **not** overwrite older schemas in-place unless you have Git history you trust.
  - If Git history is not reliable or you want an explicit archive, move the previous file to:
    - `schema/archive/producoes.schema.legacy.pre-2026-01-14.json`
  - Keep `schema/producoes.schema.json` as the **single source of truth** the parser validates against.
- Schema changes should be **additive** whenever possible (new optional fields, new record types).
  - Breaking changes require a version bump and explicit migration notes.

### Record type: TEXTOS_JORNAIS_REVISTAS (Lattes section)

This corresponds to the Lattes section titled **“Textos em jornais de notícias/revistas”** (anchor/name: `TextosJornaisRevistas`).

Detection heuristics (robust):

- Header block usually appears as one of:
  - `div.cita-artigos > b` containing the title text
  - `a[name="TextosJornaisRevistas"]` (sometimes repeated)
- After the header, records appear as repeating pairs:
  - index cell: `div.layout-cell.layout-cell-1 ... <b>N.</b>`
  - content cell: `div.layout-cell.layout-cell-11 > span.transform` (this is the citation payload)

Extraction contract for Claude:

- For each record, capture **raw_text** = `span.transform.innerText` (or equivalent textContent with normalized whitespace).
- Also capture **raw_html** = the `span.transform` HTML (optional but recommended for debugging).
- Minimal parsed fields (best-effort; keep nulls if not confidently parsed):
  - **authors**: list[str] parsed from the leading segment split by ` ; ` until the first `" . "` that marks the end of author list.
    - Keep names as displayed (including initials), but normalize excessive spaces.
  - **title**: the segment between the end of authors and the next `"."` (first title sentence).
  - **venue**: journal/magazine/newspaper name (e.g., “Jornal Cruzeiro do Sul”, “Unesp Ciência”, “Cultivar Grandes Culturas”).
  - **location**: city/state when present (e.g., “Sorocaba”, “São Paulo”).
  - **pages**: parse patterns like `p. A2 - A2` or `p. 16 - 19`.
  - **date**: parse Portuguese dates like `27 mar.  2025`, `12 fev.  2019`, `01 nov.  2018`.
    - Store normalized ISO `YYYY-MM-DD` when day is present, else `YYYY-MM` or `YYYY`.
  - **url_lattes_ids** (optional): collect any `href="http://lattes.cnpq.br/<id>"` found inside the span.
- Always store a stable **source_section_key** = `"TextosJornaisRevistas"` and **record_type** = `"TEXTOS_JORNAIS_REVISTAS"`.

### Fixtures and tests

For long-term robustness, store raw HTML snippets in `tests/fixtures/` and write unit tests per section.

Recommended fixture placement for this section:

- `tests/fixtures/lattes/TextosJornaisRevistas/snippet_01.html`
  - Contains the header + a few records (1–3) exactly as captured.
- (Optional) Add edge cases:
  - `snippet_no_pages.html` (records without `p.`)
  - `snippet_with_links.html` (authors wrapped in `<a class="tooltip">...`)

Unit test expectations:

- The parser detects the section and yields N records.
- Each record contains `raw_text`, `record_type`, `source_section_key`.
- At least the **title** and **venue** parse for the majority of records; failures must emit warnings but not crash.

## Technical Details

### Dependencies
- Python 3.x
- beautifulsoup4==4.12.2
- pytest==7.4.3
- pytest-cov==4.1.0

### Data Flow
1. HTML files from Lattes CVs placed in `data/`
2. Parsers extract structured records from HTML
3. Records validated against JSON schema
4. Aggregation and deduplication
5. Output to `outputs/` directory

### Parser Implementation
- Base parser in `metricas_lattes/parsers/base.py` provides core functionality
- Type-specific parsers extend base class
- Each parser handles specific Lattes HTML sections
- Preserves raw text as source of truth
- Generates cryptographic fingerprints for integrity

### Testing Strategy
- Unit tests for each parser type
- CLI integration tests
- Coverage tracking with pytest-cov

## Development Status

🚧 In active development

## Git Status
- Main branch: `main`
- Modified: `schema/producoes.schema.json`
- Untracked directories: `data/`, `outputs/`, `metricas_lattes/`, `tests/`

## Important Notes for AI Assistants

1. **Data Integrity**: Always preserve `raw_text` as the source of truth. All parsed fields must be derivable from raw_text.

2. **Schema Compliance**: All records must validate against `schema/producoes.schema.json`. The schema is strict with `additionalProperties: false`.

3. **Provenance Tracking**: Every record must have complete provenance metadata for audit purposes.

4. **Fingerprinting**: Use SHA1/SHA256 hashes for deduplication and integrity verification.

5. **Lattes HTML**: The source data is HTML exported from Lattes platform. Encoding issues (especially UTF-8) may be present.

6. **Testing**: Run tests with pytest before committing changes. Maintain test coverage.

7. **File Locations (canonical, auditável)**:
   - **Schema atual (fonte de verdade)**: `schema/producoes.schema.json`
   - **Arquivo de schemas antigos (não apagar)**: `schema/archive/`  
     - Ex.: `schema/archive/producoes.schema.legacy.pre-2026-01-14.json`
   - **Fixtures de HTML (para testes)**: `tests/fixtures/lattes/`
     - Ex.: `tests/fixtures/lattes/TextosJornaisRevistas/snippet_01.html`
   - **Dados brutos baixados (NUNCA commitar)**: `data/` (gitignored)
   - **Saídas do parser (NUNCA commitar)**: `outputs/` (gitignored)

   **Artifact Registry (o que deve existir no repo para o parser ser implementado):**
   - `schema/producoes.schema.json` (versão v1.1.0)
   - `schema/archive/producoes.schema.legacy.pre-2026-01-14.json` (snapshot do schema antigo)
   - `tests/fixtures/lattes/TextosJornaisRevistas/snippet_01.html` (amostra real do HTML)
   - (opcional) `tests/fixtures/lattes/TextosJornaisRevistas/snippet_no_pages.html`
   - (opcional) `tests/fixtures/lattes/TextosJornaisRevistas/snippet_with_links.html`

8. **Code Style**: Follow existing patterns in parser implementations. Keep parsers modular and testable.
### Running Tests
```bash
pytest tests/
pytest --cov=metricas_lattes tests/
```

### Schema Validation
Validate records against the JSON schema using standard JSON Schema validators.

### Adding New Record Types
1. Update schema enum in `record_type`
2. Add section_key to enum if needed
3. Implement parser in `metricas_lattes/parsers/`
4. Add corresponding tests
5. Update this documentation
