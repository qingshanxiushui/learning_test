import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Empty,
  Form,
  Input,
  InputNumber,
  Progress,
  Select,
  Spin,
  Typography,
} from "antd";
import { login } from "@/api/auth";
import { ApiError } from "@/api/client";
import { listChildren } from "@/api/children";
import {
  completeSession,
  markCardViewed,
  startSession,
  submitAnswer,
} from "@/api/learning";
import { getRule } from "@/api/rules";
import type {
  AnswerFeedback,
  Child,
  ContentType,
  LearningSession,
  SessionQuestion,
  SessionResult,
} from "@/types/api";

const TOKEN_KEY = "parent_demo_token";

const CARD_QUESTION_TYPES = new Set([
  "character_card",
  "english_word_card",
  "poem_card",
  "idiom_card",
  "classic_card",
  "pinyin_card",
]);

const MULTILINE_CARD_QUESTION_TYPES = new Set(["poem_card", "classic_card"]);

const CONTENT_TYPES: Array<{
  value: ContentType;
  label: string;
  mark: string;
}> = [
  { value: "character", label: "汉字", mark: "字" },
  { value: "classic", label: "国学", mark: "经" },
  { value: "poem", label: "古诗", mark: "诗" },
  { value: "idiom", label: "成语", mark: "言" },
  { value: "englishWord", label: "英语", mark: "Aa" },
  { value: "math", label: "算术", mark: "算" },
  { value: "pinyin", label: "拼音", mark: "拼" },
];

type Phase = "choose" | "learning" | "result";

