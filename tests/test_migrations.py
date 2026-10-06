from sqlalchemy import create_engine, inspect

from database_migrations import apply_migrations

def test_migrations_create_all_tables_and_are_idempotent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")

    first = apply_migrations(engine)
    second = apply_migrations(engine)

    tables = set(inspect(engine).get_table_names())

    assert first == [
        "0001_usuarios_e_imoveis.sql",
        "0002_textos_do_site.sql",
        "0003_sessoes_revogadas.sql",
    ]
    assert second == []
    assert {"users", "real_estate", "real_estate_photos", "site_texts", "revoked_tokens"} <= tables

def test_migrated_schema_matches_models(tmp_path):
    from models.base import Base
    from models import users, real_estate, site

    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    apply_migrations(engine)
    inspector = inspect(engine)

    for name, table in Base.metadata.tables.items():
        columns = {column["name"] for column in inspector.get_columns(name)}
        assert columns == {column.name for column in table.columns}
