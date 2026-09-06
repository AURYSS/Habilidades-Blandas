"""Endpoints de ingesta y consulta de datos (habilidades blandas)."""

from __future__ import annotations

import io
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..config import SKILLS
from ..database import get_db
from ..models import Empleado
from ..schemas import DataMeta, DataPage, SegmentRequest
from ..services.data_loader import load_and_validate_csv
from ..services.repository import COLUMNAS, empleados_a_df
from ..services.synthetic import generar_dataset

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["Datos"])


def _limpio_df(df):
    return df.replace({float("nan"): None, "NaN": None, "None": None})


@router.get("/meta", response_model=DataMeta)
def obtener_meta(db: Session = Depends(get_db)):
    try:
        df = empleados_a_df(db)
        departamentos = sorted(df["departamento"].dropna().unique().tolist()) if not df.empty else []
        puestos = sorted(df["puesto"].dropna().unique().tolist()) if not df.empty else []
        ant_min = int(df["antiguedad_anos"].min()) if not df.empty and df["antiguedad_anos"].notna().any() else None
        ant_max = int(df["antiguedad_anos"].max()) if not df.empty and df["antiguedad_anos"].notna().any() else None
        presentes = [s for s in SKILLS if s in df.columns and df[s].notna().any()]
        return DataMeta(
            total=len(df),
            departamentos=departamentos,
            puestos=puestos,
            habilidades=presentes,
            antiguedad_min=ant_min,
            antiguedad_max=ant_max,
            db_status="online",
            db_message="Conexión exitosa",
        )
    except Exception as e:
        logger.error("Meta DB error: %s", e)
        return DataMeta(
            total=0, departamentos=[], puestos=[], habilidades=[], db_status="offline", db_message=str(e)
        )


@router.get("", response_model=DataPage)
def listar_datos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    df = empleados_a_df(db)
    total = len(df)
    start = (page - 1) * page_size
    registros = _limpio_df(df.iloc[start:start + page_size]).to_dict("records")
    return DataPage(total=total, page=page, page_size=page_size, records=registros)


@router.post("/segmentar")
def segmentar(body: SegmentRequest | None = None, db: Session = Depends(get_db)):
    body = body or SegmentRequest()
    df = empleados_a_df(db)
    if body.departamento:
        df = df[df["departamento"].astype(str) == body.departamento]
    if body.puesto:
        df = df[df["puesto"].astype(str) == body.puesto]
    if body.antiguedad_min is not None:
        df = df[df["antiguedad_anos"] >= body.antiguedad_min]
    if body.antiguedad_max is not None:
        df = df[df["antiguedad_anos"] <= body.antiguedad_max]
    if body.habilidad and body.habilidad in df.columns:
        if body.umbral_min is not None:
            df = df[df[body.habilidad] >= body.umbral_min]
        if body.umbral_max is not None:
            df = df[df[body.habilidad] <= body.umbral_max]
    df = _limpio_df(df)
    return {"total": len(df), "records": df.to_dict("records")}


@router.post("/upload")
def subir_archivo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    nombre = file.filename or "dataset.csv"
    try:
        contenido = file.file.read()
    except Exception as e:
        raise HTTPException(400, f"Error leyendo archivo: {e}")

    df, msg = load_and_validate_csv(io.BytesIO(contenido), nombre)
    if df is None:
        raise HTTPException(400, f"Validación fallida: {msg}")

    n_antes = db.execute(select(func.count()).select_from(Empleado)).scalar_one()
    columnas_empleado = [c for c in COLUMNAS if c in df.columns]
    objectos = [
        Empleado(**{k: (None if (v is not None and v != v) else v) for k, v in row.items() if k in columnas_empleado})
        for _, row in df.iterrows()
    ]
    db.add_all(objectos)
    db.commit()
    n_total = db.execute(select(func.count()).select_from(Empleado)).scalar_one()
    return {"insertados": len(objectos), "total_tabla": n_total, "mensaje": msg}


@router.post("/sintetico")
def generar_sintetico(cantidad: int = Query(2500, ge=1, le=50000), db: Session = Depends(get_db)):
    df = _limpio_df(generar_dataset(cantidad))
    objectos = [Empleado(**{k: row[k] for k in df.columns}) for _, row in df.iterrows()]
    db.add_all(objectos)
    db.commit()
    total = db.execute(select(func.count()).select_from(Empleado)).scalar_one()
    return {"generados": len(objectos), "total_tabla": int(total)}


@router.delete("", status_code=204)
def limpiar_datos(db: Session = Depends(get_db)):
    db.execute(delete(Empleado))
    db.commit()
    return None