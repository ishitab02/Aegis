const API_BASE = "/api/v1";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  getHealth: () => apiFetch("/health"),
  getSentinelAggregate: () => apiFetch("/sentinel/aggregate"),
  getSentinel: (id: string) => apiFetch(`/sentinel/${id}`),
  runDetection: (protocolAddress: string) =>
    apiFetch("/sentinel/detect", {
      method: "POST",
      body: JSON.stringify({ protocol_address: protocolAddress }),
    }),
  getForensics: () => apiFetch("/forensics"),
  getProtocolStatus: (address: string) =>
    apiFetch(`/reports/protocol?address=${address}`),
};
