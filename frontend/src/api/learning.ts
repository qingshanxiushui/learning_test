import { request } from "@/api/client";
import type {
  AnswerFeedback,
  ContentType,
  LearningSession,
  SessionQuestion,
  SessionResult,
} from "@/types/api";

export function startSession(
  token: string,
  childId: string,
  selectedContentTypes: ContentType[],
): Promise<{ session: LearningSession; questions: SessionQuestion[] }> {
  return request(`/children/${childId}/sessions`, {
    method: "POST",
    token,
    body: { selected_content_types: selectedContentTypes },
  });
}

export function submitAnswer(
  token: string,
  childId: string,
  sessionId: string,
  payload: {
    session_question_id: string;
    user_answer: string;
    answer_duration_ms: number;
  },
): Promise<AnswerFeedback> {
  return request(`/children/${childId}/sessions/${sessionId}/answers`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function markCardViewed(
  token: string,
  childId: string,
  sessionId: string,
  questionId: string,
  viewDurationMs: number,
): Promise<{
  session_question_id: string;
  viewed_at: string;
  progress: { completed_questions: number; total_questions: number };
}> {
  return request(
    `/children/${childId}/sessions/${sessionId}/questions/${questionId}/viewed`,
    {
      method: "POST",
      token,
      body: { view_duration_ms: viewDurationMs },
    },
  );
}

export function completeSession(
  token: string,
  childId: string,
  sessionId: string,
): Promise<SessionResult> {
  return request(`/children/${childId}/sessions/${sessionId}/complete`, {
    method: "POST",
    token,
  });
}
