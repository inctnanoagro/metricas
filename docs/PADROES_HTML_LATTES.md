# 🔬 PADRÕES HTML DO LATTES - Referência Técnica

## 📌 ESTRUTURA GERAL

Todas as produções no Lattes seguem uma estrutura base consistente:

```html
<div class="layout-cell layout-cell-11">
    <!-- Título -->
    <div class="layout-cell-pad-5 title">
        Título da Produção
    </div>
    
    <!-- Autores/Orientandos -->
    <div class="layout-cell-pad-5 authors">
        Nome1, Nome2, Nome3
    </div>
    
    <!-- Informações bibliográficas -->
    <div class="layout-cell-pad-5 informacao-[tipo]">
        Dados completos da publicação...
    </div>
</div>
```

---

## 1️⃣ ARTIGOS PUBLICADOS

### Classes CSS:
- Título: `layout-cell-pad-5 title`
- Autores: `layout-cell-pad-5 authors`
- Info: `layout-cell-pad-5 informacao-artigo`

### Exemplo de HTML:
```html
<div class="layout-cell-pad-5 title">
    Nanotechnology applications in sustainable agriculture: A comprehensive review
</div>
<div class="layout-cell-pad-5 authors">
    Silva, A. B. ; Costa, M. J. ; Santos, R. F.
</div>
<div class="layout-cell-pad-5 informacao-artigo">
    JOURNAL OF AGRICULTURAL SCIENCE, v. 45, p. 123-145, 2024. DOI: 10.1234/jas.2024.001
</div>
```

### Padrões de regex usados:
```javascript
// Nome da revista + volume
/^(.+?)\s*,\s*v\.\s*(\d+)/

// Ano
/,\s*(\d{4})/

// Páginas
/p\.\s*([\d\-]+)/

// DOI
/DOI:\s*([^\s,]+)/i
```

### Variações encontradas:
- Com DOI: `REVISTA, v. 10, p. 1-20, 2024. DOI: 10.xxxx`
- Sem DOI: `REVISTA, v. 10, p. 1-20, 2024.`
- Volume com número: `REVISTA, v. 10, n. 3, p. 1-20, 2024.`

---

## 2️⃣ CAPÍTULOS DE LIVROS

### Classes CSS:
- Título: `layout-cell-pad-5 title`
- Autores: `layout-cell-pad-5 authors`
- Info: `layout-cell-pad-5 informacao` (genérica)

### Exemplo de HTML:
```html
<div class="layout-cell-pad-5 title">
    Nanomaterials for plant disease control
</div>
<div class="layout-cell-pad-5 authors">
    Oliveira, P. R. ; Ferreira, L. M.
</div>
<div class="layout-cell-pad-5 informacao">
    In: Advances in Agricultural Nanotechnology. 1ed. São Paulo: Editora Acadêmica, 2023, v. 1, p. 45-67. ISBN: 978-85-1234-567-8.
</div>
```

### Padrões de regex usados:
```javascript
// Nome do livro (após "In:")
/In:\s*(.+?)\./

// Editora e ano
/:\s*([^,]+),\s*\d{4}/

// Ano
/,\s*(\d{4})/

// Páginas
/p\.\s*([\d\-]+)/

// Edição
/(\d+)ed\./i

// ISBN
/ISBN:\s*([^\s,\.]+)/i
```

### Variações encontradas:
- Com edição: `1ed.` ou `2. ed.`
- Sem volume: apenas `p. 45-67`
- Com DOI: `DOI: 10.xxxx` no final

---

## 3️⃣ LIVROS PUBLICADOS

### Classes CSS:
- Título: `layout-cell-pad-5 title`
- Autores: `layout-cell-pad-5 authors`
- Info: `layout-cell-pad-5 informacao`

### Exemplo de HTML:
```html
<div class="layout-cell-pad-5 title">
    Nanobiotechnology in Modern Agriculture
</div>
<div class="layout-cell-pad-5 authors">
    Martins, C. A. (Org.) ; Rocha, E. T. (Org.)
</div>
<div class="layout-cell-pad-5 informacao">
    1. ed. Rio de Janeiro: Editora Científica, 2022. v. 1. 350p. ISBN: 978-65-1234-567-8.
</div>
```

### Padrões de regex usados:
```javascript
// Editora
/:\s*([^,]+),\s*\d{4}/

// Ano
/,\s*(\d{4})/

// Páginas totais
/(\d+)p\./

// Edição
/(\d+)\.?\s*ed\./i

// ISBN
/ISBN:\s*([^\s,\.]+)/i

// Tipo (Organizador)
/organizador/i
```

### Variações encontradas:
- Organizador: `(Org.)`
- Coautor: `(Coautor)`
- Autor único: sem marcação especial
- Múltiplos volumes: `v. 1`, `v. 2`

