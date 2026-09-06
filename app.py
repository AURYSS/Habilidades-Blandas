import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import joblib
import plotly.express as px
import plotly.graph_objects as go
import importlib

# Importar módulos locales
from modules.data_loader import load_and_validate_csv
from modules.database import (
    init_db,
    insertar_encuestas,
    obtener_todas_las_encuestas,
    limpiar_base_de_datos
)
from modules.statistics import (
    calcular_promedio_manual,
    calcular_moda_manual,
    calcular_varianza_manual,
    calcular_desviacion_estandar_manual,
    normalizacion_min_max_manual,
    calcular_promedios_dimensiones,
    calcular_minimo_manual,
    calcular_maximo_manual,
    calcular_rango_manual,
    calcular_k_sturges,
    calcular_amplitud_manual,
    calcular_mediana_manual,
    calcular_cv_manual,
    generar_tabla_frecuencias_manual
)
from modules.clustering import train_clustering_model, apply_pca_reduction, save_model, MODELS_DIR
from modules.nlp import analizar_sentimientos_dataset, obtener_terminos_frecuentes_tfidf
from modules.visualizations import (
    plot_pca_2d,
    plot_pca_3d,
    plot_distribucion_signos_cluster,
    plot_perfil_clusters,
    plot_distribucion_signo,
    plot_matriz_correlacion,
    plot_histograma_poligono,
    plot_metodo_codo
)
from modules.report_generator import generate_pdf_report
from generate_massive_data import generar_dataset
import modules.history
importlib.reload(modules.history)
from modules.history import log_model_training, get_model_history

# Mapeo robusto global de signos a sus elementos correspondientes
SIGN_TO_ELEMENT = {
    "Aries": "Fuego", "Leo": "Fuego", "Sagitario": "Fuego", "Fuego": "Fuego",
    "Tauro": "Tierra", "Virgo": "Tierra", "Capricornio": "Tierra", "Tierra": "Tierra",
    "Géminis": "Aire", "Libra": "Aire", "Acuario": "Aire", "Aire": "Aire",
    "Cáncer": "Agua", "Escorpio": "Agua", "Piscis": "Agua", "Agua": "Agua"
}

