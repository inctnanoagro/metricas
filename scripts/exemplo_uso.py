#!/usr/bin/env python3
"""
Exemplo prático de uso do sistema de parsing.

Demonstra como usar os parsers para extrair dados de fixtures Lattes.
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metricas_lattes.parser_router import parse_fixture


def exemplo_basico():
    """Exemplo básico: parse um único arquivo"""
    print("="*80)
    print("EXEMPLO 1: Parse básico de um arquivo")
    print("="*80)

    # Caminho para um fixture
    fixture_path = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes' / 'Artigos aceitos para publicação.html'

    # Parse o arquivo
    result = parse_fixture(fixture_path)

    # Mostrar informações básicas
    print(f"\nTipo de produção: {result['tipo_producao']}")
    print(f"Total de items: {len(result['items'])}")
    print(f"Schema version: {result['schema_version']}")

    # Mostrar primeiro item
    if result['items']:
        item = result['items'][0]
        print(f"\nPrimeiro item:")
        print(f"  Número: {item['numero_item']}")
        print(f"  Autores: {item.get('autores', 'N/A')}")
        print(f"  Título: {item.get('titulo', 'N/A')}")
        print(f"  Ano: {item.get('ano', 'N/A')}")


def exemplo_processamento_em_lote():
    """Exemplo: processar múltiplos arquivos"""
    print("\n")
    print("="*80)
    print("EXEMPLO 2: Processamento em lote")
    print("="*80)

    fixtures_dir = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes'

    # Lista de tipos específicos para processar
    tipos_interesse = [
        'Artigos completos publicados em periódicos.html',
        'Capítulos de livros publicados.html',
        'Textos em jornais de notícias_revistas.html'
    ]

    total_items = 0

    for tipo in tipos_interesse:
        fixture_path = fixtures_dir / tipo
        if not fixture_path.exists():
            continue

        result = parse_fixture(fixture_path)
        num_items = len(result['items'])
        total_items += num_items

        print(f"\n{tipo}")
        print(f"  Items extraídos: {num_items}")

        # Estatísticas
        items_com_doi = sum(1 for item in result['items'] if item.get('doi'))
        items_com_titulo = sum(1 for item in result['items'] if item.get('titulo'))

        print(f"  Com DOI: {items_com_doi}")
        print(f"  Com título: {items_com_titulo}")

    print(f"\nTotal de items em todos os tipos: {total_items}")


def exemplo_filtragem():
    """Exemplo: filtrar items por critérios"""
    print("\n")
    print("="*80)
    print("EXEMPLO 3: Filtragem de dados")
    print("="*80)

    fixture_path = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes' / 'Artigos completos publicados em periódicos.html'

    result = parse_fixture(fixture_path)

    # Filtrar: artigos de 2024 ou posterior
    artigos_recentes = [
        item for item in result['items']
        if item.get('ano') and item['ano'] >= 2024
    ]

    print(f"\nTotal de artigos: {len(result['items'])}")
    print(f"Artigos de 2024+: {len(artigos_recentes)}")

    # Mostrar alguns
    print(f"\nPrimeiros 3 artigos recentes:")
    for item in artigos_recentes[:3]:
        print(f"\n  [{item.get('ano')}] {item.get('titulo', 'Sem título')[:60]}...")
        if item.get('veiculo'):
            print(f"     Em: {item['veiculo']}")


def exemplo_exportacao():
    """Exemplo: exportar dados para JSON"""
    print("\n")
    print("="*80)
    print("EXEMPLO 4: Exportação para JSON")
    print("="*80)

    fixture_path = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes' / 'Capítulos de livros publicados.html'

    result = parse_fixture(fixture_path)

    # Criar diretório de output
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(exist_ok=True)

    # Salvar resultado completo
    output_path = output_dir / 'capitulos_parsed.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nResultado salvo em: {output_path}")
    print(f"Total de capítulos: {len(result['items'])}")

    # Criar versão simplificada (apenas campos principais)
    simplified = []
    for item in result['items']:
        simplified.append({
            'numero': item['numero_item'],
            'autores': item.get('autores'),
            'titulo': item.get('titulo'),
            'livro': item.get('livro'),
            'ano': item.get('ano')
        })

    simplified_path = output_dir / 'capitulos_simplificado.json'
    with open(simplified_path, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)

    print(f"Versão simplificada salva em: {simplified_path}")


def exemplo_agregacao():
    """Exemplo: agregar estatísticas por ano"""
    print("\n")
    print("="*80)
    print("EXEMPLO 5: Agregação e estatísticas")
    print("="*80)

    fixture_path = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'lattes' / 'Artigos completos publicados em periódicos.html'

    result = parse_fixture(fixture_path)

    # Contar por ano
    por_ano = {}
    for item in result['items']:
        ano = item.get('ano')
        if ano:
            por_ano[ano] = por_ano.get(ano, 0) + 1

    # Ordenar por ano
    anos_ordenados = sorted(por_ano.items(), reverse=True)

    print(f"\nDistribuição de artigos por ano:")
    print(f"{'Ano':<10} {'Quantidade':>10}")
    print("-" * 25)

    for ano, count in anos_ordenados[:10]:  # Top 10
        print(f"{ano:<10} {count:>10}")

    # Estatísticas
    total = len(result['items'])
    com_doi = sum(1 for item in result['items'] if item.get('doi'))
    com_volume = sum(1 for item in result['items'] if item.get('volume'))

    print(f"\nEstatísticas:")
    print(f"  Total: {total}")
    print(f"  Com DOI: {com_doi} ({com_doi/total*100:.1f}%)")
    print(f"  Com volume: {com_volume} ({com_volume/total*100:.1f}%)")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("EXEMPLOS DE USO - Sistema de Parsing Lattes")
    print("="*80)

    try:
        exemplo_basico()
        exemplo_processamento_em_lote()
        exemplo_filtragem()
        exemplo_exportacao()
        exemplo_agregacao()

        print("\n" + "="*80)
        print("EXEMPLOS CONCLUÍDOS COM SUCESSO!")
        print("="*80)
        print("\nPróximos passos:")
        print("  - Explore outros fixtures em tests/fixtures/lattes/")
        print("  - Customize os parsers em metricas_lattes/parsers/")
        print("  - Adicione novos parsers específicos no registry")
        print("  - Leia a documentação em docs/PARSER_SYSTEM.md")
        print()

    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
