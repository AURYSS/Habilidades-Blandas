"""Configuración central de la aplicación.

Todas las variables sensibles se leen de variables de entorno (ver `backend/.env`,
que está excluido del control de versiones). El esquema lógico vive en `habilidades`.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------- rutas base
BASE_DIR = Path(__file__).resolve().parent.parent        # backend/
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Carga backend/.env si existe (no se versiona).
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------- postgres
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "softskills")
DB_SCHEMA = os.getenv("DB_SCHEMA", "habilidades")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

# ---------------------------------------------------------------- app
APP_NAME = os.getenv("APP_NAME", "Soft Skills Analytics API")
APP_VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ---------------------------------------------------------------- dominio
# Habilidades blandas medidas en escala Likert 1-10 (1 columna por habilidad).
SKILLS = [
    "Comunicacion_Efectiva",
    "Trabajo_Equipo",
    "Resolucion_Conflictos",
    "Liderazgo",
]

SKILL_LABELS = {
    "Comunicacion_Efectiva": "Comunicación Efectiva",
    "Trabajo_Equipo": "Trabajo en Equipo",
    "Resolucion_Conflictos": "Resolución de Conflictos",
    "Liderazgo": "Liderazgo",
}

# Etiqueta canónica usada para identificar a cada empleado.
ID_EMPLEADO_PREFIX = "EMP"

# Contexto organizacional del dataset (generador sintético + carga).
DEPARTAMENTOS = ["Finanzas", "Marketing", "Operaciones", "Recursos_Humanos", "TI", "Ventas"]
PUESTOS = ["Junior", "Especialista", "Senior", "Lider", "Gerente"]

# Escala Likert usada en la valoración de cada habilidad.
LIKERT_MIN = 1
LIKERT_MAX = 10