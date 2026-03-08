import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Minus,
  AlertTriangle,
  Radio,
} from "lucide-react";
import clsx from "clsx";
import { api, type LiveMonitorData } from "../../lib/api";

type ThreatColor = "green" | "yellow" | "red";

function threatColor(data: LiveMonitorData | undefined): ThreatColor {
  if (!data || data.status === "unavailable") return "yellow";
  const anomalies = data.anomalies ?? [];
  if (anomalies.some((a) => a.severity === "CRITICAL" || a.severity === "HIGH")) return "red";
  if (anomalies.some((a) => a.severity === "MEDIUM")) return "yellow";
  return "green";
}

function threatLabel(color: ThreatColor) {
  switch (color) {
    case "green":
      return "Healthy";
    case "yellow":
      return "Warning";
    case "red":
      return "Threat Detected";
  }
}

function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

function formatEthPrice(price: number | null | undefined): string {
  if (price == null) return "—";
  return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(pct: number | null | undefined): string {
  if (pct == null) return "—";
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

export function LiveMonitor() {
  const { data, isLoading, error, dataUpdatedAt } = useQuery<LiveMonitorData>({
    queryKey: ["live-monitor-aave"],
    queryFn: () => api.getLiveAaveMonitor(),
    refetchInterval: 10_000,
    retry: 2,
  });

  const color = threatColor(data);
  const isUnavailable = data?.status === "unavailable";
  const changePct = data?.tvl_change_percent ?? null;
  const lastUpdate = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : "—";

  return (
    <section className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
        <div className="flex items-center gap-3">
          <div
            className={clsx(
              "flex h-9 w-9 items-center justify-center rounded-lg",
              color === "green" && "bg-success/20 text-success",
              color === "yellow" && "bg-yellow-500/20 text-yellow-400",
              color === "red" && "bg-red-500/20 text-red-400",
            )}
          >
            <Radio className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text-primary">Live Aave V3 Monitor</h3>
            <p className="text-xs text-text-muted">Base Mainnet &middot; Real-time data</p>
          </div>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              "h-2.5 w-2.5 rounded-full",
              color === "green" && "bg-success animate-pulse",
              color === "yellow" && "bg-yellow-400 animate-pulse",
              color === "red" && "bg-red-500 animate-pulse",
            )}
          />
          <span
            className={clsx(
              "text-xs font-medium",
              color === "green" && "text-success",
              color === "yellow" && "text-yellow-400",
              color === "red" && "text-red-400",
            )}
          >
            {threatLabel(color)}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="p-5">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Activity className="h-5 w-5 animate-spin text-text-muted" />
            <span className="ml-2 text-sm text-text-muted">Fetching live data...</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            Unable to fetch live data. Ensure the agent API is running.
          </div>
        )}

        {!isLoading && !error && isUnavailable && (
          <div className="rounded-lg border border-yellow-500/40 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-300">
            {data?.message ?? "Live data not yet available."}
          </div>
        )}

        {!isLoading && !error && !isUnavailable && data && (
          <>
            {/* Metric grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* TVL */}
              <div className="rounded-lg border border-border-subtle bg-bg-elevated p-4">
                <div className="flex items-center gap-2 text-text-muted">
                  <DollarSign className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">
                    Total Value Locked
                  </span>
                </div>
                <p className="mt-2 text-2xl font-bold text-text-primary">
                  {formatUsd(data.tvl_usd_estimate)}
                </p>
                <div className="mt-1 flex items-center gap-1 text-xs">
                  {changePct != null && changePct > 0 && (
                    <TrendingUp className="h-3 w-3 text-success" />
                  )}
                  {changePct != null && changePct < 0 && (
                    <TrendingDown className="h-3 w-3 text-red-400" />
                  )}
                  {changePct != null && changePct === 0 && (
                    <Minus className="h-3 w-3 text-text-muted" />
                  )}
                  <span
                    className={clsx(
                      changePct != null && changePct > 0 && "text-success",
                      changePct != null && changePct < 0 && "text-red-400",
                      (changePct == null || changePct === 0) && "text-text-muted",
                    )}
                  >
                    {formatPercent(changePct)}
                  </span>
                  <span className="text-text-muted">vs previous</span>
                </div>
              </div>

              {/* ETH/USD Price */}
              <div className="rounded-lg border border-border-subtle bg-bg-elevated p-4">
                <div className="flex items-center gap-2 text-text-muted">
                  <Activity className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">
                    ETH/USD (Chainlink)
                  </span>
                </div>
                <p className="mt-2 text-2xl font-bold text-text-primary">
                  {formatEthPrice(data.chainlink_eth_usd)}
                </p>
                <p className="mt-1 text-xs text-text-muted">Chainlink Data Feeds</p>
              </div>
            </div>

            {/* Anomalies */}
            {(data.anomalies?.length ?? 0) > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Detected Anomalies
                </h4>
                {data.anomalies!.map((anomaly, i) => (
                  <div
                    key={i}
                    className={clsx(
                      "rounded-lg border px-3 py-2 text-sm",
                      anomaly.severity === "CRITICAL" &&
                        "border-red-500/40 bg-red-500/10 text-red-300",
                      anomaly.severity === "HIGH" &&
                        "border-orange-500/40 bg-orange-500/10 text-orange-300",
                      anomaly.severity === "MEDIUM" &&
                        "border-yellow-500/40 bg-yellow-500/10 text-yellow-300",
                      !["CRITICAL", "HIGH", "MEDIUM"].includes(anomaly.severity) &&
                        "border-border-subtle bg-bg-elevated text-text-secondary",
                    )}
                  >
                    <span className="font-medium">{anomaly.severity}</span>
                    <span className="mx-1.5">&middot;</span>
                    <span>{anomaly.message}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Footer */}
            <div className="mt-4 flex items-center justify-between text-xs text-text-muted">
              <span>Protocol: {data.protocol ?? data.adapter_type ?? "Aave V3"}</span>
              <span>Updated: {lastUpdate}</span>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
