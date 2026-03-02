import { motion } from "framer-motion";
import { Activity, Database, Globe, Cpu, RefreshCw } from "lucide-react";
import clsx from "clsx";
import { useHealth } from "../../hooks/useHealth";
import { StatusDot } from "../common/StatusDot";

type ServiceStatus = "healthy" | "warning" | "error" | "unknown";

function getServiceStatus(status: string | undefined): ServiceStatus {
  if (!status) return "unknown";
  const upper = status.toUpperCase();
  if (upper === "HEALTHY" || upper === "ACTIVE" || upper === "CONNECTED") return "healthy";
  if (upper === "DEGRADED" || upper === "WARNING") return "warning";
  if (upper === "ERROR" || upper === "DOWN") return "error";
  return "unknown";
}

function getStatusDotType(
  status: ServiceStatus,
): "critical" | "high" | "medium" | "low" | "neutral" {
  switch (status) {
    case "healthy":
      return "low";
    case "warning":
      return "medium";
    case "error":
      return "critical";
    default:
      return "neutral";
  }
}

export function SystemStatus() {
  const { data: health, isLoading, isFetching, refetch } = useHealth();

  const services = [
    {
      name: "Agent API",
      status: health?.services?.agentApi?.status ?? "UNKNOWN",
      detail: health?.services?.agentApi?.status === "HEALTHY" ? "Connected" : undefined,
      icon: Cpu,
    },
    {
      name: "On-Chain",
      status: health?.services?.onChain?.activeSentinels != null ? "ACTIVE" : "UNKNOWN",
      detail:
        health?.services?.onChain?.activeSentinels != null
          ? `${health.services.onChain.activeSentinels} sentinels`
          : undefined,
      icon: Database,
    },
    {
      name: "CRE Workflow",
      status: "ACTIVE",
      detail: "Cron 30s",
      icon: Globe,
    },
    {
      name: "Data Feeds",
      status: "CONNECTED",
      detail: "ETH/USD",
      icon: Activity,
    },
  ];

  return (
    <section className="card">
      <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
        <div>
          <h3 className="text-base font-semibold text-text-primary">System Status</h3>
          <p className="text-sm text-text-muted">Infrastructure health</p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="btn-ghost p-2"
          aria-label="Refresh"
        >
          <RefreshCw className={clsx("h-4 w-4", isFetching && "animate-spin")} />
        </button>
      </div>

      <div className="divide-y divide-border-subtle">
        {services.map((service, index) => {
          const status = getServiceStatus(service.status);
          const ServiceIcon = service.icon;

          return (
            <motion.div
              key={service.name}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between px-5 py-3.5 transition-colors hover:bg-white/[0.02]"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-bg-elevated text-text-muted">
                  <ServiceIcon className="h-4 w-4" />
                </span>
                <div>
                  <p className="text-sm font-medium text-text-primary">{service.name}</p>
                  {service.detail && <p className="text-xs text-text-muted">{service.detail}</p>}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {isLoading ? (
                  <span className="h-4 w-12 animate-pulse rounded bg-border-subtle" />
                ) : (
                  <>
                    <StatusDot
                      status={getStatusDotType(status)}
                      animate={status === "healthy"}
                      size="sm"
                    />
                    <span
                      className={clsx(
                        "text-xs font-medium",
                        status === "healthy" && "text-success",
                        status === "warning" && "text-threat-medium",
                        status === "error" && "text-threat-critical",
                        status === "unknown" && "text-text-muted",
                      )}
                    >
                      {service.status}
                    </span>
                  </>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="border-t border-border-subtle px-5 py-3">
        <p className="text-xs text-text-muted">
          Last checked: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "—"}
        </p>
      </div>
    </section>
  );
}
