"use client";

import { useEffect, useState } from "react";
import { FileDown, FileSpreadsheet, FileText } from "lucide-react";
import {
  api,
  downloadCsv,
  downloadExcel,
  downloadExcelFiltrado,
  downloadPdf,
  downloadPdfBaseStats,
} from "@/lib/api";
import { SKILLS, SKILL_LABELS, type HistoricoItem } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";

export default function ExportPage() {
  const [sesiones, setSesiones] = useState<HistoricoItem[]>([]);
  const [sesionId, setSesionId] = useState<number | null>(null);
  const [skills, setSkills] = useState<string[]>(["Comunicacion_Efectiva", "Liderazgo"]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api
      .historial()
      .then((h) => {
        setSesiones(h);
        setSesionId((prev) => prev ?? h[0]?.id ?? null);
      })
      .catch(() => {});
  }, []);

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

  const columnas = [
    {
      key: "id",
      label: "Sesión",
      render: (r: Record<string, unknown>) => <span className="badge">#{String(r.id)}</span>,
    },
    { key: "nombre_sesion", label: "Nombre" },
    { key: "algoritmo", label: "Algoritmo" },
    {
      key: "skills",
      label: "Habilidades",
      render: (r: Record<string, unknown>) =>
        (r.skills as unknown as string[])?.map((s) => SKILL_LABELS[s]).join(", "),
    },
    { key: "k_clusters", label: "K" },
    { key: "silueta", label: "Silhouette" },
    {
      key: "timestamp",
      label: "Creado",
      render: (r: Record<string, unknown>) =>
        new Date(String(r.timestamp)).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" }),
    },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Reportes y descargas"
        title="Exportación"
        description="Descarga los datos filtrados (Excel) y ambas estadísticas (PDF): la estadística base de los datos filtrados y la estadística post-clustering del modelo elegido."
      />

      <Card title="1 · Selección de habilidades" subtitle="Determina las columnas de los archivos filtrados">
        <div className="flex flex-wrap gap-2">
          {SKILLS.map((s) => (
            <button
              key={s}
              onClick={() => toggleSkill(s)}
              className={skills.includes(s) ? "btn-primary" : "btn-secondary"}
            >
              {SKILL_LABELS[s]}
            </button>
          ))}
        </div>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6 mt-6">
        <Card
          title="Datos filtrados"
          subtitle="Excel con las habilidades seleccionadas + PDF de estadística base"
        >
          <div className="space-y-3">
            <button
              className="btn-primary w-full justify-center"
              onClick={() => {
                downloadExcelFiltrado({ habilidades: skills });
                setMsg("Generando Excel de datos filtrados…");
              }}
              disabled={skills.length < 2}
            >
              <FileSpreadsheet className="w-4 h-4" /> Descargar Excel filtrado
            </button>
            <button
              className="btn-secondary w-full justify-center"
              onClick={() => {
                downloadPdfBaseStats({ habilidades: skills });
                setMsg("Generando PDF de estadística base…");
              }}
              disabled={skills.length < 2}
            >
              <FileText className="w-4 h-4" /> PDF · Estadística base (algoritmos propios)
            </button>
          </div>
        </Card>

        <Card title="Sesión de clustering" subtitle="Resultados post-clustering de un modelo aplicado">
          <div className="mb-4">
            <label className="label">Sesión</label>
            <select className="input" value={sesionId ?? ""} onChange={(e) => setSesionId(Number(e.target.value))}>
              {sesiones.map((h) => (
                <option key={h.id} value={h.id}>
                  #{h.id} · {h.nombre_sesion} · {h.algoritmo}
                </option>
              ))}
            </select>
          </div>
          <div className="grid sm:grid-cols-3 gap-2">
            <button className="btn-secondary" disabled={!sesionId} onClick={() => sesionId && downloadCsv(sesionId)}>
              <FileDown className="w-4 h-4" /> CSV
            </button>
            <button className="btn-secondary" disabled={!sesionId} onClick={() => sesionId && downloadExcel(sesionId)}>
              <FileSpreadsheet className="w-4 h-4" /> Excel
            </button>
            <button className="btn-primary" disabled={!sesionId} onClick={() => sesionId && downloadPdf(sesionId)}>
              <FileText className="w-4 h-4" /> PDF
            </button>
          </div>
        </Card>
      </div>

      <Card title="Sesiones disponibles" className="mt-6">
        <DataTable columns={columnas} rows={sesiones as unknown as Record<string, unknown>[]} />
      </Card>

      {msg && <div className="mt-6 text-sm px-4 py-3 rounded-xl bg-brand-50 text-brand-800 border border-brand-100">{msg}</div>}
    </div>
  );
}