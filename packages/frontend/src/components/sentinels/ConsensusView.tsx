import type { ConsensusResult } from "../../types";
import { ThreatBadge } from "../common/ThreatBadge";
import { THREAT_COLORS } from "../../lib/constants";

export function ConsensusView({ consensus }: { consensus: ConsensusResult }) {
  return (
    <div className="rounded-xl border border-aegis-border bg-aegis-card p-5">
      <h3 className="font-semibold text-sm mb-4">Sentinel Consensus</h3>

      <div className="flex items-center gap-3 mb-4">
        {consensus.votes.map((vote, i) => (
          <div
            key={i}
            className="flex-1 rounded-lg border border-aegis-border p-3 text-center"
          >
            <div
              className="w-3 h-3 rounded-full mx-auto mb-2"
              style={{
                backgroundColor: THREAT_COLORS[vote.threat_level],
              }}
            />
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">
              {vote.sentinel_id.split("-")[0]}
            </p>
            <ThreatBadge level={vote.threat_level} />
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs border-t border-aegis-border pt-3">
        <div className="flex items-center gap-2">
          <span className="text-gray-400">Result:</span>
          <ThreatBadge level={consensus.final_threat_level} />
        </div>
        <div className="text-gray-400">
          {consensus.consensus_reached ? (
            <span className="text-emerald-400">
              Consensus ({(consensus.agreement_ratio * 100).toFixed(0)}%)
            </span>
          ) : (
            <span className="text-amber-400">No consensus</span>
          )}
        </div>
      </div>

      {consensus.action_recommended !== "NONE" && (
        <div className="mt-3 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
          Action: {consensus.action_recommended}
        </div>
      )}
    </div>
  );
}
