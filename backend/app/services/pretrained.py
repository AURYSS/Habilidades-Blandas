"""Pre-entrenamiento de la base de conocimiento.

Cumple el requisito académico: antes de la exposición, el algoritmo se alimenta
con el dataset (datos reales) para generar su propio conocimiento. Cada modelo
se entrena sobre un subconjunto de 2-4 habilidades (todas las combinaciones) con
normalización min-max propia, se guarda como `{nombre}.pkl` y se registra en la
tabla `modelos` para ser seleccionable desde la app.

Heurísticas usadas (algoritmos propios, sin dependencias en sklearn excepto el
ajuste del modelo en sí):
- K-Means: número de clústeres por método del codo.
- DBSCAN: eps a partir del cuantil de la distribución de distancias a los
  k-vecinos más cercanos; min_samples = 3.
- GMM: número de componentes por mínimo BIC.
"""

from __future__ import annotations

import itertools
import json
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..config import SKILLS, SKILL_LABELS, MODELS_DIR
from ..models import Modelo
from .clustering_service import (
    elegir_k_por_codo,
    normalizacion_min_max_aplicar,
    normalizacion_min_max_fit,
    save_model_bundle,
    train_clustering_model,
)

ALGORITMOS = ["kmeans"]


def _eps_dbscan(X: np.ndarray, min_samples: int = 3, quantile: float = 0.15) -> float:
    """Heurística de eps: cuantil de la distancia al vecino min_samples."""
    n = len(X)
    if n <= min_samples:
        return 1.0
    dists = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=-1)
    np.fill_diagonal(dists, np.inf)
    kth = np.partition(dists, min_samples, axis=1)[:, min_samples]
    kth = kth[np.isfinite(kth)]
    if len(kth) == 0:
        return 1.0
    kth_positivos = kth[kth > 1e-9]
    if len(kth_positivos) == 0:
        return 1.0
    eps = float(np.quantile(kth_positivos, quantile))
    if eps <= 1e-9:
        eps = float(np.min(kth_positivos))
    return max(eps, 1e-6)


def _nombre_modelo(algoritmo: str, skills: list[str]) -> str:
    cortos = [SKILL_LABELS.get(s, s).split(" ")[0].lower() for s in skills]
    base = f"{algoritmo}_{'_'.join(cortos)}".replace("á", "a").replace("é", "e")
    return base[:80]


def _configuracion_y_entrenamiento(df_feat: pd.DataFrame, algoritmo: str, escala: dict):
    """Determina hiperparámetros según heurística y devuelve (model, labels, metrics, params_extra)."""
    X = normalizacion_min_max_aplicar(df_feat, list(df_feat.columns), escala)

    if algoritmo == "kmeans":
        k_values = list(range(2, 9))
        inercias = []
        for k in k_values:
            _, _, m = train_clustering_model(X, "kmeans", {"n_clusters": k})
            inercias.append(m["Inertia (Manual)"])
        k = elegir_k_por_codo(k_values, inercias)
        model, labels, metrics = train_clustering_model(X, "kmeans", {"n_clusters": k})
        return model, labels, metrics, {"n_clusters": k}

    if algoritmo == "dbscan":
        min_samples = 3
        eps = _eps_dbscan(X.values, min_samples)
        model, labels, metrics = train_clustering_model(
            X, "dbscan", {"eps": eps, "min_samples": min_samples}
        )
        return model, labels, metrics, {"eps": round(eps, 4), "min_samples": min_samples}

    if algoritmo == "gmm":
        mejor_k, mejor_bic, mejor_modelo, mejor_labels, mejor_metrics = 2, float("inf"), None, None, None
        for k in range(2, 9):
            model, labels, metrics = train_clustering_model(X, "gmm", {"n_components": k})
            bic = metrics.get("BIC", float("inf"))
            if bic < mejor_bic:
                mejor_bic, mejor_k = bic, k
                mejor_modelo, mejor_labels, mejor_metrics = model, labels, metrics
        return mejor_modelo, mejor_labels, mejor_metrics, {"n_components": mejor_k}

    raise ValueError(algoritmo)


def entrenar_y_registrar(df: pd.DataFrame, skills: list[str], algoritmo: str, db: Session, es_base: bool = True, overwrite: bool = False):
    """Entrena un modelo para un subconjunto de habilidades y lo registra en la BD."""
    skills = sorted(set(skills))
    if not set(skills).issubset(set(SKILLS)):
        raise ValueError(f"Habilidades inválidas: {skills}")
    df_feat = df[skills].copy().dropna()
    if len(df_feat) < 10:
        raise ValueError("Se necesitan al menos 10 registros con datos completos para entrenar.")

    escala = normalizacion_min_max_fit(df_feat, skills)
    model, labels, metrics, extra = _configuracion_y_entrenamiento(df_feat, algoritmo, escala)

    nombre = _nombre_modelo(algoritmo, skills)
    existe = db.query(Modelo).filter(Modelo.nombre == nombre).first()
    if existe and not overwrite:
        return None

    path = save_model_bundle(model, nombre)
    k_clusters = metrics.get("Clusters", extra.get("n_clusters", extra.get("n_components", 3)))
    silueta = metrics.get("Silhouette Score (Manual)", metrics.get("Silhouette Score", 0.0))
    inercia = metrics.get("Inertia (Manual)")

    if existe and overwrite:
        existe.k_clusters = int(k_clusters) if k_clusters is not None else None
        existe.parametros = json.dumps({
            **extra,
            "normalizacion": escala,
            "npuntos": int(len(df_feat)),
        })
        existe.inercia = round(float(inercia), 4) if inercia is not None else None
        existe.silueta = round(float(silueta), 4) if silueta is not None else None
        existe.ruta_modelo = path
        existe.timestamp = datetime.utcnow()
        db.commit()
        db.refresh(existe)
        return existe.id
    else:
        modelo = Modelo(
            nombre=nombre,
            algoritmo=algoritmo,
            features=json.dumps(skills),
            k_clusters=int(k_clusters) if k_clusters is not None else None,
            parametros=json.dumps({
                **extra,
                "normalizacion": escala,
                "npuntos": int(len(df_feat)),
            }),
            inercia=round(float(inercia), 4) if inercia is not None else None,
            silueta=round(float(silueta), 4) if silueta is not None else None,
            ruta_modelo=path,
            ruta_scaler=None,
            es_base=es_base,
            timestamp=datetime.utcnow(),
        )
        db.add(modelo)
        db.commit()
        db.refresh(modelo)
        return modelo.id


def crear_modelos_base(df: pd.DataFrame, db: Session) -> list[int]:
    """Entrena todos los subconjuntos de 2-4 habilidades para cada algoritmo.

    Devuelve los ids de los modelos recién generados (omite los ya existentes).
    """
    nuevos = []
    for r in range(2, 5):
        for skills in itertools.combinations(SKILLS, r):
            for algoritmo in ALGORITMOS:
                mid = entrenar_y_registrar(df, list(skills), algoritmo, db)
                if mid is not None:
                    nuevos.append(mid)
    return nuevos


def compatibles(df_features: list[str]):
    """Filtra filas de modelo según el subconjunto exacto de habilidades."""
    return df_features