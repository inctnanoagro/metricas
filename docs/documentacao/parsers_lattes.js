/* ====================================
   PARSERS CORRETOS PARA LATTES
   Baseados na estrutura real do HTML
==================================== */

// ============================================
// 1. ARTIGOS PUBLICADOS
// ============================================
function extrairArtigos(html) {
    const resultados = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    
    // Seleciona divs de artigos completos
    const artigos = doc.querySelectorAll('.artigo-completo, .layout-cell-11');
    
    artigos.forEach((div) => {
        // Procura o span.transform que contém o texto
        const transformSpan = div.querySelector('span.transform');
        if (!transformSpan) return;
        
        const textoCompleto = transformSpan.textContent.trim();
        if (!textoCompleto) return;
        
        // Extrai os dados usando regex no texto completo
        let titulo = null, autores = null, veiculo = null, ano = null, 
            volume = null, paginas = null, doi = null;
        
        // Regex para capturar título (texto entre último ". " e nome da revista)
        // Padrão: AUTORES . Título. Nome do periódico, v. X, p. Y, ANO.
        const tituloMatch = textoCompleto.match(/\.\s+([^.]+)\.\s+([^,]+),\s*v\./);
        if (tituloMatch) {
            titulo = tituloMatch[1].trim();
            veiculo = tituloMatch[2].trim();
        }
        
        // Extrai autores (tudo antes do título)
        const autoresMatch = textoCompleto.match(/^(.+?)\.\s+[^.]+\.\s+[^,]+,/);
        if (autoresMatch) {
            autores = autoresMatch[1].trim();
        }
        
        // Extrai volume
        const volumeMatch = textoCompleto.match(/v\.\s*(\d+)/);
        if (volumeMatch) {
            volume = volumeMatch[1];
        }
        
        // Extrai páginas
        const paginasMatch = textoCompleto.match(/p\.\s*([\d\-]+)/);
        if (paginasMatch) {
            paginas = paginasMatch[1];
        }
        
        // Extrai ano (número de 4 dígitos no final)
        const anoMatch = textoCompleto.match(/,\s*(\d{4})\s*\.?\s*$/);
        if (anoMatch) {
            ano = parseInt(anoMatch[1], 10);
        }
        
        // Extrai DOI se houver link
        const doiLink = div.querySelector('a.icone-doi');
        if (doiLink) {
            const href = doiLink.getAttribute('href');
            const doiMatch = href.match(/10\.\d+\/[^\s]+/);
            if (doiMatch) {
                doi = doiMatch[0];
            }
        }
        
        if (titulo && autores) {
            resultados.push({
                categoria: "artigo",
                titulo,
                autores,
                veiculo,
                ano,
                volume,
                paginas,
                doi
            });
        }
    });
    
    return resultados;
}

