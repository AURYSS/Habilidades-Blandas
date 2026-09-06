"""Pre-entrenamiento de la base de conocimiento para la exposición.

Entrena y registra los 33 modelos (3 algoritmos x todas las combinaciones de
2-4 habilidades) usando el dataset cargado en la BD (empleados). Este script se
ejecuta una vez que el dataset real está en la base; equivale al endpoint
POST /api/clustering/reentrenar-base.

Uso:
    cd backend
    python -m scripts.train_pretrained
"""

from __future__ import annotations

import logging

from app.database import SessionLocal
from app.services import pretrained
from app.services.repository import empleados_a_df

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("train_pretrained")


def main():
    with SessionLocal() as db:
        df = empleados_a_df(db)
        if df.empty:
            log.error("No hay empleados en la BD. Ejecuta primero: python -m scripts.migrate")
            return
        log.info("Entrenando base de conocimiento con %d empleados...", len(df))
        nuevos = pretrained.crear_modelos_base(df, db)
        log.info("Modelos registrados: %d nuevos (los existentes se conservan).", len(nuevos))
        log.info("Total en catálogo: %d modelos.", db.query(pretrained.Modelo).count())


if __name__ == "__main__":
    main()