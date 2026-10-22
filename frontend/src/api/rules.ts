import { request } from "@/api/client";
import type { Rule, RulePayload } from "@/types/api";

export function getRule(token: string, childId: string): Promise<Rule> {
  return request<Rule>(`/children/${childId}/rules`, { token });
}

export function createRule(token: string, childId: string, payload: RulePayload): Promise<Rule> {
  return request<Rule>(`/children/${childId}/rules`, {
    method: "POST",
    token,
    body: payload
  });
}

export function updateRule(token: string, childId: string, payload: RulePayload): Promise<Rule> {
  return request<Rule>(`/children/${childId}/rules`, {
    method: "PUT",
    token,
    body: payload
  });
}
