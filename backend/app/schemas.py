"""Schemas Pydantic para la API (dominio: habilidades blandas)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from .config import SKILLS

SKILL_SET = set(SKILLS)

ALGORITMOS = Literal["kmeans", "dbscan", "gmm"]


# ---------------------------------------------------------------- datos
class DataPage(BaseModel):
    total: int
    page: int
    page_size: int
    records: list[dict[str, Any]]


class DataMeta(BaseModel):
    total: int
    departamentos: list[str]
    puestos: list[str]
    habilidades: list[str]
    antiguedad_min: int | None = None
    antiguedad_max: int | None = None
    db_status: str
    db_message: str | None = None


class SegmentRequest(BaseModel):
    departamento: str | None = None
    puesto: str | None = None
    antiguedad_min: int | None = None
    antiguedad_max: int | None = None
    habilidad: str | None = None
    umbral_min: int | None = None
    umbral_max: int | None = None


class BulkDeleteRequest(BaseModel):
    confirmar: bool = False


# ---------------------------------------------------------------- estadística
class DescriptiveResponse(BaseModel):
    habilidades: list[str]
    filas: list[dict[str, Any]]


class FrequencyResponse(BaseModel):
    habilidad: str
    tabla: list[dict[str, Any]]
    controles: dict[str, Any]


# ---------------------------------------------------------------- clustering
def _validar_skills(v: list[str]) -> list[str]:
    if not (2 <= len(v) <= 4):
        raise ValueError("Selecciona entre 2 y 4 habilidades.")
    invalidos = set(v) - SKILL_SET
    if invalidos:
        raise ValueError(f"Habilidades desconocidas: {', '.join(invalidos)}")
    return sorted(set(v))


class SkillsSelection(BaseModel):
    skills: list[str]

    @field_validator("skills")
    @classmethod
    def _chk(cls, v):
        return _validar_skills(v)


class ElbowRequest(SkillsSelection):
    normalize: bool = True


class AplicarModeloRequest(SkillsSelection):
    algoritmo: ALGORITMOS = "kmeans"
    modelo_id: int | None = None
    nombre_sesion: str = "Sesión de análisis"


class EntrenarBaseRequest(BaseModel):
    nombre_base: str = "base_de_conocimiento"


class ModeloRegistro(BaseModel):
    id: int
    nombre: str
    algoritmo: str
    skills: list[str]
    k_clusters: int | None = None
    inercia: float | None = None
    silueta: float | None = None
    parametros: dict[str, Any]
    timestamp: datetime


class EntrenarModelosResult(BaseModel):
    generados: int
    modelos: list[ModeloRegistro]


class AplicarModeloResponse(BaseModel):
    sesion_id: int
    nombre_sesion: str
    algoritmo: str
    modelo_id: int | None = None
    modelo_nombre: str | None = None
    skills: list[str]
    k_clusters: int | None = None
    silueta: float | None = None
    inercia: float | None = None
    asignados: int
    totales: int
    conteo_clusters: dict[str, int]
    promedio_por_cluster: dict[str, dict[str, float]]
    filas: list[dict[str, Any]]


class ClusterPlotsRequest(BaseModel):
    sesion_id: int
    skills: list[str] | None = None


class ClusterPlotsResponse(BaseModel):
    pca_2d: dict[str, Any]
    pca_3d: dict[str, Any]
    distribucion_departamento: dict[str, Any]
    perfil_clusters: dict[str, Any]
    varianza_explicada: list[float]


# ---------------------------------------------------------------- histórico
class HistoricoResumen(BaseModel):
    id: int
    nombre_sesion: str
    algoritmo: str
    skills: list[str] | None = None
    modelo_id: int | None = None
    k_clusters: int | None
    inercia: float | None
    silueta: float | None
    ruta_modelo: str | None
    timestamp: datetime


class ApplySessionResponse(BaseModel):
    sesion_id: int
    asignaciones: list[dict[str, Any]]