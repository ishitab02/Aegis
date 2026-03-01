import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronLeft, ChevronRight, Link as LinkIcon, Sparkles } from "lucide-react";
import { createPublicClient, http } from "viem";
import { mainnet } from "viem/chains";
import { api } from "../../lib/api";

const ENS_CLIENT = createPublicClient({
  chain: mainnet,
  transport: http(),
});

const ETH_ADDRESS_REGEX = /^0x[a-fA-F0-9]{40}$/;

const steps = ["Protocol", "Thresholds", "Notifications", "Review"];

const protocolSignatures: Array<{ id: string; label: string; prefix?: string; includes?: string[] }> = [
  { id: "aave-v3", label: "Aave V3", includes: ["aave"] },
  { id: "uniswap-v3", label: "Uniswap V3", includes: ["uni", "swap"] },
  { id: "compound-v3", label: "Compound V3", includes: ["comp"] },
  { id: "curve", label: "Curve", includes: ["curve"] },
  { id: "custom", label: "Custom Protocol" },
];

type FormState = {
  address: string;
  name: string;
  detectedType: string;
  alertThreshold: number;
  breakerThreshold: number;
  telegramEnabled: boolean;
  telegramChannel: string;
  webhookUrl: string;
};

function detectProtocolType(address: string, name: string): string {
  const normalized = `${address} ${name}`.toLowerCase();

  const matched = protocolSignatures.find((signature) => {
    if (signature.prefix && normalized.startsWith(signature.prefix)) {
      return true;
    }
    if (signature.includes?.some((segment) => normalized.includes(segment))) {
      return true;
    }
    return false;
  });

  return matched?.label ?? "Custom Protocol";
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

interface RegisterProtocolProps {
  onSuccess?: () => void;
}

export function RegisterProtocol({ onSuccess }: RegisterProtocolProps = {}) {
  const queryClient = useQueryClient();

  const [step, setStep] = useState(0);
  const [isResolvingEns, setIsResolvingEns] = useState(false);
  const [banner, setBanner] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const [form, setForm] = useState<FormState>({
    address: "",
    name: "",
    detectedType: "Custom Protocol",
    alertThreshold: 10,
    breakerThreshold: 20,
    telegramEnabled: false,
    telegramChannel: "",
    webhookUrl: "",
  });

  useEffect(() => {
    setForm((current) => ({
      ...current,
      detectedType: detectProtocolType(current.address, current.name),
    }));
  }, [form.address, form.name]);

  useEffect(() => {
    if (!banner) {
      return;
    }

    const timer = setTimeout(() => setBanner(null), 3200);
    return () => clearTimeout(timer);
  }, [banner]);

  const mutation = useMutation({
    mutationFn: () =>
      api.registerProtocol({
        address: form.address.trim(),
        name: form.name.trim(),
        alert_threshold: form.alertThreshold,
        breaker_threshold: form.breakerThreshold,
      }),
    onSuccess: async () => {
      setBanner({ type: "success", message: "Protocol registered successfully." });
      setStep(0);
      setForm({
        address: "",
        name: "",
        detectedType: "Custom Protocol",
        alertThreshold: 10,
        breakerThreshold: 20,
        telegramEnabled: false,
        telegramChannel: "",
        webhookUrl: "",
      });
      await queryClient.invalidateQueries({ queryKey: ["protocols"] });
      onSuccess?.();
    },
    onError: (error: Error) => {
      setBanner({ type: "error", message: error.message || "Failed to register protocol." });
    },
  });

  const estimatedMonthlyCost = useMemo(() => {
    const basePlan = 100;
    const telegramAddOn = form.telegramEnabled ? 12 : 0;
    const webhookAddOn = form.webhookUrl ? 8 : 0;
    const sensitivityAddOn = Math.max(0, 20 - form.alertThreshold) * 1.2;

    return basePlan + telegramAddOn + webhookAddOn + sensitivityAddOn;
  }, [form.alertThreshold, form.telegramEnabled, form.webhookUrl]);

  async function resolveEns() {
    if (!form.address.trim().endsWith(".eth")) {
      return;
    }

    setIsResolvingEns(true);
    try {
      const resolved = await ENS_CLIENT.getEnsAddress({
        name: form.address.trim(),
      });

      if (!resolved) {
        setBanner({ type: "error", message: "ENS name not found." });
      } else {
        setForm((current) => ({ ...current, address: resolved }));
        setBanner({ type: "success", message: `Resolved to ${resolved}` });
      }
    } catch (error) {
      setBanner({ type: "error", message: (error as Error).message || "ENS resolution failed." });
    } finally {
      setIsResolvingEns(false);
    }
  }

  function canAdvanceFromCurrentStep(): boolean {
    if (step === 0) {
      return ETH_ADDRESS_REGEX.test(form.address.trim()) && form.name.trim().length > 0;
    }

    if (step === 1) {
      return form.alertThreshold >= 5 && form.alertThreshold <= 50 && form.breakerThreshold >= 10 && form.breakerThreshold <= 75;
    }

    return true;
  }

  function nextStep() {
    if (!canAdvanceFromCurrentStep()) {
      setBanner({ type: "error", message: "Complete the required fields before continuing." });
      return;
    }

    setStep((current) => Math.min(steps.length - 1, current + 1));
  }

  function previousStep() {
    setStep((current) => Math.max(0, current - 1));
  }

  function submit(event: FormEvent) {
    event.preventDefault();

    if (!ETH_ADDRESS_REGEX.test(form.address.trim())) {
      setBanner({ type: "error", message: "Protocol address must be a valid 0x address." });
      setStep(0);
      return;
    }

    if (!form.name.trim()) {
      setBanner({ type: "error", message: "Protocol name is required." });
      setStep(0);
      return;
    }

    mutation.mutate();
  }

  return (
    <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Register Protocol</h3>
        <p className="text-sm text-[var(--text-secondary)]">Guided onboarding with risk thresholds and notification routing.</p>
      </div>

      <ol className="mb-6 grid grid-cols-4 gap-2">
        {steps.map((label, index) => {
          const completed = index < step;
          const active = index === step;

          return (
            <li key={label} className="flex items-center gap-2">
              <span
                className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
                  completed
                    ? "bg-[var(--success)] text-[#052e16]"
                    : active
                      ? "border border-[var(--accent)] bg-[color:rgba(59,130,246,0.15)] text-[var(--text-primary)]"
                      : "border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--text-muted)]"
                }`}
              >
                {completed ? <Check className="h-3.5 w-3.5" /> : index + 1}
              </span>
              <span className={`hidden text-xs sm:inline ${active ? "text-[var(--text-primary)]" : "text-[var(--text-muted)]"}`}>{label}</span>
            </li>
          );
        })}
      </ol>

      {banner && (
        <div
          className={`mb-4 rounded-lg border px-3 py-2 text-sm ${
            banner.type === "success"
              ? "border-[#14532d] bg-[#14532d]/35 text-[#86efac]"
              : "border-[#7f1d1d] bg-[#7f1d1d]/35 text-[#fca5a5]"
          }`}
        >
          {banner.message}
        </div>
      )}

      <form className="space-y-4" onSubmit={submit}>
        {step === 0 && (
          <div className="space-y-4">
            <div>
              <label htmlFor="protocol-address" className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
                Protocol Address or ENS
              </label>
              <div className="flex gap-2">
                <input
                  id="protocol-address"
                  value={form.address}
                  onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))}
                  placeholder="0x... or protocol.eth"
                  className="w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[color:rgba(59,130,246,0.5)]"
                  required
                />
                <button
                  type="button"
                  className="inline-flex items-center gap-1 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:border-[var(--border-muted)] disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={resolveEns}
                  disabled={!form.address.trim().endsWith(".eth") || isResolvingEns}
                >
                  <LinkIcon className="h-4 w-4" />
                  {isResolvingEns ? "Resolving" : "Resolve"}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="protocol-name" className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
                Protocol Name
              </label>
              <input
                id="protocol-name"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                placeholder="Aave V3"
                className="w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[color:rgba(59,130,246,0.5)]"
                required
              />
            </div>

            <p className="inline-flex items-center gap-1 rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-[var(--text-secondary)]">
              <Sparkles className="h-3.5 w-3.5 text-[var(--accent)]" />
              Detected type: <span className="font-medium text-[var(--text-primary)]">{form.detectedType}</span>
            </p>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-5">
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label htmlFor="alert-threshold" className="text-sm font-medium text-[var(--text-secondary)]">
                  Alert Threshold
                </label>
                <span className="text-sm text-[var(--text-primary)]">{form.alertThreshold}%</span>
              </div>
              <input
                id="alert-threshold"
                type="range"
                min={5}
                max={50}
                value={form.alertThreshold}
                onChange={(event) => setForm((current) => ({ ...current, alertThreshold: Number(event.target.value) }))}
                className="w-full accent-[var(--accent)]"
              />
              <p className="mt-1 text-xs text-[var(--text-muted)]">Lower value increases detection sensitivity.</p>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label htmlFor="breaker-threshold" className="text-sm font-medium text-[var(--text-secondary)]">
                  Circuit Breaker Threshold
                </label>
                <span className="text-sm text-[var(--text-primary)]">{form.breakerThreshold}%</span>
              </div>
              <input
                id="breaker-threshold"
                type="range"
                min={10}
                max={75}
                value={form.breakerThreshold}
                onChange={(event) => setForm((current) => ({ ...current, breakerThreshold: Number(event.target.value) }))}
                className="w-full accent-[var(--critical)]"
              />
              <p className="mt-1 text-xs text-[var(--text-muted)]">Higher value delays automated protocol pause action.</p>
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
              <p className="mb-2 text-xs uppercase tracking-[0.1em] text-[var(--text-muted)]">Preview</p>
              <p className="text-sm text-[var(--text-secondary)]">
                Alerts trigger at <span className="text-[var(--text-primary)]">{form.alertThreshold}%</span> deviation.
              </p>
              <p className="text-sm text-[var(--text-secondary)]">
                Circuit breaker engages at <span className="text-[var(--text-primary)]">{form.breakerThreshold}%</span> deviation.
              </p>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <label className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2">
              <span>
                <span className="block text-sm font-medium text-[var(--text-primary)]">Telegram Alerts</span>
                <span className="text-xs text-[var(--text-muted)]">Send high-priority alerts instantly</span>
              </span>
              <input
                type="checkbox"
                checked={form.telegramEnabled}
                onChange={(event) => setForm((current) => ({ ...current, telegramEnabled: event.target.checked }))}
                className="h-4 w-4 rounded border-[var(--border-subtle)] bg-[var(--bg-base)] accent-[var(--accent)]"
              />
            </label>

            {form.telegramEnabled && (
              <div>
                <label htmlFor="telegram-channel" className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
                  Telegram Channel / Chat ID
                </label>
                <input
                  id="telegram-channel"
                  value={form.telegramChannel}
                  onChange={(event) => setForm((current) => ({ ...current, telegramChannel: event.target.value }))}
                  placeholder="@aegis-security"
                  className="w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[color:rgba(59,130,246,0.5)]"
                />
              </div>
            )}

            <div>
              <label htmlFor="webhook-url" className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
                Webhook URL
              </label>
              <input
                id="webhook-url"
                value={form.webhookUrl}
                onChange={(event) => setForm((current) => ({ ...current, webhookUrl: event.target.value }))}
                placeholder="https://hooks.company.com/aegis"
                className="w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[color:rgba(59,130,246,0.5)]"
              />
            </div>

            <p className="text-xs text-[var(--text-muted)]">Email notifications are planned and not yet active.</p>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
              <p className="mb-3 text-xs uppercase tracking-[0.1em] text-[var(--text-muted)]">Review Configuration</p>
              <dl className="grid gap-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Protocol</dt>
                  <dd className="text-[var(--text-primary)]">{form.name || "-"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Address</dt>
                  <dd className="font-mono text-[var(--text-secondary)]">{form.address || "-"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Alert Threshold</dt>
                  <dd className="text-[var(--text-primary)]">{form.alertThreshold}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Breaker Threshold</dt>
                  <dd className="text-[var(--text-primary)]">{form.breakerThreshold}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Telegram</dt>
                  <dd className="text-[var(--text-primary)]">{form.telegramEnabled ? "Enabled" : "Disabled"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Webhook</dt>
                  <dd className="text-[var(--text-primary)]">{form.webhookUrl ? "Configured" : "Not configured"}</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
              <p className="text-xs uppercase tracking-[0.1em] text-[var(--text-muted)]">Estimated Monthly Cost</p>
              <p className="mt-1 text-2xl font-bold text-[var(--text-primary)]">{formatUsd(estimatedMonthlyCost)}</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">Includes monitoring, detection, and configured notification channels.</p>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-4">
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-lg border border-[var(--border-subtle)] px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:border-[var(--border-muted)] disabled:cursor-not-allowed disabled:opacity-40"
            onClick={previousStep}
            disabled={step === 0 || mutation.isPending}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </button>

          {step < steps.length - 1 ? (
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white transition hover:bg-[var(--accent-hover)]"
              onClick={nextStep}
            >
              Continue
              <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="submit"
              className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-55"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? "Registering..." : "Register Protocol"}
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
