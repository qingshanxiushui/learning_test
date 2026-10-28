import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Skeleton,
  Space,
  Switch,
  Table,
  Tabs,
  Typography,
  message,
  type TableProps,
} from "antd";
import StatCard from "@/features/parent/components/StatCard";
import {
  createChild,
  deleteChild,
  listChildren,
  updateChild,
} from "@/api/children";
import { getOverviewStats } from "@/api/stats";
import {
  batchUpsertCharacters,
  batchUpsertClassics,
  batchUpsertEnglishWords,
  batchUpsertIdioms,
  batchUpsertPoems,
  clearContentStats,
  createContent,
  deleteContent,
  listContents,
  patchContentStatus,
  updateContent,
} from "@/api/contents";
import { getPinyinSettings, updatePinyinSettings } from "@/api/pinyin";
import { createRule, getRule, updateRule } from "@/api/rules";
import { getMathSettings, updateMathSettings } from "@/api/math";
import { login } from "@/api/auth";
import type {
  Child,
  ContentPayload,
  ContentType,
  LearningContent,
  MathOperator,
  OverviewStats,
  PinyinCategory,
  RulePayload,
} from "@/types/api";

const DEMO_TOKEN_KEY = "parent_demo_token";

const CONTENT_TYPE_OPTIONS: { label: string; value: ContentType }[] = [
  { label: "汉字", value: "character" },
  { label: "国学", value: "classic" },
  { label: "古诗", value: "poem" },
  { label: "成语", value: "idiom" },
  { label: "英语", value: "englishWord" },
];

const LEARNING_TYPE_OPTIONS: { label: string; value: ContentType }[] = [
  ...CONTENT_TYPE_OPTIONS,
  { label: "算术", value: "math" },
  { label: "拼音", value: "pinyin" },
];

const MATH_OPERATOR_OPTIONS: { label: string; value: MathOperator }[] = [
  { label: "加法 +", value: "add" },
  { label: "减法 -", value: "subtract" },
  { label: "乘法 ×", value: "multiply" },
  { label: "除法 ÷", value: "divide" },
];

const PINYIN_CATEGORY_OPTIONS: { label: string; value: PinyinCategory }[] = [
  { label: "声母", value: "initial" },
  { label: "单韵母", value: "single_final" },
  { label: "韵母", value: "final" },
  { label: "整体认读音节", value: "whole_syllable" },
];

const CONTENT_PAGE_SIZE_OPTIONS = [10, 20, 50];

function buildEmptyStats(): OverviewStats {
  return {
    total_sessions: 0,
    sessions_last_7_days: 0,
    average_accuracy_rate: 0,
    content_count: 0,
    recent_session: null,
  };
}