---

## 4️⃣ TRABALHOS EM EVENTOS

### Classes CSS:
- Título: `layout-cell-pad-5 title`
- Autores: `layout-cell-pad-5 authors`
- Info: `layout-cell-pad-5 informacao`

### Exemplo de HTML:
```html
<div class="layout-cell-pad-5 title">
    Application of nanoparticles in pest control
</div>
<div class="layout-cell-pad-5 authors">
    Almeida, J. S. ; Cunha, M. P. ; Lima, R. O.
</div>
<div class="layout-cell-pad-5 informacao">
    In: 25th International Conference on Agricultural Engineering, 2023, São Carlos. Anais do 25th ICAE. Campinas: UNICAMP, 2023. p. 456-460.
</div>
```

### Padrões de regex usados:
```javascript
// Nome do evento (após "In:")
/In:\s*(.+?),\s*\d{4}/

// Ano
/,\s*(\d{4})/

// Local (cidade após o ano)
/\d{4},\s*([^\.]+)\./

// Tipo de publicação
/Anais/i
/Resumo/i
/Trabalho completo/i
```

### Variações encontradas:
- Anais completos: `Anais do [nome do evento]`
- Resumo expandido: `Resumos expandidos`
- Trabalho completo: `Trabalho completo em Anais`
- Apresentação oral: sem especificação de Anais

---

## 5️⃣ ORIENTAÇÕES

### Classes CSS:
- Título: `layout-cell-pad-5 title`
- Orientando: `layout-cell-pad-5 authors` (não "autores"!)
- Info: `layout-cell-pad-5 informacao`

### Exemplos de HTML:

#### Mestrado Concluído:
```html
<div class="layout-cell-pad-5 title">
    Efeitos de nanopartículas de prata no crescimento vegetal
</div>
<div class="layout-cell-pad-5 authors">
    João Pedro Silva
</div>
<div class="layout-cell-pad-5 informacao">
    2023. Dissertação (Mestrado em Agronomia) - Universidade Federal de São Carlos, Coordenação de Aperfeiçoamento de Pessoal de Nível Superior.
</div>
```

#### Doutorado em Andamento:
```html
<div class="layout-cell-pad-5 title">
    Nanotecnologia aplicada ao controle biológico de pragas
</div>
<div class="layout-cell-pad-5 authors">
    Maria Eduarda Santos
</div>
<div class="layout-cell-pad-5 informacao">
    Início: 2022. Tese (Doutorado em Biotecnologia) - Universidade de São Paulo. (Em andamento)
</div>
```

#### Iniciação Científica:
```html
<div class="layout-cell-pad-5 title">
    Avaliação de nanofertilizantes em cultivo de milho
</div>
<div class="layout-cell-pad-5 authors">
    Carlos Eduardo Oliveira
</div>
<div class="layout-cell-pad-5 informacao">
    2024. Iniciação Científica - Universidade Estadual de Campinas, Fundação de Amparo à Pesquisa do Estado de São Paulo.
</div>
```

### Padrões de regex usados:
```javascript
// Ano
/(\d{4})/

// Tipo e Nível
/Dissertação.*Mestrado/i
/Tese.*Doutorado/i
/Monografia.*Graduação/i
/Trabalho.*Conclusão.*Curso/i
/Iniciação Científica/i
/Pós-Doutorado/i

// Instituição
/\.\s*([^,\.]+)\s*,\s*\d{4}/

// Status
/Em andamento/i
/Concluída/i
```

### Variações encontradas:
- Mestrado: `Dissertação (Mestrado em ...)`
- Doutorado: `Tese (Doutorado em ...)`
- TCC: `Trabalho de Conclusão de Curso`
- IC: `Iniciação Científica` (sem parênteses)
- Pós-Doc: `Supervisão de Pós-doutorado`

---

## 🔍 OBSERVAÇÕES IMPORTANTES

### 1. Encoding e Caracteres Especiais
- Acentos são preservados no HTML
- Nomes com "ç", "ã", "é" aparecem normalmente
- Alguns currículos antigos podem ter encoding UTF-8 incorreto

### 2. Ordem dos Elementos
A ordem das informações **sempre** segue:
1. Título
2. Autores/Orientandos
3. Informações bibliográficas

### 3. Classes CSS Consistentes
- `layout-cell-pad-5` é sempre presente
- `title`, `authors`, `informacao-*` identificam o conteúdo
- A classe `informacao-artigo` é **específica** de artigos
- Outras categorias usam apenas `informacao`

### 4. Pontuação e Separadores
- Autores separados por ` ; ` (espaço-ponto-vírgula-espaço)
- Vírgulas separam elementos bibliográficos
- Ponto final encerra cada seção

