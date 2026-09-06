"""Acceso a datos: conversiones ORM <-> DataFrame y operaciones canónicas."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import SKILLS
from ..models import Asignacion, Empleado

COLUMNAS = ["id", "id_empleado", "departamento", "puesto", "antiguedad_anos"] + SKILLS


def empleados_a_df(db: Session) -> pd.DataFrame:
    filas = db.execute(select(Empleado).order_by(Empleado.id)).scalars().all()
    df = pd.DataFrame([{c: getattr(r, c) for c in COLUMNAS} for r in filas])
    if df.empty:
        return pd.DataFrame(columns=COLUMNAS)
    return df


def asignaciones_a_df(db: Session, sesion_id: int) -> pd.DataFrame:
    filas = db.execute(
        select(Asignacion).where(Asignacion.experimento_id == sesion_id)
    ).scalars().all()
    return pd.DataFrame(
        [{"id": a.empleado_id, "cluster": a.cluster} for a in filas]
    )


def guardar_asignaciones(db: Session, sesion_id: int, empleado_ids: list[int], labels) -> None:
    for emp_id, cluster in zip(empleado_ids, labels):
        db.add(Asignacion(
            experimento_id=sesion_id,
            empleado_id=int(emp_id),
            cluster=int(cluster),
        ))
    db.commit()