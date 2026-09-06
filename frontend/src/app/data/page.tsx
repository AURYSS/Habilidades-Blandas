"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Database, FileUp, Plus, Trash2, FileDown, Search } from "lucide-react";
import { api, downloadExcelFiltrado } from "@/lib/api";
import { SKILLS, type DataMeta, type DataPage } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/Card";
import { DataTable } from "@/components/DataTable";
import { StatCard } from "@/components/StatCard";

export default function DataPage() {
  const [meta, setMeta] = useState<DataMeta | null>(null);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<DataPage | null>(null);
  const [filtroDepto, setFiltroDepto] = useState("");
  const [filtroPuesto, setFiltroPuesto] = useState("");
  const [habilidad, setHabilidad] = useState<string>(SKILLS[0]);
  const [umbralMin, setUmbralMin] = useState("");
  const [umbralMax, setUmbralMax] = useState("");
  const [filtrados, setFiltrados] = useState<Record<string, unknown>[] | null>(null);
  const [msg, setMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const recargar = useCallback(() => {
    api.meta().then(setMeta).catch(() => {});
    api.datos(page, 50).then(setData).catch(() => {});
  }, [page]);

  useEffect(() => recargar(), [recargar]);

  const aplicarFiltros = async () => {
    const res = await api.segmentar({
      departamento: filtroDepto || undefined,
      puesto: filtroPuesto || undefined,
      habilidad: habilidad,
      umbral_min: umbralMin ? Number(umbralMin) : undefined,
      umbral_max: umbralMax ? Number(umbralMax) : undefined,
    });
    setFiltrados(res.records);
    setMsg(`Filtrado aplicado: ${res.total} registros.`);
  };

  const subir = async (file: File) => {
    const res = await api.subirCsv(file);
    setMsg(`Dataset cargado: ${res.insertados} registros insertados. ${res.mensaje}`);
    setPage(1);
    recargar();
  };

  const sintetico = async () => {
    const res = await api.generarSintetico(2500);
    setMsg(`Dataset sintético generado: ${res.generados} registros.`);
    setPage(1);
    recargar();
  };

  const limpiar = async () => {
    if (!confirm("¿Eliminar todos los datos?")) return;
    await api.limpiarDatos();
    setMsg("Base limpiada.");
    setPage(1);
    recargar();
  };

  const descargarFiltrados = () => {
    downloadExcelFiltrado({
      departamento: filtroDepto || undefined,
      puesto: filtroPuesto || undefined,
      habilidades: [habilidad],
    });
  };

  const columnas = [
    { key: "id_empleado", label: "ID Empleado" },
    { key: "departamento", label: "Departamento" },
    { key: "puesto", label: "Puesto" },
    { key: "antiguedad_anos", label: "Antigüedad (años)" },
    ...SKILLS.filter((s) => meta?.habilidades.includes(s) ?? true).map((s) => ({
      key: s,
      label: s.replaceAll("_", " "),
    })),
  ];

  const paginas = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div>
      <PageHeader
        eyebrow="Cargar y explorar datos"
        title="Datos de habilidades blandas"
        description="Carga datasets (CSV/Excel) con 2 a 4 habilidades en escala Likert 1-10, o genera datos sintéticos, y filtra la selección con valores cuantitativos."
        action={
          <button className="btn-primary" onClick={() => fileRef.current?.click()}>
            <FileUp className="w-4 h-4" /> Cargar dataset
          </button>
        }
      />
      <input
        ref={fileRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && subir(e.target.files[0])}
      />
      {msg && <div className="mb-4 text-sm px-4 py-3 rounded-xl bg-brand-50 text-brand-800 border border-brand-100">{msg}</div>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Registros" value={data?.total ?? "…"} icon={<Database className="w-5 h-5" />} />
        <StatCard label="Departamentos" value={meta?.departamentos.length ?? "…"} icon={<Database className="w-5 h-5" />} />
        <StatCard label="Habilidades" value={meta?.habilidades.length ?? "…"} icon={<Database className="w-5 h-5" />} />
        <StatCard label="Estado BD" value={meta?.db_status ?? "…"} icon={<Database className="w-5 h-5" />} />
      </div>

      <Card title="Filtros" subtitle="Segmenta por contexto organizacional y rango de la habilidad">
        <div className="grid md:grid-cols-5 gap-3 items-end">
          <div>
            <label className="label">Departamento</label>
            <select className="input" value={filtroDepto} onChange={(e) => setFiltroDepto(e.target.value)}>
              <option value="">Todos</option>
              {meta?.departamentos.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Puesto</label>
            <select className="input" value={filtroPuesto} onChange={(e) => setFiltroPuesto(e.target.value)}>
              <option value="">Todos</option>
              {meta?.puestos.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Habilidad</label>
            <select className="input" value={habilidad} onChange={(e) => setHabilidad(e.target.value)}>
              {SKILLS.map((s) => (
                <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">Min</label>
              <input className="input" type="number" min={1} max={10} value={umbralMin} onChange={(e) => setUmbralMin(e.target.value)} />
            </div>
            <div>
              <label className="label">Max</label>
              <input className="input" type="number" min={1} max={10} value={umbralMax} onChange={(e) => setUmbralMax(e.target.value)} />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary flex-1" onClick={aplicarFiltros}>
              <Search className="w-4 h-4" /> Filtrar
            </button>
            <button
              className="btn-secondary"
              title="Descargar Excel filtrado"
              onClick={descargarFiltrados}
              disabled={!filtrados}
            >
              <FileDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </Card>

      <div className="mt-4 mb-6 flex gap-2 flex-wrap">
        <button className="btn-secondary" onClick={sintetico}>
          <Plus className="w-4 h-4" /> Generar 2,500 sintéticos
        </button>
        <button className="btn-danger" onClick={limpiar}>
          <Trash2 className="w-4 h-4" /> Limpiar base
        </button>
      </div>

      <Card title="Tabla de datos" subtitle={filtrados ? `${filtrados.length} registros filtrados` : `Página ${page} de ${paginas}`}>
        <DataTable
          columns={columnas}
          rows={(filtrados ?? data?.records ?? []) as Record<string, unknown>[]}
        />
        {!filtrados && (
          <div className="flex justify-between items-center mt-4">
            <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Anterior
            </button>
            <span className="text-sm text-slate-500">Página {page} / {paginas}</span>
            <button className="btn-secondary" disabled={page >= paginas} onClick={() => setPage((p) => p + 1)}>
              Siguiente
            </button>
          </div>
        )}
      </Card>
    </div>
  );
}