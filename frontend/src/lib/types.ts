// Tipos compartidos con la API del backend (dominio: habilidades blandas).

export const SKILLS = [
  "Comunicacion_Efectiva",
  "Trabajo_Equipo",
  "Resolucion_Conflictos",
  "Liderazgo",
] as const;

export const SKILL_LABELS: Record<string, string> = {
  Comunicacion_Efectiva: "Comunicación Efectiva",
  Trabajo_Equipo: "Trabajo en Equipo",
  Resolucion_Conflictos: "Resolución de Conflictos",
  Liderazgo: "Liderazgo",
};

export type Skill = (typeof SKILLS)[number];

export interface DataMeta {
  total: number;
  departamentos: string[];
  puestos: string[];
  habilidades: string[];
  antiguedad_min: number | null;
  antiguedad_max: number | null;
  db_status: "online" | "offline";
  db_message?: string | null;
}

export interface DataPage {
  total: number;
  page: number;
  page_size: number;
  records: Record<string, unknown>[];
}

export interface DescriptiveRow {
  dimension: string;
  promedio: number | null;
  moda: number | string | null;
  mediana: number | null;
  varianza: number | null;
  desviacion: number | null;
  cv: number | null;
  minimo: number | null;
  maximo: number | null;
  rango: number | null;
  sturges: number | null;
  amplitud: number | null;
}

export interface FrequencyRow {
  Clase: string;
  "Marca de Clase": number | string;
  f: number;
  Fr: number;
  "%": number;
  F: number | string;
}

export interface FrequencyResponse {
  habilidad: string;
  tabla: FrequencyRow[];
  controles: Record<string, unknown>;
}

export interface PlotlyFigure {
  data: unknown[];
  layout: Record<string, unknown>;
}

export interface ElbowResponse {
  skills: string[];
  k_values: number[];
  inercias: number[];
  grafico: PlotlyFigure;
  recomendacion: number;
  n: number;
  silueta: number;
}

export interface Modelo {
  id: number;
  nombre: string;
  algoritmo: "kmeans" | "dbscan" | "gmm";
  skills: string[];
  k_clusters: number | null;
  inercia: number | null;
  silueta: number | null;
  parametros: Record<string, unknown>;
  timestamp: string;
}

export interface AplicarRequest {
  skills: string[];
  algoritmo: "kmeans" | "dbscan" | "gmm";
  modelo_id?: number | null;
  nombre_sesion: string;
}

export interface AplicarResponse {
  sesion_id: number;
  nombre_sesion: string;
  algoritmo: string;
  modelo_id: number | null;
  modelo_nombre: string | null;
  skills: string[];
  k_clusters: number | null;
  silueta: number | null;
  inercia: number | null;
  asignados: number;
  totales: number;
  conteo_clusters: Record<string, number>;
  promedio_por_cluster: Record<string, Record<string, number>>;
  filas: Record<string, unknown>[];
}

export interface ClusterPlots {
  pca_2d: PlotlyFigure;
  pca_3d: PlotlyFigure;
  distribucion_departamento: PlotlyFigure;
  perfil_clusters: PlotlyFigure;
  varianza_explicada: number[];
}

export interface HistoricoItem {
  id: number;
  nombre_sesion: string;
  algoritmo: string;
  skills: string[] | null;
  modelo_id: number | null;
  k_clusters: number | null;
  inercia: number | null;
  silueta: number | null;
  ruta_modelo: string | null;
  timestamp: string;
}

export interface DetalleExperimento {
  base: {
    nombre_sesion: string;
    algoritmo: string;
    k_clusters: number | null;
    skills: string[];
    modelo: {
      nombre: string;
      algoritmo: string;
      skills: string[];
      k_clusters: number | null;
      silueta: number | null;
      inercia: number | null;
    } | null;
    normalizar: boolean;
    creado: string | null;
  } | null;
  silueta: number | null;
  inercia: number | null;
  recomendacion_extra: string | null;
  asignados: number;
  totales: number;
}