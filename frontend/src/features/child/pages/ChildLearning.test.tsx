import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import {
  completeSession,
  markCardViewed,
  startSession,
  submitAnswer,
} from "@/api/learning";
import ChildLearning from "@/features/child/pages/ChildLearning";

vi.mock("@/api/auth", () => ({ login: vi.fn() }));
vi.mock("@/api/children", () => ({
  listChildren: vi.fn(async () => ({
    list: [
      {
        id: "child-1",
        name: "小雨",
        nickname: "雨点",
        age: 5,
        grade_level: null,
        avatar_url: null,
        status: "active",
        created_at: "2026-08-20T10:00:00Z",
        updated_at: "2026-08-20T10:00:00Z",
      },
    ],
    pagination: { page: 1, page_size: 20, total: 1 },
  })),
}));
vi.mock("@/api/rules", () => ({
  getRule: vi.fn(async () => ({
    id: "rule-1",
    child_id: "child-1",
    question_count: 1,
    default_content_types: ["poem"],
    allow_child_select_types: true,
    status: 1,
    created_at: "2026-08-20T10:00:00Z",
    updated_at: "2026-08-20T10:00:00Z",
  })),
}));
vi.mock("@/api/learning", () => ({
  startSession: vi.fn(async () => ({
    session: {
      id: "session-1",
      child_id: "child-1",
      selected_content_types: ["poem"],
      total_questions: 1,
      completed_questions: 0,
      answered_questions: 0,
      correct_questions: 0,
      accuracy_rate: 0,
      session_status: "in_progress",
      started_at: "2026-08-20T10:00:00Z",
      finished_at: null,
    },
    questions: [
      {
        id: "question-1",
        question_order: 1,
        content_type: "poem",
        question_type: "next_line_choice",
        question_stem: "“床前明月光”下一句是什么？",
        question_options: ["疑是地上霜", "处处闻啼鸟"],
      },
    ],
  })),
  submitAnswer: vi.fn(async () => ({
    session_question_id: "question-1",
    is_correct: true,
    correct_answer: "疑是地上霜",
    answer_explanation: "出自《静夜思》",
    progress: {
      answered_questions: 1,
      total_questions: 1,
      correct_questions: 1,
      accuracy_rate: 100,
    },
  })),
  markCardViewed: vi.fn(async () => ({
    session_question_id: "question-1",
    viewed_at: "2026-08-20T10:00:30Z",
    progress: { completed_questions: 1, total_questions: 1 },
  })),
  completeSession: vi.fn(async () => ({
    session: {
      id: "session-1",
      child_id: "child-1",
      selected_content_types: ["poem"],
      total_questions: 1,
      completed_questions: 1,
      answered_questions: 1,
      correct_questions: 1,
      accuracy_rate: 100,
      session_status: "completed",
      started_at: "2026-08-20T10:00:00Z",
      finished_at: "2026-08-20T10:01:00Z",
    },
    summary: { need_review_contents: [] },
  })),
}));

