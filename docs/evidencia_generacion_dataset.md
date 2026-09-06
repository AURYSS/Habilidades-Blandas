# Evidencia de generación del dataset sintético de habilidades blandas

**Carrera:** TIC · Ingeniería en Desarrollo y Gestión de Software
**Materia:** Extracción de Conocimientos en Base de Datos
**Unidad:** IV · Análisis No Supervisado (Modo Recuperación 2)
**Hito:** Algoritmo de creación de datos aleatorios y justificación de ponderaciones

El generador vive en `backend/app/services/synthetic.py` y produce un `DataFrame`
con la columna estructural idéntica al dataset real `dataset_habilidades_blandas.csv`:
`id_empleado`, `departamento`, `puesto`, `antiguedad_anos` y una columna Likert (1-10)
por cada habilidad (Comunicación Efectiva, Trabajo en Equipo, Resolución de Conflictos,
Liderazgo).

## 1. Cómo miden las empresas las habilidades blandas (base de la valoración)

Las empresas evalúan competencias socioemocionales con **escalas Likert** (1 a 5
o 1 a 10) aplicadas por autoevaluación, evaluación de jefe inmediato o
evaluación 360°. Cada habilidad se operacionaliza con ítems tipo "Con qué
frecuencia/dominio el colaborador…". El dataset canónico usa una escala 1-10 y una
columna por habilidad; el generador reproduce esa métrica agregando **contexto
organizacional** (departamento, puesto, antigüedad) que es la variable de cruce que
usará el análisis no supervisado.

## 2. Estructura de datos generada

| Columna               | Tipo         | Justificación                                                    |
|------------------------|--------------|------------------------------------------------------------------|
| `id_empleado`          | `EMP_####`   | Identificador anónimo tipo matrícula de RRHH.                    |
| `departamento`         | categórico   | 6 áreas típicas (TI, Ventas, RRHH/Recursos_Humanos, Operaciones, Finanzas, Marketing). |
| `puesto`               | categórico   | Progresión Junior → Especialista → Senior → Lider → Gerente.     |
| `antiguedad_anos`      | entero 0-20  | Ligada al puesto (carrera natural).                              |
| 4 columnas habilidad   | entero 1-10  | Valoración Likert simulada de cada competencia.                  |

## 3. Ponderaciones y su porqué

### 3.1 Medias por departamento (escala 1-10)

| Departamento      | Comunicación | Trabajo en Equipo | Resolución de Conflictos | Liderazgo |
|-------------------|--------------|-------------------|--------------------------|-----------|
| TI                | 6.2          | 7.6               | 6.5                      | 5.8       |
| Ventas            | 8.2          | 6.4               | 6.6                      | 6.2       |
| Recursos_Humanos  | 8.4          | 7.4               | 7.8                      | 6.0       |
| Operaciones       | 5.4          | 5.6               | 7.0                      | 5.2       |
| Finanzas          | 6.6          | 6.0               | 6.0                      | 5.6       |
| Marketing         | 7.6          | 6.8               | 6.2                      | 6.4       |

**Racional:**

- **Comunicación_efectiva alta en RRHH y Ventas** porque son áreas de interacción
  directa y negociación con personas; **baja en Operaciones** por su naturaleza
  técnica e interna.
- **Trabajo en equipo alto en TI y RRHH** por metodologías colaborativas (squads,
  dinámicas grupales); **bajo en Operaciones/Finanzas** por tareas más
  individualizadas.
- **Resolución de conflictos alta en RRHH y Operaciones** por su rol de mediación
  y gestión de crisis/en campo.
- **Liderazgo no depende del departamento** sino de la trayectoria: se escala con
  la antigüedad (ver 3.2).

### 3.2 Ponderaciones según puesto y antigüedad

`media_final = media_departamento + ajuste_puesto + min(3.0, antigüedad × 0.12)`

| Puesto     | Ajuste | Rango de antigüedad | Justificación                                        |
|------------|--------|---------------------|------------------------------------------------------|
| Junior     | −1.0   | 0–4 años            | Menos dominio; curva de aprendizaje.                 |
| Especialista | −0.5 | 2–8 años            | Domina su área funcional.                            |
| Senior     | 0.0    | 4–12 años           | Nivel de referencia.                                 |
| Lider      | +1.0   | 8–18 años           | Sus roles ya gestionan equipos.                      |
| Gerente    | +2.0   | 10–20 años          | Mayor responsabilidad y trayectoria.                 |

El término `min(3.0, antigüedad × 0.12)` modela que el **liderazgo** mejora con la
experiencia hasta un tope (+3 puntos a ~25 años), penalizando el sesgo de romper la
escala 1-10. Empíricamente produce: Junior ≈ 5.1, Senior ≈ 6.7, Lider ≈ 8.4,
Gerente ≈ 9.2 de media.

### 3.3 Estructura de varianza

```
puntaje = clip(round(Normal(media_departamento + ajuste_puesto [+ liderazgo·antigüedad],
                        sigma_habilidad)), 1, 10)
```

- `sigma = 1.4–1.6` por habilidad da dispersión similar a instrumentos psicométricos
  reales (CV ≈ 25–27%).
- Se suma un **factor latente común** `factor_comun` (normal estándar × 0.45) que
  correlaciona positivamente las 4 habilidades (rho empírico 0.27–0.42), tal como
  ocurre en evaluaciones 360° reales donde una persona fuerte suele destacar en
  varias competencias socioemocionales. Esto garantiza que el análisis no
  supervisado encuentre estructura agrupable (se validan clústeres con silueta
  positiva).

## 4. Reproducibilidad

- Se usa `np.random.default_rng(seed)` con `seed=42` por defecto: el dataset es
  reproducible exactamente.
- Pesos de población: departamentos `[0.12, 0.10, 0.24, 0.14, 0.22, 0.18]` y
  puestos `[0.35, 0.20, 0.25, 0.12, 0.08]`, reflejando una empresa con mayoría de
  base operativa/juniors y minoría gerencial.

## 5. Uso

Generación vía API (endpoint `POST /api/data/sintetico`) o directa:

```python
from app.services.synthetic import generar_dataset
df = generar_dataset(2500)      # 2500 empleados, seed determinística
```