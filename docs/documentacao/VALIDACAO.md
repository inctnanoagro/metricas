# 📋 GUIA DE VALIDAÇÃO - Ingestão Lattes v3

## 🎯 Objetivo
Validar a extração automática de todas as categorias de produção científica do Lattes.

---

## ✅ CATEGORIAS IMPLEMENTADAS

### 1. ✔️ Artigos Publicados (JÁ VALIDADO)
- ✅ Título
- ✅ Autores
- ✅ Veículo (nome da revista)
- ✅ Volume
- ✅ Páginas
- ✅ Ano
- ✅ DOI

### 2. 📖 Capítulos de Livros (A VALIDAR)
**Campos extraídos:**
- Título do capítulo
- Autores
- Nome do livro
- Editora
- Edição
- Páginas
- Ano
- ISBN
- DOI

**Como testar:**
1. Acesse o Lattes do pesquisador
2. Navegue até: **Produções → Livros e Capítulos → Capítulos de livros publicados**
3. Clique com botão direito na tabela → "Inspecionar"
4. Copie o HTML da div que contém os capítulos
5. Cole na ferramenta com categoria "Capítulos de livros"

**O que observar:**
- ✓ Título do capítulo é capturado corretamente
- ✓ Nome do livro aparece no campo "Livro" (geralmente após "In:")
- ✓ Editora e ano são extraídos
- ✓ Páginas do capítulo (não do livro todo)

---

### 3. 📚 Livros Publicados (A VALIDAR)
**Campos extraídos:**
- Título do livro
- Autores
- Editora
- Edição
- Número de páginas
- Ano
- ISBN
- DOI
- Tipo (Autor/Coautor/Organizador)

**Como testar:**
1. Acesse o Lattes do pesquisador
2. Navegue até: **Produções → Livros e Capítulos → Livros publicados/organizados**
3. Clique com botão direito na tabela → "Inspecionar"
4. Copie o HTML da div que contém os livros
5. Cole na ferramenta com categoria "Livros publicados"

**O que observar:**
- ✓ Título completo do livro
- ✓ Identificação se é Autor, Coautor ou Organizador
- ✓ Número total de páginas (formato: "123p.")
- ✓ Edição (se aplicável)

---

### 4. 🎤 Trabalhos em Eventos (A VALIDAR)
**Campos extraídos:**
- Título do trabalho
- Autores
- Nome do evento
- Ano
- Local (cidade)
- Tipo (Anais/Resumo/Trabalho completo/Apresentação)
- DOI

**Como testar:**
1. Acesse o Lattes do pesquisador
2. Navegue até: **Produções → Trabalhos em eventos**
3. Clique com botão direito na tabela → "Inspecionar"
4. Copie o HTML da div que contém os trabalhos
5. Cole na ferramenta com categoria "Trabalhos em eventos"

**O que observar:**
- ✓ Título do trabalho (não do evento)
- ✓ Nome do evento capturado (após "In:")
- ✓ Cidade/local do evento
- ✓ Classificação correta do tipo de publicação

---

### 5. 👨‍🎓 Orientações (A VALIDAR)
**Campos extraídos:**
- Título do trabalho
- Nome do orientando
- Instituição
- Tipo (Dissertação/Tese/TCC/IC/Supervisão)
- Nível (Mestrado/Doutorado/Graduação/Pós-Doutorado)
- Ano
- Status (Concluída/Em andamento)

**Como testar:**
1. Acesse o Lattes do pesquisador
2. Navegue até: **Orientações → Orientações concluídas** OU **Em andamento**
3. Clique com botão direito na tabela → "Inspecionar"
4. Copie o HTML da div que contém as orientações
5. Cole na ferramenta com categoria "Orientações"

**O que observar:**
- ✓ Nome do orientando (não do orientador)
- ✓ Identificação correta do tipo (Dissertação, Tese, TCC, etc.)
- ✓ Nível acadêmico correto
- ✓ Status reflete se está concluída ou em andamento

---

## 🔍 PADRÕES DE HTML DO LATTES

### Estrutura comum a todas as categorias:
```html
<div class="layout-cell">
    <div class="layout-cell-pad-5 title">
        [TÍTULO]
    </div>
    <div class="layout-cell-pad-5 authors">
        [AUTORES/ORIENTANDOS]
    </div>
    <div class="layout-cell-pad-5 informacao-artigo">
        [DADOS BIBLIOGRÁFICOS]
    </div>
</div>
```

### Diferenças entre categorias:

