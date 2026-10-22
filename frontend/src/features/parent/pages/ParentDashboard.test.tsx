import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { batchUpsertCharacters } from "@/api/contents";
import ParentDashboard from "@/features/parent/pages/ParentDashboard";

vi.mock("@/api/children", () => ({
  listChildren: vi.fn(async () => ({
    list: [
      {
        id: "child-1",
        name: "小明",
        nickname: "明明",
        age: 5,
        grade_level: "幼儿园大班",
        avatar_url: null,
        status: "active",
        created_at: "2026-08-20T10:00:00Z",
        updated_at: "2026-08-20T10:00:00Z",
      },
    ],
    pagination: {
      page: 1,
      page_size: 20,
      total: 1,
    },
  })),
}));

vi.mock("@/api/stats", () => ({
  getOverviewStats: vi.fn(async () => ({
    total_sessions: 10,
    sessions_last_7_days: 4,
    average_accuracy_rate: 86.5,
    content_count: 30,
    recent_session: null,
  })),
}));

vi.mock("@/api/contents", () => ({
  listContents: vi.fn(async () => ({
    list: [],
    pagination: {
      page: 1,
      page_size: 50,
      total: 0,
    },
  })),
  createContent: vi.fn(),
  batchUpsertCharacters: vi.fn(async () => ({
    list: [],
    created_count: 9,
    updated_count: 0,
    total_count: 9,
  })),
  updateContent: vi.fn(),
  deleteContent: vi.fn(),
  patchContentStatus: vi.fn(),
}));

vi.mock("@/api/rules", () => ({
  getRule: vi.fn(async () => ({
    id: "rule-1",
    child_id: "child-1",
    question_count: 5,
    default_content_types: ["character"],
    allow_child_select_types: true,
    status: 1,
    created_at: "2026-08-20T10:00:00Z",
    updated_at: "2026-08-20T10:00:00Z",
  })),
  createRule: vi.fn(),
  updateRule: vi.fn(),
}));

vi.mock("@/api/auth", () => ({
  login: vi.fn(),
}));

describe("ParentDashboard", () => {
  beforeEach(() => {
    localStorage.setItem("parent_demo_token", "mock-token");
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("renders parent dashboard data", async () => {
    render(<ParentDashboard />);

    expect(await screen.findByText("家长端总览")).toBeInTheDocument();
    expect(await screen.findByText("小明")).toBeInTheDocument();
    expect(await screen.findByText("总学习次数")).toBeInTheDocument();
    expect(await screen.findByText("平均正确率")).toBeInTheDocument();
    expect(await screen.findByText("学习内容管理")).toBeInTheDocument();
    expect(await screen.findByText("学习规则")).toBeInTheDocument();
  });

  it("uses the batch endpoint when creating character content", async () => {
    const user = userEvent.setup();
    render(<ParentDashboard />);

    await screen.findByText("家长端总览");
    await user.click(screen.getByRole("tab", { name: "学习内容管理" }));
    await user.click(screen.getByRole("button", { name: "新建内容" }));
    await user.type(
      screen.getByLabelText("汉字正文"),
      "- 根、茂、但、闻、响\n- 苔、初、本、习",
    );
    await user.click(screen.getByRole("button", { name: "OK" }));

    expect(batchUpsertCharacters).toHaveBeenCalledWith(
      "mock-token",
      "child-1",
      expect.objectContaining({
        content_text: "- 根、茂、但、闻、响\n- 苔、初、本、习",
        difficulty: 1,
        status: "enabled",
      }),
    );
  });
});
