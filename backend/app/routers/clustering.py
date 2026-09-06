"""Endpoints del motor de análisis no supervisado (habilidades blandas).

Flujo académico: el usuario elige 2-4 habilidades y un modelo pre-entrenado
(y seleccionable en la app) de la base de conocimiento; el algoritmo se aplica
a los datos cargados y produce asignaciones de clúster, estadísticas propias y
visualizaciones.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Asignacion, Experimento, Modelo
from ..schemas import (
    AplicarModeloRequest,
    AplicarModeloResponse,
    ClusterPlotsRequest,
    ClusterPlotsResponse,
    ElbowRequest,
    EntrenarBaseRequest,
    EntrenarModelosResult,
    ModeloRegistro,
)
from ..services import clustering_service as cs
from ..services import pretrained
from ..services.repository import empleados_a_df
from ..services.visualizations import (
    plot_distribucion_departamento_cluster,
    plot_metodo_codo,
    plot_pca_2d,
    plot_pca_3d,
    plot_perfil_clusters,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clustering", tags=["Clustering"])


def _modelo_a_registro(m: Modelo) -> ModeloRegistro:
    skills = json.loads(m.features or "[]")
    return ModeloRegistro(
        id=m.id,
        nombre=m.nombre,
        algoritmo=m.algoritmo,
        skills=skills,
        k_clusters=m.k_clusters,
        inercia=round(m.inercia, 4) if m.inercia is not None else None,
        silueta=round(m.silueta, 4) if m.silueta is not None else None,
        parametros=json.loads(m.parametros or "{}"),
        timestamp=m.timestamp,
    )


def _buscar_modelo(db: Session, skills: list[str], algoritmo: str, modelo_id: int | None = None) -> Modelo:
    if modelo_id is not None:
        m = db.get(Modelo, modelo_id)
        if not m:
            raise HTTPException(404, f"Modelo {modelo_id} no encontrado.")
        return m
    candidatos = db.execute(
        select(Modelo)
        .where(Modelo.algoritmo == algoritmo)
        .order_by(desc(Modelo.timestamp))
    ).scalars().all()
    objetivo = set(skills)
    for m in candidatos:
        feats = set(json.loads(m.features or "[]"))
        if feats == objetivo:
            return m
    raise HTTPException(
        404,
        "No existe un modelo pre-entrenado para esa combinación y algoritmo. "
        "Ejecuta 'reentrenar-base' primero.",
    )


@router.get("/modelos", response_model=list[ModeloRegistro])
def listar_modelos(
    skills: str | None = None,
    algoritmo: str | None = None,
    db: Session = Depends(get_db),
):
    """Lista de la base de conocimiento. Filtra por habilidades y/o algoritmo."""
    q = select(Modelo).order_by(desc(Modelo.timestamp))
    if algoritmo:
        q = q.where(Modelo.algoritmo == algoritmo)
    modelos = db.execute(q).scalars().all()
    if skills:
        objetivo = set(s for s in skills.split(",") if s.strip())
        modelos = [m for m in modelos if set(json.loads(m.features or "[]")) == objetivo]
    return [_modelo_a_registro(m) for m in modelos]


@router.post("/elbow")
def metodo_codo(body: ElbowRequest, db: Session = Depends(get_db)):
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")

    skills = [s for s in body.skills if s in df.columns]
    if len(skills) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 habilidades presentes en los datos.")

    df_feat = df[skills].copy()
    k_values, inercias, recomendacion = cs.aplicar_minmax_por_elbow(df_feat, normalize=body.normalize)

    # Paso final: entrenar K-Means con el K recomendado para exponer métricas.
    X = cs.normalizacion_min_max_aplicar(df_feat, skills, cs.normalizacion_min_max_fit(df_feat, skills))
    _, _, metrics = cs.train_clustering_model(X, "kmeans", {"n_clusters": recomendacion})

    return {
        "skills": skills,
        "k_values": k_values,
        "inercias": inercias,
        "grafico": plot_metodo_codo(k_values, inercias),
        "recomendacion": recomendacion,
        "n": int(len(df_feat)),
        "silueta": round(float(metrics.get("Silhouette Score (Manual)", 0.0)), 4),
    }


@router.post("/aplicar", response_model=AplicarModeloResponse)
def aplicar_modelo(body: AplicarModeloRequest, db: Session = Depends(get_db)):
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")

    skills = [s for s in body.skills if s in df.columns]
    if len(skills) < 2:
        raise HTTPException(400, "Los datos deben contener al menos 2 de las habilidades seleccionadas.")

    modelo = _buscar_modelo(db, body.skills, body.algoritmo, body.modelo_id)
    params = json.loads(modelo.parametros or "{}")
    escala = params.get("normalizacion", {}) or cs.normalizacion_min_max_fit(df[skills], skills)

    # Aplicar el modelo pre-entrenado sobre la carga actual.
    df_feat = cs.normalizacion_min_max_aplicar(df[skills], skills, escala).fillna(5)
    X = df_feat.values
    model = cs.load_model_bundle(modelo.ruta_modelo)
    labels = cs.aplicar_modelo(model, modelo.algoritmo, X, params)

    # Métricas propias sobre la aplicación actual.
    inercia = None
    if modelo.algoritmo == "kmeans":
        unicos = sorted(set(labels))
        centroids = [X[labels == c].mean(axis=0) for c in unicos]
        inercia = cs.inercia_manual(X, labels, centroids)
    silueta = cs.silueta_manual(X, labels)

    df_res = df.copy()
    df_res["cluster"] = labels

    # Persistir sesión y asignaciones.
    k_clusters = len(set(labels))
    exp = Experimento(
        nombre_sesion=body.nombre_sesion,
        algoritmo=modelo.algoritmo,
        modelo_id=modelo.id,
        k_clusters=k_clusters,
        inercia=float(inercia) if inercia is not None else None,
        silueta=float(silueta) if silueta is not None else None,
        ruta_modelo=modelo.ruta_modelo,
        features=json.dumps(skills),
        parametros=json.dumps({
            "modelo_nombre": modelo.nombre,
            "normalizacion": escala,
            "algoritmo": modelo.algoritmo,
            **params,
        }),
        timestamp=datetime.utcnow(),
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    db.execute(Asignacion.__table__.delete().where(Asignacion.experimento_id == exp.id))
    db.add_all([
        Asignacion(experimento_id=exp.id, empleado_id=int(r["id"]), cluster=int(lbl))
        for r, lbl in zip(df_res.to_dict("records"), labels)
    ])
    db.commit()

    conteo = {str(c): int(np.sum(labels == c)) for c in sorted(set(labels))}
    promedios = {}
    for c in sorted(set(labels)):
        filas = df_res[df_res["cluster"] == c][skills]
        promedios[str(c)] = {s: round(float(filas[s].mean()), 3) for s in skills}

    filas = df_res.replace({float("nan"): None}).to_dict("records")
    return AplicarModeloResponse(
        sesion_id=exp.id,
        nombre_sesion=body.nombre_sesion,
        algoritmo=modelo.algoritmo,
        modelo_id=modelo.id,
        modelo_nombre=modelo.nombre,
        skills=skills,
        k_clusters=k_clusters,
        silueta=round(float(silueta), 4) if silueta is not None else None,
        inercia=round(float(inercia), 4) if inercia is not None else None,
        asignados=int(np.sum(labels != -1)),
        totales=int(len(df_res)),
        conteo_clusters=conteo,
        promedio_por_cluster=promedios,
        filas=[{**f, "cluster": int(f["cluster"])} for f in filas],
    )


@router.post("/plots", response_model=ClusterPlotsResponse)
def graficas_clusters(body: ClusterPlotsRequest, db: Session = Depends(get_db)):
    exp = db.get(Experimento, body.sesion_id)
    if not exp:
        raise HTTPException(404, "Sesión no encontrada.")
    skills = json.loads(exp.features or "[]")
    if not skills:
        raise HTTPException(400, "La sesión no tiene habilidades definidas.")

    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base.")

    asign = db.execute(
        select(Asignacion).where(Asignacion.experimento_id == exp.id)
    ).scalars().all()
    if not asign:
        raise HTTPException(404, "La sesión no tiene asignaciones.")

    mapa = {a.empleado_id: a.cluster for a in asign}
    df_res = df.copy()
    df_res["Cluster"] = df_res["id"].map(mapa).astype(int)

    df_feat = df_res[skills].copy().fillna(5)
    df_pca, varianza = cs.apply_pca_reduction(df_feat, n_components=3)
    if "PC3" not in df_pca.columns:
        df_pca["PC3"] = 0.0
    hover = df_res[["id_empleado", "departamento", "puesto"]].reset_index(drop=True)

    return ClusterPlotsResponse(
        pca_2d=plot_pca_2d(df_pca, df_res["Cluster"].values, hover),
        pca_3d=plot_pca_3d(df_pca, df_res["Cluster"].values, hover),
        distribucion_departamento=plot_distribucion_departamento_cluster(
            df_res[["Cluster", "departamento"]]
        ),
        perfil_clusters=plot_perfil_clusters(df_feat, df_res["Cluster"].values),
        varianza_explicada=[round(float(v), 4) for v in varianza],
    )


@router.post("/reentrenar-base", response_model=EntrenarModelosResult)
def reentrenar_base(body: EntrenarBaseRequest, db: Session = Depends(get_db)):
    """Genera (o completa) la base de conocimiento con todos los subconjuntos de habilidades."""
    df = empleados_a_df(db)
    if df.empty:
        raise HTTPException(404, "No hay datos en la base para entrenar. Carga primero un dataset.")

    nuevos = pretrained.crear_modelos_base(df, db)
    todos = db.execute(select(Modelo).order_by(desc(Modelo.timestamp))).scalars().all()
    return EntrenarModelosResult(
        generados=len(nuevos),
        modelos=[_modelo_a_registro(m) for m in todos],
    )