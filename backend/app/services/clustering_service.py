"""Servicio de clustering: entrenamiento, métricas manuales, PCA, persistencia y aplicación.

Los modelos se pre-entrenan fuera de línea (scripts/train_pretrained.py) y se
almacenan como `.pkl` en backend/models/ con un registro en la tabla `modelos`.
La app selecciona un modelo de la base de conocimiento y lo aplica a la carga
actual de datos para producir asignaciones de clúster.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

from ..config import MODELS_DIR


# ---------------------------------------------------------------- fórmulas propias
def distancia_euclidiana(p1, p2):
    return sum((a - b) ** 2 for a, b in zip(p1, p2)) ** 0.5


def inercia_manual(X, labels, centroids) -> float:
    inercia = 0.0
    for i, punto in enumerate(X):
        c = centroids[labels[i]]
        inercia += sum((a - b) ** 2 for a, b in zip(punto, c))
    return inercia


def silueta_manual(X, labels) -> float:
    n = len(X)
    if n < 2 or len(set(labels)) < 2:
        return 0.0
    unicos = np.unique(labels)
    s_total = 0.0
    for i in range(n):
        x_i = X[i]
        lbl = labels[i]
        same = np.where((labels == lbl) & (np.arange(n) != i))[0]
        a_i = (
            np.mean(np.sqrt(((X[same] - x_i) ** 2).sum(axis=1)))
            if len(same)
            else 0.0
        )
        b_i = float("inf")
        for otro in unicos:
            if otro == lbl:
                continue
            mask = labels == otro
            avg = np.mean(np.sqrt(((X[mask] - x_i) ** 2).sum(axis=1)))
            b_i = min(b_i, avg)
        if a_i == 0.0 and b_i == float("inf"):
            s_total += 0.0
        else:
            s_total += (b_i - a_i) / max(a_i, b_i)
    return float(s_total / n)


def normalizacion_min_max_fit(df: pd.DataFrame, cols: list[str]) -> dict[str, dict[str, float]]:
    """Ajusta min/max por columna (criterio propio, sin sklearn)."""
    escala = {}
    for col in cols:
        valores = df[col].dropna().tolist()
        if not valores:
            escala[col] = {"min": 0.0, "max": 1.0}
            continue
        vmin, vmax = float(min(valores)), float(max(valores))
        escala[col] = {"min": vmin, "max": vmax}
    return escala


def normalizacion_min_max_aplicar(df: pd.DataFrame, cols: list[str], escala: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Aplica la normalización min-max con la escala pre-calculada."""
    df_out = df.copy()
    for col in cols:
        s = escala.get(col, {"min": 0.0, "max": 1.0})
        rango = s["max"] - s["min"]
        if rango == 0:
            df_out[col] = 0.0
        else:
            df_out[col] = (df[col].astype(float) - s["min"]) / rango
    return df_out


# ---------------------------------------------------------------- entrenamiento
def train_clustering_model(df_features: pd.DataFrame, algorithm="kmeans", params=None, fill_value: float = 5.0):
    params = params or {}
    df_filled = df_features.fillna(fill_value)
    X = df_filled.values
    metrics: dict[str, Any] = {}
    model, labels = None, None

    if algorithm == "kmeans":
        n_clusters = params.get("n_clusters", 3)
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = model.fit_predict(X)
        metrics["Inertia (Manual)"] = float(inercia_manual(X, labels, model.cluster_centers_))
        metrics["Silhouette Score (Manual)"] = (
            float(silueta_manual(X, labels)) if len(set(labels)) > 1 else 0.0
        )
        metrics["Clusters"] = int(n_clusters)
    elif algorithm == "dbscan":
        eps = float(params.get("eps", 2.0))
        min_samples = int(params.get("min_samples", 5))
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(X)
        mask = labels != -1
        metrics["Silhouette Score"] = (
            float(silhouette_score(X[mask], labels[mask]))
            if len(set(labels[mask])) > 1 and len(labels[mask]) > 1
            else 0.0
        )
        metrics["Noise points"] = int(np.sum(labels == -1))
        metrics["Clusters"] = int(len(set(labels)) - (1 if -1 in labels else 0))
    elif algorithm == "gmm":
        n_components = int(params.get("n_components", 3))
        model = GaussianMixture(n_components=n_components, random_state=42)
        model.fit(X)
        labels = model.predict(X)
        metrics["BIC"] = float(model.bic(X))
        metrics["AIC"] = float(model.aic(X))
        metrics["Clusters"] = int(n_components)
        metrics["Silhouette Score"] = (
            float(silhouette_score(X, labels)) if len(set(labels)) > 1 else 0.0
        )
    else:
        raise ValueError(f"Algoritmo desconocido: {algorithm}")

    return model, labels, metrics


def aplicar_modelo(model, algorithm: str, X_ndarray: np.ndarray, params: dict | None = None) -> np.ndarray:
    """Aplica un modelo pre-entrenado (o su configuración) a datos nuevos."""
    params = params or {}
    if algorithm == "kmeans" or algorithm == "gmm":
        return model.predict(X_ndarray)
    if algorithm == "dbscan":
        db = DBSCAN(
            eps=float(params.get("eps", 2.0)),
            min_samples=int(params.get("min_samples", 5)),
        )
        return db.fit_predict(X_ndarray)
    raise ValueError(f"Algoritmo desconocido: {algorithm}")


def elegir_k_por_codo(k_values: list[int], inercias: list[float]) -> int:
    """Heurística de punto de codo: mayor pérdida relativa de inercia."""
    if len(inercias) < 3:
        return k_values[-1]
    mejor_k, mejor_ratio = k_values[0], 0.0
    prev = inercias[0]
    for k, iner in zip(k_values[1:], inercias[1:]):
        ratio = (prev - iner) / prev if prev else 0.0
        if ratio > mejor_ratio:
            mejor_ratio, mejor_k = ratio, k
        prev = iner
    return mejor_k


def aplicar_minmax_por_elbow(df_feat: pd.DataFrame, normalize: bool = True):
    """Devuelve k recomendado + inercias para codo (k=2..8)."""
    k_values = list(range(2, 9))
    inercias = []
    for k in k_values:
        X = df_feat.copy()
        if normalize:
            escala = normalizacion_min_max_fit(X, list(X.columns))
            X = normalizacion_min_max_aplicar(X, list(X.columns), escala)
        _, labels, metrics = train_clustering_model(X, "kmeans", {"n_clusters": k})
        inercias.append(round(float(metrics["Inertia (Manual)"]), 2))
    return k_values, inercias, elegir_k_por_codo(k_values, inercias)


# ---------------------------------------------------------------- PCA y persistencia
def apply_pca_reduction(df_features: pd.DataFrame, n_components: int = 3):
    n_components = max(2, min(int(n_components), df_features.shape[1], len(df_features)))
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(df_features.fillna(5))
    cols = [f"PC{i + 1}" for i in range(n_components)]
    return pd.DataFrame(X_pca, columns=cols, index=df_features.index), pca.explained_variance_ratio_.tolist()


def save_model_bundle(model, nombre: str) -> str:
    """Guarda el modelo como pkl y devuelve la ruta."""
    path = MODELS_DIR / f"{nombre}.pkl"
    joblib.dump(model, path)
    return str(path)


def load_model_bundle(path: str):
    return joblib.load(path)