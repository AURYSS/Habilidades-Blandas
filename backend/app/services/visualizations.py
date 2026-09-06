"""Servicio de visualización: genera figuras Plotly listas para renderizar en el front."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

COLORES = [
    "#0EA5E9", "#F59E0B", "#8B5CF6", "#10B981", "#EF4444",
    "#6366F1", "#EC4899", "#14B8A6", "#F97316", "#94A3B8",
]


def _to_native(value):
    """Convierte tipos numpy (escalares, arrays) a nativos de Python para JSON."""
    if isinstance(value, dict):
        return {k: _to_native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_native(v) for v in value]
    if isinstance(value, np.ndarray):
        return _to_native(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def _fig_json(fig) -> dict:
    obj = fig.to_plotly_json()
    layout = obj.get("layout", {})
    layout.pop("template", None)
    return _to_native(obj)


def plot_pca_2d(df_pca: pd.DataFrame, labels, hover_data: pd.DataFrame | None = None) -> dict:
    df = df_pca.reset_index(drop=True).copy()
    df["Cluster"] = np.asarray(labels).astype(str)
    hover_cols = ["Cluster"]
    if hover_data is not None:
        for c in hover_data.columns:
            df[c] = hover_data[c].reset_index(drop=True)
            hover_cols.append(c)
    colores = {str(i): COLORES[i % len(COLORES)] for i in sorted(set(labels))}
    fig = px.scatter(
        df, x="PC1", y="PC2", color="Cluster",
        title="Reducción PCA (2D)",
        hover_data=hover_cols,
        color_discrete_map=colores, template="plotly_white",
    )
    fig.update_traces(marker=dict(size=8, opacity=0.85, line=dict(width=1, color="white")))
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor="rgba(0,0,0,0)")
    return _fig_json(fig)


def plot_pca_3d(df_pca: pd.DataFrame, labels, hover_data: pd.DataFrame | None = None) -> dict:
    df = df_pca.reset_index(drop=True).copy()
    df["Cluster"] = np.asarray(labels).astype(str)
    hover_cols = ["Cluster"]
    if hover_data is not None:
        for c in hover_data.columns:
            df[c] = hover_data[c].reset_index(drop=True)
            hover_cols.append(c)
    colores = {str(i): COLORES[i % len(COLORES)] for i in sorted(set(labels))}
    fig = px.scatter_3d(
        df, x="PC1", y="PC2", z="PC3", color="Cluster",
        title="Visualización PCA (3D)",
        hover_data=hover_cols,
        color_discrete_map=colores, template="plotly_white",
    )
    fig.update_traces(marker=dict(size=5, opacity=0.85))
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    return _fig_json(fig)


def plot_distribucion_departamento_cluster(df_full: pd.DataFrame) -> dict:
    df = (
        df_full.groupby(["Cluster", "departamento"], as_index=False)
        .size()
        .rename(columns={"size": "Cantidad"})
    )
    df["Cluster"] = df["Cluster"].astype(str)
    fig = px.bar(
        df, x="Cluster", y="Cantidad", color="departamento", barmode="stack",
        title="Distribución de Departamentos por Clúster", template="plotly_white",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return _fig_json(fig)


def plot_perfil_clusters(df_features: pd.DataFrame, labels) -> dict:
    df = df_features.copy()
    df["Cluster"] = labels.astype(str)
    medias = df.groupby("Cluster").mean(numeric_only=True).reset_index()
    melt = medias.melt(id_vars="Cluster", var_name="Habilidad", value_name="Promedio")
    fig = px.bar(
        melt, x="Habilidad", y="Promedio", color="Cluster", barmode="group",
        title="Perfil de Clústeres", template="plotly_white",
        color_discrete_sequence=COLORES,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return _fig_json(fig)


def plot_distribucion_departamento(df: pd.DataFrame) -> dict:
    counts = df["departamento"].value_counts().reset_index()
    counts.columns = ["Departamento", "Cantidad"]
    fig = px.pie(
        counts, names="Departamento", values="Cantidad", hole=0.42,
        title="Distribución General por Departamento", template="plotly_white",
        color_discrete_sequence=COLORES,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _fig_json(fig)


def plot_histograma_poligono(serie: pd.Series, titulo="Frecuencias") -> dict:
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    if serie.empty:
        return _fig_json(go.Figure())
    counts, bins = np.histogram(serie, bins="sturges")
    centros = 0.5 * (bins[:-1] + bins[1:])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=centros, y=counts, name="Frecuencia", marker_color="#0EA5E9", opacity=0.7))
    fig.add_trace(go.Scatter(x=centros, y=counts, mode="lines+markers", name="Polígono",
                             line=dict(color="#F59E0B", width=3), marker=dict(size=8)))
    fig.update_layout(title=titulo, template="plotly_white", barmode="overlay",
                      margin=dict(l=30, r=30, t=50, b=30))
    return _fig_json(fig)


def plot_matriz_correlacion(df_features: pd.DataFrame) -> dict:
    corr = df_features.corr(numeric_only=True)
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdBu_r", zmin=-1, zmax=1,
        text=np.round(corr.values, 2), texttemplate="%{text}", hoverongaps=False,
    ))
    fig.update_layout(title="Matriz de Correlación (Pearson)", template="plotly_white",
                      margin=dict(l=30, r=30, t=50, b=30))
    return _fig_json(fig)


def plot_metodo_codo(k_values, inercias) -> dict:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=k_values, y=inercias, mode="lines+markers", name="Inercia (Manual)",
        line=dict(color="#0EA5E9", width=3),
        marker=dict(size=10, color="#F59E0B"),
    ))
    fig.update_layout(
        title="Método del Codo (Inercia Manual vs K)",
        xaxis_title="Número de Clústeres (K)", yaxis_title="Inercia Manual",
        template="plotly_white", margin=dict(l=30, r=30, t=50, b=30),
    )
    return _fig_json(fig)