"use client";

import { useCallback, useEffect, useState } from "react";
import { Play, DatabaseZap, Loader2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { AplicarResponse, ElbowResponse, Modelo, PlotlyFigure } from "@/lib/types";
import { SKILLS, SKILL_LABELS } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { PlotView } from "@/components/PlotView";

const ALGORITMOS = [
  { value: "kmeans", label: "K-Means" },
  { value: "dbscan", label: "DBSCAN" },
  { value: "gmm", label: "GMM (mixturas)" },
] as const;

export default function MLPage() {
  const [skills, setSkills] = useState<string[]>(["Comunicacion_Efectiva", "Liderazgo"]);
  const [algoritmo, setAlgoritmo] = useState<(typeof ALGORITMOS)[number]["value"]>("kmeans");
  const [modelos, setModelos] = useState<Modelo[]>([]);
  const [modeloId, setModeloId] = useState<number | null>(null);
  const [elbow, setElbow] = useState<ElbowResponse | null>(null);
  const [resultado, setResultado] = useState<AplicarResponse | null>(null);
  const [plots, setPlots] = useState<{
    pca_2d: PlotlyFigure;
    pca_3d: PlotlyFigure;
    distribucion_departamento: PlotlyFigure;
    perfil_clusters: PlotlyFigure;
    varianza_explicada: number[];
  } | null>(null);
  const [cargando, setCargando] = useState(false);
  const [msg, setMsg] = useState("");

  const toggleSkill = (s: string) => {
    setSkills((prev) => {
      if (prev.includes(s)) {
        if (prev.length <= 2) return prev;
        return prev.filter((x) => x !== s);
      }
      if (prev.length >= 4) return prev;
      return [...prev, s];
    });
  };

  const cargarModelos = useCallback(async () => {
    try {
      const lista = await api.modelos(skills, algoritmo);
      setModelos(lista);
      setModeloId(lista[0]?.id ?? null);
    } catch {
      setModelos([]);
      setModeloId(null);
    }
  }, [skills, algoritmo]);

  useEffect(() => {
    setResultado(null);
    setPlots(null);
    cargarModelos();
  }, [skills, algoritmo, cargarModelos]);

  const runElbow = async () => {
    setCargando(true);
    try {
      const r = await api.codo(skills);
      setElbow(r);
      setMsg(`Codo listo · K recomendado: ${r.recomendacion} · Silhouette: ${r.silueta.toFixed(4)}`);
    } catch (e) {
      setMsg(`Error en codo: ${(e as Error).message}`);
    } finally {
      setCargando(false);
    }
  };

  const aplicar = async () => {
    setCargando(true);
    try {
      const r = await api.aplicar({
        skills,
        algoritmo,
        modelo_id: modeloId,
        nombre_sesion: `Análisis ${SKILL_LABELS[skills[0]]} + ${SKILL_LABELS[skills[1]]}`,
      });
      setResultado(r);
      setMsg(`Modelo ${r.modelo_nombre} aplicado a ${r.totales} empleados.`);
      const p = await api.plots(r.sesion_id);
      setPlots(p);
    } catch (e) {
      setMsg(`Error al aplicar: ${(e as Error).message}`);
    } finally {
      setCargando(false);
    }
  };

  const reentrenar = async () => {
    setCargando(true);
    try {
      const r = await api.reentrenarBase();
      setMsg(`Base de conocimiento: ${r.generados} modelos nuevos (${r.modelos.length} en total).`);
      cargarModelos();
    } catch (e) {
      setMsg(`Error: ${(e as Error).message}`);
    } finally {
      setCargando(false);
    }
  };

  const columnasResultado = [
    { key: "id_empleado", label: "ID" },
    { key: "departamento", label: "Departamento" },
    { key: "puesto", label: "Puesto" },
    ...skills.map((s) => ({ key: s, label: s.replaceAll("_", " ") })),
    {
      key: "cluster",
      label: "Clúster",
      render: (r: Record<string, unknown>) => <span className="badge">{String(r.cluster)}</span>,
    },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Aprendizaje no supervisado"
        title="Machine Learning"
        description="Selecciona entre 2 y 4 habilidades, elige un modelo pre-entrenado de la base de conocimiento y aplícalo a los datos cargados para generar clústeres."
        action={
          <button className="btn-secondary" onClick={reentrenar} disabled={cargando}>
            <DatabaseZap className="w-4 h-4" /> Reentrenar base
          </button>
        }
      />

      <Card title="1 · Selección de habilidades" subtitle="Mínimo 2 y máximo 4 de la escala Likert 1-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SKILLS.map((s) => {
            const activo = skills.includes(s);
              return (
                <button
                key={s}
                onClick={() => toggleSkill(s)}
                className={`rounded-xl border px-4 py-3 text-sm font-semibold transition-all text-left ${
                  activo
                    ? "border-brand-500 bg-brand-50 text-brand-800 ring-2 ring-brand-500/25"
                    : "border-slate-200 bg-white text-slate-600 hover:border-brand-300"
                }`}
              >
                <input type="checkbox" readOnly checked={activo} className="mr-2 accent-brand-600" />
                {SKILL_LABELS[s]}
              </button>
            );
          })}
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Seleccionadas: <strong>{skills.map((s) => SKILL_LABELS[s]).join(" · ")}</strong>
        </p>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6 mt-6">
        <Card title="2 · Modelo de la base de conocimiento" subtitle="Modelos pre-entrenados compatibles con la selección">
          <div className="grid sm:grid-cols-3 gap-2 mb-4">
            {ALGORITMOS.map((a) => (
              <button
                key={a.value}
                className={algoritmo === a.value ? "btn-primary" : "btn-secondary"}
                onClick={() => setAlgoritmo(a.value)}
              >
                {a.label}
              </button>
            ))}
          </div>
          {modelos.length ? (
            <select className="input" value={modeloId ?? ""} onChange={(e) => setModeloId(Number(e.target.value))}>
              {modelos.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nombre} · k={m.k_clusters} · sil={m.silueta?.toFixed(3)}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-slate-500">No hay modelos para esta combinación. Genera la base con «Reentrenar base».</p>
          )}
          <button className="btn-primary w-full mt-4" onClick={aplicar} disabled={cargando || !modelos.length}>
            {cargando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Aplicar modelo a los datos
          </button>
          <button className="btn-secondary w-full mt-2" onClick={runElbow} disabled={cargando}>
            <Plus className="w-4 h-4" /> Método del codo para k
          </button>
        </Card>

        {resultado && (
          <Card title="Resultados de la aplicación" subtitle={`Sesión #${resultado.sesion_id} · ${resultado.modelo_nombre}`}>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                <p className="text-[11px] font-bold uppercase text-slate-500">Clústeres</p>
                <p className="text-xl font-extrabold text-ink-900">{resultado.k_clusters}</p>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                <p className="text-[11px] font-bold uppercase text-slate-500">Silhouette</p>
                <p className="text-xl font-extrabold text-ink-900">{resultado.silueta?.toFixed(4)}</p>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                <p className="text-[11px] font-bold uppercase text-slate-500">Asignados</p>
                <p className="text-xl font-extrabold text-ink-900">{resultado.asignados} / {resultado.totales}</p>
              </div>
              <div className="rounded-xl bg-slate-50 border border-slate-200 p-3">
                <p className="text-[11px] font-bold uppercase text-slate-500">Inercia (manual)</p>
                <p className="text-xl font-extrabold text-ink-900">{resultado.inercia?.toFixed(2)}</p>
              </div>
            </div>
            <DataTable
              columns={[
                { key: "c", label: "Clúster" },
                ...skills.map((s) => ({ key: s, label: s.replaceAll("_", " ") })),
              ]}
              rows={Object.entries(resultado.conteo_clusters).map(([c]) => {
                const row: Record<string, unknown> = { c };
                Object.entries(resultado.promedio_por_cluster[c] ?? {}).forEach(([k, v]) => (row[k] = v as unknown));
                return row;
              })}
            />
          </Card>
        )}
      </div>

      {elbow && (
        <Card title="Método del codo" subtitle={`K recomendado: ${elbow.recomendacion} · n=${elbow.n}`} className="mt-6">
          <div className="grid md:grid-cols-2 gap-4">
            <PlotView figure={elbow.grafico} height={320} />
            <div className="flex flex-wrap gap-2">
              {elbow.k_values.map((k, i) => (
                <button
                  key={k}
                  className={k === elbow.recomendacion ? "btn-primary" : "btn-ghost"}
                  onClick={() => setMsg(`Inercia en k=${k}: ${elbow.inercias[i]}`)}
                >
                  k={k}: {elbow.inercias[i]}
                </button>
              ))}
            </div>
          </div>
        </Card>
      )}

      {resultado && (
        <Card
          title="Clústeres · visualización y perfil"
          subtitle={`Varianza explicada por PCA: ${plots?.varianza_explicada.join(", ") ?? "…"}`}
          className="mt-6"
        >
          <div className="grid lg:grid-cols-2 gap-6">
            {plots?.pca_2d && <PlotView figure={plots.pca_2d} height={380} />}
            {plots?.pca_3d && <PlotView figure={plots.pca_3d} height={380} />}
            {plots?.perfil_clusters && <PlotView figure={plots.perfil_clusters} height={340} />}
            {plots?.distribucion_departamento && <PlotView figure={plots.distribucion_departamento} height={340} />}
          </div>
        </Card>
      )}

      {resultado && (
        <Card title="Datos con asignación de clúster" subtitle="Filas completas con el clúster resultante" className="mt-6">
          <DataTable columns={columnasResultado} rows={resultado.filas as Record<string, unknown>[]} />
        </Card>
      )}

      {msg && <div className="mt-6 text-sm px-4 py-3 rounded-xl bg-brand-50 text-brand-800 border border-brand-100">{msg}</div>}
    </div>
  );
}