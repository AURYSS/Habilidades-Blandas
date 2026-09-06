import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-600 mb-1.5">{eyebrow}</p>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-ink-900">{title}</h1>
        {description && <p className="mt-1.5 text-sm text-slate-500 max-w-2xl">{description}</p>}
      </div>
      {action}
    </div>
  );
}