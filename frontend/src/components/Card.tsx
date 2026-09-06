import type { ReactNode } from "react";

export function Card({
  title,
  subtitle,
  action,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`card ${className}`}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 px-6 pt-5 pb-3">
          <div>
            {title && <h3 className="font-bold text-ink-900 text-[15px]">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className="px-6 pb-6" style={{ paddingTop: title ? 0 : 16 }}>
        {children}
      </div>
    </div>
  );
}