**Artigos:**
- Classe específica: `informacao-artigo`
- Padrão: `Revista, v. X, p. Y-Z, ano`

**Capítulos:**
- Classe específica: `informacao`
- Padrão: `In: Nome do livro. Edição. Editora, ano, p. X-Y`

**Livros:**
- Classe específica: `informacao`
- Padrão: `Editora, ano. XXXp.`

**Eventos:**
- Classe específica: `informacao`
- Padrão: `In: Nome do evento, ano, Cidade. Anais...`

**Orientações:**
- Classe específica: `informacao`
- Padrão: `Ano. Tipo de orientação (Nível). Instituição`

---

## 🐛 PONTOS DE ATENÇÃO PARA TESTES

### Casos especiais a verificar:

1. **Múltiplos autores com pontuação complexa**
   - Ex: "Silva, J. A. ; Santos, M. B. ; Costa, R. C."

2. **DOIs em diferentes formatos**
   - Ex: "DOI: 10.1234/journal.2024.001"
   - Ex: "doi:10.1234/journal"

3. **Páginas em formatos variados**
   - Ex: "p. 123-145"
   - Ex: "p.123-145"
   - Ex: "123p." (para livros completos)

4. **Eventos com nomes longos e vírgulas**
   - Ex: "Congresso Internacional de Pesquisa, Inovação e Desenvolvimento"

5. **Orientações em andamento vs concluídas**
   - Verificar se o status é identificado corretamente

6. **Livros sem edição especificada**
   - Campo deve ficar vazio, não null

7. **Trabalhos sem DOI**
   - Campo deve ficar vazio, não causar erro

---

## 📊 CHECKLIST DE VALIDAÇÃO

Para cada categoria, verificar:

- [ ] HTML é parseado sem erros
- [ ] Todos os itens da seção são capturados
- [ ] Campos obrigatórios são preenchidos
- [ ] Campos opcionais ficam vazios quando não há dados
- [ ] Ordem do Lattes é preservada
- [ ] Edição manual funciona corretamente
- [ ] Remoção individual funciona
- [ ] JSON gerado contém todos os campos

---

## 📝 FORMATO DO JSON EXPORTADO

```json
{
  "pesquisador": "Nome do Pesquisador",
  "periodo": "2020-2024",
  "data_ingestao": "2024-01-15T10:30:00.000Z",
  "total_producoes": 10,
  "producoes": [
    {
      "categoria": "artigo",
      "ordem_lattes": 1,
      "titulo": "...",
      "autores": "...",
      "veiculo": "...",
      "ano": 2024,
      "volume": "10",
      "paginas": "123-145",
      "doi": "10.1234/..."
    },
    {
      "categoria": "capitulo",
      "ordem_lattes": 1,
      "titulo": "...",
      "autores": "...",
      "livro": "...",
      "editora": "...",
      "ano": 2023,
      "paginas": "45-67",
      "isbn": "978-...",
      "doi": null
    },
    // ... outras produções
  ]
}
```

---

## 🚀 PRÓXIMOS PASSOS APÓS VALIDAÇÃO

1. ✅ Confirmar que todas as 5 categorias funcionam
2. 📋 Documentar padrões específicos encontrados
3. 🔧 Ajustar regex se necessário
4. 🎨 Refinar interface (cores, labels)
5. 🌐 Deploy final no GitHub Pages

---

## 💡 DICAS PARA TESTES EFICIENTES

1. **Comece com um pesquisador que tenha todos os tipos de produção**
2. **Teste com HTML real do Lattes, não fabricado**
3. **Valide tanto itens recentes quanto antigos**
4. **Verifique casos com dados incompletos**
5. **Teste a edição manual após a importação**
6. **Baixe o JSON e valide a estrutura**

---

## 🐞 REPORTAR PROBLEMAS

Caso encontre erros na extração:

1. Anote qual categoria está falhando
2. Identifique qual campo não foi extraído corretamente
3. Copie o HTML da div específica que falhou
4. Descreva o resultado esperado vs obtido

Exemplo:
```
Categoria: Capítulos
Campo com erro: editora
HTML: [colar HTML da div]
Esperado: "Editora XYZ"
Obtido: null
```

---

## ✨ MELHORIAS FUTURAS (PÓS-VALIDAÇÃO)

- [ ] Detecção automática de categoria pelo HTML
- [ ] Validação de DOI com chamada à API
- [ ] Export para CSV além de JSON
- [ ] Importação de JSON existente
- [ ] Filtros por ano/categoria
- [ ] Busca/ordenação na lista
- [ ] Indicador de qualidade dos dados
