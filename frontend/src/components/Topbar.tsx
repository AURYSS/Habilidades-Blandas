"use client";

import { useEffect, useState } from "react";
import { CircleCheck, CircleX, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

export function Topbar() {
  const [status, setStatus] = useState<{ online: boolean; extra?: Record<string, string> }>({
    online: false,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api
      .health()
      .then((h) => active && setStatus({ online: h.database === "online", extra: h }))
      .catch(() => active && setStatus({ online: false }))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/85 backdrop-blur-md">
      <div className="px-4 sm:px-8 lg:px-10 py-4 flex items-center justify-between">
        <div>
          <p className="text-[13px] font-semibold text-slate-500">Dashboard · Habilidades Blandas</p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`badge ${
              loading
                ? "bg-slate-100 text-slate-500"
                : status.online
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : status.extra?.status === "ok"
                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                    : "bg-rose-50 text-rose-700 border border-rose-200"
            }`}
          >
            {loading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : status.online ? (
              <CircleCheck className="w-3.5 h-3.5" />
            ) : (
              <CircleX className="w-3.5 h-3.5" />
            )}
            {loading 
              ? "Verificando…" 
              : status.online 
                ? "API en línea" 
                : status.extra?.status === "ok" 
                  ? "BD desconectada" 
                  : "API sin conexión"}
          </span>
        </div>
      </div>
    </header>
  );
}