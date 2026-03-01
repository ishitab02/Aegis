import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, Download, ExternalLink, FileSearch } from "lucide-react";
import { api } from "../../lib/api";
import type { ForensicsSummary, ThreatLevel } from "../../types";
import { LoadingSkeleton } from "../common/LoadingSkeleton";
import { ThreatBadge } from "../common/ThreatBadge";
import { AttackFlowDiagram } from "./AttackFlowDiagram";

function asObject(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
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

function normalizeSeverity(value: unknown): ThreatLevel {
  if (typeof value !== "string") {
    return "MEDIUM";
  }

  const upper = value.toUpperCase();
  if (upper === "CRITICAL" || upper === "HIGH" || upper === "MEDIUM" || upper === "LOW" || upper === "NONE") {
    return upper;
  }

  if (upper.includes("CRIT")) return "CRITICAL";
  if (upper.includes("HIGH")) return "HIGH";
  if (upper.includes("LOW")) return "LOW";
  return "MEDIUM";
}

function parseRecommendations(value: unknown): ForensicsSummary["recommendations"] {
  const items = asList(value);

  return items
    .map((entry) => {
      if (typeof entry === "string") {
        return { text: entry, priority: "MEDIUM" as const };
      }

      const object = asObject(entry);
      const text = asString(object.text, asString(object.recommendation, asString(object.action, "")));
      if (!text) {
        return null;
      }

      const priorityRaw = asString(object.priority, "MEDIUM").toUpperCase();
      const priority = priorityRaw === "HIGH" || priorityRaw === "LOW" ? (priorityRaw as "HIGH" | "LOW") : "MEDIUM";
      return { text, priority };
    })
    .filter((item): item is { text: string; priority: "HIGH" | "MEDIUM" | "LOW" } => item !== null);
}

function parseSummary(raw: unknown, reportId: string): ForensicsSummary {
  const root = asObject(raw);
  const reportPayload = asObject(root.report || root.data || raw);
  const summary = asObject(reportPayload.executive_summary || reportPayload.summary || reportPayload.attack_summary);
  const technical = asObject(reportPayload.technical_details || reportPayload.details || root.details);

  const flowRaw =
    asList(reportPayload.attack_flow).length > 0
      ? asList(reportPayload.attack_flow)
      : asList(reportPayload.transaction_flow).length > 0
        ? asList(reportPayload.transaction_flow)
        : asList(summary.attack_flow);

  const flow = flowRaw.map((entry, index) => {
    const node = asObject(entry);
    const label = asString(node.label, asString(node.name, asString(node.step, `Step ${index + 1}`)));

    return {
      id: asString(node.id, `node-${index}`),
      label,
      address: asString(node.address, ""),
      action: asString(node.action, ""),
    };
  });

  const destinationsRaw =
    asList(reportPayload.fund_destinations).length > 0
      ? asList(reportPayload.fund_destinations)
      : asList(summary.fund_destinations).length > 0
        ? asList(summary.fund_destinations)
        : asList(reportPayload.destinations);

  const destinations = destinationsRaw.map((entry) => {
    const item = asObject(entry);
    const statusRaw = asString(item.status, "UNTRACED").toUpperCase();

    return {
      address: asString(item.address, "Unknown"),
      amount: asString(item.amount, "N/A"),
      status: (statusRaw === "TRACED" ? "TRACED" : "UNTRACED") as "TRACED" | "UNTRACED",
      chain: asString(item.chain, "Base"),
    };
  });

  const affectedFunctions = asList(technical.affected_functions).map((item) => asString(item)).filter(Boolean);

  const recommendations =
    parseRecommendations(reportPayload.recommendations).length > 0
      ? parseRecommendations(reportPayload.recommendations)
      : parseRecommendations(summary.recommendations);

  const protocol = asString(root.protocol, asString(reportPayload.protocol, "Unknown Protocol"));

  return {
    reportId: asString(root.id, reportId),
    protocol,
    address: asString(reportPayload.address, protocol),
    severity: normalizeSeverity(summary.severity || reportPayload.severity || root.severity),
    attackType: asString(summary.attack_type, asString(reportPayload.attack_type, "Unknown")),
    estimatedLoss: asString(summary.estimated_loss, asString(reportPayload.estimated_loss, "Undisclosed")),
    summaryText: asString(summary.description, asString(summary.summary, "No executive summary was provided.")),
    timestamp: toUnixSeconds(root.created_at || reportPayload.timestamp || Date.now()),
    flow,
    destinations,
    technicalDetails: {
      vulnerability: asString(technical.vulnerability, "Not specified"),
      affectedFunctions,
      codeSnippet: asString(technical.code_snippet, asString(technical.snippet, "No code snippet provided.")),
    },
    recommendations:
      recommendations.length > 0
        ? recommendations
        : [
            {
              text: "Review and harden access controls for sensitive contract functions.",
              priority: "HIGH",
            },
          ],
  };
}

export function ReportViewer({ reportId }: { reportId?: string }) {
  const [openSections, setOpenSections] = useState({
    summary: true,
    flow: true,
    destinations: true,
    technical: true,
    recommendations: true,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["forensics-report", reportId],
    queryFn: () => api.getForensicsById(reportId || "") as Promise<unknown>,
    enabled: Boolean(reportId),
  });

  const report = useMemo(() => parseSummary(data, reportId || "report"), [data, reportId]);

  function toggleSection(section: keyof typeof openSections) {
    setOpenSections((current) => ({ ...current, [section]: !current[section] }));
  }

  if (!reportId) {
    return (
      <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-6">
        <p className="text-sm text-[var(--text-muted)]">Select a report to inspect forensic details.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <header className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">Forensics Report</p>
            <h2 className="mt-1 text-xl font-semibold text-[var(--text-primary)]">{report.reportId}</h2>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              {report.protocol} • {new Date(report.timestamp * 1000).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <ThreatBadge level={report.severity} />
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:border-[var(--border-muted)]"
              onClick={() => window.print()}
            >
              <Download className="h-4 w-4" />
              Download PDF
            </button>
          </div>
        </div>
      </header>

      {isLoading && (
        <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
          <LoadingSkeleton lines={8} />
        </section>
      )}

      {error && (
        <section className="rounded-xl border border-[#7f1d1d] bg-[#7f1d1d]/30 p-4">
          <p className="text-sm text-[#fecaca]">Failed to load report from `/api/v1/forensics/{reportId}`.</p>
        </section>
      )}

      {!isLoading && !error && (
        <>
          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <button
              type="button"
              className="flex w-full items-center justify-between px-4 py-3 text-left"
              onClick={() => toggleSection("summary")}
            >
              <span className="text-base font-semibold text-[var(--text-primary)]">1. Executive Summary</span>
              <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition ${openSections.summary ? "rotate-180" : ""}`} />
            </button>
            {openSections.summary && (
              <div className="grid gap-3 border-t border-[var(--border-subtle)] px-4 py-3 sm:grid-cols-3">
                <article className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
                  <p className="text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">Attack Type</p>
                  <p className="mt-1 text-sm text-[var(--text-primary)]">{report.attackType}</p>
                </article>
                <article className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
                  <p className="text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">Estimated Loss</p>
                  <p className="mt-1 text-sm text-[var(--text-primary)]">{report.estimatedLoss}</p>
                </article>
                <article className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
                  <p className="text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">Protocol</p>
                  <p className="mt-1 text-sm text-[var(--text-primary)]">{report.address}</p>
                </article>
                <p className="sm:col-span-3 text-sm text-[var(--text-secondary)]">{report.summaryText}</p>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <button
              type="button"
              className="flex w-full items-center justify-between px-4 py-3 text-left"
              onClick={() => toggleSection("flow")}
            >
              <span className="text-base font-semibold text-[var(--text-primary)]">2. Attack Flow</span>
              <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition ${openSections.flow ? "rotate-180" : ""}`} />
            </button>
            {openSections.flow && (
              <div className="border-t border-[var(--border-subtle)] px-4 py-3">
                <AttackFlowDiagram nodes={report.flow} />
              </div>
            )}
          </section>

          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <button
              type="button"
              className="flex w-full items-center justify-between px-4 py-3 text-left"
              onClick={() => toggleSection("destinations")}
            >
              <span className="text-base font-semibold text-[var(--text-primary)]">3. Fund Destinations</span>
              <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition ${openSections.destinations ? "rotate-180" : ""}`} />
            </button>
            {openSections.destinations && (
              <div className="border-t border-[var(--border-subtle)] px-4 py-3">
                <div className="overflow-x-auto">
                  <table className="min-w-full border-collapse">
                    <thead>
                      <tr className="border-b border-[var(--border-subtle)] text-left text-xs uppercase tracking-[0.1em] text-[var(--text-muted)]">
                        <th className="px-2 py-2">Address</th>
                        <th className="px-2 py-2">Amount</th>
                        <th className="px-2 py-2">Status</th>
                        <th className="px-2 py-2">Explorer</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.destinations.map((destination) => (
                        <tr key={`${destination.address}-${destination.amount}`} className="border-b border-[var(--border-subtle)] text-sm">
                          <td className="px-2 py-2 font-mono text-[var(--text-secondary)]">{destination.address}</td>
                          <td className="px-2 py-2 text-[var(--text-secondary)]">{destination.amount}</td>
                          <td className="px-2 py-2">
                            <span
                              className={`rounded px-2 py-1 text-xs font-medium ${
                                destination.status === "TRACED"
                                  ? "bg-[#14532d]/40 text-[#86efac]"
                                  : "bg-[#7f1d1d]/40 text-[#fca5a5]"
                              }`}
                            >
                              {destination.status}
                            </span>
                          </td>
                          <td className="px-2 py-2">
                            <a
                              href={`https://basescan.org/address/${destination.address}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-[var(--accent)] hover:text-[var(--accent-hover)]"
                            >
                              Open
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <button
              type="button"
              className="flex w-full items-center justify-between px-4 py-3 text-left"
              onClick={() => toggleSection("technical")}
            >
              <span className="text-base font-semibold text-[var(--text-primary)]">4. Technical Details</span>
              <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition ${openSections.technical ? "rotate-180" : ""}`} />
            </button>
            {openSections.technical && (
              <div className="space-y-3 border-t border-[var(--border-subtle)] px-4 py-3">
                <article>
                  <p className="mb-1 text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">Vulnerability</p>
                  <p className="text-sm text-[var(--text-secondary)]">{report.technicalDetails.vulnerability}</p>
                </article>

                <article>
                  <p className="mb-1 text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">Affected Functions</p>
                  {report.technicalDetails.affectedFunctions.length > 0 ? (
                    <ul className="space-y-1 text-sm text-[var(--text-secondary)]">
                      {report.technicalDetails.affectedFunctions.map((func) => (
                        <li key={func} className="font-mono">
                          {func}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[var(--text-muted)]">No function list available.</p>
                  )}
                </article>

                <article>
                  <p className="mb-1 inline-flex items-center gap-1 text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">
                    <FileSearch className="h-3.5 w-3.5" />
                    Code Snippet
                  </p>
                  <pre className="overflow-x-auto rounded-md border border-[var(--border-subtle)] bg-[var(--bg-base)] p-3 text-xs text-[var(--text-secondary)]">
                    <code>{report.technicalDetails.codeSnippet}</code>
                  </pre>
                </article>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <button
              type="button"
              className="flex w-full items-center justify-between px-4 py-3 text-left"
              onClick={() => toggleSection("recommendations")}
            >
              <span className="text-base font-semibold text-[var(--text-primary)]">5. Recommendations</span>
              <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition ${openSections.recommendations ? "rotate-180" : ""}`} />
            </button>
            {openSections.recommendations && (
              <div className="space-y-2 border-t border-[var(--border-subtle)] px-4 py-3">
                {report.recommendations.map((recommendation, index) => (
                  <article
                    key={`${recommendation.text}-${index}`}
                    className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2"
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span
                        className={`rounded px-2 py-0.5 text-xs font-medium ${
                          recommendation.priority === "HIGH"
                            ? "bg-[#7f1d1d]/45 text-[#fca5a5]"
                            : recommendation.priority === "LOW"
                              ? "bg-[#14532d]/45 text-[#86efac]"
                              : "bg-[#713f12]/45 text-[#fde047]"
                        }`}
                      >
                        {recommendation.priority}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--text-secondary)]">{recommendation.text}</p>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  );
}
