import { AlertTriangle, CheckCircle, ShieldAlert, ShieldOff } from "lucide-react";
import type { ThreatLevel } from "../../types";
import { THREAT_COLORS } from "../../lib/constants";

const ICONS: Record<ThreatLevel, typeof CheckCircle> = {
  NONE: CheckCircle,
  LOW: CheckCircle,
  MEDIUM: AlertTriangle,
  HIGH: ShieldAlert,
  CRITICAL: ShieldOff,
};

const LABELS: Record<ThreatLevel, string> = {
  NONE: "All Clear",
  LOW: "Low Risk",
  MEDIUM: "Elevated",
  HIGH: "High Risk",
  CRITICAL: "CRITICAL",
};

export function ThreatDashboard({
  threatLevel,
  consensusReached,
  agreementRatio,
}: {
  threatLevel: ThreatLevel;
  consensusReached: boolean;
  agreementRatio: number;
}) {
  const Icon = ICONS[threatLevel];
  const color = THREAT_COLORS[threatLevel];
  const isCritical = threatLevel === "CRITICAL";

  return (
    <div
      className={`relative rounded-2xl border p-8 text-center overflow-hidden ${
        isCritical
          ? "border-red-500/50 bg-red-500/5"
          : "border-aegis-border bg-aegis-card"
      }`}
    >
      {isCritical && (
        <div className="absolute inset-0 bg-red-500/5 animate-pulse" />
      )}

      <div className="relative">
        <Icon
          className="w-16 h-16 mx-auto mb-4"
          style={{ color }}
          strokeWidth={1.5}
        />
        <h2
          className="text-3xl font-black tracking-tight mb-1"
          style={{ color }}
        >
          {LABELS[threatLevel]}
        </h2>
        <p className="text-gray-400 text-sm">
          {consensusReached
            ? `Consensus reached (${(agreementRatio * 100).toFixed(0)}% agreement)`
            : "Sentinel monitoring active"}
        </p>
      </div>
    </div>
  );
}
