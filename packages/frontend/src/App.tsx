import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Navigate, NavLink, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  Activity,
  ChevronRight,
  Boxes,
  Check,
  Copy,
  ExternalLink,
  FileSearch,
  LogOut,
  RefreshCw,
  Radio,
  Shield,
  Wallet,
  AlertTriangle,
} from "lucide-react";
import clsx from "clsx";
import { base, baseSepolia } from "wagmi/chains";
import { PageWrapper } from "./components/layout/PageWrapper";
import { AlertHistory } from "./components/alerts/AlertHistory";
import { ThreatFeed } from "./components/dashboard/ThreatFeed";
import { LiveMonitor } from "./components/dashboard/LiveMonitor";
import { ReportViewer } from "./components/forensics/ReportViewer";
import { ThreatDashboard } from "./components/dashboard/ThreatDashboard";
import { SystemStatus } from "./components/dashboard/SystemStatus";
import { MetricCard } from "./components/dashboard/MetricCard";
import { useSentinels } from "./hooks/useSentinels";
import { useAlerts } from "./hooks/useAlerts";
import { useProtocols } from "./hooks/useProtocols";
import { useHealth } from "./hooks/useHealth";
import { useAlertStream } from "./hooks/useAlertStream";
import { useWallet } from "./hooks/useWallet";
import { ProtocolsPage } from "./pages/Protocols";
import { LoadingSkeleton } from "./components/common/LoadingSkeleton";
import { EulerDemo } from "./components/demo/EulerDemo";
import { api } from "./lib/api";

type StreamInfo = ReturnType<typeof useAlertStream>;

type ForensicsListRow = {
  id: string;
  protocol: string;
  severity: string;
  timestamp: number;
};

function normalizeForensicsSeverity(value: unknown): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    return "UNKNOWN";
  }
  return value.toUpperCase();
}

function toUnixSeconds(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value > 1_000_000_000_000 ? Math.floor(value / 1000) : value;
  }
  if (typeof value === "string") {
    const numeric = Number(value);
    if (!Number.isNaN(numeric)) {
      return numeric > 1_000_000_000_000 ? Math.floor(numeric / 1000) : numeric;
    }

    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return Math.floor(parsed / 1000);
    }
  }
  return Math.floor(Date.now() / 1000);
}

function normalizeForensicsList(payload: unknown): ForensicsListRow[] {
  const root = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : {};
  const source = Array.isArray(root.reports)
    ? root.reports
    : Array.isArray(root.items)
      ? root.items
      : Array.isArray(payload)
        ? payload
        : [];

  return source
    .map((entry, index) => {
      const row = entry && typeof entry === "object" ? (entry as Record<string, unknown>) : {};
      const report =
        row.report && typeof row.report === "object" ? (row.report as Record<string, unknown>) : {};
      const summary =
        report.executive_summary && typeof report.executive_summary === "object"
          ? (report.executive_summary as Record<string, unknown>)
          : {};

      const id = typeof row.id === "string" && row.id ? row.id : `report-${index}`;
      const protocol =
        (typeof row.protocol === "string" && row.protocol) ||
        (typeof report.protocol === "string" && report.protocol) ||
        "Unknown Protocol";
      const severity = normalizeForensicsSeverity(
        summary.severity ?? report.severity ?? row.severity,
      );
      const timestamp = toUnixSeconds(row.created_at ?? report.timestamp ?? row.timestamp);

      return { id, protocol, severity, timestamp };
    })
    .sort((a, b) => b.timestamp - a.timestamp);
}

function DashboardNavLink({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          "rounded px-3 py-1.5 text-xs font-medium transition",
          isActive
            ? "bg-accent/15 text-text-primary"
            : "bg-bg-elevated text-text-secondary hover:bg-white/[0.04] hover:text-text-primary",
        )
      }
    >
      {label}
    </NavLink>
  );
}

