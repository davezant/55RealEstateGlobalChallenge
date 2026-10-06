import io

import pytest
from werkzeug.datastructures import FileStorage

from services import real_estate as service
from services.errors import UploadRejected, ValidationFailed

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32

def upload(content=PNG, name="foto.png"):
    return FileStorage(stream=io.BytesIO(content), filename=name)

def codes(exc_info):
    return set(exc_info.value.fields)

def test_create_generates_slug_and_starts_as_draft(db, apartment_data):
    prop = service.create_property(db, apartment_data)
    assert prop.slug == "apartamento-alameda-lorena-br-0101"
    assert prop.status.value == "rascunho"

def test_create_rejects_duplicate_ref(db, apartment_data):
    service.create_property(db, apartment_data)
    with pytest.raises(ValidationFailed) as exc:
        service.create_property(db, apartment_data)
    assert ("ref", "ref_duplicada") in codes(exc)

def test_create_rejects_land_area_for_apartment(db, apartment_data):
    apartment_data["area_terreno"] = "100"
    with pytest.raises(ValidationFailed) as exc:
        service.create_property(db, apartment_data)
    assert ("area_terreno", "nao_se_aplica") in codes(exc)

def test_create_rejects_wrong_currency(db, apartment_data):
    apartment_data["preco_moeda"] = "USD"
    with pytest.raises(ValidationFailed) as exc:
        service.create_property(db, apartment_data)
    assert ("preco_moeda", "moeda_incompativel") in codes(exc)

def test_create_reports_each_field(db, apartment_data):
    apartment_data["ref"] = "abc"
    apartment_data["titulo"] = ""
    with pytest.raises(ValidationFailed) as exc:
        service.create_property(db, apartment_data)
    fields = {field for field, _ in exc.value.fields}
    assert {"ref", "titulo"} <= fields

def test_create_rejects_float_money(db, apartment_data):
    body = {"preco": {"valor": 10.5, "moeda": "BRL"}}
    data = {**apartment_data, **service.from_api(body)}
    with pytest.raises(ValidationFailed) as exc:
        service.create_property(db, data)
    assert ("preco_valor", "invalido") in codes(exc)

def test_update_keeps_other_fields(db, apartment_data):
    prop = service.create_property(db, apartment_data)
    service.update_property(db, prop, {"bairro": "Pinheiros"})
    assert prop.neighborhood == "Pinheiros"
    assert prop.title == "Apartamento Alameda Lorena"

def test_publish_requires_photo(db, apartment_data):
    prop = service.create_property(db, apartment_data)
    with pytest.raises(ValidationFailed) as exc:
        service.change_status(db, prop, "publicado")
    assert ("imagens", "foto_obrigatoria") in codes(exc)

def test_publish_requires_complete_data(db, apartment_data, tmp_path):
    del apartment_data["andar"]
    prop = service.create_property(db, apartment_data)
    service.add_photo(db, prop, upload(), "Sala", str(tmp_path))
    with pytest.raises(ValidationFailed) as exc:
        service.change_status(db, prop, "publicado")
    assert ("andar", "obrigatorio") in codes(exc)

