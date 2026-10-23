import { request } from "@/api/client";
import type {
  CharacterBatchPayload,
  CharacterBatchResult,
  ContentPayload,
  LearningContent,
  Paginated,
  ContentStatus,
  ContentType,
} from "@/types/api";

export function listContents(
  token: string,
  childId: string,
  query: {
    page?: number;
    page_size?: number;
    content_type?: ContentType;
    status?: ContentStatus;
    keyword?: string;
  } = {},
): Promise<Paginated<LearningContent>> {
  const params = new URLSearchParams();
  params.set("page", String(query.page ?? 1));
  params.set("page_size", String(query.page_size ?? 20));
  if (query.content_type) {
    params.set("content_type", query.content_type);
  }
  if (query.status) {
    params.set("status", query.status);
  }
  if (query.keyword) {
    params.set("keyword", query.keyword);
  }
  return request<Paginated<LearningContent>>(
    `/children/${childId}/contents?${params.toString()}`,
    { token },
  );
}

export function createContent(
  token: string,
  childId: string,
  payload: ContentPayload,
): Promise<LearningContent> {
  return request<LearningContent>(`/children/${childId}/contents`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function batchUpsertCharacters(
  token: string,
  childId: string,
  payload: CharacterBatchPayload,
): Promise<CharacterBatchResult> {
  return request<CharacterBatchResult>(
    `/children/${childId}/contents/characters/batch`,
    {
      method: "POST",
      token,
      body: payload,
    },
  );
}

export function batchUpsertEnglishWords(
  token: string,
  childId: string,
  payload: CharacterBatchPayload,
): Promise<CharacterBatchResult> {
  return request<CharacterBatchResult>(
    `/children/${childId}/contents/english/batch`,
    {
      method: "POST",
      token,
      body: payload,
    },
  );
}

export function updateContent(
  token: string,
  childId: string,
  contentId: string,
  payload: ContentPayload,
): Promise<LearningContent> {
  return request<LearningContent>(
    `/children/${childId}/contents/${contentId}`,
    {
      method: "PUT",
      token,
      body: payload,
    },
  );
}

export function deleteContent(
  token: string,
  childId: string,
  contentId: string,
): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(
    `/children/${childId}/contents/${contentId}`,
    {
      method: "DELETE",
      token,
    },
  );
}

export function patchContentStatus(
  token: string,
  childId: string,
  contentId: string,
  status: ContentStatus,
): Promise<LearningContent> {
  return request<LearningContent>(
    `/children/${childId}/contents/${contentId}/status`,
    {
      method: "PATCH",
      token,
      body: { status },
    },
  );
}
