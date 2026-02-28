import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { AggregateResponse } from "../types";

export function useSentinels() {
  return useQuery<AggregateResponse>({
    queryKey: ["sentinels"],
    queryFn: () => api.getSentinelAggregate() as Promise<AggregateResponse>,
    refetchInterval: 5000,
    retry: 2,
  });
}
