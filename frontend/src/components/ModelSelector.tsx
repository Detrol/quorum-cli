/**
 * Model selection component.
 */

import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import type { ModelInfo } from "../ipc/protocol.js";
import { t } from "../i18n/index.js";

interface ModelSelectorProps {
  onSelect: () => void;  // Called when done, triggers soft reload
}

export function ModelSelector({ onSelect }: ModelSelectorProps) {
  const {
    availableModels,
    selectedModels,
    toggleSelectedModel,
    validatedModels,
    invalidModels,
  } = useStore();

  const [selectedIndex, setSelectedIndex] = useState(0);
  const [confirming, setConfirming] = useState(false);

  // Flatten models into a list
  const allModels: { provider: string; model: ModelInfo }[] = [];
  for (const [provider, models] of Object.entries(availableModels)) {
    for (const model of models) {
      allModels.push({ provider, model });
    }
  }

  useInput((input, key) => {
    if (key.escape) {
      if (confirming) {
        setConfirming(false);
      } else {
        onSelect();  // Soft reload
      }
      return;
    }

    if (key.upArrow) {
      setSelectedIndex((prev) => Math.max(0, prev - 1));
      return;
    }

    if (key.downArrow) {
      setSelectedIndex((prev) => Math.min(allModels.length - 1, prev + 1));
      return;
    }

    if (input === " " && allModels.length > 0) {
      const modelId = allModels[selectedIndex].model.id;
      // Only allow toggling validated models
      if (validatedModels.has(modelId)) {
        toggleSelectedModel(modelId);
      }
      return;
    }

    if (key.return) {
      if (selectedModels.length >= 2) {
        onSelect();  // Models already saved in store, just soft reload
      } else {
        setConfirming(true);
      }
      return;
    }
  });

  if (allModels.length === 0) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="red"
        paddingX={2}
        paddingY={1}
      >
        <Text bold color="red">
          {t("selector.model.noModels")}
        </Text>
        <Text dimColor>{t("selector.model.checkApi")}</Text>
      </Box>
    );
  }

  let currentProvider = "";

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
          {t("selector.model.title")}
        </Text>
        <Text dimColor> {t("selector.model.instructions")}</Text>
      </Box>

      {/* Selected count */}
      <Box marginBottom={1}>
        <Text>{t("selector.model.selected")}</Text>
        <Text color={selectedModels.length >= 2 ? "green" : "yellow"} bold>
          {selectedModels.length}
        </Text>
        <Text dimColor> {t("selector.model.minimum")}</Text>
      </Box>

      {/* Model list */}
      {allModels.map((item, index) => {
        const modelId = item.model.id;
        const isSelected = selectedModels.includes(modelId);
        const isCurrent = index === selectedIndex;
        const isValid = validatedModels.has(modelId);
        const error = invalidModels[modelId];
        const isDisabled = !isValid;

        // Provider header
        let providerHeader = null;
        if (item.provider !== currentProvider) {
          currentProvider = item.provider;
          providerHeader = (
            <Box key={`provider-${item.provider}`} marginTop={index > 0 ? 1 : 0}>
              <Text bold color="blue">
                {item.provider.toUpperCase()}
              </Text>
            </Box>
          );
        }

        return (
          <React.Fragment key={modelId}>
            {providerHeader}
            <Box>
              <Text
                backgroundColor={isCurrent ? "blue" : undefined}
                color={isDisabled ? "gray" : isCurrent ? "white" : undefined}
                dimColor={isDisabled}
              >
                {isSelected ? "◉ " : "○ "}
              </Text>
              <Text
                backgroundColor={isCurrent ? "blue" : undefined}
                color={
                  error
                    ? "red"
                    : isDisabled
                    ? "gray"
                    : isSelected
                    ? "green"
                    : isCurrent
                    ? "white"
                    : undefined
                }
                bold={isSelected && !isDisabled}
                dimColor={isDisabled && !error}
              >
                {item.model.display_name || modelId}
              </Text>
              {error && <Text color="red"> ✗ {error}</Text>}
              {isSelected && isValid && <Text color="green"> ✓</Text>}
            </Box>
          </React.Fragment>
        );
      })}

      {/* Warning if less than 2 selected */}
      {confirming && selectedModels.length < 2 && (
        <Box marginTop={1}>
          <Text color="yellow">
            ⚠ {t("selector.model.warning")}
          </Text>
        </Box>
      )}

      {/* Instructions */}
      <Box marginTop={1} flexDirection="column">
        <Text dimColor>{t("selector.model.navigation")}</Text>
      </Box>
    </Box>
  );
}
