import { useMemo, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { Shield, Activity, Boxes, FileSearch, Plus, Settings, Wallet, ExternalLink, Copy, Check, LogOut, AlertTriangle } from "lucide-react";
import { useWallet } from "./hooks/useWallet";
import { base, baseSepolia } from "wagmi/chains";
import { PageWrapper } from "./components/layout/PageWrapper";
import { AlertHistory } from "./components/alerts/AlertHistory";
import { ThreatFeed } from "./components/dashboard/ThreatFeed";
import { RegisterProtocol } from "./components/protocol/RegisterProtocol";
import { CircuitBreakerCard } from "./components/protocol/CircuitBreakerCard";
import { ReportViewer } from "./components/forensics/ReportViewer";
import { ThreatDashboard } from "./components/dashboard/ThreatDashboard";
import { SystemStatus } from "./components/dashboard/SystemStatus";
import { MetricCard } from "./components/dashboard/MetricCard";
import { useSentinels } from "./hooks/useSentinels";
import { useAlerts } from "./hooks/useAlerts";
import { api } from "./lib/api";

type ProtocolEntry = {
  address: string;
  name: string;
  alert_threshold?: number;
  breaker_threshold?: number;
  active?: boolean;
};

function extractProtocols(response: unknown): ProtocolEntry[] {
  if (Array.isArray(response)) {
    return response
      .map((item) => item as Record<string, unknown>)
      .filter((item) => typeof item.address === "string")
      .map((item) => ({
        address: String(item.address),
        name:
          (typeof item.name === "string" && item.name) ||
          (typeof item.protocol_name === "string" && item.protocol_name) ||
          "Unnamed Protocol",
        alert_threshold:
          typeof item.alert_threshold === "number" ? item.alert_threshold : undefined,
        breaker_threshold:
          typeof item.breaker_threshold === "number" ? item.breaker_threshold : undefined,
        active: typeof item.active === "boolean" ? item.active : true,
      }));
  }

  if (!response || typeof response !== "object") {
    return [];
  }

  const root = response as Record<string, unknown>;
  const list = (root.protocols ?? root.data ?? root.items) as unknown;
  return extractProtocols(list);
}

// Dashboard Page
function DashboardPage() {
  const { data: sentinelData, error: sentinelError } = useSentinels();
  const { data: alertsData } = useAlerts({ page: 1, limit: 50 });
  const { data: protocolsData } = useQuery({
    queryKey: ["protocols"],
    queryFn: () => api.getProtocols() as Promise<unknown>,
    refetchInterval: 30000,
  });

  const protocols = useMemo(() => extractProtocols(protocolsData), [protocolsData]);
  const criticalAlerts = useMemo(
    () =>
      (alertsData?.items ?? []).filter(
        (a) => a.threatLevel === "CRITICAL" || a.threatLevel === "HIGH"
      ).length,
    [alertsData]
  );

  return (
    <PageWrapper
      title="Security Dashboard"
      subtitle="Real-time threat monitoring and protocol protection"
    >
      {/* Error banner */}
      {sentinelError && (
        <div className="mb-6 rounded-lg border border-threat-medium/30 bg-threat-medium-muted/20 px-4 py-3 text-sm text-yellow-300">
          Unable to connect to AEGIS API. Make sure the API service is running.
        </div>
      )}

      {/* Threat status hero */}
      <div className="mb-6">
        <ThreatDashboard
          threatLevel={sentinelData?.consensus?.final_threat_level ?? "NONE"}
          consensusReached={sentinelData?.consensus?.consensus_reached ?? false}
          agreementRatio={sentinelData?.consensus?.agreement_ratio ?? 0}
        />
      </div>

      {/* Metrics row */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Protocols Monitored"
          value={protocols.length}
          icon={Boxes}
          indicator={protocols.length > 0 ? "success" : "neutral"}
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
          icon={Shield}
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
          icon={Settings}
          indicator="success"
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ThreatFeed />
        </div>
        <div className="space-y-6">
          <SystemStatus />
        </div>
      </div>
    </PageWrapper>
  );
}

// Alerts Page
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

// Protocols Page
function ProtocolsPage() {
  const [selectedAddress, setSelectedAddress] = useState("");
  const [showRegister, setShowRegister] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["protocols"],
    queryFn: () => api.getProtocols() as Promise<unknown>,
    refetchInterval: 15000,
  });

  const protocols = useMemo(() => extractProtocols(data), [data]);

  useEffect(() => {
    if (!selectedAddress && protocols.length > 0) {
      setSelectedAddress(protocols[0].address);
    }
  }, [protocols, selectedAddress]);

  return (
    <PageWrapper
      title="Protocol Management"
      subtitle="Register and monitor protected protocols"
      actions={
        <button
          type="button"
          onClick={() => setShowRegister(!showRegister)}
          className="btn-primary gap-2"
        >
          <Plus className="h-4 w-4" />
          Register Protocol
        </button>
      }
    >
      {/* Register form (collapsible) */}
      {showRegister && (
        <div className="mb-6">
          <RegisterProtocol onSuccess={() => setShowRegister(false)} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Protocol list */}
        <section className="card">
          <div className="border-b border-border-subtle px-5 py-4">
            <h3 className="text-base font-semibold text-text-primary">
              Registered Protocols
            </h3>
            <p className="text-sm text-text-muted">
              {protocols.length} protocol{protocols.length !== 1 ? "s" : ""} monitored
            </p>
          </div>

          {isLoading && (
            <div className="p-5">
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded-lg bg-border-subtle" />
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="p-5">
              <p className="text-sm text-red-300">Failed to load protocols.</p>
            </div>
          )}

          {!isLoading && !error && protocols.length === 0 && (
            <div className="p-5 text-center">
              <Boxes className="mx-auto mb-3 h-8 w-8 text-text-muted" />
              <p className="text-sm text-text-muted">No protocols registered yet.</p>
              <button
                type="button"
                onClick={() => setShowRegister(true)}
                className="mt-3 text-sm text-accent hover:underline"
              >
                Register your first protocol
              </button>
            </div>
          )}

          {protocols.length > 0 && (
            <div className="divide-y divide-border-subtle">
              {protocols.map((protocol) => (
                <button
                  key={protocol.address}
                  type="button"
                  onClick={() => setSelectedAddress(protocol.address)}
                  className={`flex w-full items-center justify-between px-5 py-4 text-left transition-colors ${
                    selectedAddress === protocol.address
                      ? "bg-accent/5"
                      : "hover:bg-white/[0.02]"
                  }`}
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-text-primary">
                      {protocol.name}
                    </p>
                    <p className="truncate font-mono text-xs text-text-muted">
                      {protocol.address}
                    </p>
                  </div>
                  <div className="ml-4 flex items-center gap-3 text-xs text-text-secondary">
                    <span>Alert: {protocol.alert_threshold ?? "—"}%</span>
                    <span>Breaker: {protocol.breaker_threshold ?? "—"}%</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Circuit breaker status */}
        <div>
          {selectedAddress ? (
            <CircuitBreakerCard address={selectedAddress} />
          ) : (
            <section className="card p-6 text-center">
              <Shield className="mx-auto mb-3 h-8 w-8 text-text-muted" />
              <p className="text-sm text-text-muted">
                Select a protocol to view circuit breaker status
              </p>
            </section>
          )}
        </div>
      </div>
    </PageWrapper>
  );
}

// Forensics Page
function ForensicsPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <PageWrapper
      title="Forensic Analysis"
      subtitle="Detailed investigation reports for detected incidents"
    >
      {id ? (
        <ReportViewer reportId={id} />
      ) : (
        <section className="card p-8 text-center">
          <FileSearch className="mx-auto mb-4 h-12 w-12 text-text-muted" />
          <h3 className="mb-2 text-lg font-semibold text-text-primary">
            No Report Selected
          </h3>
          <p className="text-sm text-text-muted">
            Select a forensic report from the alerts page to view detailed analysis.
          </p>
        </section>
      )}
    </PageWrapper>
  );
}

// Live Feed Page
function LiveFeedPage() {
  return (
    <PageWrapper
      title="Live Feed"
      subtitle="Real-time threat detection stream"
    >
      <ThreatFeed compact={false} />
    </PageWrapper>
  );
}

// Wallet Settings Component
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

  const currentNetwork = chainId === baseSepolia.id ? "Base Sepolia" : chainId === base.id ? "Base" : `Chain ${chainId}`;

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

  const availableConnectors = connectors.filter((c) => c.ready);

  return (
    <section className="card">
      <div className="border-b border-border-subtle px-5 py-4">
        <h3 className="text-base font-semibold text-text-primary">Wallet Connection</h3>
        <p className="text-sm text-text-muted">Manage your connected wallet</p>
      </div>
      <div className="p-5">
        {isConnected && address ? (
          <div className="space-y-4">
            {/* Connected wallet info */}
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
                    <p className="font-mono text-sm font-medium text-text-primary">{shortAddress}</p>
                    <p className="text-xs text-text-muted">Connected</p>
                  </div>
                </div>
                <span className="flex h-2 w-2">
                  <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-success opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                </span>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={copyAddress}
                  className="btn-ghost flex-1 text-xs"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
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

            {/* Network info */}
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

            {/* Disconnect button */}
            <button
              type="button"
              onClick={() => disconnect()}
              className="btn-danger w-full"
            >
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
                {availableConnectors.map((connector) => (
                  <button
                    key={connector.uid}
                    type="button"
                    onClick={() => connect({ connector })}
                    disabled={isConnecting}
                    className="btn-secondary w-full text-sm"
                  >
                    {isConnecting ? "Connecting..." : `Connect ${connector.name}`}
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

// Settings Page
function SettingsPage() {
  return (
    <PageWrapper
      title="Settings"
      subtitle="Configure your AEGIS dashboard preferences"
    >
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Wallet Settings */}
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
              <select className="input w-full">
                <option value="5">5 seconds</option>
                <option value="10">10 seconds</option>
                <option value="30" selected>30 seconds</option>
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
              <label className="mb-2 block text-sm font-medium text-text-primary">API Endpoint</label>
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
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/alerts" element={<AlertsPage />} />
      <Route path="/protocols" element={<ProtocolsPage />} />
      <Route path="/forensics" element={<ForensicsPage />} />
      <Route path="/forensics/:id" element={<ForensicsPage />} />
      <Route path="/feed" element={<LiveFeedPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
