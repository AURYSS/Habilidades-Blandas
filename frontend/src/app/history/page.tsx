"use client";

import { useEffect, useState } from "react";
import { Trash2, Eye, History, Activity } from "lucide-react";
import { api } from "@/lib/api";
import { SKILL_LABELS, type DetalleExperimento, type HistoricoItem } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { StatCard } from "@/components/StatCard";

export default function HistoryPage() {
  const [items, setItems] = useState<HistoricoItem[]>([]);
  const [detalle, setDetalle] = useState<{ sesionId: number; data: DetalleExperimento } | null>(null);

  const recargar = () => {
    api.historial().then(setItems).catch(() => {});
  };
  useEffect(() => recargar(), []);

  const ver = async (id: number) => {
    try {
      const d = await api.detalleExperimento(id);
      setDetalle({ sesionId: id, data: d });
    } catch {
      setDetalle(null);
    }
  };

  const eliminar = async (id: number) => {
    if (!confirm("¿Eliminar la sesión y sus asignaciones?")) return;
    await api.eliminarExperimento(id);
    if (detalle?.sesionId === id) setDetalle(null);
    recargar();
  };

  const reentrenar = async (item: HistoricoItem) => {
    try {
      const skills = item.skills as unknown as string[];
      await api.aplicar({
        skills,
        algoritmo: "kmeans",
        modelo_id: null,
        nombre_sesion: `${item.nombre_sesion} (Re-entrenado)`,
      });
      recargar();
      alert("Sesión re-entrenada con éxito.");
    } catch (e) {
      alert(`Error al re-entrenar: ${(e as Error).message}`);
    }
  };

  const columnas = [
    {
      key: "id",
      label: "ID",
      render: (r: Record<string, unknown>) => <span className="badge">#{String(r.id)}</span>,
    },
    { key: "nombre_sesion", label: "Nombre" },
    { key: "algoritmo", label: "Algoritmo" },
    {
      key: "skills",
      label: "Habilidades",
      render: (r: Record<string, unknown>) =>
        (r.skills as unknown as string[])?.map((s) => SKILL_LABELS[s]).join(" · ") || "—",
    },
    { key: "k_clusters", label: "K" },
    { key: "inercia", label: "Inercia" },
    { key: "silueta", label: "Silhouette" },
    {
      key: "timestamp",
      label: "Creado",
      render: (r: Record<string, unknown>) =>
        new Date(String(r.timestamp)).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" }),
    },
    {
      key: "_acciones",
      label: "",
      render: (r: Record<string, unknown>) => {
        const item = r as unknown as HistoricoItem;
        return (
          <div className="flex gap-2">
            <button className="btn-ghost" title="Ver detalle" onClick={() => ver(Number(r.id))}>
              <Eye className="w-4 h-4" />
            </button>
            <button className="btn-ghost text-brand-600" title="Re-entrenar" onClick={() => reentrenar(item)}>
              <Activity className="w-4 h-4" />
            </button>
            <button className="btn-ghost text-red-500" title="Eliminar" onClick={() => eliminar(Number(r.id))}>
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        );
      },
    },
  ];

  const base = detalle?.data.base;

  return (
    <div>
      <PageHeader
        eyebrow="Histórico de sesiones"
        title="Experimentos"
        description="Sesiones donde un modelo pre-entrenado fue aplicado sobre los datos cargados. Consulta el detalle o elimina una sesión."
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Sesiones" value={items.length} icon={<History className="w-5 h-5" />} />
        <StatCard label="Asignados" value={detalle?.data.asignados ?? "—"} icon={<Activity className="w-5 h-5" />} />
        <StatCard label="Totales" value={detalle?.data.totales ?? "—"} icon={<Activity className="w-5 h-5" />} />
        <StatCard label="Silhouette" value={detalle?.data.silueta?.toFixed(3) ?? "—"} icon={<Activity className="w-5 h-5" />} />
      </div>

      <Card title="Sesiones">
        <DataTable columns={columnas} rows={items as unknown as Record<string, unknown>[]} />
      </Card>

      {detalle && base && (
        <Card title={`Detalle · sesión #${detalle.sesionId}`} className="mt-6">
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-1 text-slate-600">
              <p><strong className="text-ink-900">Nombre:</strong> {base.nombre_sesion}</p>
              <p><strong className="text-ink-900">Algoritmo:</strong> {base.algoritmo}</p>
              <p><strong className="text-ink-900">Clústeres (k):</strong> {base.k_clusters ?? "—"}</p>
              <p><strong className="text-ink-900">Creado:</strong> {base.creado}</p>
            </div>
            <div className="space-y-1 text-slate-600">
              <p>
                <strong className="text-ink-900">Habilidades:</strong>{" "}
                {base.skills?.map((s) => SKILL_LABELS[s]).join(", ") ?? "—"}
              </p>
              <p>
                <strong className="text-ink-900">Modelo:</strong> {base.modelo?.nombre ?? "—"}
              </p>
              <p><strong className="text-ink-900">Silhouette:</strong> {detalle.data.silueta?.toFixed(4)}</p>
              <p><strong className="text-ink-900">Inercia (manual):</strong> {detalle.data.inercia?.toFixed(2)}</p>
            </div>
          </div>
          {detalle.data.recomendacion_extra && (
            <p className="mt-4 text-sm px-4 py-3 rounded-xl bg-amber-50 text-amber-800 border border-amber-200">
              {detalle.data.recomendacion_extra}
            </p>
          )}
        </Card>
      )}
    </div>
  );
}