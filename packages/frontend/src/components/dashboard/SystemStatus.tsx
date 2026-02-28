import { Activity, Database, Globe, Cpu } from "lucide-react";
import { useHealth } from "../../hooks/useHealth";

export function SystemStatus() {
  const { data: health, isLoading } = useHealth();

  const services = [
    {
      name: "Agent API",
      status: health?.services?.agentApi?.status ?? "UNKNOWN",
      icon: Cpu,
    },
    {
      name: "On-Chain",
      status:
        health?.services?.onChain?.activeSentinels != null
          ? `${health.services.onChain.activeSentinels} sentinels`
          : "UNKNOWN",
      icon: Database,
    },
    {
      name: "CRE Workflow",
      status: "ACTIVE",
      icon: Globe,
    },
    {
      name: "Data Feeds",
      status: "CONNECTED",
      icon: Activity,
    },
  ];

  return (
    <div className="rounded-xl border border-aegis-border bg-aegis-card p-5">
      <h3 className="font-semibold text-sm mb-4">System Status</h3>
      <div className="space-y-3">
        {services.map((svc) => (
          <div key={svc.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <svc.icon className="w-4 h-4 text-gray-500" />
              <span className="text-gray-300">{svc.name}</span>
            </div>
            <span
              className={`text-xs font-mono ${
                svc.status === "HEALTHY" ||
                svc.status === "ACTIVE" ||
                svc.status === "CONNECTED"
                  ? "text-emerald-400"
                  : svc.status === "UNKNOWN"
                    ? "text-gray-500"
                    : "text-amber-400"
              }`}
            >
              {isLoading ? "..." : svc.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