export default function ChildLearning() {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) ?? "");
  const [children, setChildren] = useState<Child[]>([]);
  const [childId, setChildId] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<ContentType[]>([]);
  const [selectionAllowed, setSelectionAllowed] = useState(true);
  const [phase, setPhase] = useState<Phase>("choose");
  const [session, setSession] = useState<LearningSession | null>(null);
  const [questions, setQuestions] = useState<SessionQuestion[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState("");
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [result, setResult] = useState<SessionResult | null>(null);
  const [loading, setLoading] = useState(Boolean(token));
  const [error, setError] = useState("");
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now());
  const [loginForm] = Form.useForm();

  function handleRequestError(reason: unknown, fallback: string) {
    if (reason instanceof ApiError && reason.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      setToken("");
      setChildren([]);
      setPhase("choose");
      setError("登录已过期，请家长重新登录。");
      return;
    }
    if (reason instanceof ApiError && reason.code === 42204) {
      setError("这个分类还没有可学习的内容，请让家长先添加并启用内容。");
      return;
    }
    if (reason instanceof ApiError && reason.code === 40404) {
      setError("学习规则还没有设置好，请让家长先完成设置。");
      return;
    }
    setError(reason instanceof Error ? reason.message : fallback);
  }

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let active = true;
    listChildren(token)
      .then((response) => {
        if (!active) return;
        const enabledChildren = response.list.filter(
          (child) => child.status === "active",
        );
        setChildren(enabledChildren);
        setChildId((current) => current || enabledChildren[0]?.id || "");
      })
      .catch(
        (reason) =>
          active &&
          handleRequestError(reason, "无法加载孩子档案，请让家长重新登录。"),
      )
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    if (!token || !childId) return;
    getRule(token, childId)
      .then((rule) => {
        setSelectionAllowed(rule.allow_child_select_types);
        setSelectedTypes(rule.default_content_types);
      })
      .catch(() => {
        setSelectionAllowed(true);
        setSelectedTypes([]);
      });
  }, [childId, token]);

  async function handleLogin(values: {
    account_name: string;
    password: string;
  }) {
    setLoading(true);
    setError("");
    try {
      const response = await login(values.account_name, values.password);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      setToken(response.access_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "登录失败");
      setLoading(false);
    }
  }

  function toggleType(type: ContentType) {
    if (!selectionAllowed) return;
    setSelectedTypes((current) =>
      current.includes(type)
        ? current.filter((item) => item !== type)
        : [...current, type],
    );
  }

  async function handleStart() {
    if (!childId) return;
    setLoading(true);
    setError("");
    try {
      const response = await startSession(token, childId, selectedTypes);
      setSession(response.session);
      setQuestions(response.questions);
      setQuestionIndex(0);
      setSelectedAnswer("");
      setFeedback(null);
      setQuestionStartedAt(Date.now());
      setPhase("learning");
    } catch (reason) {
      handleRequestError(reason, "暂时不能开始学习");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    const question = questions[questionIndex];
    if (!session || !question || !selectedAnswer) return;
    setLoading(true);
    try {
      const response = await submitAnswer(token, childId, session.id, {
        session_question_id: question.id,
        user_answer: selectedAnswer,
        answer_duration_ms: Date.now() - questionStartedAt,
      });
      setFeedback(response);
    } catch (reason) {
      handleRequestError(reason, "答案提交失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleContinue() {
    if (!session) return;
    if (questionIndex < questions.length - 1) {
      setQuestionIndex((current) => current + 1);
      setSelectedAnswer("");
      setFeedback(null);
      setQuestionStartedAt(Date.now());
      return;
    }
    setLoading(true);
    try {
      const response = await completeSession(token, childId, session.id);
      setResult(response);
      setPhase("result");
    } catch (reason) {
      handleRequestError(reason, "学习结果保存失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleCardContinue() {
    const question = questions[questionIndex];
    if (!session || !question) return;
    setLoading(true);
    try {
      const response = await markCardViewed(
        token,
        childId,
        session.id,
        question.id,
        Date.now() - questionStartedAt,
      );
      setSession((current) =>
        current
          ? {
              ...current,
              completed_questions: response.progress.completed_questions,
            }
          : current,
      );
      if (questionIndex < questions.length - 1) {
        setQuestionIndex((current) => current + 1);
        setQuestionStartedAt(Date.now());
      } else {
        const completed = await completeSession(token, childId, session.id);
        setResult(completed);
        setPhase("result");
      }
    } catch (reason) {
      handleRequestError(reason, "学习进度保存失败");
    } finally {
      setLoading(false);
    }
  }

  function restart() {
    setPhase("choose");
    setSession(null);
    setQuestions([]);
    setResult(null);
    setError("");
  }

  if (!token) {
    return (
      <section className="child-gate">
        <div className="child-gate-copy">
          <span className="child-kicker">开始前的小准备</span>
          <Typography.Title>请家长来一下</Typography.Title>
          <Typography.Paragraph>
            登录一次，孩子之后就能直接开始学习。
          </Typography.Paragraph>
        </div>
        <Form
          form={loginForm}
          layout="vertical"
          onFinish={handleLogin}
          className="child-login"
        >
          {error && <Alert type="error" message={error} showIcon />}
          <Form.Item
            name="account_name"
            label="家长账号"
            rules={[{ required: true }]}
          >
            <Input size="large" autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password size="large" autoComplete="current-password" />
          </Form.Item>
          <Button
            htmlType="submit"
            type="primary"
            size="large"
            block
            loading={loading}
          >
            确认登录
          </Button>
        </Form>
      </section>
    );
  }

  if (loading && children.length === 0) {
    return (
      <div className="child-loading">
        <Spin size="large" />
      </div>
    );
  }

  if (children.length === 0) {
    return <Empty description="还没有可用的孩子档案，请先到家长端创建" />;
  }

  const currentQuestion = questions[questionIndex];

  return (
    <section className="child-experience">
      {error && (
        <Alert
          className="child-alert"
          type="error"
          message={error}
          closable
          onClose={() => setError("")}
        />
      )}

      {phase === "choose" && (
        <div className="child-choose">
          <div className="child-welcome">
            <div>
              <span className="child-kicker">今天学一点</span>
              <Typography.Title>
                准备好了吗，
                {children.find((child) => child.id === childId)?.nickname ||
                  children.find((child) => child.id === childId)?.name}
              </Typography.Title>
            </div>
            <Select
              size="large"
              value={childId}
              onChange={setChildId}
              options={children.map((child) => ({
                value: child.id,
                label: child.nickname || child.name,
              }))}
              aria-label="选择孩子"
            />
          </div>

          <div className="type-grid" aria-label="学习类型">
            {CONTENT_TYPES.map((type) => {
              const selected = selectedTypes.includes(type.value);
              return (
                <button
                  key={type.value}
                  type="button"
                  className={`type-tile type-${type.value} ${selected ? "is-selected" : ""}`}
                  onClick={() => toggleType(type.value)}
                  aria-pressed={selected}
                  disabled={!selectionAllowed}
                >
                  <span className="type-mark">{type.mark}</span>
                  <strong>{type.label}</strong>
                  <span>{selected ? "已选择" : "点我选择"}</span>
                </button>
              );
            })}
          </div>

          <div className="child-start-row">
            <span>
              {selectionAllowed
                ? "不选也可以直接开始"
                : "家长已经选好今天的内容"}
            </span>
            <Button
              type="primary"
              size="large"
              loading={loading}
              onClick={handleStart}
            >
              开始学习
            </Button>
          </div>
        </div>
      )}

      {phase === "learning" && currentQuestion && session && (
        <div className="learning-stage">
          <div className="learning-progress">
            <span>
              第 {questionIndex + 1} 题，共 {questions.length} 题
            </span>
            <Progress
              percent={Math.round(
                ((questionIndex + 1) / questions.length) * 100,
              )}
              showInfo={false}
              strokeColor="#ea6a47"
            />
          </div>
          <div
            className={`question-panel ${
              MULTILINE_CARD_QUESTION_TYPES.has(currentQuestion.question_type)
                ? "is-multiline-card"
                : ""
            }`}
          >
            <span className="question-kind">
              {
                CONTENT_TYPES.find(
                  (type) => type.value === currentQuestion.content_type,
                )?.label
              }
            </span>
            <Typography.Title level={2}>
              {currentQuestion.question_stem}
            </Typography.Title>
            {currentQuestion.question_type === "math_arithmetic" ? (
              <div className="math-input">
                <InputNumber
                  size="large"
                  min={0}
                  value={selectedAnswer === "" ? null : Number(selectedAnswer)}
                  onChange={(value) =>
                    setSelectedAnswer(value == null ? "" : String(value))
                  }
                  disabled={Boolean(feedback)}
                  autoFocus
                />
              </div>
            ) : !CARD_QUESTION_TYPES.has(currentQuestion.question_type) ? (
              <div className="answer-grid">
                {currentQuestion.question_options.map((option) => {
                  const state = feedback
                    ? option === feedback.correct_answer
                      ? "is-correct"
                      : option === selectedAnswer
                        ? "is-wrong"
                        : ""
                    : option === selectedAnswer
                      ? "is-selected"
                      : "";
                  return (
                    <button
                      key={option}
                      type="button"
                      className={`answer-option ${state}`}
                      onClick={() => !feedback && setSelectedAnswer(option)}
                      disabled={Boolean(feedback)}
                    >
                      {option}
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>

          {CARD_QUESTION_TYPES.has(currentQuestion.question_type) ? (
            <Button
              className="submit-answer"
              size="large"
              type="primary"
              loading={loading}
              onClick={handleCardContinue}
            >
              {questionIndex === questions.length - 1 ? "完成学习" : "下一个"}
            </Button>
          ) : feedback ? (
            <div
              className={`feedback-strip ${feedback.is_correct ? "feedback-correct" : "feedback-wrong"}`}
            >
              <div>
                <strong>{feedback.is_correct ? "答对了" : "再记一记"}</strong>
                <span>
                  {feedback.is_correct
                    ? feedback.answer_explanation
                    : `正确答案：${feedback.correct_answer}`}
                </span>
              </div>
              <Button
                size="large"
                type="primary"
                onClick={handleContinue}
                loading={loading}
              >
                {questionIndex === questions.length - 1 ? "看结果" : "下一题"}
              </Button>
            </div>
          ) : (
            <Button
              className="submit-answer"
              size="large"
              type="primary"
              disabled={!selectedAnswer}
              loading={loading}
              onClick={handleSubmit}
            >
              提交答案
            </Button>
          )}
        </div>
      )}

      {phase === "result" && result && (
        <div className="result-stage">
          <span className="result-label">本次完成</span>
          <Typography.Title>做得好，学习完成</Typography.Title>
          {result.session.answered_questions > 0 ? (
            <div className="result-score">
              <strong>
                {result.session.accuracy_rate}
                <small>%</small>
              </strong>
              <span>
                答对 {result.session.correct_questions} /{" "}
                {result.session.answered_questions} 题
              </span>
            </div>
          ) : (
            <div className="result-score">
              <strong>{result.session.completed_questions}</strong>
              <span>个内容已学习</span>
            </div>
          )}
          {result.session.answered_questions > 0 && (
            <div className="result-review">
              <Typography.Title level={3}>下次再复习</Typography.Title>
              {result.summary.need_review_contents.length ? (
                <div className="review-list">
                  {result.summary.need_review_contents.map((item) => (
                    <span key={item.content_id}>{item.title}</span>
                  ))}
                </div>
              ) : (
                <p>全部答对，这次没有需要复习的内容。</p>
              )}
            </div>
          )}
          <Button type="primary" size="large" onClick={restart}>
            再来一次
          </Button>
        </div>
      )}
    </section>
  );
}
