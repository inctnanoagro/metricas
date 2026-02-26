from metricas_lattes.batch_full_profile import normalize_text, normalize_nested_text


def test_normalize_text_mojibake_latin1() -> None:
    assert normalize_text("ParticipaÃ§Ã£o em bancas") == "Participação em bancas"
    assert normalize_text("OrientaÃ§Ã£o") == "Orientação"


def test_normalize_text_html_entities() -> None:
    assert normalize_text("Participa&ccedil;&atilde;o") == "Participação"


def test_normalize_text_cp1252_emoji() -> None:
    assert normalize_text("CoraÃ§Ã£o ðŸ’•") == "Coração 💕"


def test_normalize_nested_text_excludes_raw() -> None:
    payload = {
        "researcher": {"full_name": "ParticipaÃ§Ã£o"},
        "productions": [
            {"titulo": "OrientaÃ§Ã£o", "raw": "ParticipaÃ§Ã£o raw"},
        ],
    }
    normalized = normalize_nested_text(payload, exclude_keys={"raw"})
    assert normalized["researcher"]["full_name"] == "Participação"
    assert normalized["productions"][0]["titulo"] == "Orientação"
    assert normalized["productions"][0]["raw"] == "ParticipaÃ§Ã£o raw"
