import { Lock, Unlock } from "lucide-react";

export function CircuitBreakerStatus({
  paused,
  reason,
  cooldownEnds,
}: {
  paused: boolean;
  reason?: string;
  cooldownEnds?: number;
}) {
  const now = Math.floor(Date.now() / 1000);
  const remaining = cooldownEnds ? Math.max(0, cooldownEnds - now) : 0;

  return (
    <div
      className={`rounded-xl border p-5 ${
        paused
          ? "border-red-500/30 bg-red-500/5"
          : "border-aegis-border bg-aegis-card"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">Circuit Breaker</h3>
        {paused ? (
          <div className="flex items-center gap-1.5 text-red-400 text-xs font-bold">
            <Lock className="w-4 h-4" />
            PAUSED
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-bold">
            <Unlock className="w-4 h-4" />
            ACTIVE
          </div>
        )}
      </div>

      {paused && (
        <div className="space-y-2 text-xs">
          {reason && <p className="text-gray-400">{reason}</p>}
          {remaining > 0 && (
            <p className="text-amber-400">
              Cooldown: {Math.floor(remaining / 60)}m {remaining % 60}s
              remaining
            </p>
          )}
        </div>
      )}

      {!paused && (
        <p className="text-xs text-gray-500">
          Protocol is operating normally. Circuit breaker will trigger on 2/3
          CRITICAL consensus.
        </p>
      )}
    </div>
  );
}
