"""Endpoints de historial de sesiones de análisis (habilidades blandas)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Asignacion, Empleado, Experimento, Modelo
from ..schemas import ApplySessionResponse, HistoricoResumen

router = APIRouter(prefix="/history", tags=["Historial"])


@router.get("", response_model=list[HistoricoResumen])
def listar_historial(db: Session = Depends(get_db)):
    items = db.execute(select(Experimento).order_by(Experimento.timestamp.desc())).scalars().all()
    return [
        HistoricoResumen(
            id=e.id,
            nombre_sesion=e.nombre_sesion,
            algoritmo=e.algoritmo,
            skills=json.loads(e.features or "[]"),
            modelo_id=e.modelo_id,
            k_clusters=e.k_clusters,
            inercia=e.inercia,
            silueta=e.silueta,
            ruta_modelo=e.ruta_modelo,
            timestamp=e.timestamp,
        )
        for e in items
    ]


@router.get("/{sesion_id}/asignaciones", response_model=ApplySessionResponse)
def asignaciones_sesion(sesion_id: int, db: Session = Depends(get_db)):
    exp = db.get(Experimento, sesion_id)
    if not exp:
        raise HTTPException(404, "Sesión no encontrada.")
    asign = db.execute(
        select(Asignacion).where(Asignacion.experimento_id == sesion_id)
    ).scalars().all()
    return ApplySessionResponse(
        sesion_id=sesion_id,
        asignaciones=[
            {"empleado_id": a.empleado_id, "cluster": a.cluster}
            for a in asign
        ],
    )


@router.get("/{sesion_id}/detalle")
def detalle_experimento(sesion_id: int, db: Session = Depends(get_db)):
    exp = db.get(Experimento, sesion_id)
    if not exp:
        raise HTTPException(404, "Sesión no encontrada.")

    parametros = json.loads(exp.parametros or "{}")
    skills = json.loads(exp.features or "[]")
    modelo_info = None
    if exp.modelo_id:
        m = db.get(Modelo, exp.modelo_id)
        if m:
            modelo_info = {
                "nombre": m.nombre,
                "algoritmo": m.algoritmo,
                "skills": json.loads(m.features or "[]"),
                "k_clusters": m.k_clusters,
                "silueta": m.silueta,
                "inercia": m.inercia,
            }

    asignados = db.execute(
        select(func.count(Asignacion.id)).where(Asignacion.experimento_id == sesion_id)
    ).scalar() or 0
    totales = db.execute(select(func.count(Empleado.id))).scalar() or 0

    recomendacion = None
    if exp.silueta is not None:
        s = float(exp.silueta)
        if s < 0.25:
            recomendacion = (
                f"La silhouette media ({s:.4f}) es baja: revisa la heterogeneidad de los datos "
                "o selecciona otro modelo de la base de conocimiento."
            )
        elif s > 0.55:
            recomendacion = (
                f"Silhouette media de {s:.4f}: las agrupaciones son sólidas y permiten "
                "perfilar segmentos de colaboradores diferenciados."
            )

    return {
        "base": {
            "nombre_sesion": exp.nombre_sesion,
            "algoritmo": exp.algoritmo.upper(),
            "k_clusters": exp.k_clusters,
            "skills": skills,
            "modelo": modelo_info,
            "normalizar": bool(parametros.get("normalizacion")),
            "creado": exp.timestamp.isoformat() if exp.timestamp else None,
        },
        "silueta": exp.silueta,
        "inercia": exp.inercia,
        "recomendacion_extra": recomendacion,
        "asignados": asignados,
        "totales": totales,
    }


@router.delete("/{sesion_id}", status_code=204)
def eliminar_sesion(sesion_id: int, db: Session = Depends(get_db)):
    exp = db.get(Experimento, sesion_id)
    if not exp:
        raise HTTPException(404, "Sesión no encontrada.")
    db.delete(exp)
    db.commit()
    return None