/* ====================================
   PARSERS PARA CATEGORIAS DO LATTES
   ==================================== */

// ============================================
// 1. ARTIGOS (já implementado - mantido)
// ============================================
function extrairArtigos(html) {
    const resultados = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const layoutTabela = doc.querySelectorAll(
        'div[class*="layout-cell-pad-5"]',
    );

    layoutTabela.forEach((celula) => {
        const nomeClasse = celula.className || "";

        if (
            nomeClasse.includes("title") &&
            !nomeClasse.includes("informacao-artigo")
        ) {
            const titulo = celula.textContent.trim();
            const divPai = celula.closest(".layout-cell");

            if (!divPai) return;

            const autoresDiv = divPai.querySelector(
                'div[class*="authors"]',
            );
            const demaisDiv = divPai.querySelector(
                'div[class*="informacao-artigo"]',
            );

            const autores = autoresDiv
                ? autoresDiv.textContent.trim()
                : null;
            const demais = demaisDiv
                ? demaisDiv.textContent.trim()
                : null;

            let veiculo = null,
                ano = null,
                volume = null,
                paginas = null,
                doi = null;

            if (demais) {
                const match = demais.match(/^(.+?)\s*,\s*v\.\s*(\d+)/);
                if (match) {
                    veiculo = match[1].trim();
                    volume = match[2];
                }

                const anoMatch = demais.match(/,\s*(\d{4})/);
                if (anoMatch) {
                    ano = parseInt(anoMatch[1], 10);
                }

                const paginasMatch = demais.match(/p\.\s*([\d\-]+)/);
                if (paginasMatch) {
                    paginas = paginasMatch[1];
                }

                const doiMatch = demais.match(/DOI:\s*([^\s,]+)/i);
                if (doiMatch) {
                    doi = doiMatch[1];
                }
            }

            resultados.push({
                categoria: "artigo",
                titulo,
                autores,
                veiculo,
                ano,
                volume,
                paginas,
                doi,
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

    const layoutTabela = doc.querySelectorAll(
        'div[class*="layout-cell-pad-5"]',
    );

    layoutTabela.forEach((celula) => {
        const nomeClasse = celula.className || "";

        // Identifica títulos de capítulos
        if (
            nomeClasse.includes("title") &&
            !nomeClasse.includes("informacao")
        ) {
            const titulo = celula.textContent.trim();
            const divPai = celula.closest(".layout-cell");

            if (!divPai) return;

            const autoresDiv = divPai.querySelector(
                'div[class*="authors"]',
            );
            const demaisDiv = divPai.querySelector(
                'div[class*="informacao"]',
            );

            const autores = autoresDiv
                ? autoresDiv.textContent.trim()
                : null;
            const demais = demaisDiv
                ? demaisDiv.textContent.trim()
                : null;

            let livro = null,
                ano = null,
                paginas = null,
                editora = null,
                edicao = null,
                isbn = null,
                doi = null;

            if (demais) {
                // Extrai nome do livro (geralmente após "In:")
                const livroMatch = demais.match(/In:\s*(.+?)\./);
                if (livroMatch) {
                    livro = livroMatch[1].trim();
                }

                // Extrai ano
                const anoMatch = demais.match(/,\s*(\d{4})/);
                if (anoMatch) {
                    ano = parseInt(anoMatch[1], 10);
                }

                // Extrai páginas (formatos: p. 123-456 ou p.123-456)
                const paginasMatch = demais.match(/p\.\s*([\d\-]+)/);
                if (paginasMatch) {
                    paginas = paginasMatch[1];
                }

                // Extrai editora
                const editoraMatch = demais.match(/:\s*([^,]+),\s*\d{4}/);
                if (editoraMatch) {
                    editora = editoraMatch[1].trim();
                }

                // Extrai edição
                const edicaoMatch = demais.match(/(\d+)ed\./i);
                if (edicaoMatch) {
                    edicao = edicaoMatch[1];
                }

                // Extrai ISBN
                const isbnMatch = demais.match(/ISBN:\s*([^\s,\.]+)/i);
                if (isbnMatch) {
                    isbn = isbnMatch[1];
                }

                // Extrai DOI
                const doiMatch = demais.match(/DOI:\s*([^\s,]+)/i);
                if (doiMatch) {
                    doi = doiMatch[1];
                }
            }

            resultados.push({
                categoria: "capitulo",
                titulo,
                autores,
                livro,
                ano,
                paginas,
                editora,
                edicao,
                isbn,
                doi,
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

    const layoutTabela = doc.querySelectorAll(
        'div[class*="layout-cell-pad-5"]',
    );

    layoutTabela.forEach((celula) => {
        const nomeClasse = celula.className || "";

        if (
            nomeClasse.includes("title") &&
            !nomeClasse.includes("informacao")
        ) {
            const titulo = celula.textContent.trim();
            const divPai = celula.closest(".layout-cell");

            if (!divPai) return;

            const autoresDiv = divPai.querySelector(
                'div[class*="authors"]',
            );
            const demaisDiv = divPai.querySelector(
                'div[class*="informacao"]',
            );

            const autores = autoresDiv
                ? autoresDiv.textContent.trim()
                : null;
            const demais = demaisDiv
                ? demaisDiv.textContent.trim()
                : null;

            let ano = null,
                paginas = null,
                editora = null,
                edicao = null,
                isbn = null,
                doi = null,
                tipo = null;

            if (demais) {
                // Extrai ano
                const anoMatch = demais.match(/,\s*(\d{4})/);
                if (anoMatch) {
                    ano = parseInt(anoMatch[1], 10);
                }

                // Extrai número de páginas (formato: 123p.)
                const paginasMatch = demais.match(/(\d+)p\./);
                if (paginasMatch) {
                    paginas = paginasMatch[1];
                }

                // Extrai editora (geralmente antes do ano)
                const editoraMatch = demais.match(/:\s*([^,]+),\s*\d{4}/);
                if (editoraMatch) {
                    editora = editoraMatch[1].trim();
                }

                // Extrai edição
                const edicaoMatch = demais.match(/(\d+)\.?\s*ed\./i);
                if (edicaoMatch) {
                    edicao = edicaoMatch[1];
                }

                // Extrai ISBN
                const isbnMatch = demais.match(/ISBN:\s*([^\s,\.]+)/i);
                if (isbnMatch) {
                    isbn = isbnMatch[1];
                }

                // Extrai DOI
                const doiMatch = demais.match(/DOI:\s*([^\s,]+)/i);
                if (doiMatch) {
                    doi = doiMatch[1];
                }

                // Identifica tipo de livro
                if (demais.match(/organizador/i)) {
                    tipo = "Organizador";
                } else if (demais.match(/coautor/i)) {
                    tipo = "Coautor";
                } else {
                    tipo = "Autor";
                }
            }

            resultados.push({
                categoria: "livro",
                titulo,
                autores,
                ano,
                paginas,
                editora,
                edicao,
                isbn,
                doi,
                tipo,
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

    const layoutTabela = doc.querySelectorAll(
        'div[class*="layout-cell-pad-5"]',
    );

    layoutTabela.forEach((celula) => {
        const nomeClasse = celula.className || "";

        if (
            nomeClasse.includes("title") &&
            !nomeClasse.includes("informacao")
        ) {
            const titulo = celula.textContent.trim();
            const divPai = celula.closest(".layout-cell");

            if (!divPai) return;

            const autoresDiv = divPai.querySelector(
                'div[class*="authors"]',
            );
            const demaisDiv = divPai.querySelector(
                'div[class*="informacao"]',
            );

            const autores = autoresDiv
                ? autoresDiv.textContent.trim()
                : null;
            const demais = demaisDiv
                ? demaisDiv.textContent.trim()
                : null;

            let evento = null,
                ano = null,
                local = null,
                tipo = null,
                doi = null;

            if (demais) {
                // Extrai nome do evento (geralmente após "In:")
                const eventoMatch = demais.match(/In:\s*(.+?),\s*\d{4}/);
                if (eventoMatch) {
                    evento = eventoMatch[1].trim();
                }

                // Extrai ano
                const anoMatch = demais.match(/,\s*(\d{4})/);
                if (anoMatch) {
                    ano = parseInt(anoMatch[1], 10);
                }

                // Extrai local (cidade)
                const localMatch = demais.match(/\d{4},\s*([^\.]+)\./);
                if (localMatch) {
                    local = localMatch[1].trim();
                }

                // Identifica tipo de publicação
                if (demais.match(/Anais/i)) {
                    tipo = "Anais";
                } else if (demais.match(/Resumo/i)) {
                    tipo = "Resumo";
                } else if (demais.match(/Trabalho completo/i)) {
                    tipo = "Trabalho completo";
                } else {
                    tipo = "Apresentação";
                }

                // Extrai DOI
                const doiMatch = demais.match(/DOI:\s*([^\s,]+)/i);
                if (doiMatch) {
                    doi = doiMatch[1];
                }
            }

            resultados.push({
                categoria: "evento",
                titulo,
                autores,
                evento,
                ano,
                local,
                tipo,
                doi,
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

    const layoutTabela = doc.querySelectorAll(
        'div[class*="layout-cell-pad-5"]',
    );

    layoutTabela.forEach((celula) => {
        const nomeClasse = celula.className || "";

        if (
            nomeClasse.includes("title") &&
            !nomeClasse.includes("informacao")
        ) {
            const titulo = celula.textContent.trim();
            const divPai = celula.closest(".layout-cell");

            if (!divPai) return;

            const autoresDiv = divPai.querySelector(
                'div[class*="authors"]',
            );
            const demaisDiv = divPai.querySelector(
                'div[class*="informacao"]',
            );

            // Para orientações, o campo "autores" é o orientando
            const orientando = autoresDiv
                ? autoresDiv.textContent.trim()
                : null;
            const demais = demaisDiv
                ? demaisDiv.textContent.trim()
                : null;

            let ano = null,
                tipo = null,
                instituicao = null,
                nivel = null,
                status = null;

            if (demais) {
                // Extrai ano
                const anoMatch = demais.match(/(\d{4})/);
                if (anoMatch) {
                    ano = parseInt(anoMatch[1], 10);
                }

                // Identifica tipo e nível
                if (demais.match(/Dissertação.*Mestrado/i)) {
                    tipo = "Dissertação";
                    nivel = "Mestrado";
                } else if (demais.match(/Tese.*Doutorado/i)) {
                    tipo = "Tese";
                    nivel = "Doutorado";
                } else if (demais.match(/Monografia.*Graduação/i)) {
                    tipo = "Monografia";
                    nivel = "Graduação";
                } else if (demais.match(/Trabalho.*Conclusão.*Curso/i)) {
                    tipo = "TCC";
                    nivel = "Graduação";
                } else if (demais.match(/Iniciação Científica/i)) {
                    tipo = "Iniciação Científica";
                    nivel = "Graduação";
                } else if (demais.match(/Pós-Doutorado/i)) {
                    tipo = "Supervisão";
                    nivel = "Pós-Doutorado";
                }

                // Extrai instituição
                const instituicaoMatch = demais.match(/\.\s*([^,\.]+)\s*,\s*\d{4}/);
                if (instituicaoMatch) {
                    instituicao = instituicaoMatch[1].trim();
                }

                // Identifica status
                if (demais.match(/Em andamento/i)) {
                    status = "Em andamento";
                } else if (demais.match(/Concluída/i) || demais.match(/Concluído/i)) {
                    status = "Concluída";
                } else {
                    status = "Concluída"; // padrão
                }
            }

            resultados.push({
                categoria: "orientacao",
                titulo,
                orientando,
                ano,
                tipo,
                nivel,
                instituicao,
                status,
            });
        }
    });

    return resultados;
}

// ============================================
// FUNÇÃO PRINCIPAL DE INGESTÃO (atualizada)
// ============================================
function ingerir(html, categoria) {
    let resultados = [];

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

    // Adiciona ID único e ordem do Lattes
    return resultados.map((item, index) => ({
        id: nextId++,
        ordem_lattes: index + 1,
        ...item,
    }));
}
