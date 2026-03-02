import { useState, useEffect, useCallback } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  AlertTriangle,
  Shield,
  Activity,
  Zap,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import clsx from "clsx";
import { api } from "../../lib/api";
import { ThreatBadge } from "../common/ThreatBadge";

type SentinelAssessment = {
  sentinel_id: number;
  sentinel_type: string;
  threat_level: string;
  confidence: number;
  details: string;
  indicators: string[];
  recommended_action: string;
};

type Consensus = {
  consensus_reached: boolean;
  final_threat_level: string;
  agreement_ratio: number;
  participating_sentinels: number;
  vote_breakdown: Record<string, number>;
  recommended_action: string;
};

type StepData = {
  step_number: number;
  timestamp_offset_seconds: number;
  title: string;
  description: string;
  metrics: Record<string, unknown>;
  sentinel_assessments: SentinelAssessment[];
  consensus: Consensus | null;
  action_taken: string;
  is_critical: boolean;
};

type ScenarioData = {
  scenario_id: string;
  scenario_name: string;
  description: string;
  protocol_name: string;
  protocol_address: string;
  attack_type: string;
  total_steps: number;
  steps: StepData[];
};

function formatUSD(value: unknown): string {
  if (typeof value !== "number") return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: value >= 1_000_000 ? "compact" : "standard",
    maximumFractionDigits: 0,
  }).format(value);
}

function MetricBox({
  label,
  value,
  variant = "default",
}: {
  label: string;
  value: string;
  variant?: "default" | "danger" | "success" | "warning";
}) {
  return (
    <div
      className={clsx(
        "rounded-lg border px-3 py-2",
        variant === "danger" && "border-red-500/30 bg-red-500/10",
        variant === "success" && "border-green-500/30 bg-green-500/10",
        variant === "warning" && "border-yellow-500/30 bg-yellow-500/10",
        variant === "default" && "border-border-subtle bg-bg-elevated",
      )}
    >
      <p className="text-xs text-text-muted">{label}</p>
      <p
        className={clsx(
          "text-sm font-semibold",
          variant === "danger" && "text-red-400",
          variant === "success" && "text-green-400",
          variant === "warning" && "text-yellow-400",
          variant === "default" && "text-text-primary",
        )}
      >
        {value}
      </p>
    </div>
  );
}

