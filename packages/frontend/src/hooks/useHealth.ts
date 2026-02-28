import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { HealthResponse } from "../types";

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => api.getHealth() as Promise<HealthResponse>,
    refetchInterval: 10000,
    retry: 1,
  });
}
