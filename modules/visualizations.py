import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_pca_2d(df_pca, labels, hover_data=None):
    """
    Genera un gráfico interactivo Plotly 2D con los 2 primeros componentes principales.
    """
    df = df_pca.copy()
    df["Cluster"] = labels.astype(str)
    
    if hover_data is not None:
        for col in hover_data.columns:
            df[col] = hover_data[col]
            
    fig = px.scatter(
        df, x="PC1", y="PC2", color="Cluster",
        title="Reducción de Dimensionalidad PCA (2D)",
        hover_data=hover_data.columns.tolist() if hover_data is not None else None,
        color_discrete_sequence=px.colors.qualitative.Bold,
        template="plotly_white"
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig

def plot_pca_3d(df_pca, labels, hover_data=None):
    """
    Genera un gráfico interactivo Plotly 3D con los 3 primeros componentes principales.
    """
    df = df_pca.copy()
    df["Cluster"] = labels.astype(str)
    
    if hover_data is not None:
        for col in hover_data.columns:
            df[col] = hover_data[col]
            
    fig = px.scatter_3d(
        df, x="PC1", y="PC2", z="PC3", color="Cluster",
        title="Visualización de Clústeres PCA (3D)",
        hover_data=hover_data.columns.tolist() if hover_data is not None else None,
        color_discrete_sequence=px.colors.qualitative.Bold,
        template="plotly_white"
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig

def plot_distribucion_signos_cluster(df_full):
    """
    Muestra la distribución de los signos zodiacales dentro de cada clúster para validación.
    """
    # Agrupar por Cluster y Signo
    df_grouped = df_full.groupby(["Cluster", "signo"]).size().reset_index(name="Cantidad")
    df_grouped["Cluster"] = df_grouped["Cluster"].astype(str)
    
    fig = px.bar(
        df_grouped, x="Cluster", y="Cantidad", color="signo",
        title="Distribución de Signos Zodiacales por Clúster",
        barmode="stack",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    return fig

def plot_perfil_clusters(df_features, labels):
    """
    Muestra el promedio de características para cada clúster (gráfico de radar o barras agrupadas).
    """
    df = df_features.copy()
    df["Cluster"] = labels.astype(str)
    
    # Calcular promedio por clúster
    df_mean = df.groupby("Cluster").mean().reset_index()
    
    # Reestructurar para Plotly
    df_melt = df_mean.melt(id_vars="Cluster", var_name="Pregunta", value_name="Promedio")
    
    fig = px.bar(
        df_melt, x="Pregunta", y="Promedio", color="Cluster",
        title="Perfil de Clústeres: Respuestas Promedio",
        barmode="group",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    return fig

def plot_distribucion_signo(df):
    """
    Muestra la distribución general de signos zodiacales en el dataset.
    """
    counts = df["signo"].value_counts().reset_index()
    counts.columns = ["Signo", "Cantidad"]
    
    fig = px.pie(
        counts, names="Signo", values="Cantidad",
        title="Distribución General por Signo Zodiacal",
        template="plotly_white",
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def plot_histograma_poligono(serie, titulo="Histograma y Polígono de Frecuencias"):
    """
    Genera un histograma junto con su polígono de frecuencias.
    """
    serie_clean = serie.dropna()
    if len(serie_clean) == 0:
        return go.Figure()
        
    counts, bins = np.histogram(serie_clean, bins='sturges')
    bins_centers = 0.5 * (bins[:-1] + bins[1:])
    
    fig = go.Figure()
    
    # Histograma
    fig.add_trace(go.Bar(
        x=bins_centers,
        y=counts,
        name='Frecuencia',
        marker_color='#297E91',
        opacity=0.7
    ))
    
    # Polígono de frecuencias
    fig.add_trace(go.Scatter(
        x=bins_centers,
        y=counts,
        mode='lines+markers',
        name='Polígono',
        line=dict(color='#5CB2C4', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=titulo,
        template="plotly_white",
        xaxis_title="Valor",
        yaxis_title="Frecuencia",
        barmode='overlay',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def plot_matriz_correlacion(df_features):
    """
    Genera un Heatmap con la correlación de Pearson entre las preguntas numéricas.
    """
    corr = df_features.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.index,
        colorscale='RdBu_r',
        zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        hoverongaps = False
    ))
    
    fig.update_layout(
        title="Matriz de Correlación entre Preguntas Likert",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

def plot_metodo_codo(k_values, inercias):
    """
    Genera la gráfica del Método del Codo para encontrar el número óptimo de clústeres.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=k_values,
        y=inercias,
        mode='lines+markers',
        name='Inercia (Manual)',
        line=dict(color='#5CB2C4', width=3),
        marker=dict(size=10, color='#297E91')
    ))
    
    fig.update_layout(
        title="Método del Codo (Inercia Manual vs K)",
        xaxis_title="Número de Clústeres (K)",
        yaxis_title="Inercia (Manual)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    return fig

