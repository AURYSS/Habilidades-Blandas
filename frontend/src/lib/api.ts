import type {
  AplicarRequest,
  AplicarResponse,
  ClusterPlots,
  DataMeta,
  DataPage,
  DescriptiveRow,
  DetalleExperimento,
  ElbowResponse,
  FrequencyResponse,
  HistoricoItem,
  Modelo,
  PlotlyFigure,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body?.slice(0, 200) || res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () => request<Record<string, string>>("/health"),

  // Datos
  meta: () => request<DataMeta>("/data/meta"),
  datos: (page = 1, page_size = 50) =>
    request<DataPage>(`/data?page=${page}&page_size=${page_size}`),
  segmentar: (body: {
    departamento?: string;
    puesto?: string;
    antiguedad_min?: number;
    antiguedad_max?: number;
    habilidad?: string;
    umbral_min?: number;
    umbral_max?: number;
  }) =>
    request<{ total: number; records: Record<string, unknown>[] }>("/data/segmentar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  subirCsv: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ insertados: number; total_tabla: number; mensaje: string }>("/data/upload", {
      method: "POST",
      body: form,
      headers: {},
    });
  },
  generarSintetico: (cantidad: number) =>
    request<{ generados: number; total_tabla: number }>(`/data/sintetico?cantidad=${cantidad}`, {
      method: "POST",
    }),
  limpiarDatos: () => request<void>("/data", { method: "DELETE" }),

  // Estadística base
  descriptiva: () => request<{ habilidades: string[]; filas: DescriptiveRow[] }>("/statistics/descriptiva"),
  frecuencias: (habilidad: string, departamento?: string) =>
    request<FrequencyResponse>(
      `/statistics/frecuencias?habilidad=${encodeURIComponent(habilidad)}${departamento ? `&departamento=${encodeURIComponent(departamento)}` : ""}`,
    ),
  graficoDimension: (habilidad: string) =>
    request<{ histograma: PlotlyFigure; distribucion_departamento: PlotlyFigure }>(
      `/statistics/graficos/dimension?habilidad=${encodeURIComponent(habilidad)}`,
    ),
  graficoCorrelacion: () =>
    request<{ correlacion: PlotlyFigure }>("/statistics/graficos/correlacion"),

  // Clustering (base de conocimiento)
  modelos: (skills?: string[], algoritmo?: string) => {
    const qs = new URLSearchParams();
    if (skills?.length) qs.set("skills", skills.join(","));
    if (algoritmo) qs.set("algoritmo", algoritmo);
    return request<Modelo[]>(`/clustering/modelos${qs.toString() ? `?${qs.toString()}` : ""}`);
  },
  codo: (skills: string[], normalize = true) =>
    request<ElbowResponse>("/clustering/elbow", {
      method: "POST",
      body: JSON.stringify({ skills, normalize }),
    }),
  aplicar: (body: AplicarRequest) =>
    request<AplicarResponse>("/clustering/aplicar", { method: "POST", body: JSON.stringify(body) }),
  reentrenarBase: () =>
    request<{ generados: number; modelos: Modelo[] }>("/clustering/reentrenar-base", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  plots: (sesion_id: number) =>
    request<ClusterPlots>("/clustering/plots", {
      method: "POST",
      body: JSON.stringify({ sesion_id }),
    }),

  // Historial
  historial: () => request<HistoricoItem[]>("/history"),
  detalleExperimento: (sesionId: number) =>
    request<DetalleExperimento>(`/history/${sesionId}/detalle`),
  asignaciones: (sesionId: number) =>
    request<{ sesion_id: number; asignaciones: unknown[] }>(`/history/${sesionId}/asignaciones`),
  eliminarExperimento: (sesionId: number) =>
    request<void>(`/history/${sesionId}`, { method: "DELETE" }),
};

export const downloadUrl = (path: string) => `${API_URL}${path}`;

export function descargarComo(path: string, filename: string) {
  fetch(downloadUrl(path))
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    })
    .catch((e) => alert(`No se pudo descargar: ${e}`));
}

export function downloadCsv(sesionId: number) {
  descargarComo(`/export/csv?sesion_id=${sesionId}`, `resultados_sesion_${sesionId}.csv`);
}
export function downloadExcel(sesionId: number) {
  descargarComo(`/export/excel?sesion_id=${sesionId}`, `resultados_sesion_${sesionId}.xlsx`);
}
export function downloadPdf(sesionId: number) {
  descargarComo(`/export/pdf?sesion_id=${sesionId}`, `reporte_clustering_${sesionId}.pdf`);
}
export function downloadExcelFiltrado(params: {
  departamento?: string;
  puesto?: string;
  antiguedad_min?: number;
  antiguedad_max?: number;
  habilidades?: string[];
}) {
  const qs = new URLSearchParams();
  if (params.departamento) qs.set("departamento", params.departamento);
  if (params.puesto) qs.set("puesto", params.puesto);
  if (params.antiguedad_min != null) qs.set("antiguedad_min", String(params.antiguedad_min));
  if (params.antiguedad_max != null) qs.set("antiguedad_max", String(params.antiguedad_max));
  if (params.habilidades?.length) qs.set("habilidades", params.habilidades.join(","));
  descargarComo(`/export/excel-filtrado${qs.toString() ? `?${qs.toString()}` : ""}`, "datos_filtrados_habilidades.xlsx");
}
export function downloadPdfBaseStats(params: {
  departamento?: string;
  puesto?: string;
  antiguedad_min?: number;
  antiguedad_max?: number;
  habilidades?: string[];
}) {
  const qs = new URLSearchParams();
  if (params.departamento) qs.set("departamento", params.departamento);
  if (params.puesto) qs.set("puesto", params.puesto);
  if (params.antiguedad_min != null) qs.set("antiguedad_min", String(params.antiguedad_min));
  if (params.antiguedad_max != null) qs.set("antiguedad_max", String(params.antiguedad_max));
  if (params.habilidades?.length) qs.set("habilidades", params.habilidades.join(","));
  descargarComo(`/export/pdf-estadistica-base${qs.toString() ? `?${qs.toString()}` : ""}`, "estadistica_base_habilidades.pdf");
}