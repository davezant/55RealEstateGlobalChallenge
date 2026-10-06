import os
from flask import Blueprint, render_template, url_for, send_from_directory, request, jsonify, current_app, abort
from werkzeug.exceptions import RequestEntityTooLarge

from database import SessionLocal
from domain.real_estate import PLACES
from services import real_estate as real_estate_service
from services import pages as pages_service
from services.errors import NotFound
from services.media import FILENAME_PATTERN

main_blueprint = Blueprint("main", __name__)

@main_blueprint.app_context_processor
def inject_footer():
    with SessionLocal() as db:
        return {"footer": pages_service.get_texts(db, "rodape")}

@main_blueprint.route("/saude")
def health():
    response = {"ok": True}
    return jsonify(response), 200

@main_blueprint.route("/media/<arquivo>")
def media(arquivo):
    if not FILENAME_PATTERN.match(arquivo):
        abort(404)
    return send_from_directory(os.path.abspath(current_app.config["UPLOAD_FOLDER"]), arquivo)

@main_blueprint.route("/")
def home():
    with SessionLocal() as db:
        texts = pages_service.get_texts(db, "inicio")
        highlights = [
            real_estate_service.to_list_view(prop)
            for prop in real_estate_service.list_public(db)
            if prop.status.value == "publicado"
        ][:3]

    return render_template("index.html", inicio=texts, highlights=highlights)

@main_blueprint.route("/imoveis")
def assets():
    place = request.args.get("pais")
    order = request.args.get("ordenar", "recentes")

    if place not in PLACES:
        place = None
    if order not in real_estate_service.ORDER_OPTIONS:
        order = "recentes"

    with SessionLocal() as db:
        items = [real_estate_service.to_list_view(prop) for prop in real_estate_service.list_public(db, place, order)]

    return render_template(
        "real_estate.html",
        items=items,
        selected_place=place or "",
        selected_order=order,
        places=PLACES.values(),
    )

@main_blueprint.route("/diagnostico")
def diagnosis():
    return render_template("diagnosis.html")

@main_blueprint.route("/tese")
def thesis():
    return render_template("tese.html")

@main_blueprint.route("/pracas")
def places_page():
    return render_template("pracas.html")

@main_blueprint.route("/tokenizacao")
def tokenization():
    return render_template("tokenizacao.html")

@main_blueprint.route("/lista-de-espera")
def waitlist():
    return render_template("waitlist.html")

@main_blueprint.route("/governanca")
def governance():
    return render_template("governanca.html")

@main_blueprint.route("/schedule/")
def schedule():
    return render_template("schedule.html")

@main_blueprint.route("/imoveis/<slug>")
def real_estate_product(slug):
    with SessionLocal() as db:
        try:
            prop = real_estate_service.get_by_slug(db, slug)
        except NotFound:
            return render_template("error.html", message="Imóvel não encontrado.", back_url=url_for("main.assets"), back_label="Voltar aos imóveis"), 404

        asset = real_estate_service.to_detail_view(prop)

    return render_template("real_estate_product.html", asset=asset)

@main_blueprint.app_errorhandler(404)
def not_found(error):
    if request.path.startswith(("/api/", "/media/")):
        return jsonify({"erro": "nao_encontrado"}), 404
    return render_template("error.html", message="Página não encontrada.", back_url=url_for("main.home"), back_label="Voltar ao início"), 404

@main_blueprint.app_errorhandler(413)
def too_large(error):
    if request.path.startswith("/api/"):
        return jsonify({"erro": "arquivo_grande"}), 413
    return "Envio grande demais.", 413
