"""Generador de datasets sintéticos de habilidades blandas.

Justificación de la generación y de las ponderaciones (evidencia académica):

1. Dominio: valoración de habilidades blandas en escala Likert 1-10, una columna
   por habilidad (Comunicación Efectiva, Trabajo en Equipo, Resolución de Conflictos,
   Liderazgo) más contexto organizacional (departamento, puesto, antigüedad).

2. Contexto laboral realista:
   - Cada empleado pertenece a un departamento y tiene un puesto con cierta
     antigüedad. Esto genera mezclas sociodemográficas consistentes.
   - `antiguedad_anos` se genera según el puesto: Junior (0-4), Especialista (2-8),
     Senior (4-12), Lider (8-18), Gerente (10-20). Esto refleja la progresión
     natural de carrera.

3. Ponderaciones por habilidad por departamento (medias sobre la escala 1-10):
   - Comunicación Efectiva: alta en RRHH y Ventas (negociación/interacción directa);
     media en Mercadotecnia; menor en Operaciones (tareas técnicas internas).
   - Trabajo en Equipo: alto en TI y RRHH (metodologías colaborativas); menor en
     Operaciones donde el trabajo es más individualizado.
   - Resolución de Conflictos: alto en RRHH y Operaciones (gestión de crisis);
     medio en el resto.
   - Liderazgo: no depende del departamento sino de la antigüedad y el puesto
     (se escala con los años de experiencia), con mayor varianza en TI.

4. Estructura de varianza:
   - Cada puntaje = clip(round(N(media_departamento + ajuste_puesto/antiguedad, sigma)), 1, 10).
   - Ajuste por puesto: Junior -1, Senior 0, Lider +1, Gerente +2.
   - Se introduce un factor común latente (nivel general de competencias) para que
     las cuatro habilidades queden correlacionadas positivamente (r ~ 0.3-0.6),
     tal como ocurre en instrumentos psicométricos reales.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import DEPARTAMENTOS, ID_EMPLEADO_PREFIX, PUESTOS, SKILLS

# Media por departamento por habilidad (escala 1-10).
MEDIAS_DEPARTAMENTO: dict[str, dict[str, float]] = {
    "TI":               {"Comunicacion_Efectiva": 6.2, "Trabajo_Equipo": 7.6, "Resolucion_Conflictos": 6.5, "Liderazgo": 5.8},
    "Ventas":           {"Comunicacion_Efectiva": 8.2, "Trabajo_Equipo": 6.4, "Resolucion_Conflictos": 6.6, "Liderazgo": 6.2},
    "Recursos_Humanos": {"Comunicacion_Efectiva": 8.4, "Trabajo_Equipo": 7.4, "Resolucion_Conflictos": 7.8, "Liderazgo": 6.0},
    "Operaciones":      {"Comunicacion_Efectiva": 5.4, "Trabajo_Equipo": 5.6, "Resolucion_Conflictos": 7.0, "Liderazgo": 5.2},
    "Finanzas":         {"Comunicacion_Efectiva": 6.6, "Trabajo_Equipo": 6.0, "Resolucion_Conflictos": 6.0, "Liderazgo": 5.6},
    "Marketing":        {"Comunicacion_Efectiva": 7.6, "Trabajo_Equipo": 6.8, "Resolucion_Conflictos": 6.2, "Liderazgo": 6.4},
}

# Sigma por habilidad (dispersión del instrumento).
SIGMA = {"Comunicacion_Efectiva": 1.4, "Trabajo_Equipo": 1.4, "Resolucion_Conflictos": 1.5, "Liderazgo": 1.6}

# Ajuste por puesto (progresión de carrera).
AJUSTE_PUESTO = {"Junior": -1.0, "Especialista": -0.5, "Senior": 0.0, "Lider": 1.0, "Gerente": 2.0}

# Rango de antigüedad (años) por puesto.
ANTIGUEDAD_POR_PUESTO = {"Junior": (0, 4), "Especialista": (2, 8), "Senior": (4, 12), "Lider": (8, 18), "Gerente": (10, 20)}

# Pesos de departamentos y puestos en la empresa simulada.
P_DEPARTAMENTOS = [0.12, 0.10, 0.24, 0.14, 0.22, 0.18]
P_PUESTOS = [0.35, 0.20, 0.25, 0.12, 0.08]


def _clip_int(x: float, lo: int = 1, hi: int = 10) -> int:
    return int(max(lo, min(hi, round(x))))


def generar_dataset(n_registros: int = 2500, seed: int | None = 42) -> pd.DataFrame:
    """Genera un dataset sintético de habilidades blandas reproducible."""
    rng = np.random.default_rng(seed)
    filas = []
    for i in range(1, n_registros + 1):
        depto = str(rng.choice(DEPARTAMENTOS, p=P_DEPARTAMENTOS))
        puesto = str(rng.choice(PUESTOS, p=P_PUESTOS))
        a_min, a_max = ANTIGUEDAD_POR_PUESTO[puesto]
        antiguedad = int(rng.integers(a_min, a_max + 1))

        # Factor latente común: nivel general de competencias socioemocionales.
        factor_comun = float(rng.normal(0.0, 1.0))
        reg = {
            "id_empleado": f"{ID_EMPLEADO_PREFIX}_{i:04d}",
            "departamento": depto,
            "puesto": puesto,
            "antiguedad_anos": antiguedad,
        }
        for skill in SKILLS:
            media = MEDIAS_DEPARTAMENTO[depto][skill] + AJUSTE_PUESTO[puesto]
            if skill == "Liderazgo":
                media = media + min(3.0, antiguedad * 0.12)
            valor = media + 0.45 * factor_comun + float(rng.normal(0.0, SIGMA[skill]))
            reg[skill] = _clip_int(valor)
        filas.append(reg)
    return pd.DataFrame(filas)