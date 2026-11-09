import type { ContentType, ReadingSettings } from "@/types/api";

/** 需要展示「朗读」按钮的卡片题型（拼音、算术题型除外）。 */
export const READABLE_CARD_QUESTION_TYPES: ReadonlySet<string> = new Set([
  "character_card",
  "classic_card",
  "poem_card",
  "idiom_card",
  "english_word_card",
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
