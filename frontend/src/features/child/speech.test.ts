import { describe, expect, it } from "vitest";
import {
  DEFAULT_READ_RATE,
  getReadRate,
  getSpeechLanguage,
  pickVoice,
  READABLE_CARD_QUESTION_TYPES,
  speechSynthesisSupported,
  toReadText,
  voiceMatchesLang,
} from "@/features/child/speech";
import type { ReadingSettings } from "@/types/api";

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
});
