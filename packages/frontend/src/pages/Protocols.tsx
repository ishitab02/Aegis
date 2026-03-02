import { Fragment, useMemo, useState } from "react";
import { Boxes, ChevronDown, ChevronUp, Plus, RefreshCw, X } from "lucide-react";
import clsx from "clsx";
import { useAlerts, formatRelativeTime } from "../hooks/useAlerts";
import { useProtocols } from "../hooks/useProtocols";
import { CircuitBreakerCard } from "../components/protocol/CircuitBreakerCard";
import { RegisterProtocol } from "../components/protocol/RegisterProtocol";
import { LoadingSkeleton } from "../components/common/LoadingSkeleton";

type StatusFilter = "all" | "active" | "paused";

function statusLabel(active: boolean): "ACTIVE" | "PAUSED" {
  return active ? "ACTIVE" : "PAUSED";
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) {
    return fallback;
  }

  if (error.message.toLowerCase().includes("timed out")) {
    return "Request timed out. Please retry.";
  }

  return error.message || fallback;
}

export function ProtocolsPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [expandedAddress, setExpandedAddress] = useState<string | null>(null);
  const [registerOpen, setRegisterOpen] = useState(false);

  const {
    data: protocols,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useProtocols({ refetchInterval: 15_000 });

  const {
    data: alerts,
    error: alertsError,
  } = useAlerts({ page: 1, limit: 200, refetchInterval: 15_000 });

  const latestByProtocol = useMemo(() => {
    const map = new Map<string, number>();

    for (const alert of alerts?.items ?? []) {
      const key = alert.protocol.toLowerCase();
      const current = map.get(key) ?? 0;
      if (alert.createdAt > current) {
        map.set(key, alert.createdAt);
      }
    }

    return map;
  }, [alerts]);

  const filteredProtocols = useMemo(() => {
    const all = protocols ?? [];
    if (statusFilter === "all") {
      return all;
    }

    const expected = statusFilter === "active";
    return all.filter((protocol) => protocol.active === expected);
  }, [protocols, statusFilter]);

  const protocolErrorMessage = getErrorMessage(error, "Failed to load protocols.");
  const alertsErrorMessage = getErrorMessage(alertsError, "Failed to load alert timestamps.");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border-subtle bg-bg-surface p-4">
        <div>
          <h1 className="text-xl font-semibold text-white">Protocols</h1>
          <p className="text-sm text-text-muted">Manage registered protocols and inspect circuit breaker state.</p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
            className="rounded border border-border-subtle bg-bg-elevated px-3 py-2 text-sm text-text-primary"
          >
            <option value="all">All status</option>
            <option value="active">Active only</option>
            <option value="paused">Paused only</option>
          </select>

          <button
            type="button"
            onClick={() => setRegisterOpen(true)}
            className="inline-flex items-center gap-2 rounded bg-blue-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-blue-400"
          >
            <Plus className="h-4 w-4" />
            Register New Protocol
          </button>
        </div>
      </div>

      <section className="overflow-hidden rounded-lg border border-border-subtle bg-bg-surface">
        <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3">
          <p className="text-sm text-text-secondary">
            {filteredProtocols.length} protocol{filteredProtocols.length === 1 ? "" : "s"}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="rounded border border-border-subtle p-2 text-text-secondary transition hover:bg-bg-elevated"
            aria-label="Refresh protocols"
          >
            <RefreshCw className={clsx("h-4 w-4", isFetching && "animate-spin")} />
          </button>
        </div>

        {isLoading && (
          <div className="space-y-3 p-4">
            <LoadingSkeleton className="h-10" />
            <LoadingSkeleton className="h-10" />
            <LoadingSkeleton className="h-10" />
          </div>
        )}

        {error && !isLoading && (
          <div className="p-4">
            <div className="rounded-lg border border-red-500/40 bg-red-500/20 px-4 py-3">
              <p className="text-sm text-red-200">{protocolErrorMessage}</p>
              <button
                type="button"
                onClick={() => refetch()}
                className="mt-2 rounded border border-red-500/50 px-2 py-1 text-xs text-red-200 transition hover:bg-red-500/20"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!isLoading && !error && filteredProtocols.length === 0 && (
          <div className="px-4 py-10 text-center">
            <Boxes className="mx-auto mb-2 h-8 w-8 text-text-disabled" />
            <p className="text-sm text-text-secondary">No protocols match the selected status.</p>
            <p className="mt-1 text-xs text-text-disabled">Register a new protocol or adjust the status filter.</p>
          </div>
        )}

        {!isLoading && !error && filteredProtocols.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-border-subtle text-left text-xs uppercase tracking-[0.08em] text-text-muted">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Address</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Alert Threshold</th>
                  <th className="px-4 py-3">Last Alert</th>
                  <th className="w-14 px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {filteredProtocols.map((protocol) => {
                  const rowOpen = expandedAddress === protocol.address;
                  const latest = latestByProtocol.get(protocol.address.toLowerCase());
                  const status = statusLabel(protocol.active);

                  return (
                    <Fragment key={protocol.address}>
                      <tr
                        className="cursor-pointer border-b border-border-subtle text-sm text-text-primary transition hover:bg-bg-elevated/40"
                        onClick={() => setExpandedAddress((current) => (current === protocol.address ? null : protocol.address))}
                      >
                        <td className="px-4 py-3 font-medium text-white">{protocol.name}</td>
                        <td className="px-4 py-3 font-mono text-xs text-text-muted">{protocol.address}</td>
                        <td className="px-4 py-3">
                          <span
                            className={clsx(
                              "inline-flex rounded px-2 py-0.5 text-xs font-medium",
                              status === "PAUSED"
                                ? "bg-red-500/20 text-red-300"
                                : "bg-green-500/20 text-green-300"
                            )}
                          >
                            {status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-text-secondary">{protocol.alertThreshold}%</td>
                        <td className="px-4 py-3 text-text-muted">
                          {latest ? formatRelativeTime(latest) : "No alerts"}
                        </td>
                        <td className="px-4 py-3 text-right text-text-muted">
                          {rowOpen ? <ChevronUp className="ml-auto h-4 w-4" /> : <ChevronDown className="ml-auto h-4 w-4" />}
                        </td>
                      </tr>

                      {rowOpen && (
                        <tr className="border-b border-border-subtle bg-bg-elevated/40">
                          <td colSpan={6} className="p-4">
                            <CircuitBreakerCard address={protocol.address} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {alertsError && !isLoading && !error && (
          <div className="border-t border-border-subtle px-4 py-3 text-xs text-yellow-300">{alertsErrorMessage}</div>
        )}
      </section>

      {registerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg border border-border-subtle bg-bg-elevated p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Register New Protocol</h2>
              <button
                type="button"
                onClick={() => setRegisterOpen(false)}
                className="rounded p-2 text-text-secondary transition hover:bg-bg-surface"
                aria-label="Close register modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <RegisterProtocol onSuccess={() => setRegisterOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
}
