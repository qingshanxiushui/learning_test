import { describe, expect, it } from "vitest";
import {
  DEFAULT_AUTO_STOP_SECONDS,
  DEFAULT_READ_RATE,
  getReadRate,
  getRecordConfig,
  getSpeechLanguage,
  normalizeTranscript,
  pickVoice,
  READABLE_CARD_QUESTION_TYPES,
  speechRecognitionSupported,
  speechSynthesisSupported,
  toReadText,
  voiceMatchesLang,
} from "@/features/child/speech";
import type { ReadingSettings, RecordingSettings } from "@/types/api";

function stubVoice(lang: string): SpeechSynthesisVoice {
  return { lang, name: lang } as unknown as SpeechSynthesisVoice;
}

function clearSpeechStub() {
  Reflect.deleteProperty(window, "speechSynthesis");
  Reflect.deleteProperty(window, "SpeechSynthesisUtterance");
}

describe("speech helpers", () => {
  it("cleans decorative symbols and line breaks from the read text", () => {
    expect(
      toReadText("《静夜思》唐·李白\n床前明月光\n疑是地上霜", "poem"),
    ).toBe("静夜思 唐 李白 床前明月光 疑是地上霜");
    expect(toReadText("根", "character")).toBe("根");
    expect(toReadText("地大物博", "idiom")).toBe("地大物博");
    expect(toReadText("apple", "englishWord")).toBe("apple");
  });

  it("keeps punctuation as natural pauses", () => {
    expect(toReadText("床前明月光，疑是地上霜。", "poem")).toBe(
      "床前明月光，疑是地上霜。",
    );
  });

  it("selects the speech language from the content type", () => {
    expect(getSpeechLanguage("englishWord")).toBe("en-US");
    expect(getSpeechLanguage("character")).toBe("zh-CN");
    expect(getSpeechLanguage("classic")).toBe("zh-CN");
    expect(getSpeechLanguage("poem")).toBe("zh-CN");
    expect(getSpeechLanguage("idiom")).toBe("zh-CN");
  });

  it("matches regional voices to the target language", () => {
    expect(voiceMatchesLang("zh-CN", "zh-CN")).toBe(true);
    expect(voiceMatchesLang("en_US", "en-US")).toBe(true);
    expect(voiceMatchesLang("en-GB", "en-US")).toBe(true);
    expect(voiceMatchesLang("zh-TW", "zh-CN")).toBe(true);
    expect(voiceMatchesLang("ja-JP", "zh-CN")).toBe(false);
  });

  it("prefers an exact voice and falls back to a same-language voice", () => {
    const voices = [stubVoice("zh-TW"), stubVoice("en-US")];
    expect(pickVoice(voices, "zh-CN")?.lang).toBe("zh-TW");
    expect(pickVoice(voices, "en-GB")?.lang).toBe("en-US");
    expect(pickVoice(voices, "fr-FR")).toBeNull();
  });

  it("only marks the five card types as readable", () => {
    expect([...READABLE_CARD_QUESTION_TYPES].sort()).toEqual([
      "character_card",
      "classic_card",
      "english_word_card",
      "idiom_card",
      "poem_card",
    ]);
    expect(READABLE_CARD_QUESTION_TYPES.has("math_arithmetic")).toBe(false);
    expect(READABLE_CARD_QUESTION_TYPES.has("pinyin_card")).toBe(false);
  });

  it("detects Web Speech API support", () => {
    clearSpeechStub();
    expect(speechSynthesisSupported()).toBe(false);

    Object.assign(window, {
      speechSynthesis: {},
      SpeechSynthesisUtterance: class {},
    });
    expect(speechSynthesisSupported()).toBe(true);

    clearSpeechStub();
  });

  it("reads the per-type rate from reading settings", () => {
    const settings: ReadingSettings = {
      id: "r-1",
      child_id: "child-1",
      character_rate: 0.7,
      classic_rate: 0.6,
      poem_rate: 0.5,
      idiom_rate: 0.9,
      english_rate: 1.1,
      status: 1,
      created_at: "2026-11-06T10:00:00Z",
      updated_at: "2026-11-06T10:00:00Z",
    };
    expect(getReadRate("character", settings)).toBe(0.7);
    expect(getReadRate("classic", settings)).toBe(0.6);
    expect(getReadRate("poem", settings)).toBe(0.5);
    expect(getReadRate("idiom", settings)).toBe(0.9);
    expect(getReadRate("englishWord", settings)).toBe(1.1);
    // 无设置时回退默认语速；非朗读类型（如 math/pinyin）也回退默认。
    expect(getReadRate("poem", null)).toBe(DEFAULT_READ_RATE);
    expect(getReadRate("math", settings)).toBe(DEFAULT_READ_RATE);
  });

  it("normalizes the transcript for idiom matching", () => {
    expect(normalizeTranscript("地大物博")).toBe("地大物博");
    expect(normalizeTranscript(" 地大物博 ")).toBe("地大物博");
    expect(normalizeTranscript("地大，物博")).toBe("地大物博");
    expect(normalizeTranscript("地 大 物 博")).toBe("地大物博");
  });

  it("detects speech recognition support", () => {
    Reflect.deleteProperty(window, "SpeechRecognition");
    Reflect.deleteProperty(window, "webkitSpeechRecognition");
    expect(speechRecognitionSupported()).toBe(false);

    Object.assign(window, { SpeechRecognition: class {} });
    expect(speechRecognitionSupported()).toBe(true);

    Reflect.deleteProperty(window, "SpeechRecognition");
    Reflect.deleteProperty(window, "webkitSpeechRecognition");
  });

  it("reads per-type recording config with defaults", () => {
    const settings: RecordingSettings = {
      id: "rec-1",
      child_id: "child-1",
      character_enabled: false,
      character_auto_stop: true,
      character_auto_stop_seconds: 8,
      english_enabled: true,
      english_auto_stop: false,
      english_auto_stop_seconds: 5,
      idiom_enabled: true,
      idiom_auto_stop: true,
      idiom_auto_stop_seconds: 3,
      pinyin_enabled: true,
      pinyin_auto_stop: false,
      pinyin_auto_stop_seconds: 5,
      status: 1,
      created_at: "2026-11-19T10:00:00Z",
      updated_at: "2026-11-19T10:00:00Z",
    };
    expect(getRecordConfig("character", settings)).toEqual({
      enabled: false,
      autoStop: true,
      seconds: 8,
    });
    expect(getRecordConfig("englishWord", settings)).toEqual({
      enabled: true,
      autoStop: false,
      seconds: 5,
    });
    expect(getRecordConfig("idiom", settings)).toEqual({
      enabled: true,
      autoStop: true,
      seconds: 3,
    });
    expect(getRecordConfig("pinyin", settings)).toEqual({
      enabled: true,
      autoStop: false,
      seconds: 5,
    });
    // 无设置时回退默认（开启、手动结束、默认时长）
    expect(getRecordConfig("character", null)).toEqual({
      enabled: true,
      autoStop: false,
      seconds: DEFAULT_AUTO_STOP_SECONDS,
    });
  });
});
