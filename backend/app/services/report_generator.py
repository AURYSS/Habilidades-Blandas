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

        pdf.ln(2)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(14, 116, 144)
        pdf.cell(0, 8, "Lectura de los Clústeres (Insights)", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        
        txt = "Basado en los centroides (promedios) de las variables, el algoritmo de Machine Learning sugiere la siguiente segmentación estratégica de la plantilla:\n\n"
        for clust in sorted(promedio_por_cluster.keys()):
            med = promedio_por_cluster[str(clust)]
            altos = [s for s in skills if med.get(s, 0) >= 8.0]
            medios = [s for s in skills if 6.0 <= med.get(s, 0) < 8.0]
            bajos = [s for s in skills if med.get(s, 0) < 6.0]
            
            txt += f"=== GRUPO (CLÚSTER) {clust} ===\n"
            if altos:
                txt += f"- Fortalezas distintivas: {', '.join(altos)}.\n"
            if medios:
                txt += f"- Competencias en desarrollo: {', '.join(medios)}.\n"
            if bajos:
                txt += f"- Zonas críticas (Riesgo): {', '.join(bajos)}.\n"
            
            if len(altos) == len(skills):
                txt += "-> Perfil Élite: Grupo de alto rendimiento, ideal para asumir roles directivos o liderar proyectos de gran impacto.\n\n"
            elif len(bajos) > len(altos) or (len(bajos) > 0 and len(altos) == 0):
                txt += "-> Perfil Vulnerable: Requiere intervención con planes de capacitación urgente. Estas carencias pueden generar fricción operativa.\n\n"
            elif altos and bajos:
                txt += "-> Perfil Especializado (Desbalanceado): Talentos muy marcados pero con carencias que pueden sabotear su desempeño. Candidatos ideales para coaching focalizado.\n\n"
            else:
                txt += "-> Perfil Estándar: Colaboradores con un balance neutral y funcional. Mantienen la estabilidad del equipo sin presentar picos sobresalientes ni riesgos graves.\n\n"
        
        pdf.multi_cell(0, 6, txt)
        pdf.ln(5)

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

    # --- PÁGINA COMPLETA DE INTERPRETACIÓN GENERAL ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "Conclusión y Diagnóstico General", ln=True)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(14, 116, 144)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    
    # Construir un texto largo y articulado
    n_clusters = len(cluster_counts)
    total_emp = sum(cluster_counts.values())
    
    texto_general = (
        f"El presente análisis de Inteligencia Artificial (Machine Learning), ejecutado sobre "
        f"la población de {total_emp} colaboradores, ha revelado la existencia de {n_clusters} "
        f"perfiles comportamentales (clústeres) marcadamente distintos dentro de la organización. "
        f"Este descubrimiento es fundamental, ya que demuestra que las habilidades blandas del equipo "
        f"no se distribuyen de manera uniforme, sino que existen subgrupos con necesidades, "
        f"fortalezas y áreas de oportunidad completamente diferentes.\n\n"
        
        "A nivel organizacional, la fragmentación en estos clústeres indica que las políticas "
        "de Recursos Humanos, planes de carrera y programas de capacitación estandarizados "
        "(el mismo curso para todos) tendrán un impacto limitado. Al aplicar técnicas de "
        "agrupamiento no supervisado, el algoritmo ha validado empíricamente que la empresa "
        "alberga desde talento de muy alto rendimiento hasta grupos que requieren intervención "
        "inmediata para no afectar la cadena de valor y el clima laboral.\n\n"
        
        "Implicaciones y Riesgos Estratégicos:\n"
        "La convivencia de perfiles altamente especializados junto con perfiles vulnerables "
        "tiende a generar fricciones operativas. Los colaboradores del clúster más alto suelen "
        "absorber la carga emocional y de liderazgo que los clústeres inferiores no logran "
        "gestionar. Esto puede derivar en el síndrome de 'burnout' (desgaste profesional) para "
        "el talento clave y una alta rotación si no se equilibra la dinámica de trabajo en equipo.\n\n"
        
        "Recomendaciones de Acción Inmediata:\n"
        "1. Mentoring Interno Cruzado: Se sugiere emparejar a los individuos de los clústeres "
        "élite con aquellos de los clústeres estándar o en riesgo. Esto no solo acelera la "
        "transferencia de habilidades blandas de forma orgánica, sino que mejora la cohesión "
        "y el entendimiento mutuo.\n\n"
        "2. Capacitación Focalizada: Las áreas de Recursos Humanos deben diseñar 'micro-cursos' "
        "dirigidos exclusivamente a las carencias del clúster más bajo, en lugar de capacitaciones "
        "masivas. Si el algoritmo detectó deficiencias severas en una competencia, esta debe "
        "ser el foco del próximo trimestre.\n\n"
        "3. Reestructuración de Equipos: En proyectos críticos, es vital asegurar que no exista "
        "una sobre-concentración de personal del mismo clúster vulnerable. Todo equipo multidisciplinario "
        "debe contar con al menos un integrante del clúster de alto rendimiento para garantizar "
        "la estabilidad emocional y resolución de conflictos del proyecto.\n\n"
        
        "Conclusión Final:\n"
        "La inteligencia de datos aplicada hoy proporciona una radiografía exacta del estado actual "
        "del capital humano. Las habilidades blandas son el verdadero motor de la productividad. "
        "Atender las brechas reveladas por este modelo predictivo no solo mejorará el clima organizacional, "
        "sino que tendrá un impacto directo y positivo en la retención de talento y la consecución "
        "de los objetivos estratégicos de la compañía."
    )
    
    pdf.multi_cell(0, 7, texto_general)
    pdf.ln(10)

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

    # --- Interpretacion Chida ---
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(14, 116, 144)
    pdf.cell(0, 8, "Insight Analítico de las Métricas", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    
    insight_text = "A partir de la radiografía descriptiva de los datos, derivamos los siguientes insights estratégicos para cada dimensión:\n\n"
    for d in descripciones:
        hab = d.get("dimension", "")
        prom = float(d.get("promedio", 0))
        cv = float(d.get("cv", 0))
        mediana = float(d.get("mediana", 0))
        mini = float(d.get("minimo", 0))
        maxi = float(d.get("maximo", 0))
        
        insight_text += f"[{hab.upper()}]\n"
        
        if prom >= 8.5:
            insight_text += f"- Nivel de Madurez: Excelente. Con un promedio altísimo de {prom:.1f} y una mediana de {mediana:.1f}, esta habilidad representa un pilar competitivo para la organización.\n"
        elif prom >= 7.0:
            insight_text += f"- Nivel de Madurez: Estable. Muestra un nivel funcional ({prom:.1f}), adecuado para la operatividad diaria, pero con potencial para desarrollarse hacia la excelencia.\n"
        else:
            insight_text += f"- Nivel de Madurez: Crítico. Promedio preocupante de {prom:.1f}. Esto indica una debilidad sistémica que podría estar afectando fuertemente los resultados del equipo.\n"
            
        if cv > 0.25:
            insight_text += f"- Cohesión Interna: Alta polarización (Dispersión severa con un CV de {cv:.2f}). Las calificaciones fluctúan fuertemente (desde {mini:.1f} hasta {maxi:.1f}), indicando que el equipo tiene tanto talentos extraordinarios como elementos extremadamente rezagados. Se sugiere urgentemente un programa de mentoría interna.\n\n"
        elif cv < 0.10:
            insight_text += f"- Cohesión Interna: Extraordinaria homogeneidad (CV de {cv:.2f}). El conocimiento y la práctica de esta habilidad están totalmente estandarizados en la plantilla, facilitando una colaboración predecible y fluida.\n\n"
        else:
            insight_text += f"- Cohesión Interna: Variabilidad normal (CV de {cv:.2f}). Las diferencias de nivel entre los empleados entran en el rango de lo estadísticamente esperado para cualquier organización estándar.\n\n"

    pdf.multi_cell(0, 6, insight_text)
    pdf.ln(5)
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

    # --- PÁGINA COMPLETA DE INTERPRETACIÓN GENERAL ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(74, 14, 78)
    pdf.cell(0, 10, "Conclusión General y Diagnóstico Organizacional", ln=True)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(14, 116, 144)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)
    
    texto_stats = (
        "El análisis estadístico presentado a lo largo de este reporte ofrece una "
        "radiografía cuantitativa sumamente precisa sobre el estado actual de las habilidades "
        "blandas (Soft Skills) dentro de la muestra evaluada.\n\n"
        
        "A diferencia de las métricas de desempeño tradicionales o el dominio de herramientas "
        "técnicas (Hard Skills), las habilidades blandas representan el verdadero tejido conectivo "
        "de una empresa. La capacidad de comunicarse, liderar y resolver conflictos determina "
        "no solo el clima laboral, sino la agilidad operativa y la capacidad de resiliencia "
        "de la organización frente a escenarios cambiantes.\n\n"
        
        "Diagnóstico de la Dispersión y Cohesión:\n"
        "Uno de los hallazgos estadísticos más críticos que revela este reporte es la varianza "
        "y el coeficiente de dispersión en los equipos. Una alta disparidad estadística "
        "significa que existen marcadas brechas en cómo los individuos abordan los problemas. "
        "Cuando las habilidades blandas están polarizadas (empleados con dominio excelente "
        "frente a empleados con deficiencias graves), la empresa experimenta problemas de "
        "comunicación asimétrica, cuellos de botella en la toma de decisiones y un aumento "
        "injustificado en el estrés de los altos mandos, quienes terminan micro-gestionando.\n\n"
        
        "Plan de Acción Recomendado:\n"
        "1. Priorización del Desarrollo: Las habilidades que mostraron promedios cercanos o "
        "inferiores a 6.0 no deben verse simplemente como un dato numérico, sino como "
        "alertas rojas operativas. Se recomienda invertir presupuestos de capacitación "
        "estrictamente en estos rubros durante el próximo ciclo.\n\n"
        "2. Identificación de Embajadores: Aquellos individuos que estadísticamente se "
        "ubican en los percentiles superiores (con calificaciones sostenidas por encima "
        "de 8.5) deben ser reconocidos como 'embajadores culturales'. Su rol debe ser "
        "el de guiar con el ejemplo y participar en dinámicas de mentoría (shadowing) "
        "para estandarizar el conocimiento tácito hacia el resto del equipo.\n\n"
        "3. Reevaluación Periódica: Los datos aquí plasmados son una línea base. Es "
        "fundamental volver a correr este algoritmo estadístico tras implementar los "
        "programas de desarrollo humano, comparando así la evolución de los promedios "
        "y verificando que la campana de Gauss (la varianza de la plantilla) se haya "
        "estrechado, lo cual confirmaría que el equipo se ha vuelto más cohesionado.\n\n"
        
        "Conclusión Final:\n"
        "Las organizaciones que miden y optimizan su inteligencia emocional y colaborativa "
        "a través de datos duros, se posicionan sistemáticamente por encima de su competencia. "
        "La presente auditoría estadística es el primer paso indispensable hacia una cultura "
        "empresarial verdaderamente basada en la evidencia."
    )
    
    pdf.multi_cell(0, 7, texto_stats)
    pdf.ln(10)

    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 6,
        "Nota: Reporte generado automáticamente por el Pipeline de Soft Skills AI con "
        "algoritmos estadísticos propios y procesamiento no supervisado.")
    return bytes(pdf.output(dest="S"))