import os
from flask import Blueprint, jsonify, make_response, render_template, url_for, request, redirect, g, abort
from pydantic import ValidationError
from sqlalchemy.orm import Session
from werkzeug.exceptions import Unauthorized, TooManyRequests

from database import get_db, SessionLocal
from libs.security.jwt import decode_access_token
from services.admin import login_user, current_session, revoke_session, attach_session_cookie, COOKIE_NAME
from services.errors import ValidationFailed, UploadRejected, NotFound, message_for
from services import real_estate as real_estate_service
from services import pages as pages_service
from schemas.admin import UserLoginSchema
from schemas.site import SiteTextSchema
from dotenv import load_dotenv

load_dotenv()

db = Session()

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")

LOGIN_PAGES = {"admin.login_page", "admin.login_form", "admin.logout"}

SAVED_MESSAGES = {
    "imovel": "Imóvel salvo.",
    "inicio": "Textos da Início salvos.",
    "rodape": "Texto do rodapé salvo.",
}

@admin_blueprint.before_request
def authenticate():
    if request.endpoint in LOGIN_PAGES:
        return None

    with SessionLocal() as session_db:
        payload = current_session(session_db, request)

    if not payload:
        return redirect(url_for("admin.login_form"))

    g.current_user = payload

@admin_blueprint.get("/")
def handle_admin():
    return redirect(url_for("admin.login_form"))

@admin_blueprint.get("/login")
def login_page():
    token = request.cookies.get(COOKIE_NAME)
    if token and decode_access_token(token):
        return redirect(url_for("admin.real_estate"))
    return render_template("admin/login.html")

@admin_blueprint.post("/login")
def login_form():
    db = next(get_db())

    try:
        form_data = UserLoginSchema.model_validate(request.form.to_dict())
    except ValidationError:
        return render_template("admin/login.html", error="Dados inválidos")
    try:
        user_jwt = login_user(db, form_data, request.remote_addr or "")
        response = make_response(redirect(url_for("admin.real_estate")))
        
        return attach_session_cookie(response, user_jwt)
    except TooManyRequests as e:
        return render_template("admin/login.html", error=e.description), 429
    except Unauthorized as e:
        return render_template("admin/login.html", error=e.description)
    finally:
        db.close()

@admin_blueprint.route("/logout")
def logout():
    with SessionLocal() as session_db:
        revoke_session(session_db, request)

    response = make_response(redirect(url_for("admin.login_page"),code=303))
    response.delete_cookie(COOKIE_NAME)

    return response

# Views 

@admin_blueprint.route("/real-estate")
def real_estate():
    with SessionLocal() as session_db:
        items = [
            real_estate_service.to_list_view(prop)
            for prop in real_estate_service.list_all(session_db)
        ]

    saved = SAVED_MESSAGES.get(request.args.get("salvo", ""))

    return render_template("admin/views/real_estate.html", user=g.current_user, items=items, saved=saved)

@admin_blueprint.route("/pages", methods=["GET", "POST"])
def pages():
    errors = {}
    submitted = None

    with SessionLocal() as session_db:
        if request.method == "POST":
            page = request.form.get("pagina", "")
            fields = {
                name: value
                for name, value in request.form.items()
                if name != "pagina"
            }
            try:
                SiteTextSchema.model_validate({"campos": fields})
                pages_service.save_texts(session_db, page, fields)
                return redirect(url_for("admin.pages", salvo=page))
            except ValidationError:
                errors[page] = "Preencha todos os campos com até 2000 caracteres."
                submitted = (page, fields)
            except NotFound:
                abort(404)

        texts = {page: pages_service.get_texts(session_db, page) for page in pages_service.DEFAULTS}

    if submitted:
        texts[submitted[0]].update(submitted[1])

    saved = SAVED_MESSAGES.get(request.args.get("salvo", ""))

    return render_template("admin/views/pages.html", user=g.current_user, texts=texts, errors=errors, saved=saved)

def form_values(prop) -> dict:
    values = real_estate_service.to_canonical(prop)
    values["situacao"] = prop.status.value
    return values

def collect_errors(exc: ValidationFailed) -> dict:
    return {field: message_for(code) for field, code in exc.fields}

def render_property_form(prop, values: dict, errors: dict, status: int = 200):
    return render_template(
        "admin/views/real_estate_form.html",
        user=g.current_user,
        real_estate=prop,
        form=values,
        errors=errors,
    ), status

def save_photos(session_db, prop) -> dict:
    upload_dir = os.path.abspath(os.getenv("UPLOAD_DIR", "uploads/"))
    errors = {}

    files = request.files.getlist("imagens")
    alts = request.form.getlist("imagens_alt[]")

    for index, file in enumerate(files):
        if not file or not file.filename:
            continue
        alt = alts[index] if index < len(alts) else ""
        try:
            real_estate_service.add_photo(session_db, prop, file, alt, upload_dir)
        except ValidationFailed as exc:
            errors.update(collect_errors(exc))
            break
        except UploadRejected as exc:
            errors["imagens"] = message_for(exc.code)
            break

    if errors:
        return errors

    for key, value in request.form.items():
        if key.startswith("existing_alt_") and key[len("existing_alt_"):].isdigit():
            try:
                real_estate_service.update_photo_alt(session_db, prop, int(key[len("existing_alt_"):]), value)
            except ValidationFailed as exc:
                errors.update(collect_errors(exc))
            except NotFound:
                continue

    for photo_id in request.form.getlist("delete_images"):
        if not photo_id.isdigit():
            continue
        try:
            real_estate_service.delete_photo(session_db, prop, int(photo_id), upload_dir)
        except ValidationFailed as exc:
            errors.update(collect_errors(exc))
        except NotFound:
            continue

    return errors

def handle_property_form(session_db, prop):
    form = request.form.to_dict()
    data = real_estate_service.from_form(form)
    target = form.get("situacao") or None

    try:
        if prop is None:
            prop = real_estate_service.create_property(session_db, data)
        else:
            prop = real_estate_service.update_property(session_db, prop, data)
    except ValidationFailed as exc:
        return render_property_form(prop, form, collect_errors(exc), 422)

    errors = save_photos(session_db, prop)

    if not errors and target and target != prop.status.value:
        try:
            real_estate_service.change_status(session_db, prop, target)
        except ValidationFailed as exc:
            errors = collect_errors(exc)

    if errors:
        return render_property_form(prop, form_values(prop), errors, 422)

    return redirect(url_for("admin.real_estate", salvo="imovel"))

@admin_blueprint.route("/real-estate/new", methods=["GET", "POST"])
def real_estate_new():
    if request.method == "POST":
        with SessionLocal() as session_db:
            return handle_property_form(session_db, None)

    return render_property_form(None, {"pais": "BR", "preco_moeda": "BRL", "situacao": "rascunho"}, {})

@admin_blueprint.route("/real-estate/<int:real_estate_id>/edit", methods=["GET", "POST"])
def real_estate_edit(real_estate_id):
    with SessionLocal() as session_db:
        try:
            prop = real_estate_service.get_by_id(session_db, real_estate_id)
        except NotFound:
            abort(404)

        if request.method == "POST":
            return handle_property_form(session_db, prop)

        return render_property_form(prop, form_values(prop), {})

# Fallback
@admin_blueprint.get("/<path:subpath>")
def handle_admin_404(subpath):
    return redirect(url_for("admin.login_form"))