function DashboardPage({ stream }: { stream: StreamInfo }) {
  const { data: sentinelData, error: sentinelError } = useSentinels();
  const { data: alertsData } = useAlerts({ page: 1, limit: 50 });
  const { data: protocols } = useProtocols({ refetchInterval: 30_000 });
  const { data: health } = useHealth();

  const [now, setNow] = useState(Math.floor(Date.now() / 1000));

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const criticalAlerts = useMemo(
    () =>
      (alertsData?.items ?? []).filter(
        (a) => a.threatLevel === "CRITICAL" || a.threatLevel === "HIGH",
      ).length,
    [alertsData],
  );

  const isHealthy = (health?.status ?? "").toUpperCase() === "HEALTHY";

  const latestScanTs =
    stream.lastEventAt ??
    (typeof sentinelData?.timestamp === "number" ? sentinelData.timestamp : null);

  const secondsSinceScan = latestScanTs == null ? null : Math.max(0, now - latestScanTs);

  return (
    <PageWrapper
      title="Security Dashboard"
      subtitle="Real-time threat monitoring and protocol protection"
    >
      <section className="card mb-6 p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/20 text-accent">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-wide text-text-primary">AEGIS</h2>
              <p className="text-xs text-text-muted">Autonomous DeFi Security Command</p>
            </div>
          </div>

          <div className="grid gap-2 text-sm text-text-secondary sm:grid-cols-2 sm:gap-4">
            <div className="inline-flex items-center gap-2">
              <span
                className={clsx(
                  "h-2.5 w-2.5 rounded-full",
                  isHealthy ? "bg-success" : "bg-threat-critical",
                )}
              />
              <span>System: {isHealthy ? "Healthy" : "Degraded"}</span>
            </div>
            <div className="inline-flex items-center gap-2">
              <Radio className="h-4 w-4" />
              <span>
                Last scan: {secondsSinceScan == null ? "waiting..." : `${secondsSinceScan}s ago`}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <DashboardNavLink to="/" label="Dashboard" />
          <DashboardNavLink to="/alerts" label="Alerts" />
          <DashboardNavLink to="/protocols" label="Protocols" />
          <DashboardNavLink to="/feed" label="Live Feed" />
          <DashboardNavLink to="/forensics" label="Forensics" />
          <DashboardNavLink to="/demo" label="Demo" />
        </div>

        <p className="mt-2 text-xs text-text-muted">SSE stream: {stream.status}</p>
      </section>

      {sentinelError && (
        <div className="mb-6 rounded-lg border border-threat-medium/30 bg-threat-medium-muted/20 px-4 py-3 text-sm text-yellow-300">
          Unable to connect to AEGIS API. Make sure the API service is running.
        </div>
      )}

      <div className="mb-6">
        <ThreatDashboard
          threatLevel={sentinelData?.consensus?.final_threat_level ?? "NONE"}
          consensusReached={sentinelData?.consensus?.consensus_reached ?? false}
          agreementRatio={sentinelData?.consensus?.agreement_ratio ?? 0}
          votes={sentinelData?.consensus?.votes}
        />
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Protocols Monitored"
          value={protocols?.length ?? 0}
          icon={Boxes}
          indicator={(protocols?.length ?? 0) > 0 ? "success" : "neutral"}
        />
        <MetricCard
          label="Active Alerts"
          value={criticalAlerts}
          icon={Activity}
          indicator={criticalAlerts > 0 ? "warning" : "success"}
          trend={criticalAlerts > 0 ? "up" : "neutral"}
          change={criticalAlerts > 0 ? `${criticalAlerts} active` : undefined}
        />
        <MetricCard
          label="Consensus Rate"
          value={`${((sentinelData?.consensus?.agreement_ratio ?? 0) * 100).toFixed(0)}%`}
          icon={Radio}
          indicator={
            (sentinelData?.consensus?.agreement_ratio ?? 0) >= 0.8
              ? "success"
              : (sentinelData?.consensus?.agreement_ratio ?? 0) >= 0.5
                ? "warning"
                : "neutral"
          }
        />
        <MetricCard
          label="Detection Cycle"
          value="30s"
          subvalue="CRE Automation"
          icon={Shield}
          indicator="success"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <LiveMonitor />
          <ThreatFeed />
        </div>
        <div className="space-y-6">
          <SystemStatus />
        </div>
      </div>
    </PageWrapper>
  );
}

