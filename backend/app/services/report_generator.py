"""Generador de reportes PDF profesionales (fpdf2)."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
LOGO_PATH = BASE_DIR / "static" / "logo.png"


class SoftSkillsReportPDF(FPDF):
    def __init__(self, logo_path: str | None = None):
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, 10, 8, 25)
            except Exception:
                pass
        self.set_font("helvetica", "B", 20)
        self.set_text_color(14, 116, 144)
        self.cell(30)
        self.cell(0, 10, "Soft Skills AI - Reporte Analítico", align="L")
        self.ln(8)
        self.set_font("helvetica", "I", 12)
        self.set_text_color(100, 100, 100)
        self.cell(30)
        self.cell(0, 10, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="L")
        self.ln(20)
        self.set_draw_color(14, 116, 144)
        self.set_line_width(0.5)
        self.line(10, 35, 200, 35)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Pipeline de Aprendizaje No Supervisado', align="C")


def _interpretar_silueta(sil: float) -> str:
    if sil >= 0.5:
        return (
            f"El coeficiente de Silhouette de {sil:.4f} es sobresaliente: la cohesión "
            "intra-clúster supera ampliamente la separación inter-clúster. Los grupos "
            "son homogéneos y bien delimitados, lo que permite inferencias poblacionales "
            "de alta confianza."
        )
    if sil >= 0.25:
        return (
            f"El Silhouette de {sil:.4f} es aceptable: existe estructura de agrupamiento "
            "real con cierta superposición natural en las fronteras, típico en datos "
            "psicométricos donde el comportamiento humano es multifactorial."
        )
    return (
        f"El Silhouette de {sil:.4f} revela alto solapamiento: el fenómeno se comporta "
        "como un espectro continuo. Las conclusiones deben tratarse como tendencias "
        "macroscópicas y no reglas deterministas."
    )


def _render_tabla(pdf: FPDF, titulo: str, columnas: list[str], filas: list[list], col_widths: list[float] | None = None):
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, titulo, ln=True)
    pdf.ln(2)
    if col_widths is None:
        total = 190.0
        col_widths = [total / len(columnas)] * len(columnas)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(14, 116, 144)
    pdf.set_text_color(255, 255, 255)
    for c, w in zip(columnas, col_widths):
        pdf.cell(w, 9, str(c)[:16], border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for fila in filas:
        fila = ["" if v is None else v for v in fila]
        max_height = 0
        for c, w in zip(fila, col_widths):
            max_height = max(max_height, 9)
        if pdf.get_y() + max_height + 4 > 275:
            pdf.add_page()
        pdf.set_fill_color(*((245, 245, 245) if fill else (255, 255, 255)))
        for c, w in zip(fila, col_widths):
            pdf.cell(w, max_height, str(c)[:16], border=1, fill=True, align="C")
        pdf.ln()
        fill = not fill
    pdf.ln(6)


def generar_pdf_report(
    nombre_sesion: str,
    algoritmo: str,
    metrics: dict,
    cluster_counts: dict,
    graphs_bytes: list[bytes] | None = None,
    skills: list[str] | None = None,
    modelo_nombre: str | None = None,
    promedio_por_cluster: dict | None = None,
    tablas: list[dict] | None = None,
    logo_path: str | None = None,
) -> bytes:
    pdf = SoftSkillsReportPDF(logo_path=logo_path or str(LOGO_PATH))
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "1. Configuración del Análisis", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Sesión: {nombre_sesion}", ln=True)
    pdf.cell(0, 8, f"Algoritmo: {algoritmo.upper()}", ln=True)
    if modelo_nombre:
        pdf.cell(0, 8, f"Modelo seleccionado: {modelo_nombre}", ln=True)
    if skills:
        pdf.cell(0, 8, "Habilidades: " + ", ".join(skills), ln=True)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "2. Métricas de Desempeño", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)

    sil = metrics.get("Silhouette Score (Manual)") or metrics.get("Silhouette Score") or 0.0
    pdf.cell(0, 8, f"- Silhouette Score: {float(sil):.4f}", ln=True)
    if "Inertia (Manual)" in metrics:
        pdf.cell(0, 8, f"- Inercia (Manual): {metrics['Inertia (Manual)']:.2f}", ln=True)
    if "Noise points" in metrics:
        pdf.cell(0, 8, f"- Puntos de Ruido: {metrics['Noise points']}", ln=True)
    if "BIC" in metrics:
        pdf.cell(0, 8, f"- BIC: {metrics['BIC']:.2f}", ln=True)

    pdf.ln(2)
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, _interpretar_silueta(float(sil)))
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "3. Distribución de Población por Clúster", ln=True)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_fill_color(14, 116, 144)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 10, "Clúster", border=1, fill=True, align="C")
    pdf.cell(60, 10, "Individuos", border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for clust, count in sorted(cluster_counts.items(), key=lambda x: str(x[0])):
        pdf.set_fill_color(*((245, 245, 245) if fill else (255, 255, 255)))
        pdf.cell(60, 10, f"Clúster {clust}", border=1, fill=True, align="C")
        pdf.cell(60, 10, str(count), border=1, fill=True, align="C")
        pdf.ln()
        fill = not fill
    pdf.ln(5)

    if promedio_por_cluster and skills:
        columnas = ["Clúster"] + [s[:14] for s in skills]
        col_widths = [36.0] + [154.0 / max(1, len(skills))] * len(skills)
        filas = []
        for clust in sorted(promedio_por_cluster.keys()):
            med = promedio_por_cluster[str(clust)]
            filas.append([f"Clúster {clust}"] + [f"{med.get(s, 0.0):.2f}" for s in skills])
        _render_tabla(pdf, "3.1 Perfil Promedio por Habilidad", columnas, filas, col_widths)

    if graphs_bytes:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(74, 14, 78)
        pdf.cell(0, 10, "4. Visualizaciones Analíticas", ln=True)
        pdf.ln(2)
        for img in graphs_bytes:
            if pdf.get_y() > 200:
                pdf.add_page()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(img)
                tmp_name = tmp.name
            try:
                pdf.image(tmp_name, x=10, w=190)
                pdf.ln(8)
            finally:
                os.remove(tmp_name)

    if tablas:
        pdf.add_page()
        for t in tablas:
            _render_tabla(pdf, t.get("titulo", "Detalle"), t.get("columnas", []),
                          t.get("filas", []), t.get("col_widths"))

    pdf.add_page()
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 6,
        "Nota: Reporte generado automáticamente por el Pipeline de Soft Skills AI con "
        "algoritmos estadísticos propios y procesamiento no supervisado.")
    return bytes(pdf.output(dest="S"))


def generar_pdf_base_stats(
    nombre_sesion: str,
    habilidades: list[str],
    descripciones: list[dict],
    frecuencias: dict[str, list[dict]],
    controles: dict[str, dict],
    filtros: dict | None = None,
    logo_path: str | None = None,
) -> bytes:
    """PDF de estadística base (estadísticos propios) sobre los datos filtrados."""
    pdf = SoftSkillsReportPDF(logo_path=logo_path or str(LOGO_PATH))
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "1. Configuración", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Conjunto: {nombre_sesion}", ln=True)
    pdf.cell(0, 8, "Habilidades seleccionadas: " + ", ".join(habilidades), ln=True)
    if filtros:
        texto = "; ".join(f"{k}: {v}" for k, v in filtros.items() if v)
        if texto:
            pdf.cell(0, 8, "Filtros: " + texto, ln=True)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "2. Estadísticos Descriptivos Propios", ln=True)
    pdf.ln(2)

    columnas = ["Habilidad", "Prom", "Moda", "Mediana", "Var", "Desv", "CV", "Min", "Max", "Rango", "Sturges", "Amplitud"]
    col_widths = [34, 14, 14, 16, 16, 14, 14, 12, 12, 14, 16, 14]
    filas = []
    for d in descripciones:
        filas.append([
            d.get("dimension", ""),
            d.get("promedio", 0), d.get("moda", ""), d.get("mediana", ""),
            d.get("varianza", 0), d.get("desviacion", 0), d.get("cv", 0),
            d.get("minimo", ""), d.get("maximo", ""), d.get("rango", 0),
            d.get("sturges", 0), d.get("amplitud", 0),
        ])
    _render_tabla(pdf, "Métricas por Habilidad", columnas, filas, col_widths)

    pdf.add_page()
    for h in habilidades:
        tabla = frecuencias.get(h, [])
        ctl = controles.get(h, {})
        pdf.set_font("helvetica", "B", 15)
        pdf.set_text_color(74, 14, 78)
        pdf.cell(0, 10, f"3. Tabla de Frecuencias - {h}", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, (
            f"n={ctl.get('n', 0)} | Prom={ctl.get('promedio', 0):.3f} | Var={ctl.get('varianza', 0):.3f} "
            f"| Sturges={ctl.get('k_utilizado', 0)} | Amplitud={ctl.get('amplitud', 0):.3f}"
        ), ln=True)
        pdf.ln(2)
        if tabla:
            cols_t = list(tabla[0].keys())
            col_w = [190.0 / len(cols_t)] * len(cols_t)
            _render_tabla(pdf, "", cols_t, [[fila.get(c, "") for c in cols_t] for fila in tabla], col_w)
        pdf.ln(4)

    return bytes(pdf.output(dest="S"))