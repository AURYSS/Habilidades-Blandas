"""Endpoints de exportación: CSV, Excel con datos filtrados, PDF de estadística base y clústeres."""

from __future__ import annotations

import io
import json

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import SKILLS
from ..database import get_db
from ..models import Asignacion, Experimento
from ..services import statistics_service as stats
from ..services.report_generator import (
    generar_pdf_base_stats,
    generar_pdf_report,
)
from ..services.repository import empleados_a_df
from ..services.visualizations import plot_pca_2d

router = APIRouter(prefix="/export", tags=["Exportación"])


def _df_filtrado(
    db: Session,
    departamento: str | None = None,
    puesto: str | None = None,
    antiguedad_min: int | None = None,
    antiguedad_max: int | None = None,
    habilidades: list[str] | None = None,
):
    df = empleados_a_df(db)
    if df.empty:
        return df, "No hay datos en la base."
    if departamento:
        df = df[df["departamento"].astype(str) == departamento]
    if puesto:
        df = df[df["puesto"].astype(str) == puesto]
    if antiguedad_min is not None:
        df = df[df["antiguedad_anos"] >= antiguedad_min]
    if antiguedad_max is not None:
        df = df[df["antiguedad_anos"] <= antiguedad_max]
    skills = [s for s in (habilidades or SKILLS) if s in df.columns]
    cols = ["id_empleado", "departamento", "puesto", "antiguedad_anos"] + skills
    cols = [c for c in cols if c in df.columns]
    return df[cols], None


@router.get("/csv")
def exportar_csv(sesion_id: int = Query(...), db: Session = Depends(get_db)):
    df = _df_resultados_sesion(db, sesion_id)
    df = df.replace({float("nan"): None})
    return Response(
        df.to_csv(index=False).encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="resultados_sesion_{sesion_id}.csv"'},
    )


@router.get("/excel")
def exportar_excel(sesion_id: int = Query(...), db: Session = Depends(get_db)):
    df = _df_resultados_sesion(db, sesion_id).replace({float("nan"): None})
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    return Response(
        buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="resultados_sesion_{sesion_id}.xlsx"'},
    )


@router.get("/excel-filtrado")
def exportar_excel_filtrado(
    departamento: str | None = None,
    puesto: str | None = None,
    antiguedad_min: int | None = None,
    antiguedad_max: int | None = None,
    habilidades: str | None = Query(None, description="Coma-separadas: las 2-4 habilidades seleccionadas"),
    db: Session = Depends(get_db),
):
    skills = [s.strip() for s in habilidades.split(",") if s.strip()] if habilidades else None
    df, err = _df_filtrado(db, departamento, puesto, antiguedad_min, antiguedad_max, skills)
    if df.empty:
        raise HTTPException(404, err or "Sin registros con esos filtros.")
    df = df.replace({float("nan"): None})
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="DatosFiltrados")
    return Response(
        buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="datos_filtrados_habilidades.xlsx"'},
    )


@router.get("/pdf-estadistica-base")
def exportar_pdf_estadistica_base(
    departamento: str | None = None,
    puesto: str | None = None,
    antiguedad_min: int | None = None,
    antiguedad_max: int | None = None,
    habilidades: str | None = Query(None, description="Coma-separadas: las 2-4 habilidades seleccionadas"),
    db: Session = Depends(get_db),
):
    skills = [s.strip() for s in habilidades.split(",") if s.strip()] if habilidades else None
    df, err = _df_filtrado(db, departamento, puesto, antiguedad_min, antiguedad_max, skills)
    if df.empty:
        raise HTTPException(404, err or "Sin registros con esos filtros.")

    sk = [c for c in SKILLS if c in df.columns]
    descripciones = stats.filas_descriptivas(df, sk)
    frecuencias, controles = {}, {}
    for h in sk:
        valores = df[h].dropna().tolist()
        frecuencias[h] = stats.tabla_frecuencias_manual(valores)
        rango = stats.rango_manual(valores)
        k = stats.sturges(len(valores))
        k_int = int(round(k)) if k > 0 else 1
        controles[h] = {
            "n": len(valores),
            "promedio": round(stats.promedio_manual(valores), 3),
            "varianza": round(stats.varianza_manual(valores), 3),
            "k_utilizado": k_int,
            "amplitud": round(stats.amplitud_manual(rango, k_int), 3),
        }

    filtros = {"departamento": departamento, "puesto": puesto,
               "antiguedad_min": antiguedad_min, "antiguedad_max": antiguedad_max}
    pdf = generar_pdf_base_stats(
        nombre_sesion="Estadística base (datos filtrados)",
        habilidades=sk,
        descripciones=descripciones,
        frecuencias=frecuencias,
        controles=controles,
        filtros=filtros,
    )
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="estadistica_base_habilidades.pdf"'},
    )