function AlertsPage() {
  return (
    <PageWrapper
      title="Alert History"
      subtitle="Complete timeline of detected threats and actions taken"
    >
      <AlertHistory title="" subtitle="" />
    </PageWrapper>
  );
}

function ProtocolsRoutePage() {
  return (
    <PageWrapper
      title="Protocol Management"
      subtitle="Register, filter, and inspect protected protocols"
    >
      <ProtocolsPage />
    </PageWrapper>
  );
}

function ForensicsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["forensics-reports"],
    queryFn: () => api.getForensics() as Promise<unknown>,
    enabled: !id,
    refetchInterval: 20_000,
  });

  const reports = useMemo(() => normalizeForensicsList(data), [data]);
  const errorMessage =
    error instanceof Error
      ? error.message.toLowerCase().includes("timed out")
        ? "Forensics list request timed out. Please retry."
        : error.message
      : "Failed to load forensic reports.";

  return (
    <PageWrapper
      title="Forensic Analysis"
      subtitle="Detailed investigation reports for detected incidents"
    >
      {id ? (
        <ReportViewer reportId={id} />
      ) : (
        <section className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
            <div>
              <h3 className="text-base font-semibold text-text-primary">Forensics Reports</h3>
              <p className="text-sm text-text-muted">
                {reports.length} report{reports.length === 1 ? "" : "s"} available
              </p>
            </div>
            <button
              type="button"
              onClick={() => refetch()}
              disabled={isFetching}
              className="btn-ghost p-2"
              aria-label="Refresh reports"
            >
              <RefreshCw className={clsx("h-4 w-4", isFetching && "animate-spin")} />
            </button>
          </div>

          {isLoading && (
            <div className="space-y-3 p-5">
              <LoadingSkeleton className="h-20" />
              <LoadingSkeleton className="h-20" />
              <LoadingSkeleton className="h-20" />
            </div>
          )}

          {error && !isLoading && (
            <div className="p-5">
              <div className="rounded-lg border border-red-500/40 bg-red-500/20 px-4 py-3">
                <p className="text-sm text-red-200">{errorMessage}</p>
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="mt-2 rounded border border-red-500/50 px-2 py-1 text-xs text-red-200 transition hover:bg-red-500/20"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {!isLoading && !error && reports.length === 0 && (
            <div className="px-6 py-10 text-center">
              <FileSearch className="mx-auto mb-3 h-10 w-10 text-text-muted" />
              <h4 className="text-base font-medium text-text-primary">No reports generated yet</h4>
              <p className="mt-1 text-sm text-text-muted">
                Run forensic analysis from an alert to populate this list.
              </p>
            </div>
          )}

          {!isLoading && !error && reports.length > 0 && (
            <div className="divide-y divide-border-subtle">
              {reports.map((report) => (
                <button
                  key={report.id}
                  type="button"
                  onClick={() => navigate(`/forensics/${report.id}`)}
                  className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition hover:bg-white/[0.02]"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-text-primary">{report.id}</p>
                    <p className="truncate text-xs text-text-muted">{report.protocol}</p>
                    <p className="mt-1 text-xs text-text-disabled">
                      {new Date(report.timestamp * 1000).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={clsx(
                        "rounded px-2 py-1 text-xs font-medium",
                        report.severity === "CRITICAL" && "bg-red-500/20 text-red-300",
                        report.severity === "HIGH" && "bg-orange-500/20 text-orange-300",
                        report.severity === "MEDIUM" && "bg-yellow-500/20 text-yellow-300",
                        (report.severity === "LOW" ||
                          report.severity === "NONE" ||
                          report.severity === "UNKNOWN") &&
                          "bg-bg-elevated text-text-secondary",
                      )}
                    >
                      {report.severity}
                    </span>
                    <ChevronRight className="h-4 w-4 text-text-muted" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>
      )}
    </PageWrapper>
  );
}

function LiveFeedPage() {
  return (
    <PageWrapper title="Live Feed" subtitle="Real-time threat detection stream">
      <ThreatFeed compact={false} />
    </PageWrapper>
  );
}

function DemoPage() {
  return (
    <PageWrapper
      title="Euler Finance Exploit Demo"
      subtitle="Watch AEGIS detect and mitigate the $197M hack in real-time"
    >
      <EulerDemo />
    </PageWrapper>
  );
}

function WalletSettings() {
  const {
    address,
    shortAddress,
    chainId,
    isConnected,
    isConnecting,
    isWrongNetwork,
    isSwitching,
    connectors,
    connect,
    disconnect,
    switchChain,
  } = useWallet();

  const [copied, setCopied] = useState(false);

  const currentNetwork =
    chainId === baseSepolia.id ? "Base Sepolia" : chainId === base.id ? "Base" : `Chain ${chainId}`;

  async function copyAddress() {
    if (!address) return;
    await navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const explorerUrl = address
    ? chainId === baseSepolia.id
      ? `https://sepolia.basescan.org/address/${address}`
      : `https://basescan.org/address/${address}`
    : "";

  const availableConnectors = connectors.map((connector) => ({
    connector,
    isReady: (connector as { ready?: boolean }).ready ?? true,
  }));

  return (
    <section className="card">
      <div className="border-b border-border-subtle px-5 py-4">
        <h3 className="text-base font-semibold text-text-primary">Wallet Connection</h3>
        <p className="text-sm text-text-muted">Manage your connected wallet</p>
      </div>
      <div className="p-5">
        {isConnected && address ? (
          <div className="space-y-4">
            <div className="rounded-lg border border-border-subtle bg-bg-elevated p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className="h-10 w-10 rounded-full"
                    style={{
                      backgroundColor: `hsl(${Array.from(address.slice(2, 10)).reduce((a, c) => a + c.charCodeAt(0), 0) % 360} 55% 50%)`,
                    }}
                  />
                  <div>
                    <p className="font-mono text-sm font-medium text-text-primary">
                      {shortAddress}
                    </p>
                    <p className="text-xs text-text-muted">Connected</p>
                  </div>
                </div>
                <span className="flex h-2 w-2">
                  <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-success opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                </span>
              </div>

              <div className="flex gap-2">
                <button type="button" onClick={copyAddress} className="btn-ghost flex-1 text-xs">
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-success" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                  {copied ? "Copied" : "Copy Address"}
                </button>
                <a
                  href={explorerUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-ghost flex-1 text-xs"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  View on Explorer
                </a>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text-primary">Network</label>
              {isWrongNetwork ? (
                <div className="rounded-lg border border-threat-high/50 bg-threat-high-muted/20 p-3">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-orange-300">
                    <AlertTriangle className="h-4 w-4" />
                    Unsupported Network
                  </div>
                  <p className="mb-3 text-xs text-text-muted">
                    Please switch to Base or Base Sepolia to use AEGIS Protocol.
                  </p>
                  <button
                    type="button"
                    onClick={() => switchChain({ chainId: baseSepolia.id })}
                    disabled={isSwitching}
                    className="btn-primary w-full text-xs"
                  >
                    {isSwitching ? "Switching..." : "Switch to Base Sepolia"}
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-base p-3">
                    <span className="text-sm text-text-secondary">{currentNetwork}</span>
                    <span className="rounded-full bg-success-muted/50 px-2 py-0.5 text-xs font-medium text-green-300">
                      Connected
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => switchChain({ chainId: baseSepolia.id })}
                      disabled={isSwitching || chainId === baseSepolia.id}
                      className={`btn-ghost flex-1 text-xs ${chainId === baseSepolia.id ? "text-accent" : ""}`}
                    >
                      Base Sepolia
                    </button>
                    <button
                      type="button"
                      onClick={() => switchChain({ chainId: base.id })}
                      disabled={isSwitching || chainId === base.id}
                      className={`btn-ghost flex-1 text-xs ${chainId === base.id ? "text-accent" : ""}`}
                    >
                      Base Mainnet
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button type="button" onClick={() => disconnect()} className="btn-danger w-full">
              <LogOut className="h-4 w-4" />
              Disconnect Wallet
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-lg border border-border-subtle bg-bg-elevated p-6 text-center">
              <Wallet className="mx-auto mb-3 h-10 w-10 text-text-muted" />
              <h4 className="mb-1 text-sm font-medium text-text-primary">No Wallet Connected</h4>
              <p className="mb-4 text-xs text-text-muted">
                Connect your wallet to register protocols and interact with the circuit breaker.
              </p>
              <div className="space-y-2">
                {availableConnectors.map(({ connector, isReady }) => (
                  <button
                    key={connector.uid}
                    type="button"
                    onClick={() => connect({ connector })}
                    disabled={isConnecting || !isReady}
                    className="btn-secondary w-full justify-between text-sm"
                  >
                    <span>{isConnecting ? "Connecting..." : `Connect ${connector.name}`}</span>
                    {!isReady && <span className="text-2xs text-text-muted">Unavailable</span>}
                  </button>
                ))}
                {availableConnectors.length === 0 && (
                  <p className="text-xs text-text-muted">
                    No wallet detected. Please install MetaMask or another Web3 wallet.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function SettingsPage() {
  return (
    <PageWrapper title="Settings" subtitle="Configure your AEGIS dashboard preferences">
      <div className="grid gap-6 lg:grid-cols-2">
        <WalletSettings />

        <section className="card">
          <div className="border-b border-border-subtle px-5 py-4">
            <h3 className="text-base font-semibold text-text-primary">Notifications</h3>
            <p className="text-sm text-text-muted">Configure alert delivery</p>
          </div>
          <div className="space-y-4 p-5">
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Email Alerts</p>
                <p className="text-xs text-text-muted">Receive critical alerts via email</p>
              </div>
              <input type="checkbox" className="h-4 w-4 rounded accent-accent" defaultChecked />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Telegram Notifications</p>
                <p className="text-xs text-text-muted">Push alerts to Telegram channel</p>
              </div>
              <input type="checkbox" className="h-4 w-4 rounded accent-accent" />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Webhook Integration</p>
                <p className="text-xs text-text-muted">POST alerts to custom endpoint</p>
              </div>
              <input type="checkbox" className="h-4 w-4 rounded accent-accent" />
            </label>
          </div>
        </section>

        <section className="card">
          <div className="border-b border-border-subtle px-5 py-4">
            <h3 className="text-base font-semibold text-text-primary">Display</h3>
            <p className="text-sm text-text-muted">Customize dashboard appearance</p>
          </div>
          <div className="space-y-4 p-5">
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Compact Mode</p>
                <p className="text-xs text-text-muted">Reduce spacing for more data density</p>
              </div>
              <input type="checkbox" className="h-4 w-4 rounded accent-accent" />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Auto-refresh</p>
                <p className="text-xs text-text-muted">Automatically fetch latest data</p>
              </div>
              <input type="checkbox" className="h-4 w-4 rounded accent-accent" defaultChecked />
            </label>
            <div>
              <p className="mb-2 text-sm font-medium text-text-primary">Refresh Interval</p>
              <select className="input w-full" defaultValue="30">
                <option value="5">5 seconds</option>
                <option value="10">10 seconds</option>
                <option value="30">30 seconds</option>
                <option value="60">1 minute</option>
              </select>
            </div>
          </div>
        </section>

        <section className="card lg:col-span-2">
          <div className="border-b border-border-subtle px-5 py-4">
            <h3 className="text-base font-semibold text-text-primary">API Configuration</h3>
            <p className="text-sm text-text-muted">Manage API keys and endpoints</p>
          </div>
          <div className="space-y-4 p-5">
            <div>
              <label className="mb-2 block text-sm font-medium text-text-primary">API Key</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  className="input flex-1"
                  value="aegis-dev-key-••••••••"
                  readOnly
                />
                <button className="btn-secondary">Regenerate</button>
              </div>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-text-primary">
                API Endpoint
              </label>
              <input
                type="text"
                className="input w-full"
                value="http://localhost:3000/api/v1"
                readOnly
              />
            </div>
          </div>
        </section>
      </div>
    </PageWrapper>
  );
}

export default function App() {
  const stream = useAlertStream();

  return (
    <div className="min-h-screen bg-bg-base">
      <Routes>
        <Route path="/" element={<DashboardPage stream={stream} />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/protocols" element={<ProtocolsRoutePage />} />
        <Route path="/forensics" element={<ForensicsPage />} />
        <Route path="/forensics/:id" element={<ForensicsPage />} />
        <Route path="/feed" element={<LiveFeedPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
