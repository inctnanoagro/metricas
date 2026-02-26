# Documentação Técnica - Repositório `inct/metricas`

**Data de Geração:** 2026-02-22  
**Autor:** Case (OpenClaw)

## 1. Visão Geral do Projeto (INCT NanoAgro)

- **Propósito:** Mapeamento e gestão de métricas de produção científica para o Instituto Nacional de Ciência e Tecnologia (INCT) em Nanotecnologia para o Agronegócio.
- **Período de Análise:** O sistema foca em dados gerados entre 2024 e 2025, conforme o escopo do relatório final FAPESP TT-IV.
- **Fonte de Dados Primária:** Currículos Lattes dos pesquisadores, exportados em formato HTML.

## 2. Arquitetura e Pipeline de Dados

O fluxo de processamento é dividido em quatro estágios principais, garantindo a transformação de dados brutos em informações validadas e enriquecidas.

### Estágio 1: Ingestão e Processamento Batch
- **Descrição:** Converte os arquivos HTML do Lattes em um formato JSON estruturado e canônico.
- **Script Principal:** `metricas_lattes/batch_full_profile.py`
- **Entrada:** Diretório contendo arquivos `*full_profile.html`.
- **Saída:** Arquivos JSON individuais para cada pesquisador em `outputs/<nome_do_batch>/researchers/`.
- **Regras de Negócio Cruciais:**
    - **Filtro Temporal:** Apenas produções científicas publicadas nos anos de **2024 e 2025** são processadas. Itens fora desse período são descartados.
    - **Validação de Data:** Itens onde o ano de publicação não pode ser extraído ou inferido são ignorados.

### Estágio 2: Publicação para Validação (GitHub Pages)
- **Descrição:** Os dados processados são preparados e publicados em uma interface web estática para que os pesquisadores possam validar suas produções.
- **Interface:** `docs/validacao/index.html`, hospedado via GitHub Pages.
- **Fonte de Dados da Interface:** A aplicação web lê os arquivos JSON do diretório `docs/prefill/`.
- **Script de Sincronização:** `scripts/sync_validation_to_pages.py` é utilizado para copiar os resultados do batch (Estágio 1) para a pasta `docs/prefill/`, tornando-os acessíveis ao viewer.

### Estágio 3: Validação Humana
- **Descrição:** O pesquisador acessa a página de validação, marca quais produções pertencem ao INCT e baixa um arquivo JSON com os resultados.
- **Saída (Export do Navegador):** Um único arquivo JSON (`*_validation.json`) contendo:
    - `lattes_id`: Identificador do pesquisador.
    - `pertence_inct`: Um booleano (`true`/`false`) para cada item de produção.
    - `fingerprint_sha1`: Hash que identifica unicamente cada produção, servindo como chave para o merge.
    - Contadores e metadados da validação.

### Estágio 4: Aplicação da Validação
- **Descrição:** Os dados validados pelos pesquisadores são reincorporados ao dataset principal.
- **Script Principal:** `scripts/apply_validation_json.py`
- **Entrada:** Um diretório contendo os múltiplos arquivos `*_validation.json` recebidos dos pesquisadores.
- **Lógica:** O script lê cada arquivo de validação, localiza o JSON original do pesquisador correspondente e utiliza o `fingerprint_sha1` para dar "merge" nos dados, adicionando um bloco `validacao_inct` a cada item de produção.
- **Saída:** Arquivos JSON enriquecidos no diretório `outputs/<nome_do_batch>/validated/`.

## 3. Scripts de Manutenção e Diagnóstico

Para garantir a integridade e a qualidade dos dados, dois scripts principais de manutenção foram desenvolvidos.

### 3.1. `compare_html_vs_json.py`
- **Propósito:** Realizar um diagnóstico quantitativo, comparando o número de itens de produção listados no HTML original com o número de itens processados no JSON resultante.
- **Função:** Ajuda a identificar discrepâncias que podem indicar falhas no parser ou o impacto dos filtros de data aplicados no batch.
- **Uso Típico:**
  ```bash
  python scripts/compare_html_vs_json.py \
    --html-dir <diretorio_dos_htmls> \
    --json-dir outputs \
    --batch <nome_do_batch> \
    --out <diretorio_de_saida_do_relatorio>
  ```
- **Interpretação:** É esperado que existam diferenças (`mismatch`) devido ao filtro de anos (2024-2025). O script é vital para detectar se uma seção inteira de produção foi ignorada por um erro de parsing.

### 3.2. `apply_validation_json.py`
- **Propósito:** Automatizar o processo de merge entre os dados processados e as validações manuais enviadas pelos pesquisadores.
- **Função:** Conforme descrito no Estágio 4, este script é o passo final do pipeline, integrando a validação humana ao dataset canônico.
- **Uso Típico:**
  ```bash
  python scripts/apply_validation_json.py \
    --validation-dir <diretorio_com_jsons_validados> \
    --researchers-dir <diretorio_com_jsons_originais> \
    --validated-output-dir <diretorio_de_saida_final>
  ```

## 4. Glossário Técnico

- **`fingerprint_sha1`**: Um hash SHA1 gerado a partir do título normalizado de uma produção. É a chave primária utilizada para vincular dados entre os diferentes estágios do pipeline.
- **`lattes_id`**: O identificador único de 16 dígitos de um Currículo Lattes.
- **`dry_run`**: Nomenclatura utilizada para identificar um lote de processamento executado em modo de teste ou simulação.
- **JSON Canônico**: Refere-se ao arquivo JSON gerado no Estágio 1, que serve como a fonte da verdade antes da validação humana.

---
*Este documento reflete o estado do repositório em Fevereiro de 2026 e deve ser mantido atualizado a cada alteração significativa no pipeline ou nos scripts.*
