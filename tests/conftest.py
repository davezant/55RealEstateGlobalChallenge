import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

TMP = tempfile.mkdtemp()

os.environ.setdefault("SEGREDO_APP", "x" * 40)
os.environ["DB_PATH"] = os.path.join(TMP, "test.db")
os.environ["UPLOAD_DIR"] = os.path.join(TMP, "uploads")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models import users, real_estate, site

@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session

@pytest.fixture
def apartment_data():
    return {
        "ref": "BR-0101",
        "titulo": "Apartamento Alameda Lorena",
        "tipologia": "apartamento",
        "pais": "BR",
        "cidade": "São Paulo",
        "bairro": "Jardins",
        "descricao": "Planta de 212 m² em rua arborizada.",
        "preco_valor": "4850000.10",
        "preco_moeda": "BRL",
        "area_privativa": "212.00",
        "quartos": 3,
        "banheiros": 3,
        "vagas": 2,
        "andar": 14,
        "parceiro": "Parceiro Local Sul 01",
    }
