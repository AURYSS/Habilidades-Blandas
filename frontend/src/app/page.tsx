"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Database,
  FlaskConical,
  FileDown,
  BarChart3,
  Activity,
} from "lucide-react";
import { api } from "@/lib/api";
import type { DataMeta } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Card } from "@/components/Card";

export default function HomePage() {
  const [meta, setMeta] = useState<DataMeta | null>(null);
  const [health, setHealth] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    api.meta().then(setMeta).catch(() => setMeta(null));
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  const links = [
    { href: "/data", label: "Cargar datos", desc: "CSV / Excel de habilidades blandas", icon: Database },
    { href: "/statistics", label: "Estadística base", desc: "Estadísticos propios y frecuencias", icon: BarChart3 },
    { href: "/ml", label: "Machine Learning", desc: "Aplicar modelo pre-entrenado a los datos", icon: FlaskConical },
    { href: "/export", label: "Exportación", desc: "Excel de datos filtrados y PDF de estadísticas", icon: FileDown },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Unidad IV · Análisis No Supervisado"
        title="Soft Skills AI"
        description="Pipeline de medición de habilidades blandas: carga de dataset, estadística con algoritmos propios y aplicación de modelos pre-entrenados (K-Means, DBSCAN, GMM) seleccionables desde la app."
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Empleados en base"
          value={meta ? meta.total : "…"}
          icon={<Activity className="w-5 h-5" />}
          accent="bg-brand-50 text-brand-700"
          hint={meta && meta.db_status === "online" ? "PostgreSQL online" : undefined}
        />
        <StatCard
          label="Habilidades medidas"
          value={meta && meta.habilidades.length ? meta.habilidades.length : "…"}
          icon={<BarChart3 className="w-5 h-5" />}
          accent="bg-amber-50 text-amber-700"
          hint={meta?.habilidades.join(" · ")}
        />
        <StatCard
          label="Departamentos"
          value={meta && meta.departamentos.length ? meta.departamentos.length : "…"}
          icon={<Database className="w-5 h-5" />}
          accent="bg-emerald-50 text-emerald-700"
          hint={meta?.departamentos.slice(0, 3).join(" · ")}
        />
        <StatCard
          label="API / BD"
          value={health?.status ?? "…"}
          icon={<Activity className="w-5 h-5" />}
          accent="bg-violet-50 text-violet-700"
          hint={health?.database === "online" ? "Base conectada" : "Revisar conexión"}
        />
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        {links.map(({ href, label, desc, icon: Icon }) => (
          <Link key={href} href={href}>
            <Card className="hover:shadow-lift transition-shadow duration-200 h-full">
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center">
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-bold text-ink-900">{label}</p>
                  <p className="text-sm text-slate-500">{desc}</p>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-300" />
              </div>
            </Card>
          </Link>
        ))}
      </div>

      <Card title="Requisito académico" className="mt-8">
        <ol className="list-decimal list-inside text-sm text-slate-600 space-y-2">
          <li>Cargar un dataset y generar una base de conocimiento con modelos pre-entrenados.</li>
          <li>Seleccionar entre 2 y 4 habilidades y elegir un modelo (K-Means, DBSCAN o GMM).</li>
          <li>Filtrar según la selección y reflejarlo en una tabla con datos cuantitativos.</li>
          <li>Descargar los datos filtrados como Excel y ambas estadísticas como PDF.</li>
        </ol>
      </Card>
    </div>
  );
}