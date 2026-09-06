"use client";

import type { ReactNode } from "react";

export function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  empty = "Sin registros.",
}: {
  columns: { key: string; label: string; render?: (row: T) => ReactNode }[];
  rows: T[];
  empty?: string;
}) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-400 py-8 text-center">{empty}</p>;
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 text-left">
            {columns.map((c) => (
              <th key={c.key} className="px-4 py-3 text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-slate-50/70 transition-colors">
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-2.5 text-slate-700 whitespace-nowrap">
                  {c.render ? c.render(row) : String(row[c.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}