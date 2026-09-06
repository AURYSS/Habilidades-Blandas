"""Endpoints de estadística descriptiva con algoritmos propios (habilidades blandas)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import SKILLS, SKILL_LABELS
from ..database import get_db
from ..schemas import DescriptiveResponse, FrequencyResponse
from ..services import statistics_service as stats
from ..services.repository import empleados_a_df
from ..services.visualizations import (
    plot_histograma_poligono,
    plot_matriz_correlacion,
    plot_distribucion_departamento,
)

router = APIRouter(prefix="/statistics", tags=["Estadística"])


@router.get("/descriptiva", response_model=DescriptiveResponse)
def descriptiva(db: Session = Depends(get_db)):
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")

    presentes = [c for c in SKILLS if c in df.columns]
    filas = stats.filas_descriptivas(df, presentes)
    return DescriptiveResponse(habilidades=presentes, filas=filas)


@router.get("/frecuencias", response_model=FrequencyResponse)
def frecuencias(
    habilidad: str = Query(SKILLS[0]),
    departamento: str | None = Query(None, description="Filtro por departamento"),
    db: Session = Depends(get_db),
):
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")

    if habilidad not in SKILLS or habilidad not in df.columns:
        raise HTTPException(400, f"Habilidad desconocida: {habilidad}. Válidas: {SKILLS}")

    if departamento:
        df = df[df["departamento"].astype(str) == departamento]

    valores = df[habilidad].dropna().tolist()
    if not valores:
        raise HTTPException(404, "Sin valores para la habilidad seleccionada.")

    tabla = stats.tabla_frecuencias_manual(valores)
    rango = stats.rango_manual(valores)
    k = stats.sturges(len(valores))
    k_int = int(round(k)) if k > 0 else 1
    controles = {
        "minimo": stats.minimo_manual(valores),
        "maximo": stats.maximo_manual(valores),
        "rango": round(rango, 3),
        "sturges": round(k, 3),
        "k_utilizado": k_int,
        "amplitud": round(stats.amplitud_manual(rango, k_int), 3),
        "promedio": round(stats.promedio_manual(valores), 3),
        "mediana": round(stats.mediana_manual(valores), 3) if stats.mediana_manual(valores) is not None else None,
        "moda": stats.moda_manual(valores),
        "varianza": round(stats.varianza_manual(valores), 3),
        "desviacion": round(stats.desviacion_estandar_manual(valores), 3),
        "cv": round(stats.cv_manual(valores), 2),
        "n": len(valores),
    }
    return FrequencyResponse(habilidad=habilidad, tabla=tabla, controles=controles)


@router.get("/graficos/dimension")
def grafico_dimension(
    habilidad: str = Query(SKILLS[0]),
    db: Session = Depends(get_db),
):
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")
    if habilidad not in SKILLS or habilidad not in df.columns:
        raise HTTPException(400, f"Habilidad desconocida: {habilidad}")
    serie = df[habilidad].dropna()
    return {
        "histograma": plot_histograma_poligono(serie, titulo=f"Frecuencias - {SKILL_LABELS.get(habilidad, habilidad)}"),
        "distribucion_departamento": plot_distribucion_departamento(df),
    }


@router.get("/graficos/correlacion")
def grafico_correlacion(db: Session = Depends(get_db)):
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")
    numericas = [c for c in SKILLS if c in df.columns]
    if len(numericas) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 habilidades para correlacionar.")
    return {"correlacion": plot_matriz_correlacion(df[numericas])}