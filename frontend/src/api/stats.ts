import { request } from "@/api/client";
import type { OverviewStats } from "@/types/api";

export function getOverviewStats(childId: string, token: string): Promise<OverviewStats> {
  return request<OverviewStats>(`/children/${childId}/stats/overview`, { token });
}