# Configuración de página de Streamlit
st.set_page_config(
    page_title="AI.Studio - Soft Skills Pipeline",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilización premium personalizada (Soft Skills Cute Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&family=Poppins:wght@300;400;600;800&display=swap');
    
    /* Decoración sutil de fondo */
    .stApp {
        background-image: radial-gradient(#FBE4B5, rgba(251,228,181,.3) 2px, transparent 4px),
                          radial-gradient(#5CB2C4, rgba(92,178,196,.15) 1px, transparent 3px);
        background-size: 400px 400px, 250px 250px;
        background-position: 0 0, 40px 60px;
    }

    h1, h2, h3, .main-title, .section-header {
        font-family: 'Poppins', sans-serif !important;
        color: #1A4D5B;
    }

    p, span, div, li, td, th {
        font-family: 'Nunito', sans-serif;
    }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1A4D5B, #297E91);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-shadow: 0px 2px 4px rgba(26, 77, 91, 0.2);
    }
    .sub-title {
        color: #297E91;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1A4D5B;
        border-bottom: 2px dashed #5CB2C4;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Panel de Glassmorphism Claro */
    .metric-card {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(12px) !important;
        border: 2px solid #5CB2C4 !important;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px 0 rgba(41, 126, 145, 0.15);
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px 0 rgba(41, 126, 145, 0.3);
        border: 2px solid #297E91 !important;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #1A4D5B, #297E91);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #1A4D5B;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
        font-weight: 700;
    }
    
    /* Botones Cutes pero con nuevos colores */
    .stButton > button {
        background: linear-gradient(135deg, #297E91 0%, #5CB2C4 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(41, 126, 145, 0.4) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1A4D5B 0%, #297E91 100%) !important;
        transform: scale(1.05);
        box-shadow: 0 6px 15px rgba(26, 77, 91, 0.6) !important;
    }

    /* Tablas y dataframes */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* INNOVACIÓN: Ocultar sidebar por completo */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    
    /* Hacer que el header de Streamlit desaparezca para un look más limpio */
    header { background: transparent !important; }
    
    /* Estilizar radio buttons horizontales como Pills/Pestañas modernas */
    div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: center;
        margin-bottom: 20px;
    }
    div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #5CB2C4;
        padding: 12px 24px;
        border-radius: 50px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(92, 178, 196, 0.1);
    }
    div[role="radiogroup"] > label:hover {
        background: #5CB2C4;
        border-color: #5CB2C4;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(92, 178, 196, 0.3);
    }
    div[role="radiogroup"] > label:hover p {
        color: white !important;
    }
    div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #1A4D5B, #297E91);
        border-color: #1A4D5B;
        box-shadow: 0 8px 15px rgba(26, 77, 91, 0.4);
    }
    div[role="radiogroup"] > label[data-checked="true"] p {
        color: white !important;
        font-weight: 800;
    }
    /* Ocultar el círculo nativo del radio button */
    div[role="radiogroup"] > label span[data-baseweb="radio"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estados de sesión
if "df_raw" not in st.session_state:
    st.session_state.df_raw = None
if "df_filtered" not in st.session_state:
    st.session_state.df_filtered = None
if "df_results" not in st.session_state:
    st.session_state.df_results = None
if "model_metrics" not in st.session_state:
    st.session_state.model_metrics = None
if "last_model_path" not in st.session_state:
    st.session_state.last_model_path = None
if "last_algorithm" not in st.session_state:
    st.session_state.last_algorithm = None
if "features_used" not in st.session_state:
    st.session_state.features_used = []

# Intentar cargar datos de PostgreSQL si existen al inicio
try:
    df_db = obtener_todas_las_encuestas()
    if not df_db.empty and st.session_state.df_raw is None:
        st.session_state.df_raw = df_db
        st.session_state.df_filtered = df_db.copy()
    db_status = "🟢 En Línea"
    reg_count = len(df_db) if not df_db.empty else 0
except Exception as e:
    db_status = "🔴 Error de Conexión"
    reg_count = 0

# Título y Subtítulo - Top Bar Moderno
col_title, col_status = st.columns([3, 1])

with col_title:
    st.markdown('<div class="main-title">🌱 Soft Skills Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Unidad IV: Análisis No Supervisado</div>', unsafe_allow_html=True)

with col_status:
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); padding: 15px; border-radius: 15px; border: 2px solid #5CB2C4; text-align: right; box-shadow: 0 4px 6px rgba(41, 126, 145, 0.1);">
        <p style="margin: 0; font-size: 0.9rem; color: #297E91; text-transform: uppercase; letter-spacing: 1px;"><b>Estado Sistema</b></p>
        <p style="margin: 0; font-size: 1rem; color: #1A4D5B; font-weight: 700;">{db_status}</p>
        <p style="margin: 0; font-size: 0.9rem; color: #1A4D5B;"><b>{reg_count}</b> Registros</p>
    </div>
    """, unsafe_allow_html=True)

st.write("") # Espaciador visual

# Navegación horizontal moderna tipo "Pills"
pantalla = st.radio(
    "Navegación",
    [
        "📥 Importar Dataset",
        "👁️ Explorador de Registros",
        "🔍 Segmentación Avanzada",
        "📊 Análisis Descriptivo",
        "🧠 Motor de Machine Learning",
        "💬 Insights Cualitativos",
        "💾 Exportar Reportes",
        "🕒 Registro de Experimentos"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")
# ==============================================================================
# PANTALLA 1: INGESTA DE DATOS
# ==============================================================================
if pantalla == "📥 Importar Dataset":
    st.markdown('<div class="section-header">1. Ingesta y Persistencia</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Suba el archivo CSV con las respuestas Likert (`p1`-`p12`) y respuestas abiertas (`p1a`-`p12a`).")
        uploaded_file = st.file_uploader("Subir dataset en formato .csv", type=["csv"])
        
        if uploaded_file is not None:
            df, msg = load_and_validate_csv(uploaded_file)
            if df is not None:
                st.success(f"¡Carga en memoria exitosa! {msg}")
                if st.button("Guardar e Ingestar", use_container_width=True):
                    try:
                        cant = insertar_encuestas(df)
                        st.success(f"¡Persistencia exitosa! Se insertaron {cant} registros en la base de datos local.")
                        # Recargar de BD para mantener el ID de la BD
                        st.session_state.df_raw = obtener_todas_las_encuestas()
                        st.session_state.df_filtered = st.session_state.df_raw.copy()
                    except Exception as e:
                        if isinstance(e, UnicodeDecodeError):
                            st.error("Error de conexión: El servidor PostgreSQL local rechazó la conexión. Por favor verifica que tu contraseña del usuario 'postgres' sea correcta y que hayas creado la base de datos vacía llamada 'zodiac' en pgAdmin.")
                        else:
                            st.error(f"Error de conexión a Postgres: {e}")
            else:
                st.error(f"Error de Validación: {msg}")
                
    with col2:
        st.markdown("### Acciones Demo / Sintéticas")
        
        # Generador de datos sintéticos a medida
        n_synthetic = st.number_input("Cantidad de registros sintéticos a generar:", min_value=1, max_value=50000, value=5000, step=500)
        
        if st.button(f"Generar {n_synthetic} registros sintéticos", use_container_width=True):
            with st.spinner(f"Generando {n_synthetic} registros..."):
                df_demo = generar_dataset(n_synthetic)
                try:
                    cant = insertar_encuestas(df_demo)
                    st.success(f"¡Éxito! {cant} registros insertados en Postgres.")
                    st.session_state.df_raw = obtener_todas_las_encuestas()
                    st.session_state.df_filtered = st.session_state.df_raw.copy()
                except Exception as e:
                    if isinstance(e, UnicodeDecodeError):
                        st.error("Error de conexión: El servidor PostgreSQL local rechazó la conexión. Verifica tu contraseña y que la base de datos 'zodiac' exista.")
                    else:
                        st.error(f"Error de conexión a Postgres: {e}")
                
        if st.button("Vaciar Tabla 'encuestas' ", use_container_width=True):
            try:
                limpiar_base_de_datos()
                st.session_state.df_raw = None
                st.session_state.df_filtered = None
                st.session_state.df_results = None
                st.success("Tabla vaciada con éxito.")
            except Exception as e:
                st.error(f"Error de base de datos: {e}")
                
    if st.session_state.df_raw is not None:
        st.markdown("### Estado de la Base de Datos")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total en Postgres", f"{len(st.session_state.df_raw)} registros")
        with c2:
            st.metric("Columnas Likert", "p1 - p15")
        with c3:
            st.metric("Columnas Abiertas", "p1a - p15a")

# ==============================================================================
# PANTALLA 2: VISUALIZAR DATOS
# ==============================================================================
elif pantalla == "👁️ Explorador de Registros":
    st.markdown('<div class="section-header">2. Consulta Tabular</div>', unsafe_allow_html=True)
    
    # Intentar recargar desde la BD
    try:
        st.session_state.df_raw = obtener_todas_las_encuestas()
    except Exception as e:
        st.error(f"No se pudo consultar PostgreSQL: {e}")
        
    if st.session_state.df_raw is None or st.session_state.df_raw.empty:
        st.warning("La base de datos está vacía. Ingeste datos en la pestaña '1. Ingesta de Datos'.")
    else:
        st.write("Vista de los registros:")
        
        records_per_page = st.selectbox("Registros por página", [10, 25, 50, 100], index=0)
        total_len = len(st.session_state.df_raw)
        pages = max(1, int(np.ceil(total_len / records_per_page)))
        page_num = st.number_input("Página", min_value=1, max_value=pages, value=1)
        
        start_idx = (page_num - 1) * records_per_page
        end_idx = min(start_idx + records_per_page, total_len)
        
        st.write(f"Mostrando registros del {start_idx + 1} al {end_idx} de un total de {total_len}.")
        st.dataframe(st.session_state.df_raw.iloc[start_idx:end_idx], use_container_width=True)

# ==============================================================================
# PANTALLA 3: FILTROS Y EXPORTACIÓN
# ==============================================================================
elif pantalla == "🔍 Segmentación Avanzada":
    st.markdown('<div class="section-header">3. Segmentación y Filtros de Información</div>', unsafe_allow_html=True)
    
    try:
        st.session_state.df_raw = obtener_todas_las_encuestas()
    except:
        pass
        
    if st.session_state.df_raw is None or st.session_state.df_raw.empty:
        st.warning("La base de datos está vacía. Cargue datos antes de filtrar.")
    else:
        df = st.session_state.df_raw.copy()
        
        col1, col2 = st.columns(2)
        with col1:
            min_age = int(df["edad"].min())
            max_age = int(df["edad"].max())
            age_range = st.slider("Rango de Edad:", min_age, max_age, (min_age, max_age))
            
            generos_disponibles = ["Todos"] + df["genero"].unique().tolist()
            genero_selected = st.selectbox("Seleccione Género:", generos_disponibles)
            
        with col2:
            signos_disponibles = ["Todos"] + df["signo"].unique().tolist()
            signo_selected = st.selectbox("Seleccione Signo Zodiacal:", signos_disponibles)
            
        df_filtered = df[(df["edad"] >= age_range[0]) & (df["edad"] <= age_range[1])]
        
        if genero_selected != "Todos":
            df_filtered = df_filtered[df_filtered["genero"] == genero_selected]
            
        if signo_selected != "Todos":
            df_filtered = df_filtered[df_filtered["signo"] == signo_selected]
            
        st.session_state.df_filtered = df_filtered
        
        st.markdown(f"#### Resultados Filtrados: {len(df_filtered)} registros encontrados.")
        st.dataframe(df_filtered, use_container_width=True)
        
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar Datos Filtrados (CSV)",
            data=csv_data,
            file_name="datos_filtrados_zodiac.csv",
            mime="text/csv",
            use_container_width=True
        )

# ==============================================================================
# PANTALLA 4: ESTADÍSTICAS BÁSICAS
# ==============================================================================
elif pantalla == "📊 Análisis Descriptivo":
    st.markdown('<div class="section-header">4. Estadísticas Descriptivas (Algoritmos Propios)</div>', unsafe_allow_html=True)
    
    if st.session_state.df_filtered is None or len(st.session_state.df_filtered) == 0:
        st.warning("No hay registros filtrados o la base de datos está vacía.")
    else:
        df = st.session_state.df_filtered.copy()
        
        st.markdown("### Métricas de Rúbrica de Evaluación por Dimensión (Elemento)")
        st.write("Calculados usando **funciones manuales programadas paso a paso** (Rúbrica de evaluación):")
        
        # Obtener puntuaciones promedio por dimensión (Fuego, Tierra, Aire, Agua)
        df_dimensiones = calcular_promedios_dimensiones(df)
        
        stat_rows = []
        for dim_name in df_dimensiones.columns:
            val_col = df_dimensiones[dim_name].tolist()
            
            promedio = calcular_promedio_manual(val_col)
            moda = calcular_moda_manual(val_col)
            mediana = calcular_mediana_manual(val_col)
            varianza = calcular_varianza_manual(val_col)
            std_dev = calcular_desviacion_estandar_manual(val_col)
            cv = calcular_cv_manual(val_col)
            
            minimo = calcular_minimo_manual(val_col)
            maximo = calcular_maximo_manual(val_col)
            rango = calcular_rango_manual(val_col)
            k_sturges = calcular_k_sturges(len(val_col))
            amplitud = calcular_amplitud_manual(rango, k_sturges)
            
            stat_rows.append({
                "Elemento/Dimensión": dim_name,
                "Promedio": round(promedio, 3) if promedio is not None else None,
                "Moda": round(moda, 3) if isinstance(moda, float) else moda,
                "Mediana (Me)": round(mediana, 3) if mediana is not None else None,
                "Varianza": round(varianza, 3) if varianza is not None else None,
                "Desviación Est.": round(std_dev, 3) if std_dev is not None else None,
                "CV (%)": round(cv, 2) if cv is not None else None,
                "Rango": round(rango, 3) if rango is not None else None,
                "Amplitud": round(amplitud, 3) if amplitud is not None else None,
                "K (Sturges)": round(k_sturges, 3)
            })
            
        st.table(pd.DataFrame(stat_rows))
        
        st.markdown("---")
        st.markdown("### 📊 Análisis de Frecuencias por Dimensión (Escolar)")
        st.write("Selecciona una dimensión para desplegar su **Tabla de Distribución de Frecuencias** y métricas manuales de control.")
        
        dim_seleccionada = st.selectbox("Seleccione el elemento a visualizar detalladamente:", df_dimensiones.columns)
        
        # Filtramos la población basándonos en el elemento seleccionado
        df_poblacion = df.copy()
        if "Fuego" in dim_seleccionada:
            df_poblacion = df_poblacion[df_poblacion["signo"].isin(["Aries", "Leo", "Sagitario"])]
        elif "Tierra" in dim_seleccionada:
            df_poblacion = df_poblacion[df_poblacion["signo"].isin(["Tauro", "Virgo", "Capricornio"])]
        elif "Aire" in dim_seleccionada:
            df_poblacion = df_poblacion[df_poblacion["signo"].isin(["Géminis", "Libra", "Acuario"])]
        elif "Agua" in dim_seleccionada:
            df_poblacion = df_poblacion[df_poblacion["signo"].isin(["Cáncer", "Escorpio", "Piscis"])]
            
        # Generar los promedios SOLO para esta población filtrada
        df_dim_poblacion = calcular_promedios_dimensiones(df_poblacion)
        
        if df_dim_poblacion.empty:
            st.warning("No hay suficientes datos de estos signos para generar la tabla.")
            val_sel = []
        else:
            val_sel = df_dim_poblacion[dim_seleccionada].tolist()
        
        col_resumen, col_tabla = st.columns([1, 2])
        
        with col_resumen:
            st.markdown("#### Métricas de Control")
            rango_sel = calcular_rango_manual(val_sel)
            k_sel = calcular_k_sturges(len(val_sel))
            k_sel_int = int(round(k_sel)) if k_sel > 0 else 1
            a_sel = calcular_amplitud_manual(rango_sel, k_sel_int)
            
            st.write(f"**Rango (R):** {calcular_maximo_manual(val_sel):.2f} - {calcular_minimo_manual(val_sel):.2f} = **{rango_sel:.2f}**")
            st.write(f"**K (Intervalo):** 1 + 3.322 * log({len(val_sel)}) = **{k_sel:.3f}** (Usamos {k_sel_int})")
            st.write(f"**A (Amplitud):** {rango_sel:.2f} / {k_sel_int} = **{a_sel:.3f}**")
            st.markdown("---")
            st.write(f"**Media (X̄):** {calcular_promedio_manual(val_sel):.2f}")
            moda_val = calcular_moda_manual(val_sel)
            st.write(f"**Mo (Moda):** {moda_val:.2f}" if isinstance(moda_val, float) else f"**Mo (Moda):** {moda_val}")
            st.write(f"**Me (Mediana):** {calcular_mediana_manual(val_sel):.2f}")
            st.markdown("---")
            st.write(f"**Varianza (S²):** {calcular_varianza_manual(val_sel):.3f}")
            st.write(f"**DesStd (S):** {calcular_desviacion_estandar_manual(val_sel):.3f}")
            st.write(f"**CV:** {calcular_cv_manual(val_sel):.2f}%")
            
        with col_tabla:
            st.markdown("#### Tabla de Distribución de Frecuencias")
            df_freq = generar_tabla_frecuencias_manual(val_sel)
            st.dataframe(df_freq, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Visualización de Frecuencias y Distribuciones")
        
        col_viz1, col_viz2 = st.columns(2)
        
        with col_viz1:
            st.markdown("#### Histograma y Polígono de Frecuencias")
            fig_hist = plot_histograma_poligono(df_dimensiones[dim_seleccionada], titulo=f"Histograma: {dim_seleccionada}")
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with col_viz2:
            st.markdown("#### Porcentajes por Signo Zodiacal")
            st.plotly_chart(plot_distribucion_signo(df), use_container_width=True)

# ==============================================================================
# PANTALLA 5: ENTRENAR MODELO
# ==============================================================================
elif pantalla == "🧠 Motor de Machine Learning":
    st.markdown('<div class="section-header">5. Configuración y Entrenamiento del Modelo</div>', unsafe_allow_html=True)
    
    try:
        st.session_state.df_raw = obtener_todas_las_encuestas()
    except:
        pass
        
    if st.session_state.df_raw is None or st.session_state.df_raw.empty:
        st.warning("La base de datos está vacía. Ingeste datos primero.")
    else:
        df = st.session_state.df_raw.copy()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Configuración de Algoritmo")
            algo = st.selectbox("Algoritmo de Agrupamiento:", ["K-Means"])
            
            params = {}
            params["n_clusters"] = st.slider("Número de Clústeres (K) por Elemento:", 2, 8, 3)
                
            normalize = st.checkbox("Normalizar Características mediante Min-Max Manual", value=True)
            
            st.markdown("---")
            st.markdown("### Analizador del Método del Codo")
            elem_codo = st.selectbox("Elemento para analizar (Codo):", ["Fuego", "Agua", "Aire", "Tierra"])
            if st.button("Visualizar Método del Codo", use_container_width=True):
                with st.spinner(f"Calculando inercias manuales para {elem_codo} (K=2 a K=8)..."):
                    # Mapear signos a elementos
                    df["elemento_temp"] = df["signo"].map(SIGN_TO_ELEMENT)
                    df_elem = df[df["elemento_temp"] == elem_codo].copy()
                    
                    elementos_vars = {
                        "Fuego": ["p1", "p2", "p3"],
                        "Agua": ["p4", "p5", "p6"],
                        "Aire": ["p7", "p8", "p9"],
                        "Tierra": ["p10", "p11", "p12"]
                    }
                    features = elementos_vars[elem_codo]
                    df_feat = df_elem[features].copy()
                    if normalize:
                        df_feat = normalizacion_min_max_manual(df_feat, features)
                    
                    k_values = list(range(2, 9))
                    inercias = []
                    for k in k_values:
                        _, _, metrics = train_clustering_model(df_feat, "kmeans", {"n_clusters": k})
                        inercias.append(metrics["Inertia (Manual)"])
                        
                    st.plotly_chart(plot_metodo_codo(k_values, inercias), use_container_width=True)

            
        with col2:
            st.markdown("### Arquitectura de Submodelos Segmentados")
            st.info("💡 **Solución al Sesgo de Nulos**: Se entrenarán 4 submodelos independientes en paralelo (uno por cada elemento). Cada modelo usará únicamente las 3 preguntas correspondientes a su elemento (Fuego: p1-p3, Agua: p4-p6, Aire: p7-p9, Tierra: p10-p12), eliminando la necesidad de imputar valores en las preguntas que el usuario no contestó.")
            nombre_sesion = st.text_input("Nombre de esta sesión (Ej. Prueba K=3):", value="Mi Modelo")
            
        if st.button("Iniciar Aprendizaje de IA", use_container_width=True):
            if not nombre_sesion.strip():
                st.error("Por favor, ingrese un nombre para la sesión.")
                st.stop()
                
            from datetime import datetime
            session_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            algo_key = "kmeans"
            
            elementos_vars = {
                "Fuego": ["p1", "p2", "p3"],
                "Agua": ["p4", "p5", "p6"],
                "Aire": ["p7", "p8", "p9"],
                "Tierra": ["p10", "p11", "p12"]
            }
            
            all_metrics = {}
            df_res = df.copy()
            df_res["Cluster"] = -1  # Inicializar
            modelos_paths = {}
            
            # Mapear signos a elementos para filtrar
            df["elemento_temp"] = df["signo"].map(SIGN_TO_ELEMENT)
            for elem, features in elementos_vars.items():
                df_elem_indices = df[df["elemento_temp"] == elem].index
                df_elem = df.loc[df_elem_indices].copy()
                
                if len(df_elem) == 0:
                    continue
                    
                df_feat = df_elem[features].copy()
                if normalize:
                    df_feat = normalizacion_min_max_manual(df_feat, features)
                    
                model, labels, metrics = train_clustering_model(df_feat, algo_key, params)
                
                # Asignar etiquetas a la fila correspondiente
                df_res.loc[df_elem_indices, "Cluster"] = labels
                
                # Guardar modelo
                saved_path = save_model(model, algo_key, elem)
                modelos_paths[elem] = saved_path
                all_metrics[elem] = metrics
                
                # Guardar en el historial
                k_val = params.get("n_clusters", 3)
                log_model_training(nombre_sesion, algo_key, elem, k_val, metrics.get("Inertia (Manual)"), metrics.get("Silhouette Score (Manual)"), saved_path, timestamp=session_timestamp)
                
            st.session_state.last_algorithm = algo_key
            st.session_state.df_results = df_res
            st.session_state.model_metrics = all_metrics
            st.session_state.last_model_path = list(modelos_paths.values())[0] if modelos_paths else None
            st.session_state.modelos_paths_dict = modelos_paths
            
            st.success(f"¡Los 4 submodelos de {algo} fueron entrenados y guardados con éxito!")
            
            st.markdown("### Métricas de Evaluación por Elemento")
            c1, c2, c3, c4 = st.columns(4)
            cols_elem = [c1, c2, c3, c4]
            for idx, (elem, metrics) in enumerate(all_metrics.items()):
                with cols_elem[idx]:
                    st.markdown(f"**Elemento {elem}**")
                    st.metric("Silhouette Score (Manual)", f"{metrics.get('Silhouette Score (Manual)', 0.0):.4f}")
                    if "Inertia (Manual)" in metrics:
                        st.metric("Inercia (Manual)", f"{metrics.get('Inertia (Manual)', 0.0):.2f}")

# ==============================================================================
# PANTALLA 6: RESULTADOS DE IA & NLP
# ==============================================================================
elif pantalla == "💬 Insights Cualitativos":
    st.markdown('<div class="section-header">6. Resultados y Análisis Cualitativo NLP</div>', unsafe_allow_html=True)
    
    if st.session_state.df_results is None:
        st.warning("No hay resultados de entrenamiento. Por favor entrene un modelo primero.")
    else:
        df_res = st.session_state.df_results.copy()
        
        # Selector de Elemento para Visualizar
        st.markdown("### Visualización por Elemento Astrológico")
        elem_visualizar = st.selectbox(
            "Seleccione el elemento para visualizar su agrupamiento y análisis independiente:",
            ["Fuego", "Agua", "Aire", "Tierra"]
        )
        
        # Filtrar datos de este elemento robustamente
        df_res["elemento_temp"] = df_res["signo"].map(SIGN_TO_ELEMENT)
        df_elem = df_res[df_res["elemento_temp"] == elem_visualizar].copy()
        
        if df_elem.empty:
            st.warning(f"No hay registros cargados para el elemento {elem_visualizar}.")
        else:
            elementos_vars = {
                "Fuego": ["p1", "p2", "p3"],
                "Agua": ["p4", "p5", "p6"],
                "Aire": ["p7", "p8", "p9"],
                "Tierra": ["p10", "p11", "p12"]
            }
            features = elementos_vars[elem_visualizar]
            
            df_feat = df_elem[features].copy()
            df_pca, variance = apply_pca_reduction(df_feat, n_components=3)
            
            st.write(f"Visualización de los sub-clústeres del elemento **{elem_visualizar}** entrenados en base a: `{features}`")
            st.write(f"Varianza explicada acumulada (PC1 + PC2 + PC3): **{sum(variance)*100:.2f}%**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_pca_2d(df_pca, df_elem["Cluster"], hover_data=df_elem[["id", "edad", "genero"]]), use_container_width=True)
            with col2:
                st.plotly_chart(plot_pca_3d(df_pca, df_elem["Cluster"], hover_data=df_elem[["id", "edad", "genero"]]), use_container_width=True)
                
            # NLP Cualitativo específico del elemento
            st.markdown(f"### Análisis Cualitativo NLP: Respuestas de {elem_visualizar}")
            
            # Columnas abiertas específicas para el elemento
            open_cols_mapping = {
                "Fuego": ["p1a", "p2a", "p3a"],
                "Agua": ["p4a", "p5a", "p6a"],
                "Aire": ["p7a", "p8a", "p9a"],
                "Tierra": ["p10a", "p11a", "p12a"]
            }
            nlp_cols = open_cols_mapping[elem_visualizar]
            
            df_sent = analizar_sentimientos_dataset(df_elem, nlp_cols)
            df_elem["Polaridad_Sentimiento_Promedio"] = df_sent["sentimiento_promedio"]
            
            st.write("Polaridad promedio de sentimiento por participante (1.0 = Positivo, -1.0 = Negativo):")
            st.dataframe(df_elem[["id", "Cluster", "Polaridad_Sentimiento_Promedio"] + nlp_cols].head(15), use_container_width=True)
            
            st.write(f"Términos más recurrentes descubiertos en las respuestas abiertas de **{elem_visualizar}** (TF-IDF):")
            df_tfidf = obtener_terminos_frecuentes_tfidf(df_elem, nlp_cols)
            st.dataframe(df_tfidf, use_container_width=True)

# ==============================================================================
# PANTALLA 7: ZONA DE DESCARGAS
# ==============================================================================
elif pantalla == "💾 Exportar Reportes":
    st.markdown('<div class="section-header">7. Exportación e Informes</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Descargar Resultados (Excel / CSV)")
        if st.session_state.df_results is not None:
            df_res = st.session_state.df_results
            
            tipo_descarga = st.radio("Seleccione el formato y tipo de datos:", 
                                     ["CSV Completo", "Excel Cuantitativo (Numérico)", "Excel Cualitativo (Texto/Categorías)"])
            
            if tipo_descarga == "CSV Completo":
                csv_res = df_res.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar Dataset Completo (CSV)",
                    data=csv_res,
                    file_name="resultados_zodiacal_clustering.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if "Cuantitativo" in tipo_descarga:
                        cols_cuant = ["id", "edad"] + [f"p{i}" for i in range(1, 16)]
                        if "Cluster" in df_res.columns:
                            cols_cuant.append("Cluster")
                        cols_export = [c for c in cols_cuant if c in df_res.columns]
                        df_res[cols_export].to_excel(writer, index=False, sheet_name="Cuantitativo")
                        file_name = "resultados_cuantitativos.xlsx"
                    else:
                        cols_cual = ["id", "genero", "signo"] + [f"p{i}a" for i in range(1, 16)]
                        if "Polaridad_Sentimiento_Promedio" in df_res.columns:
                            cols_cual.append("Polaridad_Sentimiento_Promedio")
                        if "Cluster" in df_res.columns:
                            cols_cual.append("Cluster")
                        cols_export = [c for c in cols_cual if c in df_res.columns]
                        df_res[cols_export].to_excel(writer, index=False, sheet_name="Cualitativo")
                        file_name = "resultados_cualitativos.xlsx"
                        
                excel_data = output.getvalue()
                st.download_button(
                    label=f"Descargar {tipo_descarga} (Excel)",
                    data=excel_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.info("No se han generado resultados aún.")
            
        st.markdown("### Descargar Modelo de Entrenamiento (.pkl)")
        if "modelos_paths_dict" in st.session_state and st.session_state.modelos_paths_dict:
            # Selector de elemento para descargar el modelo
            elem_descargar = st.selectbox(
                "Seleccione el modelo del elemento a descargar (.pkl):",
                list(st.session_state.modelos_paths_dict.keys())
            )
            path_modelo = st.session_state.modelos_paths_dict[elem_descargar]
            if os.path.exists(path_modelo):
                with open(path_modelo, "rb") as f:
                    model_bytes = f.read()
                st.download_button(
                    label=f"Descargar Modelo de {elem_descargar} (.pkl)",
                    data=model_bytes,
                    file_name=os.path.basename(path_modelo),
                    mime="application/octet-stream",
                    use_container_width=True
                )
        else:
            st.info("No hay ningún modelo entrenado guardado.")
            
    with col2:
        st.markdown("### Reporte Estadístico Ejecutivo")
        st.write("Descarga un informe profesional en PDF listo para presentar.")

        st.write("Descarga un informe profesional en PDF con análisis detallado.")
        
        if st.session_state.df_results is not None:
            df = st.session_state.df_results
            metrics = st.session_state.model_metrics
            algo = st.session_state.last_algorithm
            
            cluster_counts = df["Cluster"].value_counts().to_dict()
            
            # Generar gráficos en PNG usando Kaleido para inyectar en el PDF
            graphs_bytes = []
            try:
                features = ["p1", "p2", "p3"] # Fuego por defecto
                df_feat = df[df["signo"].map(SIGN_TO_ELEMENT) == "Fuego"][features].copy()
                if not df_feat.empty:
                    df_pca, _ = apply_pca_reduction(df_feat, n_components=2)
                    labels = df[df["signo"].map(SIGN_TO_ELEMENT) == "Fuego"]["Cluster"]
                    
                    fig1 = plot_pca_2d(df_pca, labels)
                    graphs_bytes.append(fig1.to_image(format="png", width=800, height=600))
            except Exception as e:
                st.warning("⚠️ Nota: Las gráficas de dispersión no se incluirán en el PDF generado debido a la falta de Google Chrome / dependencias de Kaleido en este entorno local. El reporte con tablas de métricas y frecuencias se descargará con normalidad.")
            
            # Obtener el primer set de métricas si es un diccionario
            pdf_metrics = list(metrics.values())[0] if isinstance(metrics, dict) else metrics
            
            pdf_bytes = bytes(generate_pdf_report(algo, pdf_metrics, cluster_counts, graphs_bytes))
            
            st.download_button(
                label="📥 Descargar Reporte (PDF)",
                data=pdf_bytes,
                file_name="reporte_ejecutivo_zodiacal.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("Entrene el modelo para poder visualizar el reporte.")

# ==============================================================================
# PANTALLA 8: HISTORIAL DE MODELOS
# ==============================================================================
elif pantalla == "🕒 Registro de Experimentos":
    st.markdown('<div class="section-header">8. Historial de Modelos y Aprendizaje Continuo</div>', unsafe_allow_html=True)
    st.write("Aquí puedes visualizar el registro de todos los modelos entrenados previamente.")
    
    try:
        df_hist = get_model_history()
        if df_hist.empty:
            st.info("Aún no hay modelos entrenados en el historial.")
        else:
            # Ordenar por fecha descendente
            df_hist = df_hist.sort_values(by="Timestamp", ascending=False)
            st.dataframe(df_hist, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### ♻️ Reutilizar Modelo del Historial")
            st.write("Selecciona una sesión de entrenamiento por su nombre para cargar la IA con el conocimiento de ese momento.")
            
            if "Nombre_Sesion" not in df_hist.columns:
                df_hist["Nombre_Sesion"] = "Sesión Antigüa"
                
            df_hist["Nombre_Sesion"] = df_hist["Nombre_Sesion"].fillna("Sin Nombre")
            df_hist["Opcion_Dropdown"] = df_hist["Nombre_Sesion"].astype(str) + " (" + df_hist["Timestamp"].astype(str) + ")"
            sesiones_unicas = [s for s in df_hist["Opcion_Dropdown"].unique().tolist() if str(s) != "nan" and pd.notnull(s)]
            sesion_seleccionada = st.selectbox("Seleccione la Sesión de Entrenamiento:", sesiones_unicas)
            
            if st.button("Cargar e Inyectar en Sistema", use_container_width=True):
                with st.spinner("Cargando y despertando a la IA..."):
                    df_sesion = df_hist[df_hist["Opcion_Dropdown"] == sesion_seleccionada]
                    
                    if st.session_state.df_raw is None or st.session_state.df_raw.empty:
                        st.error("No hay datos en la base de datos para predecir. El historial está disponible, pero debes 'Ingestar Datos' (Pantalla 1) antes de aplicar un modelo a los encuestados.")
                    else:
                        df_res = st.session_state.df_raw.copy()
                        df_res["Cluster"] = -1
                        all_metrics = {}
                        modelos_paths = {}
                        
                        df_res["elemento_temp"] = df_res["signo"].map(SIGN_TO_ELEMENT)
                        elementos_vars = {
                            "Fuego": ["p1", "p2", "p3"],
                            "Agua": ["p4", "p5", "p6"],
                            "Aire": ["p7", "p8", "p9"],
                            "Tierra": ["p10", "p11", "p12"]
                        }
                        
                        algo_name = df_sesion.iloc[0]["Algoritmo"]
                        
                        for _, row in df_sesion.iterrows():
                            elem = row["Elemento"]
                            ruta = row["Ruta_Modelo"]
                            
                            if os.path.exists(ruta):
                                modelo = joblib.load(ruta)
                                features = elementos_vars[elem]
                                df_elem_indices = df_res[df_res["elemento_temp"] == elem].index
                                df_elem = df_res.loc[df_elem_indices].copy()
                                
                                if len(df_elem) > 0:
                                    df_feat = df_elem[features].copy()
                                    df_feat = df_feat.fillna(3)
                                    # Predecir con el modelo cargado
                                    labels = modelo.predict(df_feat.values)
                                    df_res.loc[df_elem_indices, "Cluster"] = labels
                                    
                                modelos_paths[elem] = ruta
                                all_metrics[elem] = {
                                    "Inertia (Manual)": row.get("Inercia", 0.0),
                                    "Silhouette Score (Manual)": row.get("Silueta", 0.0)
                                }
                        
                        if modelos_paths:
                            st.session_state.last_algorithm = algo_name
                            st.session_state.df_results = df_res
                            st.session_state.model_metrics = all_metrics
                            st.session_state.last_model_path = list(modelos_paths.values())[0]
                            st.session_state.modelos_paths_dict = modelos_paths
                            st.success(f"¡Modelos de la sesión {sesion_seleccionada} recargados con éxito! Ve a la Pantalla 6 para ver los resultados.")
                        else:
                            st.error("No se encontraron los archivos .pkl asociados a esta sesión.")
            
            st.markdown("---")
            # Botón para descargar el CSV de historial
            csv_hist = df_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Historial CSV",
                data=csv_hist,
                file_name="historial_modelos_zodiac.csv",
                mime="text/csv",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"No se pudo cargar el historial: {e}")
