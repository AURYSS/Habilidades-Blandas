"""Servicio de carga y validación de datasets de habilidades blandas."""

from __future__ import annotations

from typing import BinaryIO

import pandas as pd

from ..config import SKILLS

# Sinónimos aceptados en los encabezados para cada habilidad.
SKILL_ALIASES: dict[str, list[str]] = {
    "Comunicacion_Efectiva": [
        "Comunicacion_Efectiva", "Comunicación Efectiva", "Comunicacion efectiva",
        "Comunicación efectiva", "Comunicación",
    ],
    "Trabajo_Equipo": [
        "Trabajo_Equipo", "Trabajo en Equipo", "Trabajo en equipo",
        "Trabajo_equipo", "Trabajo en grupo", "Colaboración",
    ],
    "Resolucion_Conflictos": [
        "Resolucion_Conflictos", "Resolución de Conflictos", "Resolucion de conflictos",
        "Resolución de conflictos", "Resolucion_De_Conflictos",
    ],
    "Liderazgo": ["Liderazgo", "Leadership"],
}

CONTEXTO_COLS = [
    ("id_empleado", ["id_empleado", "id", "empleado", "ID Empleado", "matricula", "Matrícula", "clave"]),
    ("departamento", ["departamento", "Departamento", "área", "area", "depto", "unidad"]),
    ("puesto", ["puesto", "Puesto", "rol", "cargo", "posición"]),
    ("antiguedad_anos", ["antiguedad_anos", "antigüedad", "antigüedad (años)", "anos_antiguedad", "years experience", "experiencia"]),
]

METADATA_REQUERIDAS = ["departamento"]


def _normalizar_columna(col: str) -> str:
    return (str(col).strip().replace("  ", " ").lower())


def _buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    low = {_normalizar_columna(c): c for c in df.columns}
    for cand in candidatos:
        key = _normalizar_columna(cand)
        if key in low:
            return low[key]
    return None


def parse_likert_1_10(val) -> int | None:
    if pd.isnull(val):
        return None
    texto = str(val).strip()
    if not texto:
        return None
    try:
        num = float(texto.replace(",", "."))
        if 1 <= num <= 10:
            return int(round(num))
        return None
    except ValueError:
        return None


def load_and_validate_csv(file_obj: BinaryIO, filename: str = ""):
    """Carga CSV/Excel y lo estandariza al esquema canónico de habilidades blandas."""
    try:
        name = (filename or getattr(file_obj, "name", "")).lower()
        if name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_obj)
        else:
            df = pd.read_csv(file_obj)
    except Exception as e:
        return None, f"Error al leer el archivo: {e}"

    if df.empty:
        return None, "El archivo no contiene registros."

    # Habilidades: normalizar a claves canónicas, restando lo que no se pudo
    # mapear para informar al usuario.
    out = {}
    no_encontradas = []
    for canon in SKILLS:
        col = _buscar_columna(df, SKILL_ALIASES[canon])
        if col is None:
            no_encontradas.append(SKILL_LABEL(canon))
            continue
        valores = df[col].apply(parse_likert_1_10)
        if valores.notna().sum() == 0:
            no_encontradas.append(SKILL_LABEL(canon))
            continue
        out[canon] = valores

    # Contexto organizacional.
    contexto = {}
    for canon, candidatos in CONTEXTO_COLS:
        col = _buscar_columna(df, candidatos)
        if col is not None:
            contexto[canon] = df[col]
    if "id_empleado" in contexto:
        contexto["id_empleado"] = contexto["id_empleado"].astype(str).replace(
            {r"^\s*$": None}, regex=True
        )
    if "antiguedad_anos" in contexto:
        contexto["antiguedad_anos"] = (
            pd.to_numeric(contexto["antiguedad_anos"], errors="coerce")
            .fillna(0).astype(int)
        )

    df_out = pd.DataFrame({**contexto, **out})

    if "departamento" not in df_out.columns:
        return None, "No se encontró la columna 'departamento'."

    al_menos = sum(c in df_out.columns for c in SKILLS)
    if al_menos < 2:
        return None, (
            "Se necesitan al menos 2 habilidades valoradas (Likert 1-10). "
            f"Faltan o no validan: {', '.join(no_encontradas)}."
        )

    if no_encontradas:
        return df_out, f"Validación exitosa. Sin mapear: {', '.join(no_encontradas)}; se ignora lo no relacionado."
    return df_out, "Validación exitosa. Formato canónico de habilidades blandas."


def SKILL_LABEL(key: str) -> str:
    from ..config import SKILL_LABELS
    return SKILL_LABELS.get(key, key)