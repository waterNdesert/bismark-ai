import Link from "next/link";
import type { ReactNode, ButtonHTMLAttributes } from "react";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}
export function AppPage({ children }: { children: ReactNode }) {
  return <div className="app-page">{children}</div>;
}
export function AppPanel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`app-panel ${className}`}>{children}</section>;
}
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-icon">{icon}</div>}
      <h2>{title}</h2>
      {description && <p>{description}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}
export function AppButton({
  children,
  variant = "primary",
  className = "",
  ...props
}: {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
} & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={`app-button ${variant} ${className}`} {...props}>
      {children}
    </button>
  );
}
export function AppLink({
  href,
  children,
  secondary = false,
}: {
  href: string;
  children: ReactNode;
  secondary?: boolean;
}) {
  return (
    <Link
      className={`app-link-button ${secondary ? "secondary" : ""}`}
      href={href}
    >
      {children}
    </Link>
  );
}
export function StatusBadge({
  children,
  variant = "default",
}: {
  children: ReactNode;
  variant?: "default" | "active" | "coming";
}) {
  return (
    <span className={`status-badge ${variant}`}>
      {variant === "active" && (
        <span aria-hidden="true" className="status-dot" />
      )}
      {children}
    </span>
  );
}
