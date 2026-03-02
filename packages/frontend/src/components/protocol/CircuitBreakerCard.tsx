import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Lock, RefreshCw, ShieldCheck, Timer, Unlock } from "lucide-react";
import clsx from "clsx";
import { useAlerts, formatRelativeTime } from "../../hooks/useAlerts";
import { useProtocolStatus } from "../../hooks/useProtocols";
import { useWallet } from "../../hooks/useWallet";
import { LoadingSkeleton } from "../common/LoadingSkeleton";
import { StatusDot } from "../common/StatusDot";

function formatCountdown(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  if (h > 0) {
    return `${h}h ${m}m ${s}s`;
  }

  return `${m}m ${s}s`;
}

function getErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unable to fetch circuit breaker status.";
  }

  if (error.message.toLowerCase().includes("timed out")) {
    return "Circuit breaker status request timed out. Please retry.";
  }

  return error.message || "Unable to fetch circuit breaker status.";
}

export function CircuitBreakerCard({ address }: { address: string }) {
  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useProtocolStatus(address, { refetchInterval: 10_000 });
  const {
    data: alertHistory,
    error: alertHistoryError,
    refetch: refetchAlertHistory,
    isFetching: isFetchingAlertHistory,
  } = useAlerts({ page: 1, limit: 20, protocol: address, refetchInterval: 12_000 });
  const wallet = useWallet();

  const [now, setNow] = useState(Math.floor(Date.now() / 1000));

  useEffect(() => {
    const timer = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000);
    return () => clearInterval(timer);
  }, []);

  const paused = Boolean(data?.circuitBreaker?.paused);
  const pausedAt = data?.circuitBreaker?.pausedAt ?? 0;
  const cooldownEnds = data?.circuitBreaker?.cooldownEnds ?? 0;
  const remaining = Math.max(0, cooldownEnds - now);

  const timeline = useMemo(() => {
    const events = (alertHistory?.items ?? []).slice(0, 5).map((alert) => ({
      id: alert.id,
      label: `${alert.threatLevel} alert • ${alert.action.replace(/_/g, " ")}`,
      timestamp: alert.createdAt,
    }));

    if (paused && pausedAt > 0) {
      events.unshift({
        id: "paused",
        label: "Circuit breaker engaged",
        timestamp: pausedAt,
      });
    }

    return events.sort((left, right) => right.timestamp - left.timestamp);
  }, [alertHistory, paused, pausedAt]);

  const errorMessage = getErrorMessage(error);
  const alertTimelineErrorMessage = getErrorMessage(alertHistoryError);

  return (
    <section
      className={clsx(
        "rounded-lg border p-4",
        paused
          ? "border-red-500/40 bg-red-500/20"
          : "border-border-subtle bg-bg-surface"
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold text-white">Circuit Breaker Status</h3>
        <span
          className={clsx(
            "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium",
            paused ? "bg-red-500/20 text-red-300" : "bg-green-500/20 text-green-300"
          )}
        >
          {paused ? <Lock className="h-3.5 w-3.5" /> : <Unlock className="h-3.5 w-3.5" />}
          {paused ? "PAUSED" : "ACTIVE"}
        </span>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <LoadingSkeleton className="h-16" />
          <LoadingSkeleton className="h-20" />
          <LoadingSkeleton className="h-28" />
        </div>
      )}

      {error && !isLoading && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/20 px-4 py-3">
          <p className="text-sm text-red-300">{errorMessage}</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-2 inline-flex items-center gap-1 rounded border border-red-500/50 px-2 py-1 text-xs text-red-200 transition hover:bg-red-500/20"
            disabled={isFetching}
          >
            <RefreshCw className={clsx("h-3.5 w-3.5", isFetching && "animate-spin")} />
            Retry
          </button>
        </div>
      )}

      {!isLoading && !error && !data && (
        <div className="rounded-lg border border-border-subtle bg-bg-elevated px-4 py-8 text-center">
          <p className="text-sm text-text-secondary">No circuit breaker data available.</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded border border-border-subtle px-3 py-1.5 text-xs text-text-secondary transition hover:bg-bg-elevated"
          >
            Refresh
          </button>
        </div>
      )}

      {!isLoading && !error && data && (
        <div className="space-y-4">
          {!paused && (
            <div className="rounded-lg border border-border-subtle bg-bg-elevated p-3">
              <p className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white">
                <StatusDot status="low" animate />
                Protocol Operating Normally
              </p>
              <p className="text-sm text-text-muted">
                Last check: {new Date((data.timestamp ?? now) * 1000).toLocaleString()}
              </p>
            </div>
          )}

          {paused && (
            <div className="space-y-3 rounded-lg border border-red-500/40 bg-red-500/20 p-3">
              <p className="text-2xl font-bold tracking-wide text-red-300">PAUSED</p>
              <p className="text-sm text-red-100">
                {data.circuitBreaker?.reason || "No pause reason was provided."}
              </p>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <p className="inline-flex items-center gap-2 text-red-100">
                  <AlertTriangle className="h-4 w-4" />
                  Paused: {pausedAt > 0 ? new Date(pausedAt * 1000).toLocaleString() : "Unknown"}
                </p>
                <p className="inline-flex items-center gap-2 text-red-100">
                  <Timer className="h-4 w-4" />
                  Cooldown: {remaining > 0 ? formatCountdown(remaining) : "Completed"}
                </p>
              </div>

              <button
                type="button"
                disabled={!wallet.isConnected || remaining > 0}
                className="rounded border border-red-500/50 bg-red-500/20 px-3 py-2 text-sm font-medium text-red-200 transition hover:bg-red-500/30 disabled:cursor-not-allowed disabled:opacity-40"
                title="Resume requires authorized wallet and on-chain transaction."
              >
                Resume Protocol
              </button>
            </div>
          )}

          <div className="rounded-lg border border-border-subtle bg-bg-elevated p-3">
            <div className="mb-3 flex items-center justify-between">
              <p className="inline-flex items-center gap-2 text-sm font-medium text-white">
                <ShieldCheck className="h-4 w-4 text-blue-400" />
                Recent Breaker Timeline
              </p>
              <button
                type="button"
                onClick={() => refetchAlertHistory()}
                disabled={isFetchingAlertHistory}
                className="rounded border border-border-subtle p-1.5 text-text-secondary transition hover:bg-bg-elevated"
                aria-label="Refresh breaker timeline"
              >
                <RefreshCw className={clsx("h-3.5 w-3.5", isFetchingAlertHistory && "animate-spin")} />
              </button>
            </div>

            {alertHistoryError && (
              <div className="mb-3 rounded border border-red-500/40 bg-red-500/20 px-3 py-2 text-xs text-red-200">
                {alertTimelineErrorMessage}
              </div>
            )}

            <ul className="space-y-2">
              {timeline.length === 0 ? (
                <li className="rounded border border-border-subtle bg-bg-surface px-3 py-2 text-sm text-text-muted">
                  No breaker events yet.
                </li>
              ) : (
                timeline.map((event) => (
                  <li
                    key={event.id}
                    className="flex items-center justify-between rounded border border-border-subtle bg-bg-surface px-3 py-2"
                  >
                    <p className="text-sm text-text-primary">{event.label}</p>
                    <time
                      className="text-xs text-text-muted"
                      title={new Date(event.timestamp * 1000).toLocaleString()}
                    >
                      {formatRelativeTime(event.timestamp)}
                    </time>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
