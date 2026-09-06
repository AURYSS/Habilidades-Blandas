"""Instalación de la base de datos del pipeline de habilidades blandas.

- Crea el esquema `habilidades` y las tablas canónicas:
  empleados, experimentos, asignaciones, modelos.
- Carga el dataset real `dataset_habilidades_blandas.csv` como base de
  conocimiento (empleados) si la tabla está vacía.
- Con `--drop` elimina el esquema completo (BASE_DROP) y lo reconstruye.

Uso:
    cd backend
    python -m scripts.migrate                # idempotente
    python -m scripts.migrate --drop         # destruye esquema y reconstruye
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import select, text

from app import models  # noqa: F401  (registra tablas en metadata)
from app.config import BASE_DIR, DB_SCHEMA
from app.database import Base, engine, SessionLocal
from app.models import Empleado
from app.services.data_loader import CONTEXTO_COLS, SKILL_ALIASES, load_and_validate_csv

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("migrate")

CSV_PATH = BASE_DIR.parent / "dataset_habilidades_blandas.csv"


def crear_esquema_y_tablas(drop: bool = False):
    with engine.connect() as conn:
        if drop:
            log.warning("Eliminando esquema '%s' (DESTRUCTIVO)...", DB_SCHEMA)
            conn.execute(text(f"DROP SCHEMA IF EXISTS {DB_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        conn.execute(text("COMMIT"))
    Base.metadata.create_all(bind=engine)
    log.info("Tablas listas: empleados, experimentos, asignaciones, modelos.")


def _empleados_existentes() -> int:
    with SessionLocal() as db:
        return db.execute(select(Empleado.id)).all().__len__()


def cargar_dataset(nombre: str) -> int:
    if not CSV_PATH.exists():
        log.info("No se encontró %s; omite la carga del dataset.", CSV_PATH)
        return 0
    log.info("Cargando dataset real: %s", CSV_PATH)
    df, msg = load_and_validate_csv(open(CSV_PATH, "rb"), nombre)
    if df is None:
        log.error("Validación del dataset falló: %s", msg)
        return 0

    with SessionLocal() as db:
        # Dedupe por id_empleado para que la carga sea idempotente.
        existentes = set(db.execute(select(Empleado.id_empleado)).scalars().all())
        columnas = ["id_empleado", "departamento", "puesto", "antiguedad_anos"] + list(SKILL_ALIASES.keys())
        columnas = [c for c in columnas if c in df.columns]
        registros = df[columnas].apply(
            lambda r: {k: (None if (v is not None and v != v) else v) for k, v in r.items()},
            axis=1,
        ).tolist()
        nuevos = [Empleado(**r) for r in registros if r.get("id_empleado") not in existentes]
        db.add_all(nuevos)
        db.commit()
        log.info("Empleados insertados: %d (dedupe contra %d existentes).", len(nuevos), len(existentes))
        return len(nuevos)


def main():
    parser = argparse.ArgumentParser(description="Instalación de la BD (habilidades blandas).")
    parser.add_argument("--drop", action="store_true", help="Reconstruir el esquema desde cero.")
    args = parser.parse_args()

    crear_esquema_y_tablas(drop=args.drop)
    if _empleados_existentes() == 0:
        cargar_dataset(CSV_PATH.name)
    else:
        log.info("La tabla empleados ya tiene registros; no se recarga el dataset (usa --drop para reiniciar).")
    log.info("✔ Migración completada.")


if __name__ == "__main__":
    main()