import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Header } from "./components/layout/Header";
import { ThreatDashboard } from "./components/dashboard/ThreatDashboard";
import { SystemStatus } from "./components/dashboard/SystemStatus";
import { SentinelCard } from "./components/sentinels/SentinelCard";
import { ConsensusView } from "./components/sentinels/ConsensusView";
import { CircuitBreakerStatus } from "./components/protocol/CircuitBreakerStatus";
import { Loading } from "./components/common/Loading";
import { useSentinels } from "./hooks/useSentinels";
import { api } from "./lib/api";

export default function App() {
  const { data, isLoading, error } = useSentinels();
  const didAutoScan = useRef(false);
  const [scanning, setScanning] = useState(false);

  const scanMutation = useMutation({
    mutationFn: () =>
      api.runDetection("0x0000000000000000000000000000000000000001"),
    onMutate: () => setScanning(true),
    onSettled: () => setScanning(false),
  });

  // Auto-trigger one detection on first load so dashboard has data
  useEffect(() => {
    if (!didAutoScan.current) {
      didAutoScan.current = true;
      scanMutation.mutate();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const hasData = data?.assessments && data.assessments.length > 0;

  return (
    <div className="min-h-screen bg-aegis-dark">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 text-amber-400 text-sm">
            Unable to connect to AEGIS API. Make sure the agent and API services
            are running.
          </div>
        )}

        {isLoading && !data ? (
          <Loading text="Connecting to AEGIS network..." />
        ) : scanning && !hasData ? (
          <Loading text="Running initial sentinel scan..." />
        ) : (
          <div className="space-y-6">
            {/* Hero threat indicator */}
            <div className="relative">
              <ThreatDashboard
                threatLevel={data?.consensus?.final_threat_level ?? "NONE"}
                consensusReached={data?.consensus?.consensus_reached ?? false}
                agreementRatio={data?.consensus?.agreement_ratio ?? 0}
              />
              <button
                onClick={() => scanMutation.mutate()}
                disabled={scanning}
                className="absolute top-4 right-4 px-3 py-1.5 text-xs font-semibold rounded-lg border border-aegis-accent/30 bg-aegis-accent/10 text-aegis-accent hover:bg-aegis-accent/20 transition disabled:opacity-50"
              >
                {scanning ? "Scanning..." : "Run Scan"}
              </button>
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left: Sentinel Cards */}
              <div className="lg:col-span-2 space-y-4">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Sentinel Network
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {hasData ? (
                    data.assessments.map((assessment) => (
                      <SentinelCard
                        key={assessment.sentinel_id}
                        assessment={assessment}
                      />
                    ))
                  ) : (
                    [0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-aegis-border bg-aegis-card p-5 h-48 animate-pulse"
                      />
                    ))
                  )}
                </div>

                {/* Consensus panel */}
                {data?.consensus && (
                  <ConsensusView consensus={data.consensus} />
                )}
              </div>

              {/* Right: Status sidebar */}
              <div className="space-y-4">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Infrastructure
                </h2>
                <CircuitBreakerStatus paused={false} />
                <SystemStatus />

                {/* Chainlink services badges */}
                <div className="rounded-xl border border-aegis-border bg-aegis-card p-5">
                  <h3 className="font-semibold text-sm mb-3">
                    Chainlink Services
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "CRE",
                      "Data Feeds",
                      "Automation",
                      "VRF",
                      "CCIP",
                    ].map((svc) => (
                      <span
                        key={svc}
                        className="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider bg-aegis-accent/10 text-aegis-accent border border-aegis-accent/20"
                      >
                        {svc}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
