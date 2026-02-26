"""
ANTI-LEAK STRICT
Strict, non-tolerant rules to prevent author leakage into titles and venues.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

from metricas_lattes.parser_router import normalize_filename, parse_fixture


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "lattes"

FIXTURE_KEYS = {
    "artigos": "artigos completos publicados em periodicos",
    "capitulos": "capitulos de livros publicados",
    "textos": "textos em jornais de noticias revistas",
}


def _find_fixture_by_normalized_key(normalized_key: str) -> Path:
    for html_file in FIXTURES_DIR.glob("*.html"):
        if html_file.name.startswith((".", "_")):
            continue
        normalized = normalize_filename(html_file.name)
        if normalized_key.lower() == normalized.lower():
            return html_file
    raise FileNotFoundError(f"Nenhum fixture encontrado para: {normalized_key}")


def _norm(value: str | None) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFD", str(value))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def _author_prefix(raw: str | None) -> str | None:
    if not raw:
        return None
    if " . " in raw:
        prefix = raw.split(" . ", 1)[0]
    elif ". " in raw:
        prefix = raw.split(". ", 1)[0]
    else:
        return None
    if ";" in prefix or re.search(r"\b[A-ZÀ-Ü]{2,},\s*[A-ZÀ-Ü]", prefix):
        return prefix
    return None


def _authors_are_valid(autores: str | None) -> bool:
    if not autores:
        return False
    if ";" in autores or "," in autores:
        return True
    tokens = [t for t in autores.split() if t]
    return len(tokens) >= 2


@pytest.fixture(scope="module")
def parsed_results() -> dict[str, dict]:
    results = {}
    for key, normalized in FIXTURE_KEYS.items():
        fixture_path = _find_fixture_by_normalized_key(normalized)
        results[key] = parse_fixture(fixture_path)
    return results


def test_rule_a_titles_do_not_start_with_author_pattern(parsed_results: dict[str, dict]) -> None:
    pattern = re.compile(r"^[A-ZÀ-Ü]{2,},\s*[A-ZÀ-Ü]")
    for data in parsed_results.values():
        for item in data["items"]:
            titulo = item.get("titulo") or ""
            assert not pattern.search(titulo), f"Titulo inicia com autor: {titulo}"


def test_rule_b_titles_do_not_contain_semicolon_separator(parsed_results: dict[str, dict]) -> None:
    for data in parsed_results.values():
        for item in data["items"]:
            titulo = item.get("titulo") or ""
            assert " ; " not in titulo, f"Titulo contem separador de autores: {titulo}"


def test_rule_c_title_does_not_contain_author_prefix_from_raw(parsed_results: dict[str, dict]) -> None:
    for data in parsed_results.values():
        for item in data["items"]:
            titulo = item.get("titulo") or ""
            raw = item.get("raw") or ""
            prefix = _author_prefix(raw)
            if not prefix or not titulo:
                continue
            assert _norm(prefix) not in _norm(titulo), (
                f"Titulo contem prefixo de autores: {titulo}"
            )


def test_rule_d_autores_obrigatorio_e_consistente(parsed_results: dict[str, dict]) -> None:
    for data in parsed_results.values():
        for item in data["items"]:
            autores = item.get("autores")
            assert _authors_are_valid(autores), f"Autores invalidos: {autores}"


def test_rule_e_veiculo_nao_contem_autores_ou_separadores(parsed_results: dict[str, dict]) -> None:
    pattern = re.compile(r"[A-ZÀ-Ü]{2,},\s*[A-ZÀ-Ü]")
    for data in parsed_results.values():
        for item in data["items"]:
            veiculo = item.get("veiculo")
            if not veiculo:
                continue
            assert ";" not in veiculo, f"Veiculo contem ';': {veiculo}"
            assert not pattern.search(veiculo), f"Veiculo parece lista de autores: {veiculo}"


def test_rule_f_raw_existe_e_contem_titulo(parsed_results: dict[str, dict]) -> None:
    for data in parsed_results.values():
        for item in data["items"]:
            raw = item.get("raw") or ""
            titulo = item.get("titulo") or ""
            assert len(raw) > 20, f"Raw muito curto: {raw}"
            assert titulo, f"Titulo ausente para raw: {raw}"
            assert _norm(titulo) in _norm(raw), f"Titulo nao encontrado no raw: {titulo}"


def test_rule_g_titulo_nao_termina_com_ano(parsed_results: dict[str, dict]) -> None:
    pattern = re.compile(r"\b(19|20)\d{2}\.?$")
    for data in parsed_results.values():
        for item in data["items"]:
            titulo = item.get("titulo") or ""
            assert not pattern.search(titulo), f"Titulo termina com ano: {titulo}"


def test_rule_h_fingerprint_unico_por_fixture(parsed_results: dict[str, dict]) -> None:
    for data in parsed_results.values():
        fingerprints = [item.get("fingerprint_sha1") for item in data["items"]]
        fingerprints = [fp for fp in fingerprints if fp]
        assert len(fingerprints) == len(set(fingerprints)), "Fingerprint duplicado no fixture"


def _item_by_numero(items: list[dict], numero_item: int) -> dict:
    for item in items:
        if item.get("numero_item") == numero_item:
            return item
    raise AssertionError(f"Item numero {numero_item} nao encontrado")


def _assert_norm_equal(actual: str | None, expected: str) -> None:
    assert _norm(actual) == _norm(expected), f"Esperado: {expected} | Atual: {actual}"


def test_representative_items_artigos(parsed_results: dict[str, dict]) -> None:
    items = parsed_results["artigos"]["items"]

    item_1 = _item_by_numero(items, 1)
    _assert_norm_equal(
        item_1.get("titulo"),
        "Smart delivery of auxin: Lignin nanoparticles promote efficient and safer vascular development in crop species",
    )
    _assert_norm_equal(
        item_1.get("autores"),
        "FALEIRO, R. FALEIRO, R.; PACE, M. R.; TESSMER, M. A.; PEREIRA, A. E.; FRACETO, LEONARDO; MAYER, J. L. S.",
    )
    _assert_norm_equal(item_1.get("veiculo"), "Plant Nano Biology")
    assert item_1.get("ano") == 2026

    item_3 = _item_by_numero(items, 3)
    _assert_norm_equal(
        item_3.get("titulo"),
        "Delivering metribuzin from biodegradable nanocarriers: Assessing herbicidal effects for soybean plant protection and weed control",
    )
    _assert_norm_equal(
        item_3.get("autores"),
        "TAKESHITA, V. TAKESHITA, V.; OLIVEIRA, F. F.; GARCIA, A.; ZUVERZA-MENA, N.; TAMEZ, C.; CARDOSO, B. C.; PINACIO, C. W.; STEVEN, B.; LAREAU, J.; SABLIOV, C.; FRACETO, L. F.; TORNISIELO, V. L.; DIMKPA, C.; WHITE, JASON C.",
    )
    _assert_norm_equal(item_3.get("veiculo"), "Environmental Science-Nano")
    assert item_3.get("ano") == 2025

    item_5 = _item_by_numero(items, 5)
    _assert_norm_equal(
        item_5.get("titulo"),
        "Toxicity Assessment of Biogenic Gold Nanoparticles on Crop Seeds and Zebrafish Embryos: Implications for Agricultural and Aquatic Ecosystems",
    )
    _assert_norm_equal(
        item_5.get("autores"),
        "BOTTEON, C. BOTTEON, C.; PEREIRA, A. E.; CASTRO, L.; JUSTINO, I.; FRACETO, L. F.; BASTOS, J.; MARCATO, P. D.",
    )
    _assert_norm_equal(item_5.get("veiculo"), "ACS Omega")
    assert item_5.get("ano") == 2025


def test_representative_items_capitulos(parsed_results: dict[str, dict]) -> None:
    items = parsed_results["capitulos"]["items"]

    item_1 = _item_by_numero(items, 1)
    _assert_norm_equal(
        item_1.get("titulo"),
        "Colloidal Materials and Their Crucial Role in Soil Sustainability: An Integrated Approach",
    )
    _assert_norm_equal(
        item_1.get("autores"),
        "Villarreal, Gabriela Patricia Unigarro; Campos, Estefania Vangelie Ramos; Fraceto, Leonardo Fernandes",
    )
    _assert_norm_equal(
        item_1.get("livro"),
        "Contribution of Colloidal Materials to Air, Water and Soil Environmental Sustainability",
    )
    assert item_1.get("ano") == 2025

    item_2 = _item_by_numero(items, 2)
    _assert_norm_equal(
        item_2.get("titulo"),
        "Uses of biomolecules in development of formulations aiming sustainable agriculture",
    )
    _assert_norm_equal(
        item_2.get("autores"),
        "Campos, Estefania Vangelie Ramos; de Oliveira, Jhones Luiz; Pereira, Anderson do Espirito Santo; Vilarreal, Gabriela Patricia Unigarro; Fraceto, Leonardo Fernandes",
    )
    _assert_norm_equal(item_2.get("livro"), "Bio-Inoculants in Horticultural Crops")
    assert item_2.get("ano") == 2024

    item_4 = _item_by_numero(items, 4)
    _assert_norm_equal(
        item_4.get("titulo"),
        "Silica and Silica Nanoparticles: An Approach to Biogenic Synthesis and Their Main Applications",
    )
    _assert_norm_equal(
        item_4.get("autores"),
        "HARADA, L. K.; GUILGER-CASAGRANDE, M.; GERMANO-COSTA, T.; BILESKY-JOSE, N.; F. FRACETO, L.; LIMA, R.",
    )
    _assert_norm_equal(
        item_4.get("livro"),
        "Sustainable Plant Nutrition in a Changing World",
    )
    assert item_4.get("ano") == 2024


def test_representative_items_textos(parsed_results: dict[str, dict]) -> None:
    items = parsed_results["textos"]["items"]

    item_1 = _item_by_numero(items, 1)
    _assert_norm_equal(item_1.get("titulo"), "Nano-herbicidas no combate a daninhas")
    _assert_norm_equal(
        item_1.get("autores"),
        "TAKESHITA, VANESSA; RODRIGUES, J. S.; PREISLER, A. C.; FRACETO, L. F.",
    )
    _assert_norm_equal(item_1.get("veiculo"), "Cultivar Grandes Culturas")
    assert item_1.get("ano") == 2025

    item_2 = _item_by_numero(items, 2)
    _assert_norm_equal(
        item_2.get("titulo"),
        "Controle biologico aliado a novas tecnologias: Uma alternativa sustentavel",
    )
    _assert_norm_equal(
        item_2.get("autores"),
        "OLIVEIRA, J. L.; POLANCZYK, R. A.; FRACETO, L F",
    )
    _assert_norm_equal(item_2.get("veiculo"), "Jornal Cruzeiro do Sul")
    assert item_2.get("ano") == 2019

    item_10 = _item_by_numero(items, 10)
    _assert_norm_equal(
        item_10.get("titulo"),
        "Quatro docentes da Unesp de Sorocaba estao na lista do Webometrics ranking",
    )
    _assert_norm_equal(item_10.get("autores"), "FRACETO, LEONARDO F")
    _assert_norm_equal(item_10.get("veiculo"), "Jornal Cruzeiro do Sul")
    assert item_10.get("ano") == 2015
