import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Empty,
  Form,
  Input,
  InputNumber,
  message,
  Progress,
  Select,
  Spin,
  Typography,
} from "antd";
import { SoundOutlined } from "@ant-design/icons";
import { login } from "@/api/auth";
import { ApiError } from "@/api/client";
import { listChildren } from "@/api/children";
import {
  completeSession,
  markCardViewed,
  startSession,
  submitAnswer,
} from "@/api/learning";
import { getReadingSettings } from "@/api/reading";
import { getRule } from "@/api/rules";
import {
  getReadRate,
  getSpeechLanguage,
  pickVoice,
  READABLE_CARD_QUESTION_TYPES,
  speechSynthesisSupported,
  toReadText,
} from "@/features/child/speech";
import type {
  AnswerFeedback,
  Child,
  ContentType,
  LearningSession,
  ReadingSettings,
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

function AnnotatedText({ text, pinyin }: { text: string; pinyin: string[] }) {
  const chars = Array.from(text);
  // 后端返回的拼音必须与字符数严格一一对应，否则整体错位；
  // 长度不一致时宁可不显示拼音，也不显示错误拼音。
  const aligned = pinyin.length === chars.length ? pinyin : null;
  return (
    <span className="annotated-text">
      {chars.map((char, index) => {
        const py = aligned?.[index];
        if (char === "\n") {
          return <br key={index} />;
        }
        if (py && py !== char) {
          return (
            <span className="char-unit" key={index}>
              <span className="char-pinyin">{py}</span>
              <span className="char-glyph">{char}</span>
            </span>
          );
        }
        return (
          <span className="char-plain" key={index}>
            {char}
          </span>
        );
      })}
    </span>
  );
}

const CONTENT_TYPES: Array<{
  value: ContentType;
  label: string;
  mark: string;
  hint: string;
}> = [
  { value: "character", label: "汉字", mark: "字", hint: "常用字与象形启蒙" },
  { value: "classic", label: "国学", mark: "经", hint: "三字经与弟子规" },
  { value: "poem", label: "古诗", mark: "诗", hint: "唐诗宋词启蒙" },
  { value: "idiom", label: "成语", mark: "言", hint: "四字成语故事" },
  { value: "englishWord", label: "英语", mark: "Aa", hint: "启蒙单词与发音" },
  { value: "math", label: "算术", mark: "算", hint: "加减法口算练习" },
  { value: "pinyin", label: "拼音", mark: "拼", hint: "声母韵母与声调" },
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
  const [isReading, setIsReading] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [readSettings, setReadSettings] = useState<ReadingSettings | null>(
    null,
  );
  const [messageApi, contextHolder] = message.useMessage();

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

  // 加载朗读设置（每类型语速）。
  useEffect(() => {
    if (!token || !childId) return;
    getReadingSettings(token, childId)
      .then((settings) => setReadSettings(settings))
      .catch(() => setReadSettings(null));
  }, [childId, token]);

  // 加载浏览器可用语音；Chrome 首次 getVoices 可能为空，需在 voiceschanged 后刷新。
  useEffect(() => {
    if (!speechSynthesisSupported()) return;
    const synth = window.speechSynthesis;
    const update = () => setVoices(synth.getVoices());
    update();
    synth.addEventListener("voiceschanged", update);
    return () => synth.removeEventListener("voiceschanged", update);
  }, []);

  // 切换题目时停止朗读。
  useEffect(() => {
    stopReading();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionIndex]);

  // 卸载组件时停止朗读。
  useEffect(() => {
    return () => {
      if (speechSynthesisSupported()) window.speechSynthesis.cancel();
    };
  }, []);

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

  function stopReading() {
    if (speechSynthesisSupported()) window.speechSynthesis.cancel();
    setIsReading(false);
  }

  function handleToggleRead() {
    const question = questions[questionIndex];
    if (!question || !speechSynthesisSupported()) return;
    const synth = window.speechSynthesis;
    if (synth.speaking || synth.pending) {
      synth.cancel();
      setIsReading(false);
      return;
    }
    const lang = getSpeechLanguage(question.content_type);
    const utterance = new window.SpeechSynthesisUtterance(
      toReadText(question.question_stem, question.content_type),
    );
    utterance.lang = lang;
    utterance.rate = getReadRate(question.content_type, readSettings);
    const voice = pickVoice(voices, lang);
    if (voice) utterance.voice = voice;
    utterance.onend = () => setIsReading(false);
    utterance.onerror = () => {
      setIsReading(false);
      messageApi.error("朗读失败：可能未安装该语言的语音包，或网络不可用。");
    };
    synth.speak(utterance);
    setIsReading(true);
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
    stopReading();
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
    stopReading();
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
    stopReading();
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
  // 只要浏览器支持 Web Speech API 就允许点击；
  // 找不到匹配语音时仍以 utterance.lang 兜底（如 Chrome 云语音），不再禁用按钮。
  const canRead = speechSynthesisSupported();

  return (
    <section className="child-experience">
      {contextHolder}
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
              <span className="child-kicker">今天学一点 · 知识会发光</span>
              <Typography.Title>
                准备好了吗，
                {children.find((child) => child.id === childId)?.nickname ||
                  children.find((child) => child.id === childId)?.name}
              </Typography.Title>
              <p className="child-welcome-sub">
                选一门今天最感兴趣的课程，或者直接启航综合挑战！
              </p>
            </div>
            <div className="child-selector">
              <span className="child-selector-avatar" aria-hidden="true">
                {(
                  children.find((child) => child.id === childId)?.nickname ||
                  children.find((child) => child.id === childId)?.name ||
                  "小"
                ).slice(0, 1)}
              </span>
              <Select
                size="large"
                variant="borderless"
                value={childId}
                onChange={setChildId}
                options={children.map((child) => ({
                  value: child.id,
                  label: child.nickname || child.name,
                }))}
                aria-label="选择孩子"
              />
            </div>
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
                  <span className="type-tile-sub">{type.hint}</span>
                  <span className="type-tile-foot">
                    {selected ? "已选择" : "点我选择"}
                    <span className="type-check" aria-hidden="true">
                      ✓
                    </span>
                  </span>
                </button>
              );
            })}
          </div>

          <div className="child-bottom-bar">
            <span className="child-hint">
              <span aria-hidden="true">💡</span>
              <strong>
                {selectionAllowed
                  ? "不选也可以直接开始"
                  : "家长已经选好今天的内容"}
              </strong>
            </span>
            <div className="child-start-row">
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
                : currentQuestion.question_type === "idiom_card"
                  ? "is-idiom-card"
                  : currentQuestion.question_type === "english_word_card"
                    ? "is-english-word-card"
                    : ""
            }`}
          >
            <div className="question-head">
              <span className="question-kind">
                {
                  CONTENT_TYPES.find(
                    (type) => type.value === currentQuestion.content_type,
                  )?.label
                }
              </span>
              {READABLE_CARD_QUESTION_TYPES.has(
                currentQuestion.question_type,
              ) && (
                <Button
                  className="read-aloud"
                  type="text"
                  icon={<SoundOutlined />}
                  onClick={handleToggleRead}
                  disabled={!canRead}
                >
                  {isReading ? "停止朗读" : "朗读"}
                </Button>
              )}
            </div>
            <Typography.Title level={2}>
              {currentQuestion.question_pinyin &&
              currentQuestion.question_pinyin.length > 0 ? (
                <AnnotatedText
                  text={currentQuestion.question_stem}
                  pinyin={currentQuestion.question_pinyin}
                />
              ) : (
                currentQuestion.question_stem
              )}
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
