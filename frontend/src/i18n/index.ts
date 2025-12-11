/**
 * Internationalization (i18n) module for Quorum frontend.
 *
 * Supports 6 languages: English, Swedish, German, French, Spanish, Italian.
 * Language is determined by QUORUM_DEFAULT_LANGUAGE setting.
 */

import type { TranslationKey, Translations, SupportedLanguage } from "./types.js";
import { en } from "./translations/en.js";
import { sv } from "./translations/sv.js";
import { de } from "./translations/de.js";
import { fr } from "./translations/fr.js";
import { es } from "./translations/es.js";
import { it } from "./translations/it.js";

// All available translations
const translations: Record<SupportedLanguage, Translations> = {
  en,
  sv,
  de,
  fr,
  es,
  it,
};

// Current language (defaults to English)
let currentLanguage: SupportedLanguage = "en";

/**
 * Map language string to supported language code.
 * Handles various formats: "Swedish", "sv", "swedish", etc.
 */
function mapLanguageToCode(lang: string | null | undefined): SupportedLanguage {
  if (!lang) return "en";

  const normalized = lang.toLowerCase().trim();

  // Direct code matches
  if (normalized in translations) {
    return normalized as SupportedLanguage;
  }

  // Full name matches
  const nameMap: Record<string, SupportedLanguage> = {
    english: "en",
    swedish: "sv",
    svenska: "sv",
    german: "de",
    deutsch: "de",
    french: "fr",
    francais: "fr",
    spanish: "es",
    espanol: "es",
    italian: "it",
    italiano: "it",
  };

  return nameMap[normalized] || "en";
}

/**
 * Set the current language.
 * Call this when config is loaded from backend.
 */
export function setLanguage(lang: string | null | undefined): void {
  currentLanguage = mapLanguageToCode(lang);
}

/**
 * Get the current language code.
 */
export function getLanguage(): SupportedLanguage {
  return currentLanguage;
}

/**
 * Translate a key with optional parameter interpolation.
 *
 * @param key - Translation key
 * @param params - Parameters to interpolate (e.g., { model: "GPT-4o" })
 * @returns Translated string
 *
 * @example
 * t("thinkingComplete", { model: "GPT-4o" })
 * // → "GPT-4o finished thinking" (en)
 * // → "GPT-4o har tankt klart" (sv)
 */
export function t(key: TranslationKey, params?: Record<string, string>): string {
  let text = translations[currentLanguage]?.[key] || translations.en[key] || key;

  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(new RegExp(`\\{${k}\\}`, "g"), v);
    });
  }

  return text;
}

// Re-export types
export type { TranslationKey, Translations, SupportedLanguage } from "./types.js";