// ============================================
// 2. CAPÍTULOS DE LIVROS
// ============================================
function extrairCapitulos(html) {
    const resultados = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    
    // Seleciona todas as células de conteúdo
    const celulas = doc.querySelectorAll('.layout-cell-11');
    
    celulas.forEach((div) => {
        const transformSpan = div.querySelector('span.transform');
        if (!transformSpan) return;
        
        const textoCompleto = transformSpan.textContent.trim();
        if (!textoCompleto || !textoCompleto.includes('In:')) return;
        
        // Padrão: AUTORES . Título. In: EDITORES (Org.). Título do livro. Ed: Editora, Ano, p. X-Y.
        
        let titulo = null, autores = null, livro = null, editora = null,
            edicao = null, ano = null, paginas = null, isbn = null, doi = null;
        
        // Extrai título do capítulo (antes de "In:")
        const tituloMatch = textoCompleto.match(/\.\s+([^.]+)\.\s+In:/);
        if (tituloMatch) {
            titulo = tituloMatch[1].trim();
        }
        
        // Extrai autores (antes do título)
        const autoresMatch = textoCompleto.match(/^(.+?)\.\s+[^.]+\.\s+In:/);
        if (autoresMatch) {
            autores = autoresMatch[1].trim();
        }
        
        // Extrai título do livro (após "(Org)." e antes da edição)
        const livroMatch = textoCompleto.match(/\(Org\.\)\.\s*([^.]+)\.\s*(\d+)ed/i);
        if (livroMatch) {
            livro = livroMatch[1].trim();
            edicao = livroMatch[2];
        }
        
        // Extrai editora (após ":" e antes do ano)
        const editoraMatch = textoCompleto.match(/:\s*([^,]+),\s*\d{4}/);
        if (editoraMatch) {
            editora = editoraMatch[1].trim();
        }
        
        // Extrai ano
        const anoMatch = textoCompleto.match(/,\s*(\d{4})/);
        if (anoMatch) {
            ano = parseInt(anoMatch[1], 10);
        }
        
        // Extrai páginas
        const paginasMatch = textoCompleto.match(/p\.\s*([\d\-]+)/);
        if (paginasMatch) {
            paginas = paginasMatch[1];
        }
        
        // Extrai DOI
        const doiLink = div.querySelector('a.icone-doi');
        if (doiLink) {
            const href = doiLink.getAttribute('href');
            const doiMatch = href.match(/10\.\d+\/[^\s]+/);
            if (doiMatch) {
                doi = doiMatch[0];
            }
        }
        
        // Extrai ISBN
        const isbnMatch = textoCompleto.match(/ISBN[:\s]*([\d\-]+)/i);
        if (isbnMatch) {
            isbn = isbnMatch[1];
        }
        
        if (titulo && autores) {
            resultados.push({
                categoria: "capitulo",
                titulo,
                autores,
                livro,
                editora,
                edicao,
                ano,
                paginas,
                isbn,
                doi
            });
        }
    });
    
    return resultados;
}

// ============================================
// 3. LIVROS PUBLICADOS
// ============================================
function extrairLivros(html) {
    const resultados = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    
    const celulas = doc.querySelectorAll('.layout-cell-11');
    
    celulas.forEach((div) => {
        const transformSpan = div.querySelector('span.transform');
        if (!transformSpan) return;
        
        const textoCompleto = transformSpan.textContent.trim();
        if (!textoCompleto || textoCompleto.includes('In:')) return;
        
        // Padrão: AUTORES (Org.). Título. Edição. Editora, Ano. v. X. Yp.
        
        let titulo = null, autores = null, editora = null, edicao = null,
            ano = null, paginas = null, tipo = null, isbn = null, doi = null;
        
        // Identifica se é organizador
        if (textoCompleto.includes('(Org.)') || textoCompleto.includes('(Org)')) {
            tipo = "Organizador";
        } else if (textoCompleto.includes('(Coautor)')) {
            tipo = "Coautor";
        } else {
            tipo = "Autor";
        }
        
        // Extrai autores (até o primeiro ponto antes do título)
        const autoresMatch = textoCompleto.match(/^(.+?)\s*\.\s+/);
        if (autoresMatch) {
            autores = autoresMatch[1].trim();
        }
        
        // Extrai título (entre autores e edição/editora)
        const tituloMatch = textoCompleto.match(/\.\s+([^.]+)\.\s+(\d+\.?\s*ed\.?|[^,]+,)/i);
        if (tituloMatch) {
            titulo = tituloMatch[1].trim();
        }
        
        // Extrai edição
        const edicaoMatch = textoCompleto.match(/(\d+)\.?\s*ed\./i);
        if (edicaoMatch) {
            edicao = edicaoMatch[1];
        }
        
        // Extrai editora (texto antes do ano)
        const editoraMatch = textoCompleto.match(/\.?\s*([^,]+),\s*\d{4}/);
        if (editoraMatch) {
            editora = editoraMatch[1].trim();
        }
        
        // Extrai ano
        const anoMatch = textoCompleto.match(/,\s*(\d{4})/);
        if (anoMatch) {
            ano = parseInt(anoMatch[1], 10);
        }
        
        // Extrai número de páginas
        const paginasMatch = textoCompleto.match(/(\d+)p\s*\.?\s*$/);
        if (paginasMatch) {
            paginas = paginasMatch[1];
        }
        
        // Extrai DOI
        const doiLink = div.querySelector('a.icone-doi');
        if (doiLink) {
            const href = doiLink.getAttribute('href');
            const doiMatch = href.match(/10\.\d+\/[^\s]+/);
            if (doiMatch) {
                doi = doiMatch[0];
            }
        }
        
        // Extrai ISBN
        const isbnMatch = textoCompleto.match(/ISBN[:\s]*([\d\-]+)/i);
        if (isbnMatch) {
            isbn = isbnMatch[1];
        }
        
        if (titulo && autores) {
            resultados.push({
                categoria: "livro",
                titulo,
                autores,
                editora,
                edicao,
                ano,
                paginas,
                tipo,
                isbn,
                doi
            });
        }
    });
    
    return resultados;
}

