export type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
  request_id: string;
};

export type ContentType =
  | "character"
  | "classic"
  | "poem"
  | "idiom"
  | "englishWord"
  | "math";
export type ContentStatus = "enabled" | "disabled";

export type MathOperator = "add" | "subtract" | "multiply" | "divide";

export type MathSettings = {
  id: string;
  child_id: string;
  min_value: number;
  max_value: number;
  operators: MathOperator[];
  status: number;
  created_at: string;
  updated_at: string;
};

export type MathSettingsPayload = {
  min_value: number;
  max_value: number;
  operators: MathOperator[];
  status: number;
};

export type Child = {
  id: string;
  name: string;
  nickname: string | null;
  age: number;
  grade_level: string | null;
  avatar_url: string | null;
  status: "active" | "disabled";
  created_at: string;
  updated_at: string;
};

export type Paginated<T> = {
  list: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
};

export type OverviewStats = {
  total_sessions: number;
  sessions_last_7_days: number;
  average_accuracy_rate: number;
  content_count: number;
  recent_session: {
    id: string;
    finished_at: string;
    accuracy_rate: number;
  } | null;
};

export type Rule = {
  id: string;
  child_id: string;
  question_count: number;
  default_content_types: ContentType[];
  allow_child_select_types: boolean;
  status: number;
  created_at: string;
  updated_at: string;
};

export type RulePayload = {
  question_count: number;
  default_content_types: ContentType[];
  allow_child_select_types: boolean;
  status: number;
};

export type LearningContent = {
  id: string;
  child_id: string;
  content_type: ContentType;
  title: string;
  content_text: string;
  pronunciation: string | null;
  meaning: string | null;
  example: string | null;
  difficulty: number;
  status: ContentStatus;
  sort_order: number;
  detail: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ContentPayload = {
  content_type: ContentType;
  title: string;
  content_text: string;
  pronunciation: string | null;
  meaning: string | null;
  example: string | null;
  difficulty: number;
  status: ContentStatus;
  sort_order: number;
  detail: Record<string, unknown>;
};

export type CharacterBatchPayload = Omit<
  ContentPayload,
  "content_type" | "title"
>;

export type CharacterBatchResult = {
  list: LearningContent[];
  created_count: number;
  updated_count: number;
  total_count: number;
};

export type SessionQuestion = {
  id: string;
  question_order: number;
  content_type: ContentType;
  question_type: string;
  question_stem: string;
  question_options: string[];
};

export type LearningSession = {
  id: string;
  child_id: string;
  selected_content_types: ContentType[];
  total_questions: number;
  completed_questions: number;
  answered_questions: number;
  correct_questions: number;
  accuracy_rate: number;
  session_status: "in_progress" | "completed" | "abandoned";
  started_at: string;
  finished_at: string | null;
};

export type AnswerFeedback = {
  session_question_id: string;
  is_correct: boolean;
  correct_answer: string;
  answer_explanation: string | null;
  progress: Pick<
    LearningSession,
    | "answered_questions"
    | "total_questions"
    | "correct_questions"
    | "accuracy_rate"
  >;
};

export type SessionResult = {
  session: LearningSession;
  summary: {
    need_review_contents: Array<{
      content_id: string;
      title: string;
      content_type: ContentType;
    }>;
  };
};
