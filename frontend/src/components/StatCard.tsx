import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  icon,
  accent = "bg-brand-50 text-brand-700",
  hint,
}: {
  label: string;
  value: ReactNode;
  icon: ReactNode;
  accent?: string;
  hint?: string;
}) {
  return (
    <div className="card card-pad flex items-center gap-4 hover:shadow-lift transition-shadow duration-200">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${accent}`}>{icon}</div>
      <div className="min-w-0">
        <p className="text-[13px] font-bold text-ink-900 truncate">{value}</p>
        <p className="text-xs text-slate-500 truncate">{label}</p>
        {hint && <p className="text-[11px] text-slate-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  );
}