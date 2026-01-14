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
│   └── producoes.schema.json  # Production records schema v1.0.0
├── tests/                     # Unit tests
│   ├── test_parsers_artigos.py
│   ├── test_parsers_capitulos.py
│   └── test_cli_prefill.py
├── data/                      # Input/source data (gitignored)
├── outputs/                   # Generated outputs (gitignored)
└── docs/                      # Documentation and manuals
```

## Data Schema (v1.0.0)

The project uses a strict JSON Schema for all production records. Key components:

### Record Types
- LIVRO
- CAPITULO_DE_LIVRO
- TRABALHO_COMPLETO_EM_ANAIS
- RESUMO_EXPANDIDO_EM_ANAIS
- ARTIGO_ACEITO_PARA_PUBLICACAO

### Schema Structure
Each record contains:
- **schema_version**: Version identifier (1.0.0)
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

7. **File Locations**:
   - Schema definitions: `schema/`
   - Source data: `data/` (gitignored)
   - Outputs: `outputs/` (gitignored)
   - Never commit data files or outputs

8. **Code Style**: Follow existing patterns in parser implementations. Keep parsers modular and testable.

## Common Tasks

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
