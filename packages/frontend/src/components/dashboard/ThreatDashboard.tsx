import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, ShieldAlert, ShieldOff, Shield } from "lucide-react";
import clsx from "clsx";
import type { ThreatLevel } from "../../types";

const ICONS: Record<ThreatLevel, typeof CheckCircle> = {
  NONE: CheckCircle,
  LOW: Shield,
  MEDIUM: AlertTriangle,
  HIGH: ShieldAlert,
  CRITICAL: ShieldOff,
};

const LABELS: Record<ThreatLevel, string> = {
  NONE: "All Systems Secure",
  LOW: "Low Risk Detected",
  MEDIUM: "Elevated Threat",
  HIGH: "High Risk Alert",
  CRITICAL: "CRITICAL THREAT",
};

const SUBLABELS: Record<ThreatLevel, string> = {
  NONE: "No threats detected across monitored protocols",
  LOW: "Minor anomalies detected, monitoring continues",
  MEDIUM: "Elevated activity requires attention",
  HIGH: "Significant threat detected, action recommended",
  CRITICAL: "Immediate action required — Circuit breaker engaged",
};

function getThreatGradient(level: ThreatLevel): string {
  switch (level) {
    case "CRITICAL":
      return "from-threat-critical/20 via-threat-critical/5 to-transparent";
    case "HIGH":
      return "from-threat-high/15 via-threat-high/5 to-transparent";
    case "MEDIUM":
      return "from-threat-medium/10 via-threat-medium/5 to-transparent";
    case "LOW":
      return "from-success/10 via-success/5 to-transparent";
    default:
      return "from-success/10 via-success/5 to-transparent";
  }
}

function getThreatColor(level: ThreatLevel): string {
  switch (level) {
    case "CRITICAL":
      return "text-threat-critical";
    case "HIGH":
      return "text-threat-high";
    case "MEDIUM":
      return "text-threat-medium";
    case "LOW":
      return "text-success";
    default:
      return "text-success";
  }
}

function getThreatBorder(level: ThreatLevel): string {
  switch (level) {
    case "CRITICAL":
      return "border-threat-critical/50";
    case "HIGH":
      return "border-threat-high/40";
    case "MEDIUM":
      return "border-threat-medium/30";
    default:
      return "border-success/30";
  }
}

type VoteEntry = {
  sentinel_id?: string;
  threat_level?: string;
  confidence?: number;
};

export function ThreatDashboard({
  threatLevel,
  consensusReached,
  agreementRatio,
  votes,
}: {
  threatLevel: ThreatLevel;
  consensusReached: boolean;
  agreementRatio: number;
  votes?: VoteEntry[];
}) {
  const Icon = ICONS[threatLevel];
  const isCritical = threatLevel === "CRITICAL";
  const isHigh = threatLevel === "HIGH";

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        "relative overflow-hidden rounded-2xl border p-8 text-center",
        getThreatBorder(threatLevel),
        "bg-bg-surface",
      )}
    >
      {/* Animated gradient background */}
      <div
        className={clsx(
          "absolute inset-0 bg-gradient-to-b",
          getThreatGradient(threatLevel),
          (isCritical || isHigh) && "animate-pulse",
        )}
      />

      {/* Radial glow for critical */}
      {isCritical && (
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(239,68,68,0.15)_0%,transparent_70%)]" />
      )}

      <div className="relative">
        {/* Icon */}
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
          className="mb-4"
        >
          <Icon
            className={clsx(
              "mx-auto h-16 w-16",
              getThreatColor(threatLevel),
              isCritical && "animate-pulse",
            )}
            strokeWidth={1.5}
          />
        </motion.div>

        {/* Threat level label */}
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className={clsx("mb-2 text-3xl font-bold tracking-tight", getThreatColor(threatLevel))}
        >
          {LABELS[threatLevel]}
        </motion.h2>

        {/* Sublabel */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-4 text-sm text-text-secondary"
        >
          {SUBLABELS[threatLevel]}
        </motion.p>

        {/* Consensus indicator */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="inline-flex items-center gap-3 rounded-full border border-border-subtle bg-bg-elevated px-4 py-2"
        >
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span
                className={clsx(
                  "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
                  consensusReached ? "bg-success" : "bg-text-muted",
                )}
              />
              <span
                className={clsx(
                  "relative inline-flex h-2 w-2 rounded-full",
                  consensusReached ? "bg-success" : "bg-text-muted",
                )}
              />
            </span>
            <span className="text-sm text-text-secondary">
              {consensusReached ? "Consensus reached" : "Monitoring active"}
            </span>
          </div>

          {consensusReached && (
            <>
              <span className="h-4 w-px bg-border-subtle" />
              <span className="text-sm font-medium text-text-primary">
                {(() => {
                  if (!votes || votes.length === 0) {
                    return `${(agreementRatio * 100).toFixed(0)}% agreement`;
                  }
                  const agreeing = votes.filter(
                    (v) => v.threat_level?.toUpperCase() === threatLevel,
                  ).length;
                  return `${agreeing}/${votes.length} sentinels agree`;
                })()}
              </span>
            </>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}
