import { request } from "@/api/client";
import type { MathSettings, MathSettingsPayload } from "@/types/api";

export function getMathSettings(
  token: string,
  childId: string,
): Promise<MathSettings | null> {
  return request<MathSettings | null>(`/children/${childId}/math-settings`, {
    token,
  });
}

export function updateMathSettings(
  token: string,
  childId: string,
  payload: MathSettingsPayload,
): Promise<MathSettings> {
  return request<MathSettings>(`/children/${childId}/math-settings`, {
    method: "PUT",
    token,
    body: payload,
  });
}
