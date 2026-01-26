# Sistema de Parsing de Produções Lattes

## Visão Geral

Este documento descreve o sistema de parsing implementado para extrair produções científicas de arquivos HTML exportados da Plataforma Lattes.

## Arquitetura

### Componentes Principais

1. **Schema JSON (`schema/producoes.schema.json`)**
   - Schema canônico versão 2.0.0
   - Define estrutura de saída validável
   - Suporta múltiplos tipos de produção

2. **Router (`metricas_lattes/parser_router.py`)**
   - Ponto de entrada único: `parse_fixture(filepath)`
   - Registry de parsers específicos por tipo
   - Fallback genérico para tipos sem parser específico

3. **Parsers Específicos (`metricas_lattes/parsers/`)**
   - `artigos_v2.py`: Artigos em periódicos
   - `capitulos_v2.py`: Capítulos de livros
   - `textos_jornais.py`: Textos em jornais/revistas
   - Mais parsers podem ser adicionados facilmente

4. **Parser Genérico**
   - Extrai campos mínimos garantidos
   - Usa heurísticas robustas
   - Cobertura total de todos os tipos

## Uso Básico

### Parsing de um Arquivo

```python
from pathlib import Path
from metricas_lattes.parser_router import parse_fixture

# Parse um fixture
result = parse_fixture(Path('tests/fixtures/lattes/Artigos completos.html'))

# Resultado é um dicionário validável contra o schema
print(f"Tipo: {result['tipo_producao']}")
print(f"Items: {len(result['items'])}")

# Iterar sobre items
for item in result['items']:
    print(f"{item['numero_item']}. {item.get('titulo', 'N/A')}")
```

### Processar Todos os Fixtures

```python
from pathlib import Path
from metricas_lattes.parser_router import parse_fixture

fixtures_dir = Path('tests/fixtures/lattes')

for html_file in fixtures_dir.glob('*.html'):
    if 'full_profile' in str(html_file):
        continue

    result = parse_fixture(html_file)

    # Salvar ou processar resultado
    output_path = Path('outputs') / (html_file.stem + '.json')
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
```

## Schema de Saída

### Estrutura Top-Level

```json
{
  "schema_version": "2.0.0",
  "tipo_producao": "Nome do tipo",
  "source_file": "arquivo.html",
  "extraction_timestamp": "2026-01-14T12:00:00Z",
  "items": [...],
  "parse_metadata": {
    "parser_version": "1.0.0",
    "total_items": 10,
    "parse_errors": 0,
    "warnings": []
  }
}
```

### Estrutura de Item

Campos obrigatórios:
- `numero_item`: Número ordinal do Lattes (1, 2, 3...)
- `raw`: Texto bruto extraído (auditoria)

Campos opcionais (dependem do tipo):
- `autores`: Autores (separados por `;`)
- `titulo`: Título da produção
- `ano`: Ano de publicação
- `mes`: Mês (abreviado: jan, fev, mar...)
- `veiculo`: Nome do periódico/jornal/evento
- `volume`, `paginas`, `doi`, `isbn`, `issn`
- `livro`, `editora`, `edicao` (para capítulos)
- `evento`, `local` (para congressos)
- `instituicao`, `orientador` (para teses)
- `fingerprint_sha1`: Hash SHA1 do raw (deduplicação)

## Testes

### Rodar Suite Completa

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Rodar todos os testes
pytest tests/test_parse_fixtures.py -v

# Rodar com coverage
pytest tests/test_parse_fixtures.py --cov=metricas_lattes
```

### Tipos de Testes

1. **Validação de Schema**: Verifica conformidade com JSON Schema
2. **Campos Obrigatórios**: Verifica presença de campos mínimos
3. **Determinismo**: Parsing 2x produz mesmo resultado
4. **Sequência de Números**: Verifica numero_item válidos
5. **Fingerprints**: Valida hashes SHA1
6. **Golden Files**: Compara com saídas de referência

### Teste Manual Rápido

```bash
python3 scripts/test_parsers_manual.py
```

Mostra resumo de parsing para todos os fixtures.

## Adicionando Novo Parser

### 1. Criar Parser Específico

```python
# metricas_lattes/parsers/novo_tipo.py

class NovoTipoParser:
    def __init__(self):
        self.errors = []

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'lxml')
        items = []

        # Lógica de parsing específica...

        return items
```

### 2. Registrar no Router

```python
# metricas_lattes/parser_router.py

