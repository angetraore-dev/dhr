"""
Configuration de la base de données.

- Engine SQLAlchemy 2.x (sync, psycopg 3)
- Session factory
- Dépendance FastAPI get_db
"""
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# --- Engine ---
# pool_pre_ping : vérifie la connexion avant usage (évite les "server closed connection")
# pool_size / max_overflow : dimensionnement du pool
engine = create_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.env == "development" and settings.log_level == "debug",
    future=True,
)

# --- Session factory ---
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


# --- Base déclarative ---
class Base(DeclarativeBase):
    """Base déclarative SQLAlchemy 2.x pour tous les modèles."""
    pass


# --- Dépendance FastAPI ---
def get_db() -> Generator[Session, None, None]:
    """
    Fournit une session SQLAlchemy par requête.

    Usage :
        @router.get("/...")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Healthcheck DB ---
def check_db() -> bool:
    """Vérifie que la base répond (utilisé par /health)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False