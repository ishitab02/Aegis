const API_BASE = "/api/v1";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = await response.text().catch(() => "");
    const message = payload ? `${response.status} ${response.statusText}: ${payload}` : `${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: () => apiFetch<unknown>("/health"),
  getAlerts: (page = 1, limit = 20, protocol?: string) => {
    const query = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (protocol) {
      query.set("protocol", protocol);
    }
    return apiFetch<unknown>(`/alerts?${query.toString()}`);
  },
  getAlertById: (id: string) => apiFetch<unknown>(`/alerts/${id}`),
  getProtocols: (activeOnly = false) => {
    const query = activeOnly ? "?active=true" : "";
    return apiFetch<unknown>(`/protocols${query}`);
  },
  registerProtocol: (payload: {
    address: string;
    name: string;
    alert_threshold: number;
    breaker_threshold: number;
  }) =>
    apiFetch<unknown>("/protocols", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getProtocolStatusByAddress: (address: string) =>
    apiFetch<unknown>(`/protocols/${address}/status`),
  getSentinelAggregate: () => apiFetch<unknown>("/sentinel/aggregate"),
  runDetection: (payload: {
    protocol_address: string;
    protocol_name?: string;
    simulate_tvl_drop_percent?: number;
    simulate_price_deviation_percent?: number;
    simulate_short_voting_period?: boolean;
  }) =>
    apiFetch<unknown>("/sentinel/detect", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getForensics: () => apiFetch<unknown>("/forensics"),
  getForensicsById: (id: string) => apiFetch<unknown>(`/forensics/${id}`),
  runForensics: (payload: {
    tx_hash: string;
    protocol: string;
    description?: string;
  }) =>
    apiFetch<unknown>("/forensics", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