@router.get("/pdf")
def exportar_pdf(sesion_id: int = Query(...), db: Session = Depends(get_db)):
    exp = db.get(Experimento, sesion_id)
    if not exp:
        raise HTTPException(404, "Sesión no encontrada.")
    df = _df_resultados_sesion(db, sesion_id)
    if df.empty:
        raise HTTPException(404, "No hay datos.")

    skills = json.loads(exp.features or "[]")
    model_nombre = ""
    if exp.modelo_id:
        from ..models import Modelo as ModeloORM
        m = db.get(ModeloORM, exp.modelo_id)
        model_nombre = m.nombre if m else ""

    conteos = df["cluster"].value_counts().to_dict()
    conteos = {str(k): int(v) for k, v in conteos.items()}
    promedios = {}
    for c in sorted(df["cluster"].unique()):
        sub = df[df["cluster"] == c][skills]
        promedios[str(c)] = {s: round(float(sub[s].mean()), 3) for s in skills if s in sub.columns}

    metrics = {"Silhouette Score (Manual)": float(exp.silueta or 0.0)}
    if exp.inercia is not None:
        metrics["Inertia (Manual)"] = float(exp.inercia)

    graphs_bytes = []
    if len(skills) >= 2:
        try:
            from ..services.clustering_service import apply_pca_reduction
            df_feat = df[skills].copy().fillna(5)
            df_pca, _ = apply_pca_reduction(df_feat, n_components=2)
            hover = df[["id_empleado", "departamento"]].reset_index(drop=True)
            fig = plot_pca_2d(df_pca, df["cluster"].values, hover)
            graphs_bytes.append(fig_to_png_bytes(fig))
        except Exception:
            graphs_bytes = []

    pdf = generar_pdf_report(
        nombre_sesion=exp.nombre_sesion,
        algoritmo=exp.algoritmo,
        metrics=metrics,
        cluster_counts=conteos,
        graphs_bytes=graphs_bytes,
        skills=skills,
        modelo_nombre=model_nombre,
        promedio_por_cluster=promedios,
    )
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="reporte_clustering_{sesion_id}.pdf"'},
    )


def _df_resultados_sesion(db: Session, sesion_id: int) -> pd.DataFrame:
    exp = db.get(Experimento, sesion_id)
    if not exp:
        raise HTTPException(404, "Sesión no encontrada.")
    skills = json.loads(exp.features or "[]")
    df = empleados_a_df(db)
    if df.empty:
        return df
    asign = db.execute(
        select(Asignacion).where(Asignacion.experimento_id == sesion_id)
    ).scalars().all()
    mapa = {a.empleado_id: a.cluster for a in asign}
    df["cluster"] = df["id"].map(mapa).fillna(-1).astype(int)
    cols = ["id_empleado", "departamento", "puesto", "antiguedad_anos"] + [s for s in skills if s in df.columns]
    return df[cols + ["cluster"]]


def fig_to_png_bytes(fig: dict) -> bytes:
    import plotly.io as pio

    return pio.from_json(json.dumps(fig)).to_image(format="png", width=900, height=550)