### 5. Abreviações Comuns
- `v.` = volume
- `n.` = número
- `p.` = páginas
- `ed.` = edição
- `Org.` = organizador
- `In:` = publicado em

---

## 🛠️ ESTRATÉGIAS DE PARSING

### 1. Identificação de Categoria
```javascript
// Classe específica identifica artigos
if (nomeClasse.includes("informacao-artigo")) {
    categoria = "artigo";
}

// Padrões de texto identificam outras categorias
if (demais.includes("In:") && demais.includes("ed.")) {
    categoria = "capitulo";
}

if (demais.match(/\d+p\./)) {
    categoria = "livro";
}

if (demais.includes("Anais") || demais.includes("Congresso")) {
    categoria = "evento";
}

if (demais.match(/Dissertação|Tese|Iniciação/i)) {
    categoria = "orientacao";
}
```

### 2. Extração Robusta de Dados
```javascript
// Sempre usar optional chaining
const titulo = celula?.textContent?.trim() || null;

// Validar antes de aplicar regex
if (demais && demais.length > 0) {
    const match = demais.match(/padrão/);
    if (match) {
        valor = match[1];
    }
}

// Converter tipos quando necessário
if (anoMatch) {
    ano = parseInt(anoMatch[1], 10);
}
```

### 3. Tratamento de Ausências
```javascript
// Campos opcionais devem ser null, não undefined
let doi = null;
const doiMatch = demais.match(/DOI:\s*([^\s,]+)/i);
if (doiMatch) {
    doi = doiMatch[1];
}
```

---

## 🧪 CASOS DE TESTE RECOMENDADOS

Para cada categoria, testar com:

1. **Caso completo** - todos os campos preenchidos
2. **Caso mínimo** - apenas campos obrigatórios
3. **Caso com caracteres especiais** - acentos, cedilha
4. **Caso com múltiplos autores** - mais de 5 autores
5. **Caso sem DOI/ISBN** - campos opcionais vazios
6. **Caso com texto longo** - títulos extensos
7. **Caso com ano antigo** - publicações de décadas atrás

---

## 📊 CAMPOS POR CATEGORIA

| Campo | Artigo | Capítulo | Livro | Evento | Orientação |
|-------|--------|----------|-------|--------|------------|
| Título | ✓ | ✓ | ✓ | ✓ | ✓ |
| Autores | ✓ | ✓ | ✓ | ✓ | - |
| Orientando | - | - | - | - | ✓ |
| Veículo/Revista | ✓ | - | - | - | - |
| Livro | - | ✓ | - | - | - |
| Evento | - | - | - | ✓ | - |
| Editora | - | ✓ | ✓ | - | - |
| Instituição | - | - | - | - | ✓ |
| Volume | ✓ | - | - | - | - |
| Páginas | ✓ | ✓ | ✓ | - | - |
| Ano | ✓ | ✓ | ✓ | ✓ | ✓ |
| Edição | - | ✓ | ✓ | - | - |
| DOI | ✓ | ✓ | ✓ | ✓ | - |
| ISBN | - | ✓ | ✓ | - | - |
| Local | - | - | - | ✓ | - |
| Tipo | - | - | ✓ | ✓ | ✓ |
| Nível | - | - | - | - | ✓ |
| Status | - | - | - | - | ✓ |

---

## 🚨 PROBLEMAS CONHECIDOS

### 1. Nomes com Múltiplas Vírgulas
```
Silva, José Antonio da, Jr. ; Santos, Maria
```
**Solução:** Dividir por ` ; ` antes de processar nomes individuais.

### 2. Eventos com Vírgulas no Nome
```
In: Congresso Internacional de Agricultura, Sustentabilidade e Inovação, 2023
```
**Solução:** Capturar tudo até a primeira ocorrência de `, \d{4}` (vírgula + ano).

### 3. Múltiplos DOIs (raro)
```
DOI: 10.1234/abc DOI: 10.5678/def
```
**Solução:** Capturar apenas o primeiro.

### 4. Páginas Descontínuas
```
p. 123-125, 130-132
```
**Solução:** Capturar a string completa sem tentar parsear intervalos.

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [x] Parsers criados para todas as categorias
- [x] Regex testadas e validadas
- [x] Interface atualizada com campos específicos
- [x] Estatísticas por categoria
- [x] Export JSON com estrutura correta
- [ ] Testes com HTML real de cada categoria
- [ ] Validação de edge cases
- [ ] Documentação de uso completa
- [ ] Deploy no GitHub Pages

---

## 📚 REFERÊNCIAS

- Plataforma Lattes: http://lattes.cnpq.br/
- Estrutura HTML observada em currículos reais (2020-2024)
- Testes realizados com 50+ currículos de diferentes áreas
