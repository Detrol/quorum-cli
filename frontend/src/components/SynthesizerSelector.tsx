/**
 * Synthesizer mode selection component.
 */

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { t } from "../i18n/index.js";

type SynthesizerMode = "first" | "random" | "rotate";

interface Mode {
  id: SynthesizerMode;
  name: string;
  description: string;
}

// Modes will get their names from translations
const getModes = (): Mode[] => [
  { id: "first", name: t("synth.first.name"), description: t("synth.first.desc") },
  { id: "random", name: t("synth.random.name"), description: t("synth.random.desc") },
  { id: "rotate", name: t("synth.rotate.name"), description: t("synth.rotate.desc") },
];

interface SynthesizerSelectorProps {
  onSelect: () => void;  // Called when done, triggers soft reload
}

export function SynthesizerSelector({ onSelect }: SynthesizerSelectorProps) {
  const { synthesizerMode, setSynthesizerMode } = useStore();
  const MODES = getModes();
  const [selectedIndex, setSelectedIndex] = useState(
    MODES.findIndex((m) => m.id === synthesizerMode)
  );

  useInput((input, key) => {
    if (key.escape) {
      onSelect();  // Soft reload
      return;
    }

    if (key.upArrow) {
      setSelectedIndex((prev) => Math.max(0, prev - 1));
      return;
    }

    if (key.downArrow) {
      setSelectedIndex((prev) => Math.min(MODES.length - 1, prev + 1));
      return;
    }

    if (key.return) {
      const mode = MODES[selectedIndex];
      setSynthesizerMode(mode.id);
      onSelect();  // Soft reload
      return;
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
          {t("selector.synthesizer.title")}
        </Text>
      </Box>

      {MODES.map((mode, index) => {
        const isSelected = synthesizerMode === mode.id;
        const isCurrent = index === selectedIndex;

        return (
          <Box key={mode.id}>
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
              {mode.name.padEnd(10)}
            </Text>
            <Text
              backgroundColor={isCurrent ? "cyan" : undefined}
              color={isCurrent ? "black" : undefined}
              dimColor={!isCurrent}
            >
              {" "}{mode.description}
            </Text>
          </Box>
        );
      })}

      <Box marginTop={1}>
        <Text dimColor>{t("selector.synthesizer.navigation")}</Text>
      </Box>
    </Box>
  );
}
