import glob
import os

from database import engine

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")

def apply_migrations(target_engine=engine, directory: str = MIGRATIONS_DIR) -> list[str]:
    applied_now = []
    connection = target_engine.raw_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "name VARCHAR(120) PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.commit()

        cursor.execute("SELECT name FROM schema_migrations")
        done = {row[0] for row in cursor.fetchall()}

        for path in sorted(glob.glob(os.path.join(directory, "*.sql"))):
            name = os.path.basename(path)
            if name in done:
                continue

            with open(path, encoding="utf-8") as file:
                script = file.read()

            try:
                cursor.executescript("BEGIN;\n" + script + "\nCOMMIT;")
            except Exception:
                connection.rollback()
                raise

            cursor.execute("INSERT INTO schema_migrations (name) VALUES (?)", (name,))
            connection.commit()
            applied_now.append(name)
    finally:
        connection.close()

    return applied_now
