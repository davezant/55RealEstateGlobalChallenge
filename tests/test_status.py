from domain import status

def test_visible_states():
    assert status.is_visible("publicado")
    assert status.is_visible("reservado")
    assert status.is_visible("vendido")
    assert not status.is_visible("rascunho")
    assert not status.is_visible("arquivado")

def test_whatsapp_only_for_published_and_reserved():
    assert status.has_whatsapp("publicado")
    assert status.has_whatsapp("reservado")
    assert not status.has_whatsapp("vendido")

def test_allowed_transition():
    assert status.transition_error("rascunho", "publicado", False) is None
    assert status.transition_error("publicado", "vendido", False) is None

def test_blocked_transition():
    assert status.transition_error("rascunho", "vendido", False) == "transicao_invalida"
    assert status.transition_error("vendido", "publicado", True) == "vendido_irreversivel"

def test_sold_cannot_return_through_archive():
    assert status.transition_error("vendido", "arquivado", True) is None
    assert status.transition_error("arquivado", "rascunho", True) == "vendido_irreversivel"

def test_unknown_target():
    assert status.transition_error("rascunho", "invalido", False) == "situacao_invalida"

def test_same_state_is_noop():
    assert status.transition_error("publicado", "publicado", False) is None

def test_publication_requires_photo_with_description():
    assert status.publication_error([]) == "foto_obrigatoria"
    assert status.publication_error(["ok", " "]) == "descricao_foto_obrigatoria"
    assert status.publication_error(["ok"]) is None
