"""Servicio de NLP (sentimiento léxico en español + TF-IDF) sin descargas externas."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

PALABRAS_POSITIVAS = {
    "apasionado", "creativo", "estable", "lider", "lealtad", "ordenado", "curioso",
    "adaptable", "empatica", "profunda", "tranquilidad", "entusiasmo", "honesto",
    "directo", "libertad", "iniciativa", "inteligente", "curiosidad", "alegre",
    "bueno", "practico", "realista", "logica", "sensible", "intuitivo", "ayudar",
    "solidaria", "conexiones", "apasionada", "creativas", "estable", "liderar",
}

PALABRAS_NEGATIVAS = {
    "desespero", "impaciente", "aburro", "rutina", "cambios", "atado", "dogmas",
    "estrictas", "introvertido", "nostalgico", "malo", "triste", "enojo", "miedo",
    "duda", "conflictivo", "pesado", "aburrido", "limite",
}

STOP_WORDS_ES = [
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero",
    "si", "no", "en", "para", "de", "con", "por", "que", "es", "me", "mi",
    "se", "muy", "como", "esta", "sobre", "pregunta", "soy", "lo", "del",
    "al", "las", "mis", "mucho", "suelo", "gusta",
]


def analizar_sentimiento_local(texto) -> float:
    if not isinstance(texto, str) or not texto.strip():
        return 0.0
    palabras = re.findall(r"\b\w+\b", texto.lower())
    if not palabras:
        return 0.0
    pos = sum(1 for p in palabras if p in PALABRAS_POSITIVAS)
    neg = sum(1 for p in palabras if p in PALABRAS_NEGATIVAS)
    total = pos + neg
    if total == 0:
        for p in palabras:
            for w in PALABRAS_POSITIVAS:
                if w in p:
                    pos += 0.5
            for w in PALABRAS_NEGATIVAS:
                if w in p:
                    neg += 0.5
        total = pos + neg
        if total == 0:
            return 0.0
    return (pos - neg) / total


def analizar_sentimientos(df: pd.DataFrame, columnas_abiertas: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for col in columnas_abiertas:
        if col in df.columns:
            out[f"{col}_polaridad"] = df[col].apply(analizar_sentimiento_local)
    out["sentimiento_promedio"] = out.mean(axis=1)
    return out


def obtener_terminos_tfidf(df: pd.DataFrame, columnas_abiertas: list[str], max_features=12) -> list[dict[str, Any]]:
    textos = []
    for col in columnas_abiertas:
        if col in df.columns:
            textos.extend(df[col].dropna().astype(str).tolist())
    if not textos or all(str(t).strip() == "" for t in textos):
        return []
    try:
        vectorizer = TfidfVectorizer(stop_words=STOP_WORDS_ES, max_features=max_features)
        matrix = vectorizer.fit_transform(textos)
        names = vectorizer.get_feature_names_out()
        sums = matrix.sum(axis=0).A1
        pares = sorted(zip(names, sums), key=lambda x: x[1], reverse=True)
        return [{"termino": t, "peso": round(float(p), 4)} for t, p in pares]
    except Exception:
        return []