import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { batchUpsertCharacters, listContents } from "@/api/contents";
import ParentDashboard from "@/features/parent/pages/ParentDashboard";

const { contentsState } = vi.hoisted(() => ({
  contentsState: {
    list: [] as Array<Record<string, unknown>>,
    total: 0,
  },
}));

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
    list: contentsState.list,
    pagination: {
      page: 1,
      page_size: 10,
      total: contentsState.total,
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

  it("filters contents by learning type and resets to page 1", async () => {
    const user = userEvent.setup();
    contentsState.list = [
      { id: "c1", title: "汉字甲", content_type: "character", difficulty: 1 },
      { id: "c2", title: "古诗乙", content_type: "poem", difficulty: 2 },
    ];
    contentsState.total = 20;
    render(<ParentDashboard />);

    await screen.findByText("家长端总览");
    await user.click(screen.getByRole("tab", { name: "学习内容管理" }));
    await screen.findByText("汉字甲");

    // default load passes no content_type (all types)
    expect(listContents).toHaveBeenCalledWith("mock-token", "child-1", {
      page: 1,
      page_size: 10,
      content_type: undefined,
    });

    // open the type filter and pick 古诗
    await user.click(
      screen.getByRole("combobox", { name: "按学习类型过滤" }),
    );
    await user.click(await screen.findByTitle("古诗"));
    await screen.findByText("古诗乙");

    expect(listContents).toHaveBeenLastCalledWith("mock-token", "child-1", {
      page: 1,
      page_size: 10,
      content_type: "poem",
    });
  });

  it("paginates contents and changes page size", async () => {
    const user = userEvent.setup();
    contentsState.list = [
      { id: "c1", title: "第一页", content_type: "character", difficulty: 1 },
      { id: "c2", title: "第二页", content_type: "character", difficulty: 1 },
    ];
    contentsState.total = 50;
    render(<ParentDashboard />);

    await screen.findByText("家长端总览");
    await user.click(screen.getByRole("tab", { name: "学习内容管理" }));
    await screen.findByText("第一页");

    // go to page 2
    await user.click(screen.getByTitle("2"));
    expect(listContents).toHaveBeenLastCalledWith("mock-token", "child-1", {
      page: 2,
      page_size: 10,
      content_type: undefined,
    });

    // change page size to 20 (current page stays at 2 since still in range)
    await user.click(screen.getByRole("combobox", { name: "Page Size" }));
    await user.click(await screen.findByTitle("20 / page"));
    expect(listContents).toHaveBeenLastCalledWith("mock-token", "child-1", {
      page: 2,
      page_size: 20,
      content_type: undefined,
    });
  });
});
