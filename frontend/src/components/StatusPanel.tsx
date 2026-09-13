type StatusVariant = "idle" | "processing" | "success" | "warning" | "error";

interface StatusPanelProps {
  variant: StatusVariant;
  title: string;
  message?: string;
  children?: React.ReactNode;
}

const ICONS: Record<StatusVariant, string> = {
  idle: "",
  processing: "◌",
  success: "✓",
  warning: "⚠",
  error: "✕",
};

export function StatusPanel({ variant, title, message, children }: StatusPanelProps) {
  return (
    <div className={`status-panel status-${variant}`} role="status">
      <div className="status-icon" aria-hidden="true">
        {ICONS[variant]}
      </div>
      <div className="status-body">
        <h3>{title}</h3>
        {message && <p>{message}</p>}
        {children}
      </div>
    </div>
  );
}
