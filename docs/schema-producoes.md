📊 Registro de Produções Acadêmicas
Documentação do JSON Schema – INCT NanoAgro
Versão do schema

Padrão: JSON Schema draft-07

Arquivo: schema/producoes.schema.json

Período de referência: 01/01/2024 a 31/12/2025

🎯 Finalidade

Este schema define a estrutura padronizada para registro de produções acadêmicas associáveis ao INCT NanoAgro, com base em informações declaradas a partir do Currículo Lattes dos pesquisadores.

Usos institucionais:

Prestação de contas

Relatórios de impacto (quantitativos)

Análise estratégica interna

Consolidação e validação posterior pelos pesquisadores

🧱 Estrutura geral

Cada registro representa uma produção acadêmica individual.

Blocos principais:

identificacao

autores

tipo_producao

dados_bibliograficos

vinculo_institucional

indicadores_basicos (opcional)

metadados_coleta

Campos não previstos no schema não são permitidos.

📌 1. Identificação da produção (identificacao)

Informações básicas que identificam a produção.

Campo	Tipo	Obrigatório	Descrição
titulo	string	✅	Título da produção
ano	integer	✅	Ano da produção (2024 ou 2025)
idioma	string	❌	Idioma principal (pt, en, es, outro)
👥 2. Autores (autores)

Lista de autores da produção.

Deve conter ao menos um autor

A ordem segue a autoria original

Campo	Tipo	Obrigatório	Descrição
nome_completo	string	✅	Nome completo do autor
pesquisador_inct	boolean	❌	Indica vínculo com o INCT
instituicao	string	❌	Instituição do autor
🧪 3. Tipo de produção (tipo_producao)

Classificação principal da produção.

Valores permitidos:

artigo_periodico

capitulo_livro

livro

trabalho_evento

resumo

patente

produto_tecnologico

outro

📚 4. Dados bibliográficos (dados_bibliograficos)

Informações de publicação ou divulgação.

Campo	Tipo	Obrigatório	Descrição
revista_ou_evento	string	❌	Nome da revista ou evento
issn_isbn	string	❌	ISSN ou ISBN
doi	string	❌	DOI da produção
editora	string	❌	Editora (quando aplicável)
🏛️ 5. Vínculo institucional (vinculo_institucional)

Define se a produção pode ser associada institucionalmente ao INCT NanoAgro.

Campo	Tipo	Obrigatório	Descrição
associavel_inct	boolean	✅	Indica associação ao INCT
observacao_vinculo	string	❌	Justificativa ou observação

⚠️ A associação não exige menção explícita ao INCT na publicação; será validada posteriormente pelos pesquisadores.

📈 6. Indicadores básicos (indicadores_basicos)

Campos opcionais para análise cientométrica.

Campo	Tipo	Obrigatório	Descrição
qualis	string	❌	Classificação Qualis
fator_impacto	number	❌	Fator de impacto (≥ 0)
🗂️ 7. Metadados da coleta (metadados_coleta)

Informações administrativas sobre o registro.

Campo	Tipo	Obrigatório	Descrição
fonte	string	✅	Origem dos dados (curriculo_lattes)
data_registro	date	✅	Data do registro
responsavel_registro	string	❌	Responsável pelo lançamento
🔒 Regras institucionais

O schema é descritivo, não interpretativo

Não realiza cálculos ou inferências

A validação de vínculo é posterior e humana

Extensões futuras devem manter compatibilidade

🧭 Observação final

Este schema é a base canônica para:

formulários de coleta

validação automática

agregação cientométrica

geração de relatórios institucionais

Alterações estruturais devem ser feitas com controle de versão.