from .parsers.novo_tipo import NovoTipoParser

PARSER_REGISTRY = {
    # ...
    'padrão no nome do arquivo': NovoTipoParser,
}
```

### 3. Adicionar Testes

Os testes parametrizados detectam automaticamente novos fixtures.

### 4. Gerar Golden File (Opcional)

```bash
python3 scripts/generate_golden_files.py --only "nome do arquivo"
```

## Padrões de HTML do Lattes

### Estrutura Típica

```html
<!-- Cabeçalho da seção -->
<div class="cita-artigos"><b>Nome da Seção</b></div>

<!-- Item numerado -->
<div class="layout-cell layout-cell-1">
  <div class="layout-cell-pad-6 text-align-right">
    <b>1. </b>
  </div>
</div>

<!-- Conteúdo do item -->
<div class="layout-cell layout-cell-11">
  <span class="transform">
    AUTOR1 ; AUTOR2 ; <b>AUTOR_DESTAQUE</b> . Título da produção.
    Veículo, v. 10, p. 1-20, 2024.
  </span>
</div>
```

### Elementos Especiais

- `<b>`: Nome em negrito (autor destacado)
- `<a class="tooltip" href="...">`: Link Lattes do autor
- `<a class="icone-doi" href="...">`: Link DOI
- `<span data-tipo-ordenacao="ano">`: Metadado de ano
- `<sup><img class="jcrTip">`: Ícone de fator de impacto

## Robustez e Boas Práticas

### Parsing Defensivo

1. **Não depender de posições fixas**: Use seletores semânticos
2. **Tratar ausência de campos**: Todos campos opcionais devem ter valor `null`
3. **Preservar raw text**: Sempre guardar texto original para auditoria
4. **Normalizar whitespace**: Remover `\xa0`, múltiplos espaços
5. **Evitar regex em texto completo**: Preferir buscas localizadas

### Heurísticas Confiáveis

- **Autores**: Antes do primeiro ` . ` seguido de maiúscula
- **Ano**: Último ano de 4 dígitos (19xx ou 20xx)
- **Mês**: Padrões `jan.`, `fev.`, etc.
- **DOI**: Link com classe `icone-doi`
- **Número item**: `<b>N.</b>` em `layout-cell-1`

### Fingerprinting

```python
import hashlib

fingerprint = hashlib.sha1(raw_text.encode('utf-8')).hexdigest()
```

Use para:
- Deduplicação
- Detecção de mudanças
- Rastreabilidade

## Performance

### Otimizações Implementadas

1. **Parser lxml**: Mais rápido que html.parser
2. **Buscas localizadas**: find() e find_next_sibling()
3. **Evitar múltiplas passagens**: Parse em uma única iteração
4. **Sem regex global**: Aplicar regex apenas em trechos pequenos

### Benchmarks

- 336 artigos (812KB): ~0.2s
- 1362 resumos (grande): ~0.5s
- 27 fixtures (3137 items): ~6s total

## Troubleshooting

### Parser não encontra items

- Verificar estrutura HTML do fixture
- Confirmar presença de `layout-cell-1` e `layout-cell-11`
- Verificar se `span.transform` existe

### Validação de schema falha

- Rodar com `-v` para ver erro específico
- Verificar campos obrigatórios (numero_item, raw)
- Verificar tipos (numero_item deve ser int)

### Campos vazios ou None

- Normal para campos opcionais
- Significa que parser não conseguiu extrair com segurança
- `raw` sempre deve estar presente para auditoria manual

## Próximos Passos

### Parsers Prioritários para Implementar

1. Trabalhos completos em anais de congressos
2. Resumos em anais de congressos
3. Livros publicados/organizados
4. Patentes e produtos tecnológicos
5. Orientações (teses, dissertações, TCC)

### Melhorias Futuras

- [ ] Parser para patentes (estrutura diferente)
- [ ] Parser para orientações (extrair orientando + banca)
- [ ] Normalização de nomes de autores (SOBRENOME, Nome → Nome Sobrenome)
- [ ] Resolução de ambiguidade de ano (múltiplos anos no texto)
- [ ] Extração de ISSN/ISBN mais robusta
- [ ] Suporte a HTML encoding corrupto (Latin-1 vs UTF-8)

## Referências

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/schema
- BeautifulSoup Documentation: https://www.crummy.com/software/BeautifulSoup/
- Pytest Documentation: https://docs.pytest.org/