// ============================================
// 4. TRABALHOS EM EVENTOS
// ============================================
function extrairEventos(html) {
    const resultados = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    
    const celulas = doc.querySelectorAll('.layout-cell-11');
    
    celulas.forEach((div) => {
        const transformSpan = div.querySelector('span.transform');
        if (!transformSpan) return;
        
        const textoCompleto = transformSpan.textContent.trim();
        
        // Identifica trabalhos em eventos pela presença de "In:" e palavras-chave
        if (!textoCompleto.includes('In:') || 
            (!textoCompleto.includes('Congresso') && 
             !textoCompleto.includes('Simpósio') && 
             !textoCompleto.includes('Conferência') &&
             !textoCompleto.includes('Anais'))) {
            return;
        }
        
        // Padrão: AUTORES . Título. In: Evento, Ano, Local. Anais. Editora, Ano. p. X-Y.
        
        let titulo = null, autores = null, evento = null, ano = null,
            local = null, tipo = null, doi = null;
        
        // Extrai título (antes de "In:")
        const tituloMatch = textoCompleto.match(/\.\s+([^.]+)\.\s+In:/);
        if (tituloMatch) {
            titulo = tituloMatch[1].trim();
        }
        
        // Extrai autores
        const autoresMatch = textoCompleto.match(/^(.+?)\.\s+[^.]+\.\s+In:/);
        if (autoresMatch) {
            autores = autoresMatch[1].trim();
        }
        
        // Extrai nome do evento (após "In:" até ano)
        const eventoMatch = textoCompleto.match(/In:\s*([^,]+),\s*\d{4}/);
        if (eventoMatch) {
            evento = eventoMatch[1].trim();
        }
        
        // Extrai local (após ano, antes do ponto)
        const localMatch = textoCompleto.match(/,\s*\d{4},\s*([^.]+)\./);
        if (localMatch) {
            local = localMatch[1].trim();
        }
        
        // Extrai ano (primeiro ano após "In:")
        const anoMatch = textoCompleto.match(/In:[^,]+,\s*(\d{4})/);
        if (anoMatch) {
            ano = parseInt(anoMatch[1], 10);
        }
        
        // Identifica tipo
        if (textoCompleto.includes('Anais')) {
            tipo = "Anais";
        } else if (textoCompleto.includes('Resumo')) {
            tipo = "Resumo";
        } else {
            tipo = "Apresentação";
        }
        
        // Extrai DOI
        const doiLink = div.querySelector('a.icone-doi');
        if (doiLink) {
            const href = doiLink.getAttribute('href');
            const doiMatch = href.match(/10\.\d+\/[^\s]+/);
            if (doiMatch) {
                doi = doiMatch[0];
            }
        }
        
        if (titulo && autores) {
            resultados.push({
                categoria: "evento",
                titulo,
                autores,
                evento,
                ano,
                local,
                tipo,
                doi
            });
        }
    });
    
    return resultados;
}

