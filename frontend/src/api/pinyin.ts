import { request } from "@/api/client";
import type { PinyinSettings, PinyinSettingsPayload } from "@/types/api";

export function getPinyinSettings(
  token: string,
  childId: string,
): Promise<PinyinSettings | null> {
  return request<PinyinSettings | null>(
    `/children/${childId}/pinyin-settings`,
    { token },
  );
}

export function updatePinyinSettings(
  token: string,
  childId: string,
  payload: PinyinSettingsPayload,
): Promise<PinyinSettings> {
  return request<PinyinSettings>(`/children/${childId}/pinyin-settings`, {
    method: "PUT",
    token,
    body: payload,
  });
}
