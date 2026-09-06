"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Database,
  FileDown,
  FlaskConical,
  History,
  Sparkles,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Resumen", icon: Activity },
  { href: "/data", label: "Datos", icon: Database },
  { href: "/statistics", label: "Estadística", icon: BarChart3 },
  { href: "/ml", label: "Machine Learning", icon: FlaskConical },
  { href: "/export", label: "Exportación", icon: FileDown },
  { href: "/history", label: "Experimentos", icon: History },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex flex-col w-64 shrink-0 bg-ink-950 text-white sticky top-0 h-screen">
      <div className="px-6 py-6 flex items-center gap-3 border-b border-white/10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="font-extrabold text-[15px] tracking-tight">Soft Skills AI</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-white/10 text-white shadow-inner border border-white/10"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className="w-[18px] h-[18px]" strokeWidth={2} />
              {label}
              {active && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400" />}
            </Link>
          );
        })}
      </nav>

      <div className="px-6 py-5 border-t border-white/10">
      </div>
    </aside>
  );
}