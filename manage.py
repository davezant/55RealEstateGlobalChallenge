import os
import sys
from datetime import datetime, timezone
import click
from dotenv import load_dotenv
from sqlalchemy import select
from wsgi import app
from models.base import Base
from models import users, real_estate, site

from services.admin import create_user, normalize_email
from services.real_estate import create_property
from database import engine, get_db
from database_migrations import apply_migrations
from models.real_estate import RealEstateModel, StatusEnum
from models.users import UserModel
from schemas.admin import UserRegistrationSchema
from data.importer import read_properties, read_photo_index, photo_path
from services.real_estate import add_photo
from services.errors import ValidationFailed, UploadRejected, message_for
from werkzeug.datastructures import FileStorage
from domain.real_estate import typology_for

load_dotenv()
@app.cli.command("migrar")
def migrar():
    applied = apply_migrations()
    for name in applied:
        click.echo(f"Aplicada: {name}")
    click.echo("Banco atualizado." if applied else "Nada a aplicar.")

@app.cli.command("semear")
def semear():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_SENHA")

    if not admin_email or not admin_password:
        click.echo("Defina ADMIN_EMAIL e ADMIN_SENHA.", err=True)
        sys.exit(1)

    db = next(get_db())
    with app.app_context():
        email = normalize_email(admin_email)

        if db.scalar(select(UserModel).where(UserModel.email == email)) is None:
            create_user(db, UserRegistrationSchema(
                email=email,
                password=admin_password,
                username="Administrador",
                role="admin",
            ))

        photo_index = read_photo_index()
        upload_dir = os.path.abspath(os.getenv("UPLOAD_DIR", "uploads/"))
        missing_photos = 0
        rejected_photos = []

        for item in read_properties():
            if db.scalar(select(RealEstateModel).where(RealEstateModel.ref == item["ref"])):
                continue

            data = {key: value for key, value in item.items() if key != "situacao"}

            prop = create_property(db, data)

            label = typology_for(item["tipologia"]).label

            for number, filename in enumerate(photo_index.get(item["ref"], []), start=1):
                path = photo_path(filename)

                if not os.path.isfile(path):
                    missing_photos += 1
                    continue

                try:
                    with open(path, "rb") as file:
                        storage = FileStorage(stream=file, filename=filename)
                        add_photo(db, prop, storage, f"{label} em {item['bairro']}, foto {number}", upload_dir)
                except UploadRejected as exc:
                    rejected_photos.append((filename, item["ref"], message_for(exc.code)))
                except ValidationFailed as exc:
                    rejected_photos.append((filename, item["ref"], message_for(exc.fields[0][1])))

            prop.status = StatusEnum(item["situacao"])
            if item["situacao"] == "vendido":
                prop.sold_at = datetime.now(timezone.utc)
            db.commit()

        for filename, ref, reason in rejected_photos:
            click.echo(f"Foto recusada: {filename} ({ref}). {reason}")

        if missing_photos:
            click.echo(f"{missing_photos} fotos do índice não foram encontradas em data/Imagens/.")

        click.echo("Base de dados semeada com sucesso.")
    db.close()

if __name__ == "__main__":
    app.cli()
