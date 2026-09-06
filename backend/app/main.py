"""Punto de entrada de la API FastAPI: Soft Skills Analytics."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import APP_NAME, APP_VERSION, DEBUG
from .database import engine, init_db
from .routers import clustering, data, export, history, statistics

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "API de análisis no supervisado de habilidades blandas. Incluye base de "
        "conocimiento de modelos pre-entrenados (K-Means, DBSCAN, GMM), estadística "
        "con algoritmos propios y generación de reportes PDF/Excel."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
app.include_router(clustering.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(export.router, prefix="/api")


@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception as e:  # la BD puede no estar disponible aún
        logging.error("No se pudo inicializar la base de datos: %s", e)


@app.get("/api/health")
def health():
    from sqlalchemy import text

    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        db_error = str(e)
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "ok",
        "database": "online" if db_ok else "offline",
        "error": None if db_ok else db_error,
    }


@app.get("/api/version")
def version():
    return {"app": APP_NAME, "version": APP_VERSION}