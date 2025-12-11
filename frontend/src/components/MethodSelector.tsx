/**
 * Method selection component.
 */

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import { useStore, DiscussionMethod } from "../store/index.js";
import { t } from "../i18n/index.js";

interface Method {
  id: DiscussionMethod;
  name: string;
  description: string;
  requires: string;
  bestFor: string;
  min: number;
  evenOnly: boolean;
}

// Methods with translated names and descriptions
const getMethods = (): Method[] => [
  {
    id: "standard",
    name: t("method.standard.name"),
    description: t("method.standard.desc"),
    requires: t("method.standard.requirement"),
    bestFor: t("method.standard.useCase"),
    min: 2,
    evenOnly: false,
  },
  {
    id: "oxford",
    name: t("method.oxford.name"),
    description: t("method.oxford.desc"),
    requires: t("method.oxford.requirement"),
    bestFor: t("method.oxford.useCase"),
    min: 2,
    evenOnly: true,
  },
  {
    id: "advocate",
    name: t("method.advocate.name"),
    description: t("method.advocate.desc"),
    requires: t("method.advocate.requirement"),
    bestFor: t("method.advocate.useCase"),
    min: 3,
    evenOnly: false,
  },
  {
    id: "socratic",
    name: t("method.socratic.name"),
    description: t("method.socratic.desc"),
    requires: t("method.socratic.requirement"),
    bestFor: t("method.socratic.useCase"),
    min: 2,
    evenOnly: false,
  },
  {
    id: "delphi",
    name: t("method.delphi.name"),
    description: t("method.delphi.desc"),
    requires: t("method.delphi.requirement"),
    bestFor: t("method.delphi.useCase"),
    min: 3,
    evenOnly: false,
  },
  {
    id: "brainstorm",
    name: t("method.brainstorm.name"),
    description: t("method.brainstorm.desc"),
    requires: t("method.brainstorm.requirement"),
    bestFor: t("method.brainstorm.useCase"),
    min: 2,
    evenOnly: false,
  },
  {
    id: "tradeoff",
    name: t("method.tradeoff.name"),
    description: t("method.tradeoff.desc"),
    requires: t("method.tradeoff.requirement"),
    bestFor: t("method.tradeoff.useCase"),
    min: 2,
    evenOnly: false,
  },
];

/**
 * Check if a method is compatible with the number of selected models.
 */
function isMethodCompatible(method: Method, numModels: number): { valid: boolean; error?: string } {
  if (numModels < method.min) {
    return { valid: false, error: t("selector.method.needsMin", { min: String(method.min) }) };
  }
  if (method.evenOnly && numModels % 2 !== 0) {
    return { valid: false, error: t("selector.method.needsEven") };
  }
  return { valid: true };
}

interface MethodSelectorProps {
  onSelect: () => void;  // Called after method is set, triggers soft reload
}

export function MethodSelector({ onSelect }: MethodSelectorProps) {
  const { discussionMethod, setDiscussionMethod, selectedModels } = useStore();
  const numModels = selectedModels.length;
  const METHODS = getMethods();
  const [selectedIndex, setSelectedIndex] = useState(
    METHODS.findIndex((m) => m.id === discussionMethod)
  );

  useInput((input, key) => {
    if (key.escape) {
      onSelect();  // Just soft reload, no method change
      return;
    }

    if (key.upArrow) {
      setSelectedIndex((prev) => Math.max(0, prev - 1));
      return;
    }

    if (key.downArrow) {
      setSelectedIndex((prev) => Math.min(METHODS.length - 1, prev + 1));
      return;
    }

    if (key.return) {
      const method = METHODS[selectedIndex];
      const compat = isMethodCompatible(method, numModels);
      if (!compat.valid) {
        // Don't allow selecting incompatible method
        return;
      }
      // Set method, then soft reload
      setDiscussionMethod(method.id);
      onSelect();
      return;
    }
  });

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="magenta"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1} justifyContent="space-between">
        <Text bold color="magenta">
          {t("selector.method.title")}
        </Text>
        <Text dimColor>
          {t("selector.method.modelsSelected", { count: String(numModels), plural: numModels !== 1 ? "s" : "" })}
        </Text>
      </Box>

      {METHODS.map((method, index) => {
        const isSelected = discussionMethod === method.id;
        const isCurrent = index === selectedIndex;
        const compat = isMethodCompatible(method, numModels);
        const isDisabled = !compat.valid;

        return (
          <Box key={method.id} flexDirection="column" marginBottom={index < METHODS.length - 1 ? 1 : 0}>
            <Box>
              <Text
                backgroundColor={isCurrent && !isDisabled ? "magenta" : undefined}
                color={isDisabled ? "gray" : isCurrent ? "white" : isSelected ? "magenta" : undefined}
                bold={isSelected && !isDisabled}
                dimColor={isDisabled}
              >
                {isSelected ? "◉ " : "○ "}
              </Text>
              <Text
                backgroundColor={isCurrent && !isDisabled ? "magenta" : undefined}
                color={isDisabled ? "gray" : isCurrent ? "white" : isSelected ? "magenta" : undefined}
                bold={(isSelected || isCurrent) && !isDisabled}
                dimColor={isDisabled}
                strikethrough={isDisabled}
              >
                {method.name}
              </Text>
              <Text
                backgroundColor={isCurrent && !isDisabled ? "magenta" : undefined}
                color={isDisabled ? "red" : isCurrent ? "white" : "yellow"}
                dimColor={!isCurrent && !isDisabled}
              >
                {" "}({isDisabled ? compat.error : method.requires})
              </Text>
            </Box>
            <Box marginLeft={3}>
              <Text dimColor>{method.description}</Text>
            </Box>
            <Box marginLeft={3}>
              <Text dimColor color="cyan">Best for: {method.bestFor}</Text>
            </Box>
          </Box>
        );
      })}

      <Box marginTop={1}>
        <Text dimColor>{t("selector.method.navigation")}</Text>
      </Box>
    </Box>
  );
}
