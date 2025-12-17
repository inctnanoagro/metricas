import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator, exceptions


def carregar_json(caminho):
    """Carrega um arquivo JSON a partir do caminho informado."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar JSON: {e}")


def carregar_schema(caminho):
    """Carrega o JSON Schema."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar schema: {e}")


def validar(json_dados, schema):
    """Valida os dados contra o schema e retorna lista de erros."""
    validator = Draft7Validator(schema)
    erros = sorted(validator.iter_errors(json_dados), key=lambda e: e.path)
    return erros


def main():
    if len(sys.argv) != 2:
        print("Uso: python validacao.py <arquivo.json>")
        sys.exit(1)

    caminho_json = Path(sys.argv[1])
    caminho_schema = Path(__file__).resolve().parents[1] / "schema" / "producoes.schema.json"

    if not caminho_json.exists():
        print(f"Arquivo não encontrado: {caminho_json}")
        sys.exit(1)

    if not caminho_schema.exists():
        print(f"Schema não encontrado: {caminho_schema}")
        sys.exit(1)

    try:
        dados = carregar_json(caminho_json)
        schema = carregar_schema(caminho_schema)
        erros = validar(dados, schema)

        if not erros:
            print("✅ JSON válido segundo o schema do INCT NanoAgro.")
            sys.exit(0)

        print("❌ JSON inválido. Erros encontrados:")
        for erro in erros:
            caminho = ".".join([str(p) for p in erro.path])
            print(f"- Campo: {caminho if caminho else '(raiz)'}")
            print(f"  Motivo: {erro.message}")

        sys.exit(2)

    except exceptions.SchemaError as e:
        print(f"Erro no schema: {e}")
        sys.exit(3)

    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()