def test_first_photo_is_cover_and_publish_works(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    first = service.add_photo(db, prop, upload(), "Sala", str(tmp_path))
    second = service.add_photo(db, prop, upload(), "Varanda", str(tmp_path))
    assert first.is_cover and not second.is_cover
    service.change_status(db, prop, "publicado")
    assert prop.status.value == "publicado"

def test_photo_requires_description(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    with pytest.raises(ValidationFailed):
        service.add_photo(db, prop, upload(), "  ", str(tmp_path))

def test_photo_rejects_non_image_with_image_name(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    with pytest.raises(UploadRejected) as exc:
        service.add_photo(db, prop, upload(b"<script>alert(1)</script>", "x.png"), "Sala", str(tmp_path))
    assert exc.value.status_code == 415

def test_photo_rejects_over_five_megabytes(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    big = PNG + b"0" * (5 * 1024 * 1024)
    with pytest.raises(UploadRejected) as exc:
        service.add_photo(db, prop, upload(big), "Sala", str(tmp_path))
    assert exc.value.status_code == 413

def test_stored_name_ignores_client_filename(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    photo = service.add_photo(db, prop, upload(PNG, "../../etc/passwd.png"), "Sala", str(tmp_path))
    assert "/" not in photo.file_path and ".." not in photo.file_path
    assert (tmp_path / photo.file_path).exists()

def test_photo_limit(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    for index in range(12):
        service.add_photo(db, prop, upload(), f"Foto {index}", str(tmp_path))
    with pytest.raises(ValidationFailed) as exc:
        service.add_photo(db, prop, upload(), "Foto extra", str(tmp_path))
    assert ("imagens", "limite_fotos") in codes(exc)

def test_deleting_cover_promotes_next_photo(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    first = service.add_photo(db, prop, upload(), "Sala", str(tmp_path))
    service.add_photo(db, prop, upload(), "Varanda", str(tmp_path))
    service.delete_photo(db, prop, first.photo_id, str(tmp_path))
    assert len(prop.images) == 1 and prop.images[0].is_cover

def test_cannot_remove_last_photo_of_visible_property(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    photo = service.add_photo(db, prop, upload(), "Sala", str(tmp_path))
    service.change_status(db, prop, "publicado")
    with pytest.raises(ValidationFailed):
        service.delete_photo(db, prop, photo.photo_id, str(tmp_path))

def test_sold_property_is_never_offered_again(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    service.add_photo(db, prop, upload(), "Sala", str(tmp_path))
    service.change_status(db, prop, "publicado")
    service.change_status(db, prop, "vendido")
    service.change_status(db, prop, "arquivado")
    with pytest.raises(ValidationFailed) as exc:
        service.change_status(db, prop, "rascunho")
    assert ("situacao", "vendido_irreversivel") in codes(exc)

def test_whatsapp_url_rules(db, apartment_data, tmp_path, monkeypatch):
    monkeypatch.setenv("WHATSAPP_E164", "+99910000001")
    prop = service.create_property(db, apartment_data)
    assert service.whatsapp_url(prop) is None
    service.add_photo(db, prop, upload(), "Sala", str(tmp_path))
    service.change_status(db, prop, "publicado")
    url = service.whatsapp_url(prop)
    assert url.startswith("https://wa.me/99910000001?text=")
    assert "BR-0101" in url
    service.change_status(db, prop, "vendido")
    assert service.whatsapp_url(prop) is None

def test_price_per_m2_in_detail(db, apartment_data, tmp_path):
    prop = service.create_property(db, apartment_data)
    detail = service.to_detail(prop)
    assert detail["precoPorM2"] == {"valor": "22877.36", "moeda": "BRL"}

def test_price_ordering_never_mixes_currencies(db, tmp_path):
    base = {
        "tipologia": "apartamento", "cidade": "Cidade", "bairro": "Bairro", "descricao": "Descrição longa o bastante.",
        "area_privativa": "100", "quartos": 1, "andar": 1, "parceiro": "Parceiro",
    }
    rows = [
        ("BR-0001", "BR", "BRL", "1000000"),
        ("PA-0001", "PA", "USD", "300000"),
        ("AE-0001", "AE", "AED", "2000000"),
    ]
    for ref, country, currency, price in rows:
        prop = service.create_property(db, {**base, "ref": ref, "titulo": f"Imóvel {ref}", "pais": country, "preco_moeda": currency, "preco_valor": price})
        service.add_photo(db, prop, upload(), "Foto", str(tmp_path))
        service.change_status(db, prop, "publicado")
    refs = [prop.ref for prop in service.list_public(db, None, "preco_asc")]
    assert refs == ["BR-0001", "PA-0001", "AE-0001"]
    refs = [prop.ref for prop in service.list_public(db, None, "preco_desc")]
    assert refs == ["AE-0001", "PA-0001", "BR-0001"]
