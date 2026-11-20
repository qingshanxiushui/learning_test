import { request } from "@/api/client";
import type { RecordingSettings, RecordingSettingsPayload } from "@/types/api";

export function getRecordingSettings(
  token: string,
  childId: string,
): Promise<RecordingSettings | null> {
  return request<RecordingSettings | null>(
    `/children/${childId}/recording-settings`,
    { token },
  );
}

export function updateRecordingSettings(
  token: string,
  childId: string,
  payload: RecordingSettingsPayload,
): Promise<RecordingSettings> {
  return request<RecordingSettings>(`/children/${childId}/recording-settings`, {
    method: "PUT",
    token,
    body: payload,
  });
}
