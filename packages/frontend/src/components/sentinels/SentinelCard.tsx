import { Droplets, Eye, ShieldCheck } from "lucide-react";
import type { ThreatAssessment } from "../../types";
import { ThreatBadge } from "../common/ThreatBadge";
import { SENTINEL_LABELS } from "../../lib/constants";

const ICONS: Record<string, typeof Droplets> = {
  LIQUIDITY: Droplets,
  ORACLE: Eye,
  GOVERNANCE: ShieldCheck,
};

export function SentinelCard({
  assessment,
}: {
  assessment: ThreatAssessment;
}) {
  const Icon = ICONS[assessment.sentinel_type] ?? ShieldCheck;
  const label =
    SENTINEL_LABELS[assessment.sentinel_type] ?? assessment.sentinel_type;

  return (
    <div className="rounded-xl border border-aegis-border bg-aegis-card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-aegis-accent/10">
            <Icon className="w-5 h-5 text-aegis-accent" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">{label}</h3>
            <p className="text-xs text-gray-500">{assessment.sentinel_id}</p>
          </div>
        </div>
        <ThreatBadge level={assessment.threat_level} />
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-400">Confidence</span>
          <span className="font-mono">
            {(assessment.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-1.5">
          <div
            className="bg-aegis-accent h-1.5 rounded-full transition-all"
            style={{ width: `${assessment.confidence * 100}%` }}
          />
        </div>

        <p className="text-xs text-gray-400 mt-2 line-clamp-2">
          {assessment.details}
        </p>

        {assessment.indicators.length > 0 && (
          <div className="mt-2 space-y-1">
            {assessment.indicators.map((ind, i) => (
              <p key={i} className="text-xs text-amber-400/80">
                {ind}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
