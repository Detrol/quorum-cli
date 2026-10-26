/**
 * Language selector modal component.
 * Allows user to select response language for AI models.
 */

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { t, setLanguage } from "../i18n/index.js";
import type { SupportedLanguage } from "../i18n/index.js";

interface LanguageOption {
  code: SupportedLanguage;
  flag: string;
  nativeName: string;
}

const LANGUAGES: LanguageOption[] = [
  { code: "en", flag: "🇬🇧", nativeName: "English" },
  { code: "sv", flag: "🇸🇪", nativeName: "Svenska" },
  { code: "de", flag: "🇩🇪", nativeName: "Deutsch" },
  { code: "fr", flag: "🇫🇷", nativeName: "Français" },
  { code: "es", flag: "🇪🇸", nativeName: "Español" },
  { code: "it", flag: "🇮🇹", nativeName: "Italiano" },
  { code: "zh", flag: "🇨🇳", nativeName: "中文" },
];

interface Props {
  onClose: () => void;
}

export function LanguageSelector({ onClose }: Props) {
  const { responseLanguage, setResponseLanguage } = useStore();
  const currentIndex = LANGUAGES.findIndex((l) => l.code === responseLanguage);
  const [selectedIndex, setSelectedIndex] = useState(
    currentIndex >= 0 ? currentIndex : 0
  );

  useInput((input, key) => {
    if (key.escape) {
      onClose();
      return;
    }

    if (key.upArrow) {
      setSelectedIndex((i) => (i > 0 ? i - 1 : LANGUAGES.length - 1));
      return;
    }

    if (key.downArrow) {
      setSelectedIndex((i) => (i < LANGUAGES.length - 1 ? i + 1 : 0));
      return;
    }

    if (key.return) {
      const selected = LANGUAGES[selectedIndex];
      setResponseLanguage(selected.code);
      // Also update UI language
      setLanguage(selected.code);
      onClose();
    }
  });

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="cyan"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text bold color="cyan">
          {t("selector.language.title")}
        </Text>
      </Box>

      {LANGUAGES.map((lang, index) => {
        const isSelected = lang.code === responseLanguage;
        const isCurrent = index === selectedIndex;

        return (
          <Box key={lang.code}>
            <Text
              backgroundColor={isCurrent ? "cyan" : undefined}
              color={isCurrent ? "black" : isSelected ? "cyan" : undefined}
              bold={isSelected}
            >
              {isSelected ? "◉ " : "○ "}
            </Text>
            <Text
              backgroundColor={isCurrent ? "cyan" : undefined}
              color={isCurrent ? "black" : isSelected ? "cyan" : undefined}
              bold={isSelected}
            >
              {lang.flag} {lang.nativeName.padEnd(10)}
            </Text>
          </Box>
        );
      })}

      <Box marginTop={1}>
        <Text dimColor>{t("selector.language.navigation")}</Text>
      </Box>
    </Box>
  );
}
