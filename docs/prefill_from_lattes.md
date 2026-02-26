# Documentação Oficial: prefill_from_lattes.py

## Visão Geral
O script `prefill_from_lattes.py` é uma ferramenta utilitária focada na extração rápida de artigos para geração de arquivos de "pre-preenchimento" (prefill). Ele é utilizado principalmente para alimentar a interface de conferência manual de dados.

## Localização
`/Users/brunoperez/projects/code/inct/metricas/scripts/prefill_from_lattes.py`

## Principais Funcionalidades
- **Extração Focada:** Especializado em extrair produções do tipo "Artigos completos publicados em periódicos".
- **Ordenação Determinística:** Ordena os itens pela ordem original do Lattes para facilitar a conferência visual.
- **Geração de Prefill:** Salva o resultado no diretório `docs/prefill/` com o nome do slug do pesquisador.
- **Log de Erros:** Gera um arquivo `.errors.json` separado contendo falhas específicas de parsing para depuração.

## Uso (Linha de Comando)
```bash
python3 scripts/prefill_from_lattes.py <input_file.html> --pesquisador <slug>
```

### Argumentos:
- `input_file`: Caminho para o arquivo HTML do Lattes.
- `--pesquisador`: Slug identificador do pesquisador (ex: `bruno-perez`).

## Saída
- `docs/prefill/<slug>.json`: Dados estruturados para a interface.
- `docs/prefill/<slug>.errors.json`: Detalhes de falhas durante o processamento.

---
*Documentação gerada automaticamente pelo Assistente OpenClaw em 10/02/2026.*
