"""Conexión a PostgreSQL usando SQLAlchemy 2.0.

Toda la persistencia vive en el esquema `habilidades`.
"""

from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_URL, DB_SCHEMA

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)


@event.listens_for(engine, "connect")
def _set_schema(dbapi_connection, _):
    """Fija el search_path por conexión para que las tablas sin esquema
    apunten siempre a `habilidades`. Se ejecuta dentro de una transacción
    inmediata (commit) para que sobreviva a los ROLLBACK posteriores."""
    try:
        cur = dbapi_connection.cursor()
        cur.execute(f"SET search_path TO {DB_SCHEMA}, public")
        cur.close()
        dbapi_connection.commit()
    except Exception:
        pass


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Crea el esquema y las tablas si no existen."""
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        conn.execute(text("COMMIT"))
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependencia de FastAPI para sesiones por request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()