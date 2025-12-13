/**
 * Status display component.
 */

import React from "react";
import { Box, Text, useInput } from "ink";
import { useStore } from "../store/index.js";
import { getModelDisplayName } from "./Message.js";
import { t } from "../i18n/index.js";

export function Status() {
  const {
    selectedModels,
    availableModels,
    discussionMethod,
    synthesizerMode,
    maxTurns,
    setShowStatus,
  } = useStore();

  useInput((input, key) => {
    if (key.escape) {
      setShowStatus(false);
    }
  });

  const modelNames = selectedModels.map((id) =>
    getModelDisplayName(id, availableModels)
  );

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="blue"
      paddingX={2}
      paddingY={1}
    >
      <Text bold color="blue">
        {t("status.title")}
      </Text>

      <Box marginTop={1} flexDirection="column">
        <Box>
          <Text bold>{t("status.models")}</Text>
          {modelNames.length > 0 ? (
            <Text color="green">{modelNames.join(", ")}</Text>
          ) : (
            <Text dimColor>{t("status.none")}</Text>
          )}
        </Box>

        <Box>
          <Text bold>{t("status.method")}</Text>
          <Text color="cyan">{discussionMethod}</Text>
        </Box>

        <Box>
          <Text bold>{t("status.synthesizer")}</Text>
          <Text>{synthesizerMode}</Text>
        </Box>

        <Box>
          <Text bold>{t("status.maxTurns")}</Text>
          <Text>{maxTurns || t("status.default")}</Text>
        </Box>
      </Box>
    </Box>
  );
}
