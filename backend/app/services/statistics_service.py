"""Servicio de estadística descriptiva con algoritmos propios (rúbrica académica)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _limpiar(valores):
    return [x for x in valores if x is not None and not (isinstance(x, float) and math.isnan(x))]


def promedio_manual(valores) -> float:
    limpios = _limpiar(valores)
    if not limpios:
        return 0.0
    return sum(float(x) for x in limpios) / len(limpios)


def moda_manual(valores):
    limpios = _limpiar(valores)
    if not limpios:
        return None
    frec = {}
    for x in limpios:
        frec[x] = frec.get(x, 0) + 1
    max_freq = -1
    moda = None
    for val, f in frec.items():
        if f > max_freq:
            max_freq, moda = f, val
    return moda


def varianza_manual(valores) -> float:
    limpios = _limpiar(valores)
    n = len(limpios)
    if n < 2:
        return 0.0
    p = promedio_manual(limpios)
    return sum((float(x) - p) ** 2 for x in limpios) / (n - 1)


def desviacion_estandar_manual(valores) -> float:
    return varianza_manual(valores) ** 0.5


def mediana_manual(valores):
    limpios = sorted(_limpiar(valores))
    n = len(limpios)
    if n == 0:
        return None
    mid = n // 2
    if n % 2 == 0:
        return (float(limpios[mid - 1]) + float(limpios[mid])) / 2.0
    return float(limpios[mid])


def cv_manual(valores) -> float:
    media = promedio_manual(valores)
    if media == 0:
        return 0.0
    return (desviacion_estandar_manual(valores) / float(media)) * 100.0


def minimo_manual(valores):
    limpios = _limpiar(valores)
    return min(limpios) if limpios else None


def maximo_manual(valores):
    limpios = _limpiar(valores)
    return max(limpios) if limpios else None


def rango_manual(valores) -> float:
    mn, mx = minimo_manual(valores), maximo_manual(valores)
    if mn is None or mx is None:
        return 0.0
    return float(mx) - float(mn)


def sturges(n: int) -> float:
    if n <= 0:
        return 0.0
    return 1 + 3.322 * math.log10(n)


def amplitud_manual(rango: float, k: float) -> float:
    if k <= 0:
        return 0.0
    return float(rango) / float(k)


def normalizacion_min_max_manual(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df_out = df.copy()
    for col in cols:
        valores = df[col].dropna().tolist()
        if not valores:
            continue
        vmin, vmax = min(valores), max(valores)
        rango = vmax - vmin
        if rango == 0:
            df_out[col] = 0.0
        else:
            df_out[col] = df[col].apply(
                lambda x: (x - vmin) / rango if pd.notnull(x) else 0.0
            )
    return df_out


def filas_descriptivas(df: pd.DataFrame, cols: list[str]) -> list[dict[str, Any]]:
    """Estadísticos propios por columna (una fila por habilidad)."""
    filas = []
    for col in cols:
        if col not in df.columns:
            continue
        valores = df[col].tolist()
        n = len(_limpiar(valores))
        rango = rango_manual(valores)
        k = max(1, int(round(sturges(n)))) if n else 1
        filas.append({
            "dimension": col,
            "promedio": round(promedio_manual(valores), 4),
            "moda": moda_manual(valores),
            "mediana": mediana_manual(valores),
            "varianza": round(varianza_manual(valores), 4),
            "desviacion": round(desviacion_estandar_manual(valores), 4),
            "cv": round(cv_manual(valores), 4),
            "minimo": minimo_manual(valores),
            "maximo": maximo_manual(valores),
            "rango": round(rango, 4),
            "sturges": round(k, 4),
            "amplitud": round(amplitud_manual(rango, k), 4),
        })
    return filas


def tabla_frecuencias_manual(valores) -> list[list[dict[str, Any]]]:
    """Genera la tabla de frecuencias escolar (tabla cruda, sin redondeo final)."""
    limpios = _limpiar(valores)
    n = len(limpios)
    if n == 0:
        return []
    vmin = min(limpios)
    vmax = max(limpios)
    rango = float(vmax) - float(vmin)
    k = max(1, int(round(sturges(n))))
    amplitud = amplitud_manual(rango, k)

    filas = []
    li = float(vmin)
    freq_acum = 0
    for i in range(k):
        ls = li + amplitud
        f = 0
        for v in limpios:
            if i == k - 1:
                if li <= v <= ls:
                    f += 1
            else:
                if li <= v < ls:
                    f += 1
        marca = (li + ls) / 2.0
        fr = f / n if n else 0
        freq_acum += f
        rango_str = (
            f"[{round(li, 2)}, {round(ls, 2)}]"
            if i == k - 1
            else f"[{round(li, 2)}, {round(ls, 2)})"
        )
        filas.append(
            {
                "Clase": rango_str,
                "Marca de Clase": round(marca, 4),
                "f": f,
                "Fr": round(fr, 4),
                "%": round(fr * 100, 2),
                "F": freq_acum,
            }
        )
        li = ls

    filas.append({"Clase": "Total", "Marca de Clase": "-", "f": n, "Fr": 1.0, "%": 100.0, "F": "-"})
    return filas