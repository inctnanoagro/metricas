# Legacy Tests (Parsers v1)

This directory contains tests for the legacy parser implementation (v1).

## Status

These tests are **not run** by default (`pytest -q`) as they test the old parser API which is incompatible with the new v2 system.

## Differences v1 vs v2

**v1 Parsers** (legacy):
- Return `ParsedProduction` dataclass instances
- Different field names
- Located in `metricas_lattes/parsers/*.py`

**v2 Parsers** (current):
- Return `dict` instances
- Schema-compliant field names
- Located in `metricas_lattes/parsers/*_v2.py`
- Used by `parser_router.py`

## Running Legacy Tests

To run these tests explicitly:

```bash
pytest tests_legacy/ -v
```

Expected result: **Some failures** due to API incompatibility.

## Migration Path

To update these tests to v2:

1. Import parsers from `*_v2.py` modules
2. Change assertions from dataclass fields to dict keys
3. Update field name expectations
4. Use `parser_router.parse_fixture()` instead of direct parser calls

## Deprecation

These tests are kept for reference but may be removed in future versions once v1 parsers are fully deprecated.