export default function ParentDashboard() {
  const [messageApi, contextHolder] = message.useMessage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string>(
    localStorage.getItem(DEMO_TOKEN_KEY) ?? "",
  );
  const [loginLoading, setLoginLoading] = useState(false);

  const [children, setChildren] = useState<Child[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [stats, setStats] = useState<OverviewStats>(buildEmptyStats());
  const [contents, setContents] = useState<LearningContent[]>([]);
  const [contentTypeFilter, setContentTypeFilter] = useState<
    ContentType | undefined
  >(undefined);
  const [contentPage, setContentPage] = useState(1);
  const [contentPageSize, setContentPageSize] = useState(10);
  const [contentTotal, setContentTotal] = useState(0);
  const [contentSortBy, setContentSortBy] = useState<string | undefined>(
    undefined,
  );
  const [contentSortOrder, setContentSortOrder] = useState<"asc" | "desc">(
    "asc",
  );

  const [childModalOpen, setChildModalOpen] = useState(false);
  const [childEditing, setChildEditing] = useState<Child | null>(null);
  const [contentModalOpen, setContentModalOpen] = useState(false);
  const [contentEditing, setContentEditing] = useState<LearningContent | null>(
    null,
  );

  const [childForm] = Form.useForm();
  const [contentForm] = Form.useForm();
  const [ruleForm] = Form.useForm();
  const [mathForm] = Form.useForm();
  const [pinyinForm] = Form.useForm();
  const [loginForm] = Form.useForm();
  const selectedContentType = Form.useWatch("content_type", contentForm);
  const isBatchCreate =
    !contentEditing &&
    (selectedContentType === "character" ||
      selectedContentType === "englishWord" ||
      selectedContentType === "poem" ||
      selectedContentType === "idiom" ||
      selectedContentType === "classic");
  const isPoemBatch = isBatchCreate && selectedContentType === "poem";
  const isIdiomBatch = isBatchCreate && selectedContentType === "idiom";
  const isClassicBatch = isBatchCreate && selectedContentType === "classic";

  const selectedChild = useMemo(
    () => children.find((item) => item.id === selectedChildId) ?? null,
    [children, selectedChildId],
  );

  async function loadChildrenAndStats(
    activeToken: string,
    preferredChildId?: string,
  ) {
    const childResp = await listChildren(activeToken);
    setChildren(childResp.list);

    const nextChild =
      childResp.list.find((item) => item.id === preferredChildId) ??
      childResp.list.find((item) => item.id === selectedChildId) ??
      childResp.list[0] ??
      null;

    if (nextChild) {
      setSelectedChildId(nextChild.id);
      const overview = await getOverviewStats(nextChild.id, activeToken);
      setStats(overview);
    } else {
      setSelectedChildId(null);
      setStats(buildEmptyStats());
      setContents([]);
      setContentTotal(0);
    }
  }

  async function loadContents(
    activeToken: string,
    childId: string,
    page: number,
    pageSize: number,
    contentType?: ContentType,
    sortBy?: string,
    sortOrder?: "asc" | "desc",
  ) {
    const contentResp = await listContents(activeToken, childId, {
      page,
      page_size: pageSize,
      content_type: contentType,
      sort_by: sortBy,
      sort_order: sortOrder,
    });
    setContents(contentResp.list);
    setContentTotal(contentResp.pagination.total);
  }

  async function loadRule(activeToken: string, childId: string) {
    try {
      const rule = await getRule(activeToken, childId);
      ruleForm.setFieldsValue({
        question_count: rule.question_count,
        default_content_types: rule.default_content_types,
        allow_child_select_types: rule.allow_child_select_types,
        status: rule.status === 1,
      });
    } catch {
      ruleForm.setFieldsValue({
        question_count: 5,
        default_content_types: ["character", "poem"],
        allow_child_select_types: true,
        status: true,
      });
    }
  }

  async function loadMathSettings(activeToken: string, childId: string) {
    try {
      const settings = await getMathSettings(activeToken, childId);
      mathForm.setFieldsValue(
        settings
          ? {
              min_value: settings.min_value,
              max_value: settings.max_value,
              operators: settings.operators,
              status: settings.status === 1,
            }
          : { min_value: 0, max_value: 20, operators: ["add"], status: true },
      );
    } catch {
      mathForm.setFieldsValue({
        min_value: 0,
        max_value: 20,
        operators: ["add"],
        status: true,
      });
    }
  }

  async function submitMathSettings() {
    if (!token || !selectedChildId) {
      return;
    }
    const values = await mathForm.validateFields();
    await updateMathSettings(token, selectedChildId, {
      min_value: values.min_value,
      max_value: values.max_value,
      operators: values.operators,
      status: values.status ? 1 : 0,
    });
    messageApi.success("算术设置已保存");
  }

  async function loadPinyinSettings(activeToken: string, childId: string) {
    try {
      const settings = await getPinyinSettings(activeToken, childId);
      pinyinForm.setFieldsValue(
        settings
          ? {
              categories: settings.categories,
              with_tone: settings.with_tone,
              status: settings.status === 1,
            }
          : {
              categories: ["initial"],
              with_tone: false,
              status: true,
            },
      );
    } catch {
      pinyinForm.setFieldsValue({
        categories: ["initial"],
        with_tone: false,
        status: true,
      });
    }
  }

  async function submitPinyinSettings() {
    if (!token || !selectedChildId) {
      return;
    }
    const values = await pinyinForm.validateFields();
    await updatePinyinSettings(token, selectedChildId, {
      categories: values.categories,
      with_tone: values.with_tone ?? false,
      status: values.status ? 1 : 0,
    });
    messageApi.success("拼音设置已保存");
  }

  useEffect(() => {
    let mounted = true;
    async function fetchData() {
      setLoading(true);
      setError(null);
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        await loadChildrenAndStats(token);
        if (selectedChildId) {
          await Promise.all([
            loadContents(
              token,
              selectedChildId,
              contentPage,
              contentPageSize,
              contentTypeFilter,
              contentSortBy,
              contentSortOrder,
            ),
            loadRule(token, selectedChildId),
            loadMathSettings(token, selectedChildId),
            loadPinyinSettings(token, selectedChildId),
          ]);
        }
      } catch {
        if (mounted) {
          setError("加载失败，请检查后端服务和登录状态。");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    fetchData();
    return () => {
      mounted = false;
    };
  }, [token, selectedChildId]);

  async function onLoginSubmit(values: {
    account_name: string;
    password: string;
  }) {
    setLoginLoading(true);
    try {
      const result = await login(values.account_name, values.password);
      localStorage.setItem(DEMO_TOKEN_KEY, result.access_token);
      setToken(result.access_token);
      messageApi.success("登录成功");
      setError(null);
    } catch (err) {
      messageApi.error(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoginLoading(false);
    }
  }

  function openCreateChildModal() {
    setChildEditing(null);
    childForm.resetFields();
    childForm.setFieldsValue({ age: 5, status: "active" });
    setChildModalOpen(true);
  }

  function openEditChildModal(child: Child) {
    setChildEditing(child);
    childForm.setFieldsValue({ ...child });
    setChildModalOpen(true);
  }

  async function submitChildForm() {
    const values = await childForm.validateFields();
    if (!token) {
      return;
    }
    if (childEditing) {
      await updateChild(token, childEditing.id, values);
      messageApi.success("孩子档案已更新");
    } else {
      const newChild = await createChild(token, values);
      setSelectedChildId(newChild.id);
      messageApi.success("孩子档案已创建");
    }
    setChildModalOpen(false);
    await loadChildrenAndStats(token, selectedChildId ?? undefined);
  }

  async function handleDeleteChild(child: Child) {
    if (!token) {
      return;
    }
    await deleteChild(token, child.id);
    messageApi.success("孩子档案已删除");
    await loadChildrenAndStats(token);
  }

  function openCreateContentModal() {
    setContentEditing(null);
    contentForm.resetFields();
    contentForm.setFieldsValue({
      content_type: "character",
      difficulty: 1,
      status: "enabled",
      sort_order: 0,
      detail_json: "{}",
    });
    setContentModalOpen(true);
  }

  function openEditContentModal(item: LearningContent) {
    setContentEditing(item);
    contentForm.setFieldsValue({
      ...item,
      detail_json: JSON.stringify(item.detail ?? {}, null, 2),
    });
    setContentModalOpen(true);
  }

  async function submitContentForm() {
    if (!token || !selectedChildId) {
      return;
    }
    const values = await contentForm.validateFields();
    let parsedDetail: Record<string, unknown> = {};
    try {
      parsedDetail = JSON.parse(values.detail_json || "{}");
    } catch {
      messageApi.error("扩展字段 detail_json 不是合法 JSON");
      return;
    }

    const payload: ContentPayload = {
      content_type: values.content_type,
      title: values.title ?? "",
      content_text: values.content_text,
      pronunciation: values.pronunciation || null,
      meaning: values.meaning || null,
      example: values.example || null,
      difficulty: values.difficulty,
      status: values.status,
      sort_order: values.sort_order,
      detail: parsedDetail,
    };

    if (contentEditing) {
      await updateContent(token, selectedChildId, contentEditing.id, payload);
      messageApi.success("学习内容已更新");
    } else if (values.content_type === "character") {
      const result = await batchUpsertCharacters(token, selectedChildId, {
        content_text: payload.content_text,
        pronunciation: payload.pronunciation,
        meaning: payload.meaning,
        example: payload.example,
        difficulty: payload.difficulty,
        status: payload.status,
        sort_order: payload.sort_order,
        detail: payload.detail,
      });
      messageApi.success(
        `已新增 ${result.created_count} 个汉字，更新 ${result.updated_count} 个汉字`,
      );
    } else if (values.content_type === "englishWord") {
      const result = await batchUpsertEnglishWords(token, selectedChildId, {
        content_text: payload.content_text,
        pronunciation: payload.pronunciation,
        meaning: payload.meaning,
        example: payload.example,
        difficulty: payload.difficulty,
        status: payload.status,
        sort_order: payload.sort_order,
        detail: payload.detail,
      });
      messageApi.success(
        `已新增 ${result.created_count} 个单词，更新 ${result.updated_count} 个单词`,
      );
    } else if (values.content_type === "poem") {
      const result = await batchUpsertPoems(token, selectedChildId, {
        content_text: payload.content_text,
        pronunciation: payload.pronunciation,
        meaning: payload.meaning,
        example: payload.example,
        difficulty: payload.difficulty,
        status: payload.status,
        sort_order: payload.sort_order,
        detail: payload.detail,
      });
      messageApi.success(
        `已新增 ${result.created_count} 首古诗，更新 ${result.updated_count} 首古诗`,
      );
    } else if (values.content_type === "idiom") {
      const result = await batchUpsertIdioms(token, selectedChildId, {
        content_text: payload.content_text,
        pronunciation: payload.pronunciation,
        meaning: payload.meaning,
        example: payload.example,
        difficulty: payload.difficulty,
        status: payload.status,
        sort_order: payload.sort_order,
        detail: payload.detail,
      });
      messageApi.success(
        `已新增 ${result.created_count} 个成语，更新 ${result.updated_count} 个成语`,
      );
    } else if (values.content_type === "classic") {
      const result = await batchUpsertClassics(token, selectedChildId, {
        content_text: payload.content_text,
        pronunciation: payload.pronunciation,
        meaning: payload.meaning,
        example: payload.example,
        difficulty: payload.difficulty,
        status: payload.status,
        sort_order: payload.sort_order,
        detail: payload.detail,
      });
      messageApi.success(
        `已新增 ${result.created_count} 组国学，更新 ${result.updated_count} 组国学`,
      );
    } else {
      await createContent(token, selectedChildId, payload);
      messageApi.success("学习内容已创建");
    }
    setContentModalOpen(false);
    await loadContents(
      token,
      selectedChildId,
      contentPage,
      contentPageSize,
      contentTypeFilter,
      contentSortBy,
      contentSortOrder,
    );
  }

  async function handleDeleteContent(item: LearningContent) {
    if (!token || !selectedChildId) {
      return;
    }
    await deleteContent(token, selectedChildId, item.id);
    messageApi.success("学习内容已删除");
    await loadContents(
      token,
      selectedChildId,
      contentPage,
      contentPageSize,
      contentTypeFilter,
      contentSortBy,
      contentSortOrder,
    );
  }

  async function handleToggleContentStatus(
    item: LearningContent,
    checked: boolean,
  ) {
    if (!token || !selectedChildId) {
      return;
    }
    await patchContentStatus(
      token,
      selectedChildId,
      item.id,
      checked ? "enabled" : "disabled",
    );
    await loadContents(
      token,
      selectedChildId,
      contentPage,
      contentPageSize,
      contentTypeFilter,
      contentSortBy,
      contentSortOrder,
    );
  }

  async function handleClearStats() {
    if (!token || !selectedChildId || !contentTypeFilter) {
      return;
    }
    await clearContentStats(token, selectedChildId, contentTypeFilter);
    messageApi.success("统计已清除");
    await loadContents(
      token,
      selectedChildId,
      1,
      contentPageSize,
      contentTypeFilter,
      contentSortBy,
      contentSortOrder,
    );
  }

  async function onContentTypeFilterChange(value: ContentType | undefined) {
    setContentTypeFilter(value);
    setContentPage(1);
    if (token && selectedChildId) {
      await loadContents(
        token,
        selectedChildId,
        1,
        contentPageSize,
        value,
        contentSortBy,
        contentSortOrder,
      );
    }
  }

  async function onContentPaginationChange(page: number, pageSize: number) {
    setContentPage(page);
    setContentPageSize(pageSize);
    if (token && selectedChildId) {
      await loadContents(
        token,
        selectedChildId,
        page,
        pageSize,
        contentTypeFilter,
        contentSortBy,
        contentSortOrder,
      );
    }
  }

  const onContentTableChange: TableProps<LearningContent>["onChange"] = (
    _pagination,
    _filters,
    sorter,
    extra,
  ) => {
    if (extra.action !== "sort") {
      return;
    }
    const sorterResult = Array.isArray(sorter) ? sorter[0] : sorter;
    const sortBy = sorterResult?.field ? String(sorterResult.field) : undefined;
    const sortOrder = sorterResult?.order === "descend" ? "desc" : "asc";
    setContentSortBy(sortBy);
    setContentSortOrder(sortOrder);
    setContentPage(1);
    if (token && selectedChildId) {
      loadContents(
        token,
        selectedChildId,
        1,
        contentPageSize,
        contentTypeFilter,
        sortBy,
        sortOrder,
      );
    }
  };

  async function submitRuleForm() {
    if (!token || !selectedChildId) {
      return;
    }
    const values = await ruleForm.validateFields();
    const payload: RulePayload = {
      question_count: values.question_count,
      default_content_types: values.default_content_types,
      allow_child_select_types: values.allow_child_select_types,
      status: values.status ? 1 : 0,
    };
    try {
      await updateRule(token, selectedChildId, payload);
    } catch {
      await createRule(token, selectedChildId, payload);
    }
    messageApi.success("学习规则已保存");
  }

  async function onChildSwitch(nextChildId: string) {
    if (!token) {
      return;
    }
    setSelectedChildId(nextChildId);
    setContentTypeFilter(undefined);
    setContentPage(1);
    setContentPageSize(10);
    setContentSortBy(undefined);
    setContentSortOrder("asc");
    await Promise.all([
      loadContents(token, nextChildId, 1, 10),
      loadRule(token, nextChildId),
      loadMathSettings(token, nextChildId),
      loadPinyinSettings(token, nextChildId),
      loadChildrenAndStats(token, nextChildId),
    ]);
  }

  if (!token) {
    return (
      <>
        {contextHolder}
        <Card className="mx-auto max-w-xl">
          <Space direction="vertical" className="w-full" size={16}>
            <Typography.Title level={5} className="!mb-0">
              家长登录
            </Typography.Title>
            <Form form={loginForm} layout="vertical" onFinish={onLoginSubmit}>
              <Form.Item
                label="账号"
                name="account_name"
                rules={[{ required: true, message: "请输入账号" }]}
              >
                <Input placeholder="请输入家长账号" />
              </Form.Item>
              <Form.Item
                label="密码"
                name="password"
                rules={[{ required: true, message: "请输入密码" }]}
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
              <Button
                htmlType="submit"
                type="primary"
                loading={loginLoading}
                block
              >
                登录
              </Button>
            </Form>
          </Space>
        </Card>
      </>
    );
  }

  return (
    <Space direction="vertical" size={16} className="w-full">
      {contextHolder}
      <Card>
        <Space direction="vertical" size={8} className="w-full">
          <Typography.Title level={5} className="!mb-0">
            家长端总览
          </Typography.Title>
          <Typography.Text type="secondary">
            管理孩子档案、学习内容、学习规则，跟踪最近学习效果。
          </Typography.Text>
          <Space>
            <Typography.Text type="secondary">
              当前 token 已登录。
            </Typography.Text>
            <Button
              size="small"
              onClick={() => {
                localStorage.removeItem(DEMO_TOKEN_KEY);
                setToken("");
              }}
            >
              退出登录
            </Button>
          </Space>
        </Space>
      </Card>

      {error && (
        <Alert
          type="warning"
          message="数据加载提醒"
          description={error}
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              重试
            </Button>
          }
        />
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <StatCard title="总学习次数" value={stats.total_sessions} />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <StatCard title="最近7天学习" value={stats.sessions_last_7_days} />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <StatCard
            title="平均正确率"
            value={stats.average_accuracy_rate}
            suffix="%"
          />
        </Col>
        <Col xs={24} md={12} xl={6}>
          <StatCard title="学习内容总数" value={stats.content_count} />
        </Col>
      </Row>

      <Tabs
        items={[
          {
            key: "children",
            label: "孩子管理",
            children: (
              <Card
                title="孩子档案 CRUD"
                extra={
                  <Button type="primary" onClick={openCreateChildModal}>
                    新建孩子
                  </Button>
                }
              >
                {loading ? (
                  <Skeleton active paragraph={{ rows: 4 }} />
                ) : children.length === 0 ? (
                  <Empty description="暂无孩子档案" />
                ) : (
                  <Table
                    rowKey="id"
                    dataSource={children}
                    pagination={false}
                    columns={[
                      { title: "姓名", dataIndex: "name" },
                      {
                        title: "昵称",
                        dataIndex: "nickname",
                        render: (v) => v || "-",
                      },
                      { title: "年龄", dataIndex: "age", width: 90 },
                      {
                        title: "学段",
                        dataIndex: "grade_level",
                        render: (v) => v || "-",
                      },
                      { title: "状态", dataIndex: "status", width: 100 },
                      {
                        title: "操作",
                        key: "actions",
                        width: 220,
                        render: (_, record) => (
                          <Space>
                            <Button
                              size="small"
                              onClick={() => onChildSwitch(record.id)}
                            >
                              选择
                            </Button>
                            <Button
                              size="small"
                              onClick={() => openEditChildModal(record)}
                            >
                              编辑
                            </Button>
                            <Popconfirm
                              title="确认删除该孩子档案？"
                              onConfirm={() => handleDeleteChild(record)}
                            >
                              <Button size="small" danger>
                                删除
                              </Button>
                            </Popconfirm>
                          </Space>
                        ),
                      },
                    ]}
                  />
                )}
              </Card>
            ),
          },
          {
            key: "contents",
            label: "学习内容管理",
            children: (
              <Card
                title="学习内容 CRUD"
                extra={
                  <Space>
                    <Select
                      style={{ width: 220 }}
                      placeholder="请选择孩子"
                      value={selectedChildId ?? undefined}
                      options={children.map((item) => ({
                        label: item.name,
                        value: item.id,
                      }))}
                      onChange={onChildSwitch}
                    />
                    <Select
                      aria-label="按学习类型过滤"
                      style={{ width: 140 }}
                      placeholder="全部类型"
                      value={contentTypeFilter}
                      allowClear
                      options={CONTENT_TYPE_OPTIONS}
                      onChange={onContentTypeFilterChange}
                    />
                    <Button
                      type="primary"
                      disabled={!selectedChildId}
                      onClick={openCreateContentModal}
                    >
                      新建内容
                    </Button>
                    <Popconfirm
                      title="确认清除所选类型的统计？"
                      onConfirm={handleClearStats}
                    >
                      <Button
                        danger
                        disabled={!selectedChildId || !contentTypeFilter}
                      >
                        清除统计
                      </Button>
                    </Popconfirm>
                  </Space>
                }
              >
                {!selectedChildId ? (
                  <Empty description="请先创建并选择孩子" />
                ) : (
                  <Table
                    rowKey="id"
                    dataSource={contents}
                    pagination={{
                      current: contentPage,
                      pageSize: contentPageSize,
                      total: contentTotal,
                      showSizeChanger: true,
                      pageSizeOptions: CONTENT_PAGE_SIZE_OPTIONS,
                      showTotal: (total, range) =>
                        `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
                      onChange: onContentPaginationChange,
                    }}
                    onChange={onContentTableChange}
                    columns={[
                      { title: "标题", dataIndex: "title", sorter: true },
                      { title: "类型", dataIndex: "content_type", width: 120 },
                      { title: "难度", dataIndex: "difficulty", width: 80 },
                      {
                        title: "答题次数",
                        dataIndex: "learn_count",
                        width: 100,
                        sorter: true,
                      },
                      {
                        title: "错误次数",
                        dataIndex: "error_count",
                        width: 100,
                        sorter: true,
                      },
                      {
                        title: "错误率",
                        dataIndex: "error_rate",
                        width: 90,
                        sorter: true,
                        render: (value: number) => `${value}%`,
                      },
                      {
                        title: "启用",
                        dataIndex: "status",
                        width: 90,
                        render: (_, row) => (
                          <Switch
                            checked={row.status === "enabled"}
                            onChange={(checked) =>
                              handleToggleContentStatus(row, checked)
                            }
                          />
                        ),
                      },
                      {
                        title: "操作",
                        key: "actions",
                        width: 180,
                        render: (_, record) => (
                          <Space>
                            <Button
                              size="small"
                              onClick={() => openEditContentModal(record)}
                            >
                              编辑
                            </Button>
                            <Popconfirm
                              title="确认删除该内容？"
                              onConfirm={() => handleDeleteContent(record)}
                            >
                              <Button size="small" danger>
                                删除
                              </Button>
                            </Popconfirm>
                          </Space>
                        ),
                      },
                    ]}
                  />
                )}
              </Card>
            ),
          },
          {
            key: "rules",
            label: "学习规则",
            children: (
              <Card title="学习规则设置">
                {!selectedChild ? (
                  <Empty description="请先选择孩子" />
                ) : (
                  <Form
                    form={ruleForm}
                    layout="vertical"
                    onFinish={submitRuleForm}
                  >
                    <Row gutter={16}>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="每轮题量"
                          name="question_count"
                          rules={[{ required: true, message: "请输入题量" }]}
                        >
                          <InputNumber min={1} max={20} className="w-full" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="规则启用"
                          name="status"
                          valuePropName="checked"
                        >
                          <Switch />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="允许孩子选类型"
                          name="allow_child_select_types"
                          valuePropName="checked"
                        >
                          <Switch />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      label="默认内容类型"
                      name="default_content_types"
                      rules={[
                        { required: true, message: "请选择至少一个类型" },
                      ]}
                    >
                      <Select mode="multiple" options={LEARNING_TYPE_OPTIONS} />
                    </Form.Item>

                    <Button htmlType="submit" type="primary">
                      保存规则
                    </Button>
                  </Form>
                )}
              </Card>
            ),
          },
          {
            key: "math",
            label: "算术设置",
            children: (
              <Card title="算术设置">
                {!selectedChild ? (
                  <Empty description="请先选择孩子" />
                ) : (
                  <Form
                    form={mathForm}
                    layout="vertical"
                    onFinish={submitMathSettings}
                  >
                    <Row gutter={16}>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="最小值"
                          name="min_value"
                          rules={[{ required: true, message: "请输入最小值" }]}
                        >
                          <InputNumber min={0} className="w-full" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="最大值"
                          name="max_value"
                          rules={[{ required: true, message: "请输入最大值" }]}
                        >
                          <InputNumber min={1} className="w-full" />
                        </Form.Item>
                      </Col>
                      <Col xs={24} md={8}>
                        <Form.Item
                          label="启用算术"
                          name="status"
                          valuePropName="checked"
                        >
                          <Switch />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      label="运算符"
                      name="operators"
                      rules={[
                        { required: true, message: "请选择至少一个运算符" },
                      ]}
                    >
                      <Checkbox.Group options={MATH_OPERATOR_OPTIONS} />
                    </Form.Item>

                    <Button htmlType="submit" type="primary">
                      保存算术设置
                    </Button>
                  </Form>
                )}
              </Card>
            ),
          },
          {
            key: "pinyin",
            label: "拼音设置",
            children: (
              <Card title="拼音设置">
                {!selectedChild ? (
                  <Empty description="请先选择孩子" />
                ) : (
                  <Form
                    form={pinyinForm}
                    layout="vertical"
                    onFinish={submitPinyinSettings}
                  >
                    <Form.Item
                      label="拼音分类"
                      name="categories"
                      rules={[
                        { required: true, message: "请选择至少一个分类" },
                      ]}
                    >
                      <Select
                        mode="multiple"
                        options={PINYIN_CATEGORY_OPTIONS}
                      />
                    </Form.Item>

                    <Form.Item
                      label="是否带声调"
                      name="with_tone"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>

                    <Form.Item
                      label="启用拼音"
                      name="status"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>

                    <Button htmlType="submit" type="primary">
                      保存拼音设置
                    </Button>
                  </Form>
                )}
              </Card>
            ),
          },
        ]}
      />

      <Modal
        title={childEditing ? "编辑孩子档案" : "新建孩子档案"}
        open={childModalOpen}
        onCancel={() => setChildModalOpen(false)}
        onOk={submitChildForm}
        destroyOnHidden
      >
        <Form form={childForm} layout="vertical">
          <Form.Item
            label="姓名"
            name="name"
            rules={[{ required: true, message: "请输入姓名" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="昵称" name="nickname">
            <Input />
          </Form.Item>
          <Form.Item
            label="年龄"
            name="age"
            rules={[{ required: true, message: "请输入年龄" }]}
          >
            <InputNumber min={3} max={12} className="w-full" />
          </Form.Item>
          <Form.Item label="学段" name="grade_level">
            <Input />
          </Form.Item>
          <Form.Item label="头像地址" name="avatar_url">
            <Input />
          </Form.Item>
          {childEditing && (
            <Form.Item label="状态" name="status" rules={[{ required: true }]}>
              <Select
                options={[
                  { label: "active", value: "active" },
                  { label: "disabled", value: "disabled" },
                ]}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>

      <Modal
        title={contentEditing ? "编辑学习内容" : "新建学习内容"}
        open={contentModalOpen}
        onCancel={() => setContentModalOpen(false)}
        onOk={submitContentForm}
        destroyOnHidden
        width={760}
      >
        <Form form={contentForm} layout="vertical">
          <Row gutter={16}>
            <Col span={contentEditing || !isBatchCreate ? 12 : 24}>
              <Form.Item
                label="类型"
                name="content_type"
                rules={[{ required: true }]}
              >
                <Select options={CONTENT_TYPE_OPTIONS} />
              </Form.Item>
            </Col>
            {(contentEditing || !isBatchCreate) && (
              <Col span={12}>
                <Form.Item
                  label="标题"
                  name="title"
                  rules={[{ required: true, message: "请输入标题" }]}
                >
                  <Input />
                </Form.Item>
              </Col>
            )}
          </Row>
          <Form.Item
            label={
              isBatchCreate && selectedContentType === "character"
                ? "汉字正文"
                : isBatchCreate && selectedContentType === "englishWord"
                  ? "英语正文"
                  : isBatchCreate && selectedContentType === "poem"
                    ? "古诗正文"
                    : isBatchCreate && selectedContentType === "idiom"
                      ? "成语正文"
                      : isBatchCreate && selectedContentType === "classic"
                        ? "国学正文"
                        : "正文"
            }
            name="content_text"
            rules={[{ required: true, message: "请输入正文" }]}
            extra={
              isBatchCreate && selectedContentType === "character"
                ? "支持多行、项目符号和标点；保存后将按单字去重导入。"
                : isBatchCreate && selectedContentType === "englishWord"
                  ? "支持多行、标点、连字符和撇号；空格不分割，保存后将按词组去重导入。"
                  : isBatchCreate && selectedContentType === "poem"
                    ? "每首古诗以“《诗名》朝代·诗人”开头，正文分行/分句；保存后自动提取诗名、朝代、诗人和诗句。"
                    : isBatchCreate && selectedContentType === "idiom"
                      ? "每个《》内的成语作为一条记录，保存后按成语去重导入。"
                      : isBatchCreate && selectedContentType === "classic"
                        ? "按行分割，每两行为一组（上一行 + 下一行）；最后剩余单行将单独保存（无下一行）。"
                        : undefined
            }
          >
            <Input.TextArea
              rows={isPoemBatch || isClassicBatch ? 8 : 3}
              placeholder={
                isBatchCreate && selectedContentType === "character"
                  ? "- 根、茂、但、闻、响\n- 苔、初、本、习"
                  : isBatchCreate && selectedContentType === "englishWord"
                    ? "apple, banana\norange pear"
                    : isBatchCreate && selectedContentType === "poem"
                      ? "《静夜思》唐·李白\n床前明月光，疑是地上霜。举头望明月，低头思故乡。\n\n《春晓》唐·孟浩然\n春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。"
                      : isBatchCreate && selectedContentType === "idiom"
                        ? "《 地大物博》《博大精深》《深入人心》\n《照章办事》《事出有因》《因小失大》"
                        : isBatchCreate && selectedContentType === "classic"
                          ? "人之初，性本善。性相近，习相远。\n苟不教，性乃迁。教之道，贵以专。"
                          : undefined
              }
            />
          </Form.Item>
          {!isPoemBatch && !isIdiomBatch && !isClassicBatch && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="发音" name="pronunciation">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="释义" name="meaning">
                  <Input />
                </Form.Item>
              </Col>
            </Row>
          )}
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="难度"
                name="difficulty"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={3} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="排序"
                name="sort_order"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} className="w-full" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="状态"
                name="status"
                rules={[{ required: true }]}
              >
                <Select
                  options={[
                    { label: "enabled", value: "enabled" },
                    { label: "disabled", value: "disabled" },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
          {!isPoemBatch && !isIdiomBatch && !isClassicBatch && (
            <Form.Item label="示例" name="example">
              <Input />
            </Form.Item>
          )}
          {!isPoemBatch && !isIdiomBatch && !isClassicBatch && (
            <Form.Item
              label="扩展字段 detail_json"
              name="detail_json"
              tooltip={'输入 JSON 字符串，例如 {"author":"李白"}'}
              rules={[{ required: true, message: "请输入 detail_json" }]}
            >
              <Input.TextArea rows={6} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Space>
  );
}
