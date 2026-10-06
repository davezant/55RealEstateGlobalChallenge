import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "app.db")

if DB_PATH.endswith(("/", "\\")) or os.path.isdir(DB_PATH):
    DB_PATH = os.path.join(DB_PATH, "app.db")

db_dir = os.path.dirname(os.path.abspath(DB_PATH))
os.makedirs(db_dir, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(DB_PATH)}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
