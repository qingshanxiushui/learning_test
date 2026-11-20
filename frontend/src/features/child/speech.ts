import type {
  ContentType,
  ReadingSettings,
  RecordingSettings,
} from "@/types/api";

/** 需要展示「朗读」按钮的卡片题型（拼音、算术题型除外）。 */
export const READABLE_CARD_QUESTION_TYPES: ReadonlySet<string> = new Set([
  "character_card",
  "classic_card",
  "poem_card",
  "idiom_card",
  "english_word_card",
]);

/** 需要展示「录音」按钮的卡片题型（汉字/英语/成语/拼音；古诗、国学仅朗读不录音）。 */
export const RECORDABLE_CARD_QUESTION_TYPES: ReadonlySet<string> = new Set([
  "character_card",
  "english_word_card",
  "idiom_card",
  "pinyin_card",
]);

/** 浏览器是否支持 Web Speech API（含构造器）。 */
export function speechSynthesisSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    typeof window.SpeechSynthesisUtterance === "function"
  );
}

/** 按内容类型选择朗读语音：英语使用 en-US，其余使用 zh-CN。 */
export function getSpeechLanguage(contentType: ContentType): string {
  return contentType === "englishWord" ? "en-US" : "zh-CN";
}

/** 判断某语音的语言是否匹配目标语言（兼容 en 匹配 en-US/en-GB）。 */
export function voiceMatchesLang(voiceLang: string, lang: string): boolean {
  const normalized = voiceLang.toLowerCase().replace("_", "-");
  const target = lang.toLowerCase();
  const targetBase = target.split("-")[0];
  return (
    normalized === target ||
    normalized === targetBase ||
    normalized.startsWith(`${targetBase}-`)
  );
}

/**
 * 由题干清洗出适合朗读的文本：
 * - 去掉《》、·（含日式间隔号 ・）等装饰符号（转为空格，避免「静夜思唐」连读）；
 * - 换行转为空格作为停顿；
 * - 保留 ，。！？ 等标点作为自然停顿。
 */
export function toReadText(stem: string, _contentType: ContentType): string {
  return stem
    .replace(/[《》·・]/g, " ")
    .replace(/\n+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** 在候选语音中挑选与目标语言匹配的语音，没有匹配项时返回 null。 */
export function pickVoice(
  voices: SpeechSynthesisVoice[],
  lang: string,
): SpeechSynthesisVoice | null {
  const exact = voices.find((voice) => voice.lang === lang);
  if (exact) return exact;
  return voices.find((voice) => voiceMatchesLang(voice.lang, lang)) ?? null;
}

/** 默认朗读语速（无设置时使用）。 */
export const DEFAULT_READ_RATE = 0.8;

/** 按内容类型取朗读语速；设置缺失时回退默认语速。 */
export function getReadRate(
  contentType: ContentType,
  settings: ReadingSettings | null,
): number {
  if (!settings) return DEFAULT_READ_RATE;
  switch (contentType) {
    case "character":
      return settings.character_rate;
    case "classic":
      return settings.classic_rate;
    case "poem":
      return settings.poem_rate;
    case "idiom":
      return settings.idiom_rate;
    case "englishWord":
      return settings.english_rate;
    default:
      return DEFAULT_READ_RATE;
  }
}

// ---------------------------------------------------------------------------
// 语音识别（成语录音答题）
// ---------------------------------------------------------------------------

/** SpeechRecognition 的最小类型声明（兼容 webkit 前缀与 TS 类型缺失）。 */
export interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorLike) => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

export interface SpeechRecognitionEventLike {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
}

export interface SpeechRecognitionErrorLike {
  error: string;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

/** 获取语音识别构造器，兼容 Chrome 的 SpeechRecognition 与 Safari 的 webkitSpeechRecognition。 */
export function getSpeechRecognition(): SpeechRecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  const win = window as unknown as {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };
  return win.SpeechRecognition ?? win.webkitSpeechRecognition ?? null;
}

/** 浏览器是否支持语音识别（Web Speech API 识别部分）。 */
export function speechRecognitionSupported(): boolean {
  return getSpeechRecognition() !== null;
}

/** 归一化识别文本，去除空白、标点、书名号/引号，用于与题目成语判分比对。 */
export function normalizeTranscript(text: string): string {
  return text.replace(/[\s，。！？、,.!?·・《》"'“”]/g, "").trim();
}

// ---------------------------------------------------------------------------
// 录音设置
// ---------------------------------------------------------------------------

/** 录音配置（按内容类型）。 */
export interface RecordConfig {
  enabled: boolean;
  autoStop: boolean;
  seconds: number;
}

/** 默认自动结束时长（秒）。 */
export const DEFAULT_AUTO_STOP_SECONDS = 5;

/** 按内容类型取录音配置；设置缺失时回退默认（开启、手动结束、5 秒）。 */
export function getRecordConfig(
  contentType: ContentType,
  settings: RecordingSettings | null,
): RecordConfig {
  if (!settings) {
    return {
      enabled: true,
      autoStop: false,
      seconds: DEFAULT_AUTO_STOP_SECONDS,
    };
  }
  switch (contentType) {
    case "character":
      return {
        enabled: settings.character_enabled,
        autoStop: settings.character_auto_stop,
        seconds: settings.character_auto_stop_seconds,
      };
    case "englishWord":
      return {
        enabled: settings.english_enabled,
        autoStop: settings.english_auto_stop,
        seconds: settings.english_auto_stop_seconds,
      };
    case "idiom":
      return {
        enabled: settings.idiom_enabled,
        autoStop: settings.idiom_auto_stop,
        seconds: settings.idiom_auto_stop_seconds,
      };
    case "pinyin":
      return {
        enabled: settings.pinyin_enabled,
        autoStop: settings.pinyin_auto_stop,
        seconds: settings.pinyin_auto_stop_seconds,
      };
    default:
      return {
        enabled: false,
        autoStop: false,
        seconds: DEFAULT_AUTO_STOP_SECONDS,
      };
  }
}
