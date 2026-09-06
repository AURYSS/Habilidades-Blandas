"""Modelos ORM (SQLAlchemy 2.0) para el esquema `habilidades`."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import SKILLS
from .database import Base


class Empleado(Base):
    """Registro de un colaborador con su valoración en habilidades blandas."""

    __tablename__ = "empleados"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_empleado: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    departamento: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    puesto: Mapped[str | None] = mapped_column(String(50), nullable=True)
    antiguedad_anos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    for _skill in SKILLS:
        locals()[_skill] = mapped_column(Integer, nullable=True)


class Experimento(Base):
    """Sesión de aplicación de un modelo pre-entrenado sobre datos cargados."""

    __tablename__ = "experimentos"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_sesion: Mapped[str] = mapped_column(String(200), nullable=False)
    algoritmo: Mapped[str] = mapped_column(String(50), nullable=False)
    modelo_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    k_clusters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inercia: Mapped[float | None] = mapped_column(Float, nullable=True)
    silueta: Mapped[float | None] = mapped_column(Float, nullable=True)
    ruta_modelo: Mapped[str | None] = mapped_column(Text, nullable=True)
    features: Mapped[str | None] = mapped_column(Text, nullable=True)
    parametros: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asignaciones: Mapped[list["Asignacion"]] = relationship(
        back_populates="experimento", cascade="all, delete-orphan"
    )


class Asignacion(Base):
    """Asignaciones de clúster generadas por una sesión sobre empleados."""

    __tablename__ = "asignaciones"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experimento_id: Mapped[int] = mapped_column(
        ForeignKey("experimentos.id", ondelete="CASCADE"), index=True
    )
    empleado_id: Mapped[int] = mapped_column(Integer, index=True)
    cluster: Mapped[int | None] = mapped_column(Integer, nullable=True)

    experimento: Mapped[Experimento] = relationship(back_populates="asignaciones")


class Modelo(Base):
    """Catálogo de modelos pre-entrenados (base de conocimiento) seleccionables."""

    __tablename__ = "modelos"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    algoritmo: Mapped[str] = mapped_column(String(20), nullable=False)
    features: Mapped[str] = mapped_column(Text, nullable=False)          # JSON lista de skills
    k_clusters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parametros: Mapped[str | None] = mapped_column(Text, nullable=True)
    inercia: Mapped[float | None] = mapped_column(Float, nullable=True)
    silueta: Mapped[float | None] = mapped_column(Float, nullable=True)
    ruta_modelo: Mapped[str] = mapped_column(Text, nullable=False)
    ruta_scaler: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_base: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)