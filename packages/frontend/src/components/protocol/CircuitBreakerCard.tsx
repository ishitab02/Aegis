import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Lock, ShieldCheck, Timer, Unlock } from "lucide-react";
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

export function CircuitBreakerCard({ address }: { address: string }) {
  const { data, isLoading, error } = useProtocolStatus(address, { refetchInterval: 10_000 });
  const { data: alertHistory } = useAlerts({ page: 1, limit: 20, protocol: address, refetchInterval: 12_000 });
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

  return (
    <section
      className={`rounded-xl border p-4 transition ${
        paused
          ? "border-[#ef4444] bg-[#7f1d1d]/20"
          : "border-[var(--border-subtle)] bg-[var(--bg-surface)]"
      }`}
    >
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Circuit Breaker Status</h3>
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
            paused ? "bg-[#7f1d1d] text-[#fca5a5]" : "bg-[#14532d] text-[#86efac]"
          }`}
        >
          {paused ? <Lock className="h-3.5 w-3.5" /> : <Unlock className="h-3.5 w-3.5" />}
          {paused ? "PAUSED" : "NORMAL"}
        </span>
      </div>

      {isLoading && <LoadingSkeleton lines={5} />}
      {error && <p className="text-sm text-[#fca5a5]">Unable to fetch circuit breaker status.</p>}

      {!isLoading && !error && (
        <div className="space-y-4">
          {!paused && (
            <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
              <p className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-[var(--text-primary)]">
                <StatusDot status="low" animate />
                Protocol Operating Normally
              </p>
              <p className="text-sm text-[var(--text-secondary)]">
                Last check: {new Date((data?.timestamp ?? now) * 1000).toLocaleString()}
              </p>
            </div>
          )}

          {paused && (
            <div className="space-y-3 rounded-lg border border-[#7f1d1d] bg-[#7f1d1d]/30 p-3">
              <p className="text-2xl font-bold tracking-wide text-[#fca5a5]">PAUSED</p>
              <p className="text-sm text-[#fecaca]">{data?.circuitBreaker?.reason || "No pause reason was provided."}</p>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <p className="inline-flex items-center gap-2 text-[#fecaca]">
                  <AlertTriangle className="h-4 w-4" />
                  Paused: {pausedAt > 0 ? new Date(pausedAt * 1000).toLocaleString() : "Unknown"}
                </p>
                <p className="inline-flex items-center gap-2 text-[#fecaca]">
                  <Timer className="h-4 w-4" />
                  Cooldown: {remaining > 0 ? formatCountdown(remaining) : "Completed"}
                </p>
              </div>

              <button
                type="button"
                disabled={!wallet.isConnected || remaining > 0}
                className="rounded-lg border border-[#ef4444] bg-[#ef4444]/20 px-3 py-2 text-sm font-medium text-[#fca5a5] transition hover:bg-[#ef4444]/35 disabled:cursor-not-allowed disabled:opacity-40"
                title="Resume requires authorized wallet and on-chain transaction."
              >
                Resume Protocol
              </button>
            </div>
          )}

          <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
            <p className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-[var(--text-primary)]">
              <ShieldCheck className="h-4 w-4 text-[var(--accent)]" />
              Recent Breaker Timeline
            </p>

            <ul className="space-y-2">
              {timeline.length === 0 && <li className="text-sm text-[var(--text-muted)]">No breaker events yet.</li>}
              {timeline.map((event) => (
                <li key={event.id} className="flex items-center justify-between rounded-md border border-[var(--border-subtle)] bg-[var(--bg-surface)] px-3 py-2">
                  <p className="text-sm text-[var(--text-secondary)]">{event.label}</p>
                  <time className="text-xs text-[var(--text-muted)]" title={new Date(event.timestamp * 1000).toLocaleString()}>
                    {formatRelativeTime(event.timestamp)}
                  </time>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