// ============================================
// 5. ORIENTAÇÕES
// ============================================
function extrairOrientacoes(html) {
    const resultados = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    
    const celulas = doc.querySelectorAll('.layout-cell-11');
    
    celulas.forEach((div) => {
        const transformSpan = div.querySelector('span.transform');
        if (!transformSpan) return;
        
        const textoCompleto = transformSpan.textContent.trim();
        
        // Identifica orientações pela presença de palavras-chave
        if (!textoCompleto.includes('Orientador') && 
            !textoCompleto.includes('Coorientador') &&
            !textoCompleto.includes('Início:') &&
            !textoCompleto.includes('Mestrado') &&
            !textoCompleto.includes('Doutorado')) {
            return;
        }
        
        // Padrão: NOME. TÍTULO. Início: ANO. Tipo (Curso) - Instituição. (Orientador).
        
        let orientando = null, titulo = null, ano = null, tipo = null,
            nivel = null, instituicao = null, status = null;
        
        // Extrai nome do orientando (primeira linha antes do ponto)
        const orientandoMatch = textoCompleto.match(/^([^.]+)\./);
        if (orientandoMatch) {
            orientando = orientandoMatch[1].trim();
        }
        
        // Extrai título (entre nome e "Início:" ou tipo de orientação)
        const tituloMatch = textoCompleto.match(/\.\s+([^.]+)\.\s+(Início:|Dissertação|Tese|Monografia)/);
        if (tituloMatch) {
            titulo = tituloMatch[1].trim();
        }
        
        // Extrai ano
        const anoMatch = textoCompleto.match(/Início:\s*(\d{4})|(\d{4})\./);
        if (anoMatch) {
            ano = parseInt(anoMatch[1] || anoMatch[2], 10);
        }
        
        // Identifica tipo e nível
        if (textoCompleto.includes('Dissertação') && textoCompleto.includes('Mestrado')) {
            tipo = "Dissertação";
            nivel = "Mestrado";
        } else if (textoCompleto.includes('Tese') && textoCompleto.includes('Doutorado')) {
            tipo = "Tese";
            nivel = "Doutorado";
        } else if (textoCompleto.includes('Iniciação Científica')) {
            tipo = "Iniciação Científica";
            nivel = "Graduação";
        } else if (textoCompleto.includes('Monografia') || textoCompleto.includes('Trabalho de Conclusão')) {
            tipo = "TCC";
            nivel = "Graduação";
        } else if (textoCompleto.includes('Pós-Doutorado')) {
            tipo = "Supervisão";
            nivel = "Pós-Doutorado";
        }
        
        // Extrai instituição (após o "-" e antes do ponto final)
        const instituicaoMatch = textoCompleto.match(/\)\s*-\s*([^.]+)\./);
        if (instituicaoMatch) {
            instituicao = instituicaoMatch[1].trim();
        }
        
        // Identifica status
        if (textoCompleto.includes('Início:') || textoCompleto.includes('Em andamento')) {
            status = "Em andamento";
        } else {
            status = "Concluída";
        }
        
        if (orientando && titulo) {
            resultados.push({
                categoria: "orientacao",
                titulo,
                orientando,
                ano,
                tipo,
                nivel,
                instituicao,
                status
            });
        }
    });
    
    return resultados;
}

// ============================================
// FUNÇÃO PRINCIPAL (mantida igual)
// ============================================
function ingerir(html, categoria) {
    let resultados = [];

    try {
        switch (categoria) {
            case "artigo":
                resultados = extrairArtigos(html);
                break;
            case "capitulo":
                resultados = extrairCapitulos(html);
                break;
            case "livro":
                resultados = extrairLivros(html);
                break;
            case "evento":
                resultados = extrairEventos(html);
                break;
            case "orientacao":
                resultados = extrairOrientacoes(html);
                break;
            default:
                console.error("Categoria desconhecida:", categoria);
                return [];
        }
    } catch (error) {
        console.error("Erro ao processar HTML:", error);
        return [];
    }

    return resultados.map((item, index) => ({
        id: nextId++,
        ordem_lattes: index + 1,
        ...item,
    }));
}