function SentinelCard({ assessment }: { assessment: SentinelAssessment }) {
  const iconMap: Record<string, React.ReactNode> = {
    LIQUIDITY: <Activity className="h-4 w-4" />,
    ORACLE: <Zap className="h-4 w-4" />,
    GOVERNANCE: <Shield className="h-4 w-4" />,
  };

  return (
    <div className="rounded-lg border border-border-subtle bg-bg-elevated p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-text-muted">
            {iconMap[assessment.sentinel_type] || <AlertTriangle className="h-4 w-4" />}
          </span>
          <span className="text-sm font-medium text-text-primary">
            {assessment.sentinel_type} Sentinel
          </span>
        </div>
        <ThreatBadge level={assessment.threat_level as any} variant="compact" />
      </div>
      <p className="mb-2 text-xs text-text-secondary">{assessment.details}</p>
      {assessment.indicators.length > 0 && (
        <ul className="space-y-0.5">
          {assessment.indicators.map((ind, i) => (
            <li key={i} className="flex items-start gap-1.5 text-xs text-text-muted">
              <ChevronRight className="mt-0.5 h-3 w-3 flex-shrink-0" />
              <span>{ind}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-text-muted">
          Confidence: {(assessment.confidence * 100).toFixed(0)}%
        </span>
        <span
          className={clsx(
            "font-medium",
            assessment.recommended_action === "CIRCUIT_BREAKER" && "text-red-400",
            assessment.recommended_action === "ALERT" && "text-yellow-400",
            assessment.recommended_action === "NONE" && "text-green-400",
          )}
        >
          {assessment.recommended_action.replace(/_/g, " ")}
        </span>
      </div>
    </div>
  );
}

export function EulerDemo() {
  const [scenario, setScenario] = useState<ScenarioData | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const startMutation = useMutation({
    mutationFn: () => api.startEulerReplay() as Promise<ScenarioData>,
    onSuccess: (data) => {
      setScenario(data);
      setCurrentStep(0);
      setIsPlaying(false);
    },
  });

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying || !scenario) return;
    if (currentStep >= scenario.total_steps - 1) {
      setIsPlaying(false);
      return;
    }

    const stepData = scenario.steps[currentStep];
    const nextStepData = scenario.steps[currentStep + 1];
    const delay = (nextStepData.timestamp_offset_seconds - stepData.timestamp_offset_seconds) * 100; // 10x speed

    const timer = setTimeout(
      () => {
        setCurrentStep((s) => Math.min(s + 1, scenario.total_steps - 1));
      },
      Math.max(delay, 500),
    );

    return () => clearTimeout(timer);
  }, [isPlaying, currentStep, scenario]);

  const handleStart = useCallback(() => {
    startMutation.mutate();
  }, [startMutation]);

  const handleReset = useCallback(() => {
    setScenario(null);
    setCurrentStep(0);
    setIsPlaying(false);
  }, []);

  const stepData = scenario?.steps[currentStep];

  // Not started
  if (!scenario) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center rounded-lg border border-border-subtle bg-bg-surface p-8">
        <div className="mb-6 rounded-full bg-red-500/10 p-6">
          <AlertTriangle className="h-12 w-12 text-red-500" />
        </div>
        <h2 className="mb-2 text-2xl font-bold text-text-primary">Euler Finance Exploit Replay</h2>
        <p className="mb-6 max-w-md text-center text-text-secondary">
          Experience how AEGIS would have detected and mitigated the March 2023 Euler Finance hack
          ($197M). Watch the 9-step attack unfold and see real-time sentinel responses.
        </p>
        <button
          type="button"
          onClick={handleStart}
          disabled={startMutation.isPending}
          className="btn-primary flex items-center gap-2 px-6 py-3"
        >
          {startMutation.isPending ? (
            <span className="animate-pulse">Loading scenario...</span>
          ) : (
            <>
              <Play className="h-5 w-5" />
              Start Demo
            </>
          )}
        </button>
        {startMutation.isError && (
          <p className="mt-4 text-sm text-red-400">
            Failed to load scenario. Make sure the API is running.
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border-subtle bg-bg-surface p-4">
        <div>
          <h2 className="text-lg font-bold text-text-primary">{scenario.scenario_name}</h2>
          <p className="text-sm text-text-muted">
            {scenario.protocol_name} • {scenario.attack_type.replace(/_/g, " ")} Attack
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
            disabled={currentStep === 0}
            className="btn-ghost p-2"
            aria-label="Previous step"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>

          <button
            type="button"
            onClick={() => setIsPlaying((p) => !p)}
            className={clsx("btn-secondary gap-2 px-4", isPlaying && "bg-accent/20")}
          >
            {isPlaying ? (
              <>
                <Pause className="h-4 w-4" />
                Pause
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Play
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => setCurrentStep((s) => Math.min(scenario.total_steps - 1, s + 1))}
            disabled={currentStep >= scenario.total_steps - 1}
            className="btn-ghost p-2"
            aria-label="Next step"
          >
            <ChevronRight className="h-5 w-5" />
          </button>

          <button
            type="button"
            onClick={handleReset}
            className="btn-ghost p-2"
            aria-label="Reset demo"
          >
            <RotateCcw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Progress */}
      <div className="rounded-lg border border-border-subtle bg-bg-surface p-4">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-text-muted">
            Step {currentStep + 1} of {scenario.total_steps}
          </span>
          <span className="text-text-muted">
            T+{stepData?.timestamp_offset_seconds.toFixed(0)}s
          </span>
        </div>
        <div className="flex gap-1">
          {scenario.steps.map((step, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setCurrentStep(idx)}
              className={clsx(
                "h-2 flex-1 rounded-full transition-all",
                idx < currentStep && "bg-accent",
                idx === currentStep && step.is_critical && "bg-red-500 animate-pulse",
                idx === currentStep && !step.is_critical && "bg-accent",
                idx > currentStep && "bg-border-subtle",
              )}
              aria-label={`Go to step ${idx + 1}`}
            />
          ))}
        </div>
      </div>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        {stepData && (
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="space-y-4"
          >
            {/* Step Title */}
            <div
              className={clsx(
                "rounded-lg border p-4",
                stepData.is_critical
                  ? "border-red-500/50 bg-red-500/10"
                  : "border-border-subtle bg-bg-surface",
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">{stepData.title}</h3>
                  <p className="mt-1 text-sm text-text-secondary">{stepData.description}</p>
                </div>
                {stepData.is_critical && (
                  <div className="flex items-center gap-2 rounded-full bg-red-500/20 px-3 py-1">
                    <AlertTriangle className="h-4 w-4 text-red-400" />
                    <span className="text-sm font-medium text-red-400">CRITICAL</span>
                  </div>
                )}
              </div>
            </div>

            {/* Metrics */}
            {Object.keys(stepData.metrics).length > 0 && (
              <div className="rounded-lg border border-border-subtle bg-bg-surface p-4">
                <h4 className="mb-3 text-sm font-semibold text-text-primary">Protocol Metrics</h4>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
                  {stepData.metrics.tvl_usd !== undefined && (
                    <MetricBox
                      label="TVL"
                      value={formatUSD(stepData.metrics.tvl_usd)}
                      variant={
                        (stepData.metrics.tvl_drop_percent as number) >= 15 ? "danger" : "default"
                      }
                    />
                  )}
                  {stepData.metrics.tvl_drop_percent !== undefined && (
                    <MetricBox
                      label="TVL Change"
                      value={`-${stepData.metrics.tvl_drop_percent}%`}
                      variant="danger"
                    />
                  )}
                  {stepData.metrics.tvl_protected_usd !== undefined && (
                    <MetricBox
                      label="Protected"
                      value={formatUSD(stepData.metrics.tvl_protected_usd)}
                      variant="success"
                    />
                  )}
                  {stepData.metrics.tvl_lost_usd !== undefined && (
                    <MetricBox
                      label="Lost"
                      value={formatUSD(stepData.metrics.tvl_lost_usd)}
                      variant="danger"
                    />
                  )}
                  {stepData.metrics.flash_loan_amount_usd !== undefined && (
                    <MetricBox
                      label="Flash Loan"
                      value={formatUSD(stepData.metrics.flash_loan_amount_usd)}
                      variant="warning"
                    />
                  )}
                  {stepData.metrics.detection_latency_seconds !== undefined && (
                    <MetricBox
                      label="Detection Time"
                      value={`${stepData.metrics.detection_latency_seconds}s`}
                      variant="success"
                    />
                  )}
                  {stepData.metrics.loss_prevention_percent !== undefined && (
                    <MetricBox
                      label="Loss Prevented"
                      value={`${stepData.metrics.loss_prevention_percent}%`}
                      variant="success"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Sentinel Assessments */}
            {stepData.sentinel_assessments.length > 0 && (
              <div className="rounded-lg border border-border-subtle bg-bg-surface p-4">
                <h4 className="mb-3 text-sm font-semibold text-text-primary">
                  Sentinel Assessments
                </h4>
                <div className="grid gap-3 md:grid-cols-3">
                  {stepData.sentinel_assessments.map((assessment) => (
                    <SentinelCard key={assessment.sentinel_id} assessment={assessment} />
                  ))}
                </div>
              </div>
            )}

            {/* Consensus */}
            {stepData.consensus && (
              <div
                className={clsx(
                  "rounded-lg border p-4",
                  stepData.consensus.final_threat_level === "CRITICAL"
                    ? "border-red-500/50 bg-red-500/10"
                    : stepData.consensus.final_threat_level === "HIGH"
                      ? "border-orange-500/50 bg-orange-500/10"
                      : "border-border-subtle bg-bg-surface",
                )}
              >
                <h4 className="mb-3 text-sm font-semibold text-text-primary">Consensus Result</h4>
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-text-muted">Level:</span>
                    <ThreatBadge
                      level={stepData.consensus.final_threat_level as any}
                      variant="default"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-text-muted">Agreement:</span>
                    <span className="font-semibold text-text-primary">
                      {(stepData.consensus.agreement_ratio * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-text-muted">Action:</span>
                    <span
                      className={clsx(
                        "font-semibold",
                        stepData.consensus.recommended_action === "CIRCUIT_BREAKER" &&
                          "text-red-400",
                        stepData.consensus.recommended_action === "ALERT" && "text-yellow-400",
                      )}
                    >
                      {stepData.consensus.recommended_action.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Action Taken */}
            <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
              <h4 className="mb-1 text-sm font-semibold text-accent">Action Taken</h4>
              <p className="text-sm text-text-primary">{stepData.action_taken}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
