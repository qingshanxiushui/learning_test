import { request } from "@/api/client";
import type { Child, Paginated } from "@/types/api";

export function listChildren(token: string): Promise<Paginated<Child>> {
  return request<Paginated<Child>>("/children?page=1&page_size=20", { token });
}

export function createChild(
  token: string,
  payload: {
    name: string;
    nickname?: string | null;
    age: number;
    grade_level?: string | null;
    avatar_url?: string | null;
  }
): Promise<Child> {
  return request<Child>("/children", {
    method: "POST",
    token,
    body: payload
  });
}

export function updateChild(
  token: string,
  childId: string,
  payload: {
    name: string;
    nickname?: string | null;
    age: number;
    grade_level?: string | null;
    avatar_url?: string | null;
    status: "active" | "disabled";
  }
): Promise<Child> {
  return request<Child>(`/children/${childId}`, {
    method: "PUT",
    token,
    body: payload
  });
}

export function deleteChild(token: string, childId: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/children/${childId}`, {
    method: "DELETE",
    token
  });
}

