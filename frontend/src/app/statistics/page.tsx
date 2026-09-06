"use client";

import { useEffect, useState } from "react";
import { BarChart3, FileDown, Activity } from "lucide-react";
import { api, downloadPdfBaseStats } from "@/lib/api";
import { SKILLS, type DescriptiveRow, type FrequencyResponse, type PlotlyFigure } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { PlotView } from "@/components/PlotView";
import { StatCard } from "@/components/StatCard";

export default function StatisticsPage() {
  const [filas, setFilas] = useState<DescriptiveRow[]>([]);
  const [habilidades, setHabilidades] = useState<string[]>([]);
  const [freq, setFreq] = useState<FrequencyResponse | null>(null);
  const [grafico, setGrafico] = useState<{ histograma: PlotlyFigure; distribucion_departamento: PlotlyFigure } | null>(null);
  const [corr, setCorr] = useState<PlotlyFigure | null>(null);
  const [habilidadSel, setHabilidadSel] = useState<string>(SKILLS[0]);

  useEffect(() => {
    api
      .descriptiva()
      .then((r) => {
        setFilas(r.filas);
        setHabilidades(r.habilidades);
      })
      .catch(() => {});
    api.graficoCorrelacion().then((r) => setCorr(r.correlacion)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!habilidadSel) return;
    api.frecuencias(habilidadSel).then(setFreq).catch(() => {});
    api.graficoDimension(habilidadSel).then(setGrafico).catch(() => {});
  }, [habilidadSel]);

  const columnasDesc = [
    { key: "dimension", label: "Habilidad" },
    { key: "promedio", label: "Media" },
    { key: "moda", label: "Moda" },
    { key: "mediana", label: "Mediana" },
    { key: "varianza", label: "Varianza" },
    { key: "desviacion", label: "Desv. Est." },
    { key: "cv", label: "CV%" },
    { key: "minimo", label: "Min" },
    { key: "maximo", label: "Max" },
    { key: "rango", label: "Rango" },
    { key: "sturges", label: "Sturges (k)" },
    { key: "amplitud", label: "Amplitud" },
  ];

  const columnasFreq = [
    { key: "Clase", label: "Clase" },
    { key: "Marca de Clase", label: "Marca de Clase" },
    { key: "f", label: "f" },
    { key: "Fr", label: "Fr" },
    { key: "%", label: "%" },
    { key: "F", label: "F" },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Estadística con algoritmos propios"
        title="Estadística base"
        description="Estadísticos descriptivos de la escala Likert por habilidad: media, moda, mediana, varianza, desviación, coeficiente de variación, regla de Sturges y amplitud."
        action={
          <button className="btn-primary" onClick={() => downloadPdfBaseStats({ habilidades })} disabled={!habilidades.length}>
            <FileDown className="w-4 h-4" /> PDF estadística base
          </button>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Habilidades" value={habilidades.length} icon={<BarChart3 className="w-5 h-5" />} />
        <StatCard label="Media global" value={filas.length ? (filas.reduce((a, f) => a + (f.promedio ?? 0), 0) / filas.length).toFixed(2) : "…"} icon={<Activity className="w-5 h-5" />} />
        <StatCard label="Sturges (prom.)" value={filas.length ? (filas.reduce((a, f) => a + (f.sturges ?? 0), 0) / filas.length).toFixed(1) : "…"} icon={<Activity className="w-5 h-5" />} />
        <StatCard label="Registros (n)" value={String(freq?.controles.n ?? "…")} icon={<Activity className="w-5 h-5" />} />
      </div>

      <Card title="Estadísticos descriptivos" subtitle="Cada métrica calculada con fórmula propia (sin librerías estadísticas externas)">
        <DataTable columns={columnasDesc} rows={filas as unknown as Record<string, unknown>[]} />
      </Card>

      <Card title="Frecuencias por habilidad" subtitle="Tabla de distribución de frecuencias con regla de Sturges" className="mt-6">
        <div className="mb-4 flex flex-wrap gap-2">
          {SKILLS.map((s) => (
            <button
              key={s}
              className={habilidadSel === s ? "btn-primary" : "btn-secondary"}
              onClick={() => setHabilidadSel(s)}
            >
              {s.replaceAll("_", " ")}
            </button>
          ))}
        </div>
        <div className="grid lg:grid-cols-2 gap-6">
          {freq && (
            <div>
              <DataTable columns={columnasFreq} rows={(freq.tabla as unknown as Record<string, unknown>[])} />
              <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-500">
                {Object.entries(freq.controles)
                  .filter(([k]) => !["k_utilizado"].includes(k))
                  .map(([k, v]) => (
                    <span key={k}><strong className="text-slate-700">{k}:</strong> {String(v)}</span>
                  ))}
              </div>
            </div>
          )}
          {grafico && (
            <div className="space-y-4">
              <PlotView figure={grafico.histograma} height={260} />
            </div>
          )}
        </div>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6 mt-6">
        {grafico && (
          <Card title="Distribución por departamento">
            <PlotView figure={grafico.distribucion_departamento} height={300} />
          </Card>
        )}
        {corr && (
          <Card title="Matriz de correlación (Pearson)">
            <PlotView figure={corr} height={300} />
          </Card>
        )}
      </div>
    </div>
  );
}