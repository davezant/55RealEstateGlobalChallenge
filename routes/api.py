import os
from flask import Blueprint, jsonify, request, g, make_response
from pydantic import ValidationError
from werkzeug.exceptions import Unauthorized, TooManyRequests

from database import SessionLocal
from domain.real_estate import PLACES
from schemas.admin import UserLoginSchema
from schemas.site import SiteTextSchema
from services.admin import authenticate_user, issue_token, attach_session_cookie, current_session, revoke_session, COOKIE_NAME
from services.errors import ValidationFailed, UploadRejected, NotFound
from services import real_estate as real_estate_service
from services import pages as pages_service

api_blueprint = Blueprint("api", __name__, url_prefix="/api/v1")

def json_error(code: str, status: int, fields: list[tuple[str, str]] | None = None):
    body = {"erro": code}
    if fields:
        body["campos"] = [
            {"campo": real_estate_service.error_field_for_api(field), "codigo": reason}
            for field, reason in fields
        ]
    return jsonify(body), status

def validation_response(exc: ValidationFailed):
    code = exc.fields[0][1] if len(exc.fields) == 1 else "validacao"
    return json_error(code, exc.status_code, exc.fields)

def json_body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else None

def upload_dir() -> str:
    return os.path.abspath(os.getenv("UPLOAD_DIR", "uploads/"))

def summary(prop) -> dict:
    return {"id": prop.real_estate_id, "ref": prop.ref, "slug": prop.slug, "situacao": prop.status.value}

@api_blueprint.before_request
def authenticate():
    protected = request.path.startswith("/api/v1/admin/") or request.endpoint == "api.logout"
    if not protected:
        return None

    with SessionLocal() as db:
        payload = current_session(db, request)

    if not payload:
        return json_error("nao_autenticado", 401)

    g.current_user = payload

@api_blueprint.post("/auth/login")
def login():
    body = json_body()
    email = body.get("email") if body else None
    senha = body.get("senha") if body else None

    if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha:
        return json_error("requisicao_invalida", 400)

    try:
        credentials = UserLoginSchema(email=email, password=senha)
    except ValidationError:
        return json_error("credenciais_invalidas", 401)

    with SessionLocal() as db:
        try:
            user = authenticate_user(db, credentials, request.remote_addr or "")
        except TooManyRequests:
            return json_error("muitas_tentativas", 429)
        except Unauthorized:
            return json_error("credenciais_invalidas", 401)

        response = make_response(jsonify({"usuario": {"id": user.user_id, "nome": user.username}}), 200)
        return attach_session_cookie(response, issue_token(user))

@api_blueprint.post("/auth/logout")
def logout():
    with SessionLocal() as db:
        revoke_session(db, request)

    response = make_response("", 204)
    response.delete_cookie(COOKIE_NAME)

    return response

@api_blueprint.get("/imoveis")
def list_real_estate():
    place = request.args.get("pais")
    order = request.args.get("ordenar", "recentes")
    invalid = []

    if place is not None and place not in PLACES:
        invalid.append(("pais", "invalido"))
    if order not in real_estate_service.ORDER_OPTIONS:
        invalid.append(("ordenar", "invalido"))

    if invalid:
        return json_error("parametro_invalido", 400, invalid)

    with SessionLocal() as db:
        items = [real_estate_service.to_list_item(prop) for prop in real_estate_service.list_public(db, place, order)]

    return jsonify({"itens": items, "total": len(items)}), 200

@api_blueprint.get("/imoveis/<slug>")
def get_real_estate(slug):
    with SessionLocal() as db:
        try:
            prop = real_estate_service.get_by_slug(db, slug)
        except NotFound:
            return json_error("nao_encontrado", 404)

        return jsonify(real_estate_service.to_detail(prop)), 200

@api_blueprint.post("/admin/imoveis")
def create_real_estate():
    body = json_body()
    if body is None:
        return json_error("requisicao_invalida", 400)

    with SessionLocal() as db:
        try:
            prop = real_estate_service.create_property(db, real_estate_service.from_api(body))
        except ValidationFailed as exc:
            return validation_response(exc)

        return jsonify(summary(prop)), 201

@api_blueprint.patch("/admin/imoveis/<int:real_estate_id>")
def update_real_estate(real_estate_id):
    body = json_body()
    if body is None:
        return json_error("requisicao_invalida", 400)

    with SessionLocal() as db:
        try:
            prop = real_estate_service.get_by_id(db, real_estate_id)
            prop = real_estate_service.update_property(db, prop, real_estate_service.from_api(body))
        except NotFound:
            return json_error("nao_encontrado", 404)
        except ValidationFailed as exc:
            return validation_response(exc)

        return jsonify({**summary(prop), **real_estate_service.to_detail(prop)}), 200

@api_blueprint.post("/admin/imoveis/<int:real_estate_id>/situacao")
def change_real_estate_status(real_estate_id):
    body = json_body()
    target = body.get("situacao") if body else None

    if not isinstance(target, str):
        return json_error("requisicao_invalida", 400)

    with SessionLocal() as db:
        try:
            prop = real_estate_service.get_by_id(db, real_estate_id)
            prop = real_estate_service.change_status(db, prop, target)
        except NotFound:
            return json_error("nao_encontrado", 404)
        except ValidationFailed as exc:
            return validation_response(exc)

        return jsonify(summary(prop)), 200

@api_blueprint.post("/admin/imoveis/<int:real_estate_id>/imagens")
def upload_image(real_estate_id):
    with SessionLocal() as db:
        try:
            prop = real_estate_service.get_by_id(db, real_estate_id)
            photo = real_estate_service.add_photo(
                db, prop, request.files.get("arquivo"), request.form.get("alt"), upload_dir()
            )
        except NotFound:
            return json_error("nao_encontrado", 404)
        except UploadRejected as exc:
            return json_error(exc.code, exc.status_code)
        except ValidationFailed as exc:
            return validation_response(exc)

        return jsonify({"id": photo.photo_id, "url": real_estate_service.photo_url(photo)}), 201

@api_blueprint.delete("/admin/imoveis/<int:real_estate_id>/imagens/<int:image_id>")
def delete_image(real_estate_id, image_id):
    with SessionLocal() as db:
        try:
            prop = real_estate_service.get_by_id(db, real_estate_id)
            real_estate_service.delete_photo(db, prop, image_id, upload_dir())
        except NotFound:
            return json_error("nao_encontrado", 404)
        except ValidationFailed as exc:
            return validation_response(exc)

    return "", 204

@api_blueprint.put("/admin/textos/<page>")
def save_texts(page):
    body = json_body()
    if body is None:
        return json_error("requisicao_invalida", 400)

    try:
        data = SiteTextSchema.model_validate(body)
    except ValidationError:
        return json_error("requisicao_invalida", 400)

    with SessionLocal() as db:
        try:
            texts = pages_service.save_texts(db, page, data.campos)
        except NotFound:
            return json_error("nao_encontrado", 404)

    return jsonify({"pagina": page, "campos": texts}), 200
