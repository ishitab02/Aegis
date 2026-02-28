import { Shield } from "lucide-react";
import { useHealth } from "../../hooks/useHealth";

export function Header() {
  const { data: health } = useHealth();

  const statusColor =
    health?.status === "HEALTHY"
      ? "bg-emerald-500"
      : health?.status === "DEGRADED"
        ? "bg-amber-500"
        : "bg-red-500";

  return (
    <header className="border-b border-aegis-border bg-aegis-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-aegis-accent" />
            <div>
              <h1 className="text-lg font-bold tracking-tight">
                AEGIS Protocol
              </h1>
              <p className="text-xs text-gray-500">
                AI-Enhanced Guardian Intelligence System
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <span className={`w-2.5 h-2.5 rounded-full ${statusColor}`} />
              <span className="text-gray-400">
                {health?.status ?? "CONNECTING"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
