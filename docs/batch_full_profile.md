# Documentação Oficial: batch_full_profile.py

## Visão Geral
O script `batch_full_profile.py` é o motor de processamento em lote do sistema de métricas do INCT NanoAgro. Ele é projetado para processar diretórios contendo arquivos HTML de "perfil completo" (full profile) extraídos do Currículo Lattes, transformando-os em dados estruturados (JSON) validados por schema.

## Localização
`/Users/brunoperez/projects/code/inct/metricas/metricas_lattes/batch_full_profile.py`

## Principais Funcionalidades
- **Processamento em Lote:** Varre um diretório de entrada em busca de arquivos `*.full_profile.html`.
- **Extração de Metadados:** Identifica ID Lattes, nome completo e data da última atualização diretamente do HTML ou nome do arquivo.
- **Divisão de Seções:** Separa dinamicamente as seções de produção (Artigos, Capítulos, Textos em Jornais, etc.).
- **Normalização de Texto:** Resolve problemas de encoding misto (*mojibake*) e entidades HTML para garantir UTF-8 limpo.
- **Filtragem por Ano:** Permite restringir a extração a anos específicos (padrão: 2024, 2025).
- **Validação de Schema:** Valida cada JSON gerado contra o `researcher_output.schema.json`.
- **Relatórios de Auditoria:** Gera um sumário consolidado (`summary.json`), log de erros (`errors.json`) e um relatório em Markdown (`audit_report.md`).

## Uso (Linha de Comando)
```bash
python3 -m metricas_lattes.batch_full_profile --in <input_dir> --out <output_dir> [opções]
```

### Argumentos:
- `--in`: Diretório contendo os arquivos HTML brutos.
- `--out`: Diretório onde os resultados (JSONs e relatórios) serão salvos.
- `--schema`: (Opcional) Caminho para o arquivo de schema JSON.
- `--years`: (Opcional) Anos permitidos (ex: `2024,2025`) ou `all` para todos.

## Fluxo de Processamento
1. **Leitura:** Carrega o arquivo HTML e normaliza o encoding.
2. **Segmentação:** Identifica as `title-wrapper` divs para separar as produções por tipo.
3. **Parsing:** Utiliza a infraestrutura de parsers internos (`metricas_lattes.parsers`) para estruturar cada item.
4. **Proveniência:** Adiciona metadados de origem (`source`) a cada item extraído.
5. **Validação:** Verifica se o objeto final respeita a estrutura documental esperada.
6. **Exportação:** Salva o JSON individual do pesquisador e atualiza os relatórios globais.

## Dependências Principais
- `BeautifulSoup4` (lxml) para manipulação de HTML.
- `jsonschema` para validação de dados.
- `unicodedata` para normalização de nomes e geração de slugs.

---
*Documentação gerada automaticamente pelo Assistente OpenClaw em 10/02/2026.*
