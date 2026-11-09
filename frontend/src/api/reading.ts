import { request } from "@/api/client";
import type { ReadingSettings, ReadingSettingsPayload } from "@/types/api";

export function getReadingSettings(
  token: string,
  childId: string,
): Promise<ReadingSettings | null> {
  return request<ReadingSettings | null>(
    `/children/${childId}/reading-settings`,
    { token },
  );
}

export function updateReadingSettings(
  token: string,
  childId: string,
  payload: ReadingSettingsPayload,
): Promise<ReadingSettings> {
  return request<ReadingSettings>(`/children/${childId}/reading-settings`, {
    method: "PUT",
    token,
    body: payload,
  });
}