describe("ChildLearning", () => {
  beforeEach(() => localStorage.setItem("parent_demo_token", "mock-token"));
  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("completes a one-question learning session", async () => {
    const user = userEvent.setup();
    render(<ChildLearning />);

    expect(await screen.findByText(/准备好了吗.*雨点/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "开始学习" }));
    expect(
      await screen.findByText("“床前明月光”下一句是什么？"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "疑是地上霜" }));
    await user.click(screen.getByRole("button", { name: "提交答案" }));
    expect(await screen.findByText("答对了")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "看结果" }));
    expect(await screen.findByText("做得好，学习完成")).toBeInTheDocument();
    expect(screen.getByText("答对 1 / 1 题")).toBeInTheDocument();
  });

  it("views a character card without submitting an answer", async () => {
    vi.mocked(startSession).mockResolvedValueOnce({
      session: {
        id: "card-session",
        child_id: "child-1",
        selected_content_types: ["character"],
        total_questions: 1,
        completed_questions: 0,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "in_progress",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: null,
      },
      questions: [
        {
          id: "card-1",
          question_order: 1,
          content_type: "character",
          question_type: "character_card",
          question_stem: "根",
          question_options: [],
        },
      ],
    });
    vi.mocked(completeSession).mockResolvedValueOnce({
      session: {
        id: "card-session",
        child_id: "child-1",
        selected_content_types: ["character"],
        total_questions: 1,
        completed_questions: 1,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "completed",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: "2026-08-20T10:01:00Z",
      },
      summary: { need_review_contents: [] },
    });
    const user = userEvent.setup();
    render(<ChildLearning />);

    await screen.findByText(/准备好了吗.*雨点/);
    await user.click(screen.getByRole("button", { name: "开始学习" }));
    expect(await screen.findByText("根")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "提交答案" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "完成学习" }));
    expect(await screen.findByText("1")).toBeInTheDocument();
    expect(screen.getByText("个内容已学习")).toBeInTheDocument();
    expect(markCardViewed).toHaveBeenCalledWith(
      "mock-token",
      "child-1",
      "card-session",
      "card-1",
      expect.any(Number),
    );
    expect(submitAnswer).not.toHaveBeenCalled();
  });

  it("views an english word card without submitting an answer", async () => {
    vi.mocked(startSession).mockResolvedValueOnce({
      session: {
        id: "word-session",
        child_id: "child-1",
        selected_content_types: ["englishWord"],
        total_questions: 1,
        completed_questions: 0,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "in_progress",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: null,
      },
      questions: [
        {
          id: "word-1",
          question_order: 1,
          content_type: "englishWord",
          question_type: "english_word_card",
          question_stem: "apple",
          question_options: [],
        },
      ],
    });
    vi.mocked(completeSession).mockResolvedValueOnce({
      session: {
        id: "word-session",
        child_id: "child-1",
        selected_content_types: ["englishWord"],
        total_questions: 1,
        completed_questions: 1,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "completed",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: "2026-08-20T10:01:00Z",
      },
      summary: { need_review_contents: [] },
    });
    const user = userEvent.setup();
    render(<ChildLearning />);

    await screen.findByText(/准备好了吗.*雨点/);
    await user.click(screen.getByRole("button", { name: "开始学习" }));
    expect(await screen.findByText("apple")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "提交答案" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "完成学习" }));
    expect(await screen.findByText("1")).toBeInTheDocument();
    expect(markCardViewed).toHaveBeenCalledWith(
      "mock-token",
      "child-1",
      "word-session",
      "word-1",
      expect.any(Number),
    );
    expect(submitAnswer).not.toHaveBeenCalled();
  });

  it("views a poem card without submitting an answer", async () => {
    vi.mocked(startSession).mockResolvedValueOnce({
      session: {
        id: "poem-session",
        child_id: "child-1",
        selected_content_types: ["poem"],
        total_questions: 1,
        completed_questions: 0,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "in_progress",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: null,
      },
      questions: [
        {
          id: "poem-1",
          question_order: 1,
          content_type: "poem",
          question_type: "poem_card",
          question_stem: "《静夜思》唐·李白\n床前明月光\n疑是地上霜",
          question_options: [],
        },
      ],
    });
    vi.mocked(completeSession).mockResolvedValueOnce({
      session: {
        id: "poem-session",
        child_id: "child-1",
        selected_content_types: ["poem"],
        total_questions: 1,
        completed_questions: 1,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "completed",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: "2026-08-20T10:01:00Z",
      },
      summary: { need_review_contents: [] },
    });
    const user = userEvent.setup();
    render(<ChildLearning />);

    await screen.findByText(/准备好了吗.*雨点/);
    await user.click(screen.getByRole("button", { name: "开始学习" }));
    expect(await screen.findByText(/床前明月光/)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "提交答案" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "完成学习" }));
    expect(await screen.findByText("1")).toBeInTheDocument();
    expect(markCardViewed).toHaveBeenCalledWith(
      "mock-token",
      "child-1",
      "poem-session",
      "poem-1",
      expect.any(Number),
    );
    expect(submitAnswer).not.toHaveBeenCalled();
  });

  it("views an idiom card without submitting an answer", async () => {
    vi.mocked(startSession).mockResolvedValueOnce({
      session: {
        id: "idiom-session",
        child_id: "child-1",
        selected_content_types: ["idiom"],
        total_questions: 1,
        completed_questions: 0,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "in_progress",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: null,
      },
      questions: [
        {
          id: "idiom-1",
          question_order: 1,
          content_type: "idiom",
          question_type: "idiom_card",
          question_stem: "地大物博",
          question_options: [],
        },
      ],
    });
    vi.mocked(completeSession).mockResolvedValueOnce({
      session: {
        id: "idiom-session",
        child_id: "child-1",
        selected_content_types: ["idiom"],
        total_questions: 1,
        completed_questions: 1,
        answered_questions: 0,
        correct_questions: 0,
        accuracy_rate: 0,
        session_status: "completed",
        started_at: "2026-08-20T10:00:00Z",
        finished_at: "2026-08-20T10:01:00Z",
      },
      summary: { need_review_contents: [] },
    });
    const user = userEvent.setup();
    render(<ChildLearning />);

    await screen.findByText(/准备好了吗.*雨点/);
    await user.click(screen.getByRole("button", { name: "开始学习" }));
    expect(await screen.findByText("地大物博")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "提交答案" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "完成学习" }));
    expect(await screen.findByText("1")).toBeInTheDocument();
    expect(markCardViewed).toHaveBeenCalledWith(
      "mock-token",
      "child-1",
      "idiom-session",
      "idiom-1",
      expect.any(Number),
    );
    expect(submitAnswer).not.toHaveBeenCalled();
  });
